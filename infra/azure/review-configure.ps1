[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$SecretsDirectory='C:/Users/ander/.codex/anderzilla-azure',
 [string]$AzureCli='az',
 [ValidatePattern('^[a-z]{2,20}:[A-Za-z0-9_.-]{8,128}$')][string[]]$AdminUserId,
 [switch]$Apply
)
# -AdminUserId aad:<userId> lists the sign-ins that receive the anderzilla_admin role from the GetRoles function (REVIEW_ADMIN_USER_IDS).
# It is an identifier, not a secret. The decision uses the provider's userId, never the e-mail.
# Application settings of the review site's managed API (database + same-origin guard). Dry run by default: reads the private
# runtime-credential file locally, prints only setting NAMES and what would change (the password shows as "(hidden)").
# Merges with any existing settings; values go to Azure only in the request body (temporary file restricted to the current user).
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$app="anderzilla-review-$Environment"
$database="anderzilla-cms-$Environment"
$server="$IdentityServer.database.windows.net"
$site=Invoke-IdentityAz -Arguments @('staticwebapp','list') | Where-Object {$_.name -eq $app -and $_.resourceGroup -eq $IdentityGroup}
$secretFile=Join-Path $SecretsDirectory "content-api-$Environment.json"
if(!(Test-Path -LiteralPath $secretFile)){throw "Runtime credential file not found: $secretFile. Run content-migrate.ps1 first."}
$secret=Get-Content -LiteralPath $secretFile -Raw | ConvertFrom-Json
if($secret.environment -ne $Environment -or $secret.database -ne $database -or $secret.server -ne $server -or ([string]$secret.password).Length -lt 32){throw 'The credential file does not match this environment or is incomplete.'}
$origin=if($site){"https://$($site.defaultHostname)"}else{'(known after the site is created)'}
$desired=[ordered]@{CMS_SQL_SERVER=$server;CMS_SQL_DATABASE=$database;CMS_SQL_USER=[string]$secret.user;CMS_SQL_PASSWORD=[string]$secret.password;CMS_ENVIRONMENT=$Environment;REVIEW_ALLOWED_ORIGIN=$origin}
if($AdminUserId){$desired['REVIEW_ADMIN_USER_IDS']=(@($AdminUserId | ForEach-Object {$_.Trim()}) -join ',')}
$hidden=@('CMS_SQL_PASSWORD')
$base="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/staticSites/$app"
$current=[ordered]@{}
if($site){
 $listed=Invoke-IdentityAz -Arguments @('rest','--method','post','--url',"$base/listAppSettings",'--url-parameters','api-version=2024-11-01')
 foreach($property in $listed.properties.PSObject.Properties){$current[$property.Name]=[string]$property.Value}
}
$rows=@()
foreach($name in $desired.Keys){
 $action=if(!$site){'add (site not created yet)'}elseif(!$current.Contains($name)){'add'}elseif($current[$name] -ceq $desired[$name]){'unchanged'}else{'change'}
 $rows+=[pscustomobject]@{Setting=$name;Action=$action;Value=$(if($hidden -contains $name){'(hidden)'}else{$desired[$name]})}
}
[pscustomobject]@{Environment=$Environment;StaticWebApp=$app;Exists=[bool]$site;Applied=[bool]$Apply;SettingsKeptUntouched=@($current.Keys | Where-Object {$_ -notin $desired.Keys})} | ConvertTo-Json
$rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
if(!$Apply){Write-Host 'Dry run only. Nothing was changed.';return}
if(!$site){throw "$app does not exist; create it first."}
if(!($rows | Where-Object {$_.Action -ne 'unchanged'})){Write-Host 'Settings already match; nothing to do.';return}
if(!$PSCmdlet.ShouldProcess($app,'Merge database and origin settings into the review site')){return}
$merged=[ordered]@{}
foreach($key in $current.Keys){$merged[$key]=$current[$key]}
foreach($key in $desired.Keys){$merged[$key]=$desired[$key]}
$body=Join-Path ([System.IO.Path]::GetTempPath()) ("review-settings-"+[guid]::NewGuid().ToString('N')+'.json')
try{
 New-Item -ItemType File -Path $body -Force | Out-Null
 & icacls.exe $body /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
 if($LASTEXITCODE){throw 'Could not restrict the temporary file permissions.'}
 @{properties=$merged} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $body -Encoding ascii
 $null=Invoke-IdentityAz -Arguments @('rest','--method','put','--url',"$base/config/appsettings",'--url-parameters','api-version=2024-11-01','--body',"@$body")
}finally{Remove-Item -LiteralPath $body -Force -ErrorAction SilentlyContinue}
$after=Invoke-IdentityAz -Arguments @('rest','--method','post','--url',"$base/listAppSettings",'--url-parameters','api-version=2024-11-01')
foreach($name in $desired.Keys){if([string]$after.properties.$name -cne $desired[$name]){throw "Setting $name was not applied correctly."}}
Write-Host "Applied and verified: $($desired.Keys -join ', ') (secret values not displayed)."
$secret=$null;$desired=$null;$merged=$null;$current=$null;$listed=$null;$after=$null
