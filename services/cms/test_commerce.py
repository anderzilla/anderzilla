import tempfile
import unittest
from pathlib import Path
from api import dispatch
from core import CMS, Error, validate
from storage import SQLiteStore
from seed_commerce import FORGEKIT, seed

ADMIN = {'id': 'commerce-test', 'roles': ['anderzilla_admin']}


class CommerceTests(unittest.TestCase):
    def test_commerce_checks_market_approval_and_safe_urls(self):
        for update in ({'market':'xx'}, {'currency':'KP'}, {'ctaUrl':'http://example.com'}, {'status':'approved'}):
            with self.subTest(update=update), self.assertRaises(Error):
                validate('products', {**FORGEKIT, **update}, approved=True)
        affiliate = {key: value for key, value in FORGEKIT.items() if key not in {'slug','bodyPT','bodyEN','priceMinor','demoUrl'}}
        with self.assertRaises(Error):
            validate('affiliate_placements', affiliate, approved=True)
        validate('affiliate_placements', {**affiliate, 'approvalReference':'private approval'}, approved=True)

    def test_false_flag_and_points_demo_visibility_are_valid(self):
        flag = {'titlePT':'Produtos','titleEN':'Products','market':'br','status':'active','key':'showProducts','enabled':False}
        validate('feature_flags', flag, approved=True)
        validate('feature_flags', {**flag, 'key':'showPointsStore','enabled':True}, approved=True)

    def test_snapshot_omits_inactive_and_private_evidence_and_duplicate_flags(self):
        with tempfile.TemporaryDirectory() as folder:
            cms = CMS(SQLiteStore(Path(folder) / 'cms.db'))
            product = seed(cms, ADMIN)
            self.assertIsNone(seed(cms, ADMIN))
            cms.save(ADMIN, 'products', None, product['id'], product['version'], 'approve')
            affiliate = {'titlePT':'Teste','titleEN':'Test','market':'br','status':'candidate'}
            candidate = cms.save(ADMIN, 'affiliate_placements', affiliate)
            cms.save(ADMIN, 'affiliate_placements', None, candidate['id'], 1, 'approve')
            flag = {'titlePT':'Produtos','titleEN':'Products','market':'br','status':'active','key':'showProducts','enabled':False}
            first = cms.save(ADMIN, 'feature_flags', flag)
            cms.save(ADMIN, 'feature_flags', None, first['id'], 1, 'approve')
            second = cms.save(ADMIN, 'feature_flags', flag)
            with self.assertRaises(Error):
                cms.save(ADMIN, 'feature_flags', None, second['id'], 1, 'approve')
            release = cms.release(ADMIN, 'commerce-test-release')
            snapshot = cms.releases(ADMIN, release['id'], True)
            self.assertEqual(snapshot['collections']['affiliate_placements'], [])
            self.assertEqual(snapshot['collections']['products'][0]['data']['market'], 'intl')

    def test_api_routes_allow_commerce_collection_names(self):
        with tempfile.TemporaryDirectory() as folder:
            cms = CMS(SQLiteStore(Path(folder) / 'cms.db'))
            for name in ('affiliate_placements','ad_placements','sponsor_packages','trust_blocks','feature_flags','market_hubs'):
                record = dispatch(cms, ADMIN, 'POST', '/api/admin/records/' + name, {'data': {'titlePT':'Rascunho','market':'br'}})
                self.assertEqual(dispatch(cms, ADMIN, 'GET', '/api/admin/records/' + name)['items'][0]['id'], record['id'])

    def test_editor_cannot_mutate_commerce(self):
        with tempfile.TemporaryDirectory() as folder:
            cms = CMS(SQLiteStore(Path(folder) / 'cms.db'))
            with self.assertRaises(Error):
                cms.save({'id':'editor','roles':['anderzilla_editor']}, 'products', FORGEKIT)
