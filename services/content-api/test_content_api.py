import base64
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
CMS_DIR = HERE.parent / 'cms'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CMS_DIR))
from agent_api import AgentGateway
from content_api import MAX_JSON_BYTES, process
from core import CMS
from storage import SQLiteStore

ADMIN = {'id': 'human-admin', 'name': 'Anderson', 'roles': ['anderzilla_admin']}
ARTICLE = {'titlePT': 'T', 'titleEN': 'T', 'summaryPT': 'R', 'summaryEN': 'S', 'bodyPT': 'C', 'bodyEN': 'B', 'category': 'ia', 'sourceName': 'Fonte',
           'sourceUrl': 'https://example.com/n', 'publishedAt': '2026-10-29', 'slugPT': 'noticia', 'slugEN': 'news'}


class ContentApiEdgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.gateway = AgentGateway(CMS(SQLiteStore(Path(self.temp.name) / 'cms.db')), media_hosts=[])
        self.key = self.gateway.create_key(ADMIN, 'claude-test')['key']

    def tearDown(self):
        self.temp.cleanup()

    def call(self, method, path, body=None, headers=None, raw=None, key=True):
        headers = {'content-type': 'application/json', **({'authorization': 'Bearer ' + self.key} if key else {}), **(headers or {})}
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else b'')
        return process(method, path, {}, headers, data, gateway_factory=lambda: self.gateway)

    def test_health_is_public_and_never_touches_the_database(self):
        def forbidden():
            raise AssertionError('health must not open the database')
        status, payload, headers = process('GET', 'health', {}, {}, b'', gateway_factory=forbidden)
        self.assertEqual((status, payload), (200, {'status': 'ok'}))
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_authentication_is_required_and_challenged(self):
        status, payload, headers = self.call('GET', 'schema', key=False)
        self.assertEqual((status, headers.get('WWW-Authenticate')), (401, 'Bearer'))
        self.assertEqual(self.call('GET', 'schema', headers={'authorization': 'Bearer azk_bad_secret'})[0], 401)
        self.assertEqual(self.call('GET', 'schema')[0], 200)

    def test_client_supplied_identity_headers_never_grant_human_power(self):
        principal = base64.b64encode(json.dumps({'userId': 'x', 'userDetails': 'a@b.c', 'userRoles': ['authenticated', 'anderzilla_admin']}).encode()).decode()
        spoof = {'x-ms-client-principal': principal, 'x-ms-client-principal-name': 'anderzilla@ymail.com', 'cookie': 'StaticWebAppsAuthCookie=abc'}
        for path in ('submissions/abc/approve', 'submissions/abc/request-changes', 'releases/abc/promote', 'submissions/abc/comments'):
            status, payload, _ = self.call('POST', path, {}, headers=spoof)
            self.assertIn(status, (401, 403), path)
        self.assertEqual(self.call('GET', 'submissions', headers=spoof)[0], 401)  # human list, even with a valid agent key present
        self.assertEqual(self.call('GET', 'submissions/abc/items', headers=spoof)[0], 401)
        self.assertEqual(self.call('POST', 'submissions/abc/preview', {}, headers=spoof)[0], 401)

    def test_request_validation(self):
        self.assertEqual(self.call('POST', 'articles', headers={'content-type': 'text/plain'}, raw=b'x')[0], 415)
        self.assertEqual(self.call('POST', 'articles', raw=b'{not json')[0], 400)
        self.assertEqual(self.call('POST', 'articles', raw=b'[1,2]')[0], 422)
        self.assertEqual(self.call('POST', 'articles', raw=b'x' * (MAX_JSON_BYTES + 1))[0], 413)
        self.assertEqual(self.call('PUT', 'articles', {})[0], 405)
        self.assertEqual(self.call('DELETE', 'articles')[0], 405)
        self.assertEqual(self.call('GET', 'nope')[0], 404)

    def test_media_route_accepts_larger_bodies_than_the_others(self):
        big = json.dumps({'contentBase64': 'A' * 400000}).encode()
        status, payload, _ = self.call('POST', 'media', raw=big, headers={'idempotency-key': 'media-key-0001'})
        self.assertNotEqual(status, 413)  # reaches the domain, which rejects the incomplete upload
        self.assertEqual(self.call('POST', 'media', raw=b'{"contentBase64":"' + b'A' * 3100000 + b'"}')[0], 413)

    def test_agent_can_prepare_a_draft_but_not_approve_it(self):
        status, article, _ = self.call('POST', 'articles', {'key': 'noticia-um', 'data': ARTICLE}, headers={'idempotency-key': 'article-key-0001'})
        self.assertEqual((status, article['status']), (201, 'draft'))
        status, submission, _ = self.call('POST', 'submissions', {'records': [{'collection': 'content', 'id': article['id'], 'version': article['version']}]}, headers={'idempotency-key': 'submit-key-0001'})
        self.assertEqual((status, submission['status']), (201, 'pending'))
        self.assertEqual(self.call('POST', f"submissions/{submission['id']}/approve", {})[0], 401)
        self.assertEqual(self.call('GET', f"submissions/{submission['id']}")[1]['status'], 'pending')

    def test_infrastructure_failures_are_sanitized(self):
        def broken():
            raise RuntimeError('Server=PRIVATE-SENTINEL;Password=PRIVATE-SENTINEL')
        status, payload, headers = process('GET', 'schema', {}, {'authorization': 'Bearer x'}, b'', gateway_factory=broken)
        self.assertEqual((status, headers['Retry-After']), (503, '30'))
        self.assertNotIn('PRIVATE-SENTINEL', json.dumps(payload) + json.dumps(headers))

    def test_every_response_carries_no_store_and_no_cors(self):
        for status, payload, headers in (self.call('GET', 'schema'), self.call('GET', 'schema', key=False), self.call('GET', 'nope')):
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertFalse([name for name in headers if name.lower().startswith('access-control')])


