"""Private AnderZilla adult registration and access state for Clerk users."""
import datetime as dt
import json
import time
from zoneinfo import ZoneInfo

from .core import IdentityService, Principal, email_address, identifier, reject, text
from . import security
from .cpf import fingerprint, normalize_cpf

POLICY_VERSION = '2026-11-04'


def birth_date(value, now):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError()
        born = dt.date.fromisoformat(value)
        today = dt.datetime.fromtimestamp(now, ZoneInfo('America/Sao_Paulo')).date()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if age < 0 or age > 120:
            raise ValueError()
        return born.isoformat(), age
    except ValueError:
        reject('invalid_birth_date', 'Informe uma data de nascimento válida.')


def accepted(data):
    if data.get('termsAccepted') is not True:
        reject('consent_required', 'Leia e aceite os termos.')
    if data.get('termsVersion') != POLICY_VERSION or data.get('privacyVersion') != POLICY_VERSION:
        reject('policy_changed', 'Releia os termos e a privacidade atuais.')
    if type(data.get('marketingOptIn', False)) is not bool:
        reject('invalid_marketing', 'Escolha de marketing inválida.')


def iso(timestamp):
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).isoformat().replace('+00:00', 'Z')


class ClerkAccountService:
    def __init__(self, store, cfg, clock=None):
        self.store, self.cfg = store, cfg
        self.clock = clock or (lambda: int(time.time()))
        self.domain = IdentityService(store, clock=self.clock, policy_version=POLICY_VERSION)

    def _record(self, db, identity, required=True, allow_deleted=False):
        row = db.execute('SELECT a.*,p.cpf_fingerprint,p.cpf_last_two,p.birth_date '
                         'FROM managed_identities i JOIN accounts a ON a.id=i.account_id '
                         'LEFT JOIN managed_profiles p ON p.account_id=a.id WHERE i.subject=?', (identity.subject,)).fetchone()
        if not row:
            if required:
                reject('onboarding_required', 'Complete seu cadastro.', 403)
            return None
        if row['state'] != 'active' and not (allow_deleted and row['state'] == 'deleted'):
            reject('account_unavailable', 'Conta indisponível.', 403)
        if row['state'] == 'active' and row['email'] != identity.email:
            self._sync_email(db, row, identity.email)
            row['email'] = identity.email
        return row

    def _sync_email(self, db, row, verified_email):
        collision = db.execute('SELECT id FROM accounts WHERE email=? AND id<>?', (verified_email, row['id'])).fetchone()
        blocked = db.execute('SELECT cpf_fingerprint FROM managed_bans WHERE email_fingerprint=?',
                             (fingerprint(verified_email, self.cfg['cpfKey'], 'email'),)).fetchone()
        if collision or blocked:
            reject('account_link_required', 'A alteração de e-mail precisa de atendimento.', 409)
        db.execute('UPDATE accounts SET email=?,updated_at=? WHERE id=?', (verified_email, self.clock(), row['id']))

    def _principal(self, row, identity):
        return Principal(row['id'], identity.session_id, identity.authenticated_at)

    def _sync_collections_into_me(self, db, account_id, result):
        state = db.execute('SELECT interests_version,exploration_generation,backfilled_at FROM member_collection_state WHERE account_id=?', (account_id,)).fetchone()
        if state and state['backfilled_at'] is not None:
            interests = [r['category_id'] for r in db.execute('SELECT category_id FROM member_interests WHERE account_id=? ORDER BY category_id', (account_id,)).fetchall()]
            saved = [r['discovery_id'] for r in db.page('SELECT discovery_id FROM member_bookmarks WHERE account_id=? ORDER BY saved_at DESC, discovery_id DESC', (account_id,), 1000).fetchall()]
            opened = [r['discovery_id'] for r in db.page('SELECT discovery_id FROM member_exploration WHERE account_id=? ORDER BY last_opened_at DESC, discovery_id DESC', (account_id,), 1000).fetchall()]
            result['account']['interests'] = interests
            result['account']['saved'] = saved
            result['account']['opened'] = opened
            result['account']['interestsVersion'] = state['interests_version']
            result['account']['explorationGeneration'] = state['exploration_generation']
        else:
            result['account']['interestsVersion'] = 1
            result['account']['explorationGeneration'] = 1

    def me(self, identity):
        with self.store.transaction() as db:
            row = self._record(db, identity, required=False)
            if row is None or not row['cpf_fingerprint'] or not row['birth_date']:
                return {'account': None, 'onboardingRequired': True}
            result = self.domain._me(db, self._principal(row, identity))
            self._sync_collections_into_me(db, row['id'], result)
            result['account'].update({'provider': 'clerk', 'isMinor': False,
                                      'guardianLinked': False,
                                      'cpfMasked': '***.***.***-' + (row['cpf_last_two'] or '**')})
            result['onboardingRequired'] = False
            return result

    def onboard(self, identity, data):
        accepted(data)
        cpf = normalize_cpf(data.get('cpf'))
        cpf_hash = fingerprint(cpf, self.cfg['cpfKey'])
        born, age = birth_date(data.get('birthDate'), self.clock())
        name = text(data.get('displayName'), 80, 2)
        lang = data.get('lang', 'pt-BR')
        if lang not in {'pt-BR', 'en'}:
            reject('invalid_lang', 'Idioma inválido.')
        self.domain.rate('managed_onboard', identity.subject, 5)
        with self.store.transaction() as db:
            existing = self._record(db, identity, required=False)
            if existing is not None:
                # Network retry may return the already completed account, never reassign CPF.
                if existing['cpf_fingerprint'] != cpf_hash:
                    reject('registration_conflict', 'O cadastro já foi concluído.', 409)
                return {'accountId': existing['id']}
            blocked = db.execute('SELECT cpf_fingerprint FROM managed_bans WHERE cpf_fingerprint=? OR email_fingerprint=?',
                                 (cpf_hash, fingerprint(identity.email, self.cfg['cpfKey'], 'email'))).fetchone()
            if blocked:
                reject('registration_unavailable', 'Não foi possível concluir o cadastro.', 403)
            if db.execute('SELECT account_id FROM managed_profiles WHERE cpf_fingerprint=?', (cpf_hash,)).fetchone():
                reject('registration_conflict', 'Não foi possível concluir com os dados informados.', 409)
            if db.execute('SELECT id FROM accounts WHERE email=?', (identity.email,)).fetchone():
                # Never auto-link legacy accounts merely because the emails match.
                reject('account_link_required', 'Esta conta precisa de migração assistida.', 409)
            if age < 18:
                reject('minor_registration_unavailable', 'O cadastro está disponível apenas para maiores de 18 anos.', 403)
            account_id, now = identifier(), self.clock()
            db.execute('INSERT INTO accounts(id,email,email_verified,display_name,password_hash,state,lang,timezone,marketing_opt_in,age_confirmed_at,created_at,updated_at,avatar_url) '
                       'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', (account_id, identity.email, 1, name, None, 'active', lang, 'America/Sao_Paulo', int(data.get('marketingOptIn', False)), now, now, now, None))
            db.execute('INSERT INTO managed_identities(subject,account_id,created_at) VALUES(?,?,?)', (identity.subject, account_id, now))
            db.execute('INSERT INTO managed_profiles(account_id,cpf_fingerprint,cpf_last_two,birth_date) VALUES(?,?,?,?)',
                       (account_id, cpf_hash, cpf[-2:], born))
            db.execute('INSERT INTO wallets(account_id,available,reserved) VALUES(?,?,?)', (account_id, 0, 0))
            db.execute("INSERT INTO preferences_bookmarks(account_id,interests,saved,opened) VALUES(?,?,?,?)", (account_id, '[]', '[]', '[]'))
            db.execute('INSERT INTO member_collection_state(account_id,interests_version,exploration_generation,exploration_paused,backfilled_at,updated_at) VALUES(?,?,?,?,?,?)',
                       (account_id, 1, 1, 0, now, now))
            for purpose, granted in [('terms', True), ('privacy', True), ('marketing', data.get('marketingOptIn', False))]:
                db.execute('INSERT INTO consents(id,account_id,purpose,version,granted,created_at) VALUES(?,?,?,?,?,?)',
                           (identifier(), account_id, purpose, POLICY_VERSION, int(granted), now))
            return {'accountId': account_id}

    def profile(self, identity, data):
        # Profile endpoint only updates account profile fields; full-list replacement of interests/saved/opened
        # is retired in favor of /api/member/interests, /api/member/backpack and /api/member/exploration.
        allowed = {'displayName', 'lang', 'timezone', 'marketingOptIn', 'avatarUrl'}
        if not isinstance(data, dict) or set(data) - allowed:
            reject('invalid_fields', 'Campos desconhecidos.')
        with self.store.transaction() as db:
            row = self._record(db, identity)
            if not row['cpf_fingerprint'] or not row['birth_date']:
                reject('onboarding_required', 'Complete seu cadastro.', 403)
            principal = self._principal(row, identity)
        self.domain.update_profile(principal, data)
        return self.me(identity)

    def export(self, identity):
        with self.store.transaction() as db:
            row = self._record(db, identity)
            if not row['cpf_fingerprint'] or not row['birth_date']:
                reject('onboarding_required', 'Complete seu cadastro.', 403)
            principal = self._principal(row, identity)
        result = self.domain.export_data(principal)
        with self.store.transaction() as db:
            self._sync_collections_into_me(db, row['id'], result)
            result['interests'] = [
                {'categoryId': r['category_id'], 'createdAt': iso(r['created_at'])}
                for r in db.execute('SELECT category_id,created_at FROM member_interests WHERE account_id=? ORDER BY category_id', (row['id'],)).fetchall()
            ]
            result['backpack'] = [
                {'discoveryId': r['discovery_id'], 'savedAt': iso(r['saved_at'])}
                for r in db.execute('SELECT discovery_id,saved_at FROM member_bookmarks WHERE account_id=? ORDER BY saved_at DESC, discovery_id DESC', (row['id'],)).fetchall()
            ]
            result['exploration'] = [
                {'discoveryId': r['discovery_id'], 'firstOpenedAt': iso(r['first_opened_at']), 'lastOpenedAt': iso(r['last_opened_at']), 'openCount': r['open_count']}
                for r in db.execute('SELECT discovery_id,first_opened_at,last_opened_at,open_count FROM member_exploration WHERE account_id=? ORDER BY last_opened_at DESC, discovery_id DESC', (row['id'],)).fetchall()
            ]
            result['missionReceipts'] = [
                {'receiptId': r['id'], 'missionId': r['mission_id'], 'missionVersion': r['mission_version'], 'occurrenceKey': r['occurrence_key'], 'awardKP': r['award_kp'], 'supportRef': r['support_ref'], 'completedAt': iso(r['created_at'])}
                for r in db.execute('SELECT id,mission_id,mission_version,occurrence_key,award_kp,support_ref,created_at FROM mission_receipts WHERE account_id=? ORDER BY created_at DESC', (row['id'],)).fetchall()
            ]
            result['pendingClaims'] = [
                {'pendingId': r['id'], 'missionId': r['mission_id'], 'missionVersion': r['mission_version'], 'awardKP': r['award_kp'], 'reservationState': r['reservation_state'], 'expiresAt': iso(r['expires_at']), 'createdAt': iso(r['created_at'])}
                for r in db.execute("SELECT id,mission_id,mission_version,award_kp,reservation_state,expires_at,created_at FROM mission_pending_claims WHERE account_id=? AND reservation_state='reserved'", (row['id'],)).fetchall()
            ]
        result['registration'] = {'birthDate': row['birth_date'], 'cpfMasked': '***.***.***-' + row['cpf_last_two'],
                                  'isMinor': False}
        return result

    def delete(self, identity, confirm):
        if confirm != 'DELETE':
            reject('confirmation_required', 'Confirme a exclusão.')
        if self.clock() - identity.authenticated_at > 300:
            reject('reauth_required', 'Entre novamente para excluir sua conta.', 403)
        with self.store.transaction() as db:
            row = self._record(db, identity, allow_deleted=True)
            account_id = row['id']
            self._erase(db, row, identity.subject)
            return {'accountId': account_id}

    def _erase(self, db, row, subject, remote_completed=False):
        account_id, now = row['id'], self.clock()
        # Release any active campaign reservations held by pending claims of this account before deleting!
        active_pending = db.execute(
            "SELECT id,campaign_id,award_kp FROM mission_pending_claims WHERE account_id=? AND reservation_state='reserved'",
            (account_id,),
        ).fetchall()
        for pend in active_pending:
            cur = db.execute(
                "UPDATE mission_pending_claims SET reservation_state='released',released_at=? WHERE id=? AND reservation_state='reserved'",
                (now, pend['id']),
            )
            if getattr(cur, 'rowcount', 1) == 1:
                db.execute(
                    'UPDATE mission_campaigns SET reserved_kp = CASE WHEN reserved_kp >= ? THEN reserved_kp - ? ELSE 0 END WHERE id=?',
                    (pend['award_kp'], pend['award_kp'], pend['campaign_id']),
                )
        # Ban fingerprints and append-only ledger/completions remain solely for audit/preventing prohibited accounts.
        db.execute("UPDATE accounts SET state='deleted',email=?,display_name='Deleted',password_hash=NULL,avatar_url=NULL,marketing_opt_in=0,updated_at=? WHERE id=?",
                   ('deleted-' + account_id + '@deleted.invalid', now, account_id))
        db.execute('UPDATE sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL', (now, account_id))
        db.execute("UPDATE preferences_bookmarks SET interests='[]',saved='[]',opened='[]' WHERE account_id=?", (account_id,))
        db.execute("UPDATE mission_evidence SET payload='{}' WHERE account_id=?", (account_id,))
        db.execute("UPDATE mission_attempts SET state='expired',result_code='account_deleted' WHERE account_id=? AND state='active'", (account_id,))
        db.execute('DELETE FROM member_interests WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM member_bookmarks WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM member_exploration WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM member_exploration_tombstones WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM member_exploration_events WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM account_entitlements WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM email_verifications WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM oauth_identities WHERE account_id=?', (account_id,))
        db.execute('DELETE FROM managed_profiles WHERE account_id=?', (account_id,))
        if db.execute('SELECT account_id FROM managed_deletions WHERE account_id=?', (account_id,)).fetchone():
            if remote_completed:
                db.execute('UPDATE managed_deletions SET completed_at=? WHERE account_id=?', (now, account_id))
        else:
            db.execute('INSERT INTO managed_deletions(account_id,subject,requested_at,completed_at) VALUES(?,?,?,?)',
                       (account_id, subject, now, now if remote_completed else None))

    def apply_webhook(self, message_id, event, verified_email=None):
        """Signature verification precedes this method; receipt and effect share a transaction."""
        event_type, subject = event['type'], event['data']['id']
        with self.store.transaction() as db:
            if db.execute('SELECT message_id FROM managed_webhook_receipts WHERE message_id=?', (message_id,)).fetchone():
                return {'received': True, 'duplicate': True}
            row = db.execute('SELECT a.* FROM managed_identities i JOIN accounts a ON a.id=i.account_id WHERE i.subject=?', (subject,)).fetchone()
            if row:
                if event_type == 'user.deleted':
                    self._erase(db, row, subject, remote_completed=True)
                elif event_type == 'user.updated' and row['state'] == 'active' and verified_email and row['email'] != verified_email:
                    self._sync_email(db, row, verified_email)
            db.execute('INSERT INTO managed_webhook_receipts(message_id,event_type,received_at) VALUES(?,?,?)', (message_id, event_type, self.clock()))
            return {'received': True, 'duplicate': False}

    def finish_delete(self, account_id):
        with self.store.transaction() as db:
            db.execute('UPDATE managed_deletions SET completed_at=? WHERE account_id=?', (self.clock(), account_id))

    def ban_account(self, account_id, operator, reason):
        """Trusted operator command only; deliberately not exposed by visitor HTTP routes."""
        operator, reason = text(operator, 128), text(reason, 500)
        with self.store.transaction() as db:
            row = db.execute('SELECT a.email,p.cpf_fingerprint FROM accounts a JOIN managed_profiles p ON p.account_id=a.id WHERE a.id=?', (account_id,)).fetchone()
            if not row:
                reject('not_found', 'Cadastro não encontrado.', 404)
            now = self.clock()
            if not db.execute('SELECT cpf_fingerprint FROM managed_bans WHERE cpf_fingerprint=?', (row['cpf_fingerprint'],)).fetchone():
                db.execute('INSERT INTO managed_bans(cpf_fingerprint,email_fingerprint,account_id,created_at) VALUES(?,?,?,?)',
                           (row['cpf_fingerprint'], fingerprint(row['email'], self.cfg['cpfKey'], 'email'), account_id, now))
            db.execute("UPDATE accounts SET state='suspended',updated_at=? WHERE id=?", (now, account_id))
            db.execute('UPDATE sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL', (now, account_id))
            db.execute('INSERT INTO managed_audit(id,account_id,actor,action,reason,created_at) VALUES(?,?,?,?,?,?)',
                       (identifier(), account_id, operator, 'permanent_ban', reason, now))
