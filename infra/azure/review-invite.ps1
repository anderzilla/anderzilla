[CmdletBinding(SupportsShouldProcess)]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [string]$UserDetails='anderzilla@ymail.com',
 [ValidateRange(1,168)][int]$ExpiresInHours=24,
 [string]$AzureCli='az',
 [switch]$ToClipboard,
 [switch]$Apply
)
# Invite the owner to the review site with the custom role anderzilla_admin (the Static Web Apps way to grant a role).
# The invitation URL is a one-time sign-in link: run this yourself in your own terminal so the link appears on YOUR screen,
# open it in the browser where you are signed in, and do not paste it anywhere. Dry run by default.
. (Join-Path $PSScriptRoot 'identity-common.ps1')
Assert-IdentityAccount
$app="anderzilla-review-$Environment"
$site=Invoke-IdentityAz -Arguments @('staticwebapp','list') | Where-Object {$_.name -eq $app -and $_.resourceGroup -eq $IdentityGroup}
if(!$site){throw "$app does not exist yet; create and deploy it first."}
$users=@(Invoke-IdentityAz -Arguments @('staticwebapp','users','list','--name',$app,'--resource-group',$IdentityGroup,'--authentication-provider','all'))
[pscustomobject]@{Environment=$Environment;Site="https://$($site.defaultHostName)";User=$UserDetails;Role='anderzilla_admin';Provider='aad';LinkValidHours=$ExpiresInHours;AlreadyHasRoles=@($users | Where-Object {$_.properties.displayName -eq $UserDetails} | ForEach-Object {$_.properties.roles});Applied=[bool]$Apply} | ConvertTo-Json
if(!$Apply){Write-Host 'Dry run only. No invitation was created.';return}
if(!$PSCmdlet.ShouldProcess("$app / $UserDetails",'Create a one-time invitation with the anderzilla_admin role')){return}
$invite=Invoke-IdentityAz -Arguments @('staticwebapp','users','invite','--name',$app,'--resource-group',$IdentityGroup,'--authentication-provider','aad','--domain',$site.defaultHostname,'--user-details',$UserDetails,'--roles','anderzilla_admin','--invitation-expiration-in-hours',[string]$ExpiresInHours)
if($ToClipboard){
 # A long link copied from a wrapped terminal line can break its signature; the clipboard keeps it intact and off the screen.
 Set-Clipboard -Value $invite.invitationUrl
 Write-Host "The one-time link (valid $ExpiresInHours h) is in your clipboard and was NOT printed. Paste it into the address bar of the browser where you are signed in as $UserDetails."
}else{
 Write-Host "Open this one-time link in the browser where you are signed in as $UserDetails (valid $ExpiresInHours h):"
 Write-Host $invite.invitationUrl
}
Write-Host 'Do not share or paste the link anywhere else. If your browser blocks identity.*.azurestaticapps.net (ad blocker), allow it for this site.'
