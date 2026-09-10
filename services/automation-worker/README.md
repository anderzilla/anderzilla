# AnderZilla Automation Worker

Private Cloud Run service — request-based, scale-to-zero (`min 0`). No credentials in repo, no GCP mutations, no CMS writes. Auth is **Cloud Run IAM**; user-supplied `actor`/`role` fields are rejected. Locally there is no application-level auth; remotely even `/health` is protected by Cloud Run IAM because the service is private.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | Liveness. Remotely protected by Cloud Run IAM (private service); locally no application-level auth. Returns `{status, service, version, cmsConnectorConfigured}` |
| `POST` | `/v1/execute` | Executes one `processId`. Validates strict envelope, fetches only allowlisted hosts with SSRF guards |
| `POST` | `/v1/poll` | **Pull coordinator** for Cloud Scheduler (IAM remains platform boundary). Processes at most **one** CMS lease per call — no looping, no durable state here. |

## Request envelope (`POST /v1/execute`)

```json
{
  "schemaVersion": 1,
  "runId": "uuid-v4",
  "processId": "seo-audit | editorial-package",
  "idempotencyKey": "opaque-1..128-chars [A-Za-z0-9._:-]",
  "input": {
    "market": "br | intl | global",
    "language": "pt-BR | en",
    "targetUrl": "https://anderzilla.com/...  or allowed Azure host",
    "notes": "optional, <=2000 chars, never logged"
  }
}
```

### Validation rules (strict envelope)

- Top-level keys must be **exactly** `schemaVersion`, `runId`, `processId`, `idempotencyKey`, `input`. `input` keys must be **exactly** `market`, `language`, `targetUrl` plus optional `notes`. Any unknown key → `400 unknown_field`.
- `schemaVersion` must be exactly `1` as an **int** — `true`/`false` (bool) is rejected even though `true == 1` in Python, type must be `int`.
- `runId` must be UUID.
- `processId` in `seo-audit`, `editorial-package` — type checked as string before membership to avoid 500 on arrays/objects.
- `input.market` / `language` / `targetUrl` required. `market`/`language` type checked before set membership. Accepted `language` values are exactly `pt-BR` and `en` (aligned with CMS `automation.py`); plain `pt` is rejected with `400 language_must_be_pt-BR_or_en`.
- `targetUrl` **must** be `https` and host in allowlist (validation is **purely syntactic — no DNS**):
  - `anderzilla.com` (primary, apex)
  - `www.anderzilla.com` (alias)
  - `salmon-stone-0a4d29c0f.5.azurestaticapps.net` (homolog — AZURE-RELEASE.md)
  - `mango-coast-0322c590f.5.azurestaticapps.net` (production — AZURE-RELEASE.md)
  - `salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net` (visual preview — AZURE-NEXT-PREVIEW.md / `services/publisher/run_release.py`)
  - Any other host, `http`, userinfo, non-443 port, or fragment-userinfo is rejected. Malformed ports such as `https://anderzilla.com:abc/` return `400 invalid_targetUrl` (ValueError caught, not 500).
  - DNS resolution and private-IP/CG-NAT checks are **not** performed here. They run only inside `fetch_html` on every initial/redirect hop, which is invoked entirely inside `asyncio.to_thread` and wrapped by the global `asyncio.wait_for(..., timeout=8.0)` deadline so a slow DNS cannot block the event loop.
- `notes` is optional, bounded, and **never appears in logs or error messages**.
- Top-level or `input` keys `actor`, `role`, `roles`, `principal`, `user`, etc. are rejected (`400 actor_fields_not_allowed`) — IAM is the only boundary.
- Body `> 32KB` → `413`.

## Pull coordinator (`POST /v1/poll`)

Authenticated **Cloud Scheduler → Cloud Run IAM** invocation. Cloud Run IAM remains the platform boundary — the app never accepts `actor`/`role`/`token`/`URL` from the caller.

