"""GCP worker OIDC verification. Bearer only, fail closed, never logs token/claims.

Dedicated transport header X-AnderZilla-Worker-Authorization carries the
Google ID token (Bearer scheme) through Azure Static Web Apps, which can
consume/strip the standard Authorization header. Token remains Google OIDC
and is validated by application (verify_oauth2_token + aud/sub/email checks).
"""

import os
import time as _time
from core import Error

# Dedicated transport header through Azure Static Web Apps.
WORKER_AUTH_HEADER = "x-anderzilla-worker-authorization"
WORKER_AUTH_HEADER_CANONICAL = "X-AnderZilla-Worker-Authorization"

# Explicit sensitive-field stripping — never log or return header/token/claims.
_SENSITIVE_FIELDS = frozenset(
    {
        "authorization",
        "x-anderzilla-worker-authorization",
        "cookie",
        "token",
        "id_token",
        "access_token",
        "secret",
        "credential",
    }
)


_CERT_TIMEOUT_SECONDS = 5
_CLOCK_SKEW_SECONDS = 60

# No in-process cache of validated caller tokens past exp is kept; signature
# and expiry remain the authority of google-auth. Cert fetch timeout is bound
# via a requests Session injected into google.auth.transport.requests.Request.
# google-auth does not expose a direct timeout parameter; using
# requests.Session.request timeout is the documented safe approach. If the
# google-auth API changed to not accept a Session, this would need revisiting;
# see comments in _build_request.
# A small TTL cache of certs could be added only if it does not bypass
# signature/exp verification — not implemented here to avoid caching validated
# tokens past exp. Verified tokens are not cached.


def _build_request():
    """Build google.auth.transport.requests.Request with bounded cert fetch.

    google-auth's Request accepts a requests.Session. We provide a Session
    subclass that injects a short timeout for every HTTP request (cert fetch).
    This gives an actual short timeout for cert retrieval without bypassing
    signature/expiry checks. No validated token is cached past exp.

    Limitation: timeout is enforced at the requests layer; if google-auth
    internals stop using Session.request, timeout would not apply. This is
    the simplest documented safe approach with current google-auth 2.x.
    """
    try:
        import requests  # type: ignore
        import google.auth.transport.requests as grequests  # type: ignore

        class _TimeoutSession(requests.Session):
            def request(self, *args, **kwargs):
                kwargs["timeout"] = _CERT_TIMEOUT_SECONDS
                return super().request(*args, **kwargs)

        session = _TimeoutSession()
        # google-auth Request will use session.get with timeout via above override
        return grequests.Request(session=session)
    except Error:
        raise
    except Exception:
        # Dependency/service setup failure – fail closed without leaking details
        raise Error(503, "unavailable", "Serviço temporariamente indisponível.")


def _get_settings(env=None):
    source = env if env is not None else os.environ
    aud = source.get("CMS_GOOGLE_WORKER_AUDIENCE")
    sub = source.get("CMS_GOOGLE_WORKER_SUBJECT")
    email = source.get("CMS_GOOGLE_WORKER_EMAIL")
    if not aud or not sub or not email:
        raise Error(503, "unavailable", "Serviço temporariamente indisponível.")
    return aud, sub, email


def _validate_claims_time(claims):
    """Defense-in-depth exp/iat checks while google library remains authority.

    - exp must be numeric and strictly in the future (exp > now).
    - iat must be numeric if present and not unreasonably in the future (> now + 60s).
    Missing or non-numeric exp/iat fails.
    Google's verify_oauth2_token remains the signature/expiry authority; this
    is an additional check. exp is strict (no skew); iat allows up to 60s
    future skew to tolerate minor clock differences.
    """
    now = _time.time()
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)):
        raise Error(401, "authentication_required", "Autenticação necessária.")
    if exp <= now:
        raise Error(401, "authentication_required", "Autenticação necessária.")
    # iat check
    iat = claims.get("iat")
    if iat is not None:
        if not isinstance(iat, (int, float)):
            raise Error(401, "authentication_required", "Autenticação necessária.")
        if iat > now + _CLOCK_SKEW_SECONDS:
            raise Error(401, "authentication_required", "Autenticação necessária.")
    else:
        # iat is expected; require presence for defense in depth
        raise Error(401, "authentication_required", "Autenticação necessária.")


