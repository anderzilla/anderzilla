"""Last visual corrections before bilingual caption review and CMS import."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DEST=ROOT/'real-media-2026-09-16'
spec=importlib.util.spec_from_file_location('prep',ROOT/'prepare-real-media.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
data=json.loads((DEST/'candidate-media.json').read_text(encoding='utf-8'))
rows={row['key']:row for row in data['items']}
press=json.loads((DEST/'oneplus-press.json').read_text(encoding='utf-8'))
_,phone,error=module.prepare(('oneplus15-165hz',{'url':press['images'][0]['url'],'sourcePage':press['sourcePage'],'credit':'OnePlus','rightsUrl':press['sourcePage'],'rightsBasis':'Imagem fornecida no comunicado de imprensa oficial de lançamento do OnePlus 15.','altPT':'OnePlus 15 em três cores, com os módulos traseiros de câmera em destaque.','altEN':'OnePlus 15 in three colors, showing its rear camera modules.','kind':'photo'},0))
assert phone,error
rows['oneplus15-165hz'].update(images=[phone],status='ready',reason='Foto de divulgação do aparelho recuperada do comunicado oficial e inspecionada visualmente.')
row=rows['galaxy-s26-privacy'];row['images']=[row['images'][2],row['images'][0],row['images'][1]]
row=rows['cod-the-haunting-setembro'];row['images']=list(reversed(row['images']))
for row in rows.values():
    for index,image in enumerate(row['images']):
        image['cmsTitle']=f"{row['key']} — fonte oficial {index+1}"
        if row['key']=='gta-vi-data-plataformas':image['kind']='official-artwork'
    if row['status']=='fallback':
        row['reason']='Manter ilustração editorial original: não foi obtida foto ou captura pertinente com qualidade suficiente na revisão das fontes. '+row['reason']
data['items']=list(rows.values())
(DEST/'candidate-media-final.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'reviewed':len(rows),'ready':sum(row['status']=='ready' for row in rows.values()),'galleryArticles':sum(len(row['images'])>1 for row in rows.values()),'images':sum(len(row['images']) for row in rows.values())}))
