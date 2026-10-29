"""HTTP edge of the review site API, served only as the managed API of a Static Web App.

Every request already passed the Static Web Apps edge: it requires the signed-in role `anderzilla_admin` and replaces any
client-supplied identity headers, so `x-ms-client-principal` is trustworthy only here. This app never accepts agent keys;
agent routes answer 401. Because sign-in is cookie based, state-changing requests also need a JSON body and a same-origin
`Origin`, which a cross-site form or script cannot produce (there is no CORS)."""
import base64
import json
import logging
import os
from urllib.parse import urlsplit
from agent_api import AgentGateway, handle
from core import CMS, Error

MAX_JSON_BYTES = 300000
SECURITY_HEADERS = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Robots-Tag': 'noindex, nofollow'}
_gateway = None


def default_gateway():
    global _gateway
    if _gateway is None:
        from storage import AzureSQLStore
        _gateway = AgentGateway(CMS(AzureSQLStore()), review_base=os.environ.get('CMS_REVIEW_BASE', ''))
    return _gateway


def swa_principal(encoded):
    """Decode the Static Web Apps principal. Only an authenticated user with string roles is accepted."""
    try:
        principal = json.loads(base64.b64decode(encoded or '', validate=True))
        roles = principal.get('userRoles', [])
        if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles) or not principal.get('userId') or 'authenticated' not in roles:
            return None
        return {'id': principal['userId'], 'name': principal.get('userDetails', ''), 'roles': roles}
    except (ValueError, TypeError, KeyError, AttributeError):
        return None


def reply(status, payload, extra=None):
    return status, payload, {**SECURITY_HEADERS, **(extra or {})}


def same_origin(headers, allowed=None):
    """True when there is no Origin header (same-origin GET/fetch without it) or it matches this site."""
    origin = headers.get('origin')
    if not origin:
        return True
    allowed = allowed or os.environ.get('REVIEW_ALLOWED_ORIGIN', '')
    if allowed:
        return origin == allowed
    host = headers.get('x-forwarded-host') or headers.get('host') or ''
    return urlsplit(origin).netloc == host.split(',')[0].strip()


def process(method, route_path, query, headers, raw, gateway_factory=default_gateway):
    """Return (status, payload, headers). `headers` is a plain dict with lower-case names."""
    try:
        path = '/v1/' + route_path.strip('/')
        if method == 'GET' and path == '/v1/health':
            return reply(200, {'status': 'ok'})
        if method not in {'GET', 'POST'}:
            raise Error(405, 'method_not_allowed', 'Método não permitido.')
        if method == 'POST':
            if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                raise Error(415, 'unsupported_media_type', 'Use application/json.')
            if not same_origin(headers):
                raise Error(403, 'invalid_origin', 'Origem não permitida.')
        if len(raw) > MAX_JSON_BYTES:
            raise Error(413, 'too_large', 'Requisição muito grande.')
        try:
            body = json.loads(raw) if raw else {}
        except (ValueError, UnicodeDecodeError):
            raise Error(400, 'invalid_json', 'JSON inválido.')
        if not isinstance(body, dict):
            raise Error(422, 'invalid_body', 'Objeto JSON obrigatório.')
        human = swa_principal(headers.get('x-ms-client-principal'))
        status, payload = handle(gateway_factory(), method, path, body, None, human, headers.get('idempotency-key'), query)
        return reply(status, payload)
    except Error as error:
        return reply(error.status, {'error': {'code': error.code, 'message': str(error)}})
    except Exception as error:
        logging.error('Review API unavailable (%s); no request data is logged.', type(error).__name__)
        return reply(503, {'error': {'code': 'unavailable', 'message': 'Serviço temporariamente indisponível. Tente de novo em instantes.'}}, {'Retry-After': '30'})
