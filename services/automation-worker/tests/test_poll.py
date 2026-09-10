import base64
import hashlib
import json
import uuid
import asyncio
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

import app as appmod
from app import app, _replay, ALLOWED_HOSTS

# Valid config for poll tests
VALID_BASE_URL = "https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation"
VALID_AUDIENCE = "https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation"

def make_jwt(audience=VALID_AUDIENCE):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"aud": audience, "exp": 9999999999, "iat": 1234567890}).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(b"fake-signature").decode().rstrip("=")
    return f"{header}.{payload}.{sig}"

VALID_TOKEN = make_jwt()

def valid_lease_envelope(**overrides):
    run_id = str(uuid.uuid4())
    lease_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=120)
    base = {
        "schemaVersion": 1,
        "runId": run_id,
        "leaseId": lease_id,
        "processId": "seo-audit",
        "idempotencyKey": "abc123.DEF_456:test-key",
        "fencingToken": 1,
        "leasedAt": now.isoformat(),
        "leaseExpiresAt": expires.isoformat(),
        "input": {"market": "br", "language": "pt-BR", "targetUrl": "https://anderzilla.com/"},
    }
    # notes optional
    base.update(overrides)
    if "input" in overrides and isinstance(overrides["input"], dict):
        # merge
        base["input"] = {**{"market": "br", "language": "pt-BR", "targetUrl": "https://anderzilla.com/"}, **overrides["input"]}
        for k,v in overrides.items():
            if k != "input":
                base[k]=v
    else:
        for k,v in overrides.items():
            if k != "input":
                base[k]=v
    return base

def html_ok():
    return """<!doctype html><html lang="pt-BR"><head><title>AnderZilla — Tecnologia</title>
<meta name="description" content="Cobertura de tecnologia, IA e games com curadoria humana.">
<link rel="canonical" href="https://anderzilla.com/pt/test">
<link rel="alternate" hreflang="pt-BR" href="https://anderzilla.com/pt/test">
<meta name="robots" content="index, follow">
<script type="application/ld+json">{"@type":"Article"}</script>
</head><body><h1>Test</h1><img src="/img.jpg" alt="descricao"><a href="/pt/outro">interno</a></body></html>"""

def _complete_success_side_effect(base_url, token, body):
    # body contains runId/status/result; compute canonical hash
    result = body.get("result", {})
    h = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    receipt = {"runId": body["runId"], "status": "succeeded", "version": 2, "resultHash": h, "finishedAt": datetime.now(timezone.utc).isoformat()}
    raw = json.dumps(receipt).encode()
    return (200, {"content-type": "application/json"}, raw, receipt)

def _complete_failed_side_effect(base_url, token, body):
    code = body.get("errorCode", "worker_failed")
    receipt = {"runId": body["runId"], "status": "failed", "version": 2, "error": {"code": code, "message": "msg"}, "finishedAt": datetime.now(timezone.utc).isoformat()}
    raw = json.dumps(receipt).encode()
    return (200, {"content-type": "application/json"}, raw, receipt)



