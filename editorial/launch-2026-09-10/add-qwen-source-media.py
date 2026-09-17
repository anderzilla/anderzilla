"""Normalize visually reviewed official Qwen examples discovered in rendered pages."""
import json
from pathlib import Path
from PIL import Image
DEST=Path(__file__).resolve().parent/'real-media-2026-09-16'
path=DEST/'reviewed-media.json';review=json.loads(path.read_text(encoding='utf-8'))
groups={
 'qwen-image-3':('https://qwen.ai/blog?id=qwen-image-3.0','https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen-Image/image3/','qwen-image3-',[
  ('banner.png','Qwen-Image-3.0: banner oficial de lançamento com texto e personagem ilustrado.','Qwen-Image-3.0: official launch banner with text and an illustrated character.','official-artwork'),
  ('whale.jpg','Qwen-Image-3.0: exemplo gerado por IA, publicado pela Qwen, de um infográfico sobre tubarão-baleia com texto em chinês.','Qwen-Image-3.0: AI-generated example published by Qwen, showing a whale shark infographic with Chinese text.','official-ai-example'),
  ('update1.png','Qwen-Image-3.0: exemplo gerado por IA, publicado pela Qwen, de uma explicação de geometria com texto e diagrama.','Qwen-Image-3.0: AI-generated example published by Qwen, showing a geometry explanation with text and a diagram.','official-ai-example')]),
 'qwen38-flash-next':('https://qwen.ai/blog?id=qwen3.8-flash-next','https://qianwen-res.oss-accelerate.aliyuncs.com/Qwen3.8-Flash-Next/','qwen-flash-',[
  ('Qwen3.8-flash_banner_en.jpg','Qwen3.8-Flash-Next: banner oficial anunciando o modelo com pesos abertos.','Qwen3.8-Flash-Next: official banner announcing the open-weight model.','official-artwork'),
  ('architecture.png','Qwen3.8-Flash-Next: diagrama oficial da arquitetura com camadas QSA e GDN.','Qwen3.8-Flash-Next: official architecture diagram with QSA and GDN layers.','diagram')])
}
for key,(source,base,prefix,images) in groups.items():
    item=next(row for row in review['items'] if row['key']==key)
    item.update(status='ready',reason='Materiais do artigo oficial carregado no navegador, com inspeção visual e descrição explícita dos exemplos de IA.',images=[])
    for index,(filename,pt,en,kind) in enumerate(images,1):
        target=DEST/'assets'/f'{key}-{index}.webp'
        with Image.open(DEST/(prefix+filename)) as original:
            image=original.convert('RGB');image.thumbnail((1600,1600));image.save(target,'WEBP',quality=85,method=4)
            width,height=image.size
        item['images'].append({'url':base+filename,'sourcePage':source,'credit':'Qwen / Alibaba','rightsUrl':source,'rightsBasis':'Material publicado na fonte oficial; direitos dos titulares preservados, sem alegação de licença aberta.','altPT':pt,'altEN':en,'kind':kind,'localPath':str(target),'width':width,'height':height,'bytes':target.stat().st_size,'cmsTitle':key+f' — fonte oficial {index}','licenseLabel':'Divulgação. Direitos reservados ao titular.'})
path.write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ready':sum(row['status']=='ready' for row in review['items']),'images':sum(len(row.get('images',[])) for row in review['items'] if row['status']=='ready')}))
