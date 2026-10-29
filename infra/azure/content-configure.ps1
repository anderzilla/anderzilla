[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$SecretsDirectory='C:/Users/ander/.codex/anderzilla-azure',
 [string]$AzureCli='az',
 [switch]$Apply
)
# Application settings of the content API function app for one environment.
# Default run is a dry run: it reads the private runtime-credential file locally, compares with the app's current settings
# in memory and prints only setting NAMES and what would change. Secret values are never printed, logged, placed on a command
# line or written anywhere except the request body sent to Azure (a temporary file restricted to the current user, deleted afterwards).
# Not set on purpose: AGENT_MEDIA_HOSTS (empty = the API refuses to fetch images from URLs), CMS_REVIEW_BASE (the review site does not exist yet).
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$app="anderzilla-content-api-$Environment"
$database="anderzilla-cms-$Environment"
$server="$IdentityServer.database.windows.net"
$base="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/sites/$app"
$api='api-version=2023-12-01'
$site=Invoke-IdentityAz -Arguments @('rest','--method','get','--url',"$base`?$api")
if(!$site -or $site.kind -ne 'functionapp,linux' -or $site.properties.httpsOnly -ne $true){throw "Function app $app is missing, not Linux, or HTTPS is not enforced; stop."}
$secretFile=Join-Path $SecretsDirectory "content-api-$Environment.json"
if(!(Test-Path -LiteralPath $secretFile)){throw "Runtime credential file not found: $secretFile. Run content-migrate.ps1 first."}
$secret=Get-Content -LiteralPath $secretFile -Raw | ConvertFrom-Json
if($secret.environment -ne $Environment -or $secret.database -ne $database -or $secret.server -ne $server -or $secret.user -notmatch '^[a-z][a-z0-9_]{5,40}$' -or ([string]$secret.password).Length -lt 32){throw 'The credential file does not match this environment or is incomplete; nothing was read further.'}
$desired=[ordered]@{CMS_SQL_SERVER=$server;CMS_SQL_DATABASE=$database;CMS_SQL_USER=[string]$secret.user;CMS_SQL_PASSWORD=[string]$secret.password;CMS_ENVIRONMENT=$Environment}
$secretNames=@('CMS_SQL_PASSWORD')
$listed=Invoke-IdentityAz -Arguments @('rest','--method','post','--url',"$base/config/appsettings/list`?$api")
$current=[ordered]@{}
foreach($property in $listed.properties.PSObject.Properties){$current[$property.Name]=[string]$property.Value}
$rows=@()
foreach($name in $desired.Keys){
 $action=if(!$current.Contains($name)){'add'}elseif($current[$name] -ceq $desired[$name]){'unchanged'}else{'change'}
 $rows+=[pscustomobject]@{Setting=$name;Action=$action;Value=$(if($secretNames -contains $name){'(hidden)'}else{$desired[$name]})}
}
$unmanaged=@($current.Keys | Where-Object {$_ -notin $desired.Keys})
[pscustomobject]@{Environment=$Environment;FunctionApp=$app;Applied=[bool]$Apply;SettingsKeptUntouched=$unmanaged} | ConvertTo-Json
$rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
Write-Host 'The function app restarts when settings change. No code is deployed by this script.'
if(!$Apply){Write-Host 'Dry run only. Nothing was changed.';return}
if(!($rows | Where-Object {$_.Action -ne 'unchanged'})){Write-Host 'Settings already match; nothing to do.';return}
if(!$PSCmdlet.ShouldProcess($app,'Merge CMS database settings into the function app configuration')){return}
$merged=[ordered]@{}
foreach($key in $current.Keys){$merged[$key]=$current[$key]}
foreach($key in $desired.Keys){$merged[$key]=$desired[$key]}
$body=Join-Path ([System.IO.Path]::GetTempPath()) ("content-settings-"+[guid]::NewGuid().ToString('N')+'.json')
try{
 New-Item -ItemType File -Path $body -Force | Out-Null
 & icacls.exe $body /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
 if($LASTEXITCODE){throw 'Could not restrict the temporary file permissions.'}
 @{properties=$merged} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $body -Encoding ascii
 $null=Invoke-IdentityAz -Arguments @('rest','--method','put','--url',"$base/config/appsettings`?$api",'--body',"@$body")
}finally{
 Remove-Item -LiteralPath $body -Force -ErrorAction SilentlyContinue
}
$after=Invoke-IdentityAz -Arguments @('rest','--method','post','--url',"$base/config/appsettings/list`?$api")
foreach($name in $desired.Keys){
 if([string]$after.properties.$name -cne $desired[$name]){throw "Setting $name was not applied correctly."}
}
foreach($name in $unmanaged){
 if($null -eq $after.properties.$name){throw "Existing setting $name disappeared; investigate before continuing."}
}
Write-Host "Applied and verified: $($desired.Keys -join ', ') (secret values not displayed)."
$secret=$null;$desired=$null;$merged=$null;$current=$null;$listed=$null;$after=$null
