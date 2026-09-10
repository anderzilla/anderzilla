import json
import uuid
import asyncio
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app import app, _replay, ALLOWED_HOSTS, MAX_BYTES

client = TestClient(app)

VALID_RUN_ID = str(uuid.uuid4())
VALID_INPUT = {"market": "br", "language": "pt-BR", "targetUrl": "https://anderzilla.com/"}


def base_body(**overrides):
    body = {
        "schemaVersion": 1,
        "runId": VALID_RUN_ID,
        "processId": "editorial-package",
        "idempotencyKey": "test-key-1",
        "input": dict(VALID_INPUT),
    }
    # deep merge overrides
    for k, v in overrides.items():
        if k == "input" and isinstance(v, dict):
            body["input"].update(v)
        else:
            body[k] = v
    return body


def fresh_client():
    # clear replay between tests
    _replay.clear()
    return client


# ─── health ────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert j["service"] == "automation-worker"


# ─── auth boundary ─────────────────────────────────────────────────────

@pytest.mark.parametrize("field", ["actor", "role", "roles", "principal", "user", "actorId", "serviceAccount"])
def test_rejects_actor_fields_top_level(field):
    b = base_body()
    b[field] = "evil"
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "actor_fields_not_allowed"


@pytest.mark.parametrize("field", ["actor", "role", "principal"])
def test_rejects_actor_fields_in_input(field):
    b = base_body()
    b["input"][field] = "evil"
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "actor_fields_not_allowed"


# ─── input validation ──────────────────────────────────────────────────

def test_schema_version_must_be_1():
    b = base_body(schemaVersion=2)
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "schemaVersion" in r.json()["error"]


def test_run_id_must_be_uuid():
    b = base_body(runId="not-a-uuid")
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "runId" in r.json()["error"]


def test_process_id_allowlist():
    b = base_body(processId="unknown-process")
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400


