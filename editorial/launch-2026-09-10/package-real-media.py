"""Export the actual published covers, galleries and social copy with credits."""
import json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DEST=ROOT/'real-media-2026-09-16'
public=json.loads((DEST/'public-after.json').read_text(encoding='utf-8'))
qa=json.loads((DEST/'site-qa.json').read_text(encoding='utf-8'))
artifact=Path(qa['artifact'])
keys={row['id']:row['key'] for row in json.loads((ROOT/'cms-import-report.json').read_text(encoding='utf-8'))}
media={row['id']:row for row in public['media']}
folder=DEST/'social-kit'
folder.mkdir(exist_ok=True)
count=0
for item in public['discoveries']:
    target=folder/keys[item['id']];target.mkdir(exist_ok=True)
    refs=[item['coverMediaId']]+[key for key in item.get('mediaIds','').split(',') if key]
    credits=[]
    for index,key in enumerate(refs):
        image=media[key]
        name='cover.jpg' if index==0 else f'gallery-{index:02}.jpg'
        shutil.copyfile(artifact/image['previewUrl'].lstrip('/'),target/name)
        credits.append({'file':name,'altPT':image.get('altPT'),'altEN':image.get('altEN'),'credit':image.get('credit'),'license':image.get('license'),'sourceUrl':image.get('sourceUrl')})
        count+=1
    (target/'credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2),encoding='utf-8')
    text=[f"# {item['titlePT']}",item['summaryPT'],'[Capa](cover.jpg)','## Créditos das imagens']
    text += [f"- {row['file']}: {row['credit']}. {row['sourceUrl'] or 'Arte editorial original AnderZilla.'}" for row in credits]
    for lang,label in [('PT','Português'),('EN','English')]:
        text.append('## '+label)
        for platform in ['Instagram','Facebook','Whatsapp']:
            text.extend(['### '+platform,item.get('social'+platform+lang,'')])
        text.extend(['### Hashtags',item.get('hashtags'+lang,'')])
    (target/'post.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
(folder/'README.md').write_text('# Kit editorial com imagens das fontes\n\n60 pastas, uma por notícia. Cada pasta contém capa JPEG, galeria quando disponível, créditos e textos PT/EN para redes. Preserve os créditos e o contexto editorial. As imagens sem fotografia oficial adequada mantêm a arte original identificada.\n\nOs links dos textos sociais usam o domínio canônico AnderZilla; o site está publicado em https://anderzilla.com. Nenhuma postagem foi enviada às redes sociais.\n',encoding='utf-8')
archive=DEST/'anderzilla-imagens-reais-social-kit.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as output:
    for path in folder.rglob('*'):
        if path.is_file():output.write(path,path.relative_to(folder))
print(json.dumps({'articles':len(public['discoveries']),'images':count,'archive':str(archive),'bytes':archive.stat().st_size}))
