"""Validate an approved CMS snapshot and emit only public hub data (no HTML execution)."""
import argparse
import base64
import hashlib
import io
import ipaddress
import re
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image

CATEGORIES = {'games', 'consoles', 'celulares', 'ia', 'gadgets', 'curiosidades'}
NEWSROOM = ('verifiedAt', 'eventDate', 'editorialType', 'socialMediaId', 'hashtagsPT', 'hashtagsEN', 'socialInstagramPT', 'socialInstagramEN', 'socialFacebookPT', 'socialFacebookEN', 'socialWhatsappPT', 'socialWhatsappEN')

def public_sources(value):
    sources = json.loads(value) if value else []
    if not isinstance(sources, list) or len(sources) > 20:
        raise ValueError('Invalid source list')
    result = []
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get('name'), str) or not source['name'].strip():
            raise ValueError('Invalid source')
        row = {'name': source['name'], 'url': https(source['url'])}
        if source.get('publishedAt'):
            datetime.fromisoformat(source['publishedAt'].replace('Z', '+00:00'))
            row['publishedAt'] = source['publishedAt']
        if isinstance(source.get('note'), str):
            row['note'] = source['note']
        result.append(row)
    return result

def write_assets(snapshot, public_dir):
    """Materialize only approved, hashed WebP uploads; never trust a supplied path."""
    total = 0
    for row in snapshot.get('collections', {}).get('media', []):
        data = row['data']
        if 'assetBase64' not in data:
            continue
        raw = base64.b64decode(data['assetBase64'], validate=True)
        total += len(raw)
        sha = hashlib.sha256(raw).hexdigest()
        if row.get('status') != 'approved' or sha != data.get('assetSha256') or data.get('url') != '/media/' + sha + '.webp':
            raise ValueError('Invalid media integrity or path')
        if len(raw) > 2 * 1024 * 1024 or total > 10 * 1024 * 1024 or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
            raise ValueError('Media exceeds limits or is not WebP')
        with Image.open(io.BytesIO(raw)) as picture:
            if picture.format != 'WEBP' or max(picture.size) > 1600:
                raise ValueError('Invalid normalized image')
            picture.verify()
        folder = public_dir / 'media'
        folder.mkdir(exist_ok=True)
        (folder / (sha + '.webp')).write_bytes(raw)
        # A broadly compatible share derivative; the site retains compact WebP.
        with Image.open(io.BytesIO(raw)) as picture:
            picture.convert('RGB').save(folder / (sha + '-social.jpg'), 'JPEG', quality=90, optimize=True)


