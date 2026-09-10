"""Trusted operator import through the CMS domain, with revisions and audit.

Uses existing CMS_SQL_* credentials for Azure, exactly as the operator publisher.
This is never an HTTP adapter; it cannot grant a browser an administrative role.
"""
import argparse
import json
from pathlib import Path
from core import CMS, validate
from storage import AzureSQLStore, SQLiteStore

PRINCIPAL = {'id': 'operator:editorial-launch', 'name': 'Editorial launch operator', 'roles': ['anderzilla_admin']}


def import_manifest(cms, manifest, approve=False, progress=None):
    items = manifest.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ValueError('Expected 1–100 items')
    keys, slugs = set(), set()
    for item in items:
        if not isinstance(item, dict) or not item.get('key') or item['key'] in keys:
            raise ValueError('Every item needs a unique key')
        keys.add(item['key'])
        data = item.get('data', {})
        validate('content', data, approved=True)
        for lang in ('PT', 'EN'):
            slug = data.get('slug' + lang)
            if not slug or (lang, slug) in slugs:
                raise ValueError('Unique translated slugs required')
            slugs.add((lang, slug))
    existing = cms.list(PRINCIPAL, 'content')['items']
    media = cms.list(PRINCIPAL, 'media')['items']
    report = []
    for item in items:
        data = dict(item['data'])
        row = next((row for row in existing if row['data'].get('slugPT') == data['slugPT'] or row['data'].get('slugEN') == data['slugEN']), None)
        if row:
            if row['data'].get('sourceUrl') != data['sourceUrl']:
                raise ValueError('Existing slug has a different source: ' + item['key'])
            # Preserve all editorial changes; retry never replaces an existing record.
            action = 'preserved'
        else:
            for field, reference in (('cover', 'coverMediaId'), ('socialImage', 'socialMediaId')):
                if not item.get(field):
                    continue
                cover = item[field]
                image = next((m for m in media if m['data'].get('titlePT') == cover['filename']), None)
                if not image:
                    image = cms.upload_media(PRINCIPAL, cover)
                    media.append(image)
                if image['status'] != 'approved':
                    image = cms.save(PRINCIPAL, 'media', None, image['id'], image['version'], 'approve')
                data[reference] = image['id']
            row = cms.save(PRINCIPAL, 'content', data)
            existing.append(row)
            if approve:
                row = cms.save(PRINCIPAL, 'content', None, row['id'], row['version'], 'approve')
            action = 'created'
        event = {'key': item['key'], 'id': row['id'], 'status': row['status'], 'version': row['version'], 'action': action}
        report.append(event)
        if progress:
            progress(event)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--azure', action='store_true')
    target.add_argument('--database', type=Path)
    parser.add_argument('--approve', action='store_true', help='Approve newly created articles after CMS validation')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    cms = CMS(AzureSQLStore() if args.azure else SQLiteStore(args.database))
    report = import_manifest(cms, manifest, args.approve, lambda event: print(json.dumps(event, ensure_ascii=True), flush=True))
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
