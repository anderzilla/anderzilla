import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'real-media-2026-09-16'
source=json.loads((ROOT/'xiaomi17ultra-extra.json').read_text(encoding='utf-8'))
alts=[(0,'Xiaomi 17 Ultra verde segurado na horizontal, com as câmeras traseiras em destaque.','Green Xiaomi 17 Ultra held horizontally, showing its rear cameras.'),(3,'Detalhe do módulo circular de câmeras Leica do Xiaomi 17 Ultra verde.','Close-up of the circular Leica camera module on the green Xiaomi 17 Ultra.')]
images=[{'url':source['images'][index]['url'],'sourcePage':source['sourcePage'],'credit':'Xiaomi','rightsUrl':source['sourcePage'],'rightsBasis':'Imagem de produto publicada pela Xiaomi em sua página oficial; crédito preservado, sem alegação de licença aberta.','kind':'photo','altPT':pt,'altEN':en} for index,pt,en in alts]
items=[{'key':'xiaomi17ultra','status':'ready','reason':'Duas imagens pertinentes localizadas na página oficial do produto e inspecionadas visualmente; fundo vazio rejeitado.','images':images}]
zero=json.loads((ROOT/'zero-company-extra.json').read_text(encoding='utf-8'))
hero=next(image for image in zero['images'] if 'post-single__featured-asset' in image['path'])
items.append({'key':'zero-company-escolha-jogadores','status':'ready','reason':'Fonte específica recuperada e capa oficial inspecionada visualmente.','articleSourceUrl':zero['sourcePage'],'images':[{'url':hero['url'],'sourcePage':zero['sourcePage'],'credit':'Electronic Arts / Lucasfilm Games — via PlayStation Blog','rightsUrl':zero['sourcePage'],'rightsBasis':'Arte de divulgação publicada na notícia oficial do resultado da votação. Direitos dos titulares preservados; não é fotografia.','kind':'official-artwork','altPT':'Arte oficial de Star Wars Zero Company reunindo os personagens do jogo.','altEN':'Official Star Wars Zero Company artwork featuring the game characters.'}]})
(ROOT/'reviewed-extras.json').write_text(json.dumps({'items':items},ensure_ascii=False,indent=2),encoding='utf-8')
