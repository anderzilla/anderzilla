"""One-shot trusted CMS publisher. Deploys only the isolated Azure visual slot.

Run locally with --database PATH, or --azure and CMS_SQL_* environment settings.
This is an operator CLI, not an HTTP endpoint or an authentication bypass.
No scheduler is installed. An uncertain deployment remains deploying for reconciliation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'services' / 'cms'))
from core import CMS, Error, now
from storage import SQLiteStore, AzureSQLStore
from import_snapshot import transform, write_assets

PRINCIPAL = {'id': 'operator:cms-publisher', 'roles': ['anderzilla_admin']}
PREVIEW_URL = 'https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net'
ACTIVE = {'building', 'validated', 'deploying'}


@contextmanager
def staging_directory():
    # Next/webpack resolves junction targets incorrectly across Windows drives.
    # Keep the isolated source and its dependencies on the same volume.
    base = (ROOT / '.publisher-work').resolve() if os.name == 'nt' else Path(tempfile.gettempdir()).resolve()
    base.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='anderzilla-publisher-', dir=base)).resolve()
    try:
        yield stage
    finally:
        # Verify generated absolute scope before any recursive deletion on Windows.
        if stage.parent != base or not stage.name.startswith('anderzilla-publisher-'):
            raise RuntimeError('Unsafe staging cleanup target rejected.')
        dependencies = stage / 'web' / 'node_modules'
        if dependencies.is_symlink():
            dependencies.unlink()
        elif os.name == 'nt' and dependencies.exists():
            # Remove the junction itself without traversing the shared dependency tree.
            os.rmdir(dependencies)
        shutil.rmtree(stage)


def claim(cms, release_id=None):
    """Serialize all publication claims, not just duplicate claims of one release."""
    with cms.store.transaction() as db:
        releases = db.releases()
        if any(row['status'] in ACTIVE for row in releases):
            raise Error(409, 'publisher_busy', 'A release is active; reconcile it before publishing again.')
        candidates = [row for row in releases if row['status'] == 'queued' and (not release_id or row['id'] == release_id)]
        if not candidates:
            raise Error(409, 'nothing_queued', 'No matching queued release.')
        release = min(candidates, key=lambda row: row['createdAt'])
        release.update(status='building', updatedAt=now())
        db.update_release(release)
        db.audit(PRINCIPAL['id'], 'building', 'releases', release['id'], 1)
        snapshot = db.release(release['id'], snapshot=True)
        return release, snapshot


def digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def stage_app(root, destination):
    source = root / 'apps' / 'web'
    destination.mkdir()
    for directory in ('src', 'public', 'content'):
        if (source / directory).exists():
            shutil.copytree(source / directory, destination / directory)
    for name in ('package.json', 'package-lock.json', 'next.config.ts', 'next-env.d.ts', 'tsconfig.json', 'postcss.config.mjs', 'tailwind.config.ts'):
        if (source / name).exists():
            shutil.copy2(source / name, destination / name)
    dependencies = source / 'node_modules'
    if not dependencies.is_dir():
        raise RuntimeError('Install apps/web dependencies before running the publisher.')
    link = destination / 'node_modules'
    if os.name == 'nt':
        env = dict(os.environ, CMS_STAGE_DEPENDENCIES=str(dependencies), CMS_STAGE_LINK=str(link))
        subprocess.run([shutil.which('pwsh') or 'powershell', '-NoProfile', '-Command',
                        "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:CMS_STAGE_LINK -Target $env:CMS_STAGE_DEPENDENCIES | Out-Null"],
                       check=True, env=env, timeout=30)
    else:
        link.symlink_to(dependencies, target_is_directory=True)


def build(root, directory, snapshot, marker, preview=True):
    """Export the site from a snapshot. preview=True marks articles noindex (homolog and review builds);
    production-grade builds pass preview=False, like rebuild-production.py does."""
    stage_app(root, directory)
    target = directory / 'src' / 'components' / 'hub' / 'cms-published.json'
    target.write_text(json.dumps(transform(snapshot), ensure_ascii=False, indent=2), encoding='utf-8')
    write_assets(snapshot, directory / 'public')
    (directory / 'public' / 'cms-release.json').write_text(json.dumps(marker), encoding='utf-8')
    env = dict(os.environ, NEXT_OUTPUT='export', NEXT_TELEMETRY_DISABLED='1', CMS_PREVIEW='1' if preview else '0')
    subprocess.run([shutil.which('npm.cmd' if os.name == 'nt' else 'npm') or 'npm', 'run', 'build'], cwd=directory, env=env, check=True, timeout=600)
    artifact = directory / 'out'
    if not (artifact / 'index.html').is_file() or not (artifact / 'cms-release.json').is_file():
        raise RuntimeError('Build did not produce the expected static artifact.')
    return artifact


def deploy(root, artifact, azure_cli):
    subprocess.run([shutil.which('pwsh') or 'powershell', '-NoProfile', '-File',
                    str(root / 'infra' / 'azure' / 'deploy.ps1'), '-Environment', 'preview',
                    '-ArtifactPath', str(artifact), '-AzureCli', azure_cli], check=True, timeout=600)


def verify(marker):
    request = Request(PREVIEW_URL + '/cms-release.json?release=' + marker['releaseId'], headers={'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=30) as response:
        actual = json.loads(response.read(16384))
        if response.status != 200 or actual != marker:
            raise RuntimeError('Published release marker has not been verified; reconcile deployment.')
    with urlopen(PREVIEW_URL + '/?release=' + marker['releaseId'], timeout=30) as response:
        if response.status != 200:
            raise RuntimeError('Preview page is unavailable; reconcile deployment.')


def run(cms, release_id=None, root=ROOT, azure_cli='az', builder=build, deployer=deploy, verifier=verify):
    release, snapshot = claim(cms, release_id)
    snapshot['releaseId'] = release['id']
    marker = {'releaseId': release['id'], 'snapshotSha256': digest(snapshot), 'containsDemo': any(row['data'].get('isDemo') for rows in snapshot['collections'].values() for row in rows)}
    deploying = False
    try:
        with staging_directory() as temporary:
            artifact = builder(root, temporary / 'web', snapshot, marker)
            cms.update_release(PRINCIPAL, release['id'], 'validated')
            cms.update_release(PRINCIPAL, release['id'], 'deploying')
            deploying = True
            deployer(root, artifact, azure_cli)
            verifier(marker)
            return cms.update_release(PRINCIPAL, release['id'], 'deployed', PREVIEW_URL)
    except Exception:
        if not deploying:
            cms.update_release(PRINCIPAL, release['id'], 'failed')
        # Never mark failed if a deployment might already be live. No automatic resend.
        raise


def reconcile(cms, release_id):
    release = cms.releases(PRINCIPAL, release_id)
    if release['status'] != 'deploying':
        raise Error(409, 'invalid_transition', 'Only an uncertain deploying release can be reconciled.')
    snapshot = cms.releases(PRINCIPAL, release_id, snapshot=True)
    snapshot['releaseId'] = release_id
    verify({'releaseId': release_id, 'snapshotSha256': digest(snapshot), 'containsDemo': any(row['data'].get('isDemo') for rows in snapshot['collections'].values() for row in rows)})
    return cms.update_release(PRINCIPAL, release_id, 'deployed', PREVIEW_URL)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    store = parser.add_mutually_exclusive_group(required=True)
    store.add_argument('--database', type=Path)
    store.add_argument('--azure', action='store_true')
    parser.add_argument('--release-id')
    parser.add_argument('--azure-cli', default='az')
    parser.add_argument('--reconcile', action='store_true')
    args = parser.parse_args()
    if args.database and not args.database.is_file():
        parser.error('Database must already exist; initialize and approve content in the CMS first.')
    if args.reconcile and not args.release_id:
        parser.error('--reconcile requires --release-id')
    cms = CMS(AzureSQLStore() if args.azure else SQLiteStore(args.database))
    try:
        result = reconcile(cms, args.release_id) if args.reconcile else run(cms, args.release_id, azure_cli=args.azure_cli)
        print(json.dumps(result))
    except Exception as error:
        # Driver exceptions may contain connection information; do not print their payloads.
        print('Publisher stopped (' + type(error).__name__ + '). Inspect release status; deploying requires reconciliation.', file=sys.stderr)
        sys.exit(1)
