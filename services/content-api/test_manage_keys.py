import json
import tempfile
import unittest
from pathlib import Path

import manage_keys
from content_api import process
from agent_api import AgentGateway
from core import CMS
from storage import SQLiteStore


class ManageKeysTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.db')
        self.lines = []
        self.calls = 0

    def tearDown(self):
        self.temp.cleanup()

    def factory(self, environment):
        self.calls += 1
        return self.store

    def run_tool(self, *argv, **kwargs):
        code = manage_keys.run(list(argv), store_factory=self.factory, out=self.lines.append, **kwargs)
        return code, '\n'.join(self.lines)

    def test_dry_run_never_opens_the_database(self):
        code, text = self.run_tool('create', '--environment', 'homolog', '--name', 'claude-teste')
        self.assertEqual((code, self.calls), (0, 0))
        self.assertIn('Dry run only', text)
        self.assertNotIn('azk_', text)
        self.run_tool('revoke', '--environment', 'homolog', '--id', 'abc')
        self.assertEqual(self.calls, 0)

    def test_created_key_is_shown_once_stored_only_as_a_hash_and_authenticates(self):
        code, text = self.run_tool('create', '--environment', 'homolog', '--name', 'claude-teste', '--days', '30', '--apply')
        key = next(line for line in self.lines if line.startswith('azk_'))
        self.assertEqual(code, 0)
        self.assertEqual(text.count(key), 1)
        secret = key.split('_', 2)[2]
        with self.store.transaction() as db:
            stored = db.agent_key(key.split('_')[1])
        self.assertNotIn(secret, json.dumps(stored))
        # the key works through the public edge and still cannot approve anything
        gateway = AgentGateway(CMS(self.store), media_hosts=[])
        status, payload, _ = process('GET', 'schema', {}, {'authorization': 'Bearer ' + key}, b'', gateway_factory=lambda: gateway)
        self.assertEqual(status, 200)
        self.assertEqual(process('POST', 'submissions/x/approve', {}, {'authorization': 'Bearer ' + key, 'content-type': 'application/json'}, b'{}', gateway_factory=lambda: gateway)[0], 401)

    def test_clipboard_mode_never_prints_the_key(self):
        copied = []
        code, text = self.run_tool('create', '--environment', 'homolog', '--name', 'claude-teste', '--apply', '--clipboard', clipboard=copied.append)
        self.assertEqual(code, 0)
        self.assertTrue(copied and copied[0].startswith('azk_'))
        self.assertNotIn(copied[0], text)

    def test_list_shows_metadata_but_never_hash_or_secret(self):
        self.run_tool('create', '--environment', 'homolog', '--name', 'chatgpt-teste', '--collections', 'content,media', '--apply')
        key = next(line for line in self.lines if line.startswith('azk_'))
        self.lines.clear()
        code, text = self.run_tool('list', '--environment', 'homolog')
        self.assertEqual(code, 0)
        self.assertIn('chatgpt-teste', text)
        self.assertIn('scopes=content,media', text)
        self.assertNotIn(key.split('_', 2)[2], text)
        with self.store.transaction() as db:
            self.assertNotIn('key_hash', json.dumps(db.agent_keys()))

    def test_revoke_and_validation(self):
        self.run_tool('create', '--environment', 'homolog', '--name', 'gemini-teste', '--apply')
        key = next(line for line in self.lines if line.startswith('azk_'))
        key_id = key.split('_')[1]
        self.assertEqual(self.run_tool('revoke', '--environment', 'homolog', '--id', key_id, '--apply')[0], 0)
        gateway = AgentGateway(CMS(self.store), media_hosts=[])
        self.assertEqual(process('GET', 'schema', {}, {'authorization': 'Bearer ' + key}, b'', gateway_factory=lambda: gateway)[0], 401)
        self.assertEqual(self.run_tool('revoke', '--environment', 'homolog', '--id', 'nonexistent', '--apply')[0], 1)
        for bad in (('--days', '0'), ('--days', '400'), ('--collections', 'pages'), ('--collections', '')):
            with self.assertRaises(SystemExit):
                manage_keys.run(['create', '--environment', 'homolog', '--name', 'x-teste', *bad], store_factory=self.factory, out=self.lines.append)

    def test_refuses_a_database_that_does_not_match_the_environment(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'CMS_SQL_DATABASE': 'anderzilla-cms-production'}):
            with self.assertRaises(SystemExit) as caught:
                manage_keys.default_store('homolog')
        self.assertIn('must be anderzilla-cms-homolog', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
