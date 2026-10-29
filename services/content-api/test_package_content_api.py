import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('package_content_api', ROOT / 'infra' / 'azure' / 'package_content_api.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageContentApiTest(unittest.TestCase):
    def test_zip_has_only_the_allow_listed_files_with_posix_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            result = packager.build(Path(folder) / 'out', install=False)
            with zipfile.ZipFile(result['zip']) as bundle:
                names = bundle.namelist()
            expected = sorted(name for names in packager.SOURCES.values() for name in names)
            self.assertEqual(sorted(names), expected)
            self.assertFalse([name for name in names if '\\' in name])
            self.assertEqual(result['entries'], len(expected))
            self.assertFalse([name for name in names if name.startswith('test_')])  # tests never ship

    def test_build_is_reproducible(self):
        with tempfile.TemporaryDirectory() as folder:
            first = packager.build(Path(folder) / 'a', install=False)
            second = packager.build(Path(folder) / 'b', install=False)
            self.assertEqual(first['sha256'], second['sha256'])

    def test_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                packager.build(Path(folder), install=False)

    def test_secret_scan_and_forbidden_names(self):
        with tempfile.TemporaryDirectory() as folder:
            sample = Path(folder)
            (sample / 'ok.py').write_text('password = os.environ["CMS_SQL_PASSWORD"]\n', encoding='utf-8')
            self.assertEqual(packager.scan_sources(sample), [])
            (sample / 'bad.py').write_text('PASSWORD = "hunter2hunter2"\n', encoding='utf-8')
            self.assertEqual(packager.scan_sources(sample), ['bad.py:1'])
        bad = packager.forbidden_entries(['function_app.py', '.env', '.env.local', 'x/key.pem', 'cms.sqlite3', 'content-api-homolog.json', 'a/__pycache__/m.pyc', 'local.settings.json'])
        self.assertEqual(len(bad), 7)
        self.assertEqual(len(packager.forbidden_entries(['bin/tool.exe', 'x/y.dll', 'x/z.pyd'])), 3)  # Windows binaries never ship to Linux
        self.assertEqual(packager.forbidden_entries(['function_app.py', 'agent_api.py', 'host.json', 'PIL/Image.py', 'azure/functions/__init__.py']), [])
        # certifi's public CA bundle is required; any other .pem is still refused
        self.assertEqual(packager.forbidden_entries(['.python_packages/lib/site-packages/certifi/cacert.pem']), [])
        self.assertEqual(packager.forbidden_entries(['.python_packages/lib/site-packages/other/private.pem']), ['.python_packages/lib/site-packages/other/private.pem'])

    def test_the_real_shipped_sources_pass_the_secret_scan(self):
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            for directory, names in packager.SOURCES.items():
                for name in names:
                    if name.endswith('.py'):
                        shutil.copy(ROOT / directory / name, folder)
            self.assertEqual(sorted(path.name for path in Path(folder).glob('*.py')), sorted(n for names in packager.SOURCES.values() for n in names if n.endswith('.py')))
            self.assertEqual(packager.scan_sources(folder), [])

    def test_packaged_files_match_the_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            result = packager.build(Path(folder) / 'out', install=False)
            for name, digest in result['sources'].items():
                source = next(ROOT / folder_name / name for folder_name, names in packager.SOURCES.items() if name in names)
                self.assertEqual(packager.sha256(source), digest)


if __name__ == '__main__':
    unittest.main()
