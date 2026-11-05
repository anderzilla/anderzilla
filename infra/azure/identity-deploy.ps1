[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [Parameter(Mandatory)][string]$SettingsFile,
 [string]$AzureCli='az',
 [string]$Python='python',
 [switch]$Apply
)
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$names=Get-IdentityNames $Environment
$app=Invoke-IdentityAz -Arguments @('staticwebapp','show','--name',$names.App,'--resource-group',$IdentityGroup)
if($app.sku.name -ne 'Free'){throw 'Identity requires the existing Free SWA.'}
Assert-IdentityDatabase (Invoke-IdentityAz -Arguments @('sql','db','show','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup))
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$privatePath=(Resolve-Path -LiteralPath $SettingsFile).Path
if($privatePath.StartsWith($repo+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Settings must be stored outside the repository.'}
$settings=(Get-Content -LiteralPath $privatePath -Raw | ConvertFrom-Json).properties
foreach($key in @('IDENTITY_ENV','IDENTITY_ALLOWED_ORIGIN','IDENTITY_SQL_SERVER','IDENTITY_SQL_DATABASE','IDENTITY_SQL_USER','IDENTITY_SQL_PASSWORD')){
 if(!$settings.$key){throw "Required setting missing: $key"}
}
if($settings.IDENTITY_ENV -ne $Environment -or $settings.IDENTITY_SQL_SERVER -ne "$IdentityServer.database.windows.net" -or $settings.IDENTITY_SQL_DATABASE -ne $names.Database -or $settings.IDENTITY_SQL_USER -notin @('anderzilla_identity_runtime','anderzilla_clerk_runtime')){throw 'Private settings must target the isolated identity environment and dedicated SQL runtime user.'}
if($settings.IDENTITY_SQL_USER -eq 'anderzilla_clerk_runtime' -and $settings.IDENTITY_AUTH_PROVIDER -ne 'clerk'){throw 'The isolated Clerk SQL user requires Clerk mode.'}
$origins=@($settings.IDENTITY_ALLOWED_ORIGIN.Split(',') | ForEach-Object {$_.Trim().TrimEnd('/')})
foreach($originText in $origins){
 $origin=[Uri]$originText
 $loopback=$Environment -eq 'homolog' -and $settings.IDENTITY_AUTH_PROVIDER -eq 'clerk' -and $origin.Scheme -eq 'http' -and $origin.Host -in @('localhost','127.0.0.1')
 if(($origin.Scheme -ne 'https' -and !$loopback) -or $origin.UserInfo -or $origin.AbsolutePath -ne '/' -or $origin.Query -or $origin.Fragment){throw 'An exact HTTPS frontend origin is required (homolog Clerk also allows explicit loopback origins).'}
}
if($Environment -eq 'production' -and $origins -notcontains 'https://anderzilla.com'){throw 'Production frontend origin must include https://anderzilla.com.'}
$apiSource=Join-Path $repo 'services/identity'
foreach($name in @('function_app.py','requirements.txt','schema.azure.sql')){if(!(Test-Path -LiteralPath (Join-Path $apiSource $name))){throw "Identity implementation missing: $name"}}
Write-Host "Target $($names.App); schema and runtime account must already be migrated. No DNS, SMTP or OAuth registration will be created."
if($settings.IDENTITY_AUTH_PROVIDER -eq 'clerk'){
 Write-Host 'Clerk uses bearer tokens with credentials omitted; verify the issuer, authorized frontend origin and signed webhook configuration.'
}else{
 Write-Host 'Native frontend must use a same-site custom API hostname with credentials: include and exact credentialed CORS.'
}
if(!$Apply){Write-Host 'Plan only. Settings values were not printed or applied.';return}
if(!$PSCmdlet.ShouldProcess($names.App,'Apply private settings and deploy isolated identity API')){return}
# Keep native uploader staging and temporary archives on the local volume.
$stage=Join-Path ([IO.Path]::GetTempPath()) ('anderzilla-identity-'+[guid]::NewGuid().ToString('N'))
$static=Join-Path $stage 'static';$api=Join-Path $stage 'api';$package=Join-Path $api 'services/identity'
New-Item -ItemType Directory -Path $static,$package -Force | Out-Null
foreach($path in (Get-ChildItem -LiteralPath $apiSource -File -Filter '*.py')){
 if($path.Name -notlike 'test_*'){Copy-Item -LiteralPath $path.FullName -Destination $package}
}
Set-Content -LiteralPath (Join-Path $api 'services/__init__.py') -Value '' -Encoding utf8NoBOM
Set-Content -LiteralPath (Join-Path $package '__init__.py') -Value '' -Encoding utf8NoBOM
# Explicit HTTP binding metadata avoids depending on worker indexing settings,
# which SWA reserves and does not let this deployment configure.
foreach($routeName in @('account','points')){
 $bindingDirectory=Join-Path $api ($routeName+'Http')
 New-Item -ItemType Directory -Path $bindingDirectory -Force | Out-Null
 'from services.identity.function_app import identity_api as main' | Set-Content -LiteralPath (Join-Path $bindingDirectory '__init__.py') -Encoding utf8NoBOM
 @{scriptFile='__init__.py';bindings=@(@{authLevel='anonymous';type='httpTrigger';direction='in';name='req';route=($routeName+'/{*path}');methods=@('get','post','patch','delete','options')},@{type='http';direction='out';name='$return'})} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $bindingDirectory 'function.json') -Encoding utf8NoBOM
}
Copy-Item -LiteralPath (Join-Path $apiSource 'requirements.txt') -Destination (Join-Path $api 'requirements.txt')
'{"version":"2.0","logging":{"logLevel":{"default":"Warning"}}}' | Set-Content -LiteralPath (Join-Path $api 'host.json') -Encoding utf8NoBOM
$packages=Join-Path $api '.python_packages/lib/site-packages'
& $Python -m pip install --disable-pip-version-check --only-binary=:all: --platform manylinux_2_28_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --abi cp311 --abi abi3 --abi none --target $packages -r (Join-Path $apiSource 'requirements.txt') --quiet
if($LASTEXITCODE -or !(Test-Path (Join-Path $packages 'azure/functions/__init__.py'))){throw 'Linux API packaging failed.'}
'<!doctype html><html lang="en"><meta name="robots" content="noindex"><title>AnderZilla API</title><body>AnderZilla account service.</body></html>' | Set-Content -LiteralPath (Join-Path $static 'index.html') -Encoding utf8NoBOM
$config=@{platform=@{apiRuntime='python:3.11'};globalHeaders=@{'X-Robots-Tag'='noindex, nofollow, noarchive';'Cache-Control'='no-store'};routes=@(@{route='/api/account/*';allowedRoles=@('anonymous')},@{route='/api/points/*';allowedRoles=@('anonymous')},@{route='/*';statusCode=404})}
$config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $static 'staticwebapp.config.json') -Encoding utf8NoBOM
$url="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/staticSites/$($names.App)/config/appsettings?api-version=2024-11-01"
$oldToken=$env:SWA_CLI_DEPLOYMENT_TOKEN
$runtimeSettingsPath=[System.IO.Path]::GetTempFileName()
try {
 # Managed SWA Functions reserve IDENTITY_*; keep canonical private settings
 # and send only safe aliases to that host. Dedicated Functions are unchanged.
 $runtimeSettings=@{}
 foreach($property in $settings.PSObject.Properties){
  $name=if($property.Name.StartsWith('IDENTITY_')){'AZ_ACCOUNT_'+$property.Name.Substring(9)}else{$property.Name}
  $runtimeSettings[$name]=$property.Value
 }
 @{properties=$runtimeSettings} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $runtimeSettingsPath -Encoding utf8NoBOM
 [void](Invoke-IdentityAz -Arguments @('rest','--method','put','--url',$url,'--body',('@'+$runtimeSettingsPath)))
 $secrets=Invoke-IdentityAz -Arguments @('staticwebapp','secrets','list','--name',$names.App,'--resource-group',$IdentityGroup)
 $env:SWA_CLI_DEPLOYMENT_TOKEN=$secrets.properties.apiKey
 $secrets=$null
 if(!$env:SWA_CLI_DEPLOYMENT_TOKEN){throw 'Deployment credential unavailable.'}
 Push-Location $stage
 try {
  & npx --yes '@azure/static-web-apps-cli@2.0.10' deploy $static --app-location $static --swa-config-location $static --api-location $api --api-language python --api-version 3.11 --env production --no-use-keychain
 } finally { Pop-Location }
 if($LASTEXITCODE){throw 'Identity deployment failed.'}
 Write-Host "Identity API deployed to https://$($app.defaultHostname). Verify the configured provider, authorization, CORS and lifecycle callbacks before enabling frontend."
}finally{
 $env:SWA_CLI_DEPLOYMENT_TOKEN=$oldToken;$settings=$null;$secrets=$null;$runtimeSettings=$null
 if(Test-Path -LiteralPath $runtimeSettingsPath){Remove-Item -LiteralPath $runtimeSettingsPath -Force}
}
