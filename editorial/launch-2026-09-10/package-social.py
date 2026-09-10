"""Export a portable social handoff; no messages are sent to social platforms."""
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
items=json.loads((ROOT/'launch-manifest.json').read_text(encoding='utf-8'))['items']
folder=ROOT/'social-kit'
folder.mkdir(exist_ok=True)
index=['# AnderZilla — acervo de lançamento','', '60 matérias revisadas em português e inglês, dez por categoria. As artes desta edição usam texto em português. Legendas em PT/EN; nenhum post enviado automaticamente.','', '## Como usar','', 'No CMS, abra **Conteúdo**, busque a matéria e escolha **Editar**. O kit social oferece textos para copiar e o card vertical para baixar. A capa horizontal acompanha o link nos metadados Open Graph. Instagram: use o card vertical e a legenda; atualize o link da bio antes de anunciar esse caminho. Facebook e WhatsApp: use o link e o texto próprios do canal.','', 'Os links definitivos usam anderzilla.com. Distribua-os somente depois de a versão correspondente estar publicada nesse domínio. A prévia visual serve para revisão e permanece sem indexação.','', '## Acervo','']
labels={'games':'Games','consoles':'Consoles','celulares':'Celulares','ia':'IA','gadgets':'Gadgets','curiosidades':'Curiosidades e desenvolvimento'}
if (ROOT/'published-release.json').exists():
    release=json.loads((ROOT/'published-release.json').read_text(encoding='utf-8'))
    index[10:10]=['## Entrega conferida','',f"[Prévia visual]({release['url']}) · [CMS](https://victorious-mud-09355980f.3.azurestaticapps.net) · Release `{release['id']}`: {release['status']}. Conteúdo cadastrado e aprovado; produção ainda não promovida.",'','[Relatório de entrega](ENTREGA.md)','']
for category,label in labels.items():
    index += ['### '+label,'']
    for item in [x for x in items if x['data']['category']==category]:
        d=item['data']
        index.append(f"- [{d['titlePT']}](social-kit/{item['key']}.md) — {d['editorialType']} · apuração {d['verifiedAt']}")
    index.append('')
for item in items:
    d=item['data']
    lines=['# '+d['titlePT'],'',d['summaryPT'],'',f"Formato: {d['editorialType']} · Evento: {d['eventDate']} · Apuração: {d['verifiedAt']}",'',f"[Capa horizontal](../cards/{item['key']}-cover.jpg) · [Card vertical](../cards/{item['key']}-instagram.png)",'']
    for lang,label in [('PT','Português'),('EN','English')]:
        lines += ['## '+label,'']
        for channel in ['Instagram','Facebook','Whatsapp']:
            lines += ['### '+channel,'',d['social'+channel+lang],'']
    lines += ['## Fontes','']
    lines += [f"- [{source['name']}]({source['url']})"+(' · '+source['publishedAt'] if source.get('publishedAt') else '') for source in json.loads(d['sources'])]
    (folder/(item['key']+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
(ROOT/'README.md').write_text('\n'.join(index),encoding='utf-8')
with zipfile.ZipFile(ROOT/'anderzilla-launch-social-kit.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in [ROOT/'README.md',*ROOT.glob('ENTREGA.md'),*folder.glob('*.md'),*ROOT.glob('review-*.md'),*(ROOT/'cards').glob('*.jpg'),*(ROOT/'cards').glob('*.png')]:
        archive.write(file,file.relative_to(ROOT))
print('Portable kit: 60 articles, 120 PT images, 360 PT/EN captions.')
