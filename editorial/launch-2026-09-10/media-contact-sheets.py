"""Diagnostic thumbnails for visual inspection, never used as site imagery."""
import json, math
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent/'real-media-2026-09-16'
data=json.loads((ROOT/'candidate-media.json').read_text(encoding='utf-8'))
images=[(row['key'],index,image) for row in data['items'] for index,image in enumerate(row['images'])]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for start in range(0,len(images),16):
    subset=images[start:start+16]
    sheet=Image.new('RGB',(1280,math.ceil(len(subset)/4)*225),'#d4d4d4')
    draw=ImageDraw.Draw(sheet)
    for position,(key,index,image) in enumerate(subset):
        x=(position%4)*320;y=(position//4)*225
        with Image.open(image['localPath']) as source:
            thumbnail=ImageOps.contain(source.convert('RGB'),(310,180))
            sheet.paste(thumbnail,(x+(320-thumbnail.width)//2,y))
        draw.text((x+5,y+182),f'{start+position}: {key[:31]}',font=font,fill='black')
        draw.text((x+5,y+203),f'image {index+1}',font=font,fill='black')
    sheet.save(ROOT/f'contact-{start//16+1}.jpg',quality=90)
(ROOT/'contact-index.json').write_text(json.dumps([{'index':i,'key':key,'imageIndex':idx,'localPath':img['localPath']} for i,(key,idx,img) in enumerate(images)],indent=2),encoding='utf-8')
print(len(images))
