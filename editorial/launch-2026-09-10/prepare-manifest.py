"""Prepare reviewed editorial assets for the CMS importer; no database writes."""
import base64
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, 'Z:/AnderZilla/services/cms')
from core import validate

items = []
for name in ('games-consoles-gadgets.json', 'ia-celulares-curiosidades.json'):
    items.extend(json.loads((ROOT / name).read_text(encoding='utf-8-sig')))
counts = collections.Counter(item['data']['category'] for item in items)
assert len(counts) == 6 and all(count >= 10 for count in counts.values()), counts
assert len({item['key'] for item in items}) == len(items)
output = []
for item in items:
    data = dict(item['data'])
    for lang, route in (('PT', 'pt'), ('EN', 'en')):
        url = f"https://anderzilla.com/{route}/radar/{data['slug' + lang]}/"
        for channel in ('Instagram', 'Facebook', 'Whatsapp'):
            field = 'social' + channel + lang
            data[field] = data[field].replace('{url}', url).replace('{url' + lang + '}', url)
            assert '{url' not in data[field]
        assert data['hashtags' + lang].startswith('#')
        assert 90 <= len(data['summary' + lang]) <= 230
        assert len(data['body' + lang].split()) >= 150
    validate('content', data, approved=True)
    entry = {'key': item['key'], 'data': data}
    for field, suffix, shape in (('cover', 'cover', 'horizontal'), ('socialImage', 'instagram', 'vertical')):
        filename = item['key'] + '-' + suffix + '.webp'
        raw = (ROOT / 'cards' / filename).read_bytes()
        entry[field] = {
            'filename': 'launch-2026-09-' + filename,
            'contentBase64': base64.b64encode(raw).decode(),
            'altPT': f"Arte editorial {shape} AnderZilla: {data['titlePT']}. Ilustração conceitual, não fotografia do produto.",
            'altEN': f"AnderZilla {shape} editorial artwork: {data['titleEN']}. Conceptual illustration, not a product photograph.",
            'credit': 'AnderZilla · arte vetorial original / original vector artwork',
            'license': 'Arte editorial própria AnderZilla; autorizada para uso no site e seus canais sociais.',
        }
    output.append(entry)
(ROOT / 'launch-manifest.json').write_text(json.dumps({'items': output}, ensure_ascii=False), encoding='utf-8')
report = {'articles': len(items), 'languages': ['pt-BR', 'en'], 'categories': dict(counts), 'formats': dict(collections.Counter(x['data']['editorialType'] for x in items)), 'images': len(items)*2, 'socialTexts': len(items)*6, 'sourceLinks': sum(len(json.loads(x['data']['sources'])) for x in items), 'preparedAt': '2026-09-10', 'status': 'prepared_for_cms_import'}
(ROOT / 'quality-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True))
