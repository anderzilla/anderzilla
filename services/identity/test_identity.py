"""Adversarial local tests; Azure SQL integration is sql_smoke.py, not emulated."""
import base64
import json
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch, Mock
from urllib.parse import urlsplit, parse_qs

from services.identity import security
from services.identity.api import dispatch, CONTEXT_COOKIE, SESSION_COOKIE
from services.identity.config import POLICY_VERSION
from services.identity.core import IdentityService, Rejected
from services.identity.storage import SQLiteStore, Session

ENV = {'IDENTITY_ENV': 'homolog', 'IDENTITY_ALLOWED_ORIGIN': 'https://anderzilla.com',
       'IDENTITY_SQL_SERVER': 'test.invalid', 'IDENTITY_SQL_DATABASE': 'test', 'IDENTITY_SQL_USER': 'test',
       'IDENTITY_SQL_PASSWORD': 'test-only', 'IDENTITY_VERIFY_URL_BASE': 'https://anderzilla.com/verify',
       'IDENTITY_KP_CYCLE_BUDGET': '1000', 'IDENTITY_REWARDS_ENABLED': 'true'}


class Capture:
    def __init__(self):
        self.sent, self.ready, self.fail = [], True, False
    def is_configured(self):
        return self.ready
    def send_verification(self, email, url, lang):
        if self.fail:
            raise RuntimeError('private SMTP details that must never escape')
        self.sent.append(url)
    def token(self):
        return parse_qs(urlsplit(self.sent[-1]).query)['token'][0]


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, ENV, clear=True)
        self.env.start()
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = SQLiteStore(Path(self.tmp.name) / 'identity.sqlite')
        self.mail = Capture()
        self.now = 10000
        self.svc = IdentityService(self.store, self.mail, lambda: self.now)
        self.browser = security.token_hash('test-browser')
        self.number = 0

    def tearDown(self):
        self.tmp.cleanup()
        self.env.stop()

    def register(self, verified=True):
        self.number += 1
        email = f'test{self.number}@example.invalid'
        password = 'StrongPassword123!'
        data = {'email': email, 'password': password, 'displayName': 'Tester', 'ageConfirmed': True,
                'termsAccepted': True, 'termsVersion': POLICY_VERSION, 'privacyVersion': POLICY_VERSION}
        record = self.svc.register(data, 'register-browser-' + str(self.number))
        if verified:
            self.svc.verify_email(self.mail.token(), 'verify-browser-' + str(self.number))
        login = self.svc.login(email, password, 'login-browser-' + str(self.number))
        return self.svc.authenticate(login['sessionToken']), login, data

    def mission(self, kind='interests', mission_id='test-mission', award=25):
        definition = {'titlePT': 'Missão de teste', 'titleEN': 'Test mission'}
        if kind == 'quiz':
            definition['questions'] = [{'id': 'q1', 'promptPT': 'Escolha A', 'promptEN': 'Choose A',
                                        'options': [{'id': 'a', 'textPT': 'A', 'textEN': 'A'}, {'id': 'b', 'textPT': 'B', 'textEN': 'B'}],
                                        'correctOption': 'a'}]
        with self.store.transaction() as db:
            db.execute('INSERT INTO missions(id,version,award,starts_at,ends_at,active,verifier,definition_json,coverage_reference) VALUES(?,?,?,?,?,?,?,?,?)',
                       (mission_id, 1, award, self.now - 1, self.now + 86400, 1, kind, json.dumps(definition), 'test-only; not public'))
        return mission_id

    def evidence(self, principal=None, kind='interests'):
        mid = self.mission(kind)
        challenge = self.svc.challenge(self.browser, principal, mid, 1)
        payload = {'interests': ['games', 'ia', 'gadgets']} if kind == 'interests' else {'answers': {'q1': 'a'}}
        evidence = self.svc.evidence(self.browser, principal, challenge['challengeId'], payload)
        return mid, evidence

    def headers(self):
        response = dispatch(self.svc, 'GET', '/api/account/capabilities', {'Origin': ENV['IDENTITY_ALLOWED_ORIGIN']})
        cookie = response['headers']['Set-Cookie'].split(';', 1)[0]
        return {'Origin': ENV['IDENTITY_ALLOWED_ORIGIN'], 'Content-Type': 'application/json',
                'X-CSRF-Token': response['body']['csrfToken'], 'Cookie': cookie}

    def test_foreign_keys_are_enforced_on_every_connection(self):
        with self.store.transaction() as db:
            self.assertEqual(db.execute('PRAGMA foreign_keys').fetchone()['foreign_keys'], 1)
        with self.assertRaises(sqlite3.IntegrityError), self.store.transaction() as db:
            db.execute('INSERT INTO wallets(account_id,available,reserved) VALUES(?,?,?)', ('missing', 0, 0))

    def test_email_single_use_expiry_and_resend_replaces_token(self):
        principal, _, _ = self.register(False)
        old = self.mail.token()
        self.svc.resend(principal)
        with self.assertRaises(Rejected):
            self.svc.verify_email(old, self.browser)
        raw = self.mail.token()
        self.svc.verify_email(raw, self.browser)
        with self.assertRaises(Rejected):
            self.svc.verify_email(raw, self.browser)
        self.assertTrue(self.svc.me(principal)['account']['emailVerified'])

    def test_email_exact_expiry_rejected(self):
        self.register(False)
        self.now += 86400
        with self.assertRaises(Rejected):
            self.svc.verify_email(self.mail.token(), self.browser)

    def test_smtp_missing_does_not_create_account(self):
        self.mail.ready = False
        with self.assertRaises(Rejected):
            self.register()
        with self.store.transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) AS count FROM accounts').fetchone()['count'], 0)

    def test_smtp_failure_recoverable_by_login_and_resend(self):
        self.mail.fail = True
        with self.assertRaises(Rejected) as caught:
            self.register()
        self.assertNotIn('private SMTP', str(caught.exception))
        login = self.svc.login('test1@example.invalid', 'StrongPassword123!', self.browser)
        principal = self.svc.authenticate(login['sessionToken'])
        self.mail.fail = False
        self.svc.resend(principal)
        self.svc.verify_email(self.mail.token(), self.browser)
        self.assertTrue(self.svc.me(principal)['account']['emailVerified'])

    def test_password_policy_and_consent_fail_without_typeerror(self):
        with self.assertRaises(Rejected):
            self.svc.register({'ageConfirmed': False})
        with self.assertRaises(Rejected) as caught:
            self.svc.register({'email': 'x@example.invalid', 'displayName': 'X', 'password': 'x',
                               'ageConfirmed': True, 'termsAccepted': True, 'termsVersion': POLICY_VERSION, 'privacyVersion': POLICY_VERSION})
        self.assertEqual(caught.exception.code, 'invalid_password')

    def test_failed_login_rate_is_durable(self):
        for index in range(8):
            with self.assertRaises(Rejected) as caught:
                self.svc.login('missing@example.invalid', 'wrong', f'browser{index}')
            self.assertEqual(caught.exception.code, 'invalid_credentials')
        with self.assertRaises(Rejected) as caught:
            self.svc.login('missing@example.invalid', 'wrong', 'another-browser')
        self.assertEqual(caught.exception.status, 429)
        with self.store.transaction() as db:
            self.assertEqual(db.execute("SELECT count FROM rate_limits WHERE scope='login_email'").fetchone()['count'], 8)
        self.now += 900
        with self.assertRaises(Rejected) as caught:
            self.svc.login('missing@example.invalid', 'wrong', 'new')
        self.assertEqual(caught.exception.code, 'invalid_credentials')

    def test_profile_single_transaction_export_and_delete(self):
        principal, login, data = self.register()
        profile = self.svc.update_profile(principal, {'displayName': 'New', 'interests': ['games', 'games', 'ia'],
                                                     'saved': ['content-one'], 'opened': ['content-two'], 'marketingOptIn': True})
        self.assertEqual(profile['account']['interests'], ['games', 'ia'])
        exported = self.svc.export_data(principal)
        self.assertNotIn('password_hash', json.dumps(exported))
        self.assertEqual(exported['account']['saved'], ['content-one'])
        with self.assertRaises(Rejected):
            self.svc.delete_account(principal, 'DELETE', 'wrong')
        self.svc.delete_account(principal, 'DELETE', data['password'])
        self.assertIsNone(self.svc.authenticate(login['sessionToken']))
        with self.store.transaction() as db:
            row = db.execute('SELECT display_name,password_hash,email FROM accounts WHERE id=?', (principal.account_id,)).fetchone()
        self.assertIsNone(row['password_hash'])
        self.assertEqual(row['display_name'], 'Deleted')
        self.assertNotEqual(row['email'], data['email'])

    def test_avatar_preset_upload_and_invalid_rejected(self):
        principal, _, _ = self.register()
        profile = self.svc.update_profile(principal, {'avatarUrl': '/hub/avatars/preset-3.svg'})
        self.assertEqual(profile['account']['avatarUrl'], '/hub/avatars/preset-3.svg')
        upload = 'data:image/jpeg;base64,' + base64.b64encode(b'\xff\xd8\xff' + b'0' * 200).decode()
        profile = self.svc.update_profile(principal, {'avatarUrl': upload})
        self.assertEqual(profile['account']['avatarUrl'], upload)
        with self.assertRaises(Rejected):
            self.svc.update_profile(principal, {'avatarUrl': '/hub/avatars/preset-9.svg'})
        with self.assertRaises(Rejected):
            self.svc.update_profile(principal, {'avatarUrl': 'https://evil.example/tracker.png'})
        with self.assertRaises(Rejected):
            self.svc.update_profile(principal, {'avatarUrl': 'data:image/jpeg;base64,' + base64.b64encode(b'0' * 200000).decode()})
        with self.assertRaises(Rejected):
            self.svc.update_profile(principal, {'avatarUrl': 'data:text/html;base64,' + base64.b64encode(b'<script>').decode()})
        profile = self.svc.update_profile(principal, {'avatarUrl': None})
        self.assertIsNone(profile['account']['avatarUrl'])

    def test_sessions_expire_and_revoke_without_local_fallback(self):
        principal, login, _ = self.register()
        self.svc.logout_all(principal)
        self.assertIsNone(self.svc.authenticate(login['sessionToken']))
        new = self.svc.login('test1@example.invalid', 'StrongPassword123!', self.browser)
        self.now = new['expiresAt']
        self.assertIsNone(self.svc.authenticate(new['sessionToken']))

    def test_pending_anonymous_requires_same_browser_verified_account(self):
        _, evidence = self.evidence(None)
        principal, _, _ = self.register(False)
        with self.assertRaises(Rejected) as caught:
            self.svc.claim(principal, self.browser, 'unverified-key', pending_token=evidence['pendingToken'])
        self.assertEqual(caught.exception.code, 'email_not_verified')
        self.svc.verify_email(self.mail.token(), self.browser)
        with self.assertRaises(Rejected):
            self.svc.claim(principal, 'other-browser', 'wrong-browser-key', pending_token=evidence['pendingToken'])
        first = self.svc.claim(principal, self.browser, 'pending-replay-key', pending_token=evidence['pendingToken'])
        second = self.svc.claim(principal, self.browser, 'pending-replay-key', pending_token=evidence['pendingToken'])
        self.assertEqual(first, second)
        self.assertEqual(self.svc.wallet(principal)['available'], 25)
        with self.assertRaises(Rejected):
            self.svc.claim(principal, self.browser, 'new-key-after-claim', pending_token=evidence['pendingToken'])

    def test_concurrent_claim_same_and_different_keys_credits_once(self):
        principal, _, _ = self.register()
        mid, evidence = self.evidence(principal)
        def claim(index):
            return IdentityService(self.store, clock=lambda: self.now).claim(principal, self.browser, f'concurrent-{index}', evidence_ref=evidence['evidenceRef'], mission_id=mid, version=1)
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(claim, range(4)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(self.svc.wallet(principal)['available'], 25)
        self.assertEqual(len(self.svc.ledger(principal)['items']), 1)

    def test_pending_cannot_cross_account_or_mission(self):
        owner, _, _ = self.register()
        other, _, _ = self.register()
        mid, evidence = self.evidence(owner)
        with self.assertRaises(Rejected):
            self.svc.claim(other, self.browser, 'cross-account-key', pending_token=evidence['pendingToken'])
        with self.assertRaises(Rejected):
            self.svc.claim(owner, self.browser, 'cross-mission-key', evidence_ref=evidence['evidenceRef'], mission_id='other', version=1)
        self.assertEqual(self.svc.wallet(owner)['available'], 0)

    def test_quiz_answers_validated_server_side_and_correct_not_exposed(self):
        principal, _, _ = self.register()
        mid = self.mission('quiz')
        challenge = self.svc.challenge(self.browser, principal, mid, 1)
        self.assertNotIn('correctOption', json.dumps(challenge))
        with self.assertRaises(Rejected):
            self.svc.evidence(self.browser, principal, challenge['challengeId'], {'answers': {'q1': 'b'}, 'correct': True})
        evidence = self.svc.evidence(self.browser, principal, challenge['challengeId'], {'answers': {'q1': 'a'}})
        self.svc.claim(principal, self.browser, 'quiz-claim-key', pending_token=evidence['pendingToken'])
        self.assertEqual(self.svc.wallet(principal)['available'], 25)

    def test_duplicate_interests_not_eligible(self):
        mid = self.mission()
        challenge = self.svc.challenge(self.browser, None, mid, 1)
        with self.assertRaises(Rejected):
            self.svc.evidence(self.browser, None, challenge['challengeId'], {'interests': ['games'] * 3})

    def test_rules_changed_or_no_budget_reject_without_partial_credit(self):
        principal, _, _ = self.register()
        mid, evidence = self.evidence(principal)
        with patch.dict(os.environ, {'IDENTITY_KP_CYCLE_BUDGET': '0'}), self.assertRaises(Rejected):
            self.svc.claim(principal, self.browser, 'capacity-test-key', pending_token=evidence['pendingToken'])
        self.assertEqual(self.svc.wallet(principal)['available'], 0)
        with self.store.transaction() as db:
            db.execute('UPDATE missions SET definition_json=? WHERE id=?', ('{"updated":true}', mid))
        with self.assertRaises(Rejected):
            self.svc.claim(principal, self.browser, 'changed-rules-key', pending_token=evidence['pendingToken'])

    def test_ledger_append_only_and_user_scoped(self):
        principal, _, _ = self.register()
        other, _, _ = self.register()
        _, evidence = self.evidence(principal)
        self.svc.claim(principal, self.browser, 'ledger-claim-key', pending_token=evidence['pendingToken'])
        self.assertEqual(self.svc.ledger(other)['items'], [])
        with self.assertRaises(sqlite3.IntegrityError), self.store.transaction() as db:
            db.execute('UPDATE ledger SET available_delta=999')

    def test_capabilities_missing_config_safe_and_no_database_called(self):
        with patch.dict(os.environ, {}, clear=True):
            fake = Mock()
            result = dispatch(fake, 'GET', '/api/account/capabilities')
            self.assertFalse(result['body']['registration'])
            self.assertFalse(result['body']['google'])
            self.assertFalse(result['body']['rewards'])
            fake.email_ready.assert_not_called()
            self.assertIn('HttpOnly; Secure', result['headers']['Set-Cookie'])

    def test_csrf_exact_origin_content_type_and_preflight(self):
        headers = self.headers()
        for change in [{'Origin': 'https://evil.invalid'}, {'Origin': ''}, {'X-CSRF-Token': 'wrong'}, {'Content-Type': 'text/plain'}]:
            result = dispatch(self.svc, 'POST', '/api/account/logout', {**headers, **change}, {})
            self.assertIn(result['status'], {403, 415})
        result = dispatch(self.svc, 'OPTIONS', '/api/account/login', {'Origin': ENV['IDENTITY_ALLOWED_ORIGIN'], 'Access-Control-Request-Method': 'POST'})
        self.assertEqual(result['status'], 204)
        self.assertEqual(result['headers']['Access-Control-Allow-Credentials'], 'true')
        self.assertEqual(dispatch(self.svc, 'POST', '/api/account/logout', headers, {})['status'], 204)

    def test_api_no_user_id_authority_or_unverified_claim(self):
        headers = self.headers()
        self.assertEqual(dispatch(self.svc, 'GET', '/api/account/me', headers)['status'], 401)
        result = dispatch(self.svc, 'POST', '/api/account/register', headers, {'accountId': 'admin'})
        self.assertEqual(result['status'], 422)
        result = dispatch(self.svc, 'POST', '/api/points/evidence', headers, {'challengeId': 'fake', 'correct': True})
        self.assertEqual(result['status'], 422)
        result = dispatch(self.svc, 'POST', '/api/points/pending/claim', headers, {'pendingToken': 'x' * 43})
        self.assertEqual(result['status'], 401)

    def google_env(self):
        return patch.dict(os.environ, {'IDENTITY_GOOGLE_CLIENT_ID': 'test-client', 'IDENTITY_GOOGLE_CLIENT_SECRET': 'test-only-secret',
                                       'IDENTITY_GOOGLE_REDIRECT_URI': 'https://anderzilla.com/account/callback'})

    def test_google_direct_token_route_rejected(self):
        with self.google_env():
            result = dispatch(self.svc, 'POST', '/api/account/oauth/google/callback', self.headers(), {'idToken': 'fake', 'nonce': 'caller'})
        self.assertEqual(result['status'], 422)

    def test_google_state_pkce_single_use_browser_bound_and_no_auto_link(self):
        _, _, data = self.register(False)
        consent = {k: data[k] for k in ('ageConfirmed', 'termsAccepted', 'termsVersion', 'privacyVersion')}
        with self.google_env():
            started = self.svc.google_start(self.browser, consent)
            query = parse_qs(urlsplit(started['url']).query)
            state = query['state'][0]
            with self.assertRaises(Rejected):
                self.svc.google_callback('other-browser', 'test-code', state)
            with patch('requests.post', return_value=Mock(status_code=200, json=lambda: {'id_token': 'signed-token'})) as post, \
                 patch('services.identity.security.verify_google_id_token', return_value={'sub': 'google-sub', 'email': data['email'], 'name': 'Victim'}):
                with self.assertRaises(Rejected) as caught:
                    self.svc.google_callback(self.browser, 'test-code', state)
                self.assertEqual(caught.exception.code, 'account_link_required')
                verifier = post.call_args.kwargs['data']['code_verifier']
                self.assertEqual(security.pkce_challenge(verifier), query['code_challenge'][0])
                with self.assertRaises(Rejected):
                    self.svc.google_callback(self.browser, 'test-code', state)

    def test_google_verified_new_identity_session_and_suspend(self):
        data = {'ageConfirmed': True, 'termsAccepted': True, 'termsVersion': POLICY_VERSION, 'privacyVersion': POLICY_VERSION}
        with self.google_env():
            state = parse_qs(urlsplit(self.svc.google_start(self.browser, data)['url']).query)['state'][0]
            with patch('requests.post', return_value=Mock(status_code=200, json=lambda: {'id_token': 'signed-token'})), \
                 patch('services.identity.security.verify_google_id_token', return_value={'sub': 'google-sub', 'email': 'google@example.invalid', 'name': 'Reader'}):
                result = self.svc.google_callback(self.browser, 'code', state)
            principal = self.svc.authenticate(result['sessionToken'])
            self.assertFalse(self.svc.me(principal)['account']['hasPassword'])
            self.now += 301
            with self.assertRaises(Rejected):
                self.svc.delete_account(principal, 'DELETE')
            with self.store.transaction() as db:
                db.execute("UPDATE accounts SET state='suspended' WHERE id=?", (principal.account_id,))
            self.assertIsNone(self.svc.authenticate(result['sessionToken']))

    def test_security_google_library_checks_nonce_audience_and_expiry(self):
        # This asserts our checks around Google's signature-verifying library;
        # it does not claim a real Google user was authenticated.
        claims = {'iss': 'https://accounts.google.com', 'aud': 'client', 'nonce': 'nonce', 'email_verified': True,
                  'sub': 'sub', 'exp': 9999999999}
        with patch('google.oauth2.id_token.verify_oauth2_token', return_value=claims) as verify:
            self.assertEqual(security.verify_google_id_token('signed', 'client', 'nonce')['sub'], 'sub')
            self.assertEqual(verify.call_args.kwargs['audience'], 'client')
            for key, value in [('nonce', 'wrong'), ('aud', 'wrong'), ('email_verified', 'true'), ('exp', 1)]:
                with patch('google.oauth2.id_token.verify_oauth2_token', return_value={**claims, key: value}), self.assertRaises(ValueError):
                    security.verify_google_id_token('signed', 'client', 'nonce')

    def test_sql_server_pagination_has_no_limit_and_tuple_rows_map(self):
        cursor = Mock()
        cursor.description = [('id',), ('available_delta',)]
        cursor.fetchall.return_value = [('entry', 25)]
        connection = Mock()
        connection.cursor.return_value = cursor
        session = Session(connection, True)
        result = session.page('SELECT id,available_delta FROM ledger WHERE account_id=? ORDER BY id', ('account',), 5)
        query, params = cursor.execute.call_args.args
        self.assertNotIn('LIMIT', query)
        self.assertIn('OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY', query)
        self.assertEqual(params, ('account', 5))
        self.assertEqual(result.fetchall(), [{'id': 'entry', 'available_delta': 25}])


if __name__ == '__main__':
    unittest.main()
