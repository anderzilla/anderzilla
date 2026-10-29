"""CMS domain. Trusted principals enter only through an authenticated adapter."""
import copy
import json
import re
import uuid
import ipaddress
import base64
import hashlib
import io
from datetime import datetime, timezone
from urllib.parse import urlsplit

try:
    from . import commerce
except ImportError:
    import commerce

COMMON = {'titlePT', 'titleEN', 'summaryPT', 'summaryEN', 'isDemo'}
EDITORIAL = {'slugPT', 'slugEN', 'seoTitlePT', 'seoTitleEN', 'seoDescriptionPT', 'seoDescriptionEN', 'tags', 'author', 'coverMediaId', 'mediaIds'}
NEWSROOM = {'sources', 'verifiedAt', 'eventDate', 'editorialType', 'socialMediaId', 'instagramUrl', 'observedAt', 'editorialUpdatedAt'} | {name + lang for name in ('hashtags', 'socialInstagram', 'socialFacebook', 'socialWhatsapp') for lang in ('PT', 'EN')}
INSTAGRAM_POST = re.compile(r'^/(?:[A-Za-z0-9._]+/)?(?:p|reel|reels|tv)/[A-Za-z0-9_-]+/?$')
ASSET_FIELDS = {'assetBase64', 'assetSha256', 'mimeType'}
FIELDS = {
    'content': COMMON | EDITORIAL | NEWSROOM | {'bodyPT', 'bodyEN', 'category', 'sourceName', 'sourceUrl', 'publishedAt', 'imageUrl', 'slug'},
    'events': COMMON | {'platform', 'url', 'startsAt', 'endsAt', 'timezone'},
    'offers': COMMON | {'url', 'priceMinor', 'currency', 'disclosurePT', 'disclosureEN'},
    'affiliates': COMMON | {'url', 'disclosurePT', 'disclosureEN', 'approvalReference'},
    'campaigns': COMMON | {'url', 'imageUrl', 'placement', 'startsAt', 'endsAt', 'disclosurePT', 'disclosureEN', 'approvalReference'},
    'pages': COMMON | EDITORIAL | {'slug', 'bodyPT', 'bodyEN'},
    'media': COMMON | ASSET_FIELDS | {'url', 'altPT', 'altEN', 'credit', 'license', 'sourceUrl', 'mediaType', 'width', 'height'},
    'taxonomies': COMMON | {'slug', 'kind'},
    'missions': COMMON | {'points', 'verifier', 'limit', 'termsPT', 'termsEN'},
    'rewards': COMMON | {'points', 'category', 'regions', 'termsPT', 'termsEN'},
}
REQUIRED = {
    'content': {'titlePT', 'titleEN', 'summaryPT', 'summaryEN', 'bodyPT', 'bodyEN', 'category', 'sourceName', 'sourceUrl', 'publishedAt'},
    'events': {'titlePT', 'platform', 'url', 'startsAt', 'timezone'},
    'offers': {'titlePT', 'url', 'disclosurePT'},
    'affiliates': {'titlePT', 'url', 'disclosurePT', 'approvalReference'},
    'campaigns': {'titlePT', 'url', 'placement', 'startsAt', 'endsAt', 'disclosurePT', 'approvalReference'},
    'pages': {'titlePT', 'slug', 'bodyPT'},
    'media': {'url', 'altPT', 'credit', 'license'},
    'taxonomies': {'titlePT', 'titleEN', 'slug', 'kind'},
    'missions': {'titlePT', 'points', 'verifier', 'limit', 'termsPT'},
    'rewards': {'titlePT', 'points', 'category', 'regions', 'termsPT'},
}
FIELDS['banners'] = COMMON | {'imageMediaId', 'textPT', 'textEN', 'ctaPT', 'ctaEN', 'linkPT', 'linkEN', 'startsAt', 'endsAt', 'order', 'disclosure'}
REQUIRED['banners'] = {'titlePT', 'titleEN', 'imageMediaId', 'linkPT', 'linkEN', 'startsAt'}
for legacy in ('offers', 'affiliates', 'campaigns'):
    FIELDS[legacy] |= {'market', 'currency', 'store', 'status'}
