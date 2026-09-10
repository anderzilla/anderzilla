[CmdletBinding(SupportsShouldProcess)]
param(
  [string]$AzureCli='az',
  [System.Management.Automation.PSCredential]$AdminCredential,
  [string]$SecretsPath='C:/Users/ander/.codex/anderzilla-azure/cms-secrets.json'
)
$ErrorActionPreference='Stop'
$subscription='44b76346-26bd-4cd3-a529-627e47e99e5a'
$tenant='3fdcb773-0842-4fb9-925e-bea17d681f83'
$group='anderzilla-web'
$app='anderzilla-admin-homolog'
$account = (& $AzureCli account show --subscription $subscription -o json --only-show-errors) | ConvertFrom-Json
if ($LASTEXITCODE -or $account.user.name -ne 'anderzilla@ymail.com' -or $account.tenantId -ne $tenant) {
  throw 'Wrong Azure identity.'
}
$raw = & $AzureCli staticwebapp appsettings list -n $app -g $group --subscription $subscription -o json --only-show-errors
if ($LASTEXITCODE) { throw 'Could not read protected CMS configuration.' }
$settings = ($raw | ConvertFrom-Json).properties
$required = @('CMS_SQL_SERVER','CMS_SQL_DATABASE','CMS_SQL_USER','CMS_SQL_PASSWORD')
foreach ($name in $required) { if (-not $settings.$name) { throw "Missing CMS setting: $name" } }
if (-not $AdminCredential) {
  if (-not (Test-Path -LiteralPath $SecretsPath)) { throw 'Provide AdminCredential or the private CMS secrets file.' }
  $secret = Get-Content -Raw -LiteralPath $SecretsPath | ConvertFrom-Json
  $secretServer = if ($secret.server -match '\.') { $secret.server } else { $secret.server + '.database.windows.net' }
  if ($secretServer -ne $settings.CMS_SQL_SERVER -or $secret.database -ne $settings.CMS_SQL_DATABASE) {
    throw 'Private credential target does not match the protected CMS configuration.'
  }
  $securePassword = ConvertTo-SecureString $secret.password -AsPlainText -Force
  $AdminCredential = [System.Management.Automation.PSCredential]::new($secret.user,$securePassword)
}
$schema = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot '../../services/cms/schema.azure.sql')
$permissions = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot '../../services/cms/runtime-permissions.azure.sql')
$builder = [System.Data.SqlClient.SqlConnectionStringBuilder]::new()
$builder['Data Source'] = $settings.CMS_SQL_SERVER
$builder['Initial Catalog'] = $settings.CMS_SQL_DATABASE
$builder['User ID'] = $AdminCredential.UserName
$builder['Password'] = $AdminCredential.GetNetworkCredential().Password
$builder['Encrypt'] = $true
$builder['TrustServerCertificate'] = $false
$builder['Connect Timeout'] = 60
$connection = [System.Data.SqlClient.SqlConnection]::new($builder.ConnectionString)
try {
  if (-not $PSCmdlet.ShouldProcess("$($settings.CMS_SQL_SERVER)/$($settings.CMS_SQL_DATABASE)", 'Apply additive CMS schema and runtime grants')) { return }
  $connection.Open()
  $transaction = $connection.BeginTransaction()
  try {
    foreach ($text in @($schema,$permissions)) {
      $command = $connection.CreateCommand()
      $command.Transaction = $transaction
      $command.CommandTimeout = 60
      $command.CommandText = $text
      [void]$command.ExecuteNonQuery()
      $command.Dispose()
    }
    $transaction.Commit()
    Write-Host 'CMS schema and least-privilege grants applied.'
  } catch {
    $transaction.Rollback()
    throw
  }
} finally {
  if ($connection) { $connection.Dispose() }
  $builder.Clear()
  $AdminCredential = $null
  $securePassword = $null
  $secret = $null
  $settings = $null
  $raw = $null
}
