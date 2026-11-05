"""Only trusted host settings supply the managed SWA aliases."""
import os
import unittest
from unittest.mock import patch
from services.identity.runtime_config import configure_settings


class RuntimeSettingsTests(unittest.TestCase):
    def test_managed_aliases_map_to_canonical_names(self):
        with patch.dict(os.environ, {'AZ_ACCOUNT_ENV': 'homolog', 'CLERK_ISSUER': 'https://example.invalid'}, clear=True):
            configure_settings()
            self.assertEqual(os.environ['IDENTITY_ENV'], 'homolog')
            self.assertEqual(os.environ['CLERK_ISSUER'], 'https://example.invalid')

    def test_dedicated_function_settings_remain_supported(self):
        with patch.dict(os.environ, {'IDENTITY_ENV': 'production'}, clear=True):
            configure_settings()
            self.assertEqual(os.environ['IDENTITY_ENV'], 'production')
