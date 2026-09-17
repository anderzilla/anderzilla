[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [Parameter(Mandatory)][string]$SettingsFile,
 [string]$AzureCli='C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd',
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
if($settings.IDENTITY_ENV -ne $Environment -or $settings.IDENTITY_SQL_SERVER -ne "$IdentityServer.database.windows.net" -or $settings.IDENTITY_SQL_DATABASE -ne $names.Database -or $settings.IDENTITY_SQL_USER -ne 'anderzilla_identity_runtime'){throw 'Private settings must target the isolated identity environment and dedicated SQL runtime user.'}
$origin=[Uri]$settings.IDENTITY_ALLOWED_ORIGIN
if($origin.Scheme -ne 'https' -or $origin.UserInfo -or $origin.AbsolutePath -ne '/' -or $origin.Query -or $origin.Fragment){throw 'An exact HTTPS frontend origin is required.'}
if($Environment -eq 'production' -and $origin.Host -ne 'anderzilla.com'){throw 'Production frontend origin must be https://anderzilla.com.'}
$apiSource=Join-Path $repo 'services/identity'
foreach($name in @('function_app.py','requirements.txt','schema.azure.sql')){if(!(Test-Path -LiteralPath (Join-Path $apiSource $name))){throw "Identity implementation missing: $name"}}
Write-Host "Target $($names.App); schema and runtime account must already be migrated. No DNS, SMTP or OAuth registration will be created."
Write-Host 'Frontend must use a same-site custom API hostname with credentials: include; backend must enforce exact credentialed CORS and OPTIONS.'
if(!$Apply){Write-Host 'Plan only. Settings values were not printed or applied.';return}
if(!$PSCmdlet.ShouldProcess($names.App,'Apply private settings and deploy isolated identity API')){return}
$stage=Join-Path (Join-Path $repo '.deploy') ('identity-api-'+[guid]::NewGuid().ToString('N'))
$static=Join-Path $stage 'static';$api=Join-Path $stage 'api';$package=Join-Path $api 'services/identity'
New-Item -ItemType Directory -Path $static,$package -Force | Out-Null
foreach($path in (Get-ChildItem -LiteralPath $apiSource -File -Filter '*.py')){
 if($path.Name -notlike 'test_*'){Copy-Item -LiteralPath $path.FullName -Destination $package}
}
Set-Content -LiteralPath (Join-Path $api 'services/__init__.py') -Value '' -Encoding utf8NoBOM
Set-Content -LiteralPath (Join-Path $package '__init__.py') -Value '' -Encoding utf8NoBOM
Set-Content -LiteralPath (Join-Path $api 'function_app.py') -Value 'from services.identity.function_app import app' -Encoding utf8NoBOM
'{"version":"2.0","logging":{"logLevel":{"default":"Warning"}}}' | Set-Content -LiteralPath (Join-Path $api 'host.json') -Encoding utf8NoBOM
$packages=Join-Path $api '.python_packages/lib/site-packages'
& $Python -m pip install --disable-pip-version-check --only-binary=:all: --platform manylinux_2_28_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --abi cp311 --abi abi3 --abi none --target $packages -r (Join-Path $apiSource 'requirements.txt') --quiet
if($LASTEXITCODE -or !(Test-Path (Join-Path $packages 'azure/functions/__init__.py'))){throw 'Linux API packaging failed.'}
'<!doctype html><html lang="en"><meta name="robots" content="noindex"><title>AnderZilla API</title><body>AnderZilla account service.</body></html>' | Set-Content -LiteralPath (Join-Path $static 'index.html') -Encoding utf8NoBOM
$config=@{platform=@{apiRuntime='python:3.11'};globalHeaders=@{'X-Robots-Tag'='noindex, nofollow, noarchive';'Cache-Control'='no-store'};routes=@(@{route='/api/account/*';allowedRoles=@('anonymous')},@{route='/api/points/*';allowedRoles=@('anonymous')},@{route='/*';statusCode=404})}
$config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $static 'staticwebapp.config.json') -Encoding utf8NoBOM
$url="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/staticSites/$($names.App)/config/appsettings?api-version=2024-11-01"
$oldToken=$env:SWA_CLI_DEPLOYMENT_TOKEN
try {
 [void](Invoke-IdentityAz -Arguments @('rest','--method','put','--url',$url,'--body',('@'+$privatePath)))
 $secrets=Invoke-IdentityAz -Arguments @('staticwebapp','secrets','list','--name',$names.App,'--resource-group',$IdentityGroup)
 $env:SWA_CLI_DEPLOYMENT_TOKEN=$secrets.properties.apiKey
 $secrets=$null
 if(!$env:SWA_CLI_DEPLOYMENT_TOKEN){throw 'Deployment credential unavailable.'}
 & npx --yes '@azure/static-web-apps-cli@2.0.10' deploy $static --app-location $static --swa-config-location $static --api-location $api --api-language python --api-version 3.11 --env production --no-use-keychain
 if($LASTEXITCODE){throw 'Identity deployment failed.'}
 Write-Host "Identity API deployed to https://$($app.defaultHostname). Verify CORS, cookie sessions and same-site custom domain before enabling frontend."
}finally{$env:SWA_CLI_DEPLOYMENT_TOKEN=$oldToken;$settings=$null;$secrets=$null}
