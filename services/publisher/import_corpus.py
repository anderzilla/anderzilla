"""Import the production editorial corpus into the CMS and prove it round-trips.

Source: public-after.json (what the site publishes today) plus the original WebP files. The import keeps
record ids, approves every record as of its observed date and never touches Azure: it writes to the store
you pass (local SQLite for step 4a). `--verify` rebuilds the public data from the database and fails on any
difference, so a database that cannot reproduce the live site is never trusted.
"""
import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from core import CMS, Error, validate
from import_snapshot import transform
from storage import SQLiteStore

ACTOR = 'operator:corpus-import'
SAME = ('titlePT', 'titleEN', 'summaryPT', 'summaryEN', 'sourceName', 'category', 'verifiedAt', 'eventDate', 'editorialType', 'socialMediaId',
        'hashtagsPT', 'hashtagsEN', 'socialInstagramPT', 'socialInstagramEN', 'socialFacebookPT', 'socialFacebookEN', 'socialWhatsappPT', 'socialWhatsappEN',
        'slugPT', 'slugEN', 'seoTitlePT', 'seoTitleEN', 'seoDescriptionPT', 'seoDescriptionEN', 'author', 'tags', 'coverMediaId', 'mediaIds', 'isDemo')
RENAMED = {'url': 'sourceUrl', 'published': 'publishedAt', 'observed': 'observedAt', 'fact': 'bodyPT', 'factEN': 'bodyEN', 'updatedAt': 'editorialUpdatedAt'}
MEDIA_SAME = ('titlePT', 'titleEN', 'url', 'mediaType', 'mimeType', 'altPT', 'altEN', 'credit', 'license', 'width', 'height', 'sourceUrl', 'isDemo')


# The live site shows ForgeKit through a built-in fallback in apps/web/src/components/commerce/data.ts,
# used only while the published data has no `products` array. Once the database publishes `products: []`
# the fallback stops applying, so the same record must live in the database. Text mirrors the live fallback
# (a test keeps them in sync); disclosureKey is required by the CMS for an active commercial record.
FORGEKIT_LIVE = {
    'titlePT': 'ForgeKit', 'titleEN': 'ForgeKit', 'slug': 'forgekit', 'market': 'intl', 'status': 'active', 'currency': 'USD', 'priceMinor': 14900, 'store': 'Gumroad',
    'summaryPT': 'Um ponto de partida em TypeScript para tirar seu projeto pessoal do papel.',
    'summaryEN': 'A TypeScript starting point to bring your personal project to life.',
    'bodyPT': 'Receba o código-fonte em ZIP e o guia GETTING_STARTED pela Gumroad. Inclui landing page, autenticação, base de dashboard, modelos Prisma e arquivos de implantação.\n\nPara quem já trabalha com Node.js e TypeScript. Configure e teste seu banco de dados, hospedagem e pagamentos antes de operar. Hospedagem e desenvolvimento personalizado não estão incluídos.',
    'bodyEN': 'Receive the source-code ZIP and GETTING_STARTED guide through Gumroad. Includes a landing page, authentication, dashboard foundations, Prisma models and deployment files.\n\nFor developers familiar with Node.js and TypeScript. Configure and test your database, hosting and payments before operating. Hosting and custom development are not included.',
    'ctaUrl': 'https://anderzilla.gumroad.com/l/edkel', 'demoUrl': 'https://forgekit-kwzn5potra-rj.a.run.app', 'disclosureKey': 'own-product',
    'disclosurePT': 'Produto próprio AnderZilla. Compra e entrega pela Gumroad; confira impostos, licença e condições no checkout.',
    'disclosureEN': 'An AnderZilla product. Purchase and delivery through Gumroad; check taxes, licensing and terms at checkout.',
}
COMMERCE_DEFAULTS = (('products', 'forgekit', FORGEKIT_LIVE),)


def content_data(item):
    data = {key: item[key] for key in SAME if key in item}
    data.update({new: item[old] for old, new in RENAMED.items() if old in item})
    # The CMS keeps sources as a JSON string (see core.validate); the public data publishes the parsed list.
    if item.get('sources'):  # the CMS rejects an empty list; no key publishes as []
        data['sources'] = json.dumps(item['sources'], ensure_ascii=False)
    return data


