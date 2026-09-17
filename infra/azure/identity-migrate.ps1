[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [Parameter(Mandatory)][System.Management.Automation.PSCredential]$AdminCredential,
 [Parameter(Mandatory)][System.Security.SecureString]$RuntimePassword,
 [string]$AzureCli='C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd'
)
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$names=Get-IdentityNames $Environment
Assert-IdentityDatabase (Invoke-IdentityAz -Arguments @('sql','db','show','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup))
$schema=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../services/identity/schema.azure.sql') -Raw
$grants=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../services/identity/runtime-permissions.azure.sql') -Raw
$builder=[System.Data.SqlClient.SqlConnectionStringBuilder]::new()
$builder['Data Source']="$IdentityServer.database.windows.net"
$builder['Initial Catalog']=$names.Database
$builder['User ID']=$AdminCredential.UserName
$builder['Password']=$AdminCredential.GetNetworkCredential().Password
$builder['Encrypt']=$true
$builder['TrustServerCertificate']=$false
$builder['Connect Timeout']=60
$connection=[System.Data.SqlClient.SqlConnection]::new($builder.ConnectionString)
try {
 if(!$PSCmdlet.ShouldProcess($names.Database,'Apply identity schema and dedicated runtime grants')){return}
 $connection.Open()
 $transaction=$connection.BeginTransaction()
 try {
  $runtime=[System.Net.NetworkCredential]::new('unused',$RuntimePassword).Password
  if($runtime.Length -lt 32){throw 'Runtime password must contain at least 32 characters.'}
  $escaped=$runtime.Replace("'","''")
  $userSql="IF DATABASE_PRINCIPAL_ID(N'anderzilla_identity_runtime') IS NULL CREATE USER anderzilla_identity_runtime WITH PASSWORD=N'$escaped';"
  $phaseIndex=0
  foreach($text in @($schema,$userSql,$grants)){
   $phase=@('schema','runtime-user','grants')[$phaseIndex]
   $phaseIndex++
   foreach($batch in ($text -split '(?im)^\s*GO\s*\r?$')){
    if([string]::IsNullOrWhiteSpace($batch)){continue}
    $command=$connection.CreateCommand();$command.Transaction=$transaction;$command.CommandTimeout=90;$command.CommandText=$batch
    try{[void]$command.ExecuteNonQuery()}finally{$command.Dispose()}
   }
  }
  $transaction.Commit()
  Write-Host 'Identity schema and dedicated runtime grants applied.'
 }catch{
  $failure=$_.Exception
  while($failure.InnerException){$failure=$failure.InnerException}
  $number=if($failure.PSObject.Properties.Name -contains 'Number'){$failure.Number}else{'unknown'}
  $line=if($failure.PSObject.Properties.Name -contains 'LineNumber'){$failure.LineNumber}else{'unknown'}
  $transaction.Rollback()
  throw "Identity migration failed in $phase (SQL error $number, line $line); transaction rolled back. Inspect SQL privately."
 }
}finally{$connection.Dispose();$builder.Clear();$runtime=$null;$escaped=$null;$userSql=$null;$AdminCredential=$null}
