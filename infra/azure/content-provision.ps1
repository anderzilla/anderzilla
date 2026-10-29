[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$AzureCli='az',
 [switch]$NoReviewSite,
 [switch]$Apply
)
# Content platform for one environment: CMS database, agent API (Azure Functions), review site (SWA Free), media (Blob).
# Default run is read-only: it inspects Azure and prints what would be created, its cost class and the exact commands.
# -Apply creates resources and still honors -WhatIf/-Confirm. Nothing here deploys code, sets credentials, changes DNS or touches existing resources.
#
# Verified on 2026-10-29 (homolog): `az functionapp create --plan <existing plan>` fails with an AlwaysOn conflict, and with
# --consumption-plan-location the app IS created on the existing Linux consumption plan (plus an Application Insights component)
# but the CLI then exits with "Cannot find ServerFarm". `az functionapp/webapp update|identity assign` also return Conflict for such
# apps, while ARM PATCH works. This script therefore creates the app, verifies it through ARM, and applies identity/HTTPS through ARM.
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$names=@{Review="anderzilla-review-$Environment";Api="anderzilla-content-api-$Environment";Database="anderzilla-cms-$Environment";Storage='anderzillacontentst';Container="media-$Environment";Plan='EastUS2LinuxDynamicPlan';Location='eastus2'}
$siteUrl="https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/sites/$($names.Api)?api-version=2023-12-01"
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
$plan=$resources | Where-Object {$_.type -eq 'Microsoft.Web/serverfarms' -and $_.name -eq $names.Plan}
$blockers=@()
if(!$existingDb -and $freeCount -ge 10){$blockers+='Subscription already has 10 SQL free-offer databases.'}
if(!$NoReviewSite -and !$existingReview -and $apps.Count -ge 10){$blockers+='Static Web Apps quota (10) reached.'}
if(!$plan){$blockers+="Expected shared consumption plan $($names.Plan) not found."}
elseif($plan.sku.name -ne 'Y1'){$blockers+='Shared plan is not the Y1 consumption plan; refusing to place the API on a paid plan.'}
if(!$existingStorage){
 $check=Invoke-IdentityAz -Arguments @('storage','account','check-name','--name',$names.Storage)
 if(!$check.nameAvailable){$blockers+="Storage account name $($names.Storage) is unavailable ($($check.reason))."}
}
if($existingDb){Assert-IdentityDatabase (Invoke-IdentityAz -Arguments @('sql','db','show','--name',$names.Database,'--server',$IdentityServer,'--resource-group',$IdentityGroup))}
if($existingReview -and $existingReview.sku.name -ne 'Free'){$blockers+='Existing review SWA is not Free.'}
$state=@{db=if($existingDb){'exists (reused)'}else{'create'};review=if($existingReview){'exists (reused)'}else{'create'};api=if($existingApi){'exists (reused)'}else{'create'};storage=if($existingStorage){'exists (reused)'}else{'create'}}
$rows=@(
 [pscustomobject]@{Resource='CMS database';Name=$names.Database;Tier='SQL free offer, serverless Gen5, max 2 vCores, 32 GiB, AutoPause 60 min, no paid fallback';Action=$state.db;Cost='R$ 0'}
 [pscustomobject]@{Resource='Agent API';Name=$names.Api;Tier="Function App, Python 3.11, Linux consumption plan $($names.Plan) (Y1); HTTPS only; system-assigned identity; Application Insights created by the CLI (free up to 5 GB/month)";Action=$state.api;Cost='R$ 0 within the monthly free grant'}
 [pscustomobject]@{Resource='Review site';Name=$names.Review;Tier='Static Web App, Free, managed API (Python 3.11)';Action=if($NoReviewSite){'skipped (-NoReviewSite)'}else{$state.review};Cost='R$ 0'}
 [pscustomobject]@{Resource='Media storage';Name="$($names.Storage)/$($names.Container)";Tier='Storage account Standard_LRS StorageV2, TLS 1.2, HTTPS only, public blob access off; private container';Action=$state.storage;Cost='cents per month at ~50 MiB'}
)
$commands=@(
 $(if(!$existingStorage){"storage account create --name $($names.Storage) --resource-group $IdentityGroup --location $($names.Location) --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --https-only true --allow-blob-public-access false"})
 "storage container create --account-name $($names.Storage) --name $($names.Container) --auth-mode login --public-access off"
 $(if(!$existingDb){"sql db create --name $($names.Database) --server $IdentityServer --resource-group $IdentityGroup --edition GeneralPurpose --family Gen5 --capacity 2 --compute-model Serverless --min-capacity 0.5 --auto-pause-delay 60 --max-size 32GB --backup-storage-redundancy Local --use-free-limit --free-limit-exhaustion-behavior AutoPause"})
 $(if(!$NoReviewSite -and !$existingReview){"staticwebapp create --name $($names.Review) --resource-group $IdentityGroup --location $($names.Location) --sku Free"})
 $(if(!$existingApi){"functionapp create --name $($names.Api) --resource-group $IdentityGroup --consumption-plan-location $($names.Location) --storage-account $($names.Storage) --runtime python --runtime-version 3.11 --functions-version 4 --os-type Linux"})
 "rest --method patch (ARM) $($names.Api): identity.type=SystemAssigned, properties.httpsOnly=true"
)
[pscustomobject]@{Environment=$Environment;FreeDatabasesBefore=$freeCount;FreeOfferCap=10;StaticWebAppsBefore=$apps.Count;SwaCap=10;Blockers=$blockers;Applied=[bool]$Apply} | ConvertTo-Json
$rows | Format-Table -AutoSize -Wrap | Out-String -Width 220 | Write-Host
Write-Host 'Commands this script would run with -Apply (the Azure CLI adds --subscription and --only-show-errors):'
$commands | Where-Object {$_} | ForEach-Object {Write-Host "  az $_"}
Write-Host 'Not included: schema, runtime SQL user, app settings, role assignment for the API identity on the container, code deploy, DNS (ia./revisao.), GitHub secrets. Each is a separate, reviewed step.'
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
  $null=Invoke-IdentityAz -Arguments @('functionapp','create','--name',$names.Api,'--resource-group',$IdentityGroup,'--consumption-plan-location',$names.Location,'--storage-account',$names.Storage,'--runtime','python','--runtime-version','3.11','--functions-version','4','--os-type','Linux')
 }catch{
  Write-Warning 'The Azure CLI reported an error after creating the function app (known post-step failure); verifying through ARM.'
 }
}
$site=Invoke-IdentityAz -Arguments @('rest','--method','get','--url',$siteUrl)
if(!$site -or $site.kind -ne 'functionapp,linux' -or $site.properties.serverFarmId -notlike "*/serverfarms/$($names.Plan)"){throw 'Function app is missing or not on the expected Linux consumption plan; stop.'}
$patch=Join-Path ([System.IO.Path]::GetTempPath()) ("content-api-patch-"+[guid]::NewGuid().ToString('N')+'.json')
try{
 Set-Content -Path $patch -Value '{"identity":{"type":"SystemAssigned"},"properties":{"httpsOnly":true}}' -Encoding ascii
 $patched=Invoke-IdentityAz -Arguments @('rest','--method','patch','--url',$siteUrl,'--body',"@$patch")
 if($patched.identity.type -ne 'SystemAssigned' -or $patched.properties.httpsOnly -ne $true){throw 'Identity or HTTPS enforcement was not applied.'}
}finally{
 Remove-Item -LiteralPath $patch -Force -ErrorAction SilentlyContinue
}
Write-Host 'Resources prepared. Schema, credentials, settings, role assignment, deployment, DNS and secrets remain separate steps.'