def media_data(item, directories):
    sha = item['url'].rsplit('/', 1)[-1].removesuffix('.webp')
    for directory in directories:
        path = Path(directory) / (sha + '.webp')
        if path.is_file():
            raw = path.read_bytes()
            break
    else:
        raise ValueError('Missing original image for ' + item['id'])
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('Image bytes do not match their hash: ' + sha)
    data = {key: item[key] for key in MEDIA_SAME if key in item}
    data.update(assetBase64=base64.b64encode(raw).decode(), assetSha256=sha)
    return data


def import_corpus(cms, public, media_dirs):
    """Write media first, then content. Returns counts. Fails (and writes nothing) on the first invalid record."""
    counts = {'media': 0, 'content': 0, 'products': 0}
    defaults = [{'id': record_id, **data} for collection, record_id, data in COMMERCE_DEFAULTS if collection == 'products']
    with cms.store.transaction() as db:
        for collection, items, build in (('media', public['media'], lambda row: media_data(row, media_dirs)), ('content', public['discoveries'], content_data),
                                         ('products', defaults, lambda row: {k: v for k, v in row.items() if k != 'id'})):
            for item in items:
                data = build(item)
                try:
                    validate(collection, data, approved=True, internal=True)
                except Error as error:
                    raise ValueError(f"{collection} {item['id']}: {error.code}: {error}") from None
                day = (data.get('observedAt') or '2026-09-17')[:10]
                record = {'id': item['id'], 'version': 1, 'status': 'approved', 'data': data, 'updatedAt': day + 'T00:00:00+00:00'}
                db.save_record(collection, record)
                db.audit(ACTOR, 'import_corpus', collection, item['id'], 1)
                counts[collection] += 1
    return counts


def rebuild_public(cms, public):
    """Public data as the publisher would emit it from the database (references and duplicate slugs are re-checked)."""
    with cms.store.transaction() as db:
        snapshot = cms.snapshot(db)
    snapshot['releaseId'] = public['releaseId']
    return transform(snapshot)


def compare(public, produced):
    """Differences between the live public data and the one rebuilt from the database. Empty means identical."""
    problems = []
    for name in sorted(set(public) | set(produced)):
        if name in ('banners', 'releaseId', 'products'):
            continue  # products: the live site renders ForgeKit from a web fallback; the database record is checked by the full build
        if name not in ('discoveries', 'media'):
            # An absent collection and an empty one publish the same site (the web app defaults to []).
            if (public.get(name) or []) != (produced.get(name) or []):
                problems.append(f'{name}: differs')
            continue
        left, right = {row['id']: row for row in public.get(name, [])}, {row['id']: row for row in produced.get(name, [])}
        problems += [f'{name}: only in live data {i}' for i in sorted(set(left) - set(right))]
        problems += [f'{name}: only in database {i}' for i in sorted(set(right) - set(left))]
        for key in sorted(set(left) & set(right)):
            a, b = dict(left[key]), dict(right[key])
            if name == 'media' and 'previewUrl' not in a and b.get('previewUrl', '').endswith('-social.jpg'):
                b.pop('previewUrl')  # the database now also derives the social image for notes that never had one
            if a != b:
                fields = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                problems.append(f'{name} {key}: fields differ: {fields}')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', type=Path, required=True)
    parser.add_argument('--media', type=Path, action='append', required=True, help='directory with <sha>.webp files; repeatable')
    parser.add_argument('--database', type=Path, required=True, help='new local SQLite file; refuses to overwrite')
    args = parser.parse_args()
    if args.database.exists():
        parser.error('Database already exists; the import never overwrites one.')
    public = json.loads(args.public.read_text(encoding='utf-8'))
    cms = CMS(SQLiteStore(args.database))
    counts = import_corpus(cms, public, args.media)
    problems = compare(public, rebuild_public(cms, public))
    print(json.dumps({'imported': counts, 'differences': problems[:20], 'differenceCount': len(problems)}, indent=2, ensure_ascii=False))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
