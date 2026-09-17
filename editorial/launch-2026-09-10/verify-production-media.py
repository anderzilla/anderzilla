import concurrent.futures,datetime,hashlib,json,urllib.request,urllib.error
from pathlib import Path
DATA=Path(__file__).resolve().parent/'real-media-2026-09-16'
build=json.loads((DATA/'production-build.json').read_text());artifact=Path(build['artifact'])
marker=json.loads((artifact/'cms-release.json').read_text())
for host in ('anderzilla.com','www.anderzilla.com'):
    with urllib.request.urlopen('https://'+host+'/cms-release.json?release='+marker['releaseId'],timeout=30) as r:
        assert json.load(r)==marker,host
public=json.loads((DATA/'public-after.json').read_text(encoding='utf-8'))
media={r['id']:r for r in public['media']};refs=set();pages=[]
for item in public['discoveries']:
    refs.add(item['coverMediaId']);refs.update(filter(None,item.get('mediaIds','').split(',')))
    for lang in ('pt','en'):pages.append('/'+lang+'/radar/'+item['slug'+lang.upper()])
images={media[key][field] for key in refs for field in ('url','previewUrl')}
def check(task):
    path,is_image=task
    request=urllib.request.Request('https://anderzilla.com'+path,method='HEAD' if is_image else 'GET')
    with urllib.request.urlopen(request,timeout=30) as r:
        assert r.status==200,path
        assert 'noindex' not in r.headers.get('X-Robots-Tag','').lower(),path
        if is_image:assert r.headers.get_content_type().startswith('image/'),path
        else:
            raw=r.read();assert hashlib.sha256(raw).digest()==hashlib.sha256((artifact/(path.lstrip('/')+'.html')).read_bytes()).digest(),path
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    list(executor.map(check,[(p,False) for p in pages]+[(p,True) for p in sorted(images)]))
for path in ('/','/robots.txt','/sitemap.xml'):
    with urllib.request.urlopen('https://anderzilla.com'+path,timeout=30) as r:
        assert r.status==200
        text=r.read().decode('utf-8')
        if path=='/':assert text==(artifact/'index.html').read_text(encoding='utf-8')
        if path=='/robots.txt':assert 'Disallow: /' not in text and 'https://anderzilla.com/sitemap.xml' in text
        if path=='/sitemap.xml':assert all('https://anderzilla.com'+page in text for page in pages)
try:
    urllib.request.urlopen('https://anderzilla.com/__release-smoke-not-found-40565a1a',timeout=30)
    raise AssertionError('Missing route did not return 404')
except urllib.error.HTTPError as error:assert error.code==404
receipt={**build,'status':'deployed-and-verified','url':'https://anderzilla.com','verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verifiedArticlePages':len(pages),'verifiedImageUrls':len(images),'domains':['anderzilla.com','www.anderzilla.com'],'rollbackArtifact':'Z:/AnderZilla/.deploy/production-before-real-media-20260916'}
(DATA/'production-release.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt),flush=True)