def _validate_aud(claims, aud):
    """Require aud claim exactly the configured audience string."""
    aud_claim = claims.get("aud")
    # Must be exactly the configured string, not list, not missing, not wrong
    if not isinstance(aud_claim, str) or aud_claim != aud:
        raise Error(401, "authentication_required", "Autenticação necessária.")


def authenticate_worker(headers, url=None, env=None, verifier=None, body=None):
    """Validate GCP OIDC token from dedicated transport header.

    Transport: X-AnderZilla-Worker-Authorization: Bearer <Google ID token>
    Azure Static Web Apps managed auth can consume/strip the standard
    Authorization header, so only the dedicated header is read.
    Never accept token from standard Authorization, query, cookie, body,
    or alternate headers. Bearer scheme and all OIDC checks still required.

    - Bearer only, no query/cookie/body token.
    - Verifies signature/certs, exp, audience, issuer Google, exact sub, exact email, email_verified.
    - Returns machine principal with only role anderzilla_worker.
    - Fed `verifier` allows dependency injection for tests: verifier(token, audience) -> claims dict.
      Even with injected verifier, aud is strictly checked for exact string, and
      exp/iat defense checks apply.
    - Never logs or returns header/token/claims; header lowercased name is in _SENSITIVE_FIELDS.
    """
    try:
        # No token in query
        if url and isinstance(url, str):
            low = url.lower()
            # block token in query string; simple heuristic
            if "token=" in low or "id_token" in low or "access_token" in low:
                raise Error(401, "authentication_required", "Autenticação necessária.")
        # No token in cookie
        cookie_val = None
        if isinstance(headers, dict):
            for key, value in headers.items():
                if key.lower() == "cookie" and isinstance(value, str) and value.strip():
                    cookie_val = value
                    break
        if cookie_val and ("bearer" in cookie_val.lower() or "token=" in cookie_val.lower()):
            raise Error(401, "authentication_required", "Autenticação necessária.")
        # No token in body — reject if body contains token-like keys (never accept bearer from body)
        if isinstance(body, dict):
            for key in body.keys():
                if isinstance(key, str) and key.lower() in _SENSITIVE_FIELDS:
                    # token/id_token/access_token in body not allowed; also authorization key
                    raise Error(401, "authentication_required", "Autenticação necessária.")
                # Also reject any value that looks like Bearer token in body
                if isinstance(body.get(key), str) and body.get(key, "").strip().lower().startswith("bearer "):
                    raise Error(401, "authentication_required", "Autenticação necessária.")

        # Extract Bearer from dedicated header only — do not read standard Authorization
        auth = None
        if isinstance(headers, dict):
            for key, value in headers.items():
                if key.lower() == WORKER_AUTH_HEADER:
                    auth = value
                    break
        if not auth or not isinstance(auth, str) or not auth.startswith("Bearer "):
            raise Error(401, "authentication_required", "Autenticação necessária.")
        token = auth[7:].strip()
        if not token:
            raise Error(401, "authentication_required", "Autenticação necessária.")
        # Reject obviously malformed token containing whitespace/newline
        if any(c.isspace() for c in token):
            raise Error(401, "authentication_required", "Autenticação necessária.")

        aud, sub, email = _get_settings(env)

        if verifier is not None:
            claims = verifier(token, aud)
        else:
            import google.oauth2.id_token  # type: ignore

            request = _build_request()
            # Use verify_oauth2_token (not verify_token) when appropriate
            claims = google.oauth2.id_token.verify_oauth2_token(token, request=request, audience=aud)

        # Strict aud check even with injected verifier
        _validate_aud(claims, aud)
        # Defense-in-depth time checks (google remains signature/expiry authority)
        _validate_claims_time(claims)

        # issuer
        iss = claims.get("iss")
        if iss not in ("https://accounts.google.com", "accounts.google.com"):
            raise Error(401, "authentication_required", "Autenticação necessária.")
        if claims.get("sub") != sub:
            raise Error(401, "authentication_required", "Autenticação necessária.")
        if claims.get("email") != email:
            raise Error(401, "authentication_required", "Autenticação necessária.")
        if claims.get("email_verified") is not True:
            raise Error(401, "authentication_required", "Autenticação necessária.")

        return {"id": sub, "sub": sub, "email": email, "roles": ["anderzilla_worker"], "name": email}
    except Error:
        raise
    except Exception:
        # Never log or return token/claims/body/custom header (x-anderzilla-worker-authorization)
        raise Error(401, "authentication_required", "Autenticação necessária.")
