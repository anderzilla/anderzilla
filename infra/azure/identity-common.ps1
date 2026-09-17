$ErrorActionPreference='Stop'
$IdentitySubscription='44b76346-26bd-4cd3-a529-627e47e99e5a'
$IdentityTenant='3fdcb773-0842-4fb9-925e-bea17d681f83'
$IdentityGroup='anderzilla-web'
$IdentityServer='anderzilla-sql-44b76346-cus'
function Invoke-IdentityAz {
  param([string[]]$Arguments)
  $result = & $AzureCli @Arguments --subscription $IdentitySubscription --only-show-errors -o json
  if($LASTEXITCODE){throw 'Azure operation failed. No credentials were printed by this script.'}
  if($result){return ($result | ConvertFrom-Json)}
}
function Assert-IdentityAccount {
  $account=Invoke-IdentityAz -Arguments @('account','show')
  if($account.id -ne $IdentitySubscription -or $account.tenantId -ne $IdentityTenant -or $account.user.name -ne 'anderzilla@ymail.com'){throw 'Wrong Azure account, subscription or tenant.'}
}
function Get-IdentityNames {
  param([ValidateSet('homolog','production')][string]$Environment)
  return @{App="anderzilla-identity-$Environment";Database="anderzilla-identity-$Environment";Server=$IdentityServer;Group=$IdentityGroup}
}
function Assert-IdentityDatabase {
  param($Database)
  if($Database.useFreeLimit -ne $true -or $Database.freeLimitExhaustionBehavior -ne 'AutoPause' -or $Database.sku.tier -ne 'GeneralPurpose' -or $Database.maxSizeBytes -gt 34359738368){throw 'Identity database must use the SQL free offer, AutoPause at exhaustion and at most 32 GiB.'}
}
