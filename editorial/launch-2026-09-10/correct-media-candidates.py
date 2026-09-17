"""Apply visual-review decisions; keep the import gate closed."""
import concurrent.futures, importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'real-media-2026-09-16'
spec=importlib.util.spec_from_file_location('prepare',ROOT/'prepare-real-media.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
data=json.loads((DEST/'candidate-media.json').read_text(encoding='utf-8'))
rows={row['key']:row for row in data['items']}
inventory={row['key']:row for row in json.loads((DEST/'source-image-inventory.json').read_text(encoding='utf-8'))}
prelim={row['key']:row for row in json.loads((DEST/'research_prelim.json').read_text(encoding='utf-8'))}

# Indices refer to the first visual review, saved separately for reproducibility.
choices={'gta-vi-data-plataformas':[1], 'no-mans-sky-cosmos':[2,0], 'muramasa-revenant-blades':[2,1], 'ffvii-revelation-data':[2,1], 'legion-go-steamos':[2], 'honor-magic-v6':[0], 'oppo-findx9ultra':[1], 'honor-robot-phone':[1,0]}
for key,indices in choices.items():
    rows[key]['images']=[rows[key]['images'][i] for i in indices]
rows['claude-fable-mythos-51'].update(status='fallback',images=[],reason='Imagem isolada de microscopia não serve como capa representativa dos modelos; manter arte editorial identificada.')
new=[]
def add(key,url,credit,pt,en,kind='photo'):
    page=inventory[key]['sourcePage']
    new.append((key,{'url':url,'sourcePage':page,'credit':credit,'rightsUrl':page,'rightsBasis':'Imagem publicada na fonte oficial identificada. Crédito e direitos dos titulares preservados; não alegamos licença aberta.','altPT':pt,'altEN':en,'kind':kind},len([x for x in new if x[0]==key])))

for key in ['physint-xbox-kojima','rog-ally-atualizacao-dock','xbox-insiders-setembro','xbox-discos-direito-digital','xbox-tokyo-game-show-2026']:
    add(key,prelim[key]['metas'][0][1],'Microsoft / Xbox','Imagem oficial do anúncio Xbox.','Official image accompanying the Xbox announcement.','official-artwork')
add('steam-deck-oled-ficha',prelim['steam-deck-oled-ficha']['metas'][0][1],'Valve','Steam Deck OLED em imagem oficial de divulgação.','Steam Deck OLED in official promotional imagery.')
add('raspberrypi-radio',prelim['raspberrypi-radio']['metas'][0][1],'Raspberry Pi — divulgação do projeto','Rádio com Raspberry Pi apresentado na reportagem original.','Raspberry Pi radio featured in the original article.')
add('logitech-mx-keypad',prelim['logitech-mx-keypad']['metas'][0][1],'Logitech','Teclado auxiliar Logitech MX em imagem de divulgação.','Logitech MX keypad in promotional imagery.')
add('gemini-38-flash',prelim['gemini-38-flash']['metas'][0][1],'Google','Imagem de divulgação do Gemini 3.8 Flash.','Gemini 3.8 Flash announcement artwork.','official-artwork')
for index,pt,en in [(9,'Jogadores usam os óculos ROG XREAL R1 com computador e portátil.','Players use ROG XREAL R1 glasses with a computer and handheld.'),(20,'Jogador usa os óculos ROG XREAL R1 em uma estação de PC.','Player using ROG XREAL R1 glasses at a PC gaming station.'),(21,'Jogador usa os óculos ROG XREAL R1 com o portátil ROG Xbox Ally.','Player using ROG XREAL R1 glasses with a ROG Xbox Ally handheld.')]:
    add('rog-xreal-r1',inventory['rog-xreal-r1']['images'][index]['url'],'ASUS ROG',pt,en)
add('rog-rapture-gt-bn98',inventory['rog-rapture-gt-bn98']['images'][5]['url'],'ASUS ROG','Roteador ROG Rapture GT-BN98 Pro em imagem de divulgação.','ROG Rapture GT-BN98 Pro router in promotional imagery.')
for index in [14,15]:
    add('gta-vi-data-plataformas',inventory['gta-vi-data-plataformas']['images'][index]['url'],'Rockstar Games','Cena de GTA VI divulgada pela Rockstar Games.','GTA VI scene published by Rockstar Games.','screenshot')
for index,error in enumerate(rows['logitech-superstrike-clique']['downloadErrors']):
    url=error['url'].replace('w_422,h_220,','')
    add('logitech-superstrike-clique',url,'Logitech G','Detalhe do mouse Logitech G PRO X2 Superstrike.','Detail of the Logitech G PRO X2 Superstrike mouse.')

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    received=list(pool.map(module.prepare,new))
grouped={}
for key,image,error in received:
    if image: grouped.setdefault(key,[]).append(image)
    else: print(json.dumps({'key':key,'error':error}),flush=True)
for key,images in grouped.items():
    if key in ['steam-deck-oled-ficha','gemini-38-flash']:
        images+=rows[key]['images'][:2]
    elif key=='gta-vi-data-plataformas':
        images+=rows[key]['images']
    rows[key].update(status='ready',images=images[:3],reason='Seleção corrigida por inspeção visual e conferência da fonte oficial.')
data['items']=list(rows.values())
(DEST/'candidate-media-corrected.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ready':sum(row['status']=='ready' for row in rows.values()),'images':sum(len(row['images']) for row in rows.values())}))
