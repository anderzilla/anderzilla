import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from api import dispatch
from automation import Automation
from core import CMS, Error
from storage import SQLiteStore

ADMIN = {'id': 'admin', 'roles': ['anderzilla_admin']}
EDITOR = {'id': 'editor', 'roles': ['anderzilla_editor']}
COMMERCIAL = {'id': 'commercial', 'roles': ['anderzilla_commercial']}


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = SQLiteStore(Path(self.temp.name) / 'cms.sqlite')
        self.service = Automation(self.store, 'local')

    def tearDown(self):
        self.temp.cleanup()

    def request(self, key='run-create-key'):
        return {'processId': 'seo-audit', 'processVersion': 1, 'input': {'market': 'global', 'language': 'pt-BR'}, 'idempotencyKey': key}

    def change(self, run, action, key, **extra):
        return self.service.change(ADMIN, run['id'], 'transition', {'version': run['version'], 'reason': 'Operação manual de teste', 'action': action, 'idempotencyKey': key, **extra})

    def test_rbac_catalog_and_hidden_runs(self):
        catalog = self.service.processes(EDITOR)['items']
        self.assertNotIn('offer-check', {row['id'] for row in catalog})
        with self.assertRaises(Error):
            self.service.create(COMMERCIAL, self.request())
        run = self.service.create(EDITOR, self.request())
        with self.assertRaises(Error):
            self.service.get(COMMERCIAL, run['id'])
        self.assertEqual(self.service.list(COMMERCIAL)['items'], [])
        with self.assertRaises(Error):
            self.service.processes({'id': 'visitor', 'roles': ['authenticated']})

    def test_concurrent_replay_creates_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            rows = list(pool.map(lambda _: self.service.create(ADMIN, self.request()), range(2)))
        self.assertEqual(rows[0], rows[1])
        self.assertEqual(self.service.summary(ADMIN)['counts']['queued'], 1)
        self.assertFalse(rows[0]['externalDispatched'])

    def test_divergent_payload_and_cross_command_key_rejected(self):
        run = self.service.create(ADMIN, self.request())
        request = self.request()
        request['input']['market'] = 'br'
        with self.assertRaises(Error) as error:
            self.service.create(ADMIN, request)
        self.assertEqual(error.exception.code, 'idempotency_conflict')
        with self.assertRaises(Error):
            self.service.change(ADMIN, run['id'], 'cancel', {'version': 1, 'reason': 'Cancelled manually', 'idempotencyKey': 'run-create-key'})

    def test_cancel_replay_stale_version_and_terminal_state(self):
        run = self.service.create(ADMIN, self.request())
        body = {'version': 1, 'reason': 'Não executar', 'idempotencyKey': 'cancel-command'}
        cancelled = self.service.change(ADMIN, run['id'], 'cancel', body)
        self.assertEqual(cancelled['status'], 'cancelled')
        self.assertEqual(self.service.change(ADMIN, run['id'], 'cancel', body), cancelled)
        with self.assertRaises(Error):
            self.change(run, 'start', 'stale-start-key')
        with self.assertRaises(Error):
            self.change(cancelled, 'start', 'terminal-start-key')

    def test_retry_new_run_replay_and_limit(self):
        run = self.service.create(ADMIN, self.request())
        for attempt in (1, 2, 3):
            running = self.change(run, 'start', 'start-key-' + str(attempt))
            failed = self.change(running, 'fail', 'fail-key-' + str(attempt))
            body = {'version': failed['version'], 'reason': 'Revisar novamente', 'idempotencyKey': 'retry-key-' + str(attempt)}
            if attempt == 3:
                with self.assertRaises(Error):
                    self.service.change(ADMIN, failed['id'], 'retry', body)
                break
            retried = self.service.change(ADMIN, failed['id'], 'retry', body)
            self.assertEqual(self.service.change(ADMIN, failed['id'], 'retry', body), retried)
            self.assertEqual(retried['parentRunId'], failed['id'])
            self.assertEqual(retried['attempt'], attempt + 1)
            parent = self.service.get(ADMIN, failed['id'])
            self.assertEqual(parent['history'][-1]['reason'], body['reason'])
            self.assertEqual(parent['history'][-1]['actor'], ADMIN['id'])
            self.assertEqual(parent['history'][-1]['childRunId'], retried['id'])
            self.assertEqual(retried['history'][0]['reason'], body['reason'])
            self.assertEqual(retried['history'][0]['parentRunId'], parent['id'])
            with self.assertRaises(Error):
                self.service.change(ADMIN, parent['id'], 'retry', {**body, 'version': parent['version'], 'idempotencyKey': 'second-' + str(attempt)})
            run = retried

    def test_manual_completion_needs_evidence(self):
        run = self.change(self.service.create(ADMIN, self.request()), 'start', 'start-key')
        with self.assertRaises(Error):
            self.change(run, 'complete', 'complete-key')
        complete = self.change(run, 'complete', 'complete-key', evidence='Revisão manual registrada no ticket interno de teste')
        self.assertEqual(complete['history'][-1]['evidenceSource'], 'operator_reported')
        self.assertFalse(complete['externalDispatched'])

    def test_scope_environment_pagination_and_router(self):
        first = self.service.create(ADMIN, self.request('first-run-key'))
        self.service.create(ADMIN, self.request('second-run-key'))
        self.assertEqual(Automation(self.store, 'homolog').list(ADMIN)['items'], [])
        response = dispatch(CMS(self.store), ADMIN, 'GET', '/api/admin/automation/runs?limit=1', environment='local')
        self.assertEqual(len(response['items']), 1)
        self.assertEqual(response['nextCursor'], '1')
        self.assertIsNone(self.service.summary(ADMIN)['costs'])

    def test_invalid_inputs_and_versions(self):
        for update in ({'processVersion': 2}, {'input': {'market': 'br', 'language': 'pt-BR', 'url': 'https://example.com'}}, {'processId': 'shell-command'}):
            with self.assertRaises(Error):
                self.service.create(ADMIN, {**self.request(), **update})
        with self.assertRaises(Error):
            self.service.preview(ADMIN, {**self.request(), 'processId': 'report-custom'})
        with self.assertRaises(Error):
            self.service.preview(ADMIN, {**self.request(), 'processId': 'report-custom', 'input': {'market': 'br', 'language': 'en', 'periodStart': '2026-09-10', 'periodEnd': '2026-09-10'}})


if __name__ == '__main__':
    unittest.main()
