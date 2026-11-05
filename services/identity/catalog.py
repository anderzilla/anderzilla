"""Editorial catalog boundary and content visibility/entitlement checks.

Filters Radar, Backpack, Exploration and Dashboard items in the API BEFORE returning
titles, summaries, images, slugs or category counts. Private/removed/unentitled items
never leak restricted metadata.
"""
import json
from pathlib import Path
import re

VALID_CATEGORIES = frozenset({'games', 'consoles', 'celulares', 'ia', 'gadgets', 'curiosidades'})
VALID_VISIBILITIES = frozenset({'public', 'member', 'entitled'})
VALID_PUBLICATION_STATUSES = frozenset({'published', 'draft', 'archived', 'removed'})
VALID_ENTITLEMENTS = frozenset({'site_plan', 'purchase', 'live_channel'})


def _calendar_day(value):
    if not isinstance(value, str):
        return ''
    day = value[:10]
    return day if re.fullmatch(r'\d{4}-\d{2}-\d{2}', day) else ''


def recency_day(item):
    published = _calendar_day(item.get('published'))
    editorial = sorted(d for d in (_calendar_day(item.get('updatedAt')), _calendar_day(item.get('verifiedAt'))) if d)
    if editorial:
        return editorial[-1]
    return published or '0000-00-00'


def sort_key_newest_first(item):
    # Returns tuple for descending sort by recency day, published day, then ascending ID tie-break.
    return (recency_day(item), _calendar_day(item.get('published')), item.get('id', ''))


def sort_discoveries(items):
    # Sort newest first; tie-break deterministically by ID ascending per MEMBER-AREA.md §5.
    return sorted(
        items,
        key=lambda x: (
            _invert_date(recency_day(x)),
            _invert_date(_calendar_day(x.get('published')) or '0000-00-00'),
            str(x.get('id', '')),
        ),
    )


def _invert_date(day_str):
    # Format YYYY-MM-DD -> tuple of negative ints for descending order alongside ascending id.
    try:
        parts = [int(p) for p in day_str.split('-')]
        if len(parts) == 3:
            return (-parts[0], -parts[1], -parts[2])
    except (ValueError, TypeError):
        pass
    return (0, 0, 0)


def _load_default_items():
    repo_root = Path(__file__).resolve().parents[2]
    cms_path = repo_root / 'apps' / 'web' / 'src' / 'components' / 'hub' / 'cms-published.json'
    disc_path = repo_root / 'apps' / 'web' / 'src' / 'components' / 'hub' / 'discoveries.json'
    manifest_path = Path(__file__).with_name('catalog_manifest.json')
    by_id = {}
    media_by_id = {}
    if cms_path.exists():
        try:
            raw = json.loads(cms_path.read_text(encoding='utf-8'))
            for m in raw.get('media', []):
                if isinstance(m, dict) and isinstance(m.get('id'), str):
                    media_by_id[m['id']] = m
            for item in raw.get('discoveries', []):
                if isinstance(item, dict) and isinstance(item.get('id'), str):
                    by_id[item['id']] = _normalize_item(item, media_by_id)
        except Exception:
            pass
    if disc_path.exists():
        try:
            for item in json.loads(disc_path.read_text(encoding='utf-8')):
                if isinstance(item, dict) and isinstance(item.get('id'), str) and item['id'] not in by_id:
                    by_id[item['id']] = _normalize_item(item, media_by_id)
        except Exception:
            pass
    if not by_id and manifest_path.exists():
        try:
            for item in json.loads(manifest_path.read_text(encoding='utf-8')):
                if isinstance(item, dict) and isinstance(item.get('id'), str):
                    by_id[item['id']] = _normalize_item(item, {})
        except Exception:
            pass
    return by_id


