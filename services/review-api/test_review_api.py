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
from agent_api import AgentGateway, handle
from core import CMS
from review_api import MAX_JSON_BYTES, process, process_roles, same_origin, swa_principal
from storage import SQLiteStore

ADMIN = {'id': 'seed-admin', 'name': 'seed', 'roles': ['anderzilla_admin']}
HOST = 'anderzilla-review-homolog.azurestaticapps.net'
ARTICLE = {'titlePT': 'T', 'titleEN': 'T', 'summaryPT': 'R', 'summaryEN': 'S', 'bodyPT': 'C', 'bodyEN': 'B', 'category': 'ia', 'sourceName': 'Fonte',
           'sourceUrl': 'https://example.com/n', 'publishedAt': '2026-10-29', 'slugPT': 'noticia', 'slugEN': 'news'}


def principal(roles=('authenticated', 'anderzilla_admin'), user='user-1'):
    return base64.b64encode(json.dumps({'userId': user, 'userDetails': 'anderzilla@ymail.com', 'userRoles': list(roles)}).encode()).decode()


class ReviewApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.gateway = AgentGateway(CMS(SQLiteStore(Path(self.temp.name) / 'cms.db')), media_hosts=[])
        self.agent = 'Bearer ' + self.gateway.create_key(ADMIN, 'claude-test')['key']

    def tearDown(self):
        self.temp.cleanup()

    def call(self, method, path, body=None, headers=None, raw=None):
        h = {'content-type': 'application/json', 'host': HOST, **(headers or {})}
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else b'')
        return process(method, path, {}, h, data, gateway_factory=lambda: self.gateway)

    def human(self, method, path, body=None, **extra):
        return self.call(method, path, body, headers={'x-ms-client-principal': principal(), **extra})

    def package(self):
        agent = {'id': 'agent:test', 'name': 'test', 'roles': ['anderzilla_agent'], 'kind': 'agent', 'scopes': ['content', 'media', 'banners']}
        record = self.gateway.upsert(agent, 'content', {'key': 'noticia-um', 'data': ARTICLE}, 'article-key-0001')
        return self.gateway.create_submission(agent, {'note': 'teste', 'records': [{'collection': 'content', 'id': record['id'], 'version': record['version']}]}, 'submit-key-0001')

    def test_health_is_public_and_needs_no_database(self):
        def forbidden():
            raise AssertionError('no database for health')
        self.assertEqual(process('GET', 'health', {}, {}, b'', gateway_factory=forbidden)[:2], (200, {'status': 'ok'}))

    def test_identity_comes_only_from_a_valid_swa_principal(self):
        self.assertEqual(self.call('GET', 'submissions')[0], 401)
        for bad in ('not-base64!!', principal(roles=('anonymous',)), principal(roles=('anderzilla_admin',)), base64.b64encode(b'{"userId":"x","userRoles":"authenticated"}').decode(),
                    base64.b64encode(b'[]').decode(), principal(user='')):
            status, payload, _ = self.call('GET', 'submissions', headers={'x-ms-client-principal': bad})
            self.assertEqual(status, 401, bad[:30])
        status, payload, _ = self.call('GET', 'submissions', headers={'x-ms-client-principal': principal(roles=('authenticated', 'anderzilla_editor'))})
        self.assertEqual(status, 403)  # signed in but not an admin
        self.assertEqual(self.human('GET', 'submissions')[0], 200)
        self.assertIsNone(swa_principal(None))

    def test_agent_keys_are_never_accepted_here(self):
        package = self.package()
        self.assertEqual(self.call('GET', 'schema', headers={'authorization': self.agent})[0], 401)
        self.assertEqual(self.call('POST', 'articles', {'key': 'x', 'data': ARTICLE}, headers={'authorization': self.agent, 'idempotency-key': 'abcdefgh1'})[0], 401)
        self.assertEqual(self.call('GET', 'submissions', headers={'authorization': self.agent})[0], 401)  # a key does not make a human
        self.assertEqual(self.call('POST', f"submissions/{package['id']}/approve", {}, headers={'authorization': self.agent})[0], 401)

    def test_full_human_review_loop(self):
        package = self.package()
        sid = package['id']
        status, listed, _ = self.human('GET', 'submissions')
        self.assertEqual((status, [row['id'] for row in listed['items']]), (200, [sid]))
        status, detail, _ = self.human('GET', f'submissions/{sid}/items')
        self.assertEqual((status, detail['items'][0]['collection']), (200, 'content'))
        record_id = detail['items'][0]['id']
        status, comment, _ = self.human('POST', f'submissions/{sid}/comments', {'collection': 'content', 'recordId': record_id, 'field': 'titlePT', 'text': 'Encurte o título.'})
        self.assertEqual(status, 201)
        self.assertEqual(self.human('POST', f'submissions/{sid}/request-changes', {})[1]['status'], 'changes_requested')
        # the agent fixes and resubmits, the human approves
        agent = {'id': package['agentId'], 'name': 'test', 'roles': ['anderzilla_agent'], 'kind': 'agent', 'scopes': ['content', 'media', 'banners']}
        fixed = self.gateway.upsert(agent, 'content', {'key': 'noticia-um', 'version': 1, 'data': {**ARTICLE, 'titlePT': 'Curto'}}, 'article-key-0002')
        self.gateway.resubmit(agent, sid, {'answeredCommentIds': [comment['id']], 'records': [{'collection': 'content', 'id': fixed['id'], 'version': fixed['version']}]}, 'resubmit-key-01')
        status, release, _ = self.human('POST', f'submissions/{sid}/approve', {})
        self.assertEqual((status, release['status']), (202, 'queued'))
        self.assertEqual(self.human('GET', f"releases/{release['id']}")[1]['status'], 'queued')
        self.assertEqual(self.human('POST', 'releases/x/promote', {})[0], 501)

    def test_preview_is_reported_as_not_configured_instead_of_failing(self):
        package = self.package()
        status, payload, _ = self.human('POST', f"submissions/{package['id']}/preview", {})
        self.assertEqual((status, payload['error']['code']), (501, 'not_implemented'))
        self.assertEqual(self.human('GET', f"submissions/{package['id']}/preview")[0], 501)

    def test_cross_site_requests_cannot_ride_the_session_cookie(self):
        package = self.package()
        path = f"submissions/{package['id']}/request-changes"
        self.assertEqual(self.human('POST', path, {}, origin='https://evil.example.com')[0], 403)
        self.assertEqual(self.human('POST', path, {}, origin='https://' + HOST)[0], 422)  # same origin passes the check; no comment yet
        self.assertEqual(self.call('POST', path, raw=b'x', headers={'x-ms-client-principal': principal(), 'content-type': 'text/plain'})[0], 415)
        self.assertEqual(self.call('POST', path, raw=b'{}', headers={'x-ms-client-principal': principal(), 'content-type': 'application/x-www-form-urlencoded'})[0], 415)
        self.assertEqual(self.human('GET', 'submissions', origin='https://evil.example.com')[0], 200)  # reads carry no side effects and the response has no CORS headers
        self.assertTrue(same_origin({'origin': 'https://a.example'}, allowed='https://a.example'))
        self.assertFalse(same_origin({'origin': 'https://b.example'}, allowed='https://a.example'))
        self.assertTrue(same_origin({}))

    def test_request_limits_and_methods(self):
        signed_in = {'x-ms-client-principal': principal()}
        self.assertEqual(self.call('POST', 'submissions/x/comments', raw=b'x' * (MAX_JSON_BYTES + 1), headers=signed_in)[0], 413)
        self.assertEqual(self.call('POST', 'submissions/x/comments', raw=b'{bad', headers=signed_in)[0], 400)
        self.assertEqual(self.call('POST', 'submissions/x/comments', raw=b'[]', headers=signed_in)[0], 422)
        self.assertEqual(self.call('PUT', 'submissions', {}, headers={'x-ms-client-principal': principal()})[0], 405)
        self.assertEqual(self.human('GET', 'nope')[0], 404)

    def test_headers_and_sanitized_failures(self):
        for status, payload, headers in (self.human('GET', 'submissions'), self.call('GET', 'submissions')):
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertFalse([name for name in headers if name.lower().startswith('access-control')])

        def broken():
            raise RuntimeError('Server=PRIVATE-SENTINEL;Password=PRIVATE-SENTINEL')
        status, payload, headers = process('GET', 'submissions', {}, {'x-ms-client-principal': principal()}, b'', gateway_factory=broken)
        self.assertEqual((status, headers['Retry-After']), (503, '30'))
        self.assertNotIn('PRIVATE-SENTINEL', json.dumps(payload) + json.dumps(headers))


