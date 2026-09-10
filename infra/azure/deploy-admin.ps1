[CmdletBinding()]
param([string]$AzureCli='az',[string]$Python='python')
$ErrorActionPreference='Stop'
$subscription='44b76346-26bd-4cd3-a529-627e47e99e5a'
$app='anderzilla-admin-homolog'
$group='anderzilla-web'
$account = (& $AzureCli account show --subscription $subscription -o json --only-show-errors) | ConvertFrom-Json
if ($LASTEXITCODE -or $account.user.name -ne 'anderzilla@ymail.com' -or $account.tenantId -ne '3fdcb773-0842-4fb9-925e-bea17d681f83') { throw 'Wrong Azure identity.' }
$resource = (& $AzureCli staticwebapp show --name $app -g $group --subscription $subscription -o json --only-show-errors) | ConvertFrom-Json
if ($LASTEXITCODE -or $resource.sku.name -ne 'Free') { throw 'Expected existing Free admin homolog resource.' }
$out=(Resolve-Path (Join-Path $PSScriptRoot '../../apps/admin/out')).Path
$sourceApi=(Resolve-Path (Join-Path $PSScriptRoot '../../services/cms')).Path
# swa deploy skips API builds. Package Linux/CPython 3.11 wheels explicitly;
# copying a Windows virtualenv would deploy incompatible native extensions.
$api=Join-Path (Join-Path $PSScriptRoot '../../.deploy') ('admin-api-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $api -Force | Out-Null
$api=(Resolve-Path $api).Path
foreach($file in @('api.py','core.py','function_app.py','storage.py','host.json','requirements.txt')) {
  Copy-Item -LiteralPath (Join-Path $sourceApi $file) -Destination $api
}
$packages=Join-Path $api '.python_packages/lib/site-packages'
& $Python -m pip install --disable-pip-version-check --only-binary=:all: --platform manylinux_2_28_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --abi cp311 --abi abi3 --abi none --target $packages -r (Join-Path $api 'requirements.txt') --quiet
if($LASTEXITCODE -or !(Test-Path (Join-Path $packages 'pytds/__init__.py')) -or !(Test-Path (Join-Path $packages 'PIL/__init__.py'))) {throw 'Linux API dependencies were not packaged.'}
$config=Get-Content (Join-Path $out 'staticwebapp.config.json') -Raw | ConvertFrom-Json
if ($config.platform.apiRuntime -ne 'python:3.11' -or !($config.routes | Where-Object {$_.route -eq '/*' -and $_.allowedRoles -contains 'anderzilla_admin'})) { throw 'Protected admin artifact required.' }
$previous=$env:SWA_CLI_DEPLOYMENT_TOKEN
try {
  $token=& $AzureCli staticwebapp secrets list -n $app -g $group --subscription $subscription --query properties.apiKey -o tsv --only-show-errors
  if ($LASTEXITCODE -or !$token) { throw 'Could not retrieve deployment credential.' }
  $env:SWA_CLI_DEPLOYMENT_TOKEN=$token.Trim()
  $token=$null
  & npx --yes '@azure/static-web-apps-cli@2.0.10' deploy $out --app-location $out --swa-config-location $out --api-location $api --api-language python --api-version 3.11 --env production --no-use-keychain
  if ($LASTEXITCODE) { throw 'Admin deploy failed.' }
  Write-Host "Admin homolog deployed: https://$($resource.defaultHostname)"
} finally {
  $env:SWA_CLI_DEPLOYMENT_TOKEN=$previous
  $token=$null
}