def _normalize_item(item, media_by_id):
    cover_id = item.get('coverMediaId')
    media = media_by_id.get(cover_id, {}) if cover_id else {}
    is_demo = bool(item.get('isDemo', False))
    pub_status = item.get('publicationStatus')
    if pub_status not in VALID_PUBLICATION_STATUSES:
        pub_status = 'draft' if is_demo else 'published'
    visibility = item.get('visibility')
    if visibility not in VALID_VISIBILITIES:
        visibility = 'public'
    return {
        'id': str(item['id']),
        'category': item.get('category') if item.get('category') in VALID_CATEGORIES else 'curiosidades',
        'titlePT': str(item.get('titlePT') or ''),
        'titleEN': str(item.get('titleEN') or ''),
        'summaryPT': str(item.get('summaryPT') or ''),
        'summaryEN': str(item.get('summaryEN') or ''),
        'sourceName': str(item.get('sourceName') or 'AnderZilla'),
        'url': str(item.get('url') or ''),
        'published': str(item.get('published') or ''),
        'updatedAt': str(item.get('updatedAt') or ''),
        'verifiedAt': str(item.get('verifiedAt') or ''),
        'slugPT': str(item.get('slugPT') or item['id']),
        'slugEN': str(item.get('slugEN') or item['id']),
        'editorialType': str(item.get('editorialType') or 'news'),
        'coverMediaId': str(cover_id or ''),
        'coverUrl': str(item.get('coverUrl') or media.get('previewUrl') or media.get('url') or ''),
        'isDemo': is_demo,
        'visibility': visibility,
        'publicationStatus': pub_status,
        'requiredEntitlement': item.get('requiredEntitlement'),
        'requiredEntitlementTarget': item.get('requiredEntitlementTarget'),
        'market': str(item.get('market') or 'global'),
        'commercialDisclosurePT': str(item.get('commercialDisclosurePT') or ''),
        'commercialDisclosureEN': str(item.get('commercialDisclosureEN') or ''),
    }


_DEFAULT_CATALOG = None


def get_catalog(overrides=None):
    global _DEFAULT_CATALOG
    if _DEFAULT_CATALOG is None:
        _DEFAULT_CATALOG = _load_default_items()
    if not overrides:
        return _DEFAULT_CATALOG
    merged = dict(_DEFAULT_CATALOG)
    for k, v in overrides.items():
        if v is None:
            merged.pop(k, None)
        else:
            base = merged.get(k, {'id': k, 'category': 'games', 'titlePT': k, 'titleEN': k, 'summaryPT': '', 'summaryEN': '', 'published': '2026-09-10'})
            merged[k] = _normalize_item({**base, **v, 'id': k}, {})
    return merged


def can_access_discovery(item, is_active_member=False, active_entitlements=None, now=None):
    """Evaluate publication and access policy before returning any item metadata."""
    if not item or not isinstance(item, dict):
        return False
    if item.get('isDemo') or item.get('publicationStatus') != 'published':
        return False
    visibility = item.get('visibility', 'public')
    if visibility == 'public':
        return True
    if not is_active_member:
        return False
    if visibility == 'member':
        return True
    if visibility == 'entitled':
        req_kind = item.get('requiredEntitlement')
        req_target = item.get('requiredEntitlementTarget') or item.get('id')
        if not req_kind or req_kind not in VALID_ENTITLEMENTS:
            return False
        for ent in (active_entitlements or ()):
            if ent.get('kind') == req_kind and ent.get('state') == 'active':
                if ent.get('target_id') in ('*', req_target):
                    if (ent.get('starts_at') is None or ent['starts_at'] <= (now or 0)) and (ent.get('ends_at') is None or ent['ends_at'] > (now or 0)):
                        return True
        return False
    return False


def project_discovery(item):
    """Return safe public/authorized metadata for an accessible discovery."""
    return {
        'id': item['id'],
        'category': item['category'],
        'titlePT': item['titlePT'],
        'titleEN': item['titleEN'],
        'summaryPT': item['summaryPT'],
        'summaryEN': item['summaryEN'],
        'sourceName': item['sourceName'],
        'url': item['url'],
        'published': item['published'],
        'updatedAt': item['updatedAt'],
        'verifiedAt': item['verifiedAt'],
        'recencyDay': recency_day(item),
        'slugPT': item['slugPT'],
        'slugEN': item['slugEN'],
        'editorialType': item['editorialType'],
        'coverMediaId': item['coverMediaId'],
        'coverUrl': item['coverUrl'],
        'visibility': item['visibility'],
        'market': item.get('market', 'global'),
        'commercialDisclosurePT': item.get('commercialDisclosurePT', ''),
        'commercialDisclosureEN': item.get('commercialDisclosureEN', ''),
    }
