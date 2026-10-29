"""Draft package -> preview snapshot -> public data, using only local SQLite. No Azure, no build."""
import base64
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from PIL import Image
from agent_api import AgentGateway, handle
from core import CMS, Error
from import_snapshot import transform, write_assets
from storage import SQLiteStore

ADMIN = {'id': 'human-admin', 'name': 'Anderson', 'roles': ['anderzilla_admin']}


def png_b64():
    buffer = io.BytesIO()
    Image.new('RGB', (96, 64), (20, 80, 200)).save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


class PreviewSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.temp.name) / 'cms.db'))
        self.gateway = AgentGateway(self.cms, media_hosts=[])
        self.auth = 'Bearer ' + self.gateway.create_key(ADMIN, 'claude-test')['key']

    def tearDown(self):
        self.temp.cleanup()

    def call(self, method, path, body=None, idem=None, human=None):
        return handle(self.gateway, method, path, body, self.auth, human, idem)

    def seed_live_article(self):
        """One approved article, so the radar is never empty (transform refuses to empty it)."""
        record = self.cms.save(ADMIN, 'content', {'titlePT': 'No ar', 'titleEN': 'Live', 'summaryPT': 'R', 'summaryEN': 'S', 'bodyPT': 'Corpo', 'bodyEN': 'Body', 'category': 'ia',
                                                  'sourceName': 'Fonte', 'sourceUrl': 'https://example.com/live', 'publishedAt': '2026-10-01', 'slugPT': 'no-ar', 'slugEN': 'live'})
        self.cms.save(ADMIN, 'content', None, record['id'], 1, 'approve')

    def package(self):
        _, media = self.call('POST', '/v1/media', {'contentBase64': png_b64(), 'filename': 'b.png', 'altPT': 'Alt PT', 'altEN': 'Alt EN', 'credit': 'Autor', 'license': 'Autorizada', 'sourceUrl': 'https://example.com/foto'}, 'media-key-0001')
        _, banner = self.call('POST', '/v1/banners', {'key': 'banner-um', 'imageMediaId': media['id'], 'titlePT': 'Oferta', 'titleEN': 'Offer', 'textPT': 'Texto', 'textEN': 'Text', 'ctaPT': 'Ver', 'ctaEN': 'See',
                                                       'linkPT': '/pt/produtos/', 'linkEN': '/en/produtos/', 'startsAt': '2026-11-01T00:00:00+00:00', 'endsAt': '2026-11-07T00:00:00+00:00', 'order': 2, 'disclosure': 'PUBLICIDADE'}, 'banner-key-0001')
        _, article = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': {'titlePT': 'Nova', 'titleEN': 'New', 'summaryPT': 'R', 'summaryEN': 'S', 'bodyPT': 'Corpo', 'bodyEN': 'Body', 'category': 'games',
                                                                                  'sourceName': 'Fonte', 'sourceUrl': 'https://example.com/n', 'publishedAt': '2026-10-29', 'slugPT': 'nova', 'slugEN': 'new', 'coverMediaId': media['id']}}, 'article-key-0001')
        records = [{'collection': c, 'id': r['id'], 'version': r['version']} for c, r in (('media', media), ('banners', banner), ('content', article))]
        status, submission = self.call('POST', '/v1/submissions', {'records': records}, 'submit-key-0001')
        self.assertEqual(status, 201, submission)
        return media, banner, article, submission

    def test_preview_includes_drafts_but_changes_nothing(self):
        self.seed_live_article()
        media, banner, article, submission = self.package()
        snapshot = self.gateway.preview_snapshot(ADMIN, submission['id'])
        public = transform(snapshot)
        self.assertEqual({row['titlePT'] for row in public['discoveries']}, {'No ar', 'Nova'})
        self.assertEqual(len(public['banners']), 1)
        shown = public['banners'][0]
        self.assertEqual((shown['image'], shown['startsAt'], shown['endsAt'], shown['link']['pt'], shown['disclosure'], shown['imageAlt']['en']),
                         (media['data']['url'], '2026-11-01', '2026-11-07', '/pt/produtos/', 'PUBLICIDADE', 'Alt EN'))
        self.assertTrue(snapshot['releaseId'].startswith('preview-'))
        with tempfile.TemporaryDirectory() as folder:
            write_assets(snapshot, Path(folder))
            self.assertEqual(len(list((Path(folder) / 'media').glob('*.webp'))), 1)
        # drafts stay drafts, there is no release, and the live snapshot is unchanged
        self.assertEqual({row['status'] for row in self.cms.list(ADMIN, 'banners')['items']}, {'draft'})
        self.assertEqual(self.cms.releases(ADMIN)['items'], [])
        with self.cms.store.transaction() as db:
            live = transform(self.cms.snapshot(db))
        self.assertEqual((len(live['discoveries']), live['banners']), (1, []))

    def test_preview_refuses_an_invalid_package(self):
        self.seed_live_article()
        _, art = self.call('POST', '/v1/articles', {'key': 'noticia-um', 'data': {'titlePT': 'Incompleta'}}, 'article-key-0002')
        _, submission = self.call('POST', '/v1/submissions', {'records': [{'collection': 'content', 'id': art['id'], 'version': art['version']}]}, 'submit-key-0002')
        with self.assertRaises(Error) as caught:
            self.gateway.preview_snapshot(ADMIN, submission['id'])
        self.assertEqual(caught.exception.code, 'incomplete_record')

    def test_banner_without_approved_image_is_not_publishable(self):
        self.seed_live_article()
        snapshot = {'schemaVersion': 1, 'createdAt': '2026-10-29T00:00:00Z', 'releaseId': 'x', 'collections': {
            'content': [{'id': 'a', 'status': 'approved', 'data': {'titlePT': 'a', 'titleEN': 'a', 'summaryPT': 'a', 'summaryEN': 'a', 'category': 'ia', 'sourceUrl': 'https://example.com/a', 'publishedAt': '2026-10-01'}}],
            'banners': [{'id': 'b', 'status': 'approved', 'data': {'titlePT': 'a', 'titleEN': 'a', 'imageMediaId': 'missing', 'linkPT': '/pt/', 'linkEN': '/en/', 'startsAt': '2026-11-01T00:00:00+00:00'}}]}}
        with self.assertRaises(ValueError):
            transform(snapshot)

    def test_human_review_endpoints(self):
        media, banner, article, submission = self.package()
        sid = submission['id']
        self.assertEqual(self.call('GET', '/v1/submissions', human=None)[0], 401)
        status, listed = self.call('GET', '/v1/submissions', human=ADMIN)
        self.assertEqual((status, [row['id'] for row in listed['items']]), (200, [sid]))
        status, detail = self.call('GET', f'/v1/submissions/{sid}/items', human=ADMIN)
        self.assertEqual(status, 200)
        by_collection = {row['collection']: row for row in detail['items']}
        self.assertTrue(by_collection['media']['data']['imageDataUrl'].startswith('data:image/webp;base64,'))
        self.assertNotIn('assetBase64', by_collection['media']['data'])
        self.assertEqual(self.call('GET', f'/v1/submissions/{sid}/items')[0], 401)  # an agent key is not a human
        self.assertEqual(self.call('POST', f'/v1/submissions/{sid}/preview', human=ADMIN)[0], 501)  # no previewer configured


if __name__ == '__main__':
    unittest.main()
