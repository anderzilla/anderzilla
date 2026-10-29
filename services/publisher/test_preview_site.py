"""PreviewBuilder and the local review server, with a fake site build (the real build is exercised by hand)."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from agent_api import AgentGateway
from core import CMS, Error
from preview_site import PreviewBuilder
from storage import SQLiteStore
import review_local

ADMIN = {'id': 'human-admin', 'name': 'Anderson', 'roles': ['anderzilla_admin']}
TOKEN = 'x' * 40


def fake_build(root, directory, snapshot, marker):
    (directory / 'out').mkdir(parents=True)
    (directory / 'out' / 'index.html').write_text('<h1>preview ' + snapshot['releaseId'] + '</h1>', encoding='utf-8')
    return directory / 'out'


class PreviewSiteTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_builder_states_and_failure(self):
        builder = PreviewBuilder(self.base / 'previews', builder=fake_build, synchronous=True)
        self.assertEqual(builder.state('abc-1'), {'state': 'none'})
        # staging_directory lives under the repo; the fake build only needs a writable directory
        builder.start(lambda: {'releaseId': 'preview-abc-1-r1'}, 'abc-1')
        state = builder.state('abc-1')
        self.assertEqual((state['state'], state['active'], state['round']), ('ready', True, '1'))
        self.assertIn('preview-abc-1-r1', (builder.active_directory() / 'index.html').read_text(encoding='utf-8'))

        def invalid():
            raise Error(422, 'incomplete_record', 'Preencha: bodyEN')
        builder.start(invalid, 'abc-2')
        self.assertEqual((builder.state('abc-2')['state'], builder.state('abc-2')['code']), ('failed', 'incomplete_record'))
        with self.assertRaises(Error):
            builder.activate('abc-2')
        with self.assertRaises(Error):
            builder.state('../evil') and builder._path('../evil')

    def test_local_server_requires_token_and_host_and_serves_preview(self):
        builder = PreviewBuilder(self.base / 'previews', builder=fake_build, synchronous=True)
        ui = self.base / 'ui'
        ui.mkdir()
        (ui / 'index.html').write_text('<title>review</title>', encoding='utf-8')
        api, preview = review_local.make_servers(self.base / 'cms.db', TOKEN, self.base / 'previews', ui_dir=ui, builder=builder)
        for server in (api, preview):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: [s.shutdown() for s in (api, preview)])
        base = f'http://127.0.0.1:{review_local.API_PORT}'

        def get(url, token=TOKEN, method='GET', data=None):
            headers = {'Authorization': 'Bearer ' + token} if token else {}
            request = Request(url, headers=headers, method=method, data=json.dumps(data).encode() if data is not None else None)
            try:
                with urlopen(request, timeout=10) as response:
                    return response.status, response.read().decode()
            except HTTPError as error:
                return error.code, error.read().decode()

        self.assertEqual(get(base + '/v1/submissions', token=None)[0], 401)
        self.assertEqual(get(base + '/v1/submissions', token='wrong' * 8)[0], 401)
        self.assertEqual(json.loads(get(base + '/v1/submissions')[1]), {'items': []})
        status, html = get(base + '/', token=None)  # UI is public static code, no data
        self.assertEqual((status, html), (200, '<title>review</title>'))
        self.assertEqual(get(base + '/../../etc/passwd', token=None)[0], 404)
        # preview of a real package through the API
        from agent_api import handle
        cms = CMS(SQLiteStore(self.base / 'cms.db'))
        gateway = AgentGateway(cms, media_hosts=[])
        auth = 'Bearer ' + gateway.create_key(ADMIN, 'claude-test')['key']
        article = {'titlePT': 'Nova', 'titleEN': 'New', 'summaryPT': 'R', 'summaryEN': 'S', 'bodyPT': 'C', 'bodyEN': 'B', 'category': 'games',
                   'sourceName': 'Fonte', 'sourceUrl': 'https://example.com/n', 'publishedAt': '2026-10-29', 'slugPT': 'nova', 'slugEN': 'new'}
        _, saved = handle(gateway, 'POST', '/v1/articles', {'key': 'noticia-um', 'data': article}, auth, None, 'article-key-0001')
        _, submission = handle(gateway, 'POST', '/v1/submissions', {'records': [{'collection': 'content', 'id': saved['id'], 'version': saved['version']}]}, auth, None, 'submit-key-0001')
        sid = submission['id']
        self.assertEqual(get(f'http://127.0.0.1:{review_local.PREVIEW_PORT}/')[0], 404)  # nothing active yet
        self.assertEqual(get(f'{base}/v1/submissions/{sid}/preview', method='POST', data={})[0], 202)
        self.assertEqual(json.loads(get(f'{base}/v1/submissions/{sid}/preview')[1])['state'], 'ready')
        status, html = get(f'http://127.0.0.1:{review_local.PREVIEW_PORT}/', token=None)
        self.assertEqual((status, html), (200, f'<h1>preview preview-{sid}-r1</h1>'))
        self.assertEqual(get(f'http://127.0.0.1:{review_local.PREVIEW_PORT}/..%2f..%2fcms.db', token=None)[0], 404)
        # Next.js chunk names contain brackets and arrive percent-encoded
        folder = builder.active_directory() / '_next' / 'static' / 'chunks' / 'app' / '[lang]'
        folder.mkdir(parents=True)
        (folder / 'page.js').write_text('ok', encoding='utf-8')
        self.assertEqual(get(f'http://127.0.0.1:{review_local.PREVIEW_PORT}/_next/static/chunks/app/%5Blang%5D/page.js', token=None), (200, 'ok'))
        self.assertEqual(self.cms_statuses(cms), {'draft'})  # building a preview approves nothing

    @staticmethod
    def cms_statuses(cms):
        return {row['status'] for row in cms.list(ADMIN, 'content')['items']}


if __name__ == '__main__':
    unittest.main()
