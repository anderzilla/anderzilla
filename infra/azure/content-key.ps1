[CmdletBinding()]
param(
 [Parameter(Mandatory)][ValidateSet('homolog','production')][string]$Environment,
 [Parameter(Mandatory)][ValidateSet('list','create','revoke','smoke')][string]$Action,
 [string]$Name,
 [ValidateRange(1,365)][int]$Days=90,
 [string]$Collections='content,media,banners',
 [string]$Id,
 [switch]$ToClipboard,
 [switch]$Apply,
 [switch]$InstallDependencies,
 [string]$SecretsDirectory='C:/Users/ander/.codex/anderzilla-azure',
 [string]$Python='python'
)
# Issue, list or revoke per-agent API keys. Run it yourself in your own terminal: a new key is shown once on YOUR screen
# (or copied to the clipboard with -ToClipboard) and is never stored; only its hash goes to the database.
# The database credential is read from the private runtime-credential file and exported only as environment variables of
# this process (removed in `finally`); it is never printed. `create` and `revoke` are dry runs unless -Apply is passed.
$ErrorActionPreference='Stop'
$database="anderzilla-cms-$Environment"
$server='anderzilla-sql-44b76346-cus.database.windows.net'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$tool=Join-Path $repo 'services/content-api/manage_keys.py'
$arguments=@($tool,$Action,'--environment',$Environment)
if($Action -eq 'smoke'){
 # Smoke test of the deployed homolog API (services/content-api/smoke_homolog.py): mints a throwaway 1-day key, runs ~28 checks
 # over HTTPS, revokes the key. It leaves test drafts and one pending package in the homolog sandbox database, so it needs -Apply.
 if($Environment -ne 'homolog'){throw 'The smoke test only runs against homolog.'}
 $tool=Join-Path $repo 'services/content-api/smoke_homolog.py'
 $arguments=@($tool)
 if(!$Apply){
  Write-Host 'Plan: create a throwaway 1-day key (not displayed), run the checks against the homolog API, revoke the key. Test drafts and one pending package stay in the homolog database (no delete permission). Nothing is approved or published.'
  Write-Host 'Dry run only. Re-run with -Apply.'
  exit 0
 }
}
if($Action -eq 'create'){
 if(!$Name){throw '-Name is required for create (for example claude-homolog).'}
 $arguments+=@('--name',$Name,'--days',[string]$Days,'--collections',$Collections)
 if($ToClipboard){$arguments+='--clipboard'}
}
if($Action -eq 'revoke'){
 if(!$Id){throw '-Id is required for revoke (see the list action).'}
 $arguments+=@('--id',$Id)
}
if($Apply -and $Action -notin 'list','smoke'){$arguments+='--apply'}
$needsDatabase=($Action -eq 'list') -or $Apply
if(!$needsDatabase){
 & $Python @arguments
 exit $LASTEXITCODE
}
# The Azure SQL driver is not part of a plain Python install. Missing packages are reported with the exact command;
# -InstallDependencies runs that command (pinned versions from the API's requirements.txt, user-level install only).
$missing=@(& $Python -c "import importlib.util as u; print(','.join(m for m in ('pytds','certifi','OpenSSL') if not u.find_spec(m)))") -join ''
if($missing){
 $pins=@(Get-Content (Join-Path $repo 'services/content-api/requirements.txt') | Where-Object {$_ -match '^(python-tds|certifi|pyOpenSSL)=='})
 if(!$InstallDependencies){throw "Missing Python packages: $missing. Re-run with -InstallDependencies, or run: $Python -m pip install --user $($pins -join ' ')"}
 & $Python -m pip install --user --disable-pip-version-check --quiet @pins
 if($LASTEXITCODE){throw 'Dependency installation failed.'}
}
$secretFile=Join-Path $SecretsDirectory "content-api-$Environment.json"
if(!(Test-Path -LiteralPath $secretFile)){throw "Runtime credential file not found: $secretFile. Run content-migrate.ps1 first."}
$secret=Get-Content -LiteralPath $secretFile -Raw | ConvertFrom-Json
if($secret.environment -ne $Environment -or $secret.database -ne $database -or $secret.server -ne $server -or ([string]$secret.password).Length -lt 32){throw 'The credential file does not match this environment or is incomplete.'}
try{
 $env:CMS_SQL_SERVER=$server;$env:CMS_SQL_DATABASE=$database;$env:CMS_SQL_USER=[string]$secret.user;$env:CMS_SQL_PASSWORD=[string]$secret.password
 & $Python @arguments
 if($LASTEXITCODE){throw "manage_keys.py exited with code $LASTEXITCODE."}
}finally{
 foreach($name in 'CMS_SQL_SERVER','CMS_SQL_DATABASE','CMS_SQL_USER','CMS_SQL_PASSWORD'){Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue}
 $secret=$null
}
