"""Build the deployable zip of the content API for Azure Functions Flex Consumption (Linux, CPython 3.12).

Source files come only from an explicit allow-list (no directory is copied wholesale). Dependencies are installed as
Linux wheels (never a Windows virtualenv). The zip uses forward slashes, sorted entries and fixed timestamps, so the same
inputs give the same hash. A secret scan of the source files and a forbidden-name scan of the whole package must pass.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {'services/content-api': ('function_app.py', 'content_api.py', 'host.json', 'requirements.txt'),
           'services/cms': ('agent_api.py', 'core.py', 'commerce.py', 'storage.py')}
REQUIRED_PACKAGES = ('azure/functions', 'pytds', 'PIL', 'OpenSSL', 'certifi')
FORBIDDEN_NAMES = re.compile(r'(?i)(^|/)(\.env[^/]*|.*\.(pem|key|pfx|p12|sqlite3?|db|exe|dll|pyd)|cms-secrets\.json|content-api-[a-z]+\.json|local\.settings\.json|__pycache__)(/|$)')
SECRET_ASSIGNMENT = re.compile(r'(?i)\b(password|secret|token|api[_-]?key|connectionstring)\b\s*[:=]\s*[\'"][^\'"\s]{8,}[\'"]')
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scan_sources(folder):
    """Fail on anything that looks like an embedded credential in the files this repository owns."""
    problems = []
    for path in sorted(Path(folder).glob('*.py')):
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if SECRET_ASSIGNMENT.search(line):
                problems.append(f'{path.name}:{number}')
    return problems


PUBLIC_ALLOWED = re.compile(r'(^|/)certifi/cacert\.pem$')  # public CA bundle that certifi needs for verified TLS to Azure SQL


def forbidden_entries(entries):
    return sorted(name for name in entries if FORBIDDEN_NAMES.search(name) and not PUBLIC_ALLOWED.search(name))


def install_dependencies(package_dir, python=sys.executable):
    target = package_dir / '.python_packages' / 'lib' / 'site-packages'
    command = [python, '-m', 'pip', 'install', '--disable-pip-version-check', '--quiet', '--no-compile', '--only-binary=:all:',
               '--platform', 'manylinux2014_x86_64', '--platform', 'manylinux_2_28_x86_64', '--implementation', 'cp',
               '--python-version', '3.12', '--abi', 'cp312', '--abi', 'abi3', '--abi', 'none',
               '--target', str(target), '-r', str(package_dir / 'requirements.txt')]
    subprocess.run(command, check=True, timeout=600)
    for cache in list(target.rglob('__pycache__')):  # bytecode is rebuilt by the host; shipping it only adds noise
        shutil.rmtree(cache)
    if (target / 'bin').is_dir():  # console-script launchers written by pip on Windows (.exe); useless on Linux
        shutil.rmtree(target / 'bin')
    missing = [name for name in REQUIRED_PACKAGES if not (target / name).exists()]
    if missing:
        raise RuntimeError('Dependencies missing from the Linux package: ' + ', '.join(missing))
    return target


def build(output_dir, install=True, root=ROOT):
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError('Output already exists; packages are immutable.')
    package = output_dir / 'package'
    package.mkdir(parents=True)
    copied = {}
    for folder, names in SOURCES.items():
        for name in names:
            source = Path(root) / folder / name
            if not source.is_file():
                raise FileNotFoundError(f'{folder}/{name}')
            shutil.copy2(source, package / name)
            copied[name] = sha256(source)
    problems = scan_sources(package)
    if problems:
        raise ValueError('Possible embedded secret in: ' + ', '.join(problems))
    if install:
        install_dependencies(package)
    entries = sorted(path.relative_to(package).as_posix() for path in package.rglob('*') if path.is_file())
    bad = forbidden_entries(entries)
    if bad:
        raise ValueError('Forbidden files in the package: ' + ', '.join(bad[:5]))
    archive = output_dir / 'content-api.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in entries:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, (package / name).read_bytes())
    return {'zip': str(archive), 'sha256': sha256(archive), 'bytes': archive.stat().st_size, 'entries': len(entries),
            'sources': copied, 'dependenciesInstalled': install, 'topLevel': sorted({name.split('/')[0] for name in entries})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new directory (must not exist)')
    parser.add_argument('--no-install', action='store_true', help='skip pip (tests only)')
    args = parser.parse_args()
    print(json.dumps(build(args.output, install=not args.no_install), indent=2))


if __name__ == '__main__':
    main()
