"""Bearer-only visitor API. Native cookies and SWA principals cannot authorize it."""
import os
from urllib.parse import parse_qs, unquote, urlsplit

from .api import fields, response
from .clerk_auth import ClerkGateway, settings
from .clerk_service import ClerkAccountService, POLICY_VERSION
from .core import Rejected, reject
from .member_service import MemberAreaService, reject_authority_fields

ALLOWED_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}
ALLOWED_HEADERS = 'Authorization, X-AnderZilla-Authorization, Content-Type, Idempotency-Key, If-Match'


def dispatch_clerk(store, method, path, headers=None, body=None, gateway=None, cfg=None, clock=None):
    cfg = cfg or settings()
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    # SWA owns and overwrites Authorization on its internal Functions hop.
    # Our header still carries a fully verified Clerk bearer, never a principal.
    authorization = headers.get('x-anderzilla-authorization')
    if authorization is None and os.environ.get('AZ_ACCOUNT_AUTH_PROVIDER') != 'clerk':
        authorization = headers.get('authorization')
    origin = headers.get('origin')
    cors = {'Vary': 'Origin', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'}
    if origin in cfg['origins']:
        cors['Access-Control-Allow-Origin'] = origin
    try:
        if origin and origin not in cfg['origins']:
            reject('invalid_origin', 'Origem não permitida.', 403)
        parsed = urlsplit(path)
        route = parsed.path.rstrip('/')
        query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
        if method == 'OPTIONS':
            if origin not in cfg['origins'] or headers.get('access-control-request-method') not in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}:
                reject('invalid_origin', 'Origem não permitida.', 403)
            return response(
                status=204,
                headers={
                    **cors,
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': ALLOWED_HEADERS,
                    'Access-Control-Max-Age': '600',
                },
            )
        member_svc = MemberAreaService(store, cfg, clock=clock)
        if method == 'GET' and route == '/api/account/capabilities':
            p_state = member_svc.program_state()
            return response(
                {
                    'provider': 'clerk',
                    'available': cfg['ok'],
                    'registration': cfg['ok'],
                    'emailPassword': False,
                    'google': False,
                    'meta': False,
                    'passwordReset': False,
                    'emailResend': False,
                    'rewards': bool(cfg['ok'] and p_state in {'active', 'new_activity_paused'}),
                    'kpProgramState': p_state if cfg['ok'] else 'disabled',
                    'memberArea': cfg['ok'],
                    'minimumAge': 18,
                    'minorAccessEnabled': False,
                    'termsVersion': POLICY_VERSION,
                    'privacyVersion': POLICY_VERSION,
                },
                headers=cors,
            )
        if not cfg['ok']:
            reject('temporarily_unavailable', 'Serviço de contas não configurado.', 503)
        if method == 'GET' and route == '/api/account/ready':
            if hasattr(store, 'health') and not store.health().get('healthy'):
                reject('temporarily_unavailable', 'Ativando serviço de contas.', 503)
            return response({'ready': True}, headers=cors)
        if method in {'POST', 'PATCH', 'DELETE', 'PUT'}:
            if origin not in cfg['origins']:
                reject('invalid_origin', 'Origem obrigatória.', 403)
            if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                reject('unsupported_media_type', 'Use JSON.', 415)
        body = {} if body is None else body
        if not isinstance(body, dict):
            reject('invalid_body', 'Objeto JSON obrigatório.')
        service = member_svc.accounts
        if method == 'GET' and route == '/api/account/me' and not authorization:
            return response({'account': None, 'onboardingRequired': False}, headers=cors)
        gateway = gateway or ClerkGateway(cfg)
        identity = gateway.verify(authorization)

        # Account routes
        if method == 'GET' and route == '/api/account/me':
            result = service.me(identity)
            if result.get('account'):
                result['wallet'] = member_svc.get_wallet(identity)
            return response(result, headers=cors)
        if method == 'POST' and route == '/api/account/onboarding':
            fields(body, 'cpf displayName birthDate termsAccepted termsVersion privacyVersion marketingOptIn lang')
            service.onboard(identity, body)
            result = service.me(identity)
            if result.get('account'):
                result['wallet'] = member_svc.get_wallet(identity)
            return response(result, headers=cors)
        if method == 'PATCH' and route == '/api/account/profile':
            reject_authority_fields(body)
            return response(service.profile(identity, body), headers=cors)
        if method == 'GET' and route == '/api/account/export':
            return response(
                service.export(identity),
                headers={**cors, 'Content-Disposition': 'attachment; filename="anderzilla-account.json"'},
            )
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

        # Member Area routes (/api/member/*)
        if route == '/api/member/dashboard' and method == 'GET':
            return response(member_svc.get_dashboard(identity), headers=cors)
        if route == '/api/member/radar' and method == 'GET':
            return response(member_svc.get_radar(identity, query), headers=cors)
        if route == '/api/member/interests':
            if method == 'GET':
                return response(member_svc.get_interests(identity), headers=cors)
            if method == 'PUT':
                return response(member_svc.put_interests(identity, body, headers), headers=cors)
        if route == '/api/member/backpack' and method == 'GET':
            return response(member_svc.get_backpack(identity, query), headers=cors)
        if route.startswith('/api/member/backpack/'):
            disc_id = unquote(route[len('/api/member/backpack/'):])
            if method == 'PUT':
                fields(body, '')
                return response(member_svc.put_backpack_item(identity, disc_id), headers=cors)
            if method == 'DELETE':
                fields(body, '')
                return response(member_svc.delete_backpack_item(identity, disc_id), headers=cors)
        if route == '/api/member/exploration' and method == 'GET':
            return response(member_svc.get_exploration(identity, query), headers=cors)
        if route == '/api/member/exploration/events' and method == 'POST':
            return response(member_svc.record_exploration_event(identity, body), headers=cors)
        if route == '/api/member/exploration/clear' and method == 'POST':
            return response(member_svc.clear_exploration(identity, body), headers=cors)
        if route.startswith('/api/member/exploration/') and method == 'DELETE':
            disc_id = unquote(route[len('/api/member/exploration/'):])
            if disc_id not in {'events', 'clear'}:
                fields(body, '')
                return response(member_svc.delete_exploration_item(identity, disc_id), headers=cors)

        # Karaca Points & Missions routes (/api/points/*)
        if route == '/api/points/wallet' and method == 'GET':
            return response(member_svc.get_wallet(identity), headers=cors)
        if route == '/api/points/ledger' and method == 'GET':
            return response(member_svc.get_ledger(identity, query), headers=cors)
        if route == '/api/points/missions' and method == 'GET':
            return response(member_svc.list_missions(identity), headers=cors)
        if route == '/api/points/challenge' and method == 'POST':
            return response(member_svc.start_challenge(identity, body, headers), headers=cors)
        if route.startswith('/api/points/challenges/') and method == 'GET':
            attempt_id = unquote(route[len('/api/points/challenges/'):])
            return response(member_svc.get_challenge(identity, attempt_id), headers=cors)
        if route == '/api/points/evidence' and method == 'POST':
            return response(member_svc.submit_evidence(identity, body, headers), headers=cors)
        if route in {'/api/points/pending/claim', '/api/points/claim'} and method == 'POST':
            return response(member_svc.claim_pending(identity, body, headers), headers=cors)
        if route.startswith('/api/points/operations/') and method == 'GET':
            op_id = unquote(route[len('/api/points/operations/'):])
            return response(member_svc.get_operation(identity, op_id), headers=cors)
        if route == '/api/points/operation-status' and method == 'GET':
            return response(member_svc.get_operation_status_by_key(identity, query, headers), headers=cors)

        reject('not_found', 'Rota não encontrada.', 404)
    except Rejected as error:
        return response({'error': {'code': error.code, 'message': str(error)}}, error.status, cors)
