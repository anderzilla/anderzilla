"""Durable stores. SQLite is local-only; Azure uses SQL with certificate verification."""
import json
import os
import sqlite3
import threading
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

    def records(self, collection, light=False):
        """light=True replaces the image bytes of media rows by the placeholder 'omitted' inside the database, so ~20 MiB never cross the wire."""
        if light and collection == 'media':
            if self.sql_server:
                query = "SELECT CASE WHEN JSON_VALUE(document,'$.data.assetSha256') IS NOT NULL THEN JSON_MODIFY(document,'$.data.assetBase64','omitted') ELSE document END FROM cms_records WHERE collection=? ORDER BY updated_at DESC"
            else:
                query = "SELECT CASE WHEN json_extract(document,'$.data.assetSha256') IS NOT NULL THEN json_set(document,'$.data.assetBase64','omitted') ELSE document END FROM cms_records WHERE collection=? ORDER BY updated_at DESC"
        else:
            query = 'SELECT document FROM cms_records WHERE collection=? ORDER BY updated_at DESC'
        return [json.loads(row[0]) for row in self.execute(query, (collection,)).fetchall()]

    def media_assets(self, record_ids):
        """Base64 bytes of many uploaded images in a few queries (one round trip per ~500 ids instead of one per image)."""
        ids, found = list(record_ids), {}
        for start in range(0, len(ids), 500):
            chunk = ids[start:start + 500]
            marks = ','.join('?' * len(chunk))
            if self.sql_server:
                query = f"SELECT id, asset.assetBase64 FROM cms_records CROSS APPLY OPENJSON(document) WITH (assetBase64 nvarchar(max) '$.data.assetBase64') AS asset WHERE collection='media' AND id IN ({marks})"
            else:
                query = f"SELECT id, json_extract(document, '$.data.assetBase64') FROM cms_records WHERE collection='media' AND id IN ({marks})"
            found.update({row[0]: row[1] for row in self.execute(query, chunk).fetchall()})
        return found

    def media_asset(self, record_id):
        """Base64 bytes of one uploaded image (SQL Server needs OPENJSON: JSON_VALUE truncates values over 4000 characters)."""
        if self.sql_server:
            query = "SELECT asset.assetBase64 FROM cms_records CROSS APPLY OPENJSON(document) WITH (assetBase64 nvarchar(max) '$.data.assetBase64') AS asset WHERE collection='media' AND id=?"
        else:
            query = "SELECT json_extract(document, '$.data.assetBase64') FROM cms_records WHERE collection='media' AND id=?"
        row = self.execute(query, (record_id,)).fetchone()
        return row[0] if row else None

    def media_bytes(self):
        """Return encoded quota usage without transferring every uploaded image."""
        if self.sql_server:
            query = "SELECT COALESCE(SUM(CONVERT(bigint,LEN(asset.assetBase64))),0) FROM cms_records CROSS APPLY OPENJSON(document) WITH (assetBase64 nvarchar(max) '$.data.assetBase64') AS asset WHERE collection='media'"
        else:
            query = "SELECT COALESCE(SUM(length(json_extract(document, '$.data.assetBase64'))),0) FROM cms_records WHERE collection='media'"
        return int(self.execute(query).fetchone()[0])

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

    # AI agent gateway: keys are stored only as hashes; requests, submissions and comments are JSON documents.
    def agent_key(self, key_id):
        row = self.execute('SELECT key_hash,document FROM agent_keys WHERE id=?', (key_id,)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def save_agent_key(self, document, key_hash):
        self.execute('INSERT INTO agent_keys(id,key_hash,document) VALUES(?,?,?)', (document['id'], key_hash, json.dumps(document)))

    def agent_keys(self):
        """Key metadata only (name, scopes, dates, revoked); the stored hash is never returned."""
        return [json.loads(row[0]) for row in self.execute('SELECT document FROM agent_keys ORDER BY id').fetchall()]

    def update_agent_key(self, document):
        self.execute('UPDATE agent_keys SET document=? WHERE id=?', (json.dumps(document), document['id']))

    def agent_request(self, agent_id, request_key):
        row = self.execute('SELECT input_hash,document FROM agent_requests WHERE agent_id=? AND request_key=?', (agent_id, request_key)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def save_agent_request(self, agent_id, request_key, input_hash, document):
        self.execute('INSERT INTO agent_requests(agent_id,request_key,input_hash,document) VALUES(?,?,?,?)', (agent_id, request_key, input_hash, json.dumps(document, ensure_ascii=False)))

    def submission(self, submission_id):
        row = self.execute('SELECT document FROM submissions WHERE id=?', (submission_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_submission(self, document, new=False):
        text = json.dumps(document, ensure_ascii=False)
        if new:
            self.execute('INSERT INTO submissions(id,updated_at,document) VALUES(?,?,?)', (document['id'], document['updatedAt'], text))
        else:
            self.execute('UPDATE submissions SET document=?,updated_at=? WHERE id=?', (text, document['updatedAt'], document['id']))

    def submissions(self):
        return [json.loads(row[0]) for row in self.execute('SELECT document FROM submissions ORDER BY updated_at DESC').fetchall()]

    def comments(self, submission_id):
        return [json.loads(row[0]) for row in self.execute('SELECT document FROM submission_comments WHERE submission_id=? ORDER BY created_at', (submission_id,)).fetchall()]

    def save_comment(self, document, new=False):
        text = json.dumps(document, ensure_ascii=False)
        if new:
            self.execute('INSERT INTO submission_comments(id,submission_id,created_at,document) VALUES(?,?,?,?)', (document['id'], document['submissionId'], document['createdAt'], text))
        else:
            self.execute('UPDATE submission_comments SET document=? WHERE id=?', (text, document['id']))


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
        return pytds.connect(server=os.environ['CMS_SQL_SERVER'], database=os.environ['CMS_SQL_DATABASE'], user=os.environ['CMS_SQL_USER'], password=os.environ['CMS_SQL_PASSWORD'], cafile=certifi.where(), validate_host=True, enc_login_only=False, autocommit=False, login_timeout=40, timeout=30)  # a paused serverless database takes up to ~40 s to resume; Static Web Apps cuts a request at ~45 s

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

    # One connection per worker thread, reused across transactions. A TLS connect plus login costs ~1.4 s on Azure SQL and a single
    # approval opens about ten transactions, which pushed it past the 45 s limit of the review site.
    _local = threading.local()

    def _key(self):
        return tuple(os.environ.get(name, '') for name in ('CMS_SQL_SERVER', 'CMS_SQL_DATABASE', 'CMS_SQL_USER'))

    def _state(self):
        state = getattr(self._local, 'state', None)
        if state is None or state['key'] != self._key():
            if state and state['connection'] is not None:
                self._close(state['connection'])
            state = self._local.state = {'key': self._key(), 'connection': None, 'depth': 0}
        return state

    @staticmethod
    def _close(connection):
        try:
            connection.close()
        except Exception:
            pass

    def _acquire(self, state):
        connection = state['connection']
        if connection is not None:
            try:  # the server may have closed an idle connection or paused the database since the last use
                connection.cursor().execute('SELECT 1').fetchone()
                connection.rollback()
                return connection
            except Exception:
                self._close(connection)
                state['connection'] = None
        state['connection'] = self.connect()
        return state['connection']

    @contextmanager
    def transaction(self):
        state = self._state()
        if state['depth']:
            raise RuntimeError('Nested CMS transactions would commit the outer one early and deadlock on the application lock.')
        db = self._acquire(state)
        state['depth'] = 1
        try:
            db.cursor().execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            # Serialize CMS writes and release snapshots across instances. Low-volume admin workload.
            db.cursor().execute("DECLARE @r int; EXEC @r = sp_getapplock @Resource='anderzilla-cms', @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000; IF @r < 0 THROW 51000, 'CMS busy', 1;")
            yield Session(db, True)
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:  # a broken connection is dropped instead of being reused
                self._close(db)
                state['connection'] = None
            raise
        finally:
            state['depth'] = 0
