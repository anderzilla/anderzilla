"""Release snapshots reference images instead of embedding them (writing ~21 MiB per release took ~2 minutes on Azure SQL)."""
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from core import CMS, Error, hydrate_assets
from storage import SQLiteStore

ADMIN = {'id': 'test-admin', 'name': 'Test', 'roles': ['anderzilla_admin']}


def upload(cms, color):
    buffer = io.BytesIO()
    Image.new('RGB', (64, 48), color).save(buffer, format='PNG')
    record = cms.upload_media(ADMIN, {'filename': 'x.png', 'contentBase64': base64.b64encode(buffer.getvalue()).decode(), 'altPT': 'a', 'altEN': 'b', 'credit': 'c', 'license': 'd'})
    return cms.save(ADMIN, 'media', None, record['id'], 1, 'approve')


class ReleaseAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.temp.name) / 'cms.db'))

    def tearDown(self):
        self.temp.cleanup()

    def test_release_snapshot_keeps_hashes_but_not_image_bytes(self):
        media = upload(self.cms, (10, 20, 30))
        external = self.cms.save(ADMIN, 'media', {'url': 'https://example.com/a.png', 'altPT': 'a', 'altEN': 'b', 'credit': 'c', 'license': 'd', 'mediaType': 'image', 'width': 10, 'height': 10})
        self.cms.save(ADMIN, 'media', None, external['id'], 1, 'approve')
        release = self.cms.release(ADMIN, 'release-assets-key')
        snapshot = self.cms.releases(ADMIN, release['id'], True)
        rows = {row['id']: row['data'] for row in snapshot['collections']['media']}
        self.assertNotIn('assetBase64', rows[media['id']])
        self.assertEqual((rows[media['id']]['assetSha256'], rows[media['id']]['url']), (media['data']['assetSha256'], media['data']['url']))
        self.assertNotIn('omitted', json.dumps(snapshot))  # the placeholder never leaks
        self.assertEqual(rows[external['id']]['url'], 'https://example.com/a.png')  # external media is untouched, no asset fields invented
        self.assertNotIn('assetBase64', rows[external['id']])
        self.assertEqual(snapshot['assets'], 'by-reference')
        self.assertLess(len(json.dumps(snapshot)), 5000)

    def test_hydrate_restores_verified_bytes_and_rejects_a_mismatch(self):
        media = upload(self.cms, (200, 10, 10))
        release = self.cms.release(ADMIN, 'release-hydrate-key')
        snapshot = self.cms.releases(ADMIN, release['id'], True)
        with self.cms.store.transaction() as db:
            hydrate_assets(db, snapshot)
        restored = snapshot['collections']['media'][0]['data']
        self.assertEqual(restored['assetBase64'], media['data']['assetBase64'])
        # a snapshot that claims another hash must be refused instead of building the site from different bytes
        tampered = self.cms.releases(ADMIN, release['id'], True)
        tampered['collections']['media'][0]['data']['assetSha256'] = '0' * 64
        with self.cms.store.transaction() as db:
            with self.assertRaises(ValueError):
                hydrate_assets(db, tampered)

    def test_full_snapshot_still_includes_assets_for_previews_and_parity_builds(self):
        media = upload(self.cms, (1, 2, 3))
        with self.cms.store.transaction() as db:
            full = self.cms.snapshot(db)
            light = self.cms.snapshot(db, include_assets=False)
        self.assertEqual(full['collections']['media'][0]['data']['assetBase64'], media['data']['assetBase64'])
        self.assertEqual(full['assets'], 'included')
        self.assertNotIn('assetBase64', light['collections']['media'][0]['data'])

    def test_light_reads_do_not_change_stored_records(self):
        media = upload(self.cms, (5, 6, 7))
        with self.cms.store.transaction() as db:
            light = db.records('media', light=True)[0]
            self.assertEqual(light['data']['assetBase64'], 'omitted')
            self.assertEqual(db.record('media', media['id'])['data']['assetBase64'], media['data']['assetBase64'])
            self.assertEqual(db.media_asset(media['id']), media['data']['assetBase64'])
            self.assertIsNone(db.media_asset('nonexistent'))
            self.assertEqual(db.media_assets([media['id'], 'nonexistent']), {media['id']: media['data']['assetBase64']})
            self.assertEqual(db.media_assets([]), {})

    def test_bulk_asset_loading_handles_more_ids_than_one_query_holds(self):
        media = [upload(self.cms, (i, 5, 5)) for i in range(3)]
        with self.cms.store.transaction() as db:
            ids = [m['id'] for m in media] + [f'missing-{i}' for i in range(600)]
            found = db.media_assets(ids)
        self.assertEqual(set(found), {m['id'] for m in media})


if __name__ == '__main__':
    unittest.main()
