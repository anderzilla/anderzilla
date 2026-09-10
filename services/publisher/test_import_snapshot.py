"""Security and publication contract checks using explicitly labelled CMS demos."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from import_snapshot import transform, write_assets
from seed_examples import examples


def snapshot():
    collections = {}
    for collection, record_id, data in examples():
        collections.setdefault(collection, []).append({'id': record_id, 'version': 1, 'status': 'approved', 'data': data})
    return {'schemaVersion': 1, 'createdAt': '2026-09-10T12:00:00Z', 'releaseId': 'test-release', 'collections': collections}


class ImportSnapshotTests(unittest.TestCase):
    def test_newsroom_sources_export_allowlist_and_https(self):
        value = snapshot()
        data = value['collections']['content'][0]['data']
        data['sources'] = json.dumps([{'name':'Official','url':'https://example.com/news','private':'do-not-publish'}])
        data['socialWhatsappPT'] = 'Leia a apuração'
        row = transform(value)['discoveries'][0]
        self.assertEqual(row['sources'], [{'name':'Official','url':'https://example.com/news'}])
        self.assertEqual(row['socialWhatsappPT'], 'Leia a apuração')
        data['sources'] = json.dumps([{'name':'Private','url':'https://127.0.0.1/news'}])
        with self.assertRaises(ValueError):
            transform(value)

    def test_content_formatting_localized_seo_and_gallery_preserved(self):
        value = snapshot()
        published = transform(value)
        self.assertEqual(len(published['discoveries']), 6)
        self.assertEqual({row['category'] for row in published['discoveries']}, {'games', 'consoles', 'celulares', 'ia', 'gadgets', 'curiosidades'})
        for original, actual in zip(value['collections']['content'], published['discoveries']):
            self.assertEqual(actual['fact'], original['data']['bodyPT'])
            self.assertEqual(actual['factEN'], original['data']['bodyEN'])
            for key in ('slugPT', 'slugEN', 'seoTitlePT', 'seoTitleEN', 'seoDescriptionPT', 'seoDescriptionEN', 'author', 'coverMediaId', 'isDemo', 'tags', 'mediaIds'):
                if key in original['data']:
                    self.assertEqual(actual[key], original['data'][key])

    def test_no_private_fields_or_base64_in_public_json(self):
        value = snapshot()
        for records in value['collections'].values():
            for row in records:
                row['data']['internalNote'] = 'PRIVATE-SENTINEL'
        text = json.dumps(transform(value))
        for field in ('assetBase64', 'assetSha256', 'approvalReference', 'internalNote', 'PRIVATE-SENTINEL'):
            self.assertNotIn(field, text)

    def test_real_rewards_and_unknown_collection_rejected(self):
        value = snapshot()
        value['collections']['rewards'][0]['data']['isDemo'] = False
        with self.assertRaises(ValueError):
            transform(value)
        value = snapshot()
        value['collections']['wallets'] = []
        with self.assertRaises(ValueError):
            transform(value)

    def test_draft_and_deleted_cover_rejected(self):
        value = snapshot()
        value['collections']['media'][0]['status'] = 'draft'
        with self.assertRaises(ValueError):
            transform(value)
        value = snapshot()
        value['collections']['media'] = []
        with self.assertRaises(ValueError):
            transform(value)

    def test_deleted_gallery_reference_rejected(self):
        value = snapshot()
        value['collections']['content'][0]['data']['mediaIds'] = 'deleted-media-id'
        with self.assertRaises(ValueError):
            transform(value)

    def test_deleted_tag_reference_rejected(self):
        value = snapshot()
        value['collections']['taxonomies'] = []
        with self.assertRaises(ValueError):
            transform(value)

    def test_local_media_path_without_verified_asset_rejected(self):
        value = snapshot()
        data = value['collections']['media'][0]['data']
        data.pop('assetBase64')
        data['url'] = '/media/../../private.txt'
        with self.assertRaises(ValueError):
            transform(value)

    def test_private_network_urls_rejected(self):
        for url in ('https://192.168.1.1/file', 'https://10.0.0.1/file', 'https://[::1]/file', 'https://internal.local/file'):
            value = snapshot()
            value['collections']['content'][0]['data']['sourceUrl'] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                transform(value)

    def test_asset_materializes_only_hash_named_webp(self):
        value = snapshot()
        data = value['collections']['media'][0]['data']
        with tempfile.TemporaryDirectory() as folder:
            write_assets(value, Path(folder))
            actual = (Path(folder) / 'media' / (data['assetSha256'] + '.webp')).read_bytes()
            self.assertEqual(hashlib.sha256(actual).hexdigest(), data['assetSha256'])

    def test_asset_hash_and_traversal_rejected(self):
        for field, replacement in [('assetSha256', '0' * 64), ('url', '/media/../../escape.webp')]:
            value = snapshot()
            value['collections']['media'][0]['data'][field] = replacement
            with tempfile.TemporaryDirectory() as folder, self.subTest(field=field), self.assertRaises(ValueError):
                write_assets(value, Path(folder))

    def test_fake_webp_header_rejected(self):
        value = snapshot()
        raw = b'RIFF\x00\x00\x00\x00WEBPnot-an-image'
        sha = hashlib.sha256(raw).hexdigest()
        value['collections']['media'][0]['data'].update(assetBase64=base64.b64encode(raw).decode(), assetSha256=sha, url='/media/' + sha + '.webp')
        with tempfile.TemporaryDirectory() as folder, self.assertRaises((ValueError, OSError)):
            write_assets(value, Path(folder))


if __name__ == '__main__':
    unittest.main()
