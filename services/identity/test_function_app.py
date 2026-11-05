"""Exercise the actual Functions host import, beyond isolated dispatch tests."""
import unittest
import os
from unittest.mock import patch
import azure.functions as func
from services.identity.function_app import app, identity_api


class HostTests(unittest.TestCase):
    def test_unexpected_failure_preserves_exact_origin_without_details(self):
        req = func.HttpRequest(method='GET', url='https://example.invalid/api/account/me',
                               headers={'Origin': 'https://anderzilla.com'}, body=b'')
        with patch.dict(os.environ, {'IDENTITY_AUTH_PROVIDER': 'clerk', 'IDENTITY_ALLOWED_ORIGIN': 'https://anderzilla.com'}), \
             patch('services.identity.clerk_api.dispatch_clerk', side_effect=RuntimeError('private-detail')):
            response = identity_api(req)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'https://anderzilla.com')
        self.assertNotIn(b'private-detail', response.get_body())

    def test_http_routes_have_separate_triggers(self):
        functions = app.get_functions()
        self.assertEqual(len(functions), 2)
        self.assertEqual({f.get_trigger().get_dict_repr()['route'] for f in functions},
                         {'account/{*path}', 'points/{*path}'})

    def test_request_limit_runs_through_real_entrypoint(self):
        req = func.HttpRequest(method='POST', url='https://example.invalid/api/account/onboarding', body=b'x' * 64001)
        self.assertEqual(identity_api(req).status_code, 413)
