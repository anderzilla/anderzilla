import time
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from automation import Automation
from core import Error
from storage import SQLiteStore
import worker_auth

ADMIN = {'id': 'admin', 'roles': ['anderzilla_admin']}
WORKER = {'id': '111111111111111111111', 'roles': ['anderzilla_worker'], 'sub': '111111111111111111111', 'email': 'worker@anderzilla-homolog.iam.gserviceaccount.com'}

WORKER_HEADER = 'X-AnderZilla-Worker-Authorization'
WORKER_HEADER_LOWER = 'x-anderzilla-worker-authorization'


def base_claims(aud='https://cms.anderzilla.com', exp=None, iat=None, aud_val=None):
    now = int(time.time())
    claims = {
        'aud': aud_val if aud_val is not None else aud,
        'sub': '111111111111111111111',
        'email': 'worker@anderzilla-homolog.iam.gserviceaccount.com',
        'iss': 'https://accounts.google.com',
        'email_verified': True,
        'exp': exp if exp is not None else now + 3600,
        'iat': iat if iat is not None else now,
    }
    return claims


ENV = {
    'CMS_GOOGLE_WORKER_AUDIENCE': 'https://cms.anderzilla.com',
    'CMS_GOOGLE_WORKER_SUBJECT': '111111111111111111111',
    'CMS_GOOGLE_WORKER_EMAIL': 'worker@anderzilla-homolog.iam.gserviceaccount.com',
}


class OidcExtraTests(unittest.TestCase):
    def test_aud_exact_string_required(self):
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: {**base_claims(), 'aud': None})
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: {**base_claims(aud_val=['https://cms.anderzilla.com'])})
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(aud_val='https://evil.com'))
        c = base_claims()
        c.pop('aud')
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: c)

    def test_standard_authorization_rejected(self):
        # Standard Authorization must be rejected — dedicated header only
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({'Authorization': 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims())
        self.assertEqual(cm.exception.status, 401)
        # Conflicting headers cannot override
        def strict_verifier(token, aud):
            if token == 'good':
                return base_claims()
            raise Exception('bad token')
        p = worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer good', 'Authorization': 'Bearer bad'}, env=ENV, verifier=strict_verifier)
        self.assertEqual(p['id'], '111111111111111111111')
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer bad', 'Authorization': 'Bearer good'}, env=ENV, verifier=strict_verifier)
        # Alternate headers rejected
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({'X-Worker-Token': 'Bearer good'}, env=ENV, verifier=strict_verifier)
        # Query / cookie / body rejected even with valid custom header
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer good'}, url='https://cms.example.com/api/worker/automation/lease?token=good', env=ENV, verifier=strict_verifier)
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer good', 'Cookie': 'token=good'}, env=ENV, verifier=strict_verifier)
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer good'}, env=ENV, verifier=strict_verifier, body={'token': 'good'})

    def test_exp_must_be_numeric_future(self):
        now = int(time.time())
        c = base_claims()
        c.pop('exp')
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: c)
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(exp='not-a-number'))
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(exp=now - 1000))
        with self.assertRaises(Error) as cm:
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(exp=now - 30))
        self.assertEqual(cm.exception.status, 401)
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(exp=now))
        c = base_claims(exp=now + 60)
        p = worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: c)
        self.assertEqual(p['id'], '111111111111111111111')

    def test_iat_not_future(self):
        now = int(time.time())
        c = base_claims()
        c.pop('iat')
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: c)
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(iat='bad'))
        with self.assertRaises(Error):
            worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=lambda t, a: base_claims(iat=now + 1000))

    def test_verify_oauth2_token_used(self):
        import google.oauth2.id_token
        called = {}
        def fake_verify(token, request, audience):
            called['audience'] = audience
            called['request'] = request
            return base_claims(aud=audience)
        with patch.object(google.oauth2.id_token, 'verify_oauth2_token', fake_verify):
            p = worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=None)
            self.assertEqual(called.get('audience'), ENV['CMS_GOOGLE_WORKER_AUDIENCE'])
            self.assertIsNotNone(called.get('request'))

    def test_cert_timeout_forced_to_five_despite_caller_120(self):
        import requests
        req = worker_auth._build_request()
        self.assertIsNotNone(req)
        sess = getattr(req, 'session', None) or getattr(req, '_session', None)
        self.assertIsNotNone(sess, "Request should expose session")
        captured = {}

        def fake_request(self, *args, **kwargs):
            captured['timeout'] = kwargs.get('timeout')
            captured['args'] = args
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {}
            mock_resp.content = b'{}'
            return mock_resp

        with patch.object(requests.Session, 'request', fake_request):
            sess.request('GET', 'https://example.com', timeout=120)
            self.assertEqual(captured.get('timeout'), 5, "caller timeout=120 must be forced to 5")
        with patch.object(requests.Session, 'request', fake_request):
            sess.request('GET', 'https://example.com')
            self.assertEqual(captured.get('timeout'), 5)
        with patch.object(requests.Session, 'request', fake_request):
            req('https://www.googleapis.com/oauth2/v1/certs', timeout=120)
            self.assertEqual(captured.get('timeout'), 5)

    def test_transport_construction_failure_has_no_unbounded_fallback(self):
        with patch('google.auth.transport.requests.Request', side_effect=RuntimeError("simulated construction failure")):
            with self.assertRaises(Error) as cm:
                worker_auth._build_request()
            self.assertEqual(cm.exception.status, 503)
            self.assertEqual(cm.exception.code, "unavailable")
            msg = str(cm.exception)
            self.assertNotIn("simulated", msg)
            self.assertNotIn("RuntimeError", msg)
            self.assertIn("temporariamente", msg.lower())
        with patch.object(worker_auth, '_build_request', side_effect=Error(503, "unavailable", "Serviço temporariamente indisponível.")):
            with self.assertRaises(Error) as cm2:
                worker_auth.authenticate_worker({WORKER_HEADER: 'Bearer tok'}, env=ENV, verifier=None)
            self.assertEqual(cm2.exception.status, 503)
            self.assertNotIn("traceback", str(cm2.exception).lower())
            self.assertNotIn("simulated", str(cm2.exception).lower())

    def test_sensitive_header_lowercase_in_stripping(self):
        self.assertIn(WORKER_HEADER_LOWER, worker_auth._SENSITIVE_FIELDS)


class LeaseRetryBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.svc = Automation(self.store, 'local', external_enabled=True)
        self.run = self.svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'lease-budget-create'})

    def tearDown(self):
        self.temp.cleanup()

    def test_deliveryCount_persisted_and_max_3(self):
        with self.store.transaction() as db:
            run = json.loads(db.execute('SELECT document FROM automation_runs WHERE environment=? AND id=?', ('local', self.run['id'])).fetchone()[0])
            self.assertEqual(run.get('deliveryCount'), 0)
            self.assertEqual(run.get('fencingToken'), 0)

        self.temp.cleanup()
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.svc = Automation(self.store, 'local', external_enabled=True)
        run = self.svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'lease-budget-2'})
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        l1 = self.svc.lease(WORKER)
        self.assertEqual(l1['fencingToken'], 1)
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            self.assertEqual(d['deliveryCount'], 1)
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            d['leaseExpiresAt'] = past
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE id=?', (d['status'], json.dumps(d), run['id']))
        l2 = self.svc.lease(WORKER)
        self.assertEqual(l2['fencingToken'], 3)
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            self.assertEqual(d['deliveryCount'], 2)
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            d['leaseExpiresAt'] = past
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE id=?', (d['status'], json.dumps(d), run['id']))
        l3 = self.svc.lease(WORKER)
        self.assertEqual(l3['fencingToken'], 5)
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            self.assertEqual(d['deliveryCount'], 3)
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            d['leaseExpiresAt'] = past
            db.execute('UPDATE automation_runs SET status=?,document=? WHERE id=?', (d['status'], json.dumps(d), run['id']))
        with self.assertRaises(Error) as cm:
            self.svc.lease(WORKER)
        self.assertEqual(cm.exception.code, 'no_work')
        with self.store.transaction() as db:
            d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
            self.assertEqual(d['status'], 'failed')
            self.assertEqual(d['error']['code'], 'lease_exhausted')
            self.assertIsNotNone(d.get('finishedAt'))
            self.assertTrue(any(h.get('code') == 'lease_exhausted' for h in d['history']))
            self.assertEqual(d['fencingToken'], 6)

    def test_new_human_retry_starts_own_delivery_count(self):
        lease = self.svc.lease(WORKER)
        self.svc.complete(WORKER, {'runId': lease['runId'], 'leaseId': lease['leaseId'], 'fencingToken': lease['fencingToken'], 'status': 'failed', 'errorCode': 'fetch_timeout', 'errorMessage': 'Timeout after 8s'})
        with self.store.transaction() as db:
            failed = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (self.run['id'],)).fetchone()[0])
        child = self.svc.change(ADMIN, self.run['id'], 'retry', {'version': failed['version'], 'reason': 'Revisar novamente', 'idempotencyKey': 'retry-lease-budget'})
        self.assertEqual(child['deliveryCount'], 0)
        self.assertEqual(child['fencingToken'], 0)
        l = self.svc.lease(WORKER)
        self.assertEqual(l['runId'], child['id'])
        self.assertEqual(l['fencingToken'], 1)

    def test_fencing_monotonic_no_double_increment_ambiguity(self):
        self.temp.cleanup()
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.svc = Automation(self.store, 'local', external_enabled=True)
        run = self.svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'mono-fence'})
        fences = []
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        for _ in range(2):
            l = self.svc.lease(WORKER)
            fences.append(l['fencingToken'])
            with self.store.transaction() as db:
                d = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (run['id'],)).fetchone()[0])
                d['leaseExpiresAt'] = past
                db.execute('UPDATE automation_runs SET status=?,document=? WHERE id=?', (d['status'], json.dumps(d), run['id']))
        l = self.svc.lease(WORKER)
        fences.append(l['fencingToken'])
        self.assertEqual(fences, [1,3,5])


class CompletionCanonicalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.svc = Automation(self.store, 'local', external_enabled=True)
        self.run = self.svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'canon-create'})
        self.lease = self.svc.lease(WORKER)

    def tearDown(self):
        self.temp.cleanup()

    def test_key_order_equivalent_replay(self):
        result_a = {'b': 2, 'a': 1}
        result_b = {'a': 1, 'b': 2}
        body_a = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': result_a}
        receipt = self.svc.complete(WORKER, body_a)
        import hashlib, json
        expected = hashlib.sha256(json.dumps(result_a, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(receipt['resultHash'], expected)
        incoming_b = hashlib.sha256(json.dumps(result_b, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(incoming_b, expected)
        receipt2 = self.svc.complete(WORKER, {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': result_b})
        self.assertEqual(receipt, receipt2)

    def test_size_uses_canonical(self):
        big_val = 'x' * (64 * 1024 - 50)
        result = {'a': big_val, 'b': 'y'}
        big = {'a': 'x' * (70 * 1024)}
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'succeeded', 'result': big}
        with self.assertRaises(Error) as cm:
            self.svc.complete(WORKER, body)
        self.assertEqual(cm.exception.code, 'result_too_large')


class ErrorAllowlistTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.svc = Automation(self.store, 'local', external_enabled=True)
        self.run = self.svc.create(ADMIN, {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'br', 'language': 'pt-BR', 'targetUrl': 'https://anderzilla.com/a'}, 'idempotencyKey': 'err-allow-create'})
        self.lease = self.svc.lease(WORKER)

    def tearDown(self):
        self.temp.cleanup()

    def test_unknown_code_mapped_to_worker_failed(self):
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'failed', 'errorCode': 'evil_code', 'errorMessage': 'https://evil.com/secret?token=abc'}
        receipt = self.svc.complete(WORKER, body)
        self.assertEqual(receipt['error']['code'], 'worker_failed')
        self.assertNotIn('evil.com', receipt['error']['message'])
        with self.store.transaction() as db:
            run = json.loads(db.execute('SELECT document FROM automation_runs WHERE id=?', (self.run['id'],)).fetchone()[0])
            self.assertEqual(run['error']['code'], 'worker_failed')
            self.assertNotIn('evil.com', run['error']['message'])
            self.assertNotIn('evil.com', json.dumps(run['history']))

    def test_allowlisted_code_stores_generic_not_raw(self):
        body = {'runId': self.lease['runId'], 'leaseId': self.lease['leaseId'], 'fencingToken': self.lease['fencingToken'], 'status': 'failed', 'errorCode': 'fetch_timeout', 'errorMessage': 'https://secret.example.com/fetch?token=abc failed after https://other'}
        receipt = self.svc.complete(WORKER, body)
        self.assertEqual(receipt['error']['code'], 'fetch_timeout')
        self.assertNotIn('secret.example.com', receipt['error']['message'])
        self.assertNotIn('https://', receipt['error']['message'])
