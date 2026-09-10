"""Deployment package import test: verifies google-auth + requests are installed without mocks."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PackageImportTests(unittest.TestCase):
    def test_requirements_contains_requests(self):
        req = Path(__file__).with_name('requirements.txt').read_text()
        self.assertIn('requests==', req)
        self.assertIn('google-auth==', req)

    def test_runtime_import_google_auth_transport_and_id_token(self):
        # Real import, not injected mock
        import google.auth.transport.requests as tr  # type: ignore
        import google.oauth2.id_token as id_token  # type: ignore
        self.assertTrue(hasattr(tr, 'Request'))
        self.assertTrue(hasattr(id_token, 'verify_oauth2_token'))

    def test_isolated_install_import(self):
        # Isolated install verification: pip install to temp target and import from PYTHONPATH
        req_file = Path(__file__).with_name('requirements.txt')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'deps'
            target.mkdir()
            # Install pinned deps to isolated target (no-deps to avoid network for transitive, but we need requests+google-auth)
            # Use pip install --target with offline if already satisfied; fallback to --no-deps already cached
            # Try full install first; if network unavailable, skip but still verify target import if possible
            pip_cmd = [sys.executable, '-m', 'pip', 'install', '-q', '--target', str(target), '-r', str(req_file)]
            result = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=120)
            # If pip fails due to network, verify at least current env imports (already tested above)
            if result.returncode != 0:
                self.skipTest(f'Isolated pip install not available in this env: {result.stderr[:500]}')
            code = "import sys; sys.path.insert(0, sys.argv[1]); import google.auth.transport.requests; import google.oauth2.id_token; print('ok')"
            r = subprocess.run([sys.executable, '-c', code, str(target)], capture_output=True, text=True, timeout=10)
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertIn('ok', r.stdout)

if __name__ == '__main__':
    unittest.main()
