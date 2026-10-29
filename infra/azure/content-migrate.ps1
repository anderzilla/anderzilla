[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [System.Management.Automation.PSCredential]$AdminCredential,
 [ValidatePattern('^[a-z][a-z0-9_]{5,40}$')][string]$RuntimeUser='anderzilla_content_runtime',
 [string]$SecretsDirectory='C:/Users/ander/.codex/anderzilla-azure',
 [switch]$RotateRuntimePassword,
 [string]$AzureCli='az',
 [switch]$Apply
)
# Additive schema + least-privilege runtime user for the content API database of one environment.
# Default run is a dry run: it validates the SQL files and the Azure target, prints the plan, and never opens a database connection.
# -Apply asks for the SQL administrator credential interactively (Get-Credential) unless -AdminCredential is passed; nothing secret is
# read from the repository, printed, or put on a command line. The generated runtime password is written only to a private file
# outside the repository (restricted to the current Windows user) and is never displayed.
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$database="anderzilla-cms-$Environment"
$server="$IdentityServer.database.windows.net"
Assert-IdentityDatabase (Invoke-IdentityAz -Arguments @('sql','db','show','--name',$database,'--server',$IdentityServer,'--resource-group',$IdentityGroup))
$schema=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../services/cms/schema.azure.sql') -Raw
$grants=(Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../services/cms/runtime-permissions.azure.sql') -Raw) -replace 'anderzilla_cms_runtime',$RuntimeUser
# Static checks: the migration may only add things and only grant to the runtime user.
$tables=@([regex]::Matches($schema,'CREATE TABLE (\w+)\(') | ForEach-Object {$_.Groups[1].Value})
if($schema -match '(?i)\b(DROP|TRUNCATE|DELETE\s+FROM|ALTER\s+TABLE|EXEC|xp_)\b'){throw 'Schema contains a destructive or unexpected statement.'}
foreach($line in ($schema -split "\r?\n" | Where-Object {$_.Trim()})){ if($line -notmatch '^IF (OBJECT_ID|NOT EXISTS)'){throw "Schema line is not idempotent: $($line.Substring(0,[Math]::Min(60,$line.Length)))"} }
$grantLines=@($grants -split "\r?\n" | Where-Object {$_.Trim() -and $_ -notmatch '^\s*--'})
foreach($line in $grantLines){
 if($line -notmatch "^(GRANT|DENY) .* TO $RuntimeUser;$"){throw "Unexpected permission statement: $line"}
 if($line -match '(?i)\b(db_owner|db_datawriter|CONTROL|ALTER|EXECUTE)\b'){throw "Permission is broader than allowed: $line"}
}
foreach($table in $tables){ if(!($grantLines | Where-Object {$_ -like "GRANT SELECT*dbo.$table *"})){throw "No SELECT grant for $table."} }
$secretFile=Join-Path $SecretsDirectory "content-api-$Environment.json"
[pscustomobject]@{Environment=$Environment;Server=$server;Database=$database;DatabaseTier='SQL free offer (verified)';TablesIdempotent=$tables.Count;GrantStatements=$grantLines.Count;RuntimeUser=$RuntimeUser;SecretFile=$secretFile;SecretFileExists=(Test-Path -LiteralPath $secretFile);Applied=[bool]$Apply} | ConvertTo-Json
Write-Host "Tables created only if missing: $($tables -join ', ')"
Write-Host "Runtime user: created only if missing (password generated locally, 48 random chars, stored only in the private file above). An existing user keeps its password unless -RotateRuntimePassword is passed."
Write-Host 'Checked inside the transaction before commit: the runtime user can insert and update records, cannot delete anything, cannot update audit/revisions/requests, can only update the document column of agent_keys, and is not db_owner. Any failure rolls everything back.'
Write-Host 'Network: the SQL server firewall must allow the public IP of the machine that runs -Apply (current rules: Azure services and one fixed bootstrap IP). Adding a rule is a separate, explicit step.'
if(!$Apply){Write-Host 'Dry run only. No connection was opened and nothing was changed.';return}
if(!$PSCmdlet.ShouldProcess("$server/$database",'Apply additive content schema and create/update the runtime user')){return}
if(!$AdminCredential){$AdminCredential=Get-Credential -Message "SQL administrator for $server (database $database)"}
if(!$AdminCredential){throw 'A SQL administrator credential is required.'}
$builder=[System.Data.SqlClient.SqlConnectionStringBuilder]::new()
$builder['Data Source']=$server;$builder['Initial Catalog']=$database
$builder['User ID']=$AdminCredential.UserName;$builder['Password']=$AdminCredential.GetNetworkCredential().Password
$builder['Encrypt']=$true;$builder['TrustServerCertificate']=$false;$builder['Connect Timeout']=90
$connection=[System.Data.SqlClient.SqlConnection]::new($builder.ConnectionString)
$wroteSecret=$false
function Invoke-Sql($connection,$transaction,[string]$text,[hashtable]$parameters=@{}){
 $command=$connection.CreateCommand();$command.Transaction=$transaction;$command.CommandTimeout=120;$command.CommandText=$text
 foreach($key in $parameters.Keys){[void]$command.Parameters.AddWithValue("@$key",$parameters[$key])}
 try{return $command.ExecuteScalar()}finally{$command.Dispose()}
}
try{
 $connection.Open()
 $transaction=$connection.BeginTransaction()
 try{
  $exists=[int](Invoke-Sql $connection $transaction 'SELECT COUNT(1) FROM sys.database_principals WHERE name=@name' @{name=$RuntimeUser})
  $password=$null
  if(!$exists -or $RotateRuntimePassword){
   $bytes=New-Object byte[] 48
   $rng=[System.Security.Cryptography.RandomNumberGenerator]::Create();$rng.GetBytes($bytes);$rng.Dispose()
   $alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
   $password=-join ($bytes | ForEach-Object {$alphabet[$_ % 64]})
   $verb=if($exists){'ALTER'}else{'CREATE'}
   [void](Invoke-Sql $connection $transaction "$verb USER [$RuntimeUser] WITH PASSWORD=N'$password';")
  }
  [void](Invoke-Sql $connection $transaction $schema)
  [void](Invoke-Sql $connection $transaction $grants)
  $present=@()
  $reader=$connection.CreateCommand();$reader.Transaction=$transaction;$reader.CommandText='SELECT name FROM sys.tables'
  $rd=$reader.ExecuteReader();while($rd.Read()){$present+=$rd.GetString(0)};$rd.Close();$reader.Dispose()
  $missing=@($tables | Where-Object {$_ -notin $present})
  if($missing.Count){throw "Tables missing after migration: $($missing -join ', ')"}
  $checks=@(
   @('dbo.cms_records','INSERT',1),@('dbo.cms_records','UPDATE',1),@('dbo.cms_records','DELETE',0),
   @('dbo.cms_audit','INSERT',1),@('dbo.cms_audit','UPDATE',0),@('dbo.cms_revisions','UPDATE',0),
   @('dbo.agent_requests','INSERT',1),@('dbo.agent_requests','UPDATE',0),@('dbo.agent_requests','DELETE',0),
   @('dbo.submissions','UPDATE',1),@('dbo.submissions','DELETE',0)
  )
  foreach($check in $checks){
   $value=[int](Invoke-Sql $connection $transaction "EXECUTE AS USER=N'$RuntimeUser'; SELECT HAS_PERMS_BY_NAME(@object,'OBJECT',@perm); REVERT;" @{object=$check[0];perm=$check[1]})
   if($value -ne $check[2]){throw "Permission check failed: $($check[1]) on $($check[0]) is $value, expected $($check[2])."}
  }
  $document=[int](Invoke-Sql $connection $transaction "EXECUTE AS USER=N'$RuntimeUser'; SELECT HAS_PERMS_BY_NAME('dbo.agent_keys','OBJECT','UPDATE','document','COLUMN'); REVERT;")
  $hash=[int](Invoke-Sql $connection $transaction "EXECUTE AS USER=N'$RuntimeUser'; SELECT HAS_PERMS_BY_NAME('dbo.agent_keys','OBJECT','UPDATE','key_hash','COLUMN'); REVERT;")
  if($document -ne 1 -or $hash -ne 0){throw 'agent_keys: the runtime user must update only the document column.'}
  $owner=[int](Invoke-Sql $connection $transaction "SELECT IS_ROLEMEMBER('db_owner',@name)" @{name=$RuntimeUser})
  if($owner -eq 1){throw 'Runtime user must not be db_owner.'}
  if($password){
   New-Item -ItemType Directory -Force -Path $SecretsDirectory | Out-Null
   [pscustomobject]@{environment=$Environment;server=$server;database=$database;user=$RuntimeUser;password=$password;createdAt=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $secretFile -Encoding ascii
   $wroteSecret=$true
   & icacls.exe $secretFile /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
   if($LASTEXITCODE){throw 'Could not restrict the secret file permissions.'}
  }
  $transaction.Commit()
  Write-Host 'Content schema and runtime grants applied; permission checks passed.'
  if($password){Write-Host "Runtime credential saved privately to $secretFile (not displayed)."}elseif($exists){Write-Host 'Runtime user already existed; its password was not changed and no secret file was written.'}
 }catch{
  $failure=$_.Exception
  while($failure.InnerException){$failure=$failure.InnerException}
  $transaction.Rollback()
  if($wroteSecret){Remove-Item -LiteralPath $secretFile -Force -ErrorAction SilentlyContinue}
  $number=if($failure.PSObject.Properties.Name -contains 'Number'){$failure.Number}else{'n/a'}
  throw "Content migration rolled back (SQL error $number): $($failure.Message)"
 }
}finally{
 $connection.Dispose();$builder.Clear();$password=$null;$AdminCredential=$null
}
