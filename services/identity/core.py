"""Visitor identity and rewards. All mutable decisions use one durable transaction."""
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import security
from .config import POLICY_VERSION

INTERESTS = {'games', 'consoles', 'celulares', 'ia', 'gadgets', 'curiosidades'}
SESSION_TTL = 30 * 86400


class Rejected(Exception):
    def __init__(self, code, message='Não foi possível concluir esta operação.', status=422):
        super().__init__(message)
        self.code, self.status = code, status


@dataclass(frozen=True)
class Principal:
    account_id: str
    session_id: str
    authenticated_at: int


def reject(code, message, status=422):
    raise Rejected(code, message, status)


def identifier():
    return str(uuid.uuid4())


def text(value, maximum=200, minimum=1):
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        reject('invalid_text', 'Texto inválido.')
    return value.strip()


def email_address(value):
    value = text(value, 320).lower()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value):
        reject('invalid_email', 'E-mail inválido.')
    return value


def preferences(values):
    if not isinstance(values, list) or len(values) > 6 or any(not isinstance(v, str) or v not in INTERESTS for v in values):
        reject('invalid_interests', 'Interesses inválidos.')
    return sorted(set(values))


def policies(data):
    if data.get('ageConfirmed') is not True or data.get('termsAccepted') is not True:
        reject('consent_required', 'Confirme idade mínima de 18 anos e os termos.')
    if data.get('termsVersion') != POLICY_VERSION or data.get('privacyVersion') != POLICY_VERSION:
        reject('policy_changed', 'Releia os termos e a política atuais.')
    if type(data.get('marketingOptIn', False)) is not bool:
        reject('invalid_marketing', 'Escolha de marketing inválida.')
    return {key: data.get(key, False) for key in ('ageConfirmed', 'termsAccepted', 'termsVersion', 'privacyVersion', 'marketingOptIn')}