- **Request body:** must be empty or `{}` and `<=1KB`; any field → `400 unknown_field`. Never accepts `actor`/`role`/`token`/`URL`/`audience`/`cmsUrl` from caller.
- **Config (all non-secret, env):**
  - `CMS_WORKER_BASE_URL` must be exact `https` URL ending ` /api/worker/automation` with host **fixed** to `victorious-mud-09355980f.3.azurestaticapps.net`, no query/fragment/userinfo, port 443 only. Example: `https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation`
  - `CMS_WORKER_AUDIENCE` must be exact `https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation` (same value). Any deviation → `503 cms_configuration_invalid`.
  - GCP metadata identity endpoint is **fixed** `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity` with query `audience=<url-encoded>&format=full` and header `Metadata-Flavor: Google`. Never accepts metadata URL from input/env.
- **Flow per call (at most one lease, no retries/loops):**
  1. Validate config.
  2. Fetch runtime service-account ID token from fixed metadata endpoint with connect/read total `<=3s`, require `Metadata-Flavor: Google` response header if provided by endpoint, bound token `<=16KB`, validate JWT shape (three base64url parts, header/payload JSON) only to reject malformed — CMS remains signature authority. Never log/return token.
  3. `POST {}` to `CMS /lease` (`<base>/lease`) with `X-AnderZilla-Worker-Authorization: Bearer <token>` (dedicated transport header through Azure Static Web Apps; see **Transport header** below), JSON, **outer + per-call timeouts `<=20.0s`** (`httpx.Timeout(20, connect=20)` + `asyncio.wait_for(20.0)`), max response `128KB`. Covers CMS auth + **Azure SQL paused→resume `login_timeout=15`** cold path. **Homolog evidence:** first lease calls timed out at `6s` while paused Azure SQL woke; subsequent warm authenticated OIDC poll returned `200 idle/no_work` in `2.22s`. `404 no_work` is a successful idle `200 {status:"idle",reason:"no_work"}`, not a failure.
  4. Validate lease envelope strictly: `schemaVersion 1` (int), UUID `runId`/`leaseId`, `processId` only `seo-audit`, `idempotencyKey` regex `^[A-Za-z0-9._:\-]{1,128}$`, `fencingToken` positive int, exact `input` fields (`market`/`language`/`targetUrl`/`notes` limits) reusing existing target URL validation. Unknown/extra fields → `502 invalid_lease_envelope`. Do not trust extra fields.
  5. Execute the same deterministic SEO audit internally under the existing `8s` deadline / non-blocking safeguards (`asyncio.to_thread(fetch_html)` + `wait_for`). No LLM, no ranking promise.
  6. `POST` strict completion to `CMS /complete` (`<base>/complete`) with same `X-AnderZilla-Worker-Authorization: Bearer <token>` and either `succeeded` + `result` or `failed` + stable allowlisted `errorCode` + generic `errorMessage`. Result is the same `targetUrl`/`finalUrl`/`httpStatus`/`market`/`language`/`checks`/`summary`/`disclaimer` as `/v1/execute` seo-audit. Bound completion `result` below CMS `64KB` (`_canonical_dumps` size); if audit result exceeds, report `failed` with `validation_error` / `Resultado inválido.` without including raw data, so the completion stays below `64KB`. **Outer + per-call timeouts `<=6.0s`** — DB is warm after lease.
  7. If CMS completion fails (non-2xx/timeout) → `502 cms_complete_failed` sanitized; lease expiry/retry on the CMS handles recovery. No loop, no second lease.
