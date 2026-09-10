import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import rag


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write('README.md', '# AnderZilla\nPublic personal publication\n')
        self.write('strategy/plan.md', '# Monetização\nCloud Run budget and games.\nPT English comparison\n')

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='utf-8')

    def test_citation_and_accent_search(self):
        rag.build(self.root)
        hit = rag.search(self.root, 'monetizacao')['results'][0]
        self.assertEqual(hit['path'], 'strategy/plan.md')
        self.assertEqual(hit['citation'], 'strategy/plan.md:1')
        self.assertEqual(hit['sha256'], rag.digest((self.root / hit['path']).read_bytes()))
        self.assertEqual(rag.read(self.root, hit['path'], 2, 1)['text'], 'Cloud Run budget and games.')

    def test_isolation_and_secret_quarantine(self):
        for name in ('private/private.md', 'strategy/private/hide.md', 'strategy/archive/old.md', 'docs/CONTEXT.md', 'apps/code.md', 'ai/secret.md'):
            self.write(name, 'confidentialunique')
        self.write('operations/leak.md', 'API_KEY=abcdefghijk123456789\nconfidentialunique')
        result = rag.build(self.root)
        self.assertEqual(result['documents'], 2)
        self.assertEqual(rag.search(self.root, 'confidentialunique')['results'], [])
        self.assertEqual(result['omitted'][0]['path'], 'operations/leak.md')

    def test_traversal_and_nonindexed(self):
        rag.build(self.root)
        for path in ('../README.md', '/README.md', 'C:/README.md', 'strategy/../../README.md', 'strategy\\plan.md', 'docs/CONTEXT.md', 'strategy/missing.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                rag.read(self.root, path)

    def test_stale_add_change_delete(self):
        for action in ('change', 'add', 'delete'):
            rag.build(self.root)
            if action == 'change':
                self.write('strategy/plan.md', 'Changed corpus')
            elif action == 'add':
                self.write('decisions/new.md', 'New decision')
            else:
                (self.root / 'decisions/new.md').unlink()
            with self.assertRaisesRegex(ValueError, 'Stale'):
                rag.search(self.root, 'games')

    def test_query_syntax_is_literal_tokens(self):
        rag.build(self.root)
        self.assertEqual(rag.query_tokens('cloud* NEAR(run) OR "x"'), '"cloud" AND "NEAR" AND "run" AND "OR" AND "x"')
        self.assertEqual(rag.search(self.root, 'cloud*')['results'][0]['path'], 'strategy/plan.md')
        self.assertEqual(rag.search(self.root, '" OR 1=1 --')['results'], [])
        for query in ('***', 'x' * 513, 123):
            with self.assertRaises(ValueError):
                rag.search(self.root, query)

    def test_bounded_output(self):
        self.write('strategy/long.md', 'longword ' * 2500)
        rag.build(self.root)
        self.assertLessEqual(len(rag.search(self.root, 'longword')['results'][0]['text']), 1400)
        self.assertLessEqual(len(rag.read(self.root, 'strategy/long.md')['text']), 10000)
        with self.assertRaises(ValueError):
            rag.search(self.root, 'games', 1000)

    def test_foreign_index_and_empty_corpus(self):
        rag.build(self.root)
        with tempfile.TemporaryDirectory() as other:
            other = Path(other)
            (other / '.cache').mkdir()
            shutil.copy(self.root / '.cache/rag.sqlite3', other / '.cache/rag.sqlite3')
            with self.assertRaisesRegex(ValueError, 'another root'):
                rag.search(other, 'games')
            with self.assertRaisesRegex(ValueError, 'No approved'):
                rag.build(other)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'outside.md'
            target.write_text('externalunique')
            try:
                (self.root / 'strategy/link.md').symlink_to(target)
            except OSError:
                self.skipTest('OS does not permit creating symlinks')
            rag.build(self.root)
            self.assertEqual(rag.search(self.root, 'externalunique')['results'], [])
            with self.assertRaises(ValueError):
                rag.read(self.root, 'strategy/link.md')

    def test_stdio_lifecycle_and_read_only_tools(self):
        rag.build(self.root)
        requests = [
            {'jsonrpc': '2.0', 'id': 0, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-11-25'}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'search', 'arguments': {'query': 'games'}}},
            {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call', 'params': {'name': 'read', 'arguments': {'path': '../README.md'}}},
            {'jsonrpc': '2.0', 'id': 5, 'method': 'tools/call', 'params': {'name': 'build', 'arguments': {}}},
        ]
        proc = subprocess.run([sys.executable, str(Path(rag.__file__)), '--root', str(self.root), 'serve'], input='\n'.join(json.dumps(r) for r in requests) + '\n', capture_output=True, text=True, encoding='utf-8', check=True)
        answers = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(answers), 6)
        self.assertIn('error', answers[0])
        self.assertEqual(answers[1]['result']['protocolVersion'], '2025-11-25')
        self.assertEqual([t['name'] for t in answers[2]['result']['tools']], ['search', 'read'])
        evidence = json.loads(answers[3]['result']['content'][0]['text'])
        self.assertTrue(evidence['results'])
        self.assertTrue(answers[4]['result']['isError'])
        self.assertTrue(answers[5]['result']['isError'])
        self.assertEqual(proc.stderr, '')

    @unittest.skipUnless(os.name == 'nt', 'Windows junction test')
    def test_windows_junction_isolation(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / 'hidden.md').write_text('externaljunctionunique')
            link = self.root / 'strategy' / 'junction'
            # Paths originate from tempfile, not user or shell-controlled input.
            proc = subprocess.run(['powershell', '-NoProfile', '-Command', f"New-Item -ItemType Junction -Path '{link}' -Target '{outside}' | Out-Null"], capture_output=True)
            if proc.returncode:
                self.skipTest('OS does not permit junction creation')
            try:
                rag.build(self.root)
                self.assertEqual(rag.search(self.root, 'externaljunctionunique')['results'], [])
                with self.assertRaises(ValueError):
                    rag.read(self.root, 'strategy/junction/hidden.md')
            finally:
                os.rmdir(link)


if __name__ == '__main__':
    unittest.main()
