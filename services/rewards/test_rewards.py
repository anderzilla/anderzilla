"""Run: python -m unittest discover -s services/rewards -v"""
from concurrent.futures import ThreadPoolExecutor
import os
import sqlite3
import tempfile
import unittest

from core import Principal, Rejected, Rewards, VerifiedCompletion


def fixture_verifier(principal, mission, evidence):
    # Test double only. Real implementations must load and validate server evidence.
    if evidence != {'test_evidence': 'correct'}:
        raise Rejected('Incorrect evidence')
    return VerifiedCompletion('once', 'test-only-evidence')


class RewardsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, 'test.sqlite')
        self.service = Rewards(self.path, fixture_verifier, clock=lambda: 100)
        self.user = Principal('user')
        self.other = Principal('other')
        self.operator = Principal('operator', frozenset({'rewards_operator'}))
        for name in ('user', 'other', 'operator'):
            self.service.db.execute('INSERT INTO accounts VALUES (?, ?, ?)', (name, 'BR', 'active'))
            self.service.db.execute('INSERT INTO wallets(account_id) VALUES (?)', (name,))
        self.service.db.execute("INSERT INTO missions VALUES ('quiz',1,100,0,200,1)")
        self.service.db.execute("INSERT INTO rewards VALUES ('fixture',1,75,1,'BR','active')")

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def award(self, user=None, key='award-key'):
        return self.service.complete(user or self.user, 'quiz', 1, {'test_evidence': 'correct'}, key)

    def reserve(self, user=None, key='reserve-key'):
        return self.service.reserve(user or self.user, 'fixture', 1, key)

    def assert_reconciled(self):
        for row in self.service.db.execute('SELECT * FROM wallets'):
            sums = self.service.db.execute('SELECT COALESCE(SUM(available_delta),0),COALESCE(SUM(reserved_delta),0) FROM ledger WHERE account_id=?', (row['account_id'],)).fetchone()
            self.assertEqual((row['available'], row['reserved']), tuple(sums))

    def test_completion_retry_and_new_key_award_once(self):
        first = self.award()
        self.assertEqual(first, self.award())
        self.assertEqual(first, self.award(key='different-key'))
        self.assertEqual(self.service.wallet(self.user), {'available': 100, 'reserved': 0})
        self.assert_reconciled()

    def test_default_verifier_fails_closed(self):
        default = Rewards(self.path, clock=lambda: 100)
        try:
            with self.assertRaises(Rejected):
                default.complete(self.user, 'quiz', 1, {}, 'reject-key')
        finally:
            default.close()
        self.assertEqual(self.service.wallet(self.user)['available'], 0)

    def test_wrong_evidence_or_outside_window_does_not_award(self):
        with self.assertRaises(Rejected):
            self.service.complete(self.user, 'quiz', 1, {}, 'wrong-key')
        self.service.clock = lambda: 200
        with self.assertRaises(Rejected):
            self.award()
        self.assert_reconciled()

    def test_idempotency_payload_collision(self):
        self.award()
        with self.assertRaises(Rejected):
            self.service.complete(self.user, 'quiz', 2, {}, 'award-key')
        with self.assertRaises(Rejected):
            self.reserve(key='award-key')

    def test_reservation_retry_and_cancellation_restore_once(self):
        self.award()
        rid = self.reserve()
        self.assertEqual(rid, self.reserve())
        self.assertEqual(self.service.wallet(self.user), {'available': 25, 'reserved': 75})
        for _ in range(2):
            self.service.transition(self.operator, rid, 'cancelled', 'Fixture cancellation')
        self.assertEqual(self.service.wallet(self.user), {'available': 100, 'reserved': 0})
        self.assertEqual(self.service.db.execute('SELECT stock FROM rewards').fetchone()[0], 1)
        self.assert_reconciled()

    def test_delivery_consumes_once_and_cannot_refund(self):
        self.award()
        rid = self.reserve()
        self.service.transition(self.operator, rid, 'fulfilling', 'Dispatch begun')
        with self.assertRaises(Rejected):
            self.service.transition(self.operator, rid, 'cancelled', 'Uncertain delivery')
        for _ in range(2):
            self.service.transition(self.operator, rid, 'fulfilled', 'Confirmed fixture delivery')
        self.assertEqual(self.service.wallet(self.user), {'available': 25, 'reserved': 0})
        self.assert_reconciled()

    def test_ownership_operator_and_suspension(self):
        self.award()
        rid = self.reserve()
        with self.assertRaises(Rejected):
            self.service.redemption(self.other, rid)
        with self.assertRaises(Rejected):
            self.service.transition(self.user, rid, 'cancelled', 'Not an operator')
        self.service.db.execute("UPDATE accounts SET state='suspended' WHERE id='user'")
        with self.assertRaises(Rejected):
            self.service.wallet(self.user)

    def test_insufficient_balance_region_and_version(self):
        with self.assertRaises(Rejected):
            self.reserve()
        self.award()
        with self.assertRaises(Rejected):
            self.service.reserve(self.user, 'fixture', 2, 'version-key')
        self.service.db.execute("UPDATE accounts SET country='US' WHERE id='user'")
        with self.assertRaises(Rejected):
            self.reserve()
        self.assert_reconciled()

    def test_failure_mid_reservation_rolls_back_stock_points_and_order(self):
        self.award()
        original = self.service.post
        def fail(*args):
            original(*args)
            raise RuntimeError('Injected database-adapter failure')
        self.service.post = fail
        with self.assertRaises(RuntimeError):
            self.reserve()
        self.assertEqual(self.service.db.execute('SELECT stock FROM rewards').fetchone()[0], 1)
        self.assertEqual(self.service.db.execute('SELECT COUNT(*) FROM redemptions').fetchone()[0], 0)
        self.assert_reconciled()

    def test_two_connections_compete_for_last_unit(self):
        self.award()
        self.award(self.other)
        def request(user):
            service = Rewards(self.path)
            try:
                return service.reserve(user, 'fixture', 1, 'parallel-key')
            except Rejected:
                return None
            finally:
                service.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            result = list(executor.map(request, [self.user, self.other]))
        self.assertEqual(sum(r is not None for r in result), 1)
        self.assertEqual(self.service.db.execute('SELECT stock FROM rewards').fetchone()[0], 0)
        self.assert_reconciled()

    def test_ledger_is_append_only(self):
        self.award()
        for sql in ('DELETE FROM ledger', 'UPDATE ledger SET available_delta=999'):
            with self.assertRaises(sqlite3.IntegrityError):
                self.service.db.execute(sql)


if __name__ == '__main__':
    unittest.main()
