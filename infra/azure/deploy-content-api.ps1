[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$AzureCli='az',
 [string]$Python='python',
 [switch]$Apply
)
# Package and deploy the content API to its Flex Consumption function app.
# Dry run (default): verifies the target through ARM, builds the Linux package locally (Python 3.12 wheels, allow-listed sources, secret scan)
# and prints its manifest. It does not contact the app and changes nothing in Azure. -Apply deploys the SAME zip and then verifies:
# the function is registered, /v1/health answers, and an invalid key reaches the database and is refused (401, not 503).
# Rollback: redeploy an earlier zip kept under .deploy/ (packages are immutable and reproducible).
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$app="anderzilla-content-api-$Environment"
$siteBase="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/sites/$app"
$site=Invoke-IdentityAz -Arguments @('rest','--method','get','--url',$siteBase,'--url-parameters','api-version=2023-12-01')
$config=$site.properties.functionAppConfig
if(!$site -or $site.kind -ne 'functionapp,linux' -or !$config -or $config.runtime.name -ne 'python' -or $config.runtime.version -ne '3.12' -or $site.properties.httpsOnly -ne $true -or $site.properties.serverFarmId -like '*EastUS2LinuxDynamicPlan*'){throw "Target $app is not the expected HTTPS-only Flex Consumption Python 3.12 app; stop."}
$settings=Invoke-IdentityAz -Arguments @('rest','--method','post','--url',"$siteBase/config/appsettings/list",'--url-parameters','api-version=2023-12-01')
$missing=@('CMS_SQL_SERVER','CMS_SQL_DATABASE','CMS_SQL_USER','CMS_SQL_PASSWORD','CMS_ENVIRONMENT') | Where-Object {[string]::IsNullOrWhiteSpace([string]$settings.properties.$_)}
if($missing){throw "Missing app settings: $($missing -join ', '). Run content-configure.ps1 first."}
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$out=Join-Path $repo (".deploy/content-api-$Environment-"+(Get-Date -Format 'yyyyMMddTHHmmss'))
$manifestJson=& $Python (Join-Path $PSScriptRoot 'package_content_api.py') --output $out
if($LASTEXITCODE){throw 'Packaging failed; nothing was deployed.'}
$manifest=$manifestJson | ConvertFrom-Json
[pscustomobject]@{Environment=$Environment;Target=$app;Runtime='Flex Consumption, Python 3.12';Zip=$manifest.zip;Sha256=$manifest.sha256;SizeMiB=[math]::Round($manifest.bytes/1MB,1);Files=$manifest.entries;TopLevel=$manifest.topLevel;SourceFilesShipped=@($manifest.sources.PSObject.Properties.Name);Applied=[bool]$Apply} | ConvertTo-Json
Write-Host "Command: az functionapp deployment source config-zip --name $app --resource-group $IdentityGroup --src <zip> --build-remote false"
if(!$Apply){Write-Host 'Dry run only. The package was built locally; nothing was deployed.';return}
if(!$PSCmdlet.ShouldProcess($app,"Deploy package $($manifest.sha256.Substring(0,12))")){return}
$null=Invoke-IdentityAz -Arguments @('functionapp','deployment','source','config-zip','--name',$app,'--resource-group',$IdentityGroup,'--src',$manifest.zip,'--build-remote','false','--timeout','600')
$host_=$site.properties.defaultHostName
function Get-Status([string]$path,[hashtable]$headers=@{}){
 $arguments=@('-s','-o','-','-w','\n%{http_code}','--max-time','60')
 foreach($key in $headers.Keys){$arguments+=@('-H',"$($key): $($headers[$key])")}
 $raw=& curl.exe @arguments "https://$host_$path"
 $parts=($raw -join "`n") -split "`n"
 return [pscustomobject]@{Status=[int]$parts[-1];Body=($parts[0..($parts.Count-2)] -join "`n")}
}
$functions=@()
for($i=0;$i -lt 10 -and !$functions;$i++){
 Start-Sleep -Seconds 15
 $list=Invoke-IdentityAz -Arguments @('rest','--method','get','--url',"$siteBase/functions",'--url-parameters','api-version=2023-12-01')
 $functions=@($list.value | ForEach-Object {($_.name -split '/')[-1]})
}
if($functions -notcontains 'content_api'){throw "Deployment finished but the function is not registered (found: $($functions -join ', ')). Check the deployment logs in the portal."}
$health=$null
for($i=0;$i -lt 12;$i++){
 $health=Get-Status '/v1/health'
 if($health.Status -eq 200){break}
 Start-Sleep -Seconds 15
}
if($health.Status -ne 200 -or ($health.Body | ConvertFrom-Json).status -ne 'ok'){throw "Health check failed (HTTP $($health.Status))."}
# An invalid key is rejected only after a database round trip, so 401 proves connectivity, credentials and schema; 503 would mean the database is unreachable.
$auth=$null
for($i=0;$i -lt 8;$i++){
 $auth=Get-Status '/v1/schema' @{Authorization='Bearer azk_probe_invalid'}
 if($auth.Status -eq 401){break}
 Start-Sleep -Seconds 20
}
$anon=Get-Status '/v1/schema'
$human=Get-Status '/v1/submissions/probe/approve' @{'x-ms-client-principal'='e30=';'Content-Type'='application/json'}
[pscustomobject]@{FunctionRegistered=($functions -contains 'content_api');Health=$health.Status;InvalidKeyReachesDatabaseAndIs401=($auth.Status -eq 401);NoKey=$anon.Status;GetOnHumanRoute=$human.Status} | ConvertTo-Json
if($auth.Status -ne 401 -or $anon.Status -ne 401){throw "Unexpected authentication behaviour (invalid key: $($auth.Status), no key: $($anon.Status)); the database may be unreachable (503) or the schema missing."}
Write-Host "Deployed and verified: $app (package $($manifest.sha256.Substring(0,12)))."
