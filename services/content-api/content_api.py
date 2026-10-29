"""HTTP edge of the AI-agent content API (no Azure dependency, so it is testable without a Functions host).

This app is public: it accepts only per-agent bearer keys. Human routes (approve, comment, request changes,
promote) are never served here; they live behind the Microsoft sign-in of the review site. Any identity header a
client sends (x-ms-client-principal, cookies) is ignored. Responses never echo secrets or driver errors."""
import json
import logging
import os
from agent_api import AgentGateway, handle
from core import CMS, Error

MAX_JSON_BYTES = 300000
MAX_MEDIA_BYTES = 3000000  # a 2 MiB image as base64 plus the JSON envelope
SECURITY_HEADERS = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Robots-Tag': 'noindex, nofollow'}
_gateway = None


def default_gateway():
    """One gateway per worker process; the SQL connection is opened per transaction, never held."""
    global _gateway
    if _gateway is None:
        from storage import AzureSQLStore
        _gateway = AgentGateway(CMS(AzureSQLStore()))
    return _gateway


def reply(status, payload, extra=None):
    return status, payload, {**SECURITY_HEADERS, **(extra or {})}


def process(method, route_path, query, headers, raw, gateway_factory=default_gateway):
    """Return (status, payload, headers). `headers` is a plain dict with lower-case names."""
    try:
        path = '/v1/' + route_path.strip('/')
        if method == 'GET' and path == '/v1/health':
            return reply(200, {'status': 'ok'})  # liveness only: no database access, no data
        if method not in {'GET', 'POST'}:
            raise Error(405, 'method_not_allowed', 'Método não permitido.')
        if method == 'POST' and headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
            raise Error(415, 'unsupported_media_type', 'Use application/json.')
        if len(raw) > (MAX_MEDIA_BYTES if path == '/v1/media' else MAX_JSON_BYTES):
            raise Error(413, 'too_large', 'Requisição muito grande.')
        try:
            body = json.loads(raw) if raw else {}
        except (ValueError, UnicodeDecodeError):
            raise Error(400, 'invalid_json', 'JSON inválido.')
        if not isinstance(body, dict):
            raise Error(422, 'invalid_body', 'Objeto JSON obrigatório.')
        status, payload = handle(gateway_factory(), method, path, body, headers.get('authorization'), None, headers.get('idempotency-key'), query)
        return reply(status, payload, {'WWW-Authenticate': 'Bearer'} if status == 401 else None)
    except Error as error:
        extra = {'WWW-Authenticate': 'Bearer'} if error.status == 401 else None
        return reply(error.status, {'error': {'code': error.code, 'message': str(error)}}, extra)
    except Exception as error:
        logging.error('Content API unavailable (%s); no request data is logged.', type(error).__name__)
        return reply(503, {'error': {'code': 'unavailable', 'message': 'Serviço temporariamente indisponível. Tente de novo em instantes.'}}, {'Retry-After': '30'})