- **Timeout budget (staged worst-case, no retries/loops, one lease per poll):** metadata `3s` (ID token) + lease `20.0s` outer+per-call + SEO `8s` + completion `6.0s` = `37s` max sequential inner time. **Cloud Run platform timeout must be at least `45s`** to avoid cutting the worker mid-lease/complete. Lease `20s` separately covers CMS auth + Azure SQL `login_timeout=15` cold resume; completion stays `6s` because DB is warm after lease. SEO `8s` (`connect 3s`) unchanged.
- **Timeout-specific failure mapping (worker never retries; CMS lease expiry re-queues):**
  | Stage | Timeout | Poll failure | Worker action |
  |---|---|---|---|
  | Metadata (ID token) | `3s` outer+per-call | `502 identity_unavailable` | No lease attempted; next Scheduler tick retries. |
  | CMS `/lease` | `20.0s` outer+per-call | `502 cms_timeout` (`TimeoutError`) or `502 cms_unavailable`/`cms_error` | No lease acquired; CMS keeps work queued. Homolog `6s` timeout was cold Azure SQL wake; warm path `2.22s`. |
  | SEO audit | `8s` overall (`connect 3s`) | **Not a poll 502** — mapped to stable `errorCode` (`fetch_timeout` → `Tempo de coleta excedido.`, etc.) and reported via `POST /complete` as `failed`. | Completion still attempted. |
  | CMS `/complete` | `6.0s` outer+per-call | `502 cms_complete_failed` (includes `cms_complete_timeout`) | Lease expiry on CMS re-queues work; no second lease in same poll call. |
- **Transport header (Cloud Run → CMS through Azure Static Web Apps):** Azure SWA managed auth can **consume or strip** the standard `Authorization` header. To traverse SWA, Cloud Run sends the Google ID token in a **dedicated fixed header** `X-AnderZilla-Worker-Authorization: Bearer <Google-ID-token>`. This is a **transport header only** — the token remains a **Google OIDC ID token** and is **validated by the CMS application** (`worker_auth.authenticate_worker` via `google.oauth2.id_token.verify_oauth2_token`, audience/sub/email/iss/email_verified, Bearer scheme, expiry). The worker **never sends** standard `Authorization`; the CMS **only reads** `X-AnderZilla-Worker-Authorization` and ignores `Authorization`/query/cookie/body/alternate headers. The header name lowercased (`x-anderzilla-worker-authorization`) is in the explicit sensitive-field stripping and is never logged or returned.
- **Responses:** `idle` (`no_work`), `succeeded` (`result` with checks), `failed` (`errorCode`/`errorMessage` allowlisted generic), `502` sanitized on token/CMS/lease/complete failures, `503` on config. All error messages are bounded and contain no URL/token/query/notes/stack.
- **Logs:** structured JSON lines to stdout with `runId`/`leaseId`/`fencingToken`/`processId`/`input.targetHost` (safe host only). No CMS full URL, token, query, notes/body, error exception text.
- **Health:** `GET /health` returns `cmsConnectorConfigured: boolean` only — no URLs, no secrets.
- **Durable state:** CMS owns it. This service is stateless pull: Scheduler triggers `/v1/poll` on a cron (schedule **outside** this service, e.g., Cloud Scheduler `*/2 * * * *` → `POST https://<cloud-run>/v1/poll` with OIDC IAM). Lease expiry on CMS re-queues work; no retry in worker.

## Processes

### `seo-audit`
Fetches HTML with (all DNS and network work runs **entirely** inside `fetch_html` which is invoked only via `asyncio.to_thread` and wrapped by the global `asyncio.wait_for(..., timeout=8.0)` deadline):
- `https` only, host allowlist, no userinfo, port 443 only — syntactic checks in `validate_execute_body`/`_validate_target_url` do **not** call DNS; DNS checks run only here
- **Timeout — global non-blocking:** the async endpoint runs all network/DNS work in a **worker thread** (`asyncio.to_thread`) so the event loop is never blocked by sync `socket`/`httpx` calls. One hard **end-to-end deadline of 8 seconds** covers the entire SEO fetch including DNS for every hop and all redirects (`asyncio.wait_for(..., timeout=8.0)`). Deadline expiry maps to `fetch_timeout` `504`. Per-connect timeout remains `3 seconds` inside `httpx.Timeout`. If the deadline fires, the worker thread may continue until its own httpx timeouts expire, but that continuation is bounded by the same per-hop timeouts and size caps and does not delay the response.
- **Size:** `Content-Length` checked; streaming capped at **2 MB**
- **Redirects:** at most 3, each hop re-validated for allowlisted `https` host, private-IP and scheme. Redirect to any other host → `400 redirect_host_not_allowed`. Private IP → `400 private_ip_blocked`.
- **Private IP blocking:** literal private IPs (defensively, even though allowlist contains no literal IPs) and DNS-resolved private/loopback/link-local/multicast/unspecified/CG-NAT (`100.64.0.0/10`) are blocked on **every hop** (initial URL + each redirect target) via `socket.getaddrinfo` checks **inside** `fetch_html` under the same deadline.

