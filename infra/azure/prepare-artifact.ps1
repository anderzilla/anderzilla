[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Destination,
    [Parameter(Mandatory)][ValidateSet('homolog', 'production', 'preview')][string]$Environment
)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path -LiteralPath $Source).Path
if (!(Test-Path -LiteralPath (Join-Path $sourcePath 'index.html'))) { throw 'Static export index.html missing. Run npm run build in apps/web.' }
$releaseMarker=Join-Path $sourcePath 'cms-release.json'
if($Environment -eq 'production' -and (Test-Path -LiteralPath $releaseMarker)) {
    $cmsRelease=Get-Content -LiteralPath $releaseMarker -Raw | ConvertFrom-Json
    if($cmsRelease.containsDemo -ne $false) {throw 'CMS artifact contains demonstration data or has no explicit production classification.'}
}
if (Test-Path -LiteralPath $Destination) { throw 'Destination must be a new directory.' }
New-Item -ItemType Directory -Path $Destination | Out-Null
Get-ChildItem -LiteralPath $sourcePath -Force | Copy-Item -Destination $Destination -Recurse
$configPath = Join-Path $Destination 'staticwebapp.config.json'
if (!(Test-Path -LiteralPath $configPath)) { throw 'Static Web Apps configuration missing.' }
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -AsHashtable
if ($Environment -eq 'homolog') {
    # A custom invited role is required: ordinary authenticated visitors cannot enter.
    # Authentication system routes stay reachable to accept the owner invitation.
    $config.routes = @(
        @{ route = '/.auth/*'; allowedRoles = @('anonymous') },
        @{ route = '/*'; allowedRoles = @('anderzilla_reviewer') }
    )
    if (!$config.ContainsKey('globalHeaders')) { $config.globalHeaders = @{} }
    $config.globalHeaders['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    $config.globalHeaders['Cache-Control'] = 'no-store'
    # A public fallback must not bypass restricted routes.
    $config.Remove('navigationFallback') | Out-Null
    $config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $configPath -Encoding utf8NoBOM
}
if ($Environment -eq 'preview') {
    # Public visual sample only. Isolated named slot, never the custom-domain deployment.
    # No accounts, private data, functioning rewards or administration in this artifact.
    if (!$config.ContainsKey('globalHeaders')) { $config.globalHeaders = @{} }
    $config.globalHeaders['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    $config.globalHeaders['Cache-Control'] = 'no-store'
    $config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $configPath -Encoding utf8NoBOM
    "User-agent: *`nDisallow: /" | Set-Content -LiteralPath (Join-Path $Destination 'robots.txt') -Encoding utf8NoBOM
}
Write-Host "Prepared $Environment artifact: $Destination"
