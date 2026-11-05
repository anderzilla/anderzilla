"""Clerk session verification. No client metadata is an identity authority."""
import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from .core import reject


def settings():
    origins = {v.strip().rstrip('/') for v in os.environ.get('IDENTITY_ALLOWED_ORIGIN', '').split(',') if v.strip()}
    issuer = os.environ.get('CLERK_ISSUER', '').rstrip('/')
    secret = os.environ.get('CLERK_SECRET_KEY', '')
    public_key = os.environ.get('CLERK_JWT_KEY', '').replace('\\n', '\n')
    cpf_key = os.environ.get('IDENTITY_CPF_HMAC_KEY', '')
    webhook_key = os.environ.get('CLERK_WEBHOOK_SIGNING_SECRET', '')
    def valid_origin(value, allow_loopback=False):
        p = urlsplit(value)
        secure = p.scheme == 'https' or (allow_loopback and os.environ.get('IDENTITY_ENV') == 'homolog' and
                 p.scheme == 'http' and p.hostname in {'localhost', '127.0.0.1'})
        return secure and p.hostname and not p.username and not p.password and not p.query and not p.fragment and not p.path
    valid = bool(origins and all(valid_origin(v, True) for v in origins) and valid_origin(issuer)
                 and secret.startswith('sk_') and len(cpf_key) >= 32 and public_key.startswith('-----BEGIN PUBLIC KEY-----')
                 and webhook_key.startswith('whsec_'))
    valid = valid and os.environ.get('IDENTITY_ENV') in {'homolog', 'production'} and all(os.environ.get(k) for k in
                  ('IDENTITY_SQL_SERVER', 'IDENTITY_SQL_DATABASE', 'IDENTITY_SQL_USER', 'IDENTITY_SQL_PASSWORD'))
    if os.environ.get('IDENTITY_ENV') == 'production':
        valid = valid and secret.startswith('sk_live_') and not issuer.endswith('.clerk.accounts.dev')
    return {'ok': valid, 'origins': origins, 'issuer': issuer, 'secret': secret, 'publicKey': public_key,
            'cpfKey': cpf_key, 'webhookKey': webhook_key}


@dataclass(frozen=True)
class ClerkIdentity:
    subject: str
    session_id: str
    email: str
    authenticated_at: int


class ClerkGateway:
    """Fixed Clerk API origin; injected HTTP transport only for offline tests."""
    def __init__(self, cfg=None, transport=None, clock=None):
        self.cfg = cfg or settings()
        self.transport = transport
        self.clock = clock or (lambda: int(time.time()))

    def _request(self, method, path):
        import requests
        caller = self.transport or requests.request
        try:
            result = caller(method, 'https://api.clerk.com/v1' + path,
                            headers={'Authorization': 'Bearer ' + self.cfg['secret']}, timeout=(4, 10))
            if result.status_code == 404:
                reject('authentication_required', 'Entre novamente.', 401)
            if result.status_code not in (200, 201):
                reject('identity_unavailable', 'Não foi possível validar sua conta.', 503)
            return result.json()
        except requests.RequestException:
            reject('identity_unavailable', 'Não foi possível validar sua conta.', 503)

    def verify(self, authorization):
        import jwt
        if not isinstance(authorization, str) or not authorization.startswith('Bearer '):
            reject('authentication_required', 'Entre para continuar.', 401)
        token = authorization[7:]
        if not token or len(token) > 8192:
            reject('authentication_required', 'Sessão inválida.', 401)
        try:
            claims = jwt.decode(token, self.cfg['publicKey'], algorithms=['RS256'], issuer=self.cfg['issuer'],
                                options={'require': ['iss', 'sub', 'sid', 'exp', 'nbf', 'iat', 'azp'], 'verify_aud': False}, leeway=5)
            if claims['azp'] not in self.cfg['origins'] or claims.get('sts') not in (None, 'active') or claims.get('act'):
                raise ValueError('Not an authorized completed session')
            if not re.fullmatch(r'user_[A-Za-z0-9]+', claims['sub']) or not re.fullmatch(r'sess_[A-Za-z0-9]+', claims['sid']):
                raise ValueError('Not a user session')
        except (jwt.PyJWTError, ValueError, TypeError):
            reject('authentication_required', 'Sessão inválida ou expirada.', 401)
        # Immediate logout/bans are checked on every call, not until JWT expiry.
        session = self._request('GET', '/sessions/' + claims['sid'])
        if session.get('status') != 'active' or session.get('user_id') != claims['sub']:
            reject('authentication_required', 'Sessão encerrada.', 401)
        email = self.verified_email(claims['sub'])
        authenticated_at = int(session.get('created_at', 0)) // 1000
        age = claims.get('fva')
        if isinstance(age, list) and age and type(age[0]) is int and age[0] >= 0:
            authenticated_at = self.clock() - age[0] * 60
        return ClerkIdentity(claims['sub'], claims['sid'], email, authenticated_at)

    def verified_email(self, subject):
        user = self._request('GET', '/users/' + subject)
        if user.get('id') != subject or user.get('banned') or user.get('locked'):
            reject('account_unavailable', 'Conta indisponível.', 403)
        primary = next((v for v in user.get('email_addresses', []) if v.get('id') == user.get('primary_email_address_id')), None)
        if not primary or primary.get('verification', {}).get('status') != 'verified':
            reject('email_not_verified', 'Confirme seu e-mail.', 403)
        from .core import email_address
        return email_address(primary.get('email_address'))

    def delete_user(self, subject):
        return self._request('DELETE', '/users/' + subject)

    def revoke_session(self, session_id):
        return self._request('POST', '/sessions/' + session_id + '/revoke')

    def ban_user(self, subject):
        return self._request('POST', '/users/' + subject + '/ban')
