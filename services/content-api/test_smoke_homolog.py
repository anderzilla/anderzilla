"""The smoke tool itself is tested against the real edge code running in-process (no network, SQLite)."""
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import smoke_homolog
from agent_api import AgentGateway
from content_api import process
from core import CMS
from storage import SQLiteStore


class FakeResponse:
    def __init__(self, status, payload):
        self.status, self.body = status, json.dumps(payload).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class SmokeToolTest(unittest.TestCase):
    def test_smoke_passes_against_the_real_edge_and_revokes_its_key(self):
        with tempfile.TemporaryDirectory() as folder:
            gateway = AgentGateway(CMS(SQLiteStore(Path(folder) / 'cms.db')), media_hosts=[])

            def fake_urlopen(request, timeout=0):
                path = request.full_url.split('.net', 1)[1]
                headers = {k.lower(): v for k, v in request.header_items()}
                status, payload, _ = process(request.get_method(), path.removeprefix('/v1/'), {}, headers, request.data or b'', gateway_factory=lambda: gateway)
                if status >= 400:
                    raise urllib.error.HTTPError(request.full_url, status, 'err', {}, __import__('io').BytesIO(json.dumps(payload).encode()))
                return FakeResponse(status, payload)

            lines = []
            with patch('smoke_homolog.urllib.request.urlopen', fake_urlopen):
                ok = smoke_homolog.Smoke(gateway, out=lines.append).run()
            self.assertTrue(ok, '\n'.join(line for line in lines if line.startswith('FAIL')))
            self.assertGreaterEqual(len(lines), 25)
            self.assertFalse([line for line in lines if 'azk_' in line])  # the key is never printed
            with gateway.store.transaction() as db:
                self.assertTrue(all(key['revoked'] for key in db.agent_keys()))

    def test_refuses_any_other_database(self):
        with patch.dict('os.environ', {'CMS_SQL_DATABASE': 'anderzilla-cms-production'}):
            with self.assertRaises(SystemExit):
                smoke_homolog.main()


if __name__ == '__main__':
    unittest.main()
