import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from api import dispatch
from core import CMS, Error
from storage import AzureSQLStore


class HealthTests(unittest.TestCase):
    def test_diagnostic_restricted_to_admin(self):
        store = SimpleNamespace(health=lambda: {'healthy': True})
        with self.assertRaises(Error):
            dispatch(CMS(store), {'id': 'editor', 'roles': ['anderzilla_editor']}, 'GET', '/api/admin/health')
        result = dispatch(CMS(store), {'id': 'admin', 'roles': ['anderzilla_admin']}, 'GET', '/api/admin/health')
        self.assertTrue(result['healthy'])

    def test_driver_error_is_sanitized(self):
        configuration = {key: 'PRIVATE-SENTINEL' for key in ('CMS_SQL_SERVER', 'CMS_SQL_DATABASE', 'CMS_SQL_USER', 'CMS_SQL_PASSWORD')}
        with patch.dict('sys.modules', {'certifi': SimpleNamespace(), 'pytds': SimpleNamespace(), 'OpenSSL': SimpleNamespace()}), patch.dict('os.environ', configuration), patch.object(AzureSQLStore, 'connect', side_effect=TimeoutError('connection timed out PRIVATE-SENTINEL')):
            result = AzureSQLStore().health()
        self.assertEqual(result['stage'], 'connect')
        self.assertEqual(result['category'], 'timeout')
        self.assertEqual(result['exceptionType'], 'TimeoutError')
        self.assertNotIn('PRIVATE-SENTINEL', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