FIELDS.update(commerce.FIELDS)
REQUIRED.update({name: {'titlePT', 'titleEN', 'market', 'status'} for name in commerce.FIELDS})
PUBLIC_COLLECTIONS = set(FIELDS) - {'missions', 'rewards'}
ROLES = {'anderzilla_admin', 'anderzilla_editor', 'anderzilla_commercial', 'anderzilla_rewards'}
# Biblioteca de imagens: 60 notícias com fotos/galerias — 2 MiB por imagem, 1600 px, total 32 MiB.
# O CMS persiste base64 (4/3 do binário); publisher valida bytes decodificados. Ambos os tetos derivam do mesmo limite lógico.
MEDIA_PER_IMAGE_BYTES = 2 * 1024 * 1024
MEDIA_PER_IMAGE_B64_LIMIT = 2800000  # ~2 MiB raw como base64 (≈2_796_203) + folga para padding
MEDIA_LIBRARY_LIMIT_BYTES = 32 * 1024 * 1024
MEDIA_LIBRARY_LIMIT_B64 = 44739244  # 32 MiB raw como base64 (4*ceil(32 MiB/3)) — quota consistente com publisher


class Error(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


def now():
    return datetime.now(timezone.utc).isoformat()


def require(principal, collection=None, publish=False):
    roles = set((principal or {}).get('roles', []))
    if not principal or not principal.get('id'):
        raise Error(401, 'authentication_required', 'Entre com uma conta autorizada.')
    if 'anderzilla_admin' in roles:
        return
    if publish or not roles.intersection(ROLES):
        raise Error(403, 'forbidden', 'Esta conta não tem permissão para esta operação.')
    required = 'anderzilla_commercial' if collection in ({'offers', 'affiliates', 'campaigns'} | set(commerce.FIELDS)) else 'anderzilla_rewards' if collection in {'missions', 'rewards'} else 'anderzilla_editor'
    if collection and required not in roles:
        raise Error(403, 'forbidden', 'Módulo não autorizado para esta conta.')


def validate(collection, data, approved=False, internal=False):
    if collection not in FIELDS:
        raise Error(404, 'not_found', 'Coleção inexistente.')
    if not isinstance(data, dict) or set(data) - FIELDS[collection]:
        raise Error(422, 'invalid_fields', 'Campos desconhecidos ou dados inválidos.')
    if set(data) & ASSET_FIELDS and not internal:
        raise Error(422, 'protected_asset', 'Use o endpoint de upload para arquivos.')
    for key, value in data.items():
        if key == 'assetBase64':
            if not isinstance(value, str) or len(value) > MEDIA_PER_IMAGE_B64_LIMIT:
                raise Error(413, 'asset_too_large', 'Arquivo normalizado muito grande.')
            continue
        if key in {'isDemo', 'enabled'}:
            if type(value) is not bool:
                raise Error(422, 'invalid_boolean', 'isDemo deve ser booleano.')
        elif key in {'points', 'limit', 'priceMinor', 'width', 'height', 'order'}:
            if type(value) is not int or not 0 <= value <= 100000000:
                raise Error(422, 'invalid_number', key + ': inteiro não negativo obrigatório.')
        elif not isinstance(value, str) or len(value) > (50000 if key.startswith('body') else 15000 if key == 'sources' else 3000):
            raise Error(422, 'invalid_text', key + ': texto inválido ou muito longo.')
        if isinstance(value, str) and value:
            if key.lower().endswith('url') or key == 'url':
                if collection == 'media' and key == 'url' and internal and data.get('assetBase64') and value == '/media/' + data.get('assetSha256', '') + '.webp' and re.fullmatch('[a-f0-9]{64}', data.get('assetSha256', '')):
                    continue
                parts = urlsplit(value)
                if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
                    raise Error(422, 'invalid_url', key + ': use um endereço HTTPS público.')
                host = parts.hostname.lower()
                if host == 'localhost' or host.endswith(('.localhost', '.local')):
                    raise Error(422, 'invalid_url', 'Endereço local não permitido.')
                try:
                    address = ipaddress.ip_address(host)
                except ValueError:
                    address = None
                if address and not address.is_global:
                    raise Error(422, 'invalid_url', 'Endereço privado não permitido.')
            if key in {'startsAt', 'endsAt', 'publishedAt', 'verifiedAt', 'eventDate', 'observedAt', 'editorialUpdatedAt'}:
                try:
                    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    if parsed.tzinfo is None and not (key in {'publishedAt', 'verifiedAt', 'eventDate', 'observedAt', 'editorialUpdatedAt'} and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)):
                        raise ValueError()
                except ValueError:
                    raise Error(422, 'invalid_date', key + ': data ISO com fuso obrigatório.')
            if key in {'slug', 'slugPT', 'slugEN'} and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
                raise Error(422, 'invalid_slug', 'Slug deve usar letras minúsculas, números e hífen.')
            if key.startswith('seoTitle') and len(value) > 100 or key.startswith('seoDescription') and len(value) > 300:
                raise Error(422, 'invalid_seo', 'Título SEO: máximo 100 caracteres; descrição: máximo 300.')
            if key == 'mediaType' and value not in {'image', 'video', 'audio', 'document'}:
                raise Error(422, 'invalid_media_type', 'Tipo de mídia inválido.')
            if key == 'kind' and value not in {'category', 'tag'}:
                raise Error(422, 'invalid_taxonomy', 'Tipo de taxonomia inválido.')
            if key == 'platform' and value not in {'twitch', 'youtube', 'kick'}:
                raise Error(422, 'invalid_platform', 'Plataforma não suportada.')
    if data.get('startsAt') and data.get('endsAt') and datetime.fromisoformat(data['endsAt'].replace('Z', '+00:00')) <= datetime.fromisoformat(data['startsAt'].replace('Z', '+00:00')):
        raise Error(422, 'invalid_period', 'Fim deve ser posterior ao início.')
    if collection == 'content' and data.get('category') and data['category'] not in {'games', 'consoles', 'celulares', 'ia', 'gadgets', 'curiosidades'}:
        raise Error(422, 'invalid_category', 'Categoria editorial não permitida.')
    if collection == 'content':
        if data.get('editorialType') and data['editorialType'] not in {'news', 'analysis', 'comparison', 'explainer', 'rumor'}:
            raise Error(422, 'invalid_editorial_type', 'Tipo editorial inválido.')
        if data.get('sources'):
            try:
                sources = json.loads(data['sources'])
                if not isinstance(sources, list) or not 1 <= len(sources) <= 20:
                    raise ValueError()
                for source in sources:
                    if not isinstance(source, dict) or set(source) - {'name', 'url', 'publishedAt', 'note'}:
                        raise ValueError()
                    if not isinstance(source.get('name'), str) or not source['name'].strip() or not source.get('url'):
                        raise ValueError()
                    validate('content', {'sourceUrl': source['url'], 'sourceName': source['name'], **({'publishedAt': source['publishedAt']} if 'publishedAt' in source else {})})
                    if 'note' in source and (not isinstance(source['note'], str) or len(source['note']) > 1500):
                        raise ValueError()
            except (ValueError, TypeError):
                raise Error(422, 'invalid_sources', 'Fontes: use uma lista JSON com 1–20 objetos name, url e data/nota opcionais.')
        for key in ('hashtagsPT', 'hashtagsEN'):
            if data.get(key) and (len(data[key].split()) > 15 or any(not re.fullmatch(r'#[\w]+', tag) for tag in data[key].split())):
                raise Error(422, 'invalid_hashtags', 'Use até 15 hashtags separadas por espaço, sem pontuação.')
        for key in ('socialInstagramPT', 'socialInstagramEN'):
            if len(data.get(key, '')) > 2200:
                raise Error(422, 'invalid_social', 'Legenda Instagram: máximo 2200 caracteres.')
        if data.get('instagramUrl'):
            parts = urlsplit(data['instagramUrl'])
            host = (parts.hostname or '').lower()
            if host not in {'instagram.com', 'www.instagram.com'} or not INSTAGRAM_POST.fullmatch(parts.path or ''):
                raise Error(422, 'invalid_instagram_url', 'instagramUrl: use um post ou reel HTTPS em instagram.com.')
    if collection == 'campaigns' and data.get('placement') and data['placement'] != 'home':
        raise Error(422, 'invalid_placement', 'Espaço disponível nesta entrega: home.')
    if collection == 'banners':
        for key in ('linkPT', 'linkEN'):
            link = data.get(key)
            if link and not (link.startswith('/') and not link.startswith('//')):
                validate('offers', {'url': link})  # same HTTPS/public-host rules as any external URL
    if collection in {'offers', 'affiliates', 'campaigns'}:
        for key, values in [('market', {'br','intl','global'}), ('currency', {'BRL','USD'}), ('status', {'candidate','active','paused','ended'})]:
            if key in data and data[key] not in values:
                raise Error(422, 'invalid_commerce', key + ': valor inválido.')
    if collection in commerce.FIELDS:
        try:
            commerce.check(collection, data, approved)
        except ValueError as exc:
            raise Error(422, 'invalid_commerce', str(exc))
    if approved:
        missing = [key for key in REQUIRED[collection] if data.get(key) in (None, '', 0)]
        if collection == 'pages' and data.get('slugPT') and 'slug' in missing:
            missing.remove('slug')
        if collection == 'media' and data.get('mediaType'):
            missing += [key for key in ('altEN',) if not data.get(key)]
            if data['mediaType'] == 'image':
                missing += [key for key in ('width', 'height') if not data.get(key)]
        if missing:
            raise Error(422, 'incomplete_record', 'Preencha: ' + ', '.join(sorted(missing)))
    return copy.deepcopy(data)


