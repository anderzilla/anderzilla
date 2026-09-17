[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$AzureCli='C:/Users/ander/.codex/tools/azure-cli/portable/bin/az.cmd',
 [switch]$Apply
)
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$names=Get-IdentityNames $Environment
$resources=@(Invoke-IdentityAz -Arguments @('resource','list'))
$apps=@($resources | Where-Object {$_.type -eq 'Microsoft.Web/staticSites'})
$databases=@($resources | Where-Object {$_.type -eq 'Microsoft.Sql/servers/databases' -and $_.name -notlike '*/master'})
$freeCount=0
foreach($entry in $databases){
 $db=Invoke-IdentityAz -Arguments @('resource','show','--ids',$entry.id,'--api-version','2023-08-01')
 if($db.properties.useFreeLimit){$freeCount++}
}
$existingDb=$databases | Where-Object {$_.name -eq "$IdentityServer/$($names.Database)"}
$existingApp=$apps | Where-Object {$_.name -eq $names.App -and $_.resourceGroup -eq $IdentityGroup}
if(!$existingDb -and $freeCount -ge 10){throw 'Subscription already has 10 SQL free-offer databases.'}
if(!$existingApp -and $apps.Count -ge 10){throw 'Review Static Web Apps quota before creating another resource.'}
$server=Invoke-IdentityAz -Arguments @('sql','server','show','--name',$IdentityServer,'--resource-group',$IdentityGroup)
if($server.location -ne 'centralus'){throw 'Unexpected existing SQL server location.'}
if($existingDb){Assert-IdentityDatabase (Invoke-IdentityAz -Arguments @('sql','db','show','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup))}
if($existingApp){
 $app=Invoke-IdentityAz -Arguments @('staticwebapp','show','--name',$names.App,'--resource-group',$IdentityGroup)
 if($app.sku.name -ne 'Free'){throw 'Existing identity SWA is not Free.'}
}
[pscustomobject]@{Environment=$Environment;App=$names.App;AppSku='Free';Database=$names.Database;Server=$IdentityServer;FreeDatabasesBefore=$freeCount;FreeOfferCap=10;Exhaustion='AutoPause';MaxDatabaseGiB=32;Applied=[bool]$Apply;Note='No paid fallback, DNS, SMTP provider, OAuth registration or CMS change.'} | ConvertTo-Json
if(!$Apply){return}
if(!$PSCmdlet.ShouldProcess("$($names.App) + $($names.Database)",'Create isolated identity Free resources')){return}
if(!$existingDb){
 $db=Invoke-IdentityAz -Arguments @('sql','db','create','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup,'--edition','GeneralPurpose','--family','Gen5','--capacity','2','--compute-model','Serverless','--min-capacity','0.5','--auto-pause-delay','60','--max-size','32GB','--backup-storage-redundancy','Local','--use-free-limit','--free-limit-exhaustion-behavior','AutoPause')
 Assert-IdentityDatabase $db
}
if(!$existingApp){
 $app=Invoke-IdentityAz -Arguments @('staticwebapp','create','--name',$names.App,'--resource-group',$IdentityGroup,'--location','eastus2','--sku','Free')
 if($app.sku.name -ne 'Free'){throw 'Unexpected deployed SWA tier; stop before any other operation.'}
}
Write-Host 'Resources prepared. Schema, runtime credentials, provider configuration and deployment remain separate.'
