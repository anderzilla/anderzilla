<#
.SYNOPSIS
    Homolog-only release for the AnderZilla Cloud Run automation worker.

.DESCRIPTION
    Reproducible homolog release — no resource creation. Verifies fixed guards
    (gcloud config/account/project/region), billing, runtime SA, Artifact
    Registry repo and APIs, runs local tests, builds a unique UTC-tagged image
    in the existing private repo, resolves the immutable sha256 digest and
    deploys it privately (gen2, throttled, min 0/max 1/concurrency 1). Post-
    deploy verifies revision readiness, 100% traffic, digest/SA/scale/concurrency
    and that IAM remains private. Prints only non-secret evidence.
    Refuses production or any project/account/region override.

.NOTES
    Bootstrap must already exist: billing linked, APIs enabled, SA and repo
    present, service manually bootstrapped in homolog and need only exist (not
    created by this script). This script never creates billing links, budgets,
    IAM bindings, APIs, accounts, repos or public access.
    Requires PowerShell 7+, gcloud, python (Cloud Build performs the build;
    local Docker is not required).

.EXAMPLE
    pwsh ./infra/gcp/deploy-automation-worker.ps1

.LINK
    services/automation-worker/README.md
#>
#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 required.' }
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $true
}

# ── Fixed homolog guards — do not parameterize ────────────────────────────
$Config  = 'anderzilla'
$Account = 'player.one@anderzilla.com'
$Project = 'anderzilla-homolog'
$Region  = 'southamerica-east1'
$Service = 'anderzilla-automation-worker'
$RuntimeSA = 'anderzilla-automation-runtime@anderzilla-homolog.iam.gserviceaccount.com'
$RepoId   = 'anderzilla-automation'
$ImageBase = "$Region-docker.pkg.dev/$Project/$RepoId/worker"
$CmsWorkerBaseUrl = 'https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation'
$CmsWorkerAudience = 'https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation'
$RequiredAPIs = @('run.googleapis.com','artifactregistry.googleapis.com','iam.googleapis.com','cloudbuild.googleapis.com')

function Fail([string]$msg) { throw $msg }

# ── Preflight: refuse credential/impersonation overrides ──────────────────
# Explicitly check known project/account overrides (preserve guards)
$blockedVars = @('CLOUDSDK_CORE_PROJECT','CLOUDSDK_CORE_ACCOUNT','CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT',
    'CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE','CLOUDSDK_AUTH_ACCESS_TOKEN_FILE',
    'GOOGLE_CLOUD_PROJECT','GCLOUD_PROJECT','GOOGLE_IMPERSONATE_SERVICE_ACCOUNT',
    'GOOGLE_APPLICATION_CREDENTIALS','GOOGLE_CREDENTIALS')
foreach ($v in $blockedVars) {
    $val = [Environment]::GetEnvironmentVariable($v)
    if (-not [string]::IsNullOrWhiteSpace($val)) { Fail "Remove env override $v before release (homolog-only, fixed project/account)." }
}

# ── Verify gcloud configuration, account, project, region ─────────────────
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) { Fail 'gcloud not found in PATH.' }