class PackagingTest(unittest.TestCase):
    FILES = ('agent_api.py', 'core.py', 'commerce.py', 'storage.py')

    def test_flat_package_imports_without_the_repository_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in self.FILES:
                shutil.copy(CMS_DIR / name, folder)
            for name in ('content_api.py', 'function_app.py', 'host.json', 'requirements.txt'):
                shutil.copy(HERE / name, folder)
            # storage is imported lazily on the first request, so import it here too: a missing file must fail the test, not production
            targets = ['content_api', 'storage'] + (['function_app'] if importlib.util.find_spec('azure.functions') else [])
            code = '; '.join(f'import {target}' for target in targets) + '; print("ok")'
            # Only the package folder plus installed third-party libraries: the repository layout must not be needed.
            libraries = [entry for entry in sys.path if 'site-packages' in entry or 'pytestlib' in entry or entry.endswith(('.zip', 'DLLs')) or entry == str(Path(sys.executable).parent / 'Lib')]
            bootstrap = 'import sys; sys.path[:] = [sys.argv[1]] + sys.argv[2:] + [p for p in sys.path if "lib" in p.lower() and "site-packages" not in p.lower() and "AnderZilla" not in p]; ' + code
            run = subprocess.run([sys.executable, '-c', bootstrap, folder, *libraries], capture_output=True, text=True, timeout=60, cwd=folder)
            self.assertEqual((run.returncode, run.stdout.strip()), (0, 'ok'), run.stderr[-400:])

    def test_host_serves_routes_at_v1_without_the_api_prefix_and_requirements_are_pinned(self):
        host = json.loads((HERE / 'host.json').read_text(encoding='utf-8'))
        self.assertEqual(host['extensions']['http']['routePrefix'], '')
        lines = [line for line in (HERE / 'requirements.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertTrue(lines and all('==' in line for line in lines))
        self.assertFalse([line for line in lines if line.startswith(('google-auth', 'requests'))])  # worker OIDC is not part of this app


if __name__ == '__main__':
    unittest.main()
