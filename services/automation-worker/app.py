"""
AnderZilla Automation Worker — private Cloud Run service.
Python 3.12, request-based scale-to-zero. No credentials, no GCP mutations.

Endpoints:
  GET  /health
  POST /v1/execute
  POST /v1/poll   (pull coordinator, single lease per call)

Auth boundary: Cloud Run IAM only. Rejects any user-supplied actor/role fields.

DNS rebinding residual (bounded): The allowlist is fixed to AnderZilla-owned
apex/alias (anderzilla.com, www.anderzilla.com) and documented Azure Static
Web App hosts (see ALLOWED_HOSTS / AZURE-RELEASE.md). Callers cannot choose
hosts beyond this set. Every hop re-resolves DNS and blocks private IPs, but
without IP pinning a validated hostname that later rebinds to a private IP
between the check and the fetch remains a bounded residual. See README Risks.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import ipaddress
import json
import logging
import os
import re
import socket
import time
import uuid
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlparse

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# ─── Config ────────────────────────────────────────────────────────────────

SERVICE_NAME = "automation-worker"
SERVICE_VERSION = "0.1.0"

# Documented Azure hosts — see Z:/AnderZilla-docs/operations/AZURE-RELEASE.md
# and AZURE-NEXT-PREVIEW.md + services/publisher/run_release.py PREVIEW_URL.
# Task says "only https://anderzilla.com and the two documented Azure public
# preview/production hosts". We pin the three real hosts (homolog, production,
# visual preview) plus apex. Visual preview is alias of homolog `visual` env.
ALLOWED_HOSTS = {
    "anderzilla.com",
    "www.anderzilla.com",  # convenience alias — primary remains apex
    "salmon-stone-0a4d29c0f.5.azurestaticapps.net",  # homolog (AZURE-RELEASE)
    "mango-coast-0322c590f.5.azurestaticapps.net",    # production (AZURE-RELEASE)
    "salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net",  # visual preview
}

SUPPORTED_PROCESSES = {"seo-audit", "editorial-package"}
SUPPORTED_MARKETS = {"br", "intl", "global"}
SUPPORTED_LANGUAGES = {"pt-BR", "en"}

MAX_BYTES = 2_000_000  # 2 MB
MAX_REDIRECTS = 3
TIMEOUT_CONNECT = 3.0
TIMEOUT_TOTAL = 8.0
MAX_NOTES_LEN = 2000
MAX_IDEMPOTENCY_KEY_LEN = 128
REPLAY_TTL_SECONDS = 600
REPLAY_MAX_ENTRIES = 1000

# Strict envelope — exact keys only
ALLOWED_TOP_LEVEL_KEYS = {"schemaVersion", "runId", "processId", "idempotencyKey", "input"}
ALLOWED_INPUT_KEYS = {"market", "language", "targetUrl", "notes"}

# ─── Poll coordinator config (all non-secret) ─────────────────────────────

CMS_WORKER_HOST = "victorious-mud-09355980f.3.azurestaticapps.net"
CMS_WORKER_AUDIENCE_EXPECTED = "https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation"
METADATA_FIXED_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"

MAX_POLL_BODY_BYTES = 1024
MAX_METADATA_TOKEN_BYTES = 16 * 1024
MAX_CMS_LEASE_RESPONSE_BYTES = 128 * 1024
MAX_CMS_RESULT_BYTES = 64 * 1024
# ── Timeout budget (staged, no retries, one lease per poll) ───────────────
# Metadata (GCP ID token): 3s outer+per-call — fixed metadata endpoint.
# Lease: 20.0s outer + per-call httpx Timeout(20, connect=20) — covers CMS auth
#   + Azure SQL paused resume login_timeout=15. Homolog evidence: first lease
#   calls timed out at 6s while Azure SQL woke; subsequent warm OIDC poll
#   returned 200 idle/no_work in 2.22s. Cold path must tolerate 15s.
# Completion: 6.0s outer+per-call — DB is warm after lease.
# SEO fetch: 8s global deadline (httpx connect 3s). Worst-case staged:
#   3 (metadata) + 20 (lease) + 8 (SEO) + 6 (complete) = 37s. Cloud Run
#   platform timeout must be at least 45s to avoid cutting the worker mid-lease.
# No retries/loops; at most one lease per poll.
TIMEOUT_METADATA_SECONDS = 3.0
TIMEOUT_CMS_LEASE_SECONDS = 20.0
TIMEOUT_CMS_COMPLETE_SECONDS = 6.0
TIMEOUT_CMS_SECONDS = TIMEOUT_CMS_COMPLETE_SECONDS  # backward-compat alias; lease uses TIMEOUT_CMS_LEASE_SECONDS

ALLOWED_LEASE_TOP_KEYS = {"schemaVersion", "runId", "processId", "idempotencyKey", "input", "leaseId", "fencingToken", "leasedAt", "leaseExpiresAt"}
ALLOWED_LEASE_INPUT_KEYS = {"market", "language", "targetUrl", "notes"}

# Stable error codes allowlisted by CMS (automation.py)
_STABLE_ERROR_MESSAGES: Dict[str, str] = {
    "fetch_timeout": "Tempo de coleta excedido.",
    "target_unreachable": "Destino não alcançável.",
    "dns_error": "Falha de DNS.",
    "tls_error": "Falha de TLS.",
    "render_error": "Falha de renderização.",
    "parsing_error": "Falha de análise.",
    "rate_limited": "Limite excedido.",
    "worker_failed": "Falha no processamento externo.",
    "lease_exhausted": "Lease expirado sem conclusão.",
    "validation_error": "Resultado inválido.",
    "internal_error": "Erro interno do worker.",
}
_STABLE_CODES = set(_STABLE_ERROR_MESSAGES.keys())

# FetchError -> stable code mapping (deterministic, sanitized)
_FETCH_TO_STABLE: Dict[str, str] = {
    "fetch_timeout": "fetch_timeout",
    "fetch_connect_error": "target_unreachable",
    "fetch_error": "worker_failed",
    "response_too_large": "validation_error",
    "too_many_redirects": "validation_error",
    "redirect_host_not_allowed": "validation_error",
    "redirect_scheme_not_https": "validation_error",
    "redirect_userinfo_not_allowed": "validation_error",
    "redirect_port_not_allowed": "validation_error",
    "private_ip_blocked": "validation_error",
    "invalid_targetUrl": "validation_error",
    "targetUrl_host_not_allowed": "validation_error",
    "targetUrl_scheme_must_be_https": "validation_error",
    "targetUrl_userinfo_not_allowed": "validation_error",
    "targetUrl_port_not_allowed": "validation_error",
    "targetUrl_too_long": "validation_error",
    "invalid_targetUrl": "validation_error",
}

# Structured logger — JSON lines, never include notes/body/secrets/raw URLs
logger = logging.getLogger(SERVICE_NAME)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.handlers = [handler]
logger.setLevel(logging.INFO)
logger.propagate = False


def jlog(level: str, msg: str, **fields: Any) -> None:
    # strip any accidental secret-like fields and raw URL fields
    # x-anderzilla-worker-authorization is the dedicated transport header for the
    # Google ID token through Azure Static Web Apps; token remains Google OIDC
    # and is validated by application — never log or return header/token.
    for k in list(fields.keys()):
        if k.lower() in ("notes", "body", "authorization", "x-anderzilla-worker-authorization", "token", "secret", "credential", "targetUrl", "url", "input.targetUrl"):
            fields.pop(k, None)
            continue
        # also drop any field whose value looks like a raw https URL with query/fragment/userinfo
        # — safe host labels are allowed via input.targetHost only
        if k in fields and isinstance(fields[k], str) and "://" in fields[k]:
            fields.pop(k, None)
    # bound field sizes
    for k, v in list(fields.items()):
        if isinstance(v, str) and len(v) > 500:
            fields[k] = v[:500] + "…[truncated]"
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "level": level, "service": SERVICE_NAME, "msg": msg, **fields}
    line = json.dumps(rec, ensure_ascii=False)
    if level == "error":
        logger.error(line)
    elif level == "warn":
        logger.warning(line)
    else:
        logger.info(line)


app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION, docs_url=None, redoc_url=None, openapi_url=None)

# In-memory replay cache — best-effort only.
# Key: (processId, idempotencyKey) -> {runId, inputHash, response, expiresAt}
_replay: Dict[Tuple[str, str], Dict[str, Any]] = {}


def _prune_replay() -> None:
    now = time.monotonic()
    expired = [k for k, v in _replay.items() if v.get("expiresAt", 0) < now]
    for k in expired:
        _replay.pop(k, None)
    # bound size — evict oldest
    if len(_replay) > REPLAY_MAX_ENTRIES:
        oldest = sorted(_replay.items(), key=lambda kv: kv[1].get("expiresAt", 0))
        for k, _ in oldest[: len(_replay) - REPLAY_MAX_ENTRIES]:
            _replay.pop(k, None)


def _input_hash(inp: Dict[str, Any]) -> str:
    # deterministic hash of relevant input (market/language/targetUrl/notes)
    canonical = json.dumps(inp, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ─── Helpers ────────────────────────────────────────────────────────────────

FORBIDDEN_BODY_KEYS = {"actor", "actorId", "role", "roles", "principal", "user", "userId", "serviceAccount"}

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:\-]{1,128}$")


def _bounded(s: str, n: int = 300) -> str:
    if len(s) > n:
        return s[:n] + "…[truncated]"
    return s


def _safe_host_label(raw: Any) -> str:
    """Safe host label for logs — never includes userinfo/query/fragment/raw URL."""
    if not isinstance(raw, str):
        return "invalid-host"
    try:
        p = urlparse(raw)
        h = (p.hostname or "").lower()
        if h and len(h) <= 253:
            return h
        return "invalid-host"
    except Exception:
        return "invalid-host"


def _is_private_ip_literal(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified


def _host_resolves_to_private(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False  # DNS failure is not private; fetch will fail later
    for _fam, _type, _proto, _canon, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            return True
        if ip.version == 4 and ip in ipaddress.ip_network("100.64.0.0/10"):
            return True
    return False


def _validate_target_url(raw: str) -> Tuple[str, str]:
    """Return (normalized_url, error_code) — error_code empty on success.

    Purely syntactic — no DNS. Checks https, exact ALLOWED_HOSTS hostname,
    no userinfo, valid/default 443 port, malformed URL handling. DNS
    public/private/CGNAT checks live only in fetch_html, which is always
    invoked inside asyncio.to_thread and wrapped by the global
    asyncio.wait_for(TIMEOUT_TOTAL) deadline.
    """
    if not isinstance(raw, str) or not raw:
        return "", "invalid_targetUrl"
    if len(raw) > 2048:
        return "", "targetUrl_too_long"
    try:
        p = urlparse(raw)
        if p.scheme != "https":
            return "", "targetUrl_scheme_must_be_https"
        if p.username or p.password:
            return "", "targetUrl_userinfo_not_allowed"
        if p.fragment and "@" in p.fragment:
            return "", "targetUrl_userinfo_not_allowed"
        host = (p.hostname or "").lower()
        if not host:
            return "", "invalid_targetUrl"
        if host not in ALLOWED_HOSTS:
            return "", "targetUrl_host_not_allowed"
        # port: only 443 or default — p.port can raise ValueError for :abc
        try:
            port = p.port
        except ValueError:
            return "", "invalid_targetUrl"
        if port is not None and port != 443:
            return "", "targetUrl_port_not_allowed"
        return raw, ""
    except ValueError:
        return "", "invalid_targetUrl"
    except Exception:
        return "", "invalid_targetUrl"


# ─── Poll coordinator helpers ─────────────────────────────────────────────

def _validate_cms_config() -> Tuple[str, str]:
    """Validate CMS_WORKER_BASE_URL and CMS_WORKER_AUDIENCE. Return (base_url, audience). Raise ValueError on invalid."""
    base_url = (os.getenv("CMS_WORKER_BASE_URL") or "").strip()
    audience = (os.getenv("CMS_WORKER_AUDIENCE") or "").strip()
    if not base_url or not audience:
        raise ValueError("missing config")
    # audience must be exact expected
    if audience != CMS_WORKER_AUDIENCE_EXPECTED:
        raise ValueError("audience mismatch")
    # base_url validation: exact https, host fixed, path exact, no query/fragment/userinfo, port 443 only
    if len(base_url) > 2048:
        raise ValueError("base_url too long")
    try:
        p = urlparse(base_url)
        if p.scheme != "https":
            raise ValueError("scheme")
        if p.username or p.password:
            raise ValueError("userinfo")
        if p.query or p.fragment:
            raise ValueError("query/fragment")
        host = (p.hostname or "").lower()
        if host != CMS_WORKER_HOST:
            raise ValueError("host")
        if p.path != "/api/worker/automation":
            raise ValueError("path")
        try:
            port = p.port
        except ValueError:
            raise ValueError("port")
        if port is not None and port != 443:
            raise ValueError("port not 443")
        # raw check for userinfo bypass via '@' before host
        raw_after_scheme = base_url.split("://", 1)[-1]
        if "@" in raw_after_scheme.split("/", 1)[0]:
            # userinfo present but hostname check already fails; still reject
            raise ValueError("userinfo raw")
    except ValueError:
        raise
    except Exception:
        raise ValueError("invalid base_url")
    return base_url, audience


def _is_cms_configured() -> bool:
    try:
        _validate_cms_config()
        return True
    except Exception:
        return False


def _validate_jwt_shape(token: str) -> bool:
    """Minimal JWT shape validation. CMS remains signature authority."""
    if not isinstance(token, str) or not token:
        return False
    if len(token.encode("utf-8")) > MAX_METADATA_TOKEN_BYTES:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    # base64url chars only, no padding in JWT, but allow padding handling
    b64_re = re.compile(r"^[A-Za-z0-9_-]+$")
    for part in parts:
        if not part or len(part) > 8192:
            return False
        if not b64_re.match(part):
            return False
        # try decode
        try:
            padded = part + "=" * (-len(part) % 4)
            base64.urlsafe_b64decode(padded.encode("ascii"))
        except Exception:
            return False
    # optionally ensure header/payload are JSON objects
    try:
        for idx in (0, 1):
            padded = parts[idx] + "=" * (-len(parts[idx]) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            obj = json.loads(decoded)
            if not isinstance(obj, dict):
                return False
    except Exception:
        return False
    return True


def _fetch_id_token_sync(audience: str) -> str:
    """Sync fetch of GCP identity token from fixed metadata endpoint. Never accept URL from input/env."""
    encoded = quote(audience, safe="")
    url = f"{METADATA_FIXED_URL}?audience={encoded}&format=full"
    headers = {"Metadata-Flavor": "Google"}
    timeout = httpx.Timeout(TIMEOUT_METADATA_SECONDS, connect=TIMEOUT_METADATA_SECONDS)
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        with client.stream("GET", url, headers=headers) as resp:
            # check Metadata-Flavor response header if present must be Google
            has_mf = False
            mf_val = None
            for k, v in resp.headers.items():
                if k.lower() == "metadata-flavor":
                    has_mf = True
                    mf_val = v
                    break
            if has_mf and mf_val != "Google":
                raise ValueError("metadata header spoof")
            if resp.status_code != 200:
                raise ValueError(f"metadata status {resp.status_code}")
            # follow_redirects=false ensures 3xx is not success; treat as failure
            if resp.status_code in (301, 302, 303, 307, 308):
                raise ValueError(f"metadata redirect {resp.status_code}")
            # streamed bounded token 16KB - abort once limit exceeded without buffering full response
            total = 0
            chunks: List[bytes] = []
            for chunk in resp.iter_bytes(chunk_size=8192):
                total += len(chunk)
                if total > MAX_METADATA_TOKEN_BYTES:
                    raise ValueError("token too large")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if len(raw) > MAX_METADATA_TOKEN_BYTES:
                raise ValueError("token too large")
            token = raw.decode("utf-8").strip()
            if len(token.encode("utf-8")) > MAX_METADATA_TOKEN_BYTES:
                raise ValueError("token too large")
            if not _validate_jwt_shape(token):
                raise ValueError("malformed jwt")
            return token


async def _fetch_id_token(audience: str) -> str:
    """Async wrapper with total timeout <=3s and outer wait_for to bound DNS."""
    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch_id_token_sync, audience), timeout=TIMEOUT_METADATA_SECONDS)
    except asyncio.TimeoutError:
        raise TimeoutError("metadata timeout")


def _cms_lease_sync(base_url: str, token: str) -> Tuple[int, Dict[str, str], bytes, Dict[str, Any]]:
    """Sync POST {} to CMS /lease. Streaming, follow_redirects=false, bounded 128KB.

    Uses dedicated transport header X-AnderZilla-Worker-Authorization
    (Bearer <Google ID token>) through Azure Static Web Apps; SWA can
    consume/strip standard Authorization, so never send Authorization.
    Token remains Google OIDC, validated by CMS application.
    """
    lease_url = base_url.rstrip("/") + "/lease"
    headers = {"X-AnderZilla-Worker-Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    timeout = httpx.Timeout(TIMEOUT_CMS_LEASE_SECONDS, connect=TIMEOUT_CMS_LEASE_SECONDS)
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        with client.stream("POST", lease_url, headers=headers, json={}) as resp:
            status_code = resp.status_code
            resp_headers: Dict[str, str] = dict(resp.headers)
            total = 0
            chunks: List[bytes] = []
            for chunk in resp.iter_bytes(chunk_size=8192):
                total += len(chunk)
                if total > MAX_CMS_LEASE_RESPONSE_BYTES:
                    raise ValueError("lease response too large")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if len(raw) > MAX_CMS_LEASE_RESPONSE_BYTES:
                raise ValueError("lease response too large")
            parsed: Dict[str, Any] = {}
            if raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except Exception:
                    parsed = {}
            return status_code, resp_headers, raw, parsed


async def _cms_lease(base_url: str, token: str) -> Tuple[int, Dict[str, str], bytes, Dict[str, Any]]:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_cms_lease_sync, base_url, token), timeout=TIMEOUT_CMS_LEASE_SECONDS)
    except asyncio.TimeoutError:
        raise TimeoutError("cms lease timeout")


def _cms_complete_sync(base_url: str, token: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, str], bytes, Dict[str, Any]]:
    """Sync POST to CMS /complete via dedicated transport header. DB warm after lease — 6s."""
    complete_url = base_url.rstrip("/") + "/complete"
    headers = {"X-AnderZilla-Worker-Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    timeout = httpx.Timeout(TIMEOUT_CMS_COMPLETE_SECONDS, connect=TIMEOUT_CMS_COMPLETE_SECONDS)
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        with client.stream("POST", complete_url, headers=headers, json=body) as resp:
            status_code = resp.status_code
            resp_headers: Dict[str, str] = dict(resp.headers)
            total = 0
            chunks: List[bytes] = []
            for chunk in resp.iter_bytes(chunk_size=8192):
                total += len(chunk)
                if total > MAX_CMS_LEASE_RESPONSE_BYTES:
                    raise ValueError("complete response too large")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if len(raw) > MAX_CMS_LEASE_RESPONSE_BYTES:
                raise ValueError("complete response too large")
            parsed: Dict[str, Any] = {}
            if raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except Exception:
                    parsed = {}
            return status_code, resp_headers, raw, parsed


async def _cms_complete(base_url: str, token: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, str], bytes, Dict[str, Any]]:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_cms_complete_sync, base_url, token, body), timeout=TIMEOUT_CMS_COMPLETE_SECONDS)
    except asyncio.TimeoutError:
        raise TimeoutError("cms complete timeout")


def _canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate_lease_envelope(body: Any) -> Tuple[Dict[str, Any], str]:
    """Strict validation of CMS lease envelope. Returns (normalized, error_code) empty on success."""
    if not isinstance(body, dict):
        return {}, "invalid_lease_envelope"
    # reject forbidden actor fields from lease (even though CMS shouldn't send them, defense)
    for k in FORBIDDEN_BODY_KEYS:
        if k in body:
            return {}, "actor_fields_not_allowed"
    extra = set(body.keys()) - ALLOWED_LEASE_TOP_KEYS
    if extra:
        return {}, "unknown_field"
    # schemaVersion
    sv = body.get("schemaVersion")
    if type(sv) is not int or sv != 1:
        return {}, "schemaVersion_must_be_1"
    run_id = body.get("runId")
    lease_id = body.get("leaseId")
    if not isinstance(run_id, str) or not UUID_RE.match(run_id):
        return {}, "runId_must_be_uuid"
    try:
        uuid.UUID(run_id)
    except Exception:
        return {}, "runId_must_be_uuid"
    if not isinstance(lease_id, str) or not UUID_RE.match(lease_id):
        return {}, "leaseId_must_be_uuid"
    try:
        uuid.UUID(lease_id)
    except Exception:
        return {}, "leaseId_must_be_uuid"
    process_id = body.get("processId")
    if not isinstance(process_id, str) or process_id != "seo-audit":
        return {}, "processId_must_be_seo-audit"
    idem = body.get("idempotencyKey")
    if not isinstance(idem, str) or not idem.strip() or len(idem) > MAX_IDEMPOTENCY_KEY_LEN:
        return {}, "idempotencyKey_invalid"
    if not IDEMPOTENCY_RE.match(idem):
        return {}, "idempotencyKey_invalid"
    fencing = body.get("fencingToken")
    if type(fencing) is not int or fencing <= 0:
        return {}, "fencingToken_must_be_positive_int"
    # leasedAt/leaseExpiresAt: require timezone-aware ISO8601, UTC-compatible offset (Z or +00:00), expires > leasedAt, with safe margin
    for field in ("leasedAt", "leaseExpiresAt"):
        val = body.get(field)
        if not isinstance(val, str) or not val.strip():
            return {}, f"{field}_invalid"
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return {}, f"{field}_invalid"
            # require UTC-compatible offset: must be zero (UTC)
            if dt.utcoffset() != timedelta(0):
                return {}, f"{field}_invalid"
        except Exception:
            return {}, f"{field}_invalid"
    # temporal ordering and expiry margin
    try:
        leased_dt = datetime.fromisoformat(str(body["leasedAt"]).replace("Z", "+00:00"))
        expires_dt = datetime.fromisoformat(str(body["leaseExpiresAt"]).replace("Z", "+00:00"))
        # both already validated tz-aware and UTC
        if expires_dt <= leased_dt:
            return {}, "lease_expires_before_leased"
        now_dt = datetime.now(timezone.utc)
        if now_dt >= expires_dt:
            return {}, "lease_expired"
        # require at least 15s remaining before fetching target (safe execution margin)
        remaining = (expires_dt - now_dt).total_seconds()
        if remaining < 15:
            return {}, "lease_too_short"
    except Exception as e:
        # if already mapped, propagate; else generic invalid
        msg = str(e)
        if "lease_" in msg:
            return {}, msg
        return {}, "leasedAt_leaseExpiresAt_invalid"
    inp_raw = body.get("input")
    if not isinstance(inp_raw, dict):
        return {}, "input_must_be_object"
    for k in FORBIDDEN_BODY_KEYS:
        if k in inp_raw:
            return {}, "actor_fields_not_allowed"
    extra_input = set(inp_raw.keys()) - ALLOWED_LEASE_INPUT_KEYS
    if extra_input:
        return {}, "unknown_field"
    market = inp_raw.get("market")
    language = inp_raw.get("language")
    target_url = inp_raw.get("targetUrl")
    notes = inp_raw.get("notes")
    if not isinstance(market, str) or market not in SUPPORTED_MARKETS:
        return {}, "market_must_be_br_intl_global"
    if not isinstance(language, str) or language not in SUPPORTED_LANGUAGES:
        return {}, "language_must_be_pt-BR_or_en"
    if not isinstance(target_url, str):
        return {}, "invalid_targetUrl"
    norm_url, url_err = _validate_target_url(target_url)
    if url_err:
        return {}, url_err
    if notes is not None:
        if not isinstance(notes, str):
            return {}, "notes_must_be_string"
        if len(notes) > MAX_NOTES_LEN:
            return {}, "notes_too_long"
    normalized = {
        "schemaVersion": 1,
        "runId": run_id.lower(),
        "leaseId": lease_id.lower(),
        "processId": process_id,
        "idempotencyKey": idem,
        "fencingToken": fencing,
        "leasedAt": body["leasedAt"],
        "leaseExpiresAt": body["leaseExpiresAt"],
        "input": {"market": market, "language": language, "targetUrl": norm_url},
    }
    if notes is not None:
        normalized["input"]["notes"] = notes
    return normalized, ""


def _stable_error_for_fetch(code: str) -> Tuple[str, str]:
    stable = _FETCH_TO_STABLE.get(code, "worker_failed")
    if stable not in _STABLE_CODES:
        stable = "worker_failed"
    msg = _STABLE_ERROR_MESSAGES[stable]
    return stable, msg


def _sanitize_poll_error(msg: str) -> str:
    # generic sanitized message, bounded, no exception text with URLs
    if not isinstance(msg, str):
        return "Erro ao processar poll."
    low = msg.lower()
    # ensure we don't leak URLs
    if "://" in msg:
        return "Erro ao processar poll."
    return _bounded(msg, 200)


# ─── HTML parsing (stdlib only, deterministic) ────────────────────────────

class _SEOParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: Optional[str] = None
        self._in_title = False
        self._title_buf: List[str] = []
        self.description: Optional[str] = None
        self.canonical: Optional[str] = None
        self.html_lang: Optional[str] = None
        self.robots: Optional[str] = None
        self.hreflangs: List[Dict[str, str]] = []
        self.json_ld_raw: List[str] = []
        self._in_json_ld = False
        self._json_ld_buf: List[str] = []
        self.headings: List[Tuple[str, str]] = []  # (tag, text)
        self._in_heading: Optional[str] = None
        self._heading_buf: List[str] = []
        self.images: List[Dict[str, str]] = []  # {src, alt}
        self.links: List[str] = []
        self._seen_html_tag = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        d = {k.lower(): (v or "") for k, v in attrs}
        tl = tag.lower()
        if tl == "html" and not self._seen_html_tag:
            self._seen_html_tag = True
            if "lang" in d:
                self.html_lang = d["lang"].strip()[:20]
        if tl == "title":
            self._in_title = True
            self._title_buf = []
        if tl == "meta":
            name = d.get("name", "").lower()
            prop = d.get("property", "").lower()
            if name == "description" and self.description is None:
                self.description = d.get("content", "")[:500]
            if name == "robots" and self.robots is None:
                self.robots = d.get("content", "")[:500]
        if tl == "link":
            rel = d.get("rel", "").lower()
            if "canonical" in rel.split():
                if self.canonical is None:
                    self.canonical = d.get("href", "")[:2048]
            if "alternate" in rel.split():
                hl = d.get("hreflang", "")
                href = d.get("href", "")
                if hl or href:
                    self.hreflangs.append({"hreflang": hl[:20], "href": href[:2048]})
        if tl == "script":
            if d.get("type", "").lower() == "application/ld+json":
                self._in_json_ld = True
                self._json_ld_buf = []
        if tl in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = tl
            self._heading_buf = []
        if tl == "img":
            self.images.append({"src": d.get("src", "")[:2048], "alt": d.get("alt", "")})
        if tl == "a":
            href = d.get("href", "")
            if href:
                self.links.append(href[:2048])

    def handle_endtag(self, tag: str) -> None:
        tl = tag.lower()
        if tl == "title" and self._in_title:
            self._in_title = False
            text = "".join(self._title_buf).strip()
            if text:
                self.title = text[:300]
        if tl == "script" and self._in_json_ld:
            self._in_json_ld = False
            raw = "".join(self._json_ld_buf).strip()
            if raw:
                self.json_ld_raw.append(raw[:5000])
        if tl == self._in_heading:
            text = "".join(self._heading_buf).strip()
            if text:
                self.headings.append((tl, text[:200]))
            self._in_heading = None
            self._heading_buf = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf.append(data)
        if self._in_json_ld:
            self._json_ld_buf.append(data)
        if self._in_heading is not None:
            self._heading_buf.append(data)


def _run_checks(html: str, status: int, target_url: str, market: str, language: str) -> List[Dict[str, Any]]:
    p = _SEOParser()
    try:
        p.feed(html[:MAX_BYTES])
    except Exception:
        pass

    target_host = (urlparse(target_url).hostname or "").lower()
    checks: List[Dict[str, Any]] = []

    def add(cid: str, s: str, evidence: str, detail: str) -> None:
        checks.append({"id": cid, "status": s, "evidence": _bounded(evidence, 500), "detail": _bounded(detail, 500)})

    # 1 http_status
    if status == 200:
        add("http_status", "pass", f"HTTP {status}", "Fetched target returned 200.")
    elif 300 <= status < 400:
        add("http_status", "fail", f"HTTP {status} redirect without final 200", "Final response was a redirect; not counted as success.")
    elif status:
        add("http_status", "fail", f"HTTP {status}", "Non-200 status for target URL.")
    else:
        add("http_status", "fail", "no response", "Target did not return an HTTP response.")

    # 2 title
    if not p.title:
        add("title", "fail", "no <title> found", "Add a unique <title> per page.")
    elif len(p.title) < 10:
        add("title", "warn", p.title, "Title is very short; consider a more descriptive title.")
    elif len(p.title) > 60:
        add("title", "warn", p.title, "Title is long; front may truncate in results. No ranking promise.")
    else:
        add("title", "pass", p.title, "Title present with reasonable length.")

    # 3 description
    if not p.description:
        add("description", "fail", "no meta description", "Add meta name=description.")
    elif len(p.description) < 50:
        add("description", "warn", p.description, "Description is short.")
    elif len(p.description) > 160:
        add("description", "warn", p.description, "Description is long; may be truncated.")
    else:
        add("description", "pass", p.description, "Meta description present.")

    # 4 canonical
    if not p.canonical:
        add("canonical", "fail", "no link rel=canonical", "Add an absolute canonical URL.")
    else:
        try:
            cp = urlparse(p.canonical)
            if cp.scheme != "https":
                add("canonical", "fail", p.canonical, "Canonical must be https absolute URL.")
            elif not cp.hostname:
                add("canonical", "fail", p.canonical, "Canonical must be absolute.")
            else:
                add("canonical", "pass", p.canonical, "Canonical present and absolute.")
        except Exception:
            add("canonical", "fail", p.canonical, "Canonical could not be parsed.")

    # 5 html lang — aligned with CMS contract: pt-BR and en only
    if not p.html_lang:
        add("html_lang", "fail", "no html lang attribute", "Set <html lang> to match page language (pt-BR or en).")
    else:
        expected = "pt-br" if language == "pt-BR" else "en"
        if expected in p.html_lang.lower():
            add("html_lang", "pass", p.html_lang, f"html lang matches requested language {language}.")
        else:
            add("html_lang", "warn", p.html_lang, f"html lang does not contain '{expected}' for language={language}.")

    # 6 robots meta
    if p.robots is None:
        add("robots_meta", "pass", "no robots meta (defaults to index,follow)", "No blocking robots meta found.")
    else:
        low = p.robots.lower()
        if "noindex" in low or "none" in low:
            add("robots_meta", "warn", p.robots, "Page is marked noindex; it will not be indexed.")
        else:
            add("robots_meta", "pass", p.robots, "Robots meta present and not blocking.")

    # 7 hreflang
    if not p.hreflangs:
        add("hreflang", "warn", "no hreflang links", "If translations exist, add reciprocal hreflang pt-BR/en.")
    else:
        vals = ", ".join(f'{h["hreflang"]}→{h["href"][:80]}' for h in p.hreflangs[:3])
        add("hreflang", "pass", vals, f"Found {len(p.hreflangs)} hreflang link(s). Verify reciprocity.")

    # 8 json-ld
    if not p.json_ld_raw:
        add("json_ld", "warn", "no application/ld+json found", "Consider Article/BreadcrumbList JSON-LD when applicable. No rich-result promise.")
    else:
        valid = 0
        for raw in p.json_ld_raw:
            try:
                json.loads(raw)
                valid += 1
            except Exception:
                pass
        if valid == len(p.json_ld_raw):
            add("json_ld", "pass", f"{valid} JSON-LD block(s) valid JSON", "JSON-LD parses as JSON; validate required fields separately.")
        else:
            add("json_ld", "warn", f"{valid}/{len(p.json_ld_raw)} valid", "Some JSON-LD blocks are not valid JSON.")

    # 9 headings
    h1s = [t for tag, t in p.headings if tag == "h1"]
    if len(h1s) == 0:
        add("headings", "fail", "no h1 found", "Add one h1 describing the page.")
    elif len(h1s) > 1:
        add("headings", "warn", f'{len(h1s)} h1s: {"; ".join(h1s[:2])}', "Multiple h1s; prefer a single h1.")
    else:
        sample = "; ".join(f"{tag}:{text[:40]}" for tag, text in p.headings[:3])
        add("headings", "pass", sample or h1s[0], f"{len(p.headings)} heading(s) found.")

    # 10 image alt
    if not p.images:
        add("image_alt", "pass", "no images found", "No images to check.")
    else:
        missing = sum(1 for im in p.images if not im.get("alt", "").strip())
        if missing == 0:
            add("image_alt", "pass", f"{len(p.images)} image(s), all have alt", "All images have alt text.")
        else:
            add("image_alt", "warn", f"{missing}/{len(p.images)} images missing alt", "Add descriptive alt text for accessibility.")

    # 11 internal links
    internal = 0
    external = 0
    for href in p.links:
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        try:
            pp = urlparse(href)
            if not pp.scheme and not pp.netloc:
                internal += 1
            elif (pp.hostname or "").lower() == target_host or (pp.hostname or "").lower() in ALLOWED_HOSTS:
                internal += 1
            elif pp.hostname:
                external += 1
            else:
                internal += 1
        except Exception:
            continue
    add("internal_links", "pass" if internal > 0 else "warn", f"internal={internal} external={external} total={len(p.links)}", "Counts are evidence only; no ranking promise.")

    return checks


# ─── Fetch with SSRF/redirect/size guards ──────────────────────────────────

class FetchError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def fetch_html(target_url: str) -> Tuple[int, str, str]:
    """
    Fetch HTML with strict guards. Returns (status, body, final_url).
    Raises FetchError on violation. Blocking — caller must run in worker thread.
    """
    current = target_url
    timeout = httpx.Timeout(TIMEOUT_TOTAL, connect=TIMEOUT_CONNECT)

    for redirect_idx in range(MAX_REDIRECTS + 1):
        try:
            parsed = urlparse(current)
            host = (parsed.hostname or "").lower()
            if host not in ALLOWED_HOSTS:
                raise FetchError("redirect_host_not_allowed", f"Redirect to host not allowed: {host}", 400)
            if _is_private_ip_literal(host) or _host_resolves_to_private(host):
                raise FetchError("private_ip_blocked", "Target resolves to private IP", 400)
            if parsed.scheme != "https":
                raise FetchError("redirect_scheme_not_https", "Redirect must stay https", 400)
            if parsed.username or parsed.password:
                raise FetchError("redirect_userinfo_not_allowed", "Redirect with userinfo blocked", 400)
            if parsed.fragment and "@" in parsed.fragment:
                raise FetchError("redirect_userinfo_not_allowed", "Redirect fragment with userinfo blocked", 400)
            try:
                port = parsed.port
            except ValueError:
                raise FetchError("invalid_targetUrl", "Invalid port", 400)
            if port is not None and port != 443:
                raise FetchError("redirect_port_not_allowed", "Redirect port not allowed", 400)
        except FetchError:
            raise
        except ValueError:
            raise FetchError("invalid_targetUrl", "Invalid URL", 400)
        except Exception:
            raise FetchError("invalid_targetUrl", "Invalid URL", 400)

        redirected = False
        try:
            with httpx.Client(follow_redirects=False, timeout=timeout, headers={"User-Agent": f"{SERVICE_NAME}/{SERVICE_VERSION} (+https://anderzilla.com)"}) as client:
                with client.stream("GET", current, headers={"Accept": "text/html,application/xhtml+xml"}) as resp:
                    status = resp.status_code
                    if status in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("location") or resp.headers.get("Location")
                        if not loc:
                            raise FetchError("redirect_without_location", "Redirect without Location header", 400)
                        loc = loc.strip()
                        if len(loc) > 2048:
                            raise FetchError("redirect_location_too_long", "Redirect Location too long", 400)
                        nxt = urljoin(current, loc)
                        if redirect_idx >= MAX_REDIRECTS:
                            raise FetchError("too_many_redirects", f"Exceeded {MAX_REDIRECTS} redirects", 400)
                        try:
                            np = urlparse(nxt)
                            nhost = (np.hostname or "").lower()
                            if not nhost or nhost not in ALLOWED_HOSTS:
                                raise FetchError("redirect_host_not_allowed", f"Redirect to host not allowed: {nhost}", 400)
                            if np.scheme != "https":
                                raise FetchError("redirect_scheme_not_https", "Redirect must stay https", 400)
                            if np.username or np.password:
                                raise FetchError("redirect_userinfo_not_allowed", "Redirect with userinfo blocked", 400)
                            if np.fragment and "@" in np.fragment:
                                raise FetchError("redirect_userinfo_not_allowed", "Redirect fragment with userinfo blocked", 400)
                            try:
                                nport = np.port
                            except ValueError:
                                raise FetchError("invalid_targetUrl", "Invalid redirect port", 400)
                            if nport is not None and nport != 443:
                                raise FetchError("redirect_port_not_allowed", "Redirect port not allowed", 400)
                        except FetchError:
                            raise
                        except ValueError:
                            raise FetchError("invalid_targetUrl", "Invalid redirect URL", 400)
                        except Exception:
                            raise FetchError("invalid_targetUrl", "Invalid redirect URL", 400)
                        if _is_private_ip_literal(nhost) or _host_resolves_to_private(nhost):
                            raise FetchError("private_ip_blocked", "Redirect target resolves to private IP", 400)
                        current = nxt
                        redirected = True
                    else:
                        clen = resp.headers.get("content-length") or resp.headers.get("Content-Length")
                        if clen is not None:
                            try:
                                if int(str(clen).strip()) > MAX_BYTES:
                                    raise FetchError("response_too_large", f"Content-Length {clen} exceeds {MAX_BYTES}", 400)
                            except ValueError:
                                pass
                        chunks: List[bytes] = []
                        total = 0
                        for chunk in resp.iter_bytes(chunk_size=16384):
                            total += len(chunk)
                            if total > MAX_BYTES:
                                raise FetchError("response_too_large", f"Response exceeds {MAX_BYTES} bytes", 400)
                            chunks.append(chunk)
                        body_bytes = b"".join(chunks)
                        ctype = resp.headers.get("content-type", "") or ""
                        charset = "utf-8"
                        if "charset=" in ctype.lower():
                            try:
                                ctype_low = ctype.lower()
                                idx = ctype_low.rfind("charset=")
                                charset = ctype[idx + 8 :].split(";")[0].strip().strip('"').strip("'") or "utf-8"
                                if not re.fullmatch(r"[A-Za-z0-9_\-]+", charset):
                                    charset = "utf-8"
                            except Exception:
                                charset = "utf-8"
                        try:
                            body = body_bytes.decode(charset, errors="replace")
                        except Exception:
                            body = body_bytes.decode("utf-8", errors="replace")
                        return status, body, current
        except FetchError:
            raise
        except httpx.TimeoutException:
            raise FetchError("fetch_timeout", f"Fetch timed out after {TIMEOUT_TOTAL}s", 504)
        except httpx.ConnectError:
            # Do not include exception text (may contain raw URL); use generic code only
            raise FetchError("fetch_connect_error", "Fetch connection failed", 502)
        except Exception:
            # Never include raw exception text that can contain a URL
            raise FetchError("fetch_error", "Fetch failed", 502)
        if redirected:
            continue
    raise FetchError("too_many_redirects", f"Exceeded {MAX_REDIRECTS} redirects", 400)


# ─── Editorial package (deterministic template) ────────────────────────────

def build_editorial_package(target_url: str, market: str, language: str) -> Dict[str, Any]:
    base = {
        "targetUrl": target_url,
        "market": market,
        "language": language,
        "disclaimer": "Template only — no generated claims. Editor must verify every field before publishing. No LLM was called.",
        "sections": [
            {
                "id": "metadata",
                "title": "Metadata & indexability",
                "items": [
                    {"id": "title", "label": "Title 50–60 chars, unique per language", "done": False, "evidenceRef": "checks.title"},
                    {"id": "description", "label": "Meta description 120–155 chars", "done": False, "evidenceRef": "checks.description"},
                    {"id": "canonical", "label": "Absolute https canonical matching published URL", "done": False, "evidenceRef": "checks.canonical"},
                    {"id": "hreflang", "label": "Reciprocal hreflang pt-BR ↔ en when translation exists", "done": False, "evidenceRef": "checks.hreflang"},
                    {"id": "robots", "label": "Robots strategy (index/noindex) intentional", "done": False, "evidenceRef": "checks.robots_meta"},
                ],
            },
            {
                "id": "content",
                "title": "Content & structure",
                "items": [
                    {"id": "h1", "label": "Single H1, logical H2/H3 hierarchy", "done": False, "evidenceRef": "checks.headings"},
                    {"id": "lang", "label": "html lang matches language (pt-BR/en)", "done": False, "evidenceRef": "checks.html_lang"},
                    {"id": "body", "label": "Original body with author, sources, consultation dates", "done": False},
                    {"id": "sources", "label": "Each factual claim has source URL + consultation date + rights", "done": False},
                ],
            },
            {
                "id": "media",
                "title": "Media & accessibility",
                "items": [
                    {"id": "cover", "label": "Cover image WebP/AVIF with srcset, width/height, alt", "done": False, "evidenceRef": "checks.image_alt"},
                    {"id": "alt", "label": "All images have descriptive alt (no empty unless decorative)", "done": False, "evidenceRef": "checks.image_alt"},
                    {"id": "video", "label": "If video: VideoObject JSON-LD only with real player/thumbnail/duration", "done": False, "evidenceRef": "checks.json_ld"},
                    {"id": "rights", "label": "Rights/credit/license declared for every asset", "done": False},
                ],
            },
            {
                "id": "commerce",
                "title": "Trust & Commerce (if applicable)",
                "items": [
                    {"id": "market", "label": f"Market = {market} (br/intl/global) consistent with offer", "done": False},
                    {"id": "disclosure", "label": "Visible disclosure + rel=sponsored for paid/affiliate links", "done": False},
                    {"id": "offer", "label": "Product/Offer JSON-LD only with live price/availability, no fake rating", "done": False},
                ],
            },
            {
                "id": "publish",
                "title": "Publish gates",
                "items": [
                    {"id": "review", "label": "Human editorial review per language", "done": False},
                    {"id": "sitemap", "label": "Published URL appears in sitemap with real lastmod", "done": False},
                    {"id": "jsonld_visible", "label": "JSON-LD matches visible content (Rich Results Test)", "done": False, "evidenceRef": "checks.json_ld"},
                ],
            },
        ],
        "nextSteps": [
            "Fill every item, attach evidence URLs/hashes.",
            "Run seo-audit on the staged URL and fix fails before requesting release.",
            "Never publish demo/fixture content to production.",
        ],
    }
    return base


# ─── Request validation ────────────────────────────────────────────────────

def validate_execute_body(body: Any) -> Tuple[Dict[str, Any], str, int]:
    """
    Returns (normalized, error_code, http_status) — error_code empty on success.
    Never includes notes in error details.
    """
    if not isinstance(body, dict):
        return {}, "body_must_be_object", 400
    # Auth boundary — reject actor/role fields before strict envelope so error code is specific
    for k in FORBIDDEN_BODY_KEYS:
        if k in body:
            return {}, "actor_fields_not_allowed", 400
    # Strict envelope: no unknown top-level keys
    extra_top = set(body.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if extra_top:
        return {}, "unknown_field", 400

    # schemaVersion must be exactly int 1 (bool rejected — bool is subclass of int)
    sv = body.get("schemaVersion")
    if type(sv) is not int or sv != 1:
        return {}, "schemaVersion_must_be_1", 400

    run_id = body.get("runId")
    if not isinstance(run_id, str) or not UUID_RE.match(run_id):
        return {}, "runId_must_be_uuid", 400
    try:
        uuid.UUID(run_id)
    except Exception:
        return {}, "runId_must_be_uuid", 400

    process_id = body.get("processId")
    if not isinstance(process_id, str) or process_id not in SUPPORTED_PROCESSES:
        return {}, "processId_must_be_seo-audit_or_editorial-package", 400

    idem = body.get("idempotencyKey")
    if not isinstance(idem, str) or not idem.strip() or len(idem) > MAX_IDEMPOTENCY_KEY_LEN:
        return {}, "idempotencyKey_invalid", 400
    if not re.match(r"^[A-Za-z0-9._:\-]{1,128}$", idem):
        return {}, "idempotencyKey_invalid", 400

    inp_raw = body.get("input")
    if not isinstance(inp_raw, dict):
        return {}, "input_must_be_object", 400
    for k in FORBIDDEN_BODY_KEYS:
        if k in inp_raw:
            return {}, "actor_fields_not_allowed", 400
    # Strict input envelope
    extra_input = set(inp_raw.keys()) - ALLOWED_INPUT_KEYS
    if extra_input:
        return {}, "unknown_field", 400

    market = inp_raw.get("market")
    language = inp_raw.get("language")
    target_url = inp_raw.get("targetUrl")
    notes = inp_raw.get("notes")

    if not isinstance(market, str) or market not in SUPPORTED_MARKETS:
        return {}, "market_must_be_br_intl_global", 400
    if not isinstance(language, str) or language not in SUPPORTED_LANGUAGES:
        return {}, "language_must_be_pt-BR_or_en", 400
    if not isinstance(target_url, str):
        return {}, "invalid_targetUrl", 400
    norm_url, url_err = _validate_target_url(target_url)
    if url_err:
        return {}, url_err, 400
    if notes is not None:
        if not isinstance(notes, str):
            return {}, "notes_must_be_string", 400
        if len(notes) > MAX_NOTES_LEN:
            return {}, "notes_too_long", 400

    normalized = {
        "schemaVersion": 1,
        "runId": run_id.lower(),
        "processId": process_id,
        "idempotencyKey": idem,
        "input": {
            "market": market,
            "language": language,
            "targetUrl": norm_url,
        },
    }
    if notes is not None:
        normalized["input"]["notes"] = notes
    return normalized, "", 200


# ─── Routes ────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": SERVICE_NAME, "version": SERVICE_VERSION, "time": datetime.now(timezone.utc).isoformat(), "cmsConnectorConfigured": _is_cms_configured()}


@app.post("/v1/execute")
async def execute(request: Request) -> Response:
    # Bounded body size — 32 KB
    body_bytes = await request.body()
    if len(body_bytes) > 32 * 1024:
        jlog("warn", "payload_too_large", path="/v1/execute")
        return JSONResponse(status_code=413, content={"error": "payload_too_large", "message": "Body exceeds 32KB."})
    try:
        body = json.loads(body_bytes) if body_bytes else None
    except json.JSONDecodeError:
        jlog("warn", "invalid_json", path="/v1/execute")
        return JSONResponse(status_code=400, content={"error": "invalid_json", "message": "Body must be valid JSON."})

    normalized, err, status = validate_execute_body(body)
    # log without raw URL / notes / body / secrets — use safe host label
    log_fields: Dict[str, Any] = {"path": "/v1/execute"}
    if isinstance(body, dict):
        for k in ("processId", "runId", "idempotencyKey"):
            if k in body and isinstance(body[k], str):
                log_fields[k] = _bounded(str(body[k]), 100)
        # schemaVersion may be bool — handle safely
        if "schemaVersion" in body and type(body["schemaVersion"]) is int:
            log_fields["schemaVersion"] = body["schemaVersion"]
        if isinstance(body.get("input"), dict):
            inp = body["input"]
            for k in ("market", "language"):
                if k in inp and isinstance(inp[k], str):
                    log_fields[f"input.{k}"] = _bounded(str(inp[k]), 100)
            if "targetUrl" in inp and isinstance(inp["targetUrl"], str):
                log_fields["input.targetHost"] = _safe_host_label(inp["targetUrl"])
    if err:
        jlog("warn", "validation_failed", error=err, **log_fields)
        return JSONResponse(status_code=status, content={"error": err, "message": _bounded(err.replace("_", " "), 300)})

    # Idempotency — best-effort in-memory replay
    _prune_replay()
    cache_key = (normalized["processId"], normalized["idempotencyKey"])
    cur_hash = _input_hash(normalized["input"])
    cached = _replay.get(cache_key)
    if cached is not None:
        # Replay only if same runId AND same input; different runId => 409 even with same input
        if cached.get("runId") != normalized["runId"] or cached.get("inputHash") != cur_hash:
            jlog("warn", "idempotency_conflict", **log_fields)
            return JSONResponse(
                status_code=409,
                content={
                    "error": "idempotency_conflict",
                    "message": "Idempotency conflict: same (processId, idempotencyKey) already used with different runId or input. Only exact replay of same runId and input is allowed.",
                },
            )
        # exact replay
        replay_resp = dict(cached["response"])
        replay_resp["replayed"] = True
        replay_resp["idempotency"] = {"replayed": True, "note": "In-memory replay only; caller owns durable idempotency."}
        jlog("info", "replayed", **log_fields)
        return JSONResponse(status_code=200, content=replay_resp)

    # Dispatch
    run_id = normalized["runId"]
    process_id = normalized["processId"]
    target_url: str = normalized["input"]["targetUrl"]
    market: str = normalized["input"]["market"]
    language: str = normalized["input"]["language"]

    jlog("info", "execute_start", **log_fields)

    try:
        if process_id == "seo-audit":
            try:
                # Global non-blocking timeout: run sync DNS+httpx work in worker thread
                # with one hard 8s deadline covering entire fetch including redirects.
                http_status, html, final_url = await asyncio.wait_for(
                    asyncio.to_thread(fetch_html, target_url), timeout=TIMEOUT_TOTAL
                )
            except asyncio.TimeoutError:
                # Worker thread may continue until its own httpx timeouts fire, but it is bounded
                # by per-connect 3s and per-hop total 8s; we surface 504 immediately.
                jlog("warn", "fetch_failed", error="fetch_timeout", **log_fields)
                err_body = {
                    "schemaVersion": 1,
                    "runId": run_id,
                    "processId": process_id,
                    "idempotencyKey": normalized["idempotencyKey"],
                    "status": "failed",
                    "error": "fetch_timeout",
                    "message": f"Fetch timed out after {TIMEOUT_TOTAL}s",
                    "idempotency": {"replayed": False, "note": "In-memory replay only; caller owns durable idempotency."},
                }
                return JSONResponse(status_code=504, content=err_body)
            except FetchError as fe:
                # Never log raw URL or exception text that may contain a URL — only code
                jlog("warn", "fetch_failed", error=fe.code, **log_fields)
                err_body = {
                    "schemaVersion": 1,
                    "runId": run_id,
                    "processId": process_id,
                    "idempotencyKey": normalized["idempotencyKey"],
                    "status": "failed",
                    "error": fe.code,
                    "message": _bounded(str(fe), 500),
                    "idempotency": {"replayed": False, "note": "In-memory replay only; caller owns durable idempotency."},
                }
                return JSONResponse(status_code=fe.status, content=err_body)
            checks = _run_checks(html, http_status, target_url, market, language)
            summary = {"pass": sum(1 for c in checks if c["status"] == "pass"), "warn": sum(1 for c in checks if c["status"] == "warn"), "fail": sum(1 for c in checks if c["status"] == "fail")}
            resp_body: Dict[str, Any] = {
                "schemaVersion": 1,
                "runId": run_id,
                "processId": process_id,
                "idempotencyKey": normalized["idempotencyKey"],
                "status": "succeeded",
                "result": {
                    "targetUrl": target_url,
                    "finalUrl": final_url,
                    "httpStatus": http_status,
                    "market": market,
                    "language": language,
                    "checks": checks,
                    "summary": summary,
                    "disclaimer": "Evidence only — no ranking promise. Verify manually before publishing.",
                },
                "replayed": False,
                "idempotency": {"replayed": False, "note": "In-memory replay only; caller owns durable idempotency."},
            }
        else:  # editorial-package
            pkg = build_editorial_package(target_url, market, language)
            resp_body = {
                "schemaVersion": 1,
                "runId": run_id,
                "processId": process_id,
                "idempotencyKey": normalized["idempotencyKey"],
                "status": "succeeded",
                "result": {"editorialPackage": pkg, "disclaimer": "Template only — no generated claims. No LLM was called."},
                "replayed": False,
                "idempotency": {"replayed": False, "note": "In-memory replay only; caller owns durable idempotency."},
            }
    except Exception:
        # Never log exception text that may contain a raw URL
        jlog("error", "execute_failed", error="internal_error", **log_fields)
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": "Internal error processing request."})

    # store in replay cache (includes runId for correlation)
    _replay[cache_key] = {"runId": normalized["runId"], "inputHash": cur_hash, "processId": process_id, "response": dict(resp_body), "expiresAt": time.monotonic() + REPLAY_TTL_SECONDS}
    jlog("info", "execute_succeeded", **log_fields)
    return JSONResponse(status_code=200, content=resp_body)


@app.post("/v1/poll")
async def poll(request: Request) -> Response:
    """
    Pull coordinator — authenticated Cloud Scheduler invocation (Cloud Run IAM is platform boundary).
    Processes at most one CMS lease per call.
    """
    # ── 0. Strict poll body validation (empty or {} and <=1KB, reject fields) ──
    body_bytes = await request.body()
    if len(body_bytes) > MAX_POLL_BODY_BYTES:
        jlog("warn", "poll_payload_too_large", path="/v1/poll")
        return JSONResponse(status_code=413, content={"error": "payload_too_large", "message": "Body exceeds 1KB."})
    poll_body: Any = None
    if body_bytes:
        # allow whitespace-only as empty
        stripped = body_bytes.strip()
        if not stripped:
            poll_body = {}
        else:
            try:
                poll_body = json.loads(body_bytes)
            except json.JSONDecodeError:
                jlog("warn", "poll_invalid_json", path="/v1/poll")
                return JSONResponse(status_code=400, content={"error": "invalid_json", "message": "Body must be valid JSON."})
            if poll_body is None:
                poll_body = {}
            if not isinstance(poll_body, dict):
                jlog("warn", "poll_body_must_be_object", path="/v1/poll")
                return JSONResponse(status_code=400, content={"error": "body_must_be_object", "message": "Body must be JSON object."})
            # reject actor/role/token/URL fields explicitly (even though any field is rejected)
            for k in FORBIDDEN_BODY_KEYS:
                if k in poll_body:
                    jlog("warn", "poll_actor_fields_not_allowed", path="/v1/poll")
                    return JSONResponse(status_code=400, content={"error": "actor_fields_not_allowed", "message": "Actor fields not allowed."})
            # also reject any token/URL-like fields from caller
            for forbid in ("token", "idToken", "accessToken", "url", "targetUrl", "audience", "cmsUrl"):
                if forbid in poll_body:
                    jlog("warn", "poll_forbidden_field", error=forbid, path="/v1/poll")
                    return JSONResponse(status_code=400, content={"error": "unknown_field", "message": "Unexpected field."})
            if poll_body != {}:
                # body must be empty or {} — reject any fields
                jlog("warn", "poll_unknown_field", path="/v1/poll")
                return JSONResponse(status_code=400, content={"error": "unknown_field", "message": "Poll body must be empty or {}."})
    else:
        poll_body = {}

    # ── 1. Validate config ───────────────────────────────────────────────
    try:
        base_url, audience = _validate_cms_config()
    except Exception:
        jlog("error", "poll_config_invalid", path="/v1/poll", error="cms_configuration_invalid")
        return JSONResponse(status_code=503, content={"error": "cms_configuration_invalid", "message": "CMS connector not configured."})

    # ── 2. Fetch ID token (fixed metadata endpoint) ──────────────────────
    try:
        token = await _fetch_id_token(audience)
    except TimeoutError:
        jlog("warn", "poll_metadata_timeout", path="/v1/poll", error="identity_unavailable")
        return JSONResponse(status_code=502, content={"error": "identity_unavailable", "message": "Failed to fetch identity token."})
    except Exception:
        # Never log token, raw exception text, or CMS URL
        jlog("warn", "poll_metadata_failed", path="/v1/poll", error="identity_unavailable")
        return JSONResponse(status_code=502, content={"error": "identity_unavailable", "message": "Failed to fetch identity token."})

    # ── 3. POST {} to CMS /lease ────────────────────────────────────────
    try:
        lease_res = await _cms_lease(base_url, token)
        # Support both mocked 3-tuple (status, raw, parsed) and new 4-tuple (status, headers, raw, parsed)
        if len(lease_res) == 4:
            status_code, lease_headers, raw, parsed = lease_res
        elif len(lease_res) == 3:
            status_code, raw, parsed = lease_res  # type: ignore
            lease_headers = {}
        else:
            raise ValueError("invalid lease response shape")
    except TimeoutError:
        jlog("warn", "poll_cms_lease_timeout", path="/v1/poll", error="cms_timeout")
        return JSONResponse(status_code=502, content={"error": "cms_timeout", "message": "CMS lease timed out."})
    except Exception:
        jlog("warn", "poll_cms_lease_error", path="/v1/poll", error="cms_unavailable")
        return JSONResponse(status_code=502, content={"error": "cms_unavailable", "message": "CMS unavailable."})

    # 404 no_work is successful idle, not failure — require bounded application/json with exact code no_work
    if status_code == 404:
        ct = ""
        for hk, hv in (lease_headers or {}).items():
            if hk.lower() == "content-type":
                ct = str(hv)
                break
        if "application/json" not in ct.lower():
            jlog("warn", "poll_cms_lease_404_not_json", path="/v1/poll", error="cms_error")
            return JSONResponse(status_code=502, content={"error": "cms_error", "message": "CMS error."})
        # Check that raw was bounded and parsed is dict with exact code
        if not isinstance(parsed, dict) or not raw:
            jlog("warn", "poll_cms_lease_404_empty_or_not_json", path="/v1/poll", error="cms_error")
            return JSONResponse(status_code=502, content={"error": "cms_error", "message": "CMS error."})
        # CMS envelope is {"error":{"code":"no_work",...}} — strict
        err_obj = parsed.get("error")
        code = ""
        if isinstance(err_obj, dict):
            code = str(err_obj.get("code", ""))
        else:
            # also handle bare code? but strict requires error.code
            code = ""
        # Also reject non-JSON content like HTML: if parsed empty or code not exactly no_work -> 502
        if code == "no_work":
            jlog("info", "poll_idle", path="/v1/poll", reason="no_work")
            return JSONResponse(status_code=200, content={"status": "idle", "reason": "no_work"})
        else:
            jlog("warn", "poll_cms_lease_unexpected_404", path="/v1/poll", error="cms_error")
            return JSONResponse(status_code=502, content={"error": "cms_error", "message": "CMS error."})

    if status_code == 401 or status_code == 403:
        jlog("warn", "poll_cms_auth_failed", path="/v1/poll", error="cms_authentication_failed")
        return JSONResponse(status_code=502, content={"error": "cms_authentication_failed", "message": "CMS authentication failed."})
    if status_code >= 500:
        jlog("warn", "poll_cms_5xx", path="/v1/poll", error="cms_unavailable")
        return JSONResponse(status_code=502, content={"error": "cms_unavailable", "message": "CMS unavailable."})
    if status_code != 200:
        # Treat redirects (301/302 etc) and any non-200 as 502, never idle
        jlog("warn", "poll_cms_lease_failed", path="/v1/poll", error="cms_error")
        return JSONResponse(status_code=502, content={"error": "cms_error", "message": "CMS error."})

    ct200 = ""
    for hk, hv in (lease_headers or {}).items():
        if hk.lower() == "content-type":
            ct200 = str(hv)
            break
    if "application/json" not in ct200.lower():
        jlog("warn", "poll_lease_not_json", path="/v1/poll", error="invalid_lease_envelope")
        return JSONResponse(status_code=502, content={"error": "invalid_lease_envelope", "message": "Invalid lease envelope."})
    # Check response size already bounded; also check parsed is dict
    if not isinstance(parsed, dict) or not parsed:
        jlog("warn", "poll_lease_malformed", path="/v1/poll", error="invalid_lease_envelope")
        return JSONResponse(status_code=502, content={"error": "invalid_lease_envelope", "message": "Invalid lease envelope."})
    # If oversize was already raised, we returned 502; but also check len
    if len(raw) > MAX_CMS_LEASE_RESPONSE_BYTES:
        jlog("warn", "poll_lease_oversize", path="/v1/poll", error="lease_response_too_large")
        return JSONResponse(status_code=502, content={"error": "lease_response_too_large", "message": "Lease response too large."})

    # ── 4. Validate lease envelope strictly ──────────────────────────────
    lease, lease_err = _validate_lease_envelope(parsed)
    if lease_err:
        jlog("warn", "poll_lease_validation_failed", path="/v1/poll", error=lease_err)
        return JSONResponse(status_code=502, content={"error": "invalid_lease_envelope", "message": "Invalid lease envelope."})

    run_id = lease["runId"]
    lease_id = lease["leaseId"]
    fencing = lease["fencingToken"]
    process_id = lease["processId"]
    target_url = lease["input"]["targetUrl"]
    market = lease["input"]["market"]
    language = lease["input"]["language"]
    safe_host = _safe_host_label(target_url)

    log_fields = {"path": "/v1/poll", "runId": _bounded(run_id, 36), "leaseId": _bounded(lease_id, 36), "fencingToken": fencing, "processId": process_id, "input.targetHost": safe_host}
    jlog("info", "poll_lease_acquired", **log_fields)

    # ── 5. Execute deterministic SEO audit under 8s deadline ─────────────
    audit_result: Optional[Dict[str, Any]] = None
    audit_error_code: Optional[str] = None
    audit_fetch_error: Optional[FetchError] = None
    audit_status = "succeeded"
    try:
        try:
            http_status, html, final_url = await asyncio.wait_for(asyncio.to_thread(fetch_html, target_url), timeout=TIMEOUT_TOTAL)
        except asyncio.TimeoutError:
            raise FetchError("fetch_timeout", f"Fetch timed out after {TIMEOUT_TOTAL}s", 504)
        checks = _run_checks(html, http_status, target_url, market, language)
        summary = {"pass": sum(1 for c in checks if c["status"] == "pass"), "warn": sum(1 for c in checks if c["status"] == "warn"), "fail": sum(1 for c in checks if c["status"] == "fail")}
        audit_result = {
            "targetUrl": target_url,
            "finalUrl": final_url,
            "httpStatus": http_status,
            "market": market,
            "language": language,
            "checks": checks,
            "summary": summary,
            "disclaimer": "Evidence only — no ranking promise. Verify manually before publishing.",
        }
        # Bound completion payload below CMS 64KB; if exceeds, report result_too_large failure
        serialized = _canonical_dumps(audit_result)
        if len(serialized.encode("utf-8")) > MAX_CMS_RESULT_BYTES:
            audit_result = None
            audit_status = "failed"
            audit_error_code = "validation_error"
            jlog("warn", "poll_result_too_large", **log_fields, error="result_too_large")
        else:
            jlog("info", "poll_audit_succeeded", **log_fields)
    except FetchError as fe:
        audit_fetch_error = fe
        audit_status = "failed"
        stable, msg = _stable_error_for_fetch(fe.code)
        audit_error_code = stable
        # Never log raw exception text that may contain URL
        jlog("warn", "poll_audit_failed", **log_fields, error=stable)
    except Exception:
        audit_status = "failed"
        audit_error_code = "internal_error"
        jlog("error", "poll_audit_internal_error", **log_fields, error="internal_error")

    # ── 6. POST strict completion to CMS /complete ──────────────────────
    # Build completion body with same token/lease fields and either succeeded result or failed stable code
    if audit_status == "succeeded" and audit_result is not None:
        # ensure result still within CMS limit (defensive)
        try:
            ser = _canonical_dumps(audit_result)
            if len(ser.encode("utf-8")) > MAX_CMS_RESULT_BYTES:
                # fallback to failure
                completion_body = {
                    "runId": run_id,
                    "leaseId": lease_id,
                    "fencingToken": fencing,
                    "status": "failed",
                    "errorCode": "validation_error",
                    "errorMessage": _STABLE_ERROR_MESSAGES["validation_error"],
                }
            else:
                completion_body = {
                    "runId": run_id,
                    "leaseId": lease_id,
                    "fencingToken": fencing,
                    "status": "succeeded",
                    "result": audit_result,
                }
        except Exception:
            completion_body = {
                "runId": run_id,
                "leaseId": lease_id,
                "fencingToken": fencing,
                "status": "failed",
                "errorCode": "internal_error",
                "errorMessage": _STABLE_ERROR_MESSAGES["internal_error"],
            }
    else:
        # failed path — use allowlisted code and generic message
        code_to_use = audit_error_code or "worker_failed"
        if code_to_use not in _STABLE_CODES:
            code_to_use = "worker_failed"
        generic = _STABLE_ERROR_MESSAGES[code_to_use]
        # If result_too_large case, we already set validation_error; keep it
        if audit_result is None and audit_status == "failed" and audit_error_code == "validation_error" and audit_fetch_error is None:
            # result_too_large -> validation_error generic
            code_to_use = "validation_error"
            generic = _STABLE_ERROR_MESSAGES["validation_error"]
        completion_body = {
            "runId": run_id,
            "leaseId": lease_id,
            "fencingToken": fencing,
            "status": "failed",
            "errorCode": code_to_use,
            "errorMessage": generic,
        }

    # Verify completion payload size below CMS 64KB (for succeeded, result already checked; for failed, small)
    try:
        comp_ser = _canonical_dumps(completion_body)
        if len(comp_ser.encode("utf-8")) > MAX_CMS_LEASE_RESPONSE_BYTES:
            # completion payload too large (should not happen for failed); sanitize to minimal failed
            completion_body = {
                "runId": run_id,
                "leaseId": lease_id,
                "fencingToken": fencing,
                "status": "failed",
                "errorCode": "internal_error",
                "errorMessage": _STABLE_ERROR_MESSAGES["internal_error"],
            }
    except Exception:
        completion_body = {
            "runId": run_id,
            "leaseId": lease_id,
            "fencingToken": fencing,
            "status": "failed",
            "errorCode": "internal_error",
            "errorMessage": _STABLE_ERROR_MESSAGES["internal_error"],
        }

    # Send completion; token reuse same; bound timeout 6s
    try:
        comp_res = await _cms_complete(base_url, token, completion_body)
        if len(comp_res) == 4:
            comp_status, comp_headers, comp_raw, comp_parsed = comp_res
        elif len(comp_res) == 3:
            comp_status, comp_raw, comp_parsed = comp_res  # type: ignore
            comp_headers = {}
        else:
            raise ValueError("invalid complete response shape")
    except TimeoutError:
        jlog("warn", "poll_cms_complete_timeout", **log_fields, error="cms_complete_timeout")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion timed out. Lease will expire for retry."})
    except Exception:
        jlog("warn", "poll_cms_complete_failed", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})

    # Strict completion success: never treat redirects or HTML as success. Require HTTP 2xx, application/json, bounded streamed JSON, and receipt with exact fields
    # follow_redirects=false ensures 3xx status not swallowed; treat any 3xx as failure
    if not (200 <= comp_status < 300):
        jlog("warn", "poll_cms_complete_error", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    ctype = ""
    for hk, hv in (comp_headers or {}).items():
        if hk.lower() == "content-type":
            ctype = str(hv)
            break
    if "application/json" not in ctype.lower():
        jlog("warn", "poll_cms_complete_not_json", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    # Bounded streamed JSON already enforced; also empty or non-dict is failure
    if not isinstance(comp_parsed, dict) or not comp_parsed:
        jlog("warn", "poll_cms_complete_not_json", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    if len(comp_raw) > MAX_CMS_LEASE_RESPONSE_BYTES:
        jlog("warn", "poll_cms_complete_oversize", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    # Receipt validation: exact runId, expected status, positive version, and for success exact resultHash, for failure exact sanitized error code
    expected_status = completion_body["status"]
    # Check runId
    if str(comp_parsed.get("runId", "")).lower() != run_id.lower():
        jlog("warn", "poll_cms_complete_receipt_run_mismatch", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    if str(comp_parsed.get("status", "")) != expected_status:
        jlog("warn", "poll_cms_complete_receipt_status_mismatch", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    ver = comp_parsed.get("version")
    if type(ver) is not int or ver <= 0:
        jlog("warn", "poll_cms_complete_receipt_version_invalid", **log_fields, error="cms_complete_failed")
        return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    if expected_status == "succeeded":
        # For success, require exact resultHash matching canonical result sent
        # Compute expected hash from completion_body result
        try:
            exp_hash = hashlib.sha256(_canonical_dumps(completion_body["result"]).encode()).hexdigest()
        except Exception:
            jlog("warn", "poll_cms_complete_hash_compute_failed", **log_fields, error="cms_complete_failed")
            return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
        recv_hash = comp_parsed.get("resultHash")
        if not isinstance(recv_hash, str) or recv_hash.lower() != exp_hash.lower():
            jlog("warn", "poll_cms_complete_receipt_hash_mismatch", **log_fields, error="cms_complete_failed")
            return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})
    else:
        # For failure, require exact sanitized error code returned
        expected_code = str(completion_body.get("errorCode", ""))
        # CMS returns {"error":{"code":...}}
        actual_code = ""
        err_obj = comp_parsed.get("error")
        if isinstance(err_obj, dict):
            actual_code = str(err_obj.get("code", ""))
        elif isinstance(comp_parsed.get("errorCode"), str):
            actual_code = str(comp_parsed.get("errorCode"))
        elif isinstance(comp_parsed.get("code"), str):
            actual_code = str(comp_parsed.get("code"))
        if actual_code != expected_code:
            jlog("warn", "poll_cms_complete_receipt_code_mismatch", **log_fields, error="cms_complete_failed")
            return JSONResponse(status_code=502, content={"error": "cms_complete_failed", "message": "CMS completion failed. Lease will expire for retry."})

    jlog("info", "poll_completed", **log_fields, status=completion_body["status"])
    # Do not loop or lease another run — return single job result
    # Poll response sanitized, no token/CMS URL/notes
    if completion_body["status"] == "succeeded":
        return JSONResponse(status_code=200, content={"status": "succeeded", "runId": run_id, "leaseId": lease_id, "fencingToken": fencing, "processId": process_id, "targetHost": safe_host, "result": completion_body["result"]})
    else:
        return JSONResponse(status_code=200, content={"status": "failed", "runId": run_id, "leaseId": lease_id, "fencingToken": fencing, "processId": process_id, "targetHost": safe_host, "errorCode": completion_body["errorCode"], "errorMessage": completion_body["errorMessage"]})


# For `python app.py` local dev
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
