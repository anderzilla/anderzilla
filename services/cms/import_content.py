"""One-time import of the sourced editorial archive. No fabricated records."""
import argparse
import json
import os
from pathlib import Path
from core import now, validate
from storage import AzureSQLStore, SQLiteStore


def import_discoveries(store, source):
    count = 0
    with store.transaction() as db:
        for item in json.loads(Path(source).read_text(encoding='utf-8-sig')):
            if db.record('content', item['id']):
                continue
            data = {key: item.get(key, '') for key in ('titlePT', 'titleEN', 'summaryPT', 'summaryEN', 'category', 'sourceName')}
            data.update(sourceUrl=item['url'], publishedAt=item['published'], slug=item['id'], bodyPT=item.get('fact', item['summaryPT']), bodyEN=item.get('factEN', item['summaryEN']))
            validate('content', data, approved=True)
            record = {'id': item['id'], 'version': 1, 'status': 'approved', 'data': data, 'updatedAt': now()}
            db.save_record('content', record)
            db.audit('archive-import', 'import_verified_archive', 'content', item['id'], 1)
            count += 1
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--database')
    parser.add_argument('--azure', action='store_true')
    args = parser.parse_args()
    if not args.azure and not args.database:
        parser.error('Use --database for local or --azure with verified environment settings.')
    print('Imported:', import_discoveries(AzureSQLStore() if args.azure else SQLiteStore(args.database), args.source))
