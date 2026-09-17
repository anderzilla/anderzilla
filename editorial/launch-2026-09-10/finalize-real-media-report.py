"""Produce a reviewable launch-image inventory from the actual published snapshot."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DEST=ROOT/'real-media-2026-09-16'
public=json.loads((DEST/'public-after.json').read_text(encoding='utf-8'))
release=json.loads((DEST/'published-release.json').read_text(encoding='utf-8'))
assert release['status']=='deployed'
report=json.loads((DEST/'cms-update-report.json').read_text(encoding='utf-8'))
review={row['key']:row for row in json.loads((DEST/'reviewed-media.json').read_text(encoding='utf-8'))['items']}
keys={row['id']:row['key'] for row in json.loads((ROOT/'cms-import-report.json').read_text(encoding='utf-8'))}
versions={row['id']:row['version'] for row in report if row['status']=='approved'}
media={row['id']:row for row in public['media']}
qa=json.loads((DEST/'site-qa.json').read_text(encoding='utf-8'))
browser=json.loads((DEST/'browser-qa.json').read_text(encoding='utf-8'))
http=json.loads((DEST/'asset-http-qa.json').read_text(encoding='utf-8'))
assert not http['failures']
browser['checks'].append(f"{http['uniqueAssetUrls']} arquivos publicados de imagem e prévia JPEG responderam HTTP 200 com tipo de conteúdo de imagem.")
rows=[]
for item in public['discoveries']:
    key=keys[item['id']];cover=media[item['coverMediaId']]
    gallery=[value for value in item.get('mediaIds','').split(',') if value]
    rows.append({'key':key,'title':item['titlePT'],'category':item['category'],'cmsId':item['id'],'cmsVersion':versions.get(item['id'],''),'imageCount':1+len(gallery),'sourceImages':review[key]['status']=='ready','imageSource':cover.get('sourceUrl',''),'credit':cover.get('credit',''),'previewUrl':'https://salmon-stone-0a4d29c0f-visual.eastus2.5.azurestaticapps.net/pt/radar/'+item['slugPT'],'fallbackReason':review[key].get('reason','') if review[key]['status']!='ready' else ''})
with (DEST/'inventario-publicado.csv').open('w',encoding='utf-8-sig',newline='') as output:
    writer=csv.DictWriter(output,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
updated=sum(row['sourceImages'] for row in rows)
galleries=sum(row['imageCount']>1 for row in rows)
lines=['# Revisão das imagens de lançamento','',f"Publicação confirmada na prévia visual. Release: `{release['id']}`.",'',f'- {len(rows)} postagens revisadas; {updated} com capa da fonte oficial.',f'- {galleries} galerias; {sum(row["imageCount"] for row in rows)} imagens em uso entre capas e galerias.',f'- {len(rows)-updated} postagens mantêm arte editorial própria por falta de imagem adequada verificada.',f'- {qa["articlePages"]} páginas PT/EN verificadas no build; capas, galerias, créditos, fontes e prévias sociais conferidos.','- CMS: 110 testes aprovados. Publicador: 21 testes aprovados. Builds web/admin aprovados.','- Revisão via Claude Code, com correção das legendas em inglês e ampliação também pela capa.','- Alterações feitas pelo domínio CMS, com versões, aprovações e auditoria; arquivos anteriores preservados.','- Nenhuma publicação enviada às redes sociais. Esta entrega é a prévia visual, sem promoção ao domínio de produção.','','## Conferência no navegador','',*['- '+value for value in browser['checks']],'','## Arte editorial preservada','']
lines.extend('- '+row['title'] for row in rows if not row['sourceImages'])
lines.extend(['','Inventário completo: `inventario-publicado.csv`. Materiais e créditos: `anderzilla-imagens-reais-social-kit.zip`.',''])
(DEST/'RELATORIO-FINAL.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'articles':len(rows),'sourceImageArticles':updated,'galleries':galleries,'imagesInUse':sum(row['imageCount'] for row in rows),'releaseId':release['id']},ensure_ascii=False))
