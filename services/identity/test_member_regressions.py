"""Independent regressions found during review of the Antigravity delivery."""
from pathlib import Path
import unittest
from . import test_member_area as fixtures


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.MemberAreaScenarioTests(methodName='test_a01_anonymous_and_origin_protection')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.user = self.fixture._create_member('review-token', 'user_review', 'review@example.invalid', 234567890)

    def call(self, method, path, body=None):
        return self.fixture._call(method, path, token=self.user['token'], body=body)

    def test_failed_answer_commits_and_cannot_reuse_attempt(self):
        challenge = self.call('POST', '/api/points/challenge', {'missionId': 'checkpoint-curiosidade', 'missionVersion': 1})
        self.assertEqual(challenge['status'], 200)
        attempt = challenge['body']['attemptId']
        wrong = self.call('POST', '/api/points/evidence', {'attemptId': attempt, 'answers': {'q1': 'b'}})
        self.assertEqual(wrong['status'], 422)
        with self.fixture.store.transaction() as db:
            self.assertEqual(db.execute('SELECT state FROM mission_attempts WHERE id=?', (attempt,)).fetchone()['state'], 'failed')
        retry = self.call('POST', '/api/points/evidence', {'attemptId': attempt, 'answers': {'q1': 'a'}})
        self.assertEqual(retry['status'], 409)

    def test_interests_require_version_and_preserve_current_selection(self):
        self.assertEqual(self.call('PUT', '/api/member/interests', {'categoryIds': ['ia']})['status'], 422)
        saved = self.call('PUT', '/api/member/interests', {'categoryIds': ['ia'], 'expectedVersion': 1})
        self.assertEqual(saved['status'], 200)
        self.assertEqual(self.call('PUT', '/api/member/interests', {'categoryIds': ['games'], 'expectedVersion': 1})['status'], 409)
        self.assertEqual(self.call('GET', '/api/member/interests')['body']['interests'], ['ia'])

    def test_missing_campaign_never_creates_automatic_funding(self):
        with self.fixture.store.transaction() as db:
            db.execute('DELETE FROM mission_campaigns')
        result = self.call('POST', '/api/points/challenge', {'missionId': 'checkpoint-curiosidade', 'missionVersion': 1})
        self.assertEqual(result['status'], 409)
        with self.fixture.store.transaction() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM mission_campaigns').fetchone()['n'], 0)

    def test_history_requires_exact_generation_after_clear_and_remove(self):
        item = 'airpods-live-translation'
        self.assertEqual(self.call('POST', '/api/member/exploration/events', {'discoveryId': item})['status'], 422)
        initial = self.call('GET', '/api/member/exploration')['body']['historyGeneration']
        event = {'discoveryId': item, 'historyGeneration': initial, 'eventId': 'review-event-old'}
        self.assertEqual(self.call('POST', '/api/member/exploration/events', event)['status'], 200)
        removed = self.call('DELETE', '/api/member/exploration/' + item)
        generation = removed['body']['historyGeneration']
        self.assertGreater(generation, initial)
        self.assertEqual(self.call('POST', '/api/member/exploration/events', event)['status'], 409)
        event = {**event, 'historyGeneration': generation, 'eventId': 'review-event-new'}
        self.assertEqual(self.call('POST', '/api/member/exploration/events', event)['status'], 200)
        self.assertEqual(self.call('POST', '/api/member/exploration/events', {**event, 'historyGeneration': generation + 100})['status'], 409)
        cleared = self.call('POST', '/api/member/exploration/clear', {'confirm': True, 'expectedGeneration': generation})
        self.assertEqual(cleared['status'], 200)
        self.assertEqual(self.call('POST', '/api/member/exploration/events', event)['status'], 409)

    def test_additive_migration_uses_runtime_schema_and_rollback_is_non_destructive(self):
        root = Path(__file__).parent
        schema = (root / 'schema.azure.sql').read_text(encoding='utf8')
        marker = '-- Member Area relational collections, entitlements and transactional KP/missions tables (prepared additive).'
        migration = (root / 'migrations/002_member_area_additive.azure.sql').read_text(encoding='utf8')
        self.assertIn(schema.split(marker)[1].strip(), migration)
        rollback = (root / 'migrations/002_member_area_rollback.azure.sql').read_text(encoding='utf8')
        self.assertNotIn('DROP TABLE', rollback)
        self.assertIn('THROW', rollback)
