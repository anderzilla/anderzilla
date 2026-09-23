"""Rebuild current code with the verified production editorial corpus; never deploy.

Default is read-only preflight. Pass --build after the source tree is ready.

A complete sha256 match of the launch directory is the historical rollback bundle.
This rebuild copies only media/ and cms-release.json from that directory, then
exports the current app with the editorial public-after.json corpus. When the
HTML/_next half of the bundle is absent, preflight continues if every media
file and cms-release.json match production-artifact-sha256.json and no file
that is present has a different hash. Any hash mismatch fails closed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.deploy/production-40565a1a-f845-4294-b216-1cff2540065a-launch'
DATA = ROOT.parent / 'AnderZilla-docs/editorial/launch-2026-09-10/real-media-2026-09-16'
sys.path.insert(0, str(ROOT / 'services/publisher'))
from run_release import staging_directory, stage_app


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    manifest = json.loads((DATA / 'production-artifact-sha256.json').read_text(encoding='utf-8'))
    public = json.loads((DATA / 'public-after.json').read_text(encoding='utf-8'))
    if len(public['discoveries']) != 60 or len(public['media']) != 231:
        raise ValueError('Unexpected editorial corpus; review the baseline explicitly.')
    source_root = SOURCE.resolve()
    missing = []
    for name, expected in manifest.items():
        path = (SOURCE / name).resolve()
        if not path.is_relative_to(source_root):
            raise ValueError('Production rollback artifact mismatch: ' + name)
        if not path.is_file():
            missing.append(name)
            continue
        if digest(path) != expected:
            raise ValueError('Production rollback artifact mismatch: ' + name)
    required = [name for name in missing if name.startswith('media/') or name == 'cms-release.json']
    if required:
        raise ValueError('Production rollback artifact mismatch: ' + required[0])
    if not (SOURCE / 'media').is_dir():
        raise ValueError('Expected all 462 original media files.')
    media = {path.name: digest(path) for path in (SOURCE / 'media').iterdir() if path.is_file()}
    if len(media) != 462:
        raise ValueError('Expected all 462 original media files.')
    for name, expected in manifest.items():
        if name.startswith('media/') and media.get(name.split('/', 1)[1]) != expected:
            raise ValueError('Production rollback artifact mismatch: ' + name)
    marker = json.loads((SOURCE / 'cms-release.json').read_text(encoding='utf-8'))
    if marker != {'releaseId': '40565a1a-f845-4294-b216-1cff2540065a', 'snapshotSha256': 'c424f7ab817c2e5d9452878e9e59d01b4ebf6869051dfdcc94467c9982f1eb73', 'containsDemo': False}:
        raise ValueError('Unexpected editorial release marker.')
    return public, media, marker, not missing


def verify_export(out, public, media):
    sitemap = (out / 'sitemap.xml').read_text(encoding='utf-8')
    for item in public['discoveries']:
        for lang in ('pt', 'en'):
            slug = item['slug' + lang.upper()]
            candidates = (out / lang / 'radar' / (slug + '.html'), out / lang / 'radar' / slug / 'index.html')
            page = next((p for p in candidates if p.is_file()), None)
            if page is None or f'/{lang}/radar/{slug}' not in sitemap:
                raise ValueError('Missing preserved article: ' + lang + '/' + slug)
            html = page.read_text(encoding='utf-8')
            if 'noindex' in html or '\ufffd' in html:
                raise ValueError('Article is not production-ready: ' + str(page))
    for name, expected in media.items():
        if not (out / 'media' / name).is_file() or digest(out / 'media' / name) != expected:
            raise ValueError('Published media changed or disappeared: ' + name)
    if 'Disallow: /\n' in (out / 'robots.txt').read_text(encoding='utf-8'):
        raise ValueError('Production must be indexable.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--output-name', default='')
    args = parser.parse_args()
    public, media, marker, full_tree = preflight()
    report = {'rollbackArtifact': str(SOURCE), 'publicData': str(DATA / 'public-after.json'), 'articles': 60, 'articlePages': 120, 'mediaFiles': len(media), 'baselineVerified': True, 'fullTreeVerified': full_tree, 'mediaVerified': True}
    if not args.build:
        print(json.dumps(report, indent=2))
        return
    name = args.output_name or 'production-rebuilt-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if not name.startswith('production-') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):
        raise ValueError('Output must be a new production-* directory name under .deploy.')
    target = ROOT / '.deploy' / name
    if target.exists():
        raise ValueError('Output already exists; immutable artifacts are never overwritten.')
    with staging_directory() as stage:
        web = stage / 'web'
        stage_app(ROOT, web)
        source_files = {p.relative_to(web).as_posix(): digest(p) for p in (web / 'src').rglob('*') if p.is_file()}
        for filename in ('package.json', 'package-lock.json', 'next.config.ts', 'tsconfig.json'):
            if (web / filename).is_file():
                source_files[filename] = digest(web / filename)
        report['sourceSha256'] = hashlib.sha256(json.dumps(source_files, sort_keys=True).encode()).hexdigest()
        report['builtAt'] = datetime.now(timezone.utc).isoformat()
        report['gitCommit'] = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        (web / 'src/components/hub/cms-published.json').write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')
        shutil.copytree(SOURCE / 'media', web / 'public/media', dirs_exist_ok=True)
        (web / 'public/cms-release.json').write_text(json.dumps(marker), encoding='utf-8')
        env = dict(os.environ, NEXT_OUTPUT='export', NEXT_TELEMETRY_DISABLED='1', CMS_PREVIEW='0')
        subprocess.run([shutil.which('npm.cmd' if os.name == 'nt' else 'npm') or 'npm', 'run', 'build'], cwd=web, env=env, check=True, timeout=900)
        out = web / 'out'
        verify_export(out, public, media)
        shutil.copytree(out, target)
    report.update(artifact=str(target), editorialRelease=marker, deployed=False)
    (target.parent / (name + '-build.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    hashes = {p.relative_to(target).as_posix(): digest(p) for p in target.rglob('*') if p.is_file()}
    (target.parent / (name + '-sha256.json')).write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
