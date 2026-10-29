[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$AzureCli='az',
 [string]$Python='python',
 [switch]$Apply
)
# Build and deploy the review site: static UI (apps/review, API base /api) plus its managed API (services/review-api, Linux wheels for
# Python 3.11, the only version Static Web Apps managed functions support). Dry run (default) builds both locally and prints the manifest;
# it does not need the Static Web App to exist and changes nothing in Azure. -Apply deploys and then checks, anonymously, that nothing is
# reachable without signing in (every route, including /api, redirects to the Microsoft login).
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$app="anderzilla-review-$Environment"
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$existing=Invoke-IdentityAz -Arguments @('staticwebapp','list') | Where-Object {$_.name -eq $app -and $_.resourceGroup -eq $IdentityGroup}
if($existing -and $existing.sku.name -ne 'Free'){throw "$app is not a Free Static Web App; stop."}
$stamp=Get-Date -Format 'yyyyMMddTHHmmss'
$work=Join-Path $repo ".deploy/review-$Environment-$stamp"
# 1. API package
$manifest=(& $Python (Join-Path $PSScriptRoot 'package_content_api.py') --profile review --output (Join-Path $work 'api-build')) | ConvertFrom-Json
if($LASTEXITCODE){throw 'API packaging failed; nothing was deployed.'}
# 2. UI build with the same-origin API base
$ui=Join-Path $repo 'apps/review'
$previous=$env:NEXT_PUBLIC_REVIEW_API_BASE
try{
 $env:NEXT_PUBLIC_REVIEW_API_BASE='/api'
 Push-Location $ui
 & npm.cmd run build | Out-Null
 if($LASTEXITCODE){throw 'UI build failed.'}
}finally{Pop-Location;$env:NEXT_PUBLIC_REVIEW_API_BASE=$previous}
$site=Join-Path $work 'site'
Copy-Item -LiteralPath (Join-Path $ui 'out') -Destination $site -Recurse
$api=$manifest.package
# 3. Static checks of what will be deployed
$config=Get-Content -LiteralPath (Join-Path $site 'staticwebapp.config.json') -Raw | ConvertFrom-Json
$open=@($config.routes | Where-Object {$_.allowedRoles -contains 'anonymous'} | ForEach-Object {$_.route})
if($config.platform.apiRuntime -ne 'python:3.11'){throw 'staticwebapp.config.json must pin python:3.11.'}
if(($open -join ',') -ne '/.auth/*'){throw "Only /.auth/* may be anonymous; found: $($open -join ', ')"}
$catchAll=$config.routes | Where-Object {$_.route -eq '/*'}
if(!$catchAll -or ($catchAll.allowedRoles -join ',') -ne 'anderzilla_admin'){throw 'The catch-all route must require exactly the anderzilla_admin role.'}
$leak=Get-ChildItem -LiteralPath $site,$api -Recurse -File -Force | Where-Object {$_.Name -match '(?i)^\.env|\.(pem|key|sqlite3?)$|cms-secrets|content-api-.*\.json$'} | Where-Object {$_.FullName -notlike '*certifi*'}
if($leak){throw "Forbidden file in the deployment: $($leak[0].Name)"}
$apiBundle=$false
if((Get-ChildItem -LiteralPath $site -Recurse -Filter *.js | Select-String -Pattern '"/api"' -SimpleMatch | Select-Object -First 1)){$apiBundle=$true}
if(!$apiBundle){throw 'The UI bundle does not use the /api base.'}
[pscustomobject]@{Environment=$Environment;Target=$app;TargetExists=[bool]$existing;ApiProfile="review, Python $($manifest.pythonVersion)";ApiSha256=$manifest.sha256;ApiFiles=$manifest.entries;ApiSizeMiB=[math]::Round($manifest.bytes/1MB,1);UiFiles=@(Get-ChildItem -LiteralPath $site -Recurse -File).Count;AnonymousRoutes=$open;CatchAllRoles=$catchAll.allowedRoles;UiUsesApiBase='/api';Staging=$work;Applied=[bool]$Apply} | ConvertTo-Json
Write-Host "Command: npx @azure/static-web-apps-cli@2.0.10 deploy <site> --app-location <site> --swa-config-location <site> --api-location <api> --api-language python --api-version 3.11 --env production (token read from az, never printed)"
if(!$existing){Write-Host "The Static Web App $app does not exist yet; create it with content-provision.ps1 (after approval)."}
if(!$Apply){Write-Host 'Dry run only. Everything was built locally; nothing was deployed.';return}
if(!$existing){throw "$app does not exist; create it first."}
if(!$PSCmdlet.ShouldProcess($app,"Deploy review site (API $($manifest.sha256.Substring(0,12)))")){return}
$old=$env:SWA_CLI_DEPLOYMENT_TOKEN
try{
 $token=(& $AzureCli staticwebapp secrets list --name $app --resource-group $IdentityGroup --subscription $IdentitySubscription --query properties.apiKey --output tsv --only-show-errors)
 if($LASTEXITCODE -or [string]::IsNullOrWhiteSpace($token)){throw 'Could not read the deployment credential.'}
 $env:SWA_CLI_DEPLOYMENT_TOKEN=$token.Trim();$token=$null
 # The SWA CLI prints progress on stderr; with ErrorActionPreference=Stop PowerShell would turn that into a terminating error
 # and abort before the verification below (seen on 2026-10-29: the deploy had completed). Judge only by the exit code.
 $stopPreference=$ErrorActionPreference
 $ErrorActionPreference='Continue'
 try{
  & npx --yes '@azure/static-web-apps-cli@2.0.10' deploy $site --app-location $site --swa-config-location $site --api-location $api --api-language python --api-version 3.11 --env production --no-use-keychain 2>&1 | ForEach-Object {Write-Host $_.ToString()}
  $deployExit=$LASTEXITCODE
 }finally{$ErrorActionPreference=$stopPreference}
 if($deployExit){throw "Review deployment failed (exit code $deployExit)."}
}finally{$env:SWA_CLI_DEPLOYMENT_TOKEN=$old;$token=$null}
$hostName=$existing.defaultHostname
function Get-Redirect([string]$path){
 $raw=& curl.exe -s -o NUL -w '%{http_code} %{redirect_url}' --max-time 60 "https://$hostName$path"
 return [string]$raw
}
$checks=@{}
for($i=0;$i -lt 8;$i++){
 Start-Sleep -Seconds 15
 $checks['/']=Get-Redirect '/'
 if($checks['/'] -like '302 *'){break}
}
foreach($path in '/api/v1/health','/api/v1/submissions','/brand/lettering.webp'){$checks[$path]=Get-Redirect $path}
$checks.GetEnumerator() | Sort-Object Name | ForEach-Object {Write-Host ("{0,-24} {1}" -f $_.Name,$_.Value)}
foreach($entry in $checks.GetEnumerator()){
 if($entry.Value -notmatch '^302 https://[^ ]*/\.auth/login/aad'){throw "Anonymous access to $($entry.Name) was not redirected to the Microsoft login ($($entry.Value)); take the site down and investigate."}
}
Write-Host "Deployed: https://$hostName . Every anonymous request is redirected to the Microsoft login. Sign-in still needs the invitation step (review-invite.ps1)."
