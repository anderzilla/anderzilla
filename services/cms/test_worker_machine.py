import hashlib
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from api import dispatch
from automation import Automation, ALLOWED_HOSTS
from core import CMS, Error
from storage import SQLiteStore
import worker_auth

ADMIN = {'id': 'admin', 'roles': ['anderzilla_admin']}
EDITOR = {'id': 'editor', 'roles': ['anderzilla_editor']}
WORKER_PRINCIPAL = {'id': '111111111111111111111', 'roles': ['anderzilla_worker'], 'sub': '111111111111111111111', 'email': 'worker@anderzilla-homolog.iam.gserviceaccount.com'}

# Dedicated transport header for Google ID token through Azure Static Web Apps.
# Standard Authorization is ignored — SWA can consume/strip it.
WORKER_HEADER = 'X-AnderZilla-Worker-Authorization'
WORKER_HEADER_LOWER = 'x-anderzilla-worker-authorization'


def worker_claims(aud='https://cms.anderzilla.com', sub='111111111111111111111', email='worker@anderzilla-homolog.iam.gserviceaccount.com', iss='https://accounts.google.com', email_verified=True):
    import time
    return {'aud': aud, 'sub': sub, 'email': email, 'iss': iss, 'email_verified': email_verified, 'exp': 9999999999, 'iat': int(time.time())}


class WorkerAuthTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            'CMS_GOOGLE_WORKER_AUDIENCE': 'https://cms.anderzilla.com',
            'CMS_GOOGLE_WORKER_SUBJECT': '111111111111111111111',
            'CMS_GOOGLE_WORKER_EMAIL': 'worker@anderzilla-homolog.iam.gserviceaccount.com',
        }

    def test_missing_settings_returns_503(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer token'}, env={}, verifier=lambda t, a: worker_claims())
        self.assertEqual(cm.exception.status, 503)

    def test_missing_bearer_returns_401(self):
        cases = [{}, {WORKER_HEADER: ''}, {WORKER_HEADER: 'Basic abc'}, {WORKER_HEADER: 'Bearer '}]
        for h in cases:
            with self.assertRaises(Error) as cm:
                worker_auth.authenticate_worker(h, env=self.env, verifier=lambda t, a: worker_claims())
            self.assertEqual(cm.exception.status, 401)

    def test_standard_authorization_alone_rejected(self):
        # Standard Authorization alone must be rejected — only dedicated header is read
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({'Authorization': 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(cm.exception.status, 401)
        # Lower-case variant also rejected
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({'authorization': 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(cm.exception.status, 401)
        # Even with valid token in Authorization, custom header missing => 401
        def strict_verifier(t, a):
            if t == 'valid':
                return worker_claims()
            raise Exception('invalid token')
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({'Authorization': 'Bearer valid'}, env=self.env, verifier=strict_verifier)
        self.assertEqual(cm.exception.status, 401)

    def test_custom_header_works_case_insensitive(self):
        # Canonical case
        p = worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(p['id'], '111111111111111111111')
        # Lowercase
        p2 = worker_auth.authenticate_worker({WORKER_HEADER_LOWER: 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(p2['id'], '111111111111111111111')
        # Mixed case
        p3 = worker_auth.authenticate_worker({'X-ANDERZILLA-WORKER-AUTHORIZATION': 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(p3['id'], '111111111111111111111')
        # Ensure Bearer scheme still required
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Token valid'}, env=self.env, verifier=lambda t, a: worker_claims())

    def test_conflicting_headers_cannot_override(self):
        # Verifier only accepts token == 'correct-token' — proves which header was read
        def strict_verifier(token, aud):
            if token == 'correct-token':
                return worker_claims()
            raise Exception('invalid token')

        # Valid in custom, invalid in Authorization => must succeed (custom wins, Authorization ignored)
        p = worker_auth.authenticate_worker(
            {WORKER_HEADER: 'Bearer correct-token', 'Authorization': 'Bearer wrong-token'},
            env=self.env, verifier=strict_verifier
        )
        self.assertEqual(p['id'], '111111111111111111111')

        # Invalid in custom, valid in Authorization => must fail (Authorization must not override)
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker(
                {WORKER_HEADER: 'Bearer wrong-token', 'Authorization': 'Bearer correct-token'},
                env=self.env, verifier=strict_verifier
            )
        self.assertEqual(cm.exception.status, 401)

        # Both present but custom is the only one read — ensure alternate header not accepted
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker(
                {'Authorization': 'Bearer correct-token', 'X-Worker-Token': 'Bearer correct-token'},
                env=self.env, verifier=strict_verifier
            )
        self.assertEqual(cm.exception.status, 401)

    def test_alternate_headers_rejected(self):
        # Random alternate headers must not be accepted
        for alt_header in ['X-Worker-Authorization', 'X-Auth-Token', 'X-Google-Token', 'Authorization-Token']:
            with self.assertRaises(Error) as cm:
                worker_auth.authenticate_worker({alt_header: 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
            self.assertEqual(cm.exception.status, 401)

    def test_token_in_query_rejected(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, url='https://cms.example.com/api/worker/automation/lease?token=tok', env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(cm.exception.status, 401)
        # Also with id_token
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, url='https://cms.example.com/api/worker/automation/lease?id_token=tok', env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(cm.exception.status, 401)

    def test_token_in_cookie_rejected(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok', 'Cookie': 'token=tok'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(cm.exception.status, 401)

    def test_token_in_body_rejected(self):
        # Body containing token-like keys must be rejected — dedicated header only
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=lambda t, a: worker_claims(), body={'token': 'tok'})
        self.assertEqual(cm.exception.status, 401)
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=lambda t, a: worker_claims(), body={'id_token': 'tok'})
        self.assertEqual(cm.exception.status, 401)

    def test_valid_claims_success(self):
        p = worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims(aud='https://cms.anderzilla.com'))
        self.assertEqual(p['id'], '111111111111111111111')
        self.assertEqual(p['roles'], ['anderzilla_worker'])

    def test_wrong_aud_fails(self):
        def verifier(t, a):
            c = worker_claims(aud='https://evil.com')
            return c
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=verifier)
        self.assertEqual(cm.exception.status, 401)

    def test_wrong_sub_fails(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=lambda t, a: worker_claims(sub='other'))
        self.assertEqual(cm.exception.status, 401)

    def test_wrong_email_fails(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=lambda t, a: worker_claims(email='evil@example.com'))
        self.assertEqual(cm.exception.status, 401)

    def test_email_not_verified_fails(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=lambda t, a: worker_claims(email_verified=False))
        self.assertEqual(cm.exception.status, 401)

    def test_wrong_issuer_fails(self):
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=lambda t, a: worker_claims(iss='https://evil.com'))
        self.assertEqual(cm.exception.status, 401)

    def test_verify_exception_fails_401(self):
        def bad(t, a):
            raise Exception('signature fail')
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=self.env, verifier=bad)
        self.assertEqual(cm.exception.status, 401)

    def test_no_sensitive_log_on_failure(self):
        token = 'super-secret-token-value-123'
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: f'Bearer {token}'}, env=self.env, verifier=lambda t, a: (_ for _ in ()).throw(Exception('fail')))
        msg = str(cm.exception)
        self.assertNotIn(token, msg)
        self.assertNotIn('super-secret', msg)
        # Also ensure header name not leaked in message (lowercase check)
        self.assertNotIn(WORKER_HEADER_LOWER, msg.lower())
        # Ensure error does not leak token via repr either
        self.assertNotIn(token, repr(cm.exception))

    def test_bearer_only_no_query_cookie_variants(self):
        p = worker_auth.authenticate_worker({WORKER_HEADER_LOWER: 'Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())
        self.assertEqual(p['id'], '111111111111111111111')
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer valid', 'Cookie': 'session=abc; Bearer valid'}, env=self.env, verifier=lambda t, a: worker_claims())

    def test_sensitive_header_lowercase_in_stripping(self):
        # Explicit sensitive-field set must contain lowercase dedicated header
        self.assertIn(WORKER_HEADER_LOWER, worker_auth._SENSITIVE_FIELDS)
        self.assertIn('authorization', worker_auth._SENSITIVE_FIELDS)


class ExternalGatingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')

    def tearDown(self):
        self.temp.cleanup()

    def test_preview_manual_when_disabled(self):
        svc = Automation(self.store, 'local', external_enabled=False)
        body = {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'global', 'language': 'pt-BR'}, 'idempotencyKey': 'k1-preview-manual'}
        res = svc.preview(ADMIN, body)
        self.assertEqual(res['executionMode'], 'manual')
        self.assertFalse(res['externalDispatchEnabled'])
        self.assertIn('manual', res['warnings'][0].lower())

    def test_preview_external_when_enabled_requires_targetUrl(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        body = {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'global', 'language': 'pt-BR'}, 'idempotencyKey': 'k2'}
        with self.assertRaises(Error) as cm:
            svc.preview(ADMIN, body)
        self.assertIn('targetUrl', cm.exception.code)

    def test_preview_external_with_valid_targetUrl(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        body = {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/test'}, 'idempotencyKey': 'k3-ext'}
        res = svc.preview(ADMIN, body)
        self.assertEqual(res['executionMode'], 'external')
        self.assertTrue(res['externalDispatchEnabled'])
        self.assertIn('externo', res['warnings'][0].lower() or 'worker' in res['warnings'][0].lower())

    def test_create_manual_vs_external(self):
        svc_manual = Automation(self.store, 'local', external_enabled=False)
        run_m = svc_manual.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'global', 'language': 'en'}, 'idempotencyKey': 'create-manual-1'})
        self.assertEqual(run_m['executionMode'], 'manual')
        self.assertFalse(run_m['externalDispatched'])
        svc_ext = Automation(self.store, 'local', external_enabled=True)
        run_e = svc_ext.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'global', 'language': 'en', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'create-ext-1'})
        self.assertEqual(run_e['executionMode'], 'external')
        self.assertFalse(run_e['externalDispatched'])
        self.assertEqual(run_e['status'], 'queued')

    def test_processes_and_summary_reflect_external(self):
        svc_off = Automation(self.store, 'local', external_enabled=False)
        self.assertFalse(svc_off.processes(ADMIN)['externalDispatchEnabled'])
        self.assertFalse(svc_off.summary(ADMIN)['externalDispatchEnabled'])
        self.assertFalse(any(p['executorConnected'] for p in svc_off.processes(ADMIN)['items'] if p['id'] == 'seo-audit'))
        svc_on = Automation(self.store, 'local', external_enabled=True)
        self.assertTrue(svc_on.processes(ADMIN)['externalDispatchEnabled'])
        self.assertTrue(svc_on.summary(ADMIN)['externalDispatchEnabled'])
        seo = [p for p in svc_on.processes(ADMIN)['items'] if p['id'] == 'seo-audit'][0]
        self.assertTrue(seo['executorConnected'])
        self.assertEqual(seo['executionMode'], 'external')


class TargetUrlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.svc = Automation(self.store, 'local', external_enabled=True)

    def tearDown(self):
        self.temp.cleanup()

    def request(self, target_url, key='k'):
        return {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': target_url}, 'idempotencyKey': key}

    def test_valid_hosts(self):
        for host in ALLOWED_HOSTS:
            url = f'https://{host}/path'
            self.svc.preview(ADMIN, self.request(url, key=f'valid-{host}'))

    def test_invalid_host_rejected(self):
        with self.assertRaises(Error) as cm:
            self.svc.preview(ADMIN, self.request('https://evil.com/', key='bad-host'))
        self.assertEqual(cm.exception.code, 'targetUrl_host_not_allowed')

    def test_scheme_must_be_https(self):
        with self.assertRaises(Error):
            self.svc.preview(ADMIN, self.request('http://anderzilla.com/', key='bad-scheme'))

    def test_userinfo_blocked(self):
        with self.assertRaises(Error) as cm:
            self.svc.preview(ADMIN, self.request('https://user:pass@anderzilla.com/', key='userinfo'))
        self.assertIn('userinfo', cm.exception.code)

    def test_fragment_userinfo_blocked(self):
        with self.assertRaises(Error):
            self.svc.preview(ADMIN, self.request('https://anderzilla.com/path#frag@evil', key='frag-userinfo'))

    def test_port_blocked(self):
        with self.assertRaises(Error) as cm:
            self.svc.preview(ADMIN, self.request('https://anderzilla.com:8443/', key='bad-port'))
        self.assertIn('port', cm.exception.code)

    def test_malformed_port_rejected(self):
        with self.assertRaises(Error) as cm:
            self.svc.preview(ADMIN, self.request('https://anderzilla.com:abc/', key='malformed-port'))
        self.assertEqual(cm.exception.code, 'invalid_targetUrl')

    def test_default_port_443_allowed(self):
        self.svc.preview(ADMIN, self.request('https://anderzilla.com:443/path', key='port-443'))
        self.svc.preview(ADMIN, self.request('https://anderzilla.com/path', key='no-port'))

    def test_missing_targetUrl_required_when_external(self):
        body = {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR'}, 'idempotencyKey': 'missing-url'}
        with self.assertRaises(Error) as cm:
            self.svc.preview(ADMIN, body)
        self.assertIn('targetUrl', cm.exception.code)

    def test_too_long(self):
        long_url = 'https://anderzilla.com/' + 'a' * 2040
        with self.assertRaises(Error) as cm:
            self.svc.preview(ADMIN, self.request(long_url, key='too-long'))
        self.assertIn('too_long', cm.exception.code)


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.worker = WORKER_PRINCIPAL

    def tearDown(self):
        self.temp.cleanup()

    def create_external(self, key, target='https://anderzilla.com/a'):
        svc = Automation(self.store, 'local', external_enabled=True)
        return svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': target}, 'idempotencyKey': key})

    def test_no_legacy_manual_lease(self):
        svc_manual = Automation(self.store, 'local', external_enabled=False)
        run = svc_manual.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR'}, 'idempotencyKey': 'legacy-manual'})
        self.assertEqual(run['executionMode'], 'manual')
        svc_ext = Automation(self.store, 'local', external_enabled=True)
        with self.assertRaises(Error) as cm:
            svc_ext.lease(self.worker)
        self.assertEqual(cm.exception.code, 'no_work')

    def test_lease_selects_oldest_and_sets_fields(self):
        r1 = self.create_external('lease-oldest-1', 'https://anderzilla.com/a')
        r2 = self.create_external('lease-oldest-2', 'https://anderzilla.com/b')
        svc = Automation(self.store, 'local', external_enabled=True)
        env = svc.lease(self.worker)
        self.assertEqual(env['runId'], r1['id'])
        self.assertEqual(env['processId'], 'seo-audit')
        self.assertIn('leaseId', env)
        self.assertIn('fencingToken', env)
        self.assertEqual(env['fencingToken'], 1)
        self.assertIn('input', env)
        self.assertEqual(env['input']['targetUrl'], 'https://anderzilla.com/a')
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', r1['id'])).fetchone()
            run = json.loads(row[0])
            self.assertEqual(run['status'], 'running')
            self.assertTrue(run['externalDispatched'])
            self.assertEqual(run['leaseId'], env['leaseId'])
            self.assertEqual(run['history'][-1]['actor'], f"gcp-worker:{self.worker['id']}")

    def test_lease_only_external_seo_audit(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        run_ed = svc.create(ADMIN, {'processId': 'editorial-package', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR'}, 'idempotencyKey': 'ed-manual'})
        self.assertEqual(run_ed['executionMode'], 'manual')
        with self.assertRaises(Error) as cm:
            svc.lease(self.worker)
        self.assertEqual(cm.exception.code, 'no_work')

    def test_atomic_concurrent_lease_once(self):
        self.create_external('conc-lease-1')
        svc1 = Automation(self.store, 'local', external_enabled=True)
        svc2 = Automation(self.store, 'local', external_enabled=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(lambda: svc1.lease(self.worker))
            f2 = pool.submit(lambda: svc2.lease(self.worker))
            results = []
            errors = []
            for f in [f1, f2]:
                try:
                    results.append(f.result())
                except Error as e:
                    errors.append(e)
                except Exception as e:
                    errors.append(e)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, 'no_work') if hasattr(errors[0], 'code') else True
        self.assertEqual(results[0]['fencingToken'], 1)

    def test_lease_expiry_recovery_and_fencing_increment(self):
        r = self.create_external('expiry-1')
        svc = Automation(self.store, 'local', external_enabled=True)
        env1 = svc.lease(self.worker)
        self.assertEqual(env1['fencingToken'], 1)
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', r['id'])).fetchone()
            run = json.loads(row[0])
            run['leaseExpiresAt'] = past
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), 'local', run['id']))
        env2 = svc.lease(self.worker)
        self.assertEqual(env2['runId'], r['id'])
        self.assertEqual(env2['fencingToken'], 3)
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', r['id'])).fetchone()
            run = json.loads(row[0])
            self.assertGreaterEqual(run['version'], 4)
            self.assertTrue(any(h.get('reason') == 'lease_expired' for h in run['history']))

    def test_lease_envelope_bounded(self):
        r = self.create_external('envelope-1', 'https://anderzilla.com/a')
        svc = Automation(self.store, 'local', external_enabled=True)
        env = svc.lease(self.worker)
        self.assertEqual(set(env.keys()), {'schemaVersion', 'runId', 'processId', 'idempotencyKey', 'input', 'leaseId', 'fencingToken', 'leasedAt', 'leaseExpiresAt'})
        self.assertEqual(env['schemaVersion'], 1)
        self.assertIn('market', env['input'])
        self.assertIn('language', env['input'])
        self.assertIn('targetUrl', env['input'])
        expected = hashlib.sha256(f"{r['id']}:1".encode()).hexdigest()[:32]
        self.assertEqual(env['idempotencyKey'], expected)


class CompleteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.worker = WORKER_PRINCIPAL
        self.svc = Automation(self.store, 'local', external_enabled=True)
        self.run = self.svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'comp-create'})
        self.lease = self.svc.lease(self.worker)

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_succeeded(self):
        result = {'checks': [{'id': 'title', 'status': 'pass'}]}
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': result}
        receipt = self.svc.complete(self.worker, body)
        self.assertEqual(receipt['status'], 'succeeded')
        self.assertIn('resultHash', receipt)
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', self.run['id'])).fetchone()
            run = json.loads(row[0])
            self.assertEqual(run['status'], 'succeeded')
            self.assertEqual(run['result'], result)
            self.assertEqual(run['history'][-1]['evidenceSource'], 'google_worker')

    def test_complete_failed(self):
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'failed', 'errorCode': 'fetch_timeout', 'errorMessage': 'Timeout after 8s'}
        receipt = self.svc.complete(self.worker, body)
        self.assertEqual(receipt['status'], 'failed')
        with self.store.transaction() as db:
            run = json.loads(db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', self.run['id'])).fetchone()[0])
            self.assertEqual(run['error']['code'], 'fetch_timeout')

    def test_complete_replay_same_receipt(self):
        result = {'checks': []}
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': result}
        r1 = self.svc.complete(self.worker, body)
        r2 = self.svc.complete(self.worker, body)
        self.assertEqual(r1, r2)

    def test_complete_divergent_returns_409(self):
        result = {'checks': []}
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': result}
        self.svc.complete(self.worker, body)
        body2 = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': {'checks': [{'id': 'x'}]}}
        with self.assertRaises(Error) as cm:
            self.svc.complete(self.worker, body2)
        self.assertEqual(cm.exception.status, 409)

    def test_complete_stale_fencing_409(self):
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': 999, 'status': 'failed', 'errorCode': 'e', 'errorMessage': 'm'}
        with self.assertRaises(Error) as cm:
            self.svc.complete(self.worker, body)
        self.assertEqual(cm.exception.status, 409)

    def test_complete_expired_lease_409(self):
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', self.run['id'])).fetchone()
            run = json.loads(row[0])
            run['leaseExpiresAt'] = past
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE environment=? AND id=?', (run['status'], json.dumps(run), 'local', run['id']))
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'failed', 'errorCode': 'e', 'errorMessage': 'm'}
        with self.assertRaises(Error) as cm:
            self.svc.complete(self.worker, body)
        self.assertEqual(cm.exception.status, 409)

    def test_complete_result_too_large_422(self):
        big = {'data': 'x' * (70 * 1024)}
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': big}
        with self.assertRaises(Error) as cm:
            self.svc.complete(self.worker, body)
        self.assertEqual(cm.exception.status, 422)

    def test_complete_strict_fields_rejected(self):
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': {}, 'extra': 1}
        with self.assertRaises(Error) as cm:
            self.svc.complete(self.worker, body)
        self.assertEqual(cm.exception.status, 422)

    def test_complete_never_accepts_publication_fields(self):
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': {}, 'publication': 'evil'}
        with self.assertRaises(Error):
            self.svc.complete(self.worker, body)


class ManualProtectionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')

    def tearDown(self):
        self.temp.cleanup()

    def test_manual_start_blocked_for_external(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        run = svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'prot-start'})
        with self.assertRaises(Error) as cm:
            svc.change(ADMIN, run['id'], 'transition', {'version': run['version'], 'reason': 'tentar iniciar', 'action': 'start', 'idempotencyKey': 'start-ext'})
        self.assertEqual(cm.exception.status, 409)

    def test_manual_complete_blocked_for_external(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        run = svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'prot-complete'})
        worker = WORKER_PRINCIPAL
        svc.lease(worker)
        with self.store.transaction() as db:
            row = db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', run['id'])).fetchone()
            cur = json.loads(row[0])
        with self.assertRaises(Error) as cm:
            svc.change(ADMIN, run['id'], 'transition', {'version': cur['version'], 'reason': 'manual complete', 'action': 'complete', 'evidence': 'evidência', 'idempotencyKey': 'manual-complete'})
        self.assertEqual(cm.exception.status, 409)

    def test_manual_cancel_allowed_for_queued_external(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        run = svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'prot-cancel'})
        cancelled = svc.change(ADMIN, run['id'], 'cancel', {'version': run['version'], 'reason': 'Cancelar a pedido', 'idempotencyKey': 'cancel-ext'})
        self.assertEqual(cancelled['status'], 'cancelled')

    def test_manual_cancel_blocked_for_running_external(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        run = svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'prot-cancel-running'})
        svc.lease(WORKER_PRINCIPAL)
        with self.store.transaction() as db:
            cur = json.loads(db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', run['id'])).fetchone()[0])
        with self.assertRaises(Error) as cm:
            svc.change(ADMIN, run['id'], 'cancel', {'version': cur['version'], 'reason': 'cancel running', 'idempotencyKey': 'cancel-run'})
        self.assertEqual(cm.exception.status, 409)

    def test_retry_preserves_mode_when_enabled(self):
        svc = Automation(self.store, 'local', external_enabled=True)
        run = svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'retry-ext-1'})
        lease = svc.lease(WORKER_PRINCIPAL)
        svc.complete(WORKER_PRINCIPAL, {'runId': lease['runId'], 'leaseId': lease['leaseId'], 'fencingToken': lease['fencingToken'], 'status': 'failed', 'errorCode': 'e', 'errorMessage': 'm'})
        with self.store.transaction() as db:
            failed = json.loads(db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', run['id'])).fetchone()[0])
        child = svc.change(ADMIN, run['id'], 'retry', {'version': failed['version'], 'reason': 'retry externo', 'idempotencyKey': 'retry-child'})
        self.assertEqual(child['executionMode'], 'external')

    def test_retry_fallback_manual_when_disabled(self):
        svc_on = Automation(self.store, 'local', external_enabled=True)
        run = svc_on.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'retry-fallback'})
        lease = svc_on.lease(WORKER_PRINCIPAL)
        svc_on.complete(WORKER_PRINCIPAL, {'runId': lease['runId'], 'leaseId': lease['leaseId'], 'fencingToken': lease['fencingToken'], 'status': 'failed', 'errorCode': 'e', 'errorMessage': 'm'})
        with self.store.transaction() as db:
            failed = json.loads(db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', run['id'])).fetchone()[0])
        with patch.dict(os.environ, {'CMS_AUTOMATION_EXTERNAL_ENABLED': 'false'}):
            svc_off = Automation(self.store, 'local', external_enabled=False)
            child = svc_off.change(ADMIN, run['id'], 'retry', {'version': failed['version'], 'reason': 'retry manual fallback', 'idempotencyKey': 'retry-fallback2'})
            self.assertEqual(child['executionMode'], 'manual')


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.cms = CMS(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_human_cannot_access_worker_lease(self):
        with self.assertRaises(Error) as cm:
            dispatch(self.cms, ADMIN, 'POST', '/api/worker/automation/lease', {}, environment='local')
        self.assertEqual(cm.exception.status, 403)

    def test_worker_cannot_access_admin_routes(self):
        with self.assertRaises(Error) as cm:
            dispatch(self.cms, WORKER_PRINCIPAL, 'GET', '/api/admin/automation/processes', {}, environment='local')
        self.assertEqual(cm.exception.status, 403)

    def test_worker_body_actor_rejected(self):
        with self.assertRaises(Error) as cm:
            dispatch(self.cms, WORKER_PRINCIPAL, 'POST', '/api/worker/automation/lease', {'actor': 'evil'}, environment='local')
        self.assertEqual(cm.exception.status, 422)

    def test_worker_lease_via_dispatch(self):
        with patch.dict(os.environ, {'CMS_AUTOMATION_EXTERNAL_ENABLED': 'true'}):
            svc = Automation(self.store, 'local', external_enabled=True)
            svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'dispatch-lease'})
            result = dispatch(self.cms, WORKER_PRINCIPAL, 'POST', '/api/worker/automation/lease', {}, environment='local')
            self.assertIn('runId', result)
            self.assertIn('leaseId', result)

    def test_worker_complete_via_dispatch_strict(self):
        with patch.dict(os.environ, {'CMS_AUTOMATION_EXTERNAL_ENABLED': 'true'}):
            svc = Automation(self.store, 'local', external_enabled=True)
            run = svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'dispatch-complete'})
            lease = dispatch(self.cms, WORKER_PRINCIPAL, 'POST', '/api/worker/automation/lease', {}, environment='local')
            body = {'runId': lease['runId'], 'leaseId': lease['leaseId'], 'fencingToken': lease['fencingToken'], 'status': 'succeeded', 'result': {'checks': []}}
            receipt = dispatch(self.cms, WORKER_PRINCIPAL, 'POST', '/api/worker/automation/complete', body, environment='local')
            self.assertEqual(receipt['status'], 'succeeded')