Returns **deterministic** checks — no ranking promise, no LLM:

`http_status`, `title`, `description`, `canonical`, `html_lang`, `robots_meta`, `hreflang`, `json_ld`, `headings`, `image_alt`, `internal_links`. Each `{id, status: pass|warn|fail, evidence, detail}` with bounded evidence. `summary` counts pass/warn/fail. `html_lang` expectation is `pt-BR` for `language=pt-BR` (expects `pt-br` in `<html lang>`) and `en` for `language=en`.

### `editorial-package`
No fetch, no LLM. Returns a deterministic checklist/template grouped by `metadata`, `content`, `media`, `commerce`, `publish` plus `nextSteps`. Every item `done:false` with `evidenceRef` where applicable. Caller must fill and have human review before publishing.

## Idempotency

- In-memory replay cache, best-effort, TTL 600s, max 1000 entries.
- Key: `(processId, idempotencyKey)` scoped tuple.
- Store: `runId` + `input` hash are persisted together with the response.
- **Replay only** when **both** `runId` and `input` hash match the cached entry for that `(processId, idempotencyKey)` → returned with `replayed:true`.
- Any other combination for the same `(processId, idempotencyKey)` — different `runId` (even with same `input`) or same `runId` with different `input` — returns `409 idempotency_conflict` with message `same (processId, idempotencyKey) already used with different runId or input. Only exact replay of same runId and input is allowed.`
- Same `idempotencyKey` under a different `processId` is **independent** — no conflict, separate cache entry.
- **Caller owns durable idempotency.** Cache is not a substitute for outbox/inbox exactly-once; it only deduplicates retries within a single instance lifetime. Every successful response includes:
  ```json
  "idempotency": {"replayed": false, "note": "In-memory replay only; caller owns durable idempotency."}
  ```

## Logging & errors

- Structured JSON lines to stdout: `{ts, level, service, msg, ...}`.
- Never logs raw `targetUrl`, URL query, fragment, userinfo, `notes`, `body`, `authorization`, `x-anderzilla-worker-authorization`, or fetch exception text that can contain a URL. The dedicated transport header `x-anderzilla-worker-authorization` (lowercase) is explicitly stripped alongside `authorization`. Logs use a **safe host label** (`input.targetHost`) derived via safe `urlparse(...).hostname` parsing instead of the raw URL, or omit the field. Validation failures with `https://user:password@anderzilla.com/path?token=secret` do not emit `password`/`token`/raw URL in logs. Poll logs contain only `runId`/`leaseId`/`fencingToken`/`processId`/`input.targetHost`. The Google ID token is never logged or returned; CMS validates it as OIDC via application.
- Uvicorn access logs are **disabled** in the Docker `CMD` (`--no-access-log`) because request targets can contain query strings.
- Large fields truncated. Errors are bounded to ~300 chars, no stack.
- Errors: `{error, message}` with stable codes (`invalid_targetUrl`, `targetUrl_host_not_allowed`, `private_ip_blocked`, `redirect_host_not_allowed`, `response_too_large`, `fetch_timeout`, `unknown_field`, `idempotency_conflict`, …). Poll maps all internal/CMS/token failures to sanitized `502`/`503` with generic messages and never leaks the token, CMS full URL, query, notes, or stack.

