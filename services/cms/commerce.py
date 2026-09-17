"""Public commerce contract; approval evidence stays inside the CMS."""
from datetime import datetime

COMMON = {'titlePT', 'titleEN', 'summaryPT', 'summaryEN', 'market', 'currency', 'status', 'ctaUrl', 'disclosureKey', 'disclosurePT', 'disclosureEN'}
FIELDS = {
    'products': COMMON | {'slug', 'bodyPT', 'bodyEN', 'priceMinor', 'store', 'demoUrl'},
    'affiliate_placements': COMMON | {'store', 'approvalReference', 'startsAt', 'endsAt'},
    'ad_placements': COMMON | {'store', 'approvalReference', 'placement', 'imageUrl', 'startsAt', 'endsAt'},
    'sponsor_packages': COMMON | {'slug', 'bodyPT', 'bodyEN', 'store', 'priceMinor'},
    'trust_blocks': COMMON | {'slug', 'bodyPT', 'bodyEN'},
    'feature_flags': COMMON | {'key', 'enabled'},
    'market_hubs': COMMON | {'slug', 'bodyPT', 'bodyEN'},
}
FLAGS = {'showProducts', 'showAffiliatesBr', 'showAffiliatesIntl', 'showAds', 'showSponsor', 'showPointsStore', 'showMarketBr', 'showMarketIntl'}


def check(collection, data, approved=False):
    for key in FIELDS[collection] & set(data):
        value = data[key]
        if key == 'enabled':
            if type(value) is not bool:
                raise ValueError('enabled deve ser booleano.')
        elif key == 'priceMinor':
            if type(value) is not int or not 0 <= value <= 100000000:
                raise ValueError('Preço em centavos deve ser inteiro não negativo.')
        elif not isinstance(value, str):
            raise ValueError(key + ': texto obrigatório.')
    for key, allowed in [('market', {'br', 'intl', 'global'}), ('currency', {'BRL', 'USD'}), ('status', {'candidate', 'active', 'paused', 'ended'})]:
        if key in data and data[key] not in allowed:
            raise ValueError(key + ': valor inválido.')
    if collection == 'feature_flags':
        if 'key' in data and data['key'] not in FLAGS:
            raise ValueError('Flag não permitida.')
        if 'enabled' in data and type(data['enabled']) is not bool:
            raise ValueError('enabled deve ser booleano.')
    dates = {}
    for key in ('startsAt', 'endsAt'):
        if data.get(key):
            try:
                dates[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
                if dates[key].tzinfo is None:
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                raise ValueError(key + ': data ISO com fuso obrigatório.')
    if len(dates) == 2 and dates['endsAt'] <= dates['startsAt']:
        raise ValueError('Fim deve ser posterior ao início.')
    if approved:
        required = {'titlePT', 'titleEN', 'market', 'status'}
        if collection == 'feature_flags':
            required |= {'key'}
            if type(data.get('enabled')) is not bool:
                raise ValueError('Informe enabled como booleano.')
        elif collection in {'trust_blocks', 'market_hubs'}:
            required |= {'slug', 'bodyPT', 'bodyEN'}
        elif data.get('status') == 'active':
            required |= {'currency', 'ctaUrl', 'store', 'disclosureKey', 'disclosurePT', 'disclosureEN'}
            if collection in {'affiliate_placements', 'ad_placements'}:
                required |= {'approvalReference'}
            if collection == 'ad_placements':
                required |= {'startsAt', 'endsAt', 'placement'}
            if collection == 'products':
                required |= {'slug', 'bodyPT', 'bodyEN'}
        missing = sorted(key for key in required if not str(data.get(key, '')).strip())
        if missing:
            raise ValueError('Preencha: ' + ', '.join(missing))