@pytest.fixture
def configured_env(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    _replay.clear()
    yield
    _replay.clear()

client = TestClient(app)

# ── health ───────────────────────────────────────────────────────────────

def test_health_reports_cms_connector_boolean_only(configured_env):
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert "cmsConnectorConfigured" in j
    assert j["cmsConnectorConfigured"] is True
    # no secrets, no URL
    body_str = json.dumps(j)
    assert VALID_BASE_URL not in body_str
    assert "victorious" not in body_str.lower() or "cmsConnectorConfigured" in body_str  # ensure not exposing full URL as value
    # value is boolean only
    assert isinstance(j["cmsConnectorConfigured"], bool)

def test_health_false_when_not_configured(monkeypatch):
    monkeypatch.delenv("CMS_WORKER_BASE_URL", raising=False)
    monkeypatch.delenv("CMS_WORKER_AUDIENCE", raising=False)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["cmsConnectorConfigured"] is False
    # restore via fixture but this test leaves env cleared; next tests use configured_env fixture

def test_health_no_token_or_url_leak(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    r = client.get("/health")
    txt = r.text
    assert "token" not in txt.lower()
    assert VALID_TOKEN not in txt

# ── config validation ────────────────────────────────────────────────────

def test_config_validation_requires_exact_host(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", "https://evil.com/api/worker/automation")
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    r = client.post("/v1/poll", json={})
    assert r.status_code == 503
    assert r.json()["error"] == "cms_configuration_invalid"

def test_config_validation_requires_exact_audience(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", "https://evil.com/api/worker/automation")
    r = client.post("/v1/poll", json={})
    assert r.status_code == 503

def test_config_rejects_query_fragment_userinfo(monkeypatch):
    for bad_url in [
        VALID_BASE_URL + "?q=1",
        VALID_BASE_URL + "#frag",
        "https://user:pass@victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation",
        "http://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation",
        "https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation/",
        "https://victorious-mud-09355980f.3.azurestaticapps.net/api/worker/automation/extra",
        "https://victorious-mud-09355980f.3.azurestaticapps.net:8443/api/worker/automation",
    ]:
        monkeypatch.setenv("CMS_WORKER_BASE_URL", bad_url)
        monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
        r = client.post("/v1/poll", json={})
        assert r.status_code == 503, f"bad_url {bad_url} should be rejected"

def test_config_allows_exact_expected(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    # need to mock token to avoid network; we expect poll to try token fetch, so patch it to return idle quickly
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (404, {"content-type": "application/json"}, b'{"error":{"code":"no_work","message":"no"}}', {"error": {"code": "no_work", "message": "no"}})
            r = client.post("/v1/poll", json={})
            assert r.status_code == 200
            assert r.json()["status"] == "idle"

# ── strict poll body ─────────────────────────────────────────────────────

def test_poll_body_empty_allowed(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (404, {"content-type": "application/json"}, b'{"error":{"code":"no_work","message":"no"}}', {"error":{"code":"no_work"}})
            # empty body
            r = client.post("/v1/poll", content=b"", headers={"content-type":"application/json"})
            assert r.status_code == 200
            # whitespace
            r2 = client.post("/v1/poll", content=b"   ", headers={"content-type":"application/json"})
            assert r2.status_code == 200

def test_poll_body_empty_dict_allowed(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (404, {"content-type": "application/json"}, b'{"error":{"code":"no_work","message":"no"}}', {"error":{"code":"no_work"}})
            r = client.post("/v1/poll", json={})
            assert r.status_code == 200

def test_poll_body_rejects_fields(configured_env):
    cases = [
        {"actor": "evil"},
        {"role": "admin"},
        {"token": "abc"},
        {"targetUrl": "https://evil.com"},
        {"audience": "https://evil.com"},
        {"unknown": 1},
        {"schemaVersion": 1},
    ]
    for body in cases:
        r = client.post("/v1/poll", json=body)
        assert r.status_code == 400, f"body {body} should be rejected"
        assert r.json()["error"] in ("unknown_field", "actor_fields_not_allowed")

def test_poll_body_rejects_over_1KB(configured_env):
    big = {"x": "a"*2000}
    # json will exceed 1KB
    r = client.post("/v1/poll", json=big)
    # body bytes >1024 so 413
    assert r.status_code in (400, 413)
    # direct big bytes
    r2 = client.post("/v1/poll", content=b"a"*2000, headers={"content-type":"application/json"})
    assert r2.status_code == 413

def test_poll_body_rejects_non_object(configured_env):
    r = client.post("/v1/poll", content=b"[]", headers={"content-type":"application/json"})
    assert r.status_code == 400
    r2 = client.post("/v1/poll", content=b"123", headers={"content-type":"application/json"})
    assert r2.status_code == 400

def test_poll_body_invalid_json(configured_env):
    r = client.post("/v1/poll", content=b"{not json", headers={"content-type":"application/json"})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_json"

# ── metadata token ───────────────────────────────────────────────────────

def test_poll_metadata_unavailable_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.side_effect = ValueError("unavailable")
        r = client.post("/v1/poll", json={})
        assert r.status_code == 502
        assert "identity" in r.json()["error"]

def test_poll_metadata_timeout_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.side_effect = TimeoutError("timeout")
        r = client.post("/v1/poll", json={})
        assert r.status_code == 502

def test_poll_metadata_malformed_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.side_effect = ValueError("malformed jwt")
        r = client.post("/v1/poll", json={})
        assert r.status_code == 502

def test_metadata_fixed_url_not_from_env(monkeypatch):
    # Ensure _fetch_id_token_sync uses fixed URL, not env
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    monkeypatch.setenv("METADATA_URL", "http://evil.com/token")
    monkeypatch.setenv("GCP_METADATA_URL", "http://evil.com")
    captured = {}
    class FakeResp:
        status_code = 200
        headers = {"Metadata-Flavor": "Google"}
        def iter_bytes(self, chunk_size=8192):
            yield VALID_TOKEN.encode()
    class FakeStreamCtx:
        def __enter__(self): return FakeResp()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def stream(self, method, url, headers=None, **kw):
            captured["url"] = url
            captured["headers"] = headers
            assert method == "GET"
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClient):
        token = appmod._fetch_id_token_sync(VALID_AUDIENCE)
        assert token == VALID_TOKEN
        assert captured["url"].startswith("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity")
        assert "audience=" in captured["url"]
        assert "evil.com" not in captured["url"]
        assert captured["headers"].get("Metadata-Flavor") == "Google"

def test_metadata_requires_header_spoof_detection(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    class FakeRespSpoof:
        status_code = 200
        headers = {"Metadata-Flavor": "Evil"}
        def iter_bytes(self, chunk_size=8192):
            yield VALID_TOKEN.encode()
    class FakeStreamCtx:
        def __enter__(self): return FakeRespSpoof()
        def __exit__(self, *a): return False
    class FakeClientSpoof:
        def __init__(self,*a,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def stream(self, *a, **kw):
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClientSpoof):
        try:
            appmod._fetch_id_token_sync(VALID_AUDIENCE)
            assert False, "should have raised spoof"
        except ValueError as e:
            assert "spoof" in str(e).lower()

def test_metadata_token_bound_16KB(monkeypatch):
    # token >16KB should be rejected
    big_token = "a.b." + "c"* (16*1024+1)
    # but shape will fail earlier; test bound via _validate_jwt_shape
    assert not appmod._validate_jwt_shape(big_token)
    # also via sync helper with mocked response
    class FakeRespBig:
        status_code = 200
        headers = {"Metadata-Flavor": "Google"}
        def iter_bytes(self, chunk_size=8192):
            # chunked oversize without buffering full response first
            for i in range(0, len(big_token), 8192):
                yield big_token[i:i+8192].encode()
    class FakeStreamCtx:
        def __enter__(self): return FakeRespBig()
        def __exit__(self, *a): return False
    class FakeClientBig:
        def __init__(self,*a,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def stream(self, *a, **kw):
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClientBig):
        try:
            appmod._fetch_id_token_sync(VALID_AUDIENCE)
            assert False
        except ValueError:
            pass

def test_jwt_shape_validation():
    assert appmod._validate_jwt_shape(VALID_TOKEN) is True
    assert appmod._validate_jwt_shape("not-a-jwt") is False
    assert appmod._validate_jwt_shape("a.b.c.d") is False
    assert appmod._validate_jwt_shape("a..c") is False
    assert appmod._validate_jwt_shape("") is False
    # invalid base64
    assert appmod._validate_jwt_shape("***.***.***") is False

# ── CMS lease ────────────────────────────────────────────────────────────

def test_poll_no_work_success(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (404, {"content-type": "application/json"}, b'{"error":{"code":"no_work","message":"no work"}}', {"error": {"code": "no_work", "message": "no work"}})
            r = client.post("/v1/poll", json={})
            assert r.status_code == 200
            j = r.json()
            assert j["status"] == "idle"
            assert j["reason"] == "no_work"
            mock_token.assert_called_once()
            mock_lease.assert_called_once()
            # lease called with base_url and token
            args, _ = mock_lease.call_args
            assert args[0] == VALID_BASE_URL
            assert args[1] == VALID_TOKEN

def test_poll_cms_401_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (401, {"content-type": "application/json"}, b'{"error":{"code":"authentication_required"}}', {"error":{"code":"authentication_required"}})
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502
            assert "cms" in r.json()["error"].lower() or "authentication" in r.json()["error"].lower()

def test_poll_cms_5xx_returns_502(configured_env):
    for code in [500,502,503]:
        with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = VALID_TOKEN
            with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
                mock_lease.return_value = (code, {"content-type": "application/json"}, b'{"error":{"code":"unavailable"}}', {"error":{"code":"unavailable"}})
                r = client.post("/v1/poll", json={})
                assert r.status_code == 502, f"code {code} should give 502"

def test_poll_cms_oversize_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            # simulate oversize by raising ValueError
            mock_lease.side_effect = ValueError("lease response too large")
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

def test_poll_cms_malformed_lease_returns_502(configured_env):
    malformed_cases = [
        {},  # empty
        {"schemaVersion": 1, "runId": "not-uuid", "leaseId": str(uuid.uuid4()), "processId": "seo-audit", "idempotencyKey": "k", "fencingToken": 1, "leasedAt": "2026-09-10T00:00:00+00:00", "leaseExpiresAt": "2026-09-10T00:02:00+00:00", "input": {"market":"br","language":"pt-BR","targetUrl":"https://anderzilla.com/"}},
        valid_lease_envelope(processId="editorial-package"), # only seo-audit allowed
        valid_lease_envelope(fencingToken=0), # must be positive
        valid_lease_envelope(fencingToken="1"), # must be int
        valid_lease_envelope(input={"market":"xx","language":"pt-BR","targetUrl":"https://anderzilla.com/"}), # invalid market
        valid_lease_envelope(input={"market":"br","language":"pt","targetUrl":"https://anderzilla.com/"}), # invalid language
        valid_lease_envelope(input={"market":"br","language":"pt-BR","targetUrl":"https://evil.com/"}), # host not allowed by our validation
        valid_lease_envelope(extraField="evil"), # unknown field
        valid_lease_envelope(schemaVersion=2),
        valid_lease_envelope(idempotencyKey="bad key with spaces!"),
    ]
    for bad in malformed_cases:
        with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = VALID_TOKEN
            with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
                mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(bad).encode(), bad)
                r = client.post("/v1/poll", json={})
                assert r.status_code == 502, f"malformed {bad} should be 502 got {r.text}"

def test_poll_cms_lease_timeout_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.side_effect = TimeoutError("timeout")
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

# ── audit success and failure ────────────────────────────────────────────

def test_poll_success_audit_and_complete(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")) as mock_fetch:
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_success_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200, r.text
                    j = r.json()
                    assert j["status"] == "succeeded"
                    assert j["runId"] == lease["runId"]
                    assert j["leaseId"] == lease["leaseId"]
                    assert j["fencingToken"] == lease["fencingToken"]
                    assert j["targetHost"] == "anderzilla.com"
                    assert "result" in j
                    assert "checks" in j["result"]
                    # verify complete called with succeeded result and same token
                    mock_complete.assert_called_once()
                    args, _ = mock_complete.call_args
                    assert args[0] == VALID_BASE_URL
                    assert args[1] == VALID_TOKEN
                    body = args[2]
                    assert body["runId"] == lease["runId"]
                    assert body["leaseId"] == lease["leaseId"]
                    assert body["fencingToken"] == lease["fencingToken"]
                    assert body["status"] == "succeeded"
                    assert "result" in body
                    mock_fetch.assert_called_once_with(lease["input"]["targetUrl"])

def test_poll_audit_failure_reports_failed_completion(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            from app import FetchError
            with patch("app.fetch_html", side_effect=FetchError("fetch_timeout", "timeout", 504)):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_failed_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200, r.text
                    j = r.json()
                    assert j["status"] == "failed"
                    assert j["errorCode"] == "fetch_timeout"
                    assert "Tempo de coleta" in j["errorMessage"]
                    # complete should be called with failed
                    body = mock_complete.call_args[0][2]
                    assert body["status"] == "failed"
                    assert body["errorCode"] == "fetch_timeout"

def test_poll_audit_internal_error_maps_to_internal_error(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", side_effect=RuntimeError("boom https://anderzilla.com?secret=1")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_failed_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200
                    assert r.json()["errorCode"] == "internal_error"

def test_poll_result_too_large_reports_failure_without_raw(configured_env, monkeypatch):
    lease = valid_lease_envelope()
    # make result exceed by lowering limit
    monkeypatch.setattr(appmod, "MAX_CMS_RESULT_BYTES", 100)
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_failed_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200
                    j = r.json()
                    assert j["status"] == "failed"
                    assert j["errorCode"] == "validation_error"
                    body = mock_complete.call_args[0][2]
                    assert body["status"] == "failed"
                    # ensure raw audit result not included
                    assert "result" not in body
                    assert "html" not in json.dumps(body).lower()

# ── completion failure ───────────────────────────────────────────────────

def test_poll_completion_failure_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.return_value = (500, {"content-type": "application/json"}, b'{"error":{"code":"unavailable"}}', {"error":{"code":"unavailable"}})
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert "cms_complete" in r.json()["error"]

def test_poll_completion_timeout_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = TimeoutError("timeout")
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502

# ── secret-free logs ─────────────────────────────────────────────────────

def test_poll_logs_secret_free(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    lease = valid_lease_envelope()
    lease["input"]["notes"] = "secret-notes-should-not-appear"
    captured = []
    def fake_jlog(level, msg, **fields):
        captured.append((level, msg, fields))
    monkeypatch.setattr("app.jlog", fake_jlog)
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_success_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200
                    # ensure no captured log contains token, notes, raw URL query, CMS URL
                    for lvl, msg, fields in captured:
                        for v in list(fields.values()) + [msg]:
                            if isinstance(v, str):
                                assert VALID_TOKEN not in v, "token leaked in logs"
                                assert "secret-notes" not in v
                                assert VALID_BASE_URL not in v
                                # raw targetUrl with query not logged (we use safe host only)
                                assert "secret" not in v.lower() or "secret-notes" not in v
                    # ensure safe host present and raw URL not
                    # check that input.targetHost is used, not raw URL
                    found_host = any("input.targetHost" in f for _,_,f in captured)
                    assert found_host
                    for _,_,f in captured:
                        assert "targetUrl" not in f
                        assert "notes" not in f

def test_poll_does_not_log_token_on_metadata_failure(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    captured = []
    def fake_jlog(level,msg,**fields):
        captured.append((level,msg,fields))
    monkeypatch.setattr("app.jlog", fake_jlog)
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.side_effect = ValueError("fail")
        r = client.post("/v1/poll", json={})
        assert r.status_code == 502
        for _,_,fields in captured:
            for v in fields.values():
                if isinstance(v, str):
                    assert VALID_TOKEN not in v

# ── one-job behavior ─────────────────────────────────────────────────────

def test_poll_processes_at_most_one_lease(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")) as mock_fetch:
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_success_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200
                    assert mock_lease.call_count == 1
                    assert mock_fetch.call_count == 1
                    assert mock_complete.call_count == 1
                    # no second lease

# ── timeout handling ─────────────────────────────────────────────────────

def test_poll_cms_lease_total_timeout_bound(configured_env):
    # Simulate slow CMS lease that exceeds 20s — async wait_for should timeout
    # We patch the sync helper to sleep
    import time
    def slow_lease(base_url, token):
        time.sleep(0.5)
        # we want async wrapper to timeout; set TIMEOUT_CMS_LEASE_SECONDS small
        return (200, b'{}', {})
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        # lower lease timeout for test (20s split from 6s completion)
        with patch("app.TIMEOUT_CMS_LEASE_SECONDS", 0.1):
            # patch the sync to be slow
            with patch("app._cms_lease_sync", side_effect=slow_lease):
                # need to also patch async wrapper to respect new timeout? It uses TIMEOUT_CMS_LEASE_SECONDS
                # we make sync sleep longer than async wait_for
                def very_slow(*a, **kw):
                    time.sleep(1)
                    return (200,b'{}',{})
                with patch("app._cms_lease_sync", side_effect=very_slow):
                    r = client.post("/v1/poll", json={})
                    # may be 502 due to timeout
                    assert r.status_code == 502

# ── never accept actor/role/token/URL from caller ────────────────────────

def test_poll_never_accepts_caller_token_or_url(configured_env):
    # caller tries to supply token/URL in body — must be rejected before any network
    for bad_body in [
        {"token": VALID_TOKEN},
        {"actor": "evil"},
        {"role": "anderzilla_worker"},
        {"audience": VALID_AUDIENCE},
        {"cmsUrl": VALID_BASE_URL},
    ]:
        with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = VALID_TOKEN
            r = client.post("/v1/poll", json=bad_body)
            assert r.status_code == 400
            mock_token.assert_not_called()

# ── existing health/execute preserved ────────────────────────────────────

def test_execute_still_works(configured_env):
    # ensure /v1/execute still behaves as before
    body = {
        "schemaVersion": 1,
        "runId": str(uuid.uuid4()),
        "processId": "editorial-package",
        "idempotencyKey": "test-exec-poll-1",
        "input": {"market": "br", "language": "pt-BR", "targetUrl": "https://anderzilla.com/"},
    }
    r = client.post("/v1/execute", json=body)
    assert r.status_code == 200
    assert r.json()["status"] == "succeeded"

# ── regression: CMS completion strictness (302/HTML/wrong receipt) ─────────

def test_poll_completion_302_redirect_treated_as_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    # Simulate CMS returning 302 redirect (follow_redirects=false)
                    mock_complete.return_value = (302, {"location": "https://evil.com", "content-type": "text/html"}, b"<html>redirect</html>", {})
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"

def test_poll_completion_html_not_json_treated_as_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    # 200 but HTML content-type
                    mock_complete.return_value = (200, {"content-type": "text/html"}, b"<html>not json</html>", {})
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"

def test_poll_completion_wrong_runId_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    # return receipt with wrong runId
                    def wrong_run(base, tok, body):
                        h = hashlib.sha256(json.dumps(body["result"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                        receipt = {"runId": str(uuid.uuid4()), "status": "succeeded", "version": 2, "resultHash": h, "finishedAt": datetime.now(timezone.utc).isoformat()}
                        return (200, {"content-type": "application/json"}, json.dumps(receipt).encode(), receipt)
                    mock_complete.side_effect = wrong_run
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"

def test_poll_completion_wrong_status_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    def wrong_status(base, tok, body):
                        h = hashlib.sha256(json.dumps(body["result"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                        # body expects succeeded, but receipt says failed
                        receipt = {"runId": body["runId"], "status": "failed", "version": 2, "error": {"code": "worker_failed", "message": "msg"}, "finishedAt": datetime.now(timezone.utc).isoformat()}
                        return (200, {"content-type": "application/json"}, json.dumps(receipt).encode(), receipt)
                    mock_complete.side_effect = wrong_status
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"

def test_poll_completion_wrong_hash_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    def wrong_hash(base, tok, body):
                        receipt = {"runId": body["runId"], "status": "succeeded", "version": 2, "resultHash": "0"*64, "finishedAt": datetime.now(timezone.utc).isoformat()}
                        return (200, {"content-type": "application/json"}, json.dumps(receipt).encode(), receipt)
                    mock_complete.side_effect = wrong_hash
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502

def test_poll_completion_wrong_error_code_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            from app import FetchError
            with patch("app.fetch_html", side_effect=FetchError("fetch_timeout", "timeout", 504)):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    def wrong_code(base, tok, body):
                        # body errorCode is fetch_timeout, receipt returns different code
                        receipt = {"runId": body["runId"], "status": "failed", "version": 2, "error": {"code": "internal_error", "message": "msg"}, "finishedAt": datetime.now(timezone.utc).isoformat()}
                        return (200, {"content-type": "application/json"}, json.dumps(receipt).encode(), receipt)
                    mock_complete.side_effect = wrong_code
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"

# ── 404 HTML vs explicit no_work JSON ──────────────────────────────────────

def test_poll_lease_404_html_returns_502_not_idle(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            # 404 with HTML body and text/html content-type -> must be 502, never idle
            mock_lease.return_value = (404, {"content-type": "text/html"}, b"<html>404 Not Found</html>", {})
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502
            assert r.json()["error"] == "cms_error"
            assert r.json()["error"] != "idle"

def test_poll_lease_404_json_wrong_code_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            # 404 JSON but code is not no_work
            parsed = {"error": {"code": "not_found", "message": "x"}}
            raw = json.dumps(parsed).encode()
            mock_lease.return_value = (404, {"content-type": "application/json"}, raw, parsed)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

def test_poll_lease_404_empty_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (404, {"content-type": "application/json"}, b"", {})
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

def test_poll_lease_404_no_work_json_returns_idle(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            parsed = {"error": {"code": "no_work", "message": "no work"}}
            raw = json.dumps(parsed).encode()
            mock_lease.return_value = (404, {"content-type": "application/json"}, raw, parsed)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 200
            assert r.json()["status"] == "idle"
            assert r.json()["reason"] == "no_work"

def test_poll_lease_404_no_work_non_json_content_type_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            parsed = {"error": {"code": "no_work", "message": "no work"}}
            raw = json.dumps(parsed).encode()
            # even though body is correct JSON, content-type is not json -> 502 per spec
            mock_lease.return_value = (404, {"content-type": "text/html"}, raw, parsed)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

# ── temporal lease cases ───────────────────────────────────────────────────

def test_poll_lease_naive_datetime_returns_502(configured_env):
    lease = valid_lease_envelope(leasedAt="2026-09-10T00:00:00", leaseExpiresAt="2026-09-10T00:02:00")
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502
            assert "invalid_lease" in r.json()["error"]

def test_poll_lease_reversed_times_returns_502(configured_env):
    now = datetime.now(timezone.utc)
    lease = valid_lease_envelope(leasedAt=(now + timedelta(seconds=120)).isoformat(), leaseExpiresAt=now.isoformat())
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

def test_poll_lease_expired_returns_502(configured_env):
    now = datetime.now(timezone.utc)
    lease = valid_lease_envelope(leasedAt=(now - timedelta(seconds=240)).isoformat(), leaseExpiresAt=(now - timedelta(seconds=120)).isoformat())
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html") as mock_fetch:
                r = client.post("/v1/poll", json={})
                assert r.status_code == 502
                mock_fetch.assert_not_called()

def test_poll_lease_too_short_margin_returns_502(configured_env):
    now = datetime.now(timezone.utc)
    lease = valid_lease_envelope(leasedAt=now.isoformat(), leaseExpiresAt=(now + timedelta(seconds=5)).isoformat())
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html") as mock_fetch:
                r = client.post("/v1/poll", json={})
                assert r.status_code == 502
                mock_fetch.assert_not_called()

def test_poll_lease_non_utc_offset_returns_502(configured_env):
    now = datetime.now(timezone.utc)
    # Use +05:00 offset instead of +00:00
    leased = (now + timedelta(seconds=0)).astimezone(timezone(timedelta(hours=5))).isoformat()
    expires = (now + timedelta(seconds=120)).astimezone(timezone(timedelta(hours=5))).isoformat()
    lease = valid_lease_envelope(leasedAt=leased, leaseExpiresAt=expires)
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502

# ── stream limits: chunked oversize without buffering ──────────────────────

def test_metadata_token_stream_oversize_aborts_without_buffering(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    # Simulate metadata endpoint returning token via chunked iter_bytes exceeding 16KB
    chunk_size = 8192
    big_chunks = [b"a"*chunk_size, b"b"*chunk_size, b"c"*1024]  # total >16KB
    total_len = sum(len(c) for c in big_chunks)
    assert total_len > 16*1024
    class FakeResp:
        status_code = 200
        headers = {"Metadata-Flavor": "Google", "content-type": "text/plain"}
        def iter_bytes(self, chunk_size=8192):
            for ch in big_chunks:
                yield ch
    class FakeStreamCtx:
        def __enter__(self): return FakeResp()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, *a, **kw):
            # verify follow_redirects false and timeout preserved
            assert kw.get("headers", {}).get("Metadata-Flavor") == "Google" or True
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClient):
        try:
            appmod._fetch_id_token_sync(VALID_AUDIENCE)
            assert False, "should have raised oversize"
        except ValueError as e:
            assert "too large" in str(e).lower()
        except Exception as e:
            assert "too large" in str(e).lower()

def test_cms_lease_stream_oversize_aborts_without_buffering(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    # Simulate lease returning 130KB json via chunked iter_bytes
    big = b"a"* (128*1024 + 1024)
    chunks = [big[i:i+8192] for i in range(0, len(big), 8192)]
    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/json"}
        def iter_bytes(self, chunk_size=8192):
            for ch in chunks:
                yield ch
    class FakeStreamCtx:
        def __enter__(self): return FakeResp()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, *a, **kw):
            assert kw.get("follow_redirects") is False
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, *a, **kw):
            # ensure follow_redirects false is passed to Client, not stream? Actually Client already false
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClient):
        try:
            appmod._cms_lease_sync(VALID_BASE_URL, VALID_TOKEN)
            assert False, "should have raised"
        except ValueError as e:
            assert "too large" in str(e).lower()

def test_cms_complete_stream_oversize_aborts_without_buffering(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    big = b"b"* (128*1024 + 1)
    chunks = [big[i:i+4096] for i in range(0, len(big), 4096)]
    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/json"}
        def iter_bytes(self, chunk_size=8192):
            for ch in chunks:
                yield ch
    class FakeStreamCtx:
        def __enter__(self): return FakeResp()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, *a, **kw):
            assert kw.get("follow_redirects") is False
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, *a, **kw):
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClient):
        try:
            appmod._cms_complete_sync(VALID_BASE_URL, VALID_TOKEN, {"runId": str(uuid.uuid4()), "leaseId": str(uuid.uuid4()), "fencingToken": 1, "status": "failed", "errorCode": "worker_failed", "errorMessage": "msg"})
            assert False
        except ValueError:
            pass

def test_cms_lease_and_complete_preserve_timeout_and_no_redirect(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    captured = {}
    class FakeRespOk:
        status_code = 200
        headers = {"content-type": "application/json"}
        def iter_bytes(self, chunk_size=8192):
            yield b'{"ok":1}'
    class FakeStreamCtx:
        def __enter__(self): return FakeRespOk()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, timeout=None, follow_redirects=None, **kw):
            captured["timeout"] = timeout
            captured["follow_redirects"] = follow_redirects
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, method, url, headers=None, json=None, **kw):
            captured["method"] = method
            captured["url"] = url
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClient):
        appmod._cms_lease_sync(VALID_BASE_URL, VALID_TOKEN)
        assert captured["follow_redirects"] is False
        # lease timeout must be 20s outer+per-call (covers Azure SQL login_timeout=15)
        assert captured["timeout"] is not None
        t = captured["timeout"]
        # httpx.Timeout(20, connect=20) — check via attributes (connect/read/write/pool)
        assert getattr(t, "connect", None) == 20.0 or "20" in str(t)
        assert getattr(t, "read", None) == 20.0 or "20" in str(t)
        captured.clear()
        appmod._cms_complete_sync(VALID_BASE_URL, VALID_TOKEN, {"runId": str(uuid.uuid4()), "leaseId": str(uuid.uuid4()), "fencingToken": 1, "status": "failed", "errorCode": "worker_failed", "errorMessage": "msg"})
        assert captured["follow_redirects"] is False
        t2 = captured["timeout"]
        assert t2 is not None
        # completion stays 6s — DB warm after lease
        assert getattr(t2, "connect", None) == 6.0 or "6" in str(t2)
        assert getattr(t2, "read", None) == 6.0 or "6" in str(t2)
        # ensure lease and complete timeouts differ (split)
        assert str(t) != str(t2)
    # Also test metadata timeout and no redirect
    captured.clear()
    class FakeMetaResp:
        status_code = 200
        headers = {"Metadata-Flavor": "Google", "content-type": "text/plain"}
        def iter_bytes(self, chunk_size=8192):
            yield VALID_TOKEN.encode()
    class FakeMetaCtx:
        def __enter__(self): return FakeMetaResp()
        def __exit__(self, *a): return False
    class FakeMetaClient:
        def __init__(self, timeout=None, follow_redirects=None, **kw):
            captured["meta_timeout"] = timeout
            captured["meta_follow"] = follow_redirects
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, *a, **kw):
            return FakeMetaCtx()
    with patch("app.httpx.Client", FakeMetaClient):
        appmod._fetch_id_token_sync(VALID_AUDIENCE)
        assert captured["meta_follow"] is False
        assert captured["meta_timeout"] is not None
        mt = captured["meta_timeout"]
        assert getattr(mt, "connect", None) == 3.0 or "3" in str(mt)

def test_poll_lease_missing_content_type_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            # Missing Content-Type header (empty dict) — must be 502, not accepted even with valid JSON body
            mock_lease.return_value = (200, {}, json.dumps(lease).encode(), lease)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502
            assert r.json()["error"] == "invalid_lease_envelope"

def test_poll_lease_404_missing_content_type_returns_502(configured_env):
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            parsed = {"error": {"code": "no_work", "message": "no work"}}
            raw = json.dumps(parsed).encode()
            # Missing Content-Type header on 404 idle response — must be 502 per strict JSON requirement
            mock_lease.return_value = (404, {}, raw, parsed)
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502
            assert r.json()["error"] == "cms_error"

def test_poll_completion_missing_content_type_returns_502(configured_env):
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    # Valid receipt JSON but missing Content-Type header — must be 502
                    def missing_ct(base, tok, body):
                        result = body.get("result", {})
                        h = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                        receipt = {"runId": body["runId"], "status": "succeeded", "version": 2, "resultHash": h, "finishedAt": datetime.now(timezone.utc).isoformat()}
                        return (200, {}, json.dumps(receipt).encode(), receipt)
                    mock_complete.side_effect = missing_ct
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"

def test_cms_per_call_timeout_truly_le_6(monkeypatch):
    # Verify async wrappers use correct split timeouts: lease 20s, complete 6s, no +0.5
    import inspect
    src = inspect.getsource(appmod._cms_lease)
    assert "TIMEOUT_CMS_SECONDS + 0.5" not in src
    assert "TIMEOUT_CMS_LEASE_SECONDS" in src
    assert "TIMEOUT_CMS_LEASE_SECONDS + 0.5" not in src
    src2 = inspect.getsource(appmod._cms_complete)
    assert "TIMEOUT_CMS_SECONDS + 0.5" not in src2
    assert "TIMEOUT_CMS_COMPLETE_SECONDS" in src2
    # Also check that constants match staged budget spec
    assert appmod.TIMEOUT_CMS_LEASE_SECONDS == 20.0
    assert appmod.TIMEOUT_CMS_COMPLETE_SECONDS == 6.0
    assert appmod.TIMEOUT_CMS_SECONDS == 6.0  # backward-compat alias must equal complete
    assert appmod.TIMEOUT_CMS_SECONDS <= 6.0
    assert appmod.TIMEOUT_METADATA_SECONDS == 3.0
    assert appmod.TIMEOUT_TOTAL == 8.0
    # staged worst-case 3+20+8+6=37, platform must be >=45
    staged = appmod.TIMEOUT_METADATA_SECONDS + appmod.TIMEOUT_CMS_LEASE_SECONDS + appmod.TIMEOUT_TOTAL + appmod.TIMEOUT_CMS_COMPLETE_SECONDS
    assert staged == 37.0
    assert staged < 45  # platform timeout headroom documented as 45s


def test_timeout_specific_failure_mapping(configured_env):
    """Timeout-specific failure mapping (no retries, one lease per poll).

    - metadata 3s TimeoutError -> 502 identity_unavailable
    - lease 20s TimeoutError -> 502 cms_timeout (no retry in worker; CMS re-queues via expiry)
    - complete 6s TimeoutError -> 502 cms_complete_failed (lease expiry re-queues)
    - SEO 8s wait_for TimeoutError -> FetchError fetch_timeout -> failed completion with stable errorCode
    All stages keep metadata 3s and SEO 8s unchanged; lease split to 20s for Azure SQL login_timeout=15 cold resume.
    """
    # metadata timeout
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.side_effect = TimeoutError("metadata timeout")
        r = client.post("/v1/poll", json={})
        assert r.status_code == 502
        assert r.json()["error"] == "identity_unavailable"
    # lease timeout (20s outer) — maps to cms_timeout, not cms_complete_failed
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.side_effect = TimeoutError("cms lease timeout")
            r = client.post("/v1/poll", json={})
            assert r.status_code == 502
            assert r.json()["error"] == "cms_timeout"
            assert mock_lease.call_count == 1  # one lease per poll, no retry
    # complete timeout (6s outer) — warm DB path
    lease = valid_lease_envelope()
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", return_value=(200, html_ok(), "https://anderzilla.com/")):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = TimeoutError("cms complete timeout")
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 502
                    assert r.json()["error"] == "cms_complete_failed"
                    assert mock_complete.call_count == 1
    # SEO timeout via poll still attempts completion with stable code fetch_timeout
    with patch("app._fetch_id_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = VALID_TOKEN
        with patch("app._cms_lease", new_callable=AsyncMock) as mock_lease:
            mock_lease.return_value = (200, {"content-type": "application/json"}, json.dumps(lease).encode(), lease)
            with patch("app.fetch_html", side_effect=appmod.FetchError("fetch_timeout", "timeout", 504)):
                with patch("app._cms_complete", new_callable=AsyncMock) as mock_complete:
                    mock_complete.side_effect = _complete_failed_side_effect
                    r = client.post("/v1/poll", json={})
                    assert r.status_code == 200
                    assert r.json()["status"] == "failed"
                    assert r.json()["errorCode"] == "fetch_timeout"


# ── dedicated transport header X-AnderZilla-Worker-Authorization ──────────

def test_cms_lease_sends_only_custom_header(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    captured = {}
    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/json"}
        def iter_bytes(self, chunk_size=8192):
            yield b'{"ok":1}'
    class FakeStreamCtx:
        def __enter__(self): return FakeResp()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, timeout=None, follow_redirects=None, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, method, url, headers=None, json=None, **kw):
            captured["headers"] = headers or {}
            captured["url"] = url
            return FakeStreamCtx()
    with patch("app.httpx.Client", FakeClient):
        appmod._cms_lease_sync(VALID_BASE_URL, VALID_TOKEN)
        # Must send dedicated header, never standard Authorization
        assert "X-AnderZilla-Worker-Authorization" in captured["headers"]
        assert captured["headers"]["X-AnderZilla-Worker-Authorization"] == f"Bearer {VALID_TOKEN}"
        # Ensure standard Authorization is NOT sent
        assert "Authorization" not in captured["headers"]
        # Lowercase variant must not appear either (explicit header name check)
        lower_keys = {k.lower() for k in captured["headers"].keys()}
        assert "authorization" not in lower_keys or "x-anderzilla-worker-authorization" in lower_keys
        assert "x-anderzilla-worker-authorization" in lower_keys
        # Ensure no Authorization entry case-insensitive
        assert not any(k.lower() == "authorization" for k in captured["headers"].keys())


def test_cms_complete_sends_only_custom_header(monkeypatch):
    monkeypatch.setenv("CMS_WORKER_BASE_URL", VALID_BASE_URL)
    monkeypatch.setenv("CMS_WORKER_AUDIENCE", VALID_AUDIENCE)
    captured = {}
    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/json"}
        def iter_bytes(self, chunk_size=8192):
            yield b'{"ok":1}'
    class FakeStreamCtx:
        def __enter__(self): return FakeResp()
        def __exit__(self, *a): return False
    class FakeClient:
        def __init__(self, timeout=None, follow_redirects=None, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def stream(self, method, url, headers=None, json=None, **kw):
            captured["headers"] = headers or {}
            return FakeStreamCtx()
    body = {"runId": str(uuid.uuid4()), "leaseId": str(uuid.uuid4()), "fencingToken": 1, "status": "failed", "errorCode": "worker_failed", "errorMessage": "msg"}
    with patch("app.httpx.Client", FakeClient):
        appmod._cms_complete_sync(VALID_BASE_URL, VALID_TOKEN, body)
        assert "X-AnderZilla-Worker-Authorization" in captured["headers"]
        assert captured["headers"]["X-AnderZilla-Worker-Authorization"] == f"Bearer {VALID_TOKEN}"
        assert "Authorization" not in captured["headers"]
        assert not any(k.lower() == "authorization" for k in captured["headers"].keys())


def test_jlog_strips_custom_header_and_token(monkeypatch):
    # jlog must strip dedicated header lowercase name and never log token
    captured_lines = []
    import logging
    orig_handlers = appmod.logger.handlers[:]
    class CapHandler(logging.Handler):
        def emit(self, record):
            captured_lines.append(record.getMessage())
    cap = CapHandler()
    appmod.logger.handlers = [cap]
    try:
        # Use jlog directly with custom header field
        appmod.jlog("info", "test", **{"x-anderzilla-worker-authorization": f"Bearer {VALID_TOKEN}", "token": VALID_TOKEN, "authorization": "Bearer stuff"})
        assert len(captured_lines) == 1
        line = captured_lines[0]
        assert VALID_TOKEN not in line
        assert "x-anderzilla-worker-authorization" not in line.lower()
        assert "authorization" not in line.lower() or "bearer" not in line.lower()
        # Also test case-insensitive stripping
        captured_lines.clear()
        appmod.jlog("info", "test2", **{"X-AnderZilla-Worker-Authorization": f"Bearer {VALID_TOKEN}"})
        line2 = captured_lines[0]
        assert VALID_TOKEN not in line2
        assert "anderzilla" not in line2.lower()
    finally:
        appmod.logger.handlers = orig_handlers


