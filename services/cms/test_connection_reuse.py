"""AzureSQLStore reuses one connection per thread, checks it before reuse and never nests transactions (no SQL Server needed)."""
import threading
import unittest
from unittest.mock import patch
from storage import AzureSQLStore

ENV = {'CMS_SQL_SERVER': 's', 'CMS_SQL_DATABASE': 'd', 'CMS_SQL_USER': 'u', 'CMS_SQL_PASSWORD': 'p'}


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=()):
        self.connection.queries.append(query)
        if self.connection.broken:
            raise OSError('connection reset')
        return self

    def fetchone(self):
        return (1,)


class FakeConnection:
    instances = []

    def __init__(self):
        self.queries, self.broken, self.commits, self.rollbacks, self.closed = [], False, 0, 0, False
        FakeConnection.instances.append(self)

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class ConnectionReuseTest(unittest.TestCase):
    def setUp(self):
        FakeConnection.instances = []
        AzureSQLStore._local = threading.local()  # a clean thread state per test
        self.env = patch.dict('os.environ', ENV)
        self.env.start()
        self.connect = patch.object(AzureSQLStore, 'connect', lambda store: FakeConnection())
        self.connect.start()
        self.store = AzureSQLStore()

    def tearDown(self):
        self.connect.stop()
        self.env.stop()

    def test_one_connection_serves_many_transactions(self):
        for _ in range(5):
            with self.store.transaction():
                pass
        self.assertEqual(len(FakeConnection.instances), 1)
        self.assertEqual(FakeConnection.instances[0].commits, 5)
        self.assertEqual(sum('sp_getapplock' in q for q in FakeConnection.instances[0].queries), 5)  # every transaction still takes the application lock

    def test_application_errors_roll_back_but_keep_the_connection(self):
        with self.assertRaises(ValueError):
            with self.store.transaction():
                raise ValueError('domain error')
        with self.store.transaction():
            pass
        self.assertEqual(len(FakeConnection.instances), 1)
        self.assertEqual((FakeConnection.instances[0].rollbacks >= 1, FakeConnection.instances[0].closed), (True, False))

    def test_a_dead_connection_is_replaced_before_use(self):
        with self.store.transaction():
            pass
        FakeConnection.instances[0].broken = True  # idle timeout or a paused database
        with self.store.transaction():
            pass
        self.assertEqual(len(FakeConnection.instances), 2)
        self.assertTrue(FakeConnection.instances[0].closed)
        self.assertFalse(FakeConnection.instances[1].closed)

    def test_a_connection_that_cannot_roll_back_is_dropped(self):
        with self.assertRaises(ValueError):
            with self.store.transaction():
                FakeConnection.instances[0].rollback = lambda: (_ for _ in ()).throw(OSError('gone'))
                raise ValueError('boom')
        self.assertTrue(FakeConnection.instances[0].closed)
        with self.store.transaction():
            pass
        self.assertEqual(len(FakeConnection.instances), 2)

    def test_nested_transactions_are_refused(self):
        with self.store.transaction():
            with self.assertRaises(RuntimeError):
                with self.store.transaction():
                    pass
        with self.store.transaction():  # the outer one finished normally and the store is usable again
            pass

    def test_each_thread_gets_its_own_connection(self):
        seen = []

        def work():
            with self.store.transaction():
                seen.append(FakeConnection.instances[-1])
        with self.store.transaction():
            main = FakeConnection.instances[-1]
        thread = threading.Thread(target=work)
        thread.start()
        thread.join()
        self.assertEqual(len(FakeConnection.instances), 2)
        self.assertIsNot(seen[0], main)

    def test_a_changed_database_never_reuses_the_old_connection(self):
        with self.store.transaction():
            pass
        with patch.dict('os.environ', {'CMS_SQL_DATABASE': 'other'}):
            with self.store.transaction():
                pass
        self.assertEqual(len(FakeConnection.instances), 2)
        self.assertTrue(FakeConnection.instances[0].closed)


if __name__ == '__main__':
    unittest.main()