class IdentityService:
    def __init__(self, store, email_sender=None, clock=None):
        self.store, self.email_sender = store, email_sender
        self.clock = clock or (lambda: int(time.time()))

    def email_ready(self):
        return bool(self.email_sender and self.email_sender.is_configured())

    def rate(self, scope, bucket, maximum=5, window=900):
        """Commit attempts before an operation that can fail/roll back."""
        bucket, now = security.token_hash(str(bucket)), self.clock()
        blocked = False
        with self.store.transaction() as db:
            row = db.execute('SELECT window_start,count FROM rate_limits WHERE scope=? AND bucket=?', (scope, bucket)).fetchone()
            if row is None:
                db.execute('INSERT INTO rate_limits(scope,bucket,window_start,count) VALUES(?,?,?,?)', (scope, bucket, now, 1))
            elif now - row['window_start'] >= window:
                db.execute('UPDATE rate_limits SET window_start=?,count=1 WHERE scope=? AND bucket=?', (now, scope, bucket))
            elif row['count'] >= maximum:
                blocked = True
            else:
                db.execute('UPDATE rate_limits SET count=count+1 WHERE scope=? AND bucket=?', (scope, bucket))
        if blocked:
            reject('rate_limited', 'Muitas tentativas. Aguarde e tente novamente.', 429)

    def _account(self, db, account_id, verified=False):
        account = db.execute('SELECT * FROM accounts WHERE id=?', (account_id,)).fetchone()
        if not account or account['state'] != 'active':
            reject('authentication_required', 'Conta indisponível.', 401)
        if verified and not account['email_verified']:
            reject('email_not_verified', 'Confirme seu e-mail antes de ganhar KP.', 403)
        return account

    def _consents(self, db, account_id, consent):
        for purpose, version, granted in [('terms', consent['termsVersion'], True), ('privacy', consent['privacyVersion'], True),
                                          ('marketing', POLICY_VERSION, consent.get('marketingOptIn', False))]:
            db.execute('INSERT INTO consents(id,account_id,purpose,version,granted,created_at) VALUES(?,?,?,?,?,?)',
                       (identifier(), account_id, purpose, version, int(granted), self.clock()))

    def _new_account(self, db, email, name, password_hash, verified, data):
        consent = policies(data)
        lang = data.get('lang', 'pt-BR')
        if lang not in {'pt-BR', 'en'}:
            reject('invalid_lang', 'Idioma inválido.')
        interests = preferences(data.get('interests', []))
        account_id, now = identifier(), self.clock()
        db.execute('INSERT INTO accounts(id,email,email_verified,display_name,password_hash,state,lang,timezone,marketing_opt_in,age_confirmed_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                   (account_id, email, int(verified), text(name, 80), password_hash, 'active', lang, 'America/Sao_Paulo', int(consent['marketingOptIn']), now, now, now))
        db.execute('INSERT INTO wallets(account_id,available,reserved) VALUES(?,?,?)', (account_id, 0, 0))
        db.execute('INSERT INTO preferences_bookmarks(account_id,interests,saved,opened) VALUES(?,?,?,?)',
                   (account_id, json.dumps(interests), '[]', '[]'))
        self._consents(db, account_id, consent)
        return account_id

    def _verification(self, db, account_id):
        raw, now = security.random_token(), self.clock()
        # Reissue invalidates prior links, including retries after failed SMTP delivery.
        db.execute('UPDATE email_verifications SET used_at=? WHERE account_id=? AND used_at IS NULL', (now, account_id))
        db.execute('INSERT INTO email_verifications(id,account_id,token_hash,expires_at,created_at) VALUES(?,?,?,?,?)',
                   (identifier(), account_id, security.token_hash(raw), now + 86400, now))
        return raw

    def _send(self, email, raw, lang):
        base = os.environ.get('IDENTITY_VERIFY_URL_BASE', '').strip()
        # URL and SMTP readiness are validated by the delivery adapter.
        try:
            self.email_sender.send_verification(email, base + ('&' if '?' in base else '?') + urlencode({'token': raw}), lang)
        except Exception:
            reject('email_unavailable', 'Envio indisponível. Entre e solicite novo link de confirmação.', 503)

    def register(self, data, bucket=''):
        if not self.email_ready():
            reject('email_unavailable', 'Cadastro por e-mail indisponível.', 503)
        consent = policies(data)
        email = email_address(data.get('email'))
        password = data.get('password')
        if not isinstance(password, str) or not 10 <= len(password) <= 128:
            reject('invalid_password', 'Senha deve ter 10–128 caracteres.')
        text(data.get('displayName'), 80)
        self.rate('register_global', 'global', 100)
        self.rate('register_browser', bucket, 5)
        self.rate('register_email', email, 3)
        encoded = security.hash_password(password)
        with self.store.transaction() as db:
            if db.execute('SELECT id FROM accounts WHERE email=?', (email,)).fetchone():
                reject('email_in_use', 'Use Entrar para acessar a conta ou reenviar a confirmação.', 409)
            account_id = self._new_account(db, email, data['displayName'], encoded, False, {**data, **consent})
            raw = self._verification(db, account_id)
        self._send(email, raw, data.get('lang', 'pt-BR'))
        return {'accountId': account_id, 'message': 'verify_email_sent'}

    def resend(self, principal):
        if not self.email_ready():
            reject('email_unavailable', 'Envio indisponível.', 503)
        self.rate('resend', principal.account_id, 3)
        with self.store.transaction() as db:
            account = self._account(db, principal.account_id)
            if account['email_verified']:
                return {'verified': True}
            raw = self._verification(db, principal.account_id)
        self._send(account['email'], raw, account['lang'])
        return {'message': 'verify_email_sent'}

    def verify_email(self, raw_token, bucket=''):
        self.rate('verify_global', 'global', 300)
        self.rate('verify_browser', bucket, 15)
        token = security.token_hash(text(raw_token, 200, 32))
        with self.store.transaction() as db:
            row = db.execute('SELECT * FROM email_verifications WHERE token_hash=?', (token,)).fetchone()
            if not row or row['used_at'] is not None or row['expires_at'] <= self.clock():
                reject('invalid_token', 'Link inválido, utilizado ou expirado.', 410)
            self._account(db, row['account_id'])
            db.execute('UPDATE email_verifications SET used_at=? WHERE id=?', (self.clock(), row['id']))
            db.execute('UPDATE accounts SET email_verified=1,updated_at=? WHERE id=?', (self.clock(), row['account_id']))
            return {'verified': True}

    def _session(self, db, account_id):
        raw, sid, now = security.random_token(), identifier(), self.clock()
        db.execute('INSERT INTO sessions(id,account_id,token_hash,created_at,expires_at) VALUES(?,?,?,?,?)',
                   (sid, account_id, security.token_hash(raw), now, now + SESSION_TTL))
        return {'accountId': account_id, 'sessionToken': raw, 'expiresAt': now + SESSION_TTL}

    def login(self, email, password, bucket=''):
        email = email_address(email)
        self.rate('login_global', 'global', 500)
        self.rate('login_email', email, 8)
        self.rate('login_browser', bucket, 20)
        with self.store.transaction() as db:
            account = db.execute('SELECT * FROM accounts WHERE email=?', (email,)).fetchone()
        if not account or account['state'] != 'active' or not security.verify_password(account['password_hash'], password):
            reject('invalid_credentials', 'Credenciais inválidas.', 401)
        with self.store.transaction() as db:
            current = self._account(db, account['id'])
            if current['password_hash'] != account['password_hash']:
                reject('invalid_credentials', 'Credenciais inválidas.', 401)
            return self._session(db, account['id'])

    def authenticate(self, token):
        if not isinstance(token, str) or len(token) > 200:
            return None
        with self.store.transaction() as db:
            row = db.execute('SELECT s.id,s.account_id,s.created_at,s.expires_at,s.revoked_at,a.state FROM sessions s JOIN accounts a ON a.id=s.account_id WHERE token_hash=?',
                             (security.token_hash(token),)).fetchone()
            if not row or row['revoked_at'] is not None or row['expires_at'] <= self.clock() or row['state'] != 'active':
                return None
            return Principal(row['account_id'], row['id'], row['created_at'])

    def logout(self, token):
        with self.store.transaction() as db:
            db.execute('UPDATE sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL', (self.clock(), security.token_hash(token)))

    def logout_all(self, principal):
        with self.store.transaction() as db:
            db.execute('UPDATE sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL', (self.clock(), principal.account_id))

    def _me(self, db, principal):
        account = self._account(db, principal.account_id)
        pref = db.execute('SELECT interests,saved,opened FROM preferences_bookmarks WHERE account_id=?', (principal.account_id,)).fetchone()
        wallet = db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (principal.account_id,)).fetchone()
        return {'account': {'id': account['id'], 'email': account['email'], 'emailVerified': bool(account['email_verified']),
                            'displayName': account['display_name'], 'hasPassword': bool(account['password_hash']),
                            'lang': account['lang'], 'timezone': account['timezone'], 'marketingOptIn': bool(account['marketing_opt_in']),
                            **{key: json.loads(pref[key]) for key in ('interests', 'saved', 'opened')}},
                'wallet': {**wallet, 'unit': 'KP'}}

    def me(self, principal):
        with self.store.transaction() as db:
            return self._me(db, principal)

    def update_profile(self, principal, patch):
        if not isinstance(patch, dict) or set(patch) - {'displayName', 'lang', 'timezone', 'marketingOptIn', 'interests', 'saved', 'opened'}:
            reject('invalid_fields', 'Campos desconhecidos.')
        values = {}
        if 'displayName' in patch:
            values['display_name'] = text(patch['displayName'], 80)
        if 'lang' in patch:
            if patch['lang'] not in {'pt-BR', 'en'}:
                reject('invalid_lang', 'Idioma inválido.')
            values['lang'] = patch['lang']
        if 'timezone' in patch:
            value = text(patch['timezone'], 64)
            try:
                ZoneInfo(value)
            except (ValueError, ZoneInfoNotFoundError):
                reject('invalid_timezone', 'Fuso inválido.')
            values['timezone'] = value
        if 'marketingOptIn' in patch:
            if type(patch['marketingOptIn']) is not bool:
                reject('invalid_marketing', 'Escolha inválida.')
            values['marketing_opt_in'] = int(patch['marketingOptIn'])
        with self.store.transaction() as db:
            self._account(db, principal.account_id)
            for column, value in values.items():
                db.execute(f'UPDATE accounts SET {column}=?,updated_at=? WHERE id=?', (value, self.clock(), principal.account_id))
            if 'marketingOptIn' in patch:
                db.execute('INSERT INTO consents(id,account_id,purpose,version,granted,created_at) VALUES(?,?,?,?,?,?)',
                           (identifier(), principal.account_id, 'marketing', POLICY_VERSION, values['marketing_opt_in'], self.clock()))
            for field in ('interests', 'saved', 'opened'):
                if field not in patch:
                    continue
                value = preferences(patch[field]) if field == 'interests' else patch[field]
                if not isinstance(value, list) or len(value) > 1000 or any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', v) for v in value):
                    reject('invalid_preferences', 'Lista de preferências inválida.')
                db.execute(f'UPDATE preferences_bookmarks SET {field}=? WHERE account_id=?', (json.dumps(list(dict.fromkeys(value))), principal.account_id))
            return self._me(db, principal)

    def export_data(self, principal):
        with self.store.transaction() as db:
            result = self._me(db, principal)
            result['ledger'] = db.execute('SELECT id,available_delta,reserved_delta,reason,reference_id,created_at FROM ledger WHERE account_id=?', (principal.account_id,)).fetchall()
            result['consents'] = db.execute('SELECT purpose,version,granted,created_at FROM consents WHERE account_id=?', (principal.account_id,)).fetchall()
            result['completions'] = db.execute('SELECT mission_id,mission_version,created_at FROM completions WHERE account_id=?', (principal.account_id,)).fetchall()
            return result

    def delete_account(self, principal, confirm, password=None):
        if confirm != 'DELETE':
            reject('confirmation_required', 'Confirme com DELETE.')
        self.rate('delete', principal.account_id, 5)
        with self.store.transaction() as db:
            account = self._account(db, principal.account_id)
        if account['password_hash']:
            if not security.verify_password(account['password_hash'], password):
                reject('invalid_credentials', 'Confirme a senha atual.', 401)
        elif self.clock() - principal.authenticated_at > 300:
            reject('reauth_required', 'Entre novamente com Google para excluir a conta.', 403)
        with self.store.transaction() as db:
            self._account(db, principal.account_id)
            db.execute("UPDATE accounts SET state='deleted',email=?,display_name='Deleted',password_hash=NULL,marketing_opt_in=0,updated_at=? WHERE id=?",
                       (f'deleted-{principal.account_id}@deleted.invalid', self.clock(), principal.account_id))
            db.execute('UPDATE sessions SET revoked_at=? WHERE account_id=?', (self.clock(), principal.account_id))
            db.execute('DELETE FROM email_verifications WHERE account_id=?', (principal.account_id,))
            db.execute('DELETE FROM oauth_identities WHERE account_id=?', (principal.account_id,))
            db.execute("UPDATE preferences_bookmarks SET interests='[]',saved='[]',opened='[]' WHERE account_id=?", (principal.account_id,))
            db.execute("UPDATE mission_evidence SET payload='{}' WHERE account_id=?", (principal.account_id,))

    def wallet(self, principal):
        with self.store.transaction() as db:
            self._account(db, principal.account_id, True)
            return {**db.execute('SELECT available,reserved FROM wallets WHERE account_id=?', (principal.account_id,)).fetchone(), 'unit': 'KP'}

    def ledger(self, principal, cursor=None, limit=25):
        if type(limit) is not int or not 1 <= limit <= 100:
            reject('invalid_limit', 'Limite de 1–100.')
        params, where = [principal.account_id], ''
        if cursor:
            try:
                timestamp, row_id = cursor.split(':', 1)
                timestamp = int(timestamp)
                uuid.UUID(row_id)
            except (ValueError, AttributeError):
                reject('invalid_cursor', 'Cursor inválido.')
            where = ' AND (created_at<? OR (created_at=? AND id<?))'
            params.extend([timestamp, timestamp, row_id])
        with self.store.transaction() as db:
            self._account(db, principal.account_id, True)
            rows = db.page('SELECT id,available_delta,reserved_delta,reason,reference_id,created_at FROM ledger WHERE account_id=?' + where + ' ORDER BY created_at DESC,id DESC', params, limit + 1).fetchall()
        items = rows[:limit]
        return {'items': items, 'nextCursor': f"{items[-1]['created_at']}:{items[-1]['id']}" if len(rows) > limit else None}

    def google_start(self, browser_hash, data):
        consent = policies(data)
        consent['lang'] = data.get('lang', 'pt-BR')
        self.rate('oauth_global', 'global', 300)
        self.rate('oauth_browser', browser_hash, 10)
        state, nonce, verifier = security.random_token(), security.random_token(), security.random_token()
        with self.store.transaction() as db:
            db.execute('DELETE FROM oauth_nonces WHERE expires_at<=?', (self.clock(),))
            db.execute('INSERT INTO oauth_nonces(state,nonce,verifier,browser_hash,consent_json,expires_at) VALUES(?,?,?,?,?,?)',
                       (state, nonce, verifier, browser_hash, json.dumps(consent), self.clock() + 600))
        params = {'response_type': 'code', 'client_id': os.environ['IDENTITY_GOOGLE_CLIENT_ID'],
                  'redirect_uri': os.environ['IDENTITY_GOOGLE_REDIRECT_URI'], 'scope': 'openid email profile',
                  'state': state, 'nonce': nonce, 'code_challenge': security.pkce_challenge(verifier), 'code_challenge_method': 'S256'}
        return {'url': 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)}

    def google_callback(self, browser_hash, code, state):
        code, state = text(code, 4096), text(state, 128)
        self.rate('oauth_callback', browser_hash, 15)
        with self.store.transaction() as db:
            row = db.execute('SELECT * FROM oauth_nonces WHERE state=?', (state,)).fetchone()
            if not row or row['expires_at'] <= self.clock() or not security.equal(row['browser_hash'], browser_hash):
                reject('invalid_state', 'Autorização inválida ou expirada.')
            db.execute('DELETE FROM oauth_nonces WHERE state=?', (state,))
        # No reusable direct-ID-token route. State is consumed before remote exchange.
        try:
            import requests
            response = requests.post('https://oauth2.googleapis.com/token', data={
                'code': code, 'client_id': os.environ['IDENTITY_GOOGLE_CLIENT_ID'],
                'client_secret': os.environ['IDENTITY_GOOGLE_CLIENT_SECRET'], 'redirect_uri': os.environ['IDENTITY_GOOGLE_REDIRECT_URI'],
                'grant_type': 'authorization_code', 'code_verifier': row['verifier']}, timeout=10)
            if response.status_code != 200:
                raise ValueError('Exchange rejected')
            claims = security.verify_google_id_token(response.json().get('id_token'), os.environ['IDENTITY_GOOGLE_CLIENT_ID'], row['nonce'])
            email = email_address(claims.get('email'))
            subject = text(claims.get('sub'), 256)
        except Exception:
            reject('google_verification_failed', 'Não foi possível validar a resposta Google. Inicie novamente.', 401)
        with self.store.transaction() as db:
            identity = db.execute("SELECT account_id FROM oauth_identities WHERE provider='google' AND subject=?", (subject,)).fetchone()
            if identity:
                account_id = identity['account_id']
                self._account(db, account_id, True)
            else:
                if db.execute('SELECT id FROM accounts WHERE email=?', (email,)).fetchone():
                    reject('account_link_required', 'Já existe cadastro por e-mail. Use sua senha; vínculo de provedores requer confirmação separada.', 409)
                account_id = self._new_account(db, email, str(claims.get('name') or email.split('@')[0])[:80], None, True, json.loads(row['consent_json']))
                db.execute('INSERT INTO oauth_identities(provider,subject,account_id,created_at) VALUES(?,?,?,?)', ('google', subject, account_id, self.clock()))
            return self._session(db, account_id)

    def _mission(self, db, mission_id, version):
        row = db.execute('SELECT * FROM missions WHERE id=? AND version=?', (mission_id, version)).fetchone()
        if not row or not row['active'] or row['starts_at'] > self.clock() or row['ends_at'] <= self.clock() or not row['coverage_reference'].strip():
            reject('mission_unavailable', 'Missão indisponível.', 404)
        return row

    def _definition(self, mission):
        try:
            data = json.loads(mission['definition_json'])
            if not isinstance(data, dict):
                raise ValueError()
            if mission['verifier'] == 'quiz':
                questions = data['questions']
                if not isinstance(questions, list) or not 1 <= len(questions) <= 10:
                    raise ValueError()
                ids = set()
                for q in questions:
                    if q['id'] in ids or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', q['id']):
                        raise ValueError()
                    ids.add(q['id'])
                    text(q['promptPT'], 1000); text(q['promptEN'], 1000)
                    options = q['options']
                    if not isinstance(options, list) or not 2 <= len(options) <= 6 or len({o['id'] for o in options}) != len(options):
                        raise ValueError()
                    for o in options:
                        text(o['id'], 64); text(o['textPT'], 500); text(o['textEN'], 500)
                    if q['correctOption'] not in {o['id'] for o in options}:
                        raise ValueError()
            return data
        except (KeyError, TypeError, ValueError):
            reject('mission_unavailable', 'Definição de missão indisponível.', 503)

    def missions(self):
        with self.store.transaction() as db:
            rows = db.execute("SELECT id,version,award,starts_at,ends_at,verifier FROM missions WHERE active=1 AND starts_at<=? AND ends_at>? AND coverage_reference<>'' ORDER BY id,version", (self.clock(), self.clock())).fetchall()
        return {'items': [{'id': r['id'], 'version': r['version'], 'awardKP': r['award'], 'kind': r['verifier'], 'startsAt': r['starts_at'], 'endsAt': r['ends_at']} for r in rows], 'nextCursor': None}

    def challenge(self, browser_hash, principal, mission_id, version):
        if not isinstance(mission_id, str) or type(version) is not int or version < 1:
            reject('invalid_mission', 'Missão inválida.')
        self.rate('challenge', browser_hash, 20)
        with self.store.transaction() as db:
            mission = self._mission(db, mission_id, version)
            definition = self._definition(mission)
            challenge_id, expires = identifier(), self.clock() + 1800
            db.execute('INSERT INTO challenges(id,browser_hash,account_id,mission_id,mission_version,definition_hash,expires_at) VALUES(?,?,?,?,?,?,?)',
                       (challenge_id, browser_hash, principal.account_id if principal else None, mission_id, version, security.token_hash(mission['definition_json']), expires))
            return {'challengeId': challenge_id, 'kind': mission['verifier'], 'expiresAt': expires,
                    'questions': [{k: q[k] for k in ('id', 'promptPT', 'promptEN', 'options')} for q in definition.get('questions', [])]}

    def _answers(self, mission, payload):
        definition = self._definition(mission)
        if mission['verifier'] == 'interests':
            values = preferences(payload.get('interests', []))
            if len(values) < 3:
                reject('evidence_invalid', 'Escolha pelo menos três interesses.')
            return {'interests': values}
        answers = payload.get('answers')
        questions = definition['questions']
        if not isinstance(answers, dict) or set(answers) != {q['id'] for q in questions} or any(answers[q['id']] != q['correctOption'] for q in questions):
            reject('evidence_invalid', 'Respostas incorretas. Reveja a fonte e tente novamente.')
        return {'answers': answers}

    def evidence(self, browser_hash, principal, challenge_id, payload):
        self.rate('evidence', browser_hash, 15)
        with self.store.transaction() as db:
            challenge = db.execute('SELECT * FROM challenges WHERE id=?', (text(challenge_id, 64),)).fetchone()
            if not challenge or not security.equal(challenge['browser_hash'], browser_hash) or challenge['expires_at'] <= self.clock():
                reject('challenge_expired', 'Desafio inválido ou expirado.', 410)
            if challenge['account_id'] and (not principal or challenge['account_id'] != principal.account_id):
                reject('evidence_not_owned', 'Desafio pertence a outra conta.', 403)
            if challenge['used_at'] is not None:
                reject('challenge_used', 'Desafio já concluído.', 409)
            mission = self._mission(db, challenge['mission_id'], challenge['mission_version'])
            if not security.equal(challenge['definition_hash'], security.token_hash(mission['definition_json'])):
                reject('mission_changed', 'A missão mudou. Inicie outro desafio.', 409)
            validated = self._answers(mission, payload)
            evidence_id, pending_token = identifier(), security.random_token()
            account_id = principal.account_id if principal else None
            db.execute('UPDATE challenges SET used_at=? WHERE id=?', (self.clock(), challenge_id))
            db.execute('INSERT INTO mission_evidence(id,challenge_id,browser_hash,account_id,mission_id,mission_version,payload,created_at) VALUES(?,?,?,?,?,?,?,?)',
                       (evidence_id, challenge_id, browser_hash, account_id, mission['id'], mission['version'], json.dumps(validated), self.clock()))
            db.execute('INSERT INTO pending_rewards(id,token_hash,browser_hash,evidence_id,expires_at) VALUES(?,?,?,?,?)',
                       (identifier(), security.token_hash(pending_token), browser_hash, evidence_id, challenge['expires_at']))
            return {'evidenceRef': evidence_id, 'pendingToken': pending_token, 'awardPreview': mission['award'], 'expiresAt': challenge['expires_at']}

    def claim(self, principal, browser_hash, key, evidence_ref=None, pending_token=None, mission_id=None, version=None):
        key = text(key, 128, 8)
        if not evidence_ref and not pending_token:
            reject('invalid_evidence', 'Informe uma evidência.')
        digest = security.token_hash(json.dumps([evidence_ref, security.token_hash(pending_token) if pending_token else None, mission_id, version, browser_hash], separators=(',', ':')))
        with self.store.transaction() as db:
            self._account(db, principal.account_id, True)
            replay = db.execute('SELECT payload_hash,result_id FROM requests WHERE account_id=? AND request_key=?', (principal.account_id, key)).fetchone()
            if replay:
                if not security.equal(replay['payload_hash'], digest):
                    reject('idempotency_conflict', 'Chave já usada para outra operação.', 409)
                return replay['result_id']
            pending = None
            if pending_token:
                pending = db.execute('SELECT * FROM pending_rewards WHERE token_hash=?', (security.token_hash(pending_token),)).fetchone()
                if not pending or not security.equal(pending['browser_hash'], browser_hash) or pending['expires_at'] <= self.clock():
                    reject('pending_expired', 'Recompensa pendente indisponível.', 410)
                if pending['claimed_at'] is not None:
                    reject('pending_claimed', 'Recompensa já reivindicada.', 409)
                evidence_ref = pending['evidence_id']
            evidence = db.execute('SELECT * FROM mission_evidence WHERE id=?', (evidence_ref,)).fetchone()
            if not evidence or not security.equal(evidence['browser_hash'], browser_hash) or (evidence['account_id'] is not None and evidence['account_id'] != principal.account_id):
                reject('evidence_not_owned', 'Evidência indisponível para esta conta.', 403)
            if not pending and evidence['account_id'] != principal.account_id:
                reject('pending_required', 'Conclua o vínculo da recompensa pendente.', 403)
            if mission_id is not None and (mission_id != evidence['mission_id'] or version != evidence['mission_version']):
                reject('evidence_mismatch', 'Evidência não corresponde à missão.')
            challenge = db.execute('SELECT definition_hash,expires_at FROM challenges WHERE id=?', (evidence['challenge_id'],)).fetchone()
            mission = self._mission(db, evidence['mission_id'], evidence['mission_version'])
            if challenge['expires_at'] <= self.clock() or not security.equal(challenge['definition_hash'], security.token_hash(mission['definition_json'])):
                reject('evidence_expired', 'Evidência expirada ou regra alterada.', 410)
            self._answers(mission, json.loads(evidence['payload']))
            completed = db.execute('SELECT id FROM completions WHERE account_id=? AND mission_id=? AND mission_version=?',
                                   (principal.account_id, mission['id'], mission['version'])).fetchone()
            cid = completed['id'] if completed else identifier()
            if not completed:
                cycle_start = self.clock() - self.clock() % (28 * 86400)
                total = db.execute('SELECT COALESCE(SUM(available_delta),0) AS amount FROM ledger WHERE available_delta>0 AND created_at>=?', (cycle_start,)).fetchone()['amount']
                own = db.execute('SELECT COALESCE(SUM(available_delta),0) AS amount FROM ledger WHERE account_id=? AND available_delta>0 AND created_at>=?', (principal.account_id, cycle_start)).fetchone()['amount']
                budget = int(os.environ.get('IDENTITY_KP_CYCLE_BUDGET', '0'))
                if total + mission['award'] > budget or own + mission['award'] > 500:
                    reject('reward_capacity', 'Emissão indisponível neste ciclo; nenhum crédito foi realizado.', 409)
                db.execute('INSERT INTO completions(id,account_id,mission_id,mission_version,evidence_ref,created_at) VALUES(?,?,?,?,?,?)',
                           (cid, principal.account_id, mission['id'], mission['version'], evidence_ref, self.clock()))
                db.execute('UPDATE wallets SET available=available+? WHERE account_id=?', (mission['award'], principal.account_id))
                db.execute('INSERT INTO ledger(id,account_id,available_delta,reserved_delta,reason,reference_id,created_at) VALUES(?,?,?,?,?,?,?)',
                           (identifier(), principal.account_id, mission['award'], 0, 'mission', cid, self.clock()))
            db.execute('UPDATE mission_evidence SET account_id=? WHERE id=?', (principal.account_id, evidence_ref))
            if pending:
                db.execute('UPDATE pending_rewards SET claimed_at=?,claimed_by=? WHERE id=?', (self.clock(), principal.account_id, pending['id']))
            db.execute('INSERT INTO requests(account_id,request_key,payload_hash,result_id) VALUES(?,?,?,?)', (principal.account_id, key, digest, cid))
            return cid
