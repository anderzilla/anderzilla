[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$AzureCli='az',
 [switch]$Apply
)
# Lets the content API function app (system-assigned identity, no keys) read and write ONLY its own media container.
# Dry run by default. Do not apply before the API code actually stores media in Blob: until then the permission is unused
# and least privilege says not to grant it (media currently lives in the database).
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$app="anderzilla-content-api-$Environment"
$account='anderzillacontentst'
$container="media-$Environment"
$role='Storage Blob Data Contributor'
$site=Invoke-IdentityAz -Arguments @('rest','--method','get','--url',"https://management.azure.com/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Web/sites/$app`?api-version=2023-12-01")
if(!$site -or $site.identity.type -ne 'SystemAssigned' -or !$site.identity.principalId){throw "Function app $app has no system-assigned identity; stop."}
$scope="/subscriptions/$IdentitySubscription/resourceGroups/$IdentityGroup/providers/Microsoft.Storage/storageAccounts/$account/blobServices/default/containers/$container"
$existing=@(Invoke-IdentityAz -Arguments @('role','assignment','list','--assignee',$site.identity.principalId,'--scope',$scope,'--role',$role))
[pscustomobject]@{Environment=$Environment;Principal="$app (system-assigned)";Role=$role;Scope="container $account/$container only";AlreadyAssigned=[bool]$existing.Count;Applied=[bool]$Apply} | ConvertTo-Json
Write-Host "Command: az role assignment create --assignee-object-id <principal of $app> --assignee-principal-type ServicePrincipal --role '$role' --scope <container $container>"
Write-Host 'Scope is a single container, not the storage account or the resource group.'
if($existing.Count){Write-Host 'Role already assigned; nothing to do.';return}
if(!$Apply){Write-Host 'Dry run only. Nothing was changed.';return}
if(!$PSCmdlet.ShouldProcess("$account/$container",'Assign Storage Blob Data Contributor to the content API identity')){return}
$null=Invoke-IdentityAz -Arguments @('role','assignment','create','--assignee-object-id',$site.identity.principalId,'--assignee-principal-type','ServicePrincipal','--role',$role,'--scope',$scope)
Write-Host 'Role assigned to the container only.'
