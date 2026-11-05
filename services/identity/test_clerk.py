"""Adversarial, offline tests. No real accounts, CPF owners or provider traffic."""
import datetime as dt
import json
import os
import sqlite3
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from services.identity.clerk_auth import ClerkGateway, ClerkIdentity, settings
from services.identity.clerk_api import dispatch_clerk
from services.identity.clerk_service import ClerkAccountService, POLICY_VERSION, birth_date
from services.identity.core import Rejected
from services.identity.cpf import normalize_cpf, fingerprint
from services.identity.managed_operator import run_ban
from services.identity.storage import SQLiteStore


def cpf(number):
    # Synthetically generated solely for offline checks; never represents ownership.
    value = f'{number:09}'
    for size in (9, 10):
        value += str((sum(int(value[i]) * (size + 1 - i) for i in range(size)) * 10 % 11) % 10)
    return value


class ManagedTests(unittest.TestCase):
    def test_managed_host_ignores_platform_bearer_and_forwards_application_bearer(self):
        with patch.dict(os.environ, {'AZ_ACCOUNT_AUTH_PROVIDER': 'clerk'}):
            result = self.call('GET', '/api/account/me', headers={'Authorization': 'Bearer platform-token'})
            self.assertEqual(result['status'], 200)
            self.assertIsNone(result['body']['account'])
            self.gateway.verify.assert_not_called()
            self.call('GET', '/api/account/me', headers={'Authorization': 'Bearer platform-token',
                                                       'X-AnderZilla-Authorization': 'Bearer clerk-token'})
            self.gateway.verify.assert_called_once_with('Bearer clerk-token')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.store = SQLiteStore(Path(self.tmp.name) / 'test.sqlite')
        self.now = int(dt.datetime(2026, 11, 4, 15, tzinfo=dt.timezone.utc).timestamp())
        self.cfg = {'ok': True, 'origins': {'https://anderzilla.com'}, 'cpfKey': 'offline-test-key-' * 4}
        self.service = ClerkAccountService(self.store, self.cfg, clock=lambda: self.now)
        self.identity = ClerkIdentity('user_TestOne', 'sess_TestOne', 'one@example.invalid', self.now)
        self.data = {'cpf': cpf(123456789), 'displayName': 'Offline Tester', 'birthDate': '2000-01-01',
                     'termsAccepted': True, 'termsVersion': POLICY_VERSION, 'privacyVersion': POLICY_VERSION}
        self.headers = {'Origin': 'https://anderzilla.com', 'Content-Type': 'application/json', 'Authorization': 'Bearer offline'}
        self.gateway = Mock()
        self.gateway.verify.return_value = self.identity

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, method, path, data=None, headers=None):
        return dispatch_clerk(self.store, method, path, self.headers if headers is None else headers, data,
                              gateway=self.gateway, cfg=self.cfg, clock=lambda: self.now)

    def register(self, identity=None, data=None):
        return self.service.onboard(identity or self.identity, data or self.data)['accountId']

    def assert_rejected(self, code, fn, *args):
        with self.assertRaises(Rejected) as caught:
            fn(*args)
        self.assertEqual(caught.exception.code, code)

    def test_cpf_formats_and_repeated_or_malformed_values(self):
        value = self.data['cpf']
        formatted = f'{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}'
        self.assertEqual(normalize_cpf(formatted), value)
        for value in [None, 123, '', '0' * 11, '1' * 11, '111.111.111-11', '12345678901', ' 12345678909', '１２３４５６７８９０９']:
            self.assert_rejected('invalid_cpf', normalize_cpf, value)

    def test_cpf_fingerprint_keyed_and_domain_separated(self):
        self.assertNotEqual(fingerprint('value', 'a' * 32), fingerprint('value', 'b' * 32))
        self.assertNotEqual(fingerprint('value', 'a' * 32), fingerprint('value', 'a' * 32, 'email'))
        self.assert_rejected('temporarily_unavailable', fingerprint, 'value', 'short')

    def test_missing_profile_needs_onboarding(self):
        self.assertEqual(self.service.me(self.identity), {'account': None, 'onboardingRequired': True})
        self.assert_rejected('onboarding_required', self.service.export, self.identity)

    def test_signup_is_verified_private_and_retry_idempotent(self):
        account_id = self.register()
        self.assertEqual(self.register(), account_id)
        result = self.service.me(self.identity)
        self.assertTrue(result['account']['emailVerified'])
        self.assertEqual(result['account']['email'], self.identity.email)
        self.assertFalse(result['account']['hasPassword'])
        self.assertNotIn(self.data['cpf'], json.dumps(result))
        with self.store.transaction() as db:
            profile = db.execute('SELECT * FROM managed_profiles WHERE account_id=?', (account_id,)).fetchone()
        self.assertNotIn(self.data['cpf'], json.dumps(profile))
        self.assertEqual(len(profile['cpf_fingerprint']), 64)

    def test_cpf_duplicate_and_reassignment_blocked(self):
        self.register()
        other = replace(self.identity, subject='user_Other', email='other@example.invalid')
        self.assert_rejected('registration_conflict', self.service.onboard, other, self.data)
        self.assert_rejected('registration_conflict', self.service.onboard, self.identity, {**self.data, 'cpf': cpf(987654321)})

    def test_concurrent_registration_same_cpf_only_once(self):
        identities = [replace(self.identity, subject='user_Concurrent' + str(n), email=f'concurrent{n}@example.invalid') for n in range(2)]
        def register(identity):
            try:
                return self.service.onboard(identity, self.data)
            except Rejected as exc:
                return exc.code
        results = list(ThreadPoolExecutor(2).map(register, identities))
        self.assertEqual(sum(isinstance(r, dict) for r in results), 1)
        self.assertEqual(results.count('registration_conflict'), 1)

    def test_minors_rejected_even_with_spoofed_parent_fields(self):
        for born in ('2010-01-01', '2008-11-05'):
            self.assert_rejected('minor_registration_unavailable', self.service.onboard, self.identity, {**self.data, 'birthDate': born})
        result = self.call('POST', '/api/account/onboarding', {**self.data, 'guardianCpf': self.data['cpf']})
        self.assertEqual(result['body']['error']['code'], 'invalid_fields')

    def test_eighteenth_birthday_sao_paulo_boundary(self):
        midnight_utc = int(dt.datetime(2026, 11, 5, 1, tzinfo=dt.timezone.utc).timestamp())
        self.assertEqual(birth_date('2008-11-05', midnight_utc)[1], 17)
        local_midnight = int(dt.datetime(2026, 11, 5, 3, tzinfo=dt.timezone.utc).timestamp())
        self.assertEqual(birth_date('2008-11-05', local_midnight)[1], 18)
        self.assertIsNotNone(self.service.onboard(self.identity, {**self.data, 'birthDate': '2008-11-04'}))

    def test_invalid_dates_and_policy_rejected(self):
        for born in ('2027-01-01', '2026-02-30', '', None, '2026-1-01'):
            self.assert_rejected('invalid_birth_date', self.service.onboard, self.identity, {**self.data, 'birthDate': born})
        self.assert_rejected('consent_required', self.service.onboard, self.identity, {**self.data, 'termsAccepted': False})
        self.assert_rejected('policy_changed', self.service.onboard, self.identity, {**self.data, 'termsVersion': 'old'})

    def test_profile_rejects_arbitrary_identity_and_cpf_changes(self):
        self.register()
        for patch in [{'id': 'other'}, {'cpf': cpf(987654321)}, {'email': 'other@example.invalid'}, {'state': 'active'}]:
            self.assert_rejected('invalid_fields', self.service.profile, self.identity, patch)
        result = self.service.profile(self.identity, {'displayName': 'Changed', 'saved': ['item-1']})
        self.assertEqual(result['account']['displayName'], 'Changed')
        self.assertEqual(result['account']['saved'], ['item-1'])

    def test_private_data_scoped_to_signed_identity(self):
        own = self.register()
        other = replace(self.identity, subject='user_Other', email='other@example.invalid')
        other_id = self.register(other, {**self.data, 'cpf': cpf(987654321), 'displayName': 'Other'})
        exported = self.service.export(other)
        self.assertEqual(exported['account']['id'], other_id)
        self.assertNotEqual(exported['account']['id'], own)
        self.assertNotIn(self.identity.email, json.dumps(exported))

    def test_legacy_email_is_not_automatically_linked(self):
        self.register()
        other = replace(self.identity, subject='user_LegacyCollision')
        self.assert_rejected('account_link_required', self.service.onboard, other, {**self.data, 'cpf': cpf(987654321)})

    def test_ban_blocks_live_session_and_reregistration(self):
        account_id = self.register()
        self.service.ban_account(account_id, 'offline-operator', 'Offline abuse test')
        for action in [lambda: self.service.me(self.identity), lambda: self.service.profile(self.identity, {'displayName': 'Bypass'}), lambda: self.service.delete(self.identity, 'DELETE')]:
            with self.assertRaises(Rejected):
                action()
        other = replace(self.identity, subject='user_NewBanned', email='new@example.invalid')
        self.assert_rejected('registration_unavailable', self.service.onboard, other, self.data)
        email_same = replace(self.identity, subject='user_NewSameEmail')
        self.assert_rejected('registration_unavailable', self.service.onboard, email_same, {**self.data, 'cpf': cpf(987654321)})

    def test_operator_ban_local_state_survives_provider_failure(self):
        account_id = self.register()
        self.gateway.ban_user.side_effect = RuntimeError('offline provider failure')
        with self.assertRaises(RuntimeError):
            run_ban(self.store, self.gateway, self.cfg, account_id, 'operator', 'Offline test')
        self.assert_rejected('account_unavailable', self.service.me, self.identity)

    def test_delete_cleans_avatar_and_cpf_and_blocks_replay(self):
        account_id = self.register()
        self.service.profile(self.identity, {'avatarUrl': '/hub/avatars/preset-1.svg'})
        self.service.delete(self.identity, 'DELETE')
        self.service.delete(self.identity, 'DELETE')  # durable retry without duplicate work
        with self.store.transaction() as db:
            account = db.execute('SELECT state,avatar_url,email FROM accounts WHERE id=?', (account_id,)).fetchone()
            self.assertIsNone(db.execute('SELECT * FROM managed_profiles WHERE account_id=?', (account_id,)).fetchone())
        self.assertEqual(account['state'], 'deleted')
        self.assertIsNone(account['avatar_url'])
        self.assertNotEqual(account['email'], self.identity.email)
        self.assert_rejected('account_unavailable', self.service.me, self.identity)
        self.assert_rejected('account_unavailable', self.service.onboard, self.identity, self.data)

    def test_delete_requires_recent_verified_factor_and_confirmation(self):
        self.register()
        self.assert_rejected('confirmation_required', self.service.delete, self.identity, 'yes')
        self.assert_rejected('reauth_required', self.service.delete, replace(self.identity, authenticated_at=self.now - 301), 'DELETE')

    def test_delete_remote_failure_is_pending_and_retryable(self):
        self.register()
        self.gateway.delete_user.side_effect = Rejected('identity_unavailable', 'Offline', 503)
        result = self.call('POST', '/api/account/delete', {'confirm': 'DELETE'})
        self.assertEqual(result['body']['error']['code'], 'deletion_pending')
        self.assertEqual(self.call('GET', '/api/account/me')['status'], 403)
        self.gateway.delete_user.side_effect = None
        self.assertEqual(self.call('POST', '/api/account/delete', {'confirm': 'DELETE'})['status'], 204)

    def test_cookie_or_admin_header_cannot_authorize(self):
        self.gateway.verify.side_effect = Rejected('authentication_required', 'Offline', 401)
        result = self.call('POST', '/api/account/onboarding', self.data,
                           {**self.headers, 'Cookie': '__Host-anderzilla_sid=fake', 'X-MS-CLIENT-PRINCIPAL': 'fake', 'Authorization': ''})
        self.assertEqual(result['status'], 401)

    def test_cors_and_mutation_origin_are_exact(self):
        self.assertEqual(self.call('POST', '/api/account/onboarding', self.data, {'Content-Type': 'application/json'})['status'], 403)
        self.assertEqual(self.call('GET', '/api/account/me', headers={'Origin': 'https://anderzilla.com.evil.invalid'})['status'], 403)
        self.assertEqual(self.call('OPTIONS', '/api/account/me', headers={'Origin': 'https://anderzilla.com', 'Access-Control-Request-Method': 'PATCH'})['status'], 204)
        self.assertEqual(self.call('POST', '/api/account/onboarding', self.data, {**self.headers, 'Content-Type': 'text/plain'})['status'], 415)

    def test_capabilities_never_reveal_keys_and_disable_native_routes(self):
        result = self.call('GET', '/api/account/capabilities')
        self.assertEqual(result['body']['provider'], 'clerk')
        self.assertEqual(result['body']['minimumAge'], 18)
        self.assertFalse(result['body']['minorAccessEnabled'])
        self.assertNotIn(self.cfg['cpfKey'], json.dumps(result))
        for route in ('register', 'login', 'password/reset', 'family/invitations'):
            self.assertEqual(self.call('POST', '/api/account/' + route, {})['status'], 404)


    def webhook(self, event, message_id='msg_Offline', timestamp=None, signature=None):
        import base64
        from svix.webhooks import Webhook
        from services.identity.clerk_webhooks import dispatch_webhook
        secret = 'whsec_' + base64.b64encode(b'offline-only-webhook-key-32-bytes!').decode()
        moment = timestamp or dt.datetime.now(dt.timezone.utc)
        raw = json.dumps(event)
        headers = {'svix-id': message_id, 'svix-timestamp': str(int(moment.timestamp())),
                   'svix-signature': signature or Webhook(secret).sign(message_id, moment, raw)}
        return dispatch_webhook(self.store, raw.encode(), headers, cfg={**self.cfg, 'webhookKey': secret},
                                gateway=self.gateway, clock=lambda: self.now)

    def test_webhook_forged_or_old_event_cannot_delete_account(self):
        self.register()
        event = {'type': 'user.deleted', 'data': {'id': self.identity.subject}}
        self.assertEqual(self.webhook(event, signature='v1,bad')['status'], 400)
        old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=10)
        self.assertEqual(self.webhook(event, timestamp=old)['status'], 400)
        self.assertIsNotNone(self.service.me(self.identity)['account'])

    def test_webhook_delete_replay_cleans_profile_and_preserves_ban(self):
        account_id = self.register()
        self.service.ban_account(account_id, 'offline-operator', 'offline test')
        event = {'type': 'user.deleted', 'data': {'id': self.identity.subject}}
        first = self.webhook(event)
        again = self.webhook(event)
        self.assertEqual(first['status'], 200)
        self.assertFalse(first['body']['duplicate'])
        self.assertTrue(again['body']['duplicate'])
        with self.store.transaction() as db:
            row = db.execute('SELECT state,email,avatar_url FROM accounts WHERE id=?', (account_id,)).fetchone()
            self.assertEqual(row['state'], 'deleted')
            self.assertIsNone(row['avatar_url'])
            self.assertNotEqual(row['email'], self.identity.email)
            self.assertIsNone(db.execute('SELECT account_id FROM managed_profiles WHERE account_id=?', (account_id,)).fetchone())
            self.assertIsNotNone(db.execute('SELECT account_id FROM managed_bans WHERE account_id=?', (account_id,)).fetchone())
        new_identity = replace(self.identity, subject='user_NewAfterBan', email='new@example.invalid')
        self.assert_rejected('registration_unavailable', self.service.onboard, new_identity, self.data)

    def test_webhook_updated_fetches_current_email_not_payload_email(self):
        self.register()
        self.gateway.verified_email.return_value = 'current@example.invalid'
        event = {'type': 'user.updated', 'data': {'id': self.identity.subject, 'email_address': 'attacker@example.invalid'}}
        self.assertEqual(self.webhook(event)['status'], 200)
        with self.store.transaction() as db:
            row = db.execute('SELECT email FROM accounts WHERE id=(SELECT account_id FROM managed_identities WHERE subject=?)', (self.identity.subject,)).fetchone()
            self.assertEqual(row['email'], 'current@example.invalid')
        self.gateway.verified_email.assert_called_once_with(self.identity.subject)


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public = cls.private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def setUp(self):
        self.now = int(time.time())
        self.cfg = {'ok': True, 'origins': {'https://anderzilla.com'}, 'issuer': 'https://clerk.anderzilla.com',
                    'secret': 'sk_test_OFFLINE', 'publicKey': self.public, 'cpfKey': 'test-key-' * 8}
        self.claims = {'iss': self.cfg['issuer'], 'sub': 'user_Offline', 'sid': 'sess_Offline', 'azp': 'https://anderzilla.com',
                       'iat': self.now, 'nbf': self.now - 1, 'exp': self.now + 60, 'fva': [0, -1]}
        self.user = {'id': 'user_Offline', 'primary_email_address_id': 'email_Offline',
                     'email_addresses': [{'id': 'email_Offline', 'email_address': 'verified@example.invalid', 'verification': {'status': 'verified'}}]}
        self.session = {'status': 'active', 'user_id': 'user_Offline', 'created_at': (self.now - 3600) * 1000}
        self.transport = Mock(side_effect=lambda method, url, **kwargs: Mock(status_code=200, json=lambda: self.session if '/sessions/' in url else self.user))
        self.gateway = ClerkGateway(self.cfg, self.transport, clock=lambda: self.now)

    def token(self, **changes):
        import jwt
        return 'Bearer ' + jwt.encode({**self.claims, **changes}, self.private, algorithm='RS256')

    def test_valid_signature_verified_email_and_recent_factor(self):
        identity = self.gateway.verify(self.token())
        self.assertEqual(identity.email, 'verified@example.invalid')
        self.assertEqual(identity.authenticated_at, self.now)
        self.assertEqual(self.transport.call_count, 2)

    def test_issuer_azp_time_status_actor_and_ids_fail_closed(self):
        for changes in [{'iss': 'https://attacker.invalid'}, {'azp': 'https://attacker.invalid'}, {'exp': self.now - 10},
                        {'nbf': self.now + 30}, {'iat': self.now + 30}, {'sts': 'pending'}, {'sts': 'unknown'},
                        {'act': {'sub': 'user_Impersonator'}}, {'sid': '../bad'}, {'sub': 'machine_fake'}]:
            with self.subTest(changes=changes), self.assertRaises(Rejected):
                self.gateway.verify(self.token(**changes))

    def test_missing_claim_signature_and_hmac_confusion_rejected(self):
        import jwt
        claims = dict(self.claims)
        claims.pop('sid')
        invalid = 'Bearer ' + jwt.encode(claims, self.private, algorithm='RS256')
        with self.assertRaises(Rejected):
            self.gateway.verify(invalid)
        with self.assertRaises(Rejected):
            self.gateway.verify('Bearer ' + jwt.encode(self.claims, 'offline-secret', algorithm='HS256'))
        with self.assertRaises(Rejected):
            self.gateway.verify(self.token() + 'tampered')

    def test_revocation_wrong_user_and_unverified_primary_email_rejected(self):
        for session in [{**self.session, 'status': 'revoked'}, {**self.session, 'user_id': 'user_Other'}]:
            self.session = session
            with self.assertRaises(Rejected):
                self.gateway.verify(self.token())
        self.session = {'status': 'active', 'user_id': 'user_Offline', 'created_at': self.now * 1000}
        self.user['email_addresses'][0]['verification']['status'] = 'unverified'
        with self.assertRaises(Rejected) as caught:
            self.gateway.verify(self.token())
        self.assertEqual(caught.exception.code, 'email_not_verified')

    def test_banned_or_locked_provider_user_rejected(self):
        for field in ('banned', 'locked'):
            self.user[field] = True
            with self.assertRaises(Rejected):
                self.gateway.verify(self.token())
            self.user[field] = False

    def test_provider_failure_has_no_fallback_or_exception_leak(self):
        import requests
        self.transport.side_effect = requests.Timeout('secret must never escape')
        with self.assertRaises(Rejected) as caught:
            self.gateway.verify(self.token())
        self.assertEqual(caught.exception.status, 503)
        self.assertNotIn('secret', str(caught.exception))

    def test_settings_missing_or_test_keys_in_production_unavailable(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(settings()['ok'])
        env = {'IDENTITY_ENV': 'production', 'IDENTITY_ALLOWED_ORIGIN': 'https://anderzilla.com',
               'CLERK_ISSUER': self.cfg['issuer'], 'CLERK_JWT_KEY': self.public, 'CLERK_SECRET_KEY': 'sk_test_OFFLINE',
               'IDENTITY_CPF_HMAC_KEY': self.cfg['cpfKey'], 'IDENTITY_SQL_SERVER': 'offline', 'IDENTITY_SQL_DATABASE': 'offline',
               'IDENTITY_SQL_USER': 'offline', 'IDENTITY_SQL_PASSWORD': 'offline',
               'CLERK_WEBHOOK_SIGNING_SECRET': 'whsec_b2ZmbGluZS10ZXN0LWtleS1vbmx5'}
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(settings()['ok'])
            os.environ['CLERK_SECRET_KEY'] = 'sk_live_OFFLINE'
            self.assertTrue(settings()['ok'])
            os.environ['IDENTITY_ALLOWED_ORIGIN'] = 'http://localhost:4027'
            self.assertFalse(settings()['ok'])
            os.environ['IDENTITY_ENV'] = 'homolog'
            self.assertTrue(settings()['ok'])
            os.environ['IDENTITY_ALLOWED_ORIGIN'] = 'http://untrusted.example.invalid'
            self.assertFalse(settings()['ok'])
            os.environ['IDENTITY_ALLOWED_ORIGIN'] = 'http://localhost:4027'
            os.environ['CLERK_ISSUER'] = 'http://localhost:4027'
            self.assertFalse(settings()['ok'])


if __name__ == '__main__':
    unittest.main()
