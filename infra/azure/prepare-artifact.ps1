[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Destination,
    [Parameter(Mandatory)][ValidateSet('homolog', 'production', 'preview')][string]$Environment
)
$ErrorActionPreference = 'Stop'
function Set-Utf8NoBom([string]$Path, [string]$Content) {
    # Set-Content -Encoding utf8NoBOM is pwsh-only; Windows PowerShell 5.1 lacks that
    # enum value and its UTF8 always writes a BOM. This works identically on both.
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}
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
# PSCustomObject throughout (not -AsHashtable): Windows PowerShell 5.1 has no
# -AsHashtable, and pwsh is not assumed to be installed. Add-Member/-Force sets
# or overwrites a property either way; PSObject.Properties.Remove drops one.
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
function Set-NoindexHeaders($cfg) {
    if (-not $cfg.PSObject.Properties.Name.Contains('globalHeaders')) {
        $cfg | Add-Member -NotePropertyName globalHeaders -NotePropertyValue ([pscustomobject]@{})
    }
    $cfg.globalHeaders | Add-Member -Force -NotePropertyName 'X-Robots-Tag' -NotePropertyValue 'noindex, nofollow, noarchive'
    $cfg.globalHeaders | Add-Member -Force -NotePropertyName 'Cache-Control' -NotePropertyValue 'no-store'
}
if ($Environment -eq 'homolog') {
    # A custom invited role is required: ordinary authenticated visitors cannot enter.
    # Authentication system routes stay reachable to accept the owner invitation.
    $config | Add-Member -Force -NotePropertyName routes -NotePropertyValue @(
        [pscustomobject]@{ route = '/.auth/*'; allowedRoles = @('anonymous') },
        [pscustomobject]@{ route = '/*'; allowedRoles = @('anderzilla_reviewer') }
    )
    Set-NoindexHeaders $config
    # A public fallback must not bypass restricted routes.
    if ($config.PSObject.Properties.Name.Contains('navigationFallback')) { $config.PSObject.Properties.Remove('navigationFallback') }
    Set-Utf8NoBom -Path $configPath -Content ($config | ConvertTo-Json -Depth 30)
}
if ($Environment -eq 'preview') {
    # Public visual sample only. Isolated named slot, never the custom-domain deployment.
    # No accounts, private data, functioning rewards or administration in this artifact.
    Set-NoindexHeaders $config
    Set-Utf8NoBom -Path $configPath -Content ($config | ConvertTo-Json -Depth 30)
    Set-Utf8NoBom -Path (Join-Path $Destination 'robots.txt') -Content "User-agent: *`nDisallow: /"
}
Write-Host "Prepared $Environment artifact: $Destination"
