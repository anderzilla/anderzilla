"""One transaction per operation. SQLite is injected explicitly in local tests only."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

class Result:
    def __init__(self, cursor):
        self.cursor = cursor
    @property
    def rowcount(self):
        return self.cursor.rowcount
    def _row(self, row):
        if row is None:
            return None
        if isinstance(row, dict) or hasattr(row, 'keys'):
            return dict(row)
        return dict(zip((column[0] for column in self.cursor.description), row))
    def fetchone(self):
        return self._row(self.cursor.fetchone())
    def fetchall(self):
        return [self._row(row) for row in self.cursor.fetchall()]

class Session:
    def __init__(self, connection, sql_server=False):
        self.connection, self.sql_server = connection, sql_server
    def execute(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query.replace('?', '%s') if self.sql_server else query, tuple(params))
        return Result(cursor)
    def page(self, query, params, limit):
        suffix = ' OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY' if self.sql_server else ' LIMIT ?'
        return self.execute(query + suffix, (*params, limit))

class SQLiteStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            db.execute('BEGIN IMMEDIATE')
            yield Session(db)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

class AzureSQLStore:
    def connect(self):
        import certifi
        import pytds
        from .tds_tls import configure
        configure()
        return pytds.connect(server=os.environ['IDENTITY_SQL_SERVER'], database=os.environ['IDENTITY_SQL_DATABASE'],
                             user=os.environ['IDENTITY_SQL_USER'], password=os.environ['IDENTITY_SQL_PASSWORD'],
                             cafile=certifi.where(), validate_host=True, enc_login_only=False, autocommit=False,
                             login_timeout=40, timeout=30)
    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.cursor().execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            db.cursor().execute("DECLARE @r int; EXEC @r = sp_getapplock @Resource='anderzilla-identity', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000; IF @r < 0 THROW 51000, 'identity busy', 1;")
            yield Session(db, True)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    def health(self):
        try:
            with self.transaction() as db:
                db.execute('SELECT COUNT(*) AS count FROM accounts').fetchone()
            return {'healthy': True}
        except Exception:
            return {'healthy': False}
