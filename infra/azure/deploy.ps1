[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('homolog', 'production')][string]$Environment,
    [string]$ArtifactPath = (Join-Path $PSScriptRoot '../../apps/web/out'),
    [string]$AzureCli = 'az'
)
$ErrorActionPreference = 'Stop'
$subscription = '44b76346-26bd-4cd3-a529-627e47e99e5a'
$tenant = '3fdcb773-0842-4fb9-925e-bea17d681f83'
$group = 'anderzilla-web'
$app = "anderzilla-web-$Environment"
$accountJson = & $AzureCli account show --subscription $subscription --output json --only-show-errors
if ($LASTEXITCODE -ne 0) { throw 'Azure account inspection failed.' }
$account = $accountJson | ConvertFrom-Json
if ($account.id -ne $subscription -or $account.tenantId -ne $tenant -or $account.user.name -ne 'anderzilla@ymail.com') {
    throw 'Wrong Azure identity, tenant or subscription; use anderzilla@ymail.com.'
}
$resourceJson = & $AzureCli staticwebapp show --subscription $subscription --resource-group $group --name $app --output json --only-show-errors
if ($LASTEXITCODE -ne 0) { throw 'Expected existing Static Web App not found. This script does not create resources.' }
$resource = $resourceJson | ConvertFrom-Json
if ($resource.sku.name -ne 'Free') { throw 'Only the Free tier is authorized by this deployment script.' }
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$stage = Join-Path $tempRoot ("anderzilla-swa-" + [guid]::NewGuid().ToString('N'))
$previousToken = $env:SWA_CLI_DEPLOYMENT_TOKEN
try {
    & (Join-Path $PSScriptRoot 'prepare-artifact.ps1') -Source $ArtifactPath -Destination $stage -Environment $Environment
    $token = & $AzureCli staticwebapp secrets list --subscription $subscription --resource-group $group --name $app --query properties.apiKey --output tsv --only-show-errors
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) { throw 'Could not retrieve deployment credential.' }
    $env:SWA_CLI_DEPLOYMENT_TOKEN = $token.Trim()
    $token = $null
    & npx --yes '@azure/static-web-apps-cli@2.0.10' deploy $stage --app-location $stage --swa-config-location $stage --env production --no-use-keychain
    if ($LASTEXITCODE -ne 0) { throw 'Static Web Apps deployment failed.' }
    Write-Host "Published $Environment to https://$($resource.defaultHostname). Verify HTTP and role access before changing DNS."
} finally {
    $env:SWA_CLI_DEPLOYMENT_TOKEN = $previousToken
    $token = $null
    # Verify the generated absolute target before recursive cleanup.
    $resolvedStage = [System.IO.Path]::GetFullPath($stage)
    if ($resolvedStage.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and
        [System.IO.Path]::GetFileName($resolvedStage) -match '^anderzilla-swa-[a-f0-9]{32}$' -and
        (Test-Path -LiteralPath $resolvedStage)) {
        Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    }
}