def validate_references(db, collection, data, record_id=None):
    """Check references again at release time, since a dependency may be archived."""
    if collection in {'feature_flags', 'market_hubs', 'trust_blocks', 'products'}:
        identity = 'key' if collection == 'feature_flags' else 'slug'
        for other in db.records(collection):
            if other['id'] != record_id and other['status'] == 'approved' and other['data'].get('market') == data.get('market') and other['data'].get(identity) == data.get(identity):
                raise Error(422, 'duplicate_commerce', 'Já existe uma revisão aprovada com esta chave neste mercado.')
    if collection in {'content', 'pages'}:
        if data.get('socialMediaId'):
            media = db.record('media', data['socialMediaId'])
            if not media or media['status'] != 'approved' or media['data'].get('mediaType', 'image') != 'image':
                raise Error(422, 'invalid_social_image', 'Selecione uma imagem social aprovada na biblioteca.')
        if data.get('coverMediaId'):
            media = db.record('media', data['coverMediaId'])
            if not media or media['status'] != 'approved' or media['data'].get('mediaType', 'image') != 'image':
                raise Error(422, 'invalid_cover', 'Selecione uma imagem aprovada na biblioteca.')
        for media_id in filter(None, (value.strip() for value in data.get('mediaIds', '').split(','))):
            media = db.record('media', media_id)
            if not media or media['status'] != 'approved':
                raise Error(422, 'invalid_media', 'A galeria deve referenciar mídias aprovadas.')
        for tag in filter(None, (value.strip() for value in data.get('tags', '').split(','))):
            taxonomy = db.record('taxonomies', tag)
            if not taxonomy or taxonomy['status'] != 'approved' or taxonomy['data'].get('kind') != 'tag':
                raise Error(422, 'invalid_tag', 'Tags devem referenciar IDs de taxonomias aprovadas.')
    if collection == 'banners' and data.get('imageMediaId'):
        media = db.record('media', data['imageMediaId'])
        if not media or media['status'] != 'approved' or media['data'].get('mediaType', 'image') != 'image':
            raise Error(422, 'invalid_banner_image', 'Selecione uma imagem aprovada na biblioteca.')
    if collection in {'content', 'pages', 'taxonomies'}:
        for other in db.records(collection):
            if other['id'] == record_id or other['status'] != 'approved':
                continue
            for key in ('slugPT', 'slugEN'):
                slug = data.get(key) or data.get('slug')
                other_slug = other['data'].get(key) or other['data'].get('slug')
                if slug and slug == other_slug:
                    raise Error(422, 'duplicate_slug', 'Slug já usado por outro registro aprovado neste idioma.')


