from pathlib import Path
from base64 import b64encode
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
import cairosvg

root = Path(__file__).parent
source = Path('C:/Users/ander/.codex/generated_images/01a08bd0-cc94-7250-a25d-381de6a84fd2/exec-ce8dd22e-0281-4955-b226-9a41c9c5fe75.png')
raw = source.read_bytes()
(root / 'skull-aligned-teeth.png').write_bytes(raw)
im = Image.open(source).convert('L')
# Analyze the ink bounds; retain the original generated raster unchanged.
bbox = im.point(lambda p: 255 if p < 100 else 0).getbbox()
left, top, right, bottom = bbox
font = TTFont(root / 'changa-one/ChangaOne-Regular.ttf')
glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
cursor, paths, bounds = 0, [], []
for char in 'ANDERZILLA':
    name = cmap[ord(char)]
    glyph = glyphs[name]
    pen = SVGPathPen(glyphs)
    glyph.draw(pen)
    bp = BoundsPen(glyphs)
    glyph.draw(bp)
    x0, y0, x1, y1 = bp.bounds
    bounds.append((cursor+x0, y0, cursor+x1, y1))
    paths.append(f'<path transform="translate({cursor} 0)" d="{pen.getCommands()}"/>')
    cursor += glyph.width
x0 = min(b[0] for b in bounds)
y0 = min(b[1] for b in bounds)
x1 = max(b[2] for b in bounds)
y1 = max(b[3] for b in bounds)
height, margin, gap = 300, 90, 42
text_scale = height / (y1-y0)
icon_scale = height / (bottom-top)
icon_width = (right-left)*icon_scale
text_width = (x1-x0)*text_scale
width = 2*margin+icon_width+gap+text_width
canvas_height = height+2*margin
text_x = margin+icon_width+gap-x0*text_scale
baseline = margin+y1*text_scale
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width:.3f}" height="{canvas_height}" viewBox="0 0 {width:.3f} {canvas_height}">
<title>ANDERZILLA — Changa One Regular — estudo com dentes alinhados</title>
<rect width="100%" height="100%" fill="white"/>
<svg x="{margin}" y="{margin}" width="{icon_width:.5f}" height="{height}" viewBox="{left} {top} {right-left} {bottom-top}" overflow="hidden">
<image width="{im.width}" height="{im.height}" xlink:href="data:image/png;base64,{b64encode(raw).decode()}"/>
</svg>
<g fill="black" transform="translate({text_x:.5f} {baseline:.5f}) scale({text_scale:.8f} {-text_scale:.8f})">{''.join(paths)}</g>
</svg>'''
(root / 'anderzilla-changa-one-v1.svg').write_text(svg, encoding='utf-8')
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(root/'anderzilla-changa-one-v1.png'), output_width=2400)
print(f'Icon ink height = text ink height = {height}; Changa One Regular actual glyph outlines; SVG retains raster mascot.')
