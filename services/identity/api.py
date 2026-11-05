"""HTTP contract. Cookies and Origin/CSRF authorize visitors, never SWA admin headers."""
import os
import re
from urllib.parse import urlsplit, parse_qs
from . import security
from .config import check_config, POLICY_VERSION
from .core import Rejected, SESSION_TTL, reject

CONTEXT_COOKIE = '__Host-anderzilla_context'
SESSION_COOKIE = '__Host-anderzilla_sid'
MUTATIONS = {'POST', 'PUT', 'PATCH', 'DELETE'}


def response(body=None, status=200, headers=None):
    return {'status': status, 'body': body if body is not None else {}, 'headers': {'Cache-Control': 'no-store', **(headers or {})}}


def context(headers):
    raw = security.cookies(headers.get('cookie', '')).get(CONTEXT_COOKIE, '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}\.[A-Za-z0-9_-]{43}', raw):
        return None
    browser, csrf = raw.split('.')
    return {'raw': raw, 'browserHash': security.token_hash(browser), 'csrfToken': csrf}


def fields(body, allowed):
    if set(body) - set(allowed.split()):
        reject('invalid_fields', 'Campos desconhecidos.')


def dispatch(service, method, path, headers=None, body=None):
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    cfg = check_config()
    cors = {'Vary': 'Origin', 'X-Content-Type-Options': 'nosniff'}
    origin = headers.get('origin')
    if cfg['origin'] and origin == cfg['origin']:
        cors.update({'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Credentials': 'true'})
    try:
        if origin and origin != cfg['origin']:
            reject('invalid_origin', 'Origem não permitida.', 403)
        parsed = urlsplit(path)
        route = parsed.path.rstrip('/')
        query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
        if method == 'OPTIONS':
            if not cfg['origin'] or origin != cfg['origin']:
                reject('invalid_origin', 'Origem não permitida.', 403)
            requested = headers.get('access-control-request-method', '')
            if requested not in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}:
                reject('invalid_method', 'Método não permitido.', 405)
            return response(status=204, headers={**cors, 'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
                            'Access-Control-Allow-Headers': 'Content-Type, X-CSRF-Token, Idempotency-Key, If-Match', 'Access-Control-Max-Age': '600'})
        if body is None:
            body = {}
        if not isinstance(body, dict):
            reject('invalid_body', 'Objeto JSON obrigatório.')
        ctx = context(headers)
        if method == 'GET' and route == '/api/account/capabilities':
            extra = dict(cors)
            if ctx is None:
                raw = security.random_token() + '.' + security.random_token()
                extra['Set-Cookie'] = security.cookie(CONTEXT_COOKIE, raw, SESSION_TTL, cfg['sameSite'] if cfg['sameSite'] in {'Lax', 'None', 'Strict'} else 'Lax')
                ctx = context({'cookie': f'{CONTEXT_COOKIE}={raw}'})
            email_ready = cfg['ok'] and service.email_ready()
            return response({'available': cfg['ok'], 'registration': bool(email_ready), 'emailPassword': cfg['ok'],
                             'google': cfg['ok'] and cfg['google'], 'meta': False, 'passwordReset': False, 'emailResend': bool(email_ready),
                             'rewards': cfg['ok'] and cfg['rewards'], 'minimumAge': 18, 'minimumAge18': True,
                             'termsVersion': POLICY_VERSION, 'privacyVersion': POLICY_VERSION, 'csrfToken': ctx['csrfToken']}, headers=extra)
        if not cfg['ok']:
            reject('temporarily_unavailable', 'Contas temporariamente indisponíveis.', 503)
        if method in MUTATIONS:
            if origin != cfg['origin']:
                reject('invalid_origin', 'Origem obrigatória e válida.', 403)
            if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                reject('unsupported_media_type', 'Use application/json.', 415)
            if ctx is None or not security.equal(ctx['csrfToken'], headers.get('x-csrf-token')):
                reject('csrf_failed', 'Atualize a página e tente novamente.', 403)
        token = security.cookies(headers.get('cookie', '')).get(SESSION_COOKIE)
        principal = None
        if token:
            principal = service.authenticate(token)

        def authenticated():
            if principal is None:
                reject('authentication_required', 'Entre na sua conta.', 401)
            return principal

        def login_result(result):
            # Revoke old cookie session after authenticating a new identity.
            if token:
                service.logout(token)
            return response({'accountId': result['accountId']}, headers={**cors, 'Set-Cookie': security.cookie(SESSION_COOKIE, result['sessionToken'], SESSION_TTL, cfg['sameSite'])})

        if method == 'POST' and route == '/api/account/register':
            fields(body, 'email password displayName lang timezone marketingOptIn interests ageConfirmed termsAccepted termsVersion privacyVersion')
            return response(service.register(body, ctx['browserHash']), 201, cors)
        if method == 'POST' and route == '/api/account/login':
            fields(body, 'email password')
            return login_result(service.login(body.get('email'), body.get('password'), ctx['browserHash']))
        if method == 'POST' and route == '/api/account/verify':
            fields(body, 'token')
            return response(service.verify_email(body.get('token'), ctx['browserHash']), headers=cors)
        if method == 'POST' and route == '/api/account/resend':
            fields(body, '')
            return response(service.resend(authenticated()), headers=cors)
        if method == 'POST' and route in {'/api/account/logout', '/api/account/logout-all'}:
            fields(body, '')
            if route.endswith('logout-all'):
                service.logout_all(authenticated())
            elif token:
                service.logout(token)
            return response(status=204, headers={**cors, 'Set-Cookie': security.cookie(SESSION_COOKIE, '', 0, cfg['sameSite'])})
        if method == 'GET' and route == '/api/account/me':
            result = service.me(authenticated())
            if ctx is not None:
                result['csrfToken'] = ctx['csrfToken']
            return response(result, headers=cors)
        if method == 'PATCH' and route == '/api/account/profile':
            return response(service.update_profile(authenticated(), body), headers=cors)
        if method == 'GET' and route == '/api/account/export':
            return response(service.export_data(authenticated()), headers={**cors, 'Content-Disposition': 'attachment; filename="anderzilla-account.json"'})
        if method == 'POST' and route == '/api/account/delete':
            fields(body, 'confirm password')
            service.delete_account(authenticated(), body.get('confirm'), body.get('password'))
            return response(status=204, headers={**cors, 'Set-Cookie': security.cookie(SESSION_COOKIE, '', 0, cfg['sameSite'])})
        if method == 'POST' and route == '/api/account/oauth/google/start':
            fields(body, 'ageConfirmed termsAccepted termsVersion privacyVersion lang marketingOptIn')
            if not cfg['google']:
                reject('google_unavailable', 'Google indisponível.', 503)
            return response(service.google_start(ctx['browserHash'], body), headers=cors)
        if method == 'POST' and route == '/api/account/oauth/google/callback':
            fields(body, 'code state')
            if not cfg['google']:
                reject('google_unavailable', 'Google indisponível.', 403 if not cfg['google'] else 503)
            return login_result(service.google_callback(ctx['browserHash'], body.get('code'), body.get('state')))
        if method == 'GET' and route == '/api/points/wallet':
            return response(service.wallet(authenticated()), headers=cors)
        if method == 'GET' and route == '/api/points/ledger':
            try:
                limit = int(query.get('limit', '25'))
            except ValueError:
                reject('invalid_limit', 'Limite inválido.')
            return response(service.ledger(authenticated(), query.get('cursor'), limit), headers=cors)
        if method == 'GET' and route == '/api/points/rewards':
            authenticated()
            return response({'items': [], 'nextCursor': None}, headers=cors)
        if method == 'GET' and route == '/api/points/missions':
            member = authenticated()
            return response(service.missions(member) if cfg['rewards'] else {'items': [], 'nextCursor': None}, headers=cors)
        if route.startswith('/api/points/') and method == 'POST':
            if not cfg['rewards']:
                reject('rewards_unavailable', 'Missões oficiais ainda indisponíveis.', 503)
            member = authenticated()
            if route == '/api/points/challenge':
                fields(body, 'missionId missionVersion')
                return response(service.challenge(ctx['browserHash'], member, body.get('missionId'), body.get('missionVersion')), headers=cors)
            if route == '/api/points/evidence':
                fields(body, 'challengeId answers interests')
                return response(service.evidence(ctx['browserHash'], member, body.get('challengeId'), body), headers=cors)
            if route in {'/api/points/claim', '/api/points/pending/claim'}:
                if route.endswith('/pending/claim'):
                    fields(body, 'pendingToken')
                    pending = body.get('pendingToken')
                    if not isinstance(pending, str) or not 32 <= len(pending) <= 128:
                        reject('invalid_token', 'Token inválido.')
                    cid = service.claim(member, ctx['browserHash'], headers.get('idempotency-key'), pending_token=pending)
                else:
                    fields(body, 'missionId missionVersion evidenceRef')
                    if not isinstance(body.get('evidenceRef'), str) or type(body.get('missionVersion')) is not int or not isinstance(body.get('missionId'), str):
                        reject('invalid_evidence', 'Missão/evidência inválidas.')
                    cid = service.claim(member, ctx['browserHash'], headers.get('idempotency-key'), evidence_ref=body['evidenceRef'], mission_id=body['missionId'], version=body['missionVersion'])
                return response({'completionId': cid}, headers=cors)
        reject('not_found', 'Rota não encontrada.', 404)
    except Rejected as error:
        return response({'error': {'code': error.code, 'message': str(error)}}, error.status, cors)
