"""Prepare official asset candidates for visual review, never auto-approve imports."""
import concurrent.futures, hashlib, io, json, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parent/'real-media-2026-09-16'

def prepare(pair):
    key,image,index=pair
    try:
        url=image['url']
        parsed=urlsplit(url)
        assert parsed.scheme=='https' and parsed.hostname and not parsed.username
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 AnderZillaEditorial/1.0'}),timeout=35) as response:
            raw=response.read(25*1024*1024+1)
        assert len(raw)<=25*1024*1024,'Original exceeds 25 MB'
        with Image.open(io.BytesIO(raw)) as source:
            assert source.format in ('JPEG','PNG','WEBP'),'Unsupported image format'
            assert source.width*source.height<=40_000_000,'Too many pixels'
            image_copy=ImageOps.exif_transpose(source).convert('RGB')
            assert image_copy.width>=500 and image_copy.height>=250,'Too small for editorial cover'
            image_copy.thumbnail((1600,1600))
            buffer=io.BytesIO()
            image_copy.save(buffer,'WEBP',quality=85,method=4)
            normalized=buffer.getvalue()
            assert len(normalized)<=2*1024*1024,'Normalized image too large'
            digest=hashlib.sha256(normalized).hexdigest()
            target=ROOT/'assets'/(digest+'.webp')
            target.write_bytes(normalized)
            return key,{**image,'localPath':str(target),'width':image_copy.width,'height':image_copy.height,'bytes':len(normalized),'cmsTitle':f'{key} — fonte oficial {index+1}','licenseLabel':'Divulgação. Direitos reservados ao titular.'},None
    except Exception as error:
        return key,None,{'url':image.get('url'),'error':str(error)}

if __name__=='__main__':
    research=json.loads((ROOT/'selected-media.json').read_text(encoding='utf-8'))
    extras={row['key']:row for row in json.loads((ROOT/'reviewed-extras.json').read_text(encoding='utf-8'))['items']}
    research['items']=[extras.get(row['key'],row) for row in research['items']]
    (ROOT/'assets').mkdir(exist_ok=True)
    rows={row['key']:{**row,'images':[],'downloadErrors':[]} for row in research['items']}
    work=[(row['key'],image,index) for row in research['items'] if row['status']=='ready' for index,image in enumerate(row['images'])]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for key,image,error in pool.map(prepare,work):
            rows[key]['images' if image else 'downloadErrors'].append(image or error)
    for row in rows.values():
        if row['status']=='ready' and not row['images']:
            row.update(status='fallback',reason='Asset download or image validation failed; see downloadErrors.')
    result={'approvedForImport':False,'items':list(rows.values())}
    (ROOT/'candidate-media.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ready':sum(row['status']=='ready' for row in rows.values()),'images':sum(len(row['images']) for row in rows.values()),'bytes':sum(path.stat().st_size for path in (ROOT/'assets').glob('*.webp'))}))
