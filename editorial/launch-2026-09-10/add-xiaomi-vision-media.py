"""Add an official image recovered from the source's rendered article."""
import hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'real-media-2026-09-16'
path=DEST/'reviewed-media.json'
review=json.loads(path.read_text(encoding='utf-8'))
key='xiaomi-vision-gran-turismo'
url='https://i02.appmifile.com/9_operatorx_operatorx_uploadTiptapImage/28/02/2026/21cddab97b6334d2f8a3bb54a041b936.jpg'
target=DEST/'assets'/(hashlib.sha256(url.encode()).hexdigest()+'.webp')
with Image.open(DEST/'xiaomi-vision-official.jpg') as original:
    image=original.convert('RGB');image.thumbnail((1600,1600))
    image.save(target,'WEBP',quality=85,method=4)
    width,height=image.size
item=next(row for row in review['items'] if row['key']==key)
item.update(status='ready',reason='Imagem oficial recuperada do artigo renderizado no navegador e inspecionada visualmente.',images=[{
    'url':url,'sourcePage':'https://www.mi.com/global/discover/article?id=5972',
    'credit':'Xiaomi','rightsUrl':'https://www.mi.com/global/discover/article?id=5972',
    'rightsBasis':'Imagem publicada na fonte oficial; direitos dos titulares preservados, sem alegação de licença aberta.',
    'altPT':'Xiaomi Vision Gran Turismo: imagem oficial de divulgação do conceito em vista frontal de três quartos.',
    'altEN':'Xiaomi Vision Gran Turismo: official promotional image of the concept in a front three-quarter view.',
    'kind':'official-product-render','localPath':str(target),'width':width,'height':height,
    'bytes':target.stat().st_size,'cmsTitle':key+' — fonte oficial 1',
    'licenseLabel':'Divulgação. Direitos reservados ao titular.'
}])
path.write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ready':sum(row['status']=='ready' for row in review['items']),'images':sum(len(row.get('images',[])) for row in review['items'] if row['status']=='ready')}))
