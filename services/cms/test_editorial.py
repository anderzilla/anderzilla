import base64
import copy
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from PIL import Image
try:
    import core
    from core import CMS, Error, FIELDS, PUBLIC_COLLECTIONS, validate, validate_references
    from storage import SQLiteStore, Session
    from seed_examples import seed
    from import_newsroom import import_manifest
except ModuleNotFoundError:
    from services.cms import core
    from services.cms.core import CMS, Error, FIELDS, PUBLIC_COLLECTIONS, validate, validate_references
    from services.cms.storage import SQLiteStore, Session
    from services.cms.seed_examples import seed
    from services.cms.import_newsroom import import_manifest

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
        with self.cms.store.transaction() as db:
            self.assertEqual(db.media_bytes(), len(row['data']['assetBase64']))
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

    def test_newsroom_rejects_unsafe_sources_dates_and_social(self):
        for data in ({'sources': json.dumps([{'name':'Bad', 'url':'https://127.0.0.1/a'}])}, {'sources':'{}'}, {'sources':'[{}]'}, {'verifiedAt':'2026-19-90'}, {'hashtagsPT':'#Games invalid'}, {'socialInstagramPT':'x'*2201}):
            with self.assertRaises(Error):
                validate('content', data)
        validate('content', {'sources':json.dumps([{'name':'Official','url':'https://example.com/news','publishedAt':'2026-09-10'}]),'verifiedAt':'2026-09-10','hashtagsPT':'#Games #Programação'})
        validate('content', {'instagramUrl':'https://www.instagram.com/p/Abc123_/'})
        validate('content', {'instagramUrl':'https://instagram.com/reel/Abc123'})
        for url in ('https://example.com/p/Abc123','https://www.instagram.com/anderzilla/','https://www.instagram.com/p/','http://www.instagram.com/p/Abc123'):
            with self.subTest(url=url), self.assertRaises(Error):
                validate('content', {'instagramUrl': url})

    def test_newsroom_import_is_audited_and_retry_preserves_edits(self):
        data = {'titlePT':'Notícia','titleEN':'News','summaryPT':'Resumo','summaryEN':'Summary','bodyPT':'Texto','bodyEN':'Text','category':'games','sourceName':'Official','sourceUrl':'https://example.com/news','publishedAt':'2026-09-10','slugPT':'noticia','slugEN':'news'}
        manifest = {'items':[{'key':'news','data':data}]}
        first = import_manifest(self.cms, manifest, approve=True)[0]
        self.assertEqual(first['status'], 'approved')
        self.assertEqual(len(self.cms.revisions(ADMIN, 'content', first['id'])['items']), 2)
        retry = import_manifest(self.cms, manifest, approve=True)[0]
        self.assertEqual(retry['action'], 'preserved')
        self.assertEqual(retry['version'], 2)
        with self.cms.store.transaction() as db:
            self.assertTrue(all(event['actor']=='operator:editorial-launch' for event in db.recent_audit()))

    def test_social_image_must_be_approved_and_release_rechecks_reference(self):
        data = {'titlePT':'Notícia','titleEN':'News','summaryPT':'Resumo','summaryEN':'Summary','bodyPT':'Texto','bodyEN':'Text','category':'games','sourceName':'Official','sourceUrl':'https://example.com/news','publishedAt':'2026-09-10','slugPT':'social','slugEN':'social'}
        image = self.upload()
        row = self.cms.save(ADMIN, 'content', {**data, 'socialMediaId':image['id']})
        with self.assertRaises(Error):
            self.approve('content', row)
        image = self.approve('media', image)
        self.approve('content', row)
        self.cms.release(ADMIN, 'social-reference-before-archive')
        self.cms.save(ADMIN, 'media', None, image['id'], image['version'], 'archive')
        with self.assertRaises(Error):
            self.cms.release(ADMIN, 'social-archived-reference')

    def test_release_cache_preserves_snapshot_and_reads_each_collection_once(self):
        seed(self.cms.store, approved=True)
        expected = {}
        # Reference implementation of the original uncached release selection.
        with self.cms.store.transaction() as db:
            for collection in sorted(PUBLIC_COLLECTIONS):
                expected[collection] = []
                for row in db.records(collection):
                    if row['status'] != 'approved':
                        continue
                    validate(collection, row['data'], approved=True, internal=True)
                    validate_references(db, collection, row['data'], row['id'])
                    public = copy.deepcopy(row)
                    public['data'].pop('approvalReference', None)
                    expected[collection].append(public)
            for collection in ('missions', 'rewards'):
                demos = [row for row in db.records(collection) if row['status'] == 'approved' and row['data'].get('isDemo') is True]
                if demos:
                    expected[collection] = demos
        reads = []
        original = Session.records

        def counted(db, collection, **options):
            reads.append(collection)
            return original(db, collection, **options)

        with patch.object(Session, 'records', counted), patch.object(Session, 'record', side_effect=AssertionError('Release must not query individual references')):
            release = self.cms.release(ADMIN, 'release-cache-equivalence')
            self.assertEqual(sorted(reads), sorted(FIELDS))
            reads.clear()
            self.assertEqual(self.cms.release(ADMIN, 'release-cache-equivalence'), release)
            self.assertEqual(reads, [])
        snapshot = self.cms.releases(ADMIN, release['id'], True)
        # Releases now reference uploaded images by id and SHA-256 instead of embedding their bytes (see test_release_assets.py).
        for row in expected.get('media', []):
            row['data'].pop('assetBase64', None)
        self.assertEqual(snapshot['collections'], expected)

    def test_release_cache_rejects_preexisting_duplicate_slugs(self):
        row = self.approve('pages', self.cms.save(ADMIN, 'pages', {'titlePT':'Page', 'slugPT':'duplicate', 'bodyPT':'Body'}))
        duplicate = {**copy.deepcopy(row), 'id':'duplicate-fixture', 'version':1}
        # Simulate a legacy inconsistent store only inside the disposable fixture.
        with self.cms.store.transaction() as db:
            db.save_record('pages', duplicate)
        with self.assertRaises(Error) as failure:
            self.cms.release(ADMIN, 'duplicate-cache-release')
        self.assertEqual(failure.exception.code, 'duplicate_slug')

    def test_import_uploads_cover_and_separate_social_image(self):
        output = io.BytesIO()
        Image.new('RGB', (120, 63), '#0000ff').save(output, format='PNG')
        cover = {'filename':'news-cover.png','contentBase64':base64.b64encode(output.getvalue()).decode(),'altPT':'Arte editorial','altEN':'Editorial art','credit':'Fixture','license':'Own test fixture'}
        data = {'titlePT':'Notícia','titleEN':'News','summaryPT':'Resumo','summaryEN':'Summary','bodyPT':'Texto','bodyEN':'Text','category':'games','sourceName':'Official','sourceUrl':'https://example.com/news','publishedAt':'2026-09-10','slugPT':'noticia','slugEN':'news'}
        manifest = {'items':[{'key':'news','data':data,'cover':cover,'socialImage':{**cover,'filename':'news-social.png'}}]}
        result = import_manifest(self.cms, manifest, approve=True)
        row = self.cms.list(ADMIN, 'content')['items'][0]
        self.assertNotEqual(row['data']['socialMediaId'], row['data']['coverMediaId'])
        self.assertEqual(len(self.cms.list(ADMIN, 'media')['items']), 2)
        self.assertEqual(result[0]['status'], 'approved')

    def test_media_library_quota_32mib_upload_rejects_without_large_fixture_and_is_atomic(self):
        # 32 MiB totais, 2 MiB por imagem, 1600 px — valida quota sem alocar 32 MB.
        first = self.upload()
        baseline_count = len(self.cms.list(ADMIN, 'media')['items'])
        with self.cms.store.transaction() as db:
            baseline_bytes = db.media_bytes()
            baseline_audit = len(db.recent_audit())
        self.assertEqual(baseline_bytes, len(first['data']['assetBase64']))
        # Simula biblioteca cheia sem criar fixtures gigantes: media_bytes() retorna o teto de 32 MiB.
        output = io.BytesIO()
        Image.new('RGB', (10, 10), '#00ff00').save(output, format='PNG')
        tiny = base64.b64encode(output.getvalue()).decode()
        with patch.object(Session, 'media_bytes', return_value=core.MEDIA_LIBRARY_LIMIT_B64):
            with self.assertRaises(Error) as failure:
                self.cms.upload_media(ADMIN, {'filename': 'tiny.png', 'contentBase64': tiny, 'altPT': 'Quota', 'altEN': 'Quota', 'credit': 'Test', 'license': 'Own test fixture'})
            self.assertEqual(failure.exception.code, 'media_quota')
            self.assertEqual(failure.exception.status, 413)
        # Atomicidade: upload recusado não persiste registro, bytes ou auditoria.
        self.assertEqual(len(self.cms.list(ADMIN, 'media')['items']), baseline_count)
        with self.cms.store.transaction() as db:
            self.assertEqual(db.media_bytes(), baseline_bytes)
            self.assertEqual(len(db.recent_audit()), baseline_audit)

    def test_media_library_quota_32mib_release_rejects_without_large_fixture(self):
        # Release também deve rejeitar snapshot que excede 32 MiB sem precisar de 16 imagens de 2 MiB.
        media = self.approve('media', self.upload())
        page = self.approve('pages', self.cms.save(ADMIN, 'pages', {'titlePT': 'Page quota', 'slugPT': 'quota-page', 'bodyPT': 'Body', 'coverMediaId': media['id']}))
        # Força o teto para um valor pequeno apenas neste teste, simulando biblioteca cheia com fixtures mínimas.
        # O release referencia as imagens por hash (a cota é aplicada no upload); o snapshot completo, usado em prévias e builds,
        # continua rejeitando quando as imagens embutidas passam do teto.
        with patch.object(core, 'MEDIA_LIBRARY_LIMIT_B64', 100):
            with self.cms.store.transaction() as db:
                with self.assertRaises(Error) as failure:
                    self.cms.snapshot(db)
            self.assertEqual(failure.exception.code, 'media_quota')
        # Com o limite real de 32 MiB o mesmo snapshot deve publicar normalmente.
        release = self.cms.release(ADMIN, 'quota-release-ok')
        self.assertEqual(release['status'], 'queued')


if __name__ == '__main__':
    unittest.main()