def https(value):
    url = urlsplit(value)
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('Only public HTTPS URLs without credentials are permitted')
    if url.hostname in {'localhost', '127.0.0.1', '::1'} or url.hostname.endswith(('.local','.localhost')):
        raise ValueError('Local URL rejected')
    try:
        address = ipaddress.ip_address(url.hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError('Private URL rejected')
    return value


def transform(snapshot):
    if snapshot.get('schemaVersion') != 1 or not isinstance(snapshot.get('collections'), dict):
        raise ValueError('Unsupported snapshot')
    out = {'enabled': True, 'discoveries': [], 'events': [], 'affiliates': [],
           'offers': [], 'campaigns': [], 'pages': [], 'media': [], 'taxonomies': [],
           'missions': [], 'rewards': [], 'releaseId': snapshot.get('releaseId')}
    for collection, records in snapshot['collections'].items():
        if collection not in {'content', 'events', 'affiliates', 'offers', 'campaigns', 'pages', 'media', 'taxonomies', 'missions', 'rewards'}:
            raise ValueError('Non-public collection in snapshot')
        for row in records:
            if row.get('status') != 'approved':
                raise ValueError('Unapproved record in snapshot')
            d = row['data']
            if collection == 'content':
                if d['category'] not in CATEGORIES:
                    raise ValueError('Unknown category')
                date = d['publishedAt'][:10]
                datetime.strptime(date, '%Y-%m-%d')
                for field in ('titlePT', 'titleEN', 'summaryPT', 'summaryEN'):
                    if not isinstance(d.get(field), str) or not d[field].strip():
                        raise ValueError('Missing translated content')
                out['discoveries'].append({
                    'id': row['id'], 'category': d['category'],
                    **{key: d[key] for key in ('titlePT', 'titleEN', 'summaryPT', 'summaryEN')},
                    'sourceName': d.get('sourceName') or urlsplit(d['sourceUrl']).hostname,
                    'url': https(d['sourceUrl']), 'published': date,
                    'observed': snapshot['createdAt'][:10],
                    'fact': d.get('bodyPT') or d['summaryPT'],
                    'factEN': d.get('bodyEN') or d['summaryEN'],
                    'sources': public_sources(d.get('sources')),
                    **{key: d[key] for key in NEWSROOM if key in d},
                    **{key: d[key] for key in ('slugPT','slugEN','seoTitlePT','seoTitleEN','seoDescriptionPT','seoDescriptionEN','author','tags','coverMediaId','mediaIds','isDemo') if key in d},
                })
            elif collection == 'events':
                if d['platform'] not in {'twitch', 'youtube', 'kick'}:
                    raise ValueError('Unknown platform')
                if datetime.fromisoformat(d['startsAt'].replace('Z', '+00:00')).tzinfo is None:
                    raise ValueError('Event must have timezone')
                out['events'].append({'id': row['id'], **{k: d[k] for k in ('titlePT', 'titleEN', 'platform', 'startsAt')}, 'isDemo': d.get('isDemo', False), **({'url': https(d['url'])} if d.get('url') else {})})
            elif collection == 'affiliates':
                out['affiliates'].append({'titlePT': d['titlePT'], 'titleEN': d['titleEN'], 'url': https(d['url']), 'status': 'active', 'isDemo': d.get('isDemo', False)})
            elif collection in {'offers', 'campaigns', 'pages'}:
                fields = {'offers': ('titlePT','titleEN','summaryPT','summaryEN','url','priceMinor','currency','disclosurePT','disclosureEN'),
                          'campaigns': ('titlePT','titleEN','url','placement','startsAt','endsAt','disclosurePT','disclosureEN'),
                          'pages': ('titlePT','titleEN','slug','bodyPT','bodyEN')}[collection]
                public = {'id': row['id'], **{key: d[key] for key in fields if key in d}}
                public.update({key: d[key] for key in ('isDemo','coverMediaId','slugPT','slugEN','seoTitlePT','seoTitleEN','seoDescriptionPT','seoDescriptionEN','tags','author','mediaIds') if key in d})
                if 'url' in public:
                    https(public['url'])
                if collection == 'campaigns' and public.get('placement') != 'home':
                    raise ValueError('Only home campaign placement is supported in this release')
                out[collection].append(public)
            elif collection == 'media':
                public = {'id': row['id'], **{key: d[key] for key in ('titlePT','titleEN','url','mediaType','mimeType','altPT','altEN','credit','license','width','height','isDemo') if key in d}}
                if not public.get('url', '').startswith('/media/'):
                    https(public['url'])
                else:
                    if not re.fullmatch(r'/media/[a-f0-9]{64}\.webp', public['url']) or not d.get('assetBase64'):
                        raise ValueError('Invalid uploaded media URL')
                    raw = base64.b64decode(d['assetBase64'], validate=True)
                    sha = hashlib.sha256(raw).hexdigest()
                    if sha != d.get('assetSha256') or public['url'] != '/media/' + sha + '.webp':
                        raise ValueError('Media integrity mismatch')
                    public['previewUrl'] = '/media/' + sha + '-social.jpg'
                out['media'].append(public)
            elif collection == 'taxonomies':
                out['taxonomies'].append({'id': row['id'], **{key: d[key] for key in ('titlePT','titleEN','slug','kind','isDemo') if key in d}})
            elif collection in {'missions','rewards'}:
                if d.get('isDemo') is not True:
                    raise ValueError('Only demo reward definitions can be published')
                out[collection].append({'id': row['id'], 'isDemo': True, **{key: d[key] for key in ('titlePT','titleEN','summaryPT','summaryEN','points','pointsCost','costKP','descriptionPT','descriptionEN','coverMediaId','termsPT','termsEN','category','regions','verifier','limit') if key in d}})
    media_ids = {row['id'] for row in out['media']}
    tag_ids = {row['id'] for row in out['taxonomies']}
    for name in ('discoveries','pages','offers','campaigns','missions','rewards'):
        for row in out[name]:
            if row.get('coverMediaId') and row['coverMediaId'] not in media_ids:
                raise ValueError('Missing approved cover media')
            if row.get('socialMediaId') and row['socialMediaId'] not in media_ids:
                raise ValueError('Missing approved social media')
            if any(value.strip() not in media_ids for value in row.get('mediaIds','').split(',') if value.strip()):
                raise ValueError('Missing approved gallery media')
            if any(value.strip() not in tag_ids for value in row.get('tags','').split(',') if value.strip()):
                raise ValueError('Missing approved tag')
    if not out['discoveries']:
        raise ValueError('Release would empty the radar; add approved content first')
    if len({x['id'] for x in out['discoveries']}) != len(out['discoveries']):
        raise ValueError('Duplicate content ID')
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    value = transform(json.loads(args.snapshot.read_text(encoding='utf-8-sig')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Validated {len(value['discoveries'])} discoveries for publication")