class RoleSourceTest(unittest.TestCase):
    OWNER = 'aad:419850329e1c4dcd9a440a2d94fcb131'

    def roles(self, body, allowed=OWNER):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        status, payload, headers = process_roles(raw, {'REVIEW_ADMIN_USER_IDS': allowed})
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        return payload['roles']

    def test_only_the_listed_provider_and_user_id_get_the_admin_role(self):
        self.assertEqual(self.roles({'identityProvider': 'aad', 'userId': '419850329e1c4dcd9a440a2d94fcb131'}), ['anderzilla_admin'])
        self.assertEqual(self.roles({'identityProvider': 'aad', 'userId': '00000000000000000000000000000000'}), [])
        self.assertEqual(self.roles({'identityProvider': 'github', 'userId': '419850329e1c4dcd9a440a2d94fcb131'}), [])  # same id, other provider

    def test_the_email_and_claims_never_grant_anything(self):
        body = {'identityProvider': 'aad', 'userId': 'ffffffffffffffffffffffffffffffff', 'userDetails': 'anderzilla@ymail.com',
                'claims': [{'typ': 'preferred_username', 'val': 'anderzilla@ymail.com'}, {'typ': 'roles', 'val': 'anderzilla_admin'}]}
        self.assertEqual(self.roles(body), [])
        self.assertEqual(self.roles({**body, 'userId': '419850329e1c4dcd9a440a2d94fcb131'}), ['anderzilla_admin'])  # the id decides, extras are ignored

    def test_malformed_input_and_empty_allow_list_fail_closed_with_200(self):
        for bad in (b'', b'not json', b'[]', b'{"identityProvider": 1, "userId": 2}', b'{"identityProvider": "aad"}', b'\xff\xfe'):
            self.assertEqual(self.roles(bad), [], bad)
        for empty in ('', '   ', ',,', 'aad:short', 'AAD:419850329e1c4dcd9a440a2d94fcb131', 'aad:419850329e1c4dcd9a440a2d94fcb131 extra'):
            self.assertEqual(self.roles({'identityProvider': 'aad', 'userId': '419850329e1c4dcd9a440a2d94fcb131'}, allowed=empty), [], empty)
        self.assertEqual(process_roles(b'{}', {})[1], {'roles': []})  # setting absent

    def test_allow_list_parsing_keeps_valid_entries_and_drops_the_rest(self):
        from review_api import admin_allowlist
        value = ' aad:419850329e1c4dcd9a440a2d94fcb131 , bad entry, github:12345678 ,, aad:x '
        self.assertEqual(admin_allowlist(value), {'aad:419850329e1c4dcd9a440a2d94fcb131', 'github:12345678'})
        self.assertEqual(admin_allowlist(None), set())

    def test_the_site_config_declares_the_role_source_and_keeps_everything_else_closed(self):
        config = json.loads((HERE.parent.parent / 'apps' / 'review' / 'public' / 'staticwebapp.config.json').read_text(encoding='utf-8'))
        self.assertEqual(config['auth']['rolesSource'], '/api/GetRoles')
        anonymous = [route['route'] for route in config['routes'] if 'anonymous' in route.get('allowedRoles', [])]
        self.assertEqual(anonymous, ['/.auth/*'])  # the role function must not be reachable anonymously
        catch_all = next(route for route in config['routes'] if route['route'] == '/*')
        self.assertEqual(catch_all['allowedRoles'], ['anderzilla_admin'])


