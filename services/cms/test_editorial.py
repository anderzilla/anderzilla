import base64
import io
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from core import CMS, Error, validate
from storage import SQLiteStore
from seed_examples import seed

ADMIN = {'id': 'admin', 'roles': ['anderzilla_admin']}


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.temp.name) / 'test.sqlite'))

    def tearDown(self):
        self.temp.cleanup()

    def approve(self, collection, row):
        return self.cms.save(ADMIN, collection, None, row['id'], row['version'], 'approve')

    def upload(self):
        output = io.BytesIO()
        Image.new('RGB', (1700, 50), '#ff0011').save(output, format='PNG')
        return self.cms.upload_media(ADMIN, {'filename': 'sample.png', 'contentBase64': base64.b64encode(output.getvalue()).decode(), 'altPT': 'Imagem de teste', 'altEN': 'Test image', 'credit': 'Test', 'license': 'Own test fixture'})

    def test_upload_normalizes_and_protects_asset(self):
        row = self.upload()
        self.assertEqual(row['status'], 'draft')
        self.assertEqual(row['data']['width'], 1600)
        self.assertEqual(row['data']['mimeType'], 'image/webp')
        image = Image.open(io.BytesIO(base64.b64decode(row['data']['assetBase64'])))
        self.assertFalse(image.getexif())
        data = {key: value for key, value in row['data'].items() if key not in {'assetBase64', 'assetSha256', 'mimeType'}}
        changed = self.cms.save(ADMIN, 'media', data, row['id'], 1)
        self.assertEqual(changed['data']['assetBase64'], row['data']['assetBase64'])
        with self.assertRaises(Error):
            self.cms.save(ADMIN, 'media', {**changed['data'], 'assetSha256': 'forged'}, row['id'], 2)

    def test_bad_upload_and_role_rejected(self):
        with self.assertRaises(Error):
            self.cms.upload_media(ADMIN, {'contentBase64': 'not-an-image'})
        with self.assertRaises(Error):
            self.cms.upload_media({'id': 'reader', 'roles': ['authenticated']}, {})
        with self.assertRaises(Error):
            self.cms.save(ADMIN, 'media', {'assetBase64': 'forged'})

    def test_media_reference_rechecked_when_archived(self):
        media = self.approve('media', self.upload())
        page = self.cms.save(ADMIN, 'pages', {'titlePT': 'Page', 'slugPT': 'page', 'bodyPT': 'Body', 'coverMediaId': media['id']})
        self.approve('pages', page)
        self.cms.save(ADMIN, 'media', None, media['id'], media['version'], 'archive')
        with self.assertRaises(Error):
            self.cms.release(ADMIN, 'release-invalid-cover')

    def test_tags_and_local_urls_rejected(self):
        page = self.cms.save(ADMIN, 'pages', {'titlePT': 'Page', 'slug': 'page', 'bodyPT': 'Body', 'tags': 'missing-id'})
        with self.assertRaises(Error):
            self.approve('pages', page)
        for url in ['https://127.0.0.1/a', 'https://localhost/a', 'https://192.168.0.1/a']:
            with self.assertRaises(Error):
                validate('media', {'url': url})

    def test_demo_seed_idempotent_and_no_real_rewards_exported(self):
        self.assertEqual(seed(self.cms.store, approved=True), 15)
        self.assertEqual(seed(self.cms.store, approved=True), 0)
        real = self.cms.save(ADMIN, 'rewards', {'titlePT': 'Private real definition', 'points': 200, 'category': 'gadgets', 'regions': 'BR', 'termsPT': 'Not funded', 'isDemo': False})
        self.approve('rewards', real)
        release = self.cms.release(ADMIN, 'demo-seed-release')
        snapshot = self.cms.releases(ADMIN, release['id'], True)
        self.assertEqual(len(snapshot['collections']['rewards']), 1)
        self.assertTrue(snapshot['collections']['rewards'][0]['data']['isDemo'])
        self.assertNotIn('approvalReference', snapshot['collections']['affiliates'][0]['data'])

    def test_duplicate_locale_slug(self):
        data = {'titlePT': 'Page', 'slugPT': 'unique', 'bodyPT': 'Body'}
        self.approve('pages', self.cms.save(ADMIN, 'pages', data))
        with self.assertRaises(Error):
            self.approve('pages', self.cms.save(ADMIN, 'pages', data))


if __name__ == '__main__':
    unittest.main()