## Run locally

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r services/automation-worker/requirements.txt
uvicorn services.automation-worker.app:app --host 127.0.0.1 --port 8080
# health — locally no app auth; remotely IAM-protected; reports cmsConnectorConfigured boolean only
curl http://127.0.0.1:8080/health
# execute — language must be pt-BR or en (pt is rejected)
curl -X POST http://127.0.0.1:8080/v1/execute -H "content-type: application/json" -d "{\"schemaVersion\":1,\"runId\":\"550e8400-e29b-41d4-a716-446655440000\",\"processId\":\"editorial-package\",\"idempotencyKey\":\"test-1\",\"input\":{\"market\":\"br\",\"language\":\"pt-BR\",\"targetUrl\":\"https://anderzilla.com/\"}}"
# poll — Cloud Scheduler → Cloud Run IAM; body must be empty or {}
$env:CMS_WORKER_BASE_URL="https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation"
$env:CMS_WORKER_AUDIENCE="https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation"
curl -X POST http://127.0.0.1:8080/v1/poll -H "content-type: application/json" -d "{}"
# idle when no work: {status:"idle",reason:"no_work"}
# succeeded: {status:"succeeded",runId,leaseId,fencingToken,targetHost,result:{checks,summary}}
```

## Tests

```powershell
pip install -r services/automation-worker/requirements-dev.txt
pytest services/automation-worker/tests -v
# or
python -m pytest services/automation-worker/tests -v
```

- `tests/test_worker.py` — preserves `/health` + `/v1/execute` contracts, SSRF/timeout guards, replay, secret-free logs (65 tests).
- `tests/test_poll.py` — mocks metadata/CMS/fetch (no network): no-work idle, success audit + completion, audit-failure completion with allowlisted code, metadata unavailable/spoof/malformed/timeout, CMS 401/5xx/oversize/malformed lease, completion failure, strict poll body (empty/{} only, `<=1KB`), config validation, result-too-large bounded to `64KB`, one-job per call, secret-free logs.

Runtime dependencies are in `requirements.txt`; `requirements-dev.txt` includes `requirements.txt` plus `pytest`/`pytest-asyncio`.

## Deploy (private Cloud Run)

- Service is private (`--no-allow-unauthenticated`), IAM invoker only — this protects `/health` remotely as well. `/v1/poll` is invoked by **Cloud Scheduler with OIDC** over IAM; no in-app actor check.
- `min-instance 0`, `max-instance 1` to start, concurrency measured. At most one lease per poll call; Scheduler schedule (e.g., `*/2 * * * *`) is **outside** this service — CMS owns durable lease state and expiry/retry.
- Uvicorn is started with `--no-access-log` so query strings in request targets are not access-logged.
- Do **not** set Cloud Run env secrets from this repo. `CMS_WORKER_BASE_URL`/`CMS_WORKER_AUDIENCE` are non-secret config; the runtime token is fetched from the fixed metadata endpoint and never logged.

## Risks / non-goals

- Replay cache is not durable — restarts lose it. **Poll has no replay cache** — CMS owns durable lease fencing; worker is stateless.
- `targetUrl` allowlist is static; DNS changes need a new image.
- No LLM call in this version; `editorial-package` is a template. `seo-audit` via poll reuses the same deterministic checks — no ranking promise.
- **DNS rebinding (bounded residual):** The allowlist is fixed to AnderZilla-owned apex/alias and documented Azure Static Web App hosts, which callers cannot choose beyond the set (see `ALLOWED_HOSTS`). Every hop re-resolves DNS and blocks private IPs, but the service does **not** implement IP pinning (no connection to a pinned IP resolved before the check). A hostname that is legitimate at validation time but later rebinds to a private IP between the DNS check and the TCP connect remains a bounded residual. Documented here as residual; not claimed as fully mitigated.
- Poll never loops or leases a second run; a Scheduler tick that races another tick relies on CMS fencing to ensure at-most-one execution per lease.
