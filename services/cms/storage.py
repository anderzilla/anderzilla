"""Durable stores. SQLite is local-only; Azure uses SQL with certificate verification."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from core import now


class Session:
    def __init__(self, connection, sql_server=False):
        self.connection, self.sql_server = connection, sql_server

    def execute(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query.replace('?', '%s') if self.sql_server else query, tuple(params))
        return cursor

    def records(self, collection):
        rows = self.execute('SELECT document FROM cms_records WHERE collection=? ORDER BY updated_at DESC', (collection,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def record(self, collection, record_id):
        row = self.execute('SELECT document FROM cms_records WHERE collection=? AND id=?', (collection, record_id)).fetchone()
        return json.loads(row[0]) if row else None

    def save_record(self, collection, record):
        document = json.dumps(record, ensure_ascii=False)
        if record['version'] == 1:
            self.execute('INSERT INTO cms_records(collection,id,updated_at,document) VALUES(?,?,?,?)', (collection, record['id'], record['updatedAt'], document))
        else:
            self.execute('UPDATE cms_records SET document=?,updated_at=? WHERE collection=? AND id=?', (document, record['updatedAt'], collection, record['id']))
        self.execute('INSERT INTO cms_revisions(collection,id,version,document) VALUES(?,?,?,?)', (collection, record['id'], record['version'], document))

    def revisions(self, collection, record_id):
        return [json.loads(row[0]) for row in self.execute('SELECT document FROM cms_revisions WHERE collection=? AND id=? ORDER BY version DESC', (collection, record_id)).fetchall()]

    def audit(self, actor, action, collection, record_id, version):
        import uuid
        entry = {'id': str(uuid.uuid4()), 'actor': actor, 'action': action, 'collection': collection, 'recordId': record_id, 'version': version, 'createdAt': now()}
        self.execute('INSERT INTO cms_audit(id,created_at,document) VALUES(?,?,?)', (entry['id'], entry['createdAt'], json.dumps(entry)))

    def recent_audit(self):
        query = 'SELECT TOP 50 document FROM cms_audit ORDER BY created_at DESC' if self.sql_server else 'SELECT document FROM cms_audit ORDER BY created_at DESC LIMIT 50'
        return [json.loads(row[0]) for row in self.execute(query).fetchall()]

    def release_by_key(self, key):
        row = self.execute('SELECT document FROM cms_releases WHERE request_key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_release(self, release, key, snapshot):
        self.execute('INSERT INTO cms_releases(id,request_key,created_at,document,snapshot) VALUES(?,?,?,?,?)', (release['id'], key, release['createdAt'], json.dumps(release), json.dumps(snapshot, ensure_ascii=False)))

    def releases(self):
        return [json.loads(row[0]) for row in self.execute('SELECT document FROM cms_releases ORDER BY created_at DESC').fetchall()]

    def release(self, release_id, snapshot=False):
        row = self.execute('SELECT ' + ('snapshot' if snapshot else 'document') + ' FROM cms_releases WHERE id=?', (release_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def update_release(self, release):
        self.execute('UPDATE cms_releases SET document=? WHERE id=?', (json.dumps(release), release['id']))


class SQLiteStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path)
        try:
            db.executescript(Path(__file__).with_name('schema.sql').read_text())
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15)
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
        return pytds.connect(server=os.environ['CMS_SQL_SERVER'], database=os.environ['CMS_SQL_DATABASE'], user=os.environ['CMS_SQL_USER'], password=os.environ['CMS_SQL_PASSWORD'], cafile=certifi.where(), validate_host=True, enc_login_only=False, autocommit=False, login_timeout=15, timeout=30)

    def health(self):
        """Protected operator diagnostic: never expose exception text or connection data."""
        stage = 'dependencies'
        db = None
        try:
            import certifi
            import pytds
            import OpenSSL
            stage = 'configuration'
            if not all(os.environ.get(key) for key in ('CMS_SQL_SERVER', 'CMS_SQL_DATABASE', 'CMS_SQL_USER', 'CMS_SQL_PASSWORD')):
                return {'healthy': False, 'stage': stage, 'category': 'missing_configuration', 'exceptionType': None}
            stage = 'connect'
            db = self.connect()
            stage = 'query'
            db.cursor().execute('SELECT 1').fetchone()
            stage = 'isolation'
            db.cursor().execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            stage = 'application_lock'
            db.cursor().execute("DECLARE @r int; EXEC @r = sp_getapplock @Resource='anderzilla-cms', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000; IF @r < 0 THROW 51000, 'CMS busy', 1;")
            stage = 'schema_read'
            db.cursor().execute('SELECT TOP 1 id FROM cms_records').fetchone()
            return {'healthy': True, 'stage': 'complete', 'category': 'ready', 'exceptionType': None}
        except Exception as error:
            name = type(error).__name__
            allowed = {'ImportError', 'ModuleNotFoundError', 'KeyError', 'TimeoutError', 'OperationalError', 'ProgrammingError', 'InterfaceError', 'DatabaseError', 'Error', 'AttributeError', 'TypeError', 'ValueError', 'SSLError', 'OSError'}
            # Compare text internally only to classify known network/auth failures.
            message = str(error).lower()
            category = ('dependency' if stage == 'dependencies' else 'timeout' if 'timeout' in message or 'timed out' in message else 'firewall' if 'firewall' in message or 'not allowed to access' in message else 'authentication' if 'login failed' in message else 'tls' if any(word in message for word in ('certificate', 'tls', 'ssl')) else 'database_permission' if 'permission' in message else 'connection' if stage == 'connect' else 'database_operation')
            return {'healthy': False, 'stage': stage, 'category': category, 'exceptionType': name if name in allowed else 'Exception'}
        finally:
            if db:
                try:
                    db.rollback()
                    db.close()
                except Exception:
                    pass

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.cursor().execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            # Serialize CMS writes and release snapshots across instances. Low-volume admin workload.
            db.cursor().execute("DECLARE @r int; EXEC @r = sp_getapplock @Resource='anderzilla-cms', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000; IF @r < 0 THROW 51000, 'CMS busy', 1;")
            yield Session(db, True)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
