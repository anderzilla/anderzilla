"""Corpus import: a tiny corpus must round-trip through the CMS exactly; the ForgeKit record must match the live web fallback."""
import base64
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from PIL import Image
from core import CMS
from import_corpus import FORGEKIT_LIVE, compare, import_corpus, rebuild_public
from storage import SQLiteStore


def webp(color):
    buffer = io.BytesIO()
    Image.new('RGB', (40, 30), color).save(buffer, format='WEBP')
    return buffer.getvalue()


class ImportCorpusTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        raw = webp((10, 90, 200))
        self.sha = hashlib.sha256(raw).hexdigest()
        (self.base / (self.sha + '.webp')).write_bytes(raw)
        self.public = {'enabled': True, 'releaseId': 'live-release', 'events': [], 'affiliates': [], 'offers': [], 'campaigns': [], 'pages': [], 'taxonomies': [], 'missions': [], 'rewards': [],
                       'media': [{'id': 'media-1', 'titlePT': 'capa', 'url': f'/media/{self.sha}.webp', 'mediaType': 'image', 'mimeType': 'image/webp', 'altPT': 'a', 'altEN': 'b', 'credit': 'c', 'license': 'd',
                                  'width': 40, 'height': 30, 'sourceUrl': 'https://example.com/foto', 'previewUrl': f'/media/{self.sha}-social.jpg'}],
                       'discoveries': [{'id': 'news-1', 'category': 'ia', 'titlePT': 'T', 'titleEN': 'T', 'summaryPT': 'R', 'summaryEN': 'S', 'sourceName': 'Fonte', 'url': 'https://example.com/n', 'published': '2026-09-10',
                                        'observed': '2026-09-17', 'fact': 'Corpo PT', 'factEN': 'Body EN', 'sources': [{'name': 'Fonte', 'url': 'https://example.com/n', 'publishedAt': '2026-09-10'}],
                                        'verifiedAt': '2026-09-10', 'slugPT': 'noticia', 'slugEN': 'news', 'coverMediaId': 'media-1', 'mediaIds': 'media-1', 'tags': '', 'isDemo': False,
                                        'updatedAt': '2026-10-27'},
                                       {'id': 'news-2', 'category': 'games', 'titlePT': 'T2', 'titleEN': 'T2', 'summaryPT': 'R', 'summaryEN': 'S', 'sourceName': 'Fonte', 'url': 'https://example.com/m', 'published': '2026-10-28',
                                        'observed': '2026-10-28', 'fact': 'Corpo 2', 'factEN': 'Body 2', 'sources': [], 'verifiedAt': '2026-10-28', 'slugPT': 'noticia-2', 'slugEN': 'news-2', 'isDemo': False}]}
        self.cms = CMS(SQLiteStore(self.base / 'cms.db'))

    def tearDown(self):
        self.temp.cleanup()

    def test_round_trip_is_identical_and_keeps_per_note_dates(self):
        self.assertEqual(import_corpus(self.cms, self.public, [self.base]), {'media': 1, 'content': 2, 'products': 1})
        produced = rebuild_public(self.cms, self.public)
        self.assertEqual(compare(self.public, produced), [])
        by_id = {row['id']: row for row in produced['discoveries']}
        self.assertEqual((by_id['news-1']['observed'], by_id['news-2']['observed']), ('2026-09-17', '2026-10-28'))  # not the release date
        self.assertEqual(by_id['news-1'].get('updatedAt'), '2026-10-27')
        self.assertNotIn('updatedAt', by_id['news-2'])  # a note without an editorial update date must not get one
        self.assertEqual([row['id'] for row in produced['products']], ['forgekit'])

    def test_compare_reports_real_differences(self):
        import_corpus(self.cms, self.public, [self.base])
        produced = rebuild_public(self.cms, self.public)
        produced['discoveries'][0]['titlePT'] = 'Alterado'
        self.assertTrue(any('fields differ' in line for line in compare(self.public, produced)))

    def test_import_rejects_tampered_or_missing_images(self):
        (self.base / (self.sha + '.webp')).write_bytes(webp((1, 1, 1)))
        with self.assertRaises(ValueError):
            import_corpus(self.cms, self.public, [self.base])
        with self.assertRaises(ValueError):
            import_corpus(CMS(SQLiteStore(self.base / 'other.db')), self.public, [self.base / 'nowhere'])
        self.assertEqual(self.cms.list({'id': 'a', 'roles': ['anderzilla_admin']}, 'content')['items'], [])  # nothing half-imported

    def test_approving_new_content_stamps_the_first_approval_date_once(self):
        admin = {'id': 'a', 'roles': ['anderzilla_admin']}
        record = self.cms.save(admin, 'content', {'titlePT': 'x', 'titleEN': 'x', 'summaryPT': 'x', 'summaryEN': 'x', 'bodyPT': 'x', 'bodyEN': 'x', 'category': 'ia', 'sourceName': 's', 'sourceUrl': 'https://example.com/x', 'publishedAt': '2026-10-29'})
        approved = self.cms.save(admin, 'content', None, record['id'], 1, 'approve')
        stamp = approved['data']['observedAt']
        edited = self.cms.save(admin, 'content', {**approved['data'], 'titlePT': 'y'}, record['id'], 2)
        again = self.cms.save(admin, 'content', None, record['id'], 3, 'approve')
        self.assertEqual((len(stamp), again['data']['observedAt']), (10, stamp))

    def test_forgekit_matches_the_live_web_fallback(self):
        source = (Path(__file__).resolve().parents[2] / 'apps/web/src/components/commerce/data.ts').read_text(encoding='utf-8')
        for key, value in FORGEKIT_LIVE.items():
            if key == 'disclosureKey':
                continue  # CMS-only requirement for active commercial records
            text = json.dumps(value, ensure_ascii=False)[1:-1].replace('\\"', '"') if isinstance(value, str) else str(value)
            self.assertIn(text, source, key)


if __name__ == '__main__':
    unittest.main()
