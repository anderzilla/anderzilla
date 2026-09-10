import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from run_release import CMS, SQLiteStore, PRINCIPAL, claim, run, PREVIEW_URL, digest


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cms = CMS(SQLiteStore(Path(self.temp.name) / 'cms.sqlite'))
        self.release = self.cms.release(PRINCIPAL, 'publisher-test-1')

    def tearDown(self):
        self.temp.cleanup()

    def status(self):
        return self.cms.releases(PRINCIPAL, self.release['id'])['status']

    def test_single_claim_blocks_another_release(self):
        claim(self.cms, self.release['id'])
        other = self.cms.release(PRINCIPAL, 'publisher-test-2')
        with self.assertRaises(Exception):
            claim(self.cms, other['id'])
        self.assertEqual(self.status(), 'building')

    def test_failure_before_deployment_is_failed(self):
        def failed(*args):
            raise RuntimeError('build failure')
        with self.assertRaises(RuntimeError):
            run(self.cms, builder=failed)
        self.assertEqual(self.status(), 'failed')

    def test_uncertain_deployment_remains_for_reconciliation(self):
        def uncertain(*args):
            raise RuntimeError('connection dropped after upload')
        with self.assertRaises(RuntimeError):
            run(self.cms, builder=lambda *args: Path('artifact'), deployer=uncertain)
        self.assertEqual(self.status(), 'deploying')

    def test_verification_required_before_deployed(self):
        observed = []
        def check(marker):
            observed.append((self.status(), marker))
        result = run(self.cms, builder=lambda *args: Path('artifact'), deployer=lambda *args: None, verifier=check)
        self.assertEqual(observed[0][0], 'deploying')
        self.assertEqual(observed[0][1]['releaseId'], self.release['id'])
        self.assertEqual(result['status'], 'deployed')
        self.assertEqual(result['url'], PREVIEW_URL)

    def test_verification_failure_is_not_false_success(self):
        def failure(marker):
            raise RuntimeError('old release returned')
        with self.assertRaises(RuntimeError):
            run(self.cms, builder=lambda *args: Path('artifact'), deployer=lambda *args: None, verifier=failure)
        self.assertEqual(self.status(), 'deploying')

    def test_frozen_snapshot_not_newer_records(self):
        self.cms.save(PRINCIPAL, 'pages', {'titlePT': 'later draft'})
        def check(root, stage, snapshot, marker):
            self.assertEqual(snapshot['collections']['pages'], [])
            self.assertEqual(marker['snapshotSha256'], digest(snapshot))
            return Path('artifact')
        run(self.cms, builder=check, deployer=lambda *args: None, verifier=lambda marker: None)


if __name__ == '__main__':
    unittest.main()