class PackagingTest(unittest.TestCase):
    def test_flat_package_imports_without_the_repository_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ('agent_api.py', 'core.py', 'commerce.py', 'storage.py'):
                shutil.copy(CMS_DIR / name, folder)
            for name in ('review_api.py', 'function_app.py', 'host.json', 'requirements.txt'):
                shutil.copy(HERE / name, folder)
            targets = ['review_api', 'storage'] + (['function_app'] if importlib.util.find_spec('azure.functions') else [])
            libraries = [entry for entry in sys.path if 'site-packages' in entry or 'pytestlib' in entry or entry.endswith(('.zip', 'DLLs')) or entry == str(Path(sys.executable).parent / 'Lib')]
            bootstrap = 'import sys; sys.path[:] = [sys.argv[1]] + sys.argv[2:] + [p for p in sys.path if "lib" in p.lower() and "site-packages" not in p.lower() and "AnderZilla" not in p]; ' + '; '.join(f'import {t}' for t in targets) + '; print("ok")'
            run = subprocess.run([sys.executable, '-c', bootstrap, folder, *libraries], capture_output=True, text=True, timeout=60, cwd=folder)
            self.assertEqual((run.returncode, run.stdout.strip()), (0, 'ok'), run.stderr[-400:])

    def test_host_keeps_the_api_prefix_and_requirements_are_pinned(self):
        host = json.loads((HERE / 'host.json').read_text(encoding='utf-8'))
        self.assertNotIn('extensions', host)  # SWA serves managed functions under /api
        lines = [line for line in (HERE / 'requirements.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertTrue(lines and all('==' in line for line in lines))


if __name__ == '__main__':
    unittest.main()
