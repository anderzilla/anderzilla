import base64
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from api import dispatch, swa_principal
from core import CMS, Error
from storage import SQLiteStore

ADMIN = {'id': 'test-admin', 'name': 'Test operator', 'roles': ['anderzilla_admin']}
EDITOR = {'id': 'test-editor', 'name': 'Test editor', 'roles': ['anderzilla_editor']}


class CMSTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.temp.name) / 'cms.db'))

    def tearDown(self):
        self.temp.cleanup()

    def draft(self):
        return self.cms.save(ADMIN, 'pages', {'titlePT': 'Teste interno', 'slug': 'teste', 'bodyPT': 'Apenas teste automatizado.'})

    def test_identity_and_roles(self):
        for principal in [None, {'id': 'outsider', 'roles': ['authenticated']}]:
            with self.assertRaises(Error):
                self.cms.list(principal, 'content')
        with self.assertRaises(Error):
            self.cms.list(EDITOR, 'rewards')
        with self.assertRaises(Error):
            self.cms.release(EDITOR, 'test-release')
        self.assertEqual(self.cms.summary(EDITOR)['capabilities']['collections'], ['content', 'events', 'pages', 'media', 'taxonomies', 'banners'])

    def test_swa_session_does_not_trust_bad_principal(self):
        self.assertIsNone(swa_principal('not-base64'))
        self.assertIsNone(swa_principal(base64.b64encode(json.dumps({'userId': 'a', 'userRoles': ['anonymous']}).encode())))

    def test_optimistic_concurrency(self):
        draft = self.draft()
        def update(_):
            try:
                self.cms.save(ADMIN, 'pages', {'titlePT': 'Edição'}, draft['id'], 1)
                return 200
            except Error as error:
                return error.status
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(update, range(2))), [200, 409])
        self.assertEqual(len(self.cms.revisions(ADMIN, 'pages', draft['id'])['items']), 2)

    def test_editing_approved_returns_to_draft(self):
        draft = self.draft()
        approved = self.cms.save(ADMIN, 'pages', None, draft['id'], 1, 'approve')
        edited = self.cms.save(ADMIN, 'pages', approved['data'], draft['id'], 2)
        self.assertEqual(edited['status'], 'draft')

    def test_release_freezes_approved_snapshot_and_replays(self):
        draft = self.draft()
        self.cms.save(ADMIN, 'pages', None, draft['id'], 1, 'approve')
        private = self.cms.save(ADMIN, 'pages', {'titlePT': 'Private draft'})
        affiliate = self.cms.save(ADMIN, 'affiliates', {'titlePT': 'Test affiliate', 'url': 'https://example.com', 'disclosurePT': 'Teste', 'approvalReference': 'PRIVATE-CONTRACT'})
        self.cms.save(ADMIN, 'affiliates', None, affiliate['id'], 1, 'approve')
        release = self.cms.release(ADMIN, 'release-test-key')
        self.cms.save(ADMIN, 'pages', {'titlePT': 'Changed'}, draft['id'], 2)
        snapshot = self.cms.releases(ADMIN, release['id'], True)
        self.assertNotIn(private['id'], json.dumps(snapshot))
        self.assertNotIn('PRIVATE-CONTRACT', json.dumps(snapshot))
        self.assertNotIn('missions', snapshot['collections'])
        self.assertEqual(snapshot['collections']['pages'][0]['version'], 2)
        self.assertEqual(release, self.cms.release(ADMIN, 'release-test-key'))

    def test_validation_and_approval(self):
        for data in [{'url': 'javascript:alert(1)'}, {'url': 'https://user:password@example.com'}, {'saldo': 100}, {'priceMinor': True}]:
            with self.assertRaises(Error):
                self.cms.save(ADMIN, 'offers', data)
        draft = self.cms.save(ADMIN, 'content', {'titlePT': 'Incomplete'})
        with self.assertRaises(Error):
            self.cms.save(ADMIN, 'content', None, draft['id'], 1, 'approve')

    def test_release_transitions(self):
        release = self.cms.release(ADMIN, 'release-status-test')
        with self.assertRaises(Error):
            self.cms.update_release(ADMIN, release['id'], 'deployed')
        for status in ['building', 'validated', 'deploying', 'deployed']:
            self.cms.update_release(ADMIN, release['id'], status)
        with self.assertRaises(Error):
            self.cms.update_release(ADMIN, release['id'], 'building')

    def test_persistence_and_router(self):
        self.draft()
        cms = CMS(SQLiteStore(Path(self.temp.name) / 'cms.db'))
        self.assertEqual(len(dispatch(cms, ADMIN, 'GET', '/api/admin/records/pages')['items']), 1)
        with self.assertRaises(Error):
            dispatch(cms, ADMIN, 'POST', '/api/admin/records/users', {'data': {'roles': ['anderzilla_admin']}})


if __name__ == '__main__':
    unittest.main()
