"""Verify the final reviewed asset set before its audited CMS import."""
import hashlib,json
from collections import Counter
from pathlib import Path
from PIL import Image
DEST=Path(__file__).resolve().parent/'real-media-2026-09-16'
raw=(DEST/'reviewed-media.json').read_bytes()
review=json.loads(raw)
assert review['approvedForImport'] is True and len(review['items'])==60
counts=Counter();titles=set()
for row in review['items']:
    if row['status']!='ready':
        counts['fallbacks']+=1
        assert not row['images']
        continue
    counts['articles']+=1;counts['galleries']+=len(row['images'])>1
    hashes=set()
    for media in row['images']:
        path=Path(media['localPath']);asset=path.read_bytes()
        digest=hashlib.sha256(asset).hexdigest()
        assert digest not in hashes,row['key']
        assert media['cmsTitle'] not in titles
        hashes.add(digest);titles.add(media['cmsTitle'])
        assert media['sourcePage'].startswith('https://')
        assert all(media[field] for field in ('altPT','altEN','credit','licenseLabel'))
        assert len(asset)<2*1024*1024
        with Image.open(path) as image:
            assert image.format=='WEBP' and max(image.size)<=1600
            assert image.size==(media['width'],media['height'])
        counts['images']+=1;counts['bytes']+=len(asset)
result={**counts,'manifestSha256':hashlib.sha256(raw).hexdigest()}
(DEST/'asset-preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
