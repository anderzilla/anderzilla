"""Bearer-only visitor API. Native cookies and SWA principals cannot authorize it."""
from urllib.parse import urlsplit

from .api import response, fields
from .core import Rejected, reject
from .clerk_auth import ClerkGateway, settings
from .clerk_service import ClerkAccountService, POLICY_VERSION


def dispatch_clerk(store, method, path, headers=None, body=None, gateway=None, cfg=None, clock=None):
    cfg = cfg or settings()
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    origin = headers.get('origin')
    cors = {'Vary': 'Origin', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'}
    if origin in cfg['origins']:
        cors['Access-Control-Allow-Origin'] = origin
    try:
        if origin and origin not in cfg['origins']:
            reject('invalid_origin', 'Origem não permitida.', 403)
        route = urlsplit(path).path.rstrip('/')
        if method == 'OPTIONS':
            if origin not in cfg['origins'] or headers.get('access-control-request-method') not in {'GET', 'POST', 'PATCH'}:
                reject('invalid_origin', 'Origem não permitida.', 403)
            return response(status=204, headers={**cors, 'Access-Control-Allow-Methods': 'GET, POST, PATCH, OPTIONS',
                                                'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Max-Age': '600'})
        if method == 'GET' and route == '/api/account/capabilities':
            return response({'provider': 'clerk', 'available': cfg['ok'], 'registration': cfg['ok'], 'emailPassword': False,
                             'google': False, 'meta': False, 'passwordReset': False, 'emailResend': False, 'rewards': False,
                             'minimumAge': 18, 'minorAccessEnabled': False,
                             'termsVersion': POLICY_VERSION, 'privacyVersion': POLICY_VERSION}, headers=cors)
        if not cfg['ok']:
            reject('temporarily_unavailable', 'Serviço de contas não configurado.', 503)
        if method in {'POST', 'PATCH', 'DELETE', 'PUT'}:
            if origin not in cfg['origins']:
                reject('invalid_origin', 'Origem obrigatória.', 403)
            if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                reject('unsupported_media_type', 'Use JSON.', 415)
        body = {} if body is None else body
        if not isinstance(body, dict):
            reject('invalid_body', 'Objeto JSON obrigatório.')
        service = ClerkAccountService(store, cfg, clock=clock)
        if method == 'GET' and route == '/api/account/me' and not headers.get('authorization'):
            return response({'account': None, 'onboardingRequired': False}, headers=cors)
        gateway = gateway or ClerkGateway(cfg)
        identity = gateway.verify(headers.get('authorization'))
        if method == 'GET' and route == '/api/account/me':
            return response(service.me(identity), headers=cors)
        if method == 'POST' and route == '/api/account/onboarding':
            fields(body, 'cpf displayName birthDate termsAccepted termsVersion privacyVersion marketingOptIn lang')
            service.onboard(identity, body)
            return response(service.me(identity), headers=cors)
        if method == 'PATCH' and route == '/api/account/profile':
            return response(service.profile(identity, body), headers=cors)
        if method == 'GET' and route == '/api/account/export':
            return response(service.export(identity), headers=cors)
        if method == 'POST' and route == '/api/account/delete':
            fields(body, 'confirm')
            deleted = service.delete(identity, body.get('confirm'))
            try:
                gateway.delete_user(identity.subject)
            except Rejected:
                reject('deletion_pending', 'A conta foi bloqueada e a exclusão no provedor será concluída.', 503)
            service.finish_delete(deleted['accountId'])
            return response(status=204, headers=cors)
        if method == 'POST' and route == '/api/account/logout':
            fields(body, '')
            gateway.revoke_session(identity.session_id)
            return response(status=204, headers=cors)
        reject('not_found', 'Rota não encontrada.', 404)
    except Rejected as error:
        return response({'error': {'code': error.code, 'message': str(error)}}, error.status, cors)
