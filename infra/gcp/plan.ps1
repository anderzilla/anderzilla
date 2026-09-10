param([Parameter(Mandatory=$true)][string]$VarFile)
$ErrorActionPreference = 'Stop'
$resolvedVars = (Resolve-Path -LiteralPath $VarFile).Path
$credentialOverrides = @(Get-ChildItem Env: | Where-Object {
    $_.Name -like 'CLOUDSDK_AUTH_*' -or $_.Name -in @('GOOGLE_IMPERSONATE_SERVICE_ACCOUNT', 'GOOGLE_CREDENTIALS', 'GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_CLOUD_KEYFILE_JSON', 'GCLOUD_KEYFILE_JSON')
})
if ($credentialOverrides.Count -gt 0) { throw 'Remove inherited credential/impersonation overrides before planning.' }
$authJson = (& gcloud --configuration=anderzilla config list auth --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'Could not verify gcloud authentication configuration.' }
$authConfig = $authJson | ConvertFrom-Json
if ($authConfig.auth.impersonate_service_account -or $authConfig.auth.access_token_file -or $authConfig.auth.credential_file_override) {
    throw 'Remove gcloud impersonation and credential overrides from configuration anderzilla.'
}
$account = (& gcloud --configuration=anderzilla config get-value account 2>$null | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $account -ne 'player.one@anderzilla.com') {
    throw 'Authenticate player.one@anderzilla.com in configuration anderzilla first.'
}
# Explicit short-lived credential prevents inheriting unrelated ADC. Never log it.
$previousToken = $env:GOOGLE_OAUTH_ACCESS_TOKEN
try {
    $token = (& gcloud --configuration=anderzilla --account=player.one@anderzilla.com auth print-access-token 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) { throw 'Could not obtain the authorized account credential.' }
    $env:GOOGLE_OAUTH_ACCESS_TOKEN = $token
    & terraform "-chdir=$PSScriptRoot" plan "-var-file=$resolvedVars"
    if ($LASTEXITCODE -ne 0) { throw 'Terraform plan failed.' }
} finally {
    $env:GOOGLE_OAUTH_ACCESS_TOKEN = $previousToken
    $token = $null
}