def hydrate_assets(db, snapshot):
    """Fill assetBase64 of every uploaded image of a by-reference snapshot, verifying each against its recorded SHA-256."""
    pending = [row for row in snapshot['collections'].get('media', []) if row['data'].get('assetSha256') and not row['data'].get('assetBase64')]
    assets = db.media_assets([row['id'] for row in pending])
    for row in pending:
        encoded = assets.get(row['id'])
        if not encoded or hashlib.sha256(base64.b64decode(encoded, validate=True)).hexdigest() != row['data']['assetSha256']:
            raise ValueError('Image bytes missing or different from the approved asset: ' + row['id'])
        row['data']['assetBase64'] = encoded
    return snapshot


class CMS:
    def __init__(self, store):
        self.store = store

    def list(self, principal, collection):
        require(principal, collection)
        validate(collection, {})
        with self.store.transaction() as db:
            return {'items': db.records(collection)}

    def upload_media(self, principal, body):
        require(principal, 'media')
        if not isinstance(body, dict) or set(body) - {'filename', 'contentBase64', 'altPT', 'altEN', 'credit', 'license'}:
            raise Error(422, 'invalid_upload', 'Campos de upload inválidos.')
        encoded = body.get('contentBase64', '')
        if not isinstance(encoded, str) or len(encoded) > MEDIA_PER_IMAGE_B64_LIMIT:
            raise Error(413, 'asset_too_large', 'Use uma imagem de até 2 MB.')
        from PIL import Image, ImageOps
        try:
            raw = base64.b64decode(encoded, validate=True)
            if not raw or len(raw) > MEDIA_PER_IMAGE_BYTES:
                raise ValueError()
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw)) as original:
                    if original.format not in {'JPEG', 'PNG', 'WEBP'} or original.width * original.height > 20000000:
                        raise ValueError()
                    original.load()
                    normalized = ImageOps.exif_transpose(original).convert('RGBA' if 'A' in original.getbands() else 'RGB')
                    normalized.thumbnail((1600, 1600))
                    output = io.BytesIO()
                    normalized.save(output, format='WEBP', quality=85, method=4, exif=b'')
                    asset = output.getvalue()
                    width, height = normalized.size
            if len(asset) > MEDIA_PER_IMAGE_BYTES:
                raise ValueError()
        except (ValueError, OSError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError):
            raise Error(422, 'invalid_image', 'Imagem inválida. Use JPEG, PNG ou WebP até 2 MB e 20 megapixels.')
        sha = hashlib.sha256(asset).hexdigest()
        data = {key: body.get(key, '') for key in ('altPT', 'altEN', 'credit', 'license')}
        data.update(titlePT=body.get('filename', 'Imagem'), mediaType='image', width=width, height=height,
                    url='/media/' + sha + '.webp', assetBase64=base64.b64encode(asset).decode(), assetSha256=sha, mimeType='image/webp')
        validate('media', data, approved=True, internal=True)
        with self.store.transaction() as db:
            if db.media_bytes() + len(data['assetBase64']) > MEDIA_LIBRARY_LIMIT_B64:
                raise Error(413, 'media_quota', 'Biblioteca atingiu o limite de 32 MB. Revise os arquivos antes de continuar.')
            record = {'id': str(uuid.uuid4()), 'version': 1, 'status': 'draft', 'data': data, 'updatedAt': now()}
            db.save_record('media', record)
            db.audit(principal['id'], 'upload_normalized_image', 'media', record['id'], 1)
            return record

    def save(self, principal, collection, data, record_id=None, version=None, action=None):
        require(principal, collection)
        validate(collection, {})
        with self.store.transaction() as db:
            previous = db.record(collection, record_id) if record_id else None
            if record_id and not previous:
                raise Error(404, 'not_found', 'Registro não encontrado.')
            if previous and (type(version) is not int or previous['version'] != version):
                raise Error(409, 'version_conflict', 'Outra pessoa alterou este registro. Recarregue antes de salvar.')
            if action and action not in {'approve', 'archive'}:
                raise Error(422, 'invalid_action', 'Transição inválida.')
            if action and not previous:
                raise Error(422, 'invalid_action', 'Crie o rascunho primeiro.')
            status = {'approve': 'approved', 'archive': 'archived'}.get(action, 'draft')
            payload = previous['data'] if action else copy.deepcopy(data)
            if action == 'approve' and collection == 'content' and not payload.get('observedAt'):
                payload = {**payload, 'observedAt': now()[:10]}  # first approval date; never re-derived from later releases
            if collection == 'media' and isinstance(payload, dict):
                for key in ASSET_FIELDS:
                    if key in payload and (not previous or payload[key] != previous['data'].get(key)):
                        raise Error(422, 'protected_asset', 'Arquivo normalizado é imutável; faça outro upload.')
                    if previous and key in previous['data']:
                        payload[key] = previous['data'][key]
                if previous and previous['data'].get('assetBase64') and payload.get('url') != previous['data']['url']:
                    raise Error(422, 'protected_asset', 'URL do upload é imutável.')
            clean = validate(collection, payload, status == 'approved', internal=True)
            if status == 'approved':
                validate_references(db, collection, clean, record_id)
            record = {'id': record_id or str(uuid.uuid4()), 'version': (previous['version'] if previous else 0) + 1, 'status': status, 'data': clean, 'updatedAt': now()}
            db.save_record(collection, record)
            db.audit(principal['id'], action or ('update' if previous else 'create'), collection, record['id'], record['version'])
            return record

    def revisions(self, principal, collection, record_id):
        require(principal, collection)
        validate(collection, {})
        with self.store.transaction() as db:
            return {'items': db.revisions(collection, record_id)}

    def summary(self, principal):
        require(principal)
        permitted = []
        for collection in FIELDS:
            try:
                require(principal, collection)
                permitted.append(collection)
            except Error:
                pass
        with self.store.transaction() as db:
            counts = {key: len(db.records(key)) for key in permitted}
            return {'counts': counts, 'recentAudit': [row for row in db.recent_audit() if row['collection'] in permitted or ('anderzilla_admin' in principal['roles'])], 'capabilities': {'collections': permitted, 'publish': 'anderzilla_admin' in principal['roles'], 'rewardsLive': False, 'analyticsConnected': False}}

    def snapshot(self, db, overlay=None, include_assets=True):
        """Frozen public view of approved records. overlay={(collection, id): record} previews drafts as approved.

        include_assets=False keeps image bytes out of the snapshot (media rows keep assetSha256 and url): the 242 library images
        are ~21 MiB, and writing that into every release took ~2 minutes on Azure SQL, past the 45 s limit of the review site.
        Assets are immutable and content-addressed, so the publisher loads them by id with hydrate_assets()."""
        # A release is read-only until its snapshot is written. Load each
        # collection once under the transaction lock, then validate the same
        # frozen view without per-reference SQL round trips. Never reuse this
        # cache across transactions or in save(), where records may change.
        records = {name: db.records(name, light=(name == 'media' and not include_assets)) for name in sorted(FIELDS)}
        for (collection, record_id), record in (overlay or {}).items():  # preview: drafts of one package count as approved
            records[collection] = [row for row in records[collection] if row['id'] != record_id] + [{**record, 'status': 'approved'}]
        indexes = {name: {row['id']: row for row in rows} for name, rows in records.items()}

        class ReleaseReferences:
            def records(self, collection):
                return records[collection]

            def record(self, collection, record_id):
                return indexes[collection].get(record_id)

        references = ReleaseReferences()
        collections = {}
        for collection in sorted(PUBLIC_COLLECTIONS):
            items = []
            for record in records[collection]:
                if record['status'] != 'approved':
                    continue
                validate(collection, record['data'], approved=True, internal=True)
                validate_references(references, collection, record['data'], record['id'])
                public = copy.deepcopy(record)
                if collection in commerce.FIELDS and record['data'].get('status') != 'active':
                    continue
                if collection in {'affiliate_placements', 'ad_placements'}:
                    public['data']['approvalVerified'] = bool(record['data'].get('approvalReference'))
                public['data'].pop('approvalReference', None)
                items.append(public)
            collections[collection] = items
        if include_assets:
            if sum(len(row['data'].get('assetBase64', '')) for row in collections.get('media', [])) > MEDIA_LIBRARY_LIMIT_B64:
                raise Error(413, 'media_quota', 'Snapshot excede limite de 32 MB de imagens.')
        else:  # the quota is enforced at upload; the light rows carry only a placeholder, which must not leak into the snapshot
            for row in collections.get('media', []):
                row['data'].pop('assetBase64', None)
        for collection in ('missions', 'rewards'):
            demos = [copy.deepcopy(row) for row in records[collection] if row['status'] == 'approved' and row['data'].get('isDemo') is True]
            for row in demos:
                validate(collection, row['data'], approved=True)
            if demos:
                collections[collection] = demos
        return {'schemaVersion': 1, 'createdAt': now(), 'assets': 'included' if include_assets else 'by-reference', 'collections': collections}

    def release(self, principal, key):
        require(principal, publish=True)
        if not isinstance(key, str) or not 8 <= len(key) <= 100:
            raise Error(422, 'invalid_idempotency', 'Informe uma chave de publicação válida.')
        with self.store.transaction() as db:
            existing = db.release_by_key(key)
            if existing:
                return existing
            snapshot = self.snapshot(db, include_assets=False)
            release = {'id': str(uuid.uuid4()), 'status': 'queued', 'createdAt': now(), 'updatedAt': now(), 'url': None}
            db.save_release(release, key, snapshot)
            db.audit(principal['id'], 'queue_release', 'releases', release['id'], 1)
            return release

    def releases(self, principal, release_id=None, snapshot=False):
        require(principal, publish=True)
        with self.store.transaction() as db:
            if release_id:
                result = db.release(release_id, snapshot)
                if result is None:
                    raise Error(404, 'not_found', 'Publicação não encontrada.')
                return result
            return {'items': db.releases()}

    def update_release(self, principal, release_id, status, url=None):
        require(principal, publish=True)
        if status not in {'building', 'validated', 'deploying', 'deployed', 'failed'}:
            raise Error(422, 'invalid_status', 'Estado de publicação inválido.')
        with self.store.transaction() as db:
            release = db.release(release_id)
            if not release:
                raise Error(404, 'not_found', 'Publicação não encontrada.')
            allowed = {'queued': {'building', 'failed'}, 'building': {'validated', 'failed'}, 'validated': {'deploying', 'failed'}, 'deploying': {'deployed', 'failed'}}
            if status not in allowed.get(release['status'], set()):
                raise Error(409, 'invalid_transition', 'Transição de publicação inválida.')
            if url:
                validate('offers', {'url': url})
            release.update(status=status, updatedAt=now(), url=url)
            db.update_release(release)
            db.audit(principal['id'], status, 'releases', release_id, 1)
            return release
