import json
import tempfile
import unittest
from pathlib import Path
from core import CMS, Error
from storage import SQLiteStore
from reporting import operations, period, csv_cell

ADMIN = {'id': 'report-test', 'roles': ['anderzilla_admin']}


class ReportingTests(unittest.TestCase):
    def test_period_uses_local_midnight_and_exclusive_end(self):
        start, end, zone = period({'start':'2026-09-01', 'end':'2026-09-02'})
        self.assertEqual(start, '2026-09-01T03:00:00+00:00')
        self.assertEqual(end, '2026-09-02T03:00:00+00:00')
        with self.assertRaises(Error):
            period({'start':'2026-09-02','end':'2026-09-01'})

    def test_snapshot_isolated_period_environment_and_private_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            cms = CMS(SQLiteStore(Path(folder) / 'test.db'))
            with cms.store.transaction() as db:
                for index, (env, stamp) in enumerate([('homolog','2026-09-01T03:00:00+00:00'),('production','2026-09-01T04:00:00+00:00'),('homolog','2026-09-02T03:00:00+00:00')]):
                    row = {'id':str(index),'processId':'seo-audit','status':'succeeded','createdAt':stamp,'privateNote':'PRIVATE-SENTINEL'}
                    db.execute('INSERT INTO automation_runs(id,environment,process_id,created_at,status,document) VALUES(?,?,?,?,?,?)',(str(index),env,'seo-audit',stamp,'succeeded',json.dumps(row)))
            result = operations(cms, ADMIN, {'start':'2026-09-01','end':'2026-09-02'}, 'homolog')
            self.assertEqual(result['snapshot']['coverage']['observedRuns'],1)
            self.assertFalse(result['snapshot']['financial']['available'])
            self.assertNotIn('PRIVATE-SENTINEL',json.dumps(result))
            with self.assertRaises(Error):
                operations(cms, {'id':'editor','roles':['anderzilla_editor']}, {'start':'2026-09-01','end':'2026-09-02'}, 'homolog')

    def test_csv_neutralizes_formula_prefixes(self):
        for value in ('=1+2','  +cmd','-1','@SUM(A1)','\t=1'):
            self.assertTrue(csv_cell(value).startswith("'"))
        self.assertEqual(csv_cell('seo-audit'), 'seo-audit')
