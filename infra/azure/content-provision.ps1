[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$AzureCli='az',
 [switch]$NoReviewSite,
 [switch]$Apply
)
# Content platform for one environment: CMS database, agent API (Azure Functions, Flex Consumption), review site (SWA Free), media (Blob).
# Default run is read-only: it inspects Azure and prints what would be created, its cost class and the exact commands.
# -Apply creates resources and still honors -WhatIf/-Confirm. Nothing here deploys code, sets credentials, changes DNS or touches existing resources.
#
# Verified on 2026-10-29 (homolog): an app created on the legacy Linux Consumption plan EastUS2LinuxDynamicPlan was left half-provisioned
# (reads and PATCH worked, but every configuration write and the delete failed with "Cannot find ServerFarm" / "Unable to resolve the App Service
# plan"). The API therefore runs on Flex Consumption (FC1), Azure's recommended serverless plan (Linux Consumption loses support on 2028-09-30),
# Python 3.12 (supported until 2028-10), 2048 MB instances, capped at 10 instances. The CLI grants the app identity "Storage Blob Data Contributor"
# on the content storage account for identity-based deployment storage (no keys). Delete with `az rest --method delete --url-parameters
# deleteEmptyServerFarm=false`: an `&` inside a URL is mangled by az.cmd.
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$names=@{Review="anderzilla-review-$Environment";Api="anderzilla-content-api-$Environment";Database="anderzilla-cms-$Environment";Storage='anderzillacontentst';Container="media-$Environment";Location='eastus2';PythonVersion='3.12';MaxInstances=10;InstanceMemoryMb=2048}
$siteBase="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/sites/$($names.Api)"
$resources=@(Invoke-IdentityAz -Arguments @('resource','list','--resource-group',$IdentityGroup))
$apps=@(Invoke-IdentityAz -Arguments @('staticwebapp','list'))
$databases=@($resources | Where-Object {$_.type -eq 'Microsoft.Sql/servers/databases' -and $_.name -notlike '*/master'})
$freeCount=0
foreach($entry in $databases){
 $db=Invoke-IdentityAz -Arguments @('resource','show','--ids',$entry.id,'--api-version','2023-08-01')
 if($db.properties.useFreeLimit){$freeCount++}
}
$existingDb=$databases | Where-Object {$_.name -eq "$IdentityServer/$($names.Database)"}
$existingReview=$apps | Where-Object {$_.name -eq $names.Review -and $_.resourceGroup -eq $IdentityGroup}
$existingApi=$resources | Where-Object {$_.type -eq 'Microsoft.Web/sites' -and $_.name -eq $names.Api}
$existingStorage=$resources | Where-Object {$_.type -eq 'Microsoft.Storage/storageAccounts' -and $_.name -eq $names.Storage}
$blockers=@()
if(!$existingDb -and $freeCount -ge 10){$blockers+='Subscription already has 10 SQL free-offer databases.'}
if(!$NoReviewSite -and !$existingReview -and $apps.Count -ge 10){$blockers+='Static Web Apps quota (10) reached.'}
if(!$existingApi){
 $runtimes=@(Invoke-IdentityAz -Arguments @('functionapp','list-flexconsumption-runtimes','--location',$names.Location,'--runtime','python'))
 if(!($runtimes | Where-Object {$_.version -eq $names.PythonVersion})){$blockers+="Flex Consumption does not offer Python $($names.PythonVersion) in $($names.Location)."}
}
if(!$existingStorage){
 $check=Invoke-IdentityAz -Arguments @('storage','account','check-name','--name',$names.Storage)
 if(!$check.nameAvailable){$blockers+="Storage account name $($names.Storage) is unavailable ($($check.reason))."}
}
if($existingDb){Assert-IdentityDatabase (Invoke-IdentityAz -Arguments @('sql','db','show','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup))}
if($existingReview -and $existingReview.sku.name -ne 'Free'){$blockers+='Existing review SWA is not Free.'}
$state=@{db=if($existingDb){'exists (reused)'}else{'create'};review=if($existingReview){'exists (reused)'}else{'create'};api=if($existingApi){'exists (reused)'}else{'create'};storage=if($existingStorage){'exists (reused)'}else{'create'}}
$rows=@(
 [pscustomobject]@{Resource='CMS database';Name=$names.Database;Tier='SQL free offer, serverless Gen5, max 2 vCores, 32 GiB, AutoPause 60 min, no paid fallback';Action=$state.db;Cost='R$ 0'}
 [pscustomobject]@{Resource='Agent API';Name=$names.Api;Tier="Function App on Flex Consumption (FC1), Python $($names.PythonVersion), $($names.InstanceMemoryMb) MB, max $($names.MaxInstances) instances; HTTPS only; system-assigned identity; identity-based deployment storage; Application Insights created by the CLI (free up to 5 GB/month)";Action=$state.api;Cost='R$ 0 within the monthly free grant (250k executions, 100k GB-s); capped at 10 instances'}
 [pscustomobject]@{Resource='Review site';Name=$names.Review;Tier='Static Web App, Free, managed API (Python 3.11)';Action=if($NoReviewSite){'skipped (-NoReviewSite)'}else{$state.review};Cost='R$ 0'}
 [pscustomobject]@{Resource='Media storage';Name="$($names.Storage)/$($names.Container)";Tier='Storage account Standard_LRS StorageV2, TLS 1.2, HTTPS only, public blob access off; private container';Action=$state.storage;Cost='cents per month at ~50 MiB'}
)
$commands=@(
 $(if(!$existingStorage){"storage account create --name $($names.Storage) --resource-group $IdentityGroup --location $($names.Location) --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --https-only true --allow-blob-public-access false"})
 "storage container create --account-name $($names.Storage) --name $($names.Container) --auth-mode login --public-access off"
 $(if(!$existingDb){"sql db create --name $($names.Database) --server $IdentityServer --resource-group $IdentityGroup --edition GeneralPurpose --family Gen5 --capacity 2 --compute-model Serverless --min-capacity 0.5 --auto-pause-delay 60 --max-size 32GB --backup-storage-redundancy Local --use-free-limit --free-limit-exhaustion-behavior AutoPause"})
 $(if(!$NoReviewSite -and !$existingReview){"staticwebapp create --name $($names.Review) --resource-group $IdentityGroup --location $($names.Location) --sku Free"})
 $(if(!$existingApi){"functionapp create --name $($names.Api) --resource-group $IdentityGroup --flexconsumption-location $($names.Location) --runtime python --runtime-version $($names.PythonVersion) --storage-account $($names.Storage) --instance-memory $($names.InstanceMemoryMb) --maximum-instance-count $($names.MaxInstances) --deployment-storage-auth-type SystemAssignedIdentity"})
 "rest --method patch (ARM) $($names.Api): properties.httpsOnly=true"
)
[pscustomobject]@{Environment=$Environment;FreeDatabasesBefore=$freeCount;FreeOfferCap=10;StaticWebAppsBefore=$apps.Count;SwaCap=10;Blockers=$blockers;Applied=[bool]$Apply} | ConvertTo-Json
$rows | Format-Table -AutoSize -Wrap | Out-String -Width 220 | Write-Host
Write-Host 'Commands this script would run with -Apply (the Azure CLI adds --subscription and --only-show-errors):'
$commands | Where-Object {$_} | ForEach-Object {Write-Host "  az $_"}
Write-Host 'Not included: schema (content-migrate.ps1), app settings (content-configure.ps1), code deploy, DNS (ia./revisao.), GitHub secrets. Each is a separate, reviewed step.'
if($blockers.Count){throw ('Blocked: ' + ($blockers -join ' '))}
if(!$Apply){Write-Host 'Dry run only. No resource was created or changed.';return}
if(!$PSCmdlet.ShouldProcess("$($names.Database), $($names.Review), $($names.Api), $($names.Storage)",'Create content platform Free-tier resources')){return}
if(!$existingStorage){
 $null=Invoke-IdentityAz -Arguments @('storage','account','create','--name',$names.Storage,'--resource-group',$IdentityGroup,'--location',$names.Location,'--sku','Standard_LRS','--kind','StorageV2','--min-tls-version','TLS1_2','--https-only','true','--allow-blob-public-access','false')
}
$null=Invoke-IdentityAz -Arguments @('storage','container','create','--account-name',$names.Storage,'--name',$names.Container,'--auth-mode','login','--public-access','off')
if(!$existingDb){
 $db=Invoke-IdentityAz -Arguments @('sql','db','create','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup,'--edition','GeneralPurpose','--family','Gen5','--capacity','2','--compute-model','Serverless','--min-capacity','0.5','--auto-pause-delay','60','--max-size','32GB','--backup-storage-redundancy','Local','--use-free-limit','--free-limit-exhaustion-behavior','AutoPause')
 Assert-IdentityDatabase $db
}
if(!$NoReviewSite -and !$existingReview){
 $app=Invoke-IdentityAz -Arguments @('staticwebapp','create','--name',$names.Review,'--resource-group',$IdentityGroup,'--location',$names.Location,'--sku','Free')
 if($app.sku.name -ne 'Free'){throw 'Unexpected deployed SWA tier; stop before any other operation.'}
}
if(!$existingApi){
 try{
  $null=Invoke-IdentityAz -Arguments @('functionapp','create','--name',$names.Api,'--resource-group',$IdentityGroup,'--flexconsumption-location',$names.Location,'--runtime','python','--runtime-version',$names.PythonVersion,'--storage-account',$names.Storage,'--instance-memory',[string]$names.InstanceMemoryMb,'--maximum-instance-count',[string]$names.MaxInstances,'--deployment-storage-auth-type','SystemAssignedIdentity')
 }catch{
  Write-Warning 'The Azure CLI reported an error while creating the function app; verifying through ARM.'
 }
}
$site=Invoke-IdentityAz -Arguments @('rest','--method','get','--url',$siteBase,'--url-parameters','api-version=2023-12-01')
$config=$site.properties.functionAppConfig
if(!$site -or $site.kind -ne 'functionapp,linux' -or !$config -or $config.runtime.version -ne $names.PythonVersion -or [int]$config.scaleAndConcurrency.maximumInstanceCount -ne $names.MaxInstances -or $site.properties.serverFarmId -like '*EastUS2LinuxDynamicPlan*'){throw 'Function app is missing or is not the expected Flex Consumption app; stop.'}
if($site.identity.type -ne 'SystemAssigned'){throw 'Function app has no system-assigned identity; stop.'}
if($site.properties.httpsOnly -ne $true){
 $patch=Join-Path ([System.IO.Path]::GetTempPath()) ("content-api-patch-"+[guid]::NewGuid().ToString('N')+'.json')
 try{
  Set-Content -Path $patch -Value '{"properties":{"httpsOnly":true}}' -Encoding ascii
  $patched=Invoke-IdentityAz -Arguments @('rest','--method','patch','--url',$siteBase,'--url-parameters','api-version=2023-12-01','--body',"@$patch")
  if($patched.properties.httpsOnly -ne $true){throw 'HTTPS enforcement was not applied.'}
 }finally{
  Remove-Item -LiteralPath $patch -Force -ErrorAction SilentlyContinue
 }
}
Write-Host 'Resources prepared. Schema, credentials, settings, deployment, DNS and secrets remain separate steps.'