def test_market_allowlist():
    b = base_body(input={"market": "xx"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400


def test_language_allowlist():
    # Only pt-BR and en accepted — aligned with CMS automation.py
    for bad in ["fr", "pt", "en-US", "PT-BR", ""]:
        b = base_body(input={"language": bad})
        r = fresh_client().post("/v1/execute", json=b)
        assert r.status_code == 400, f"{bad} should be rejected"
        assert "language" in r.json()["error"]


def test_language_accepts_ptBR_and_en():
    for good in ["pt-BR", "en"]:
        b = base_body(input={"language": good})
        r = fresh_client().post("/v1/execute", json=b)
        # editorial-package succeeds with valid language
        assert r.status_code == 200, f"{good} should be accepted: {r.text}"
        assert r.json()["result"]["editorialPackage"]["language"] == good


def test_target_url_scheme_must_be_https():
    b = base_body(input={"targetUrl": "http://anderzilla.com/"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "https" in r.json()["error"]


def test_target_url_host_allowlist():
    b = base_body(input={"targetUrl": "https://evil.com/"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "host_not_allowed" in r.json()["error"]


def test_target_url_userinfo_blocked():
    b = base_body(input={"targetUrl": "https://user:pass@anderzilla.com/"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "userinfo" in r.json()["error"]


def test_target_url_port_blocked():
    b = base_body(input={"targetUrl": "https://anderzilla.com:8443/"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "port" in r.json()["error"]


def test_target_url_private_ip_literal_blocked():
    b = base_body(input={"targetUrl": "https://192.168.1.1/"})
    # host not in allowlist already, but test literal detection directly via helper
    # so we test via allowed host that resolves to private? Instead test helper directly elsewhere.
    # For this route, host_not_allowed fires first; still 400
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400


def test_notes_bounded():
    b = base_body()
    b["input"]["notes"] = "x" * 2001
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "notes_too_long" in r.json()["error"]


def test_notes_not_logged_in_error_message():
    b = base_body()
    b["input"]["notes"] = "secret-note-should-not-appear"
    # trigger another validation error so notes would be candidate for leak
    b["input"]["targetUrl"] = "https://evil.com/"
    r = fresh_client().post("/v1/execute", json=b)
    body = r.text
    assert "secret-note" not in body


def test_idempotency_key_invalid():
    b = base_body(idempotencyKey="bad key with spaces!")
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400


def test_payload_too_large():
    big = "x" * (33 * 1024)
    r = fresh_client().post("/v1/execute", content=big, headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_invalid_json():
    r = fresh_client().post("/v1/execute", content=b"{not json", headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_json"


# ─── editorial-package (no network) ────────────────────────────────────

def test_editorial_package_returns_template():
    b = base_body(processId="editorial-package", idempotencyKey="ed-1")
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "succeeded"
    assert j["processId"] == "editorial-package"
    assert "editorialPackage" in j["result"]
    pkg = j["result"]["editorialPackage"]
    assert pkg["market"] == "br"
    assert pkg["language"] == "pt-BR"
    assert "sections" in pkg
    assert any(s["id"] == "metadata" for s in pkg["sections"])
    # editorial wording uses pt-BR/en
    body_str = json.dumps(pkg, ensure_ascii=False).lower()
    assert "pt-br" in body_str or "pt-br/en" in body_str or "pt-br" in body_str
    # no LLM, deterministic
    assert "Template only" in pkg["disclaimer"] or "template" in j["result"]["disclaimer"].lower()
    # idempotency note present
    assert "caller owns durable idempotency" in j["idempotency"]["note"].lower()
    assert j["replayed"] is False


def test_editorial_package_no_generated_claims():
    b = base_body(processId="editorial-package", idempotencyKey="ed-2")
    r = fresh_client().post("/v1/execute", json=b)
    body = json.dumps(r.json())
    # Ensure no ranking promise inside template
    assert "ranking" not in body.lower() or "no ranking promise" in body.lower()


# ─── SSRF / redirect / size guards (mocked fetch) ───────────────────────

def _html_ok():
    return """<!doctype html><html lang=\"pt-BR\"><head><title>AnderZilla — Tecnologia</title>
<meta name=\"description\" content=\"Cobertura de tecnologia, IA e games com curadoria humana.\">
<link rel=\"canonical\" href=\"https://anderzilla.com/pt/test\">
<link rel=\"alternate\" hreflang=\"pt-BR\" href=\"https://anderzilla.com/pt/test\">
<link rel=\"alternate\" hreflang=\"en\" href=\"https://anderzilla.com/en/test\">
<meta name=\"robots\" content=\"index, follow\">
<script type=\"application/ld+json\">{\"@type\":\"Article\"}</script>
</head><body><h1>Test</h1><h2>Sub</h2><img src=\"/img.jpg\" alt=\"descricao\"><a href=\"/pt/outro\">interno</a><a href=\"https://example.com\">externo</a></body></html>"""


def test_seo_audit_success_mocked():
    b = base_body(processId="seo-audit", idempotencyKey="seo-1")
    with patch("app.fetch_html", return_value=(200, _html_ok(), "https://anderzilla.com/")):
        r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["status"] == "succeeded"
    checks = j["result"]["checks"]
    ids = {c["id"] for c in checks}
    for expected in ["http_status", "title", "description", "canonical", "html_lang", "robots_meta", "hreflang", "json_ld", "headings", "image_alt", "internal_links"]:
        assert expected in ids, f"missing check {expected}"
    # deterministic: same html => same statuses
    title_check = next(c for c in checks if c["id"] == "title")
    assert title_check["status"] == "pass"
    # html lang should pass for pt-BR
    html_lang_check = next(c for c in checks if c["id"] == "html_lang")
    assert html_lang_check["status"] == "pass"
    # no ranking promise
    for c in checks:
        assert "rank #1" not in c["detail"].lower()


def test_seo_audit_html_lang_warns_when_mismatch():
    # When language=pt-BR but html lang is en, warn
    html = """<!doctype html><html lang=\"en\"><head><title>ok title here ok title</title></head><body><h1>Test</h1></body></html>"""
    b = base_body(processId="seo-audit", idempotencyKey="seo-lang-mismatch")
    with patch("app.fetch_html", return_value=(200, html, "https://anderzilla.com/")):
        r = fresh_client().post("/v1/execute", json=b)
    checks = r.json()["result"]["checks"]
    lang_check = next(c for c in checks if c["id"] == "html_lang")
    assert lang_check["status"] == "warn"
    assert "pt-br" in lang_check["detail"].lower()


def test_seo_audit_detects_missing_title():
    html = "<html><head></head><body><h1>hi</h1></body></html>"
    b = base_body(processId="seo-audit", idempotencyKey="seo-missing-title")
    with patch("app.fetch_html", return_value=(200, html, "https://anderzilla.com/")):
        r = fresh_client().post("/v1/execute", json=b)
    checks = r.json()["result"]["checks"]
    title = next(c for c in checks if c["id"] == "title")
    assert title["status"] == "fail"


def test_seo_audit_detects_multiple_h1():
    html = "<html lang=\"pt-BR\"><head><title>ok title here ok</title></head><body><h1>a</h1><h1>b</h1></body></html>"
    b = base_body(processId="seo-audit", idempotencyKey="seo-h1")
    with patch("app.fetch_html", return_value=(200, html, "https://anderzilla.com/")):
        r = fresh_client().post("/v1/execute", json=b)
    h = next(c for c in r.json()["result"]["checks"] if c["id"] == "headings")
    assert h["status"] == "warn"


def test_fetch_redirect_to_other_host_blocked():
    # Simulate fetch raising redirect_host_not_allowed
    from app import FetchError

    def raise_redirect(*a, **kw):
        raise FetchError("redirect_host_not_allowed", "Redirect to host not allowed: evil.com", 400)

    b = base_body(processId="seo-audit", idempotencyKey="seo-redirect")
    with patch("app.fetch_html", side_effect=raise_redirect):
        r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "redirect_host_not_allowed"


def test_fetch_too_large_blocked():
    from app import FetchError

    def raise_large(*a, **kw):
        raise FetchError("response_too_large", "Response exceeds 2000000 bytes", 400)

    b = base_body(processId="seo-audit", idempotencyKey="seo-large")
    with patch("app.fetch_html", side_effect=raise_large):
        r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "response_too_large"


def test_fetch_timeout_maps_to_504():
    from app import FetchError

    def raise_timeout(*a, **kw):
        raise FetchError("fetch_timeout", "Fetch timed out after 8.0s", 504)

    b = base_body(processId="seo-audit", idempotencyKey="seo-timeout")
    with patch("app.fetch_html", side_effect=raise_timeout):
        r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 504


def test_private_ip_helper_blocks_literal():
    from app import _is_private_ip_literal

    assert _is_private_ip_literal("127.0.0.1") is True
    assert _is_private_ip_literal("10.0.0.5") is True
    assert _is_private_ip_literal("192.168.1.1") is True
    assert _is_private_ip_literal("8.8.8.8") is False
    assert _is_private_ip_literal("anderzilla.com") is False


def test_validate_target_url_allows_documented_hosts():
    from app import _validate_target_url

    for host in ALLOWED_HOSTS:
        url = f"https://{host}/some/path"
        _, err = _validate_target_url(url)
        assert err == "", f"allowed host {host} should pass but got {err}"


def test_validate_target_url_rejects_plain_pt_not_needed_but_language_level():
    # targetUrl validation is host-level; language rejection is separate
    from app import _validate_target_url
    # plain pt is not a URL concept — ensure language validation rejects pt
    b = base_body(input={"language": "pt"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400


def test_azure_hosts_are_subset():
    # Ensure the two documented Azure hosts from AZURE-RELEASE are in allowlist
    assert "salmon-stone-0a4d29c0f.5.azurestaticapps.net" in ALLOWED_HOSTS
    assert "mango-coast-0322c590f.5.azurestaticapps.net" in ALLOWED_HOSTS


# ─── idempotency ─────────────────────────────────────────────────────────

def test_idempotency_replay_same_input():
    b = base_body(processId="editorial-package", idempotencyKey="idem-1", input={"targetUrl": "https://anderzilla.com/pt/test"})
    c = fresh_client()
    r1 = c.post("/v1/execute", json=b)
    assert r1.status_code == 200
    assert r1.json()["replayed"] is False
    r2 = c.post("/v1/execute", json=b)
    assert r2.status_code == 200
    assert r2.json()["replayed"] is True
    # same runId echoed? replay returns same body but replayed flag true
    # idempotency note must mention caller ownership
    assert "caller owns durable" in r2.json()["idempotency"]["note"].lower()


def test_idempotency_conflict_different_input():
    c = fresh_client()
    b1 = base_body(processId="editorial-package", idempotencyKey="idem-conflict", input={"targetUrl": "https://anderzilla.com/pt/a"})
    b2 = base_body(processId="editorial-package", idempotencyKey="idem-conflict", input={"targetUrl": "https://anderzilla.com/pt/b"})
    r1 = c.post("/v1/execute", json=b1)
    assert r1.status_code == 200
    r2 = c.post("/v1/execute", json=b2)
    assert r2.status_code == 409
    assert r2.json()["error"] == "idempotency_conflict"


def test_idempotency_conflict_different_process():
    c = fresh_client()
    b1 = base_body(processId="editorial-package", idempotencyKey="idem-proc", input={"targetUrl": "https://anderzilla.com/"})
    b2 = base_body(processId="seo-audit", idempotencyKey="idem-proc", input={"targetUrl": "https://anderzilla.com/"})
    # first editorial-package
    r1 = c.post("/v1/execute", json=b1)
    assert r1.status_code == 200
    # second with same key but different process should NOT conflict — key is scoped by (processId, idempotencyKey)
    with patch("app.fetch_html", return_value=(200, _html_ok(), "https://anderzilla.com/")):
        r2 = c.post("/v1/execute", json=b2)
    # Different processId with same key is allowed (isolated)
    assert r2.status_code == 200
    assert r2.json()["replayed"] is False


def test_seo_audit_idempotent():
    b = base_body(processId="seo-audit", idempotencyKey="seo-idem-1")
    c = fresh_client()
    with patch("app.fetch_html", return_value=(200, _html_ok(), "https://anderzilla.com/")):
        r1 = c.post("/v1/execute", json=b)
        assert r1.status_code == 200
        r2 = c.post("/v1/execute", json=b)
        assert r2.status_code == 200
        assert r2.json()["replayed"] is True


# ─── regressions: strict envelope, type checks, secret leaks, replay runId ──

def test_strict_envelope_rejects_unknown_top_level_key():
    b = base_body()
    b["extra"] = "evil"
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "unknown_field"


def test_strict_envelope_rejects_unknown_input_key():
    b = base_body()
    b["input"]["extraInput"] = "evil"
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "unknown_field"


def test_schema_version_bool_rejected():
    b = base_body()
    # True == 1 in Python but must be rejected because type is bool, not int
    b["schemaVersion"] = True
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert "schemaVersion" in r.json()["error"]
    b2 = base_body()
    b2["schemaVersion"] = False
    r2 = fresh_client().post("/v1/execute", json=b2)
    assert r2.status_code == 400


def test_process_id_type_array_returns_400_not_500():
    b = base_body()
    b["processId"] = ["seo-audit"]
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    b2 = base_body()
    b2["processId"] = {"processId": "seo-audit"}
    r2 = fresh_client().post("/v1/execute", json=b2)
    assert r2.status_code == 400


def test_market_language_type_array_returns_400_not_500():
    for bad_market in [["br"], {"market": "br"}, 123]:
        b = base_body()
        b["input"]["market"] = bad_market  # type: ignore
        r = fresh_client().post("/v1/execute", json=b)
        assert r.status_code == 400, f"market={bad_market!r} should be 400, got {r.status_code}"
        assert r.json()["error"] == "market_must_be_br_intl_global"
    for bad_lang in [["pt-BR"], {"lang": "en"}, 123]:
        b = base_body()
        b["input"]["language"] = bad_lang  # type: ignore
        r = fresh_client().post("/v1/execute", json=b)
        assert r.status_code == 400, f"language={bad_lang!r} should be 400, got {r.status_code}"
        assert "language" in r.json()["error"]


def test_malformed_port_abc_returns_400_not_500():
    b = base_body(input={"targetUrl": "https://anderzilla.com:abc/"})
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_targetUrl"


def test_log_secret_leak_validation_failure_does_not_emit_raw_url(caplog):
    import logging
    caplog.set_level(logging.INFO)
    # URL contains userinfo, query token, fragment — must not appear in logs
    secret_url = "https://user:password@anderzilla.com/path?token=secret&x=1#frag@evil"
    b = base_body(input={"targetUrl": secret_url})
    # also inject notes with secret — should not be logged
    b["input"]["notes"] = "notes-secret-should-not-appear"
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 400
    # collect all log text (caplog captures struct logger via StreamHandler? also patch jlog)
    # Inspect captured logs from caplog.text and also ensure response body doesn't leak notes
    assert "secret-note" not in r.text
    assert "notes-secret" not in caplog.text
    # Raw URL parts must not appear — especially password and token query
    for needle in ["password", "token=secret", "user:password", secret_url]:
        assert needle not in caplog.text, f"secret leak in logs: {needle}"
    # Safe host label may appear, but raw query/fragment/userinfo must not
    # Ensure that if targetHost appears, it's just the host
    # We don't assert targetHost presence here; just absence of raw URL


def test_log_does_not_contain_raw_targetUrl_query_fragment(monkeypatch):
    # Directly capture jlog calls to ensure input.targetHost is used, not raw URL
    captured = {}

    def fake_jlog(level, msg, **fields):
        captured.update(fields)
        captured["_msg"] = msg

    monkeypatch.setattr("app.jlog", fake_jlog)
    b = base_body(input={"targetUrl": "https://anderzilla.com/path?token=secret#frag"})
    fresh_client().post("/v1/execute", json=b)
    # Should have safe host label, not raw URL
    assert "input.targetUrl" not in captured
    assert "targetUrl" not in captured
    # Check no field value contains query token or fragment
    for v in captured.values():
        if isinstance(v, str):
            assert "token=secret" not in v
            assert "frag" not in v.lower() or v.lower() == "anderzilla.com"


def test_fetch_exception_text_not_logged(monkeypatch):
    # Simulate fetch raising exception whose str contains raw URL; ensure jlog does not include it
    captured = []

    def fake_jlog(level, msg, **fields):
        captured.append((level, msg, fields))

    monkeypatch.setattr("app.jlog", fake_jlog)
    monkeypatch.setattr("app.fetch_html", MagicMock(side_effect=Exception("https://anderzilla.com/path?token=secret leaked")))
    # Use seo-audit to trigger fetch path — but we mocked fetch_html so it won't reach real fetch
    # However execute's generic except will log internal_error without exception text; the fetch path
    # raises FetchError normally, but here we force a generic exception inside fetch handling.
    # Instead test the 500 branch: mock _run_checks to raise with URL in message after fetch succeeds
    # Simpler: test generic execute_failed path via patching build_editorial_package to raise
    monkeypatch.setattr("app.fetch_html", MagicMock(return_value=(200, _html_ok(), "https://anderzilla.com/")))
    monkeypatch.setattr("app._run_checks", MagicMock(side_effect=RuntimeError("https://evil.com?token=secret")))

    b = base_body(processId="seo-audit", idempotencyKey="fetch-exc-leak")
    r = fresh_client().post("/v1/execute", json=b)
    assert r.status_code == 500
    # Ensure no captured log field contains raw URL or token
    for _level, _msg, fields in captured:
        for v in fields.values():
            if isinstance(v, str):
                assert "token=secret" not in v
                assert "https://evil.com" not in v


def test_replay_correlation_different_runId_returns_409():
    c = fresh_client()
    run1 = str(uuid.uuid4())
    run2 = str(uuid.uuid4())
    b1 = {
        "schemaVersion": 1,
        "runId": run1,
        "processId": "editorial-package",
        "idempotencyKey": "replay-runid-test",
        "input": dict(VALID_INPUT),
    }
    b2 = dict(b1)
    b2["runId"] = run2
    # same input, different runId must be 409 (only exact same runId replays)
    r1 = c.post("/v1/execute", json=b1)
    assert r1.status_code == 200
    r2 = c.post("/v1/execute", json=b2)
    assert r2.status_code == 409
    assert r2.json()["error"] == "idempotency_conflict"
    assert "runId" in r2.json()["message"] or "runid" in r2.json()["message"].lower()
    assert "processId" in r2.json()["message"] and "idempotencyKey" in r2.json()["message"]


def test_replay_correlation_exact_same_runId_and_input_replays():
    c = fresh_client()
    run = str(uuid.uuid4())
    b = {
        "schemaVersion": 1,
        "runId": run,
        "processId": "editorial-package",
        "idempotencyKey": "replay-exact-test",
        "input": dict(VALID_INPUT),
    }
    r1 = c.post("/v1/execute", json=b)
    assert r1.status_code == 200
    assert r1.json()["replayed"] is False
    r2 = c.post("/v1/execute", json=b)
    assert r2.status_code == 200
    assert r2.json()["replayed"] is True


def test_replay_correlation_same_runId_different_input_returns_409():
    c = fresh_client()
    run = str(uuid.uuid4())
    b1 = {
        "schemaVersion": 1,
        "runId": run,
        "processId": "editorial-package",
        "idempotencyKey": "replay-input-test",
        "input": {"market": "br", "language": "pt-BR", "targetUrl": "https://anderzilla.com/pt/a"},
    }
    b2 = dict(b1)
    b2["input"] = {"market": "br", "language": "pt-BR", "targetUrl": "https://anderzilla.com/pt/b"}
    # Same runId but different input — inputHash mismatch => 409 (because runId matches but input doesn't, policy requires both)
    # Our implementation requires both to match for replay; any mismatch => 409
    r1 = c.post("/v1/execute", json=b1)
    assert r1.status_code == 200
    r2 = c.post("/v1/execute", json=b2)
    assert r2.status_code == 409


def test_global_timeout_maps_to_504_via_wait_for():
    # Patch asyncio.to_thread to simulate a slow fetch that exceeds TIMEOUT_TOTAL
    import asyncio

    original_to_thread = asyncio.to_thread

    async def slow_to_thread(func, *a, **kw):
        await asyncio.sleep(9)  # longer than TIMEOUT_TOTAL (8s)
        return await original_to_thread(func, *a, **kw)

    b = base_body(processId="seo-audit", idempotencyKey="timeout-504-test")
    with patch("app.asyncio.to_thread", side_effect=slow_to_thread):
        r = fresh_client().post("/v1/execute", json=b)
    # Should be mapped to fetch_timeout 504, not 500 or hang
    assert r.status_code == 504
    assert r.json()["error"] == "fetch_timeout"


# ─── real per-hop redirect validation (httpx.Client mocked) ─────────────────

def _mock_redirect_client(location_url):
    """Helper to mock httpx.Client that returns one redirect then should be validated."""
    mock_resp = MagicMock()
    mock_resp.status_code = 302
    mock_resp.headers = {"location": location_url}
    # context manager for stream
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__.return_value = mock_resp
    mock_stream_ctx.__exit__.return_value = False
    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_ctx
    mock_client_ctx = MagicMock()
    mock_client_ctx.__enter__.return_value = mock_client
    mock_client_ctx.__exit__.return_value = False
    return mock_client_ctx


def test_fetch_redirect_to_evil_host_blocked_per_hop():
    from app import fetch_html

    with patch("app.httpx.Client", return_value=_mock_redirect_client("https://evil.com/")):
        with patch("app._host_resolves_to_private", return_value=False):
            try:
                fetch_html("https://anderzilla.com/start")
                assert False, "should have raised"
            except Exception as e:
                from app import FetchError
                assert isinstance(e, FetchError)
                assert e.code == "redirect_host_not_allowed"


def test_fetch_redirect_to_http_blocked_per_hop():
    from app import fetch_html

    with patch("app.httpx.Client", return_value=_mock_redirect_client("http://anderzilla.com/")):
        with patch("app._host_resolves_to_private", return_value=False):
            try:
                fetch_html("https://anderzilla.com/start")
                assert False, "should have raised"
            except Exception as e:
                from app import FetchError
                assert isinstance(e, FetchError)
                assert e.code == "redirect_scheme_not_https"


def test_fetch_redirect_with_userinfo_blocked_per_hop():
    from app import fetch_html

    with patch("app.httpx.Client", return_value=_mock_redirect_client("https://user:pass@anderzilla.com/")):
        with patch("app._host_resolves_to_private", return_value=False):
            try:
                fetch_html("https://anderzilla.com/start")
                assert False, "should have raised"
            except Exception as e:
                from app import FetchError
                assert isinstance(e, FetchError)
                assert "userinfo" in e.code


def test_fetch_redirect_to_private_ip_blocked_per_hop():
    from app import fetch_html

    # Redirect to allowed host that resolves to private IP
    with patch("app.httpx.Client", return_value=_mock_redirect_client("https://anderzilla.com/private")):
        with patch("app._host_resolves_to_private", side_effect=lambda h: h == "anderzilla.com" and False or True):
            # First hop's host check passes; redirect target also anderzilla.com but we force private resolution
            # To make redirect target appear private, patch _host_resolves_to_private to return True only on second call
            calls = {"n": 0}

            def fake_resolves(h):
                calls["n"] += 1
                # first call is for initial URL (anderzilla.com) — not private; second for redirect target — private
                return calls["n"] >= 2

            with patch("app._host_resolves_to_private", side_effect=fake_resolves):
                try:
                    fetch_html("https://anderzilla.com/start")
                    assert False, "should have raised"
                except Exception as e:
                    from app import FetchError
                    assert isinstance(e, FetchError)
                    assert e.code == "private_ip_blocked"


def test_fetch_redirect_chain_respects_max_redirects():
    from app import fetch_html

    # Each hop redirects to same allowed host with new path; exceed MAX_REDIRECTS
    # We need to mock Client to always return 302 for each iteration
    # fetch_html loops MAX_REDIRECTS+1 times; on the (MAX_REDIRECTS+1)th redirect it should raise too_many_redirects
    mock_resp = MagicMock()
    mock_resp.status_code = 302
    mock_resp.headers = {"location": "https://anderzilla.com/next"}
    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__.return_value = mock_resp
    mock_stream_ctx.__exit__.return_value = False
    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_ctx
    mock_client_ctx = MagicMock()
    mock_client_ctx.__enter__.return_value = mock_client
    mock_client_ctx.__exit__.return_value = False

    with patch("app.httpx.Client", return_value=mock_client_ctx):
        with patch("app._host_resolves_to_private", return_value=False):
            try:
                fetch_html("https://anderzilla.com/start")
                assert False, "should have raised"
            except Exception as e:
                from app import FetchError
                assert isinstance(e, FetchError)
                assert e.code == "too_many_redirects"


def test_fetch_redirect_valid_allowed_host_succeeds_after_one_hop():
    from app import fetch_html

    # First call returns redirect to same allowed host; second returns 200
    redirect_resp = MagicMock()
    redirect_resp.status_code = 302
    redirect_resp.headers = {"location": "https://anderzilla.com/final"}
    redirect_ctx = MagicMock()
    redirect_ctx.__enter__.return_value = redirect_resp
    redirect_ctx.__exit__.return_value = False

    final_resp = MagicMock()
    final_resp.status_code = 200
    final_resp.headers = {"content-length": "5", "content-type": "text/html; charset=utf-8"}
    final_resp.iter_bytes.return_value = [b"hello"]
    final_ctx = MagicMock()
    final_ctx.__enter__.return_value = final_resp
    final_ctx.__exit__.return_value = False

    mock_client = MagicMock()
    mock_client.stream.side_effect = [redirect_ctx, final_ctx]
    mock_client_ctx = MagicMock()
    mock_client_ctx.__enter__.return_value = mock_client
    mock_client_ctx.__exit__.return_value = False

    with patch("app.httpx.Client", return_value=mock_client_ctx):
        with patch("app._host_resolves_to_private", return_value=False):
            status, body, final_url = fetch_html("https://anderzilla.com/start")
            assert status == 200
            assert body == "hello"
            assert final_url == "https://anderzilla.com/final"


# ─── regression: DNS must not block validation; slow DNS contained by deadline ──

def test_validation_does_not_call_getaddrinfo(monkeypatch):
    """validate_execute_body / _validate_target_url must be purely syntactic — no DNS."""
    import app as appmod
    from app import _validate_target_url

    # Any call to socket.getaddrinfo during validation is a failure — it would
    # block the event loop outside the global 8s wait_for deadline.
    def fail_getaddrinfo(*_a, **_kw):
        raise AssertionError("socket.getaddrinfo must not be called during validation")

    def fail_host_resolves(*_a, **_kw):
        raise AssertionError("_host_resolves_to_private must not be called during validation")

    # Patch both import paths that _host_resolves_to_private uses
    with patch("socket.getaddrinfo", side_effect=fail_getaddrinfo):
        with patch("app.socket.getaddrinfo", side_effect=fail_getaddrinfo):
            with patch("app._host_resolves_to_private", side_effect=fail_host_resolves):
                url, err = _validate_target_url("https://anderzilla.com/path")
                assert err == "", f"syntactic valid URL should pass: {err}"
                assert url == "https://anderzilla.com/path"

                url2, err2 = _validate_target_url("https://www.anderzilla.com/")
                assert err2 == ""

                # Language-level validation still syntactic
                _, err3 = _validate_target_url("https://anderzilla.com:abc/")
                assert err3 == "invalid_targetUrl"

    # editorial-package goes through validate_execute_body only — no fetch, no DNS
    with patch("socket.getaddrinfo", side_effect=fail_getaddrinfo):
        with patch("app.socket.getaddrinfo", side_effect=fail_getaddrinfo):
            with patch("app._host_resolves_to_private", side_effect=fail_host_resolves):
                b = base_body(processId="editorial-package", idempotencyKey="regression-no-dns-ed-1")
                r = fresh_client().post("/v1/execute", json=b)
                assert r.status_code == 200, r.text
                assert r.json()["status"] == "succeeded"

    # Another editorial-package with explicit targetUrl must also not hit DNS
    with patch("app._host_resolves_to_private", side_effect=fail_host_resolves):
        with patch("socket.getaddrinfo", side_effect=fail_getaddrinfo):
            b = base_body(processId="editorial-package", idempotencyKey="regression-no-dns-ed-2")
            r = fresh_client().post("/v1/execute", json=b)
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_slow_dns_in_seo_audit_contained_by_to_thread_wait_for(monkeypatch):
    """Slow DNS inside fetch_html must be inside asyncio.to_thread and bounded by wait_for -> 504.

    Uses httpx.AsyncClient (ASGI) because FastAPI's sync TestClient waits for the
    worker thread to finish even after wait_for times out, masking the non-blocking
    property. The real server (uvicorn) returns at the deadline; AsyncClient mirrors that.
    """
    import time
    import httpx
    import app as appmod
    from app import app as fastapi_app
    from app import _replay as _r

    _r.clear()
    # Shorten the global deadline so the test is fast; restore automatically via monkeypatch
    monkeypatch.setattr(appmod, "TIMEOUT_TOTAL", 0.35)

    def slow_host_resolves(hostname: str) -> bool:
        time.sleep(2.0)  # longer than the 0.35s deadline — would block forever if run on event loop
        return False

    def slow_getaddrinfo(*_a, **_kw):
        time.sleep(2.0)
        return []

    monkeypatch.setattr(appmod, "_host_resolves_to_private", slow_host_resolves)

    b = base_body(processId="seo-audit", idempotencyKey="regression-slow-dns-1")
    start = time.monotonic()
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch("socket.getaddrinfo", side_effect=slow_getaddrinfo):
            with patch("app.socket.getaddrinfo", side_effect=slow_getaddrinfo):
                r = await ac.post("/v1/execute", json=b)
    elapsed = time.monotonic() - start

    assert r.status_code == 504, r.text
    assert r.json()["error"] == "fetch_timeout"
    # Contained by deadline: wall time should be ~TIMEOUT_TOTAL, not ~2s DNS sleep
    assert elapsed < 1.5, f"slow DNS not contained by wait_for deadline: elapsed {elapsed:.2f}s"
    assert elapsed >= 0.30, f"returned too fast, deadline not honored: {elapsed:.2f}s"

    # Give the still-running worker thread time to finish before the next request
    # (it holds the monkeypatched slow function; next test would otherwise inherit it)
    await asyncio.sleep(2.2)

    # The same slow DNS must not affect editorial-package (no fetch), which should succeed instantly
    _r.clear()
    # Re-apply slow patches for the editorial check — but editorial-package should not call them
    monkeypatch.setattr(appmod, "_host_resolves_to_private", slow_host_resolves)
    with patch("app._host_resolves_to_private", side_effect=slow_host_resolves):
        with patch("socket.getaddrinfo", side_effect=slow_getaddrinfo):
            with patch("app.socket.getaddrinfo", side_effect=slow_getaddrinfo):
                b2 = base_body(processId="editorial-package", idempotencyKey="regression-slow-dns-ed-2")
                start2 = time.monotonic()
                # editorial-package via sync client is fine (no network)
                r2 = fresh_client().post("/v1/execute", json=b2)
                elapsed2 = time.monotonic() - start2
                assert r2.status_code == 200, r2.text
                assert elapsed2 < 0.5, f"editorial-package should not be delayed by DNS: {elapsed2:.2f}s"