# Verify gcloud configuration $Config exists
$currentConfig = (& gcloud --configuration=$Config config list --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { Fail "Could not verify gcloud configuration $Config." }
try { $cfgJson = $currentConfig | ConvertFrom-Json } catch { Fail "Could not parse gcloud config $Config." }
# All optional config properties must be accessed via PSObject.Properties under Set-StrictMode
$cfgCore = if ($cfgJson.PSObject.Properties['core']) { $cfgJson.core } else { $null }
$cfgCoreProject = if ($cfgCore -and $cfgCore.PSObject.Properties['project']) { $cfgCore.project } else { $null }
if ($cfgCoreProject -and $cfgCoreProject -ne $Project) {
    Fail "gcloud core.project in configuration $Config must be $Project (got $cfgCoreProject). Refusing override."
}
$cfgCoreAccount = if ($cfgCore -and $cfgCore.PSObject.Properties['account']) { $cfgCore.account } else { $null }
if ($cfgCoreAccount -and $cfgCoreAccount -ne $Account) {
    Fail "gcloud core.account in configuration $Config must be $Account (got $cfgCoreAccount). Refusing override."
}
# Impersonation / credential_file overrides in gcloud config itself
$cfgAuth = if ($cfgJson.PSObject.Properties['auth']) { $cfgJson.auth } else { $null }
$authImpersonate = if ($cfgAuth -and $cfgAuth.PSObject.Properties['impersonate_service_account']) { $cfgAuth.impersonate_service_account } else { $null }
$authCredFile = if ($cfgAuth -and $cfgAuth.PSObject.Properties['credential_file_override']) { $cfgAuth.credential_file_override } else { $null }
$authTokenFile = if ($cfgAuth -and $cfgAuth.PSObject.Properties['access_token_file']) { $cfgAuth.access_token_file } else { $null }
if ($authImpersonate -or $authCredFile -or $authTokenFile) {
    Fail "Remove gcloud impersonation/credential overrides from configuration $Config."
}

$activeAccount = (& gcloud --configuration=$Config config get-value account 2>$null | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $activeAccount -ne $Account) {
    Fail "Active gcloud account in configuration $Config must be exactly $Account (got '$activeAccount'). Authenticate $Account first."
}

$activeProject = (& gcloud --configuration=$Config config get-value project 2>$null | Out-String).Trim()
if ($activeProject -ne $Project) {
    Fail "Active gcloud project in configuration $Config must be exactly $Project (got '$activeProject'). Refusing production or override."
}
# Region guard: explicit value if set must match; unset is ok (script always passes --region)
$activeRegion = (& gcloud --configuration=$Config config get-value run/region 2>$null | Out-String).Trim()
if (-not [string]::IsNullOrWhiteSpace($activeRegion) -and $activeRegion -ne $Region -and $activeRegion -ne '(unset)') {
    Fail "gcloud run/region in configuration $Config must be $Region or unset (got '$activeRegion')."
}

# Hard refuse common production identifiers
if ($Project -ne 'anderzilla-homolog') { Fail 'Production project refused — this script is homolog-only.' }
if ($activeProject -match 'prod') { Fail 'Production-like project refused.' }

# ── Verify billing, SA, repo, APIs (read-only — never create) ────────────
Write-Host "Verifying homolog bootstrap (project=$Project region=$Region config=$Config)..." -ForegroundColor Cyan

$billingJson = (& gcloud --configuration=$Config billing projects describe $Project --project=$Project --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { Fail "Could not verify billing for $Project (gcloud billing projects describe failed)." }
try { $billing = $billingJson | ConvertFrom-Json } catch { Fail 'Could not parse billing status.' }
if (-not $billing.billingEnabled) { Fail "Billing not enabled for $Project (billingEnabled=false). Bootstrap required." }

# Runtime SA exists
$null = & gcloud --configuration=$Config iam service-accounts describe $RuntimeSA --project=$Project --format=json 2>$null
if ($LASTEXITCODE -ne 0) { Fail "Runtime service account not found: $RuntimeSA (bootstrap required)." }

# Artifact Registry repo exists
$null = & gcloud --configuration=$Config artifacts repositories describe $RepoId --location=$Region --project=$Project --format=json 2>$null
if ($LASTEXITCODE -ne 0) { Fail "Artifact Registry repo not found: $Region/$RepoId in $Project (bootstrap required)." }

# Required APIs enabled
$enabledJson = (& gcloud --configuration=$Config services list --enabled --project=$Project --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { Fail "Could not list enabled services for $Project." }
try { $enabled = $enabledJson | ConvertFrom-Json } catch { $enabled = @() }
$enabledNames = @($enabled | ForEach-Object { $_.config.name })
foreach ($api in $RequiredAPIs) {
    if ($enabledNames -notcontains $api) { Fail "Required API not enabled: $api (bootstrap required; this script does not enable APIs)." }
}

# ── Resolve repo root and run tests before any remote change ──────────────
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$WorkerDir = Join-Path $RepoRoot 'services/automation-worker'
if (-not (Test-Path -LiteralPath (Join-Path $WorkerDir 'Dockerfile'))) { Fail "Worker source not found at $WorkerDir" }
if (-not (Test-Path -LiteralPath (Join-Path $WorkerDir 'app.py'))) { Fail "Worker app.py not found at $WorkerDir" }

Write-Host "Running local tests: python -m pytest services/automation-worker/tests -q" -ForegroundColor Cyan
Push-Location $RepoRoot
try {
    $pytestCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pytestCmd) { $pytestCmd = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $pytestCmd) { Fail 'python not found for tests.' }
    & python -m pytest services/automation-worker/tests -q
    if ($LASTEXITCODE -ne 0) { Fail "Tests failed (python -m pytest services/automation-worker/tests -q). Refusing release." }
} finally { Pop-Location }

# ── Build with unique UTC tag, then resolve immutable digest ──────────────
$utcTag = (Get-Date -AsUTC -Format 'yyyyMMdd-HHmmss')
# Append short git SHA for traceability when available
try {
    $sha = (& git -C $RepoRoot rev-parse --short HEAD 2>$null | Out-String).Trim()
    if ($sha -match '^[a-f0-9]{7,40}$') { $utcTag = "$utcTag-g$sha" }
} catch {}
# Fallback uniqueness suffix if git unavailable
if ($utcTag -notmatch '-g[0-9a-f]+$') { $utcTag = "$utcTag-$([guid]::NewGuid().ToString('N').Substring(0,6))" }

$TaggedImage = "${ImageBase}:$utcTag"
Write-Host "Building $TaggedImage from $WorkerDir ..." -ForegroundColor Cyan

& gcloud --configuration=$Config builds submit --tag $TaggedImage --project=$Project --region=$Region --quiet $WorkerDir
if ($LASTEXITCODE -ne 0) { Fail "Cloud Build failed for $TaggedImage." }

# Resolve immutable digest for the tag we just pushed (never deploy mutable tag)
$digest = (& gcloud --configuration=$Config artifacts docker images describe $TaggedImage --project=$Project --format='value(image_summary.digest)' 2>$null | Out-String).Trim()
if ([string]::IsNullOrWhiteSpace($digest) -or $digest -notmatch '^sha256:[a-f0-9]{64}$') {
    # Try alternative describe via include-tags
    $imgJson = (& gcloud --configuration=$Config artifacts docker images list "$ImageBase" --project=$Project --include-tags --format=json 2>$null | Out-String)
    if ($LASTEXITCODE -eq 0) {
        try {
            $imgs = $imgJson | ConvertFrom-Json
            $hit = $imgs | Where-Object { $_.tags -contains $utcTag } | Select-Object -First 1
            if ($hit -and $hit.version -match '^sha256:[a-f0-9]{64}$') { $digest = $hit.version }
            elseif ($hit -and $hit.digest -match '^sha256:[a-f0-9]{64}$') { $digest = $hit.digest }
        } catch {}
    }
}
if ([string]::IsNullOrWhiteSpace($digest) -or $digest -notmatch '^sha256:[a-f0-9]{64}$') {
    Fail "Could not resolve immutable digest for $TaggedImage (expected sha256:64hex). Got: '$digest'."
}

$ImmutableImage = "${ImageBase}@$digest"
Write-Host "Resolved immutable image: $ImmutableImage" -ForegroundColor Green

# ── Deploy Cloud Run (private, scale-to-zero, pinned digest) ──────────────
Write-Host "Deploying $Service with digest $digest ..." -ForegroundColor Cyan

# Ensure service exists (release-only — do not create)
$null = & gcloud --configuration=$Config run services describe $Service --project=$Project --region=$Region --format=json 2>$null
if ($LASTEXITCODE -ne 0) { Fail "Cloud Run service $Service not found in $Project/$Region (bootstrap required; this script does not create services)." }

& gcloud --configuration=$Config run deploy $Service `
    --image=$ImmutableImage `
    --project=$Project `
    --region=$Region `
    --service-account=$RuntimeSA `
    --no-allow-unauthenticated `
    --min-instances=0 `
    --max-instances=1 `
    --concurrency=1 `
    --cpu=1 `
    --memory=512Mi `
    --timeout=45 `
    --cpu-throttling `
    --execution-environment=gen2 `
    --set-env-vars="CMS_WORKER_BASE_URL=$CmsWorkerBaseUrl,CMS_WORKER_AUDIENCE=$CmsWorkerAudience" `
    --quiet
if ($LASTEXITCODE -ne 0) { Fail "Cloud Run deploy failed for $Service." }

# ── Post-deploy verification (fail if any invariant is false) ─────────────
Write-Host "Verifying deployment invariants..." -ForegroundColor Cyan

$svcJson = (& gcloud --configuration=$Config run services describe $Service --project=$Project --region=$Region --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { Fail "Could not describe service $Service after deploy." }
try { $svc = $svcJson | ConvertFrom-Json } catch { Fail 'Could not parse service description.' }

$latestReady   = $svc.status.latestReadyRevisionName
$latestCreated = $svc.status.latestCreatedRevisionName
$svcUrl        = $svc.status.url
if ([string]::IsNullOrWhiteSpace($latestReady)) { Fail 'No latestReadyRevisionName after deploy.' }
if ($latestReady -ne $latestCreated) { Fail "Latest ready revision mismatch: ready=$latestReady created=$latestCreated." }
if ($latestReady -notlike "$Service-*") { Fail "Revision name does not match service prefix: $latestReady" }

# Ready condition must be True
$readyCond = @($svc.status.conditions | Where-Object { $_.type -eq 'Ready' })
if (-not $readyCond -or $readyCond[0].status -ne 'True') { Fail "Service Ready condition not True for $latestReady." }

# 100% traffic to latest revision
$traffic = @($svc.status.traffic)
if (-not $traffic -or $traffic.Count -eq 0) { Fail 'No traffic allocation found.' }
$latestTraffic = $traffic | Where-Object { $_.revisionName -eq $latestReady -or $_.isLatestRevision -eq $true -or $_.type -eq 'TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST' }
$percent = 0
foreach ($t in $traffic) {
    if ($t.revisionName -eq $latestReady) { $percent += [int]$t.percent }
    elseif ($t.isLatestRevision) { $percent += [int]$t.percent }
    elseif ($t.type -eq 'TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST') { $percent += [int]$t.percent }
}
if ($percent -ne 100) {
    # Fallback: single LATEST entry with 100
    $singleLatest = $traffic | Where-Object { $_.type -eq 'TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST' -and [int]$_.percent -eq 100 }
    if (-not $singleLatest) { Fail "Expected 100% traffic to latest revision $latestReady (got $percent%). Traffic: $($traffic | ConvertTo-Json -Compress)" }
}

# Actual digest and SA from revision
$revJson = (& gcloud --configuration=$Config run revisions describe $latestReady --project=$Project --region=$Region --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { Fail "Could not describe revision $latestReady." }
try { $rev = $revJson | ConvertFrom-Json } catch { Fail 'Could not parse revision description.' }

# Image digest check — compare deployed digest with expected
$revImage = $null
$revDigest = $null
try { $revImage = $rev.spec.containers[0].image } catch {}
try { $revDigest = $rev.status.imageDigest } catch {}
if (-not $revDigest) { try { $revDigest = $rev.status.imageDigests[0] } catch {} }
# Fallback: parse digest from image string if it contains @sha256:
if (-not $revDigest -and $revImage -match '@(sha256:[a-f0-9]{64})') { $revDigest = $Matches[1] }
if (-not $revDigest -and $revImage -match '(sha256:[a-f0-9]{64})') { $revDigest = $Matches[1] }
if ($revDigest -ne $digest) {
    # Also allow full image ref match
    if ($revImage -ne $ImmutableImage -and $revDigest -ne $digest) {
        Fail "Digest mismatch: expected $digest / $ImmutableImage, got image=$revImage digest=$revDigest"
    }
}

# Service account check (revision spec)
$revSA = $null
try { $revSA = $rev.spec.serviceAccountName } catch {}
if (-not $revSA) { try { $revSA = $rev.spec.service_account } catch {} }
if (-not $revSA) { try { $revSA = $svc.spec.template.spec.serviceAccountName } catch {} }
if (-not $revSA) { try { $revSA = $svc.spec.template.spec.service_account } catch {} }
# Cloud Run v2 field
if (-not $revSA) { try { $revSA = $rev.spec.serviceAccount } catch {} }
if ($revSA -and $revSA -ne $RuntimeSA) { Fail "Service account mismatch: expected $RuntimeSA, got $revSA" }
# Also verify service-level template SA
$svcSA = $null
try { $svcSA = $svc.spec.template.spec.serviceAccountName } catch {}
if (-not $svcSA) { try { $svcSA = $svc.spec.template.spec.service_account } catch {} }
if (-not $svcSA) { try { $svcSA = $svc.template.spec.serviceAccountName } catch {} }
if ($svcSA -and $svcSA -ne $RuntimeSA) { Fail "Service template SA mismatch: expected $RuntimeSA, got $svcSA" }

# Fixed, non-secret CMS connector configuration.
$envVars = @{}
try {
    foreach ($entry in $svc.spec.template.spec.containers[0].env) { $envVars[$entry.name] = $entry.value }
} catch {}
if ($envVars['CMS_WORKER_BASE_URL'] -ne $CmsWorkerBaseUrl -or $envVars['CMS_WORKER_AUDIENCE'] -ne $CmsWorkerAudience) {
    Fail 'CMS worker connector environment does not match the fixed homolog configuration.'
}

# maxScale 1 — check service scaling / template scaling
$maxScale = $null
try { $maxScale = $svc.spec.template.scaling.maxInstanceCount } catch {}
if (-not $maxScale) { try { $maxScale = $svc.spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale' } catch {} }
if (-not $maxScale) { try { $maxScale = $svc.template.scaling.maxInstanceCount } catch {} }
if (-not $maxScale) { try { $maxScale = $rev.spec.scaling.maxInstanceCount } catch {} }
if ($maxScale -and [int]$maxScale -ne 1) { Fail "maxScale must be 1 (got $maxScale)." }
# If none of the paths yielded a value, verify via explicit annotation/scaling field presence — fail if we cannot confirm
if (-not $maxScale) {
    $svcJsonStr = $svcJson.ToString()
    if ($svcJsonStr -notmatch '"maxInstanceCount"\s*:\s*1' -and $svcJsonStr -notmatch '"maxScale"\s*:\s*"1"') {
        Fail 'Could not verify maxScale=1 from service description.'
    }
}

# concurrency 1
$concurrency = $null
try { $concurrency = $svc.spec.template.containerConcurrency } catch {}
if (-not $concurrency) { try { $concurrency = $svc.spec.template.spec.containerConcurrency } catch {} }
if (-not $concurrency) { try { $concurrency = $rev.spec.containerConcurrency } catch {} }
if (-not $concurrency) { try { $concurrency = $rev.spec.containers[0].containerConcurrency } catch {} }
# v2 field
if (-not $concurrency) { try { $concurrency = $svc.spec.template.maxInstanceRequestConcurrency } catch {} }
if (-not $concurrency) { try { $concurrency = $rev.spec.maxInstanceRequestConcurrency } catch {} }
if ($concurrency -and [int]$concurrency -ne 1) { Fail "Concurrency must be 1 (got $concurrency)." }
if (-not $concurrency) {
    if ($svcJson -notmatch '"containerConcurrency"\s*:\s*1' -and $svcJson -notmatch '"maxInstanceRequestConcurrency"\s*:\s*1' -and $revJson -notmatch '"containerConcurrency"\s*:\s*1') {
        Fail 'Could not verify concurrency=1 from service/revision description.'
    }
}

# request timeout 45s — must be exactly 45 seconds
$timeout = $null
try { $timeout = $svc.spec.template.spec.timeoutSeconds } catch {}
if (-not $timeout) { try { $timeout = $svc.spec.template.spec.containers[0].timeoutSeconds } catch {} }
if (-not $timeout) { try { $timeout = $svc.spec.template.timeoutSeconds } catch {} }
if (-not $timeout) { try { $timeout = $rev.spec.timeoutSeconds } catch {} }
if (-not $timeout) { try { $timeout = $rev.spec.containers[0].timeoutSeconds } catch {} }
if (-not $timeout) { try { $timeout = $rev.spec.template.spec.timeoutSeconds } catch {} }
if ($null -ne $timeout -and "$timeout" -ne '') {
    $timeoutNorm = ("$timeout".Trim() -replace '"','' -replace 's$','').Trim()
    if ($timeoutNorm -ne '45') { Fail "Request timeout must be exactly 45s (got $timeout)." }
    try { if ([int]$timeoutNorm -ne 45) { Fail "Request timeout must be exactly 45s (got $timeout)." } } catch { Fail "Request timeout must be exactly 45s (got $timeout)." }
}
else {
    $combinedJson = "$svcJson`n$revJson"
    if ($combinedJson -notmatch '"timeoutSeconds"\s*:\s*"?45"?\b' -and $combinedJson -notmatch '"timeout"\s*:\s*"45s"' -and $combinedJson -notmatch '"timeoutSeconds"\s*:\s*"45s"') {
        Fail 'Could not verify request timeout=45s from service/revision description.'
    }
    $m = [regex]::Matches($combinedJson, '"timeoutSeconds"\s*:\s*"?(\d+)s?"?')
    foreach ($hit in $m) {
        if ($hit.Groups[1].Value -ne '45') { Fail "Request timeout must be exactly 45s (got $($hit.Groups[1].Value)s)." }
    }
}

# IAM: must contain no allUsers / allAuthenticatedUsers
$iamJson = (& gcloud --configuration=$Config run services get-iam-policy $Service --project=$Project --region=$Region --format=json 2>$null | Out-String)
if ($LASTEXITCODE -ne 0) { Fail "Could not fetch IAM policy for $Service." }
try { $iam = $iamJson | ConvertFrom-Json } catch { $iam = $null }
$bindings = @()
if ($iam -and $iam.PSObject.Properties['bindings']) { $bindings = @($iam.bindings) }
foreach ($b in $bindings) {
    $members = @($b.members)
    if ($members -contains 'allUsers' -or $members -contains 'allAuthenticatedUsers') {
        Fail "IAM policy must not contain allUsers/allAuthenticatedUsers (found in role $($b.role)). Service must remain private."
    }
}
# Also raw string check in case format differs
if ($iamJson -match 'allUsers' -or $iamJson -match 'allAuthenticatedUsers') {
    Fail 'IAM policy contains allUsers/allAuthenticatedUsers (raw match) — private access violated.'
}

# Extra: CPU 512Mi, throttling, gen2, SA already checked; verify via describe if present but don't hard-fail on optional fields
# CPU throttling and gen2 are deployment flags; if service description lacks them we already enforced at deploy time.

# ── Non-secret evidence only ──────────────────────────────────────────────
Write-Host ""
Write-Host "Release evidence (homolog):" -ForegroundColor Green
Write-Host "  image=$ImmutableImage"
Write-Host "  digest=$digest"
Write-Host "  revision=$latestReady"
Write-Host "  url=$svcUrl"
Write-Host "  access=private"
Write-Host ""
Write-Host "All invariants verified: ready=$latestReady 100% traffic, digest=$digest, SA=$RuntimeSA, maxScale=1, concurrency=1, no public IAM." -ForegroundColor Green
