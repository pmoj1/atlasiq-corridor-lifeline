import sys, json, shutil
sys.path.insert(0,'/tmp/atlasiq-brand-deps')
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET
root=Path('/Users/a111/Desktop/AtlasIQ/business-brand-kit')
source=root/'fonts/SpaceGrotesk.ttf'
fonts={}
for weight in (500,600):
 f=TTFont(source)
 if 'fvar' in f:f=instantiateVariableFont(f,{'wght':weight},inplace=True)
 target=Path(f'/tmp/atlasiq-space-{weight}.ttf');f.save(target)
 fonts[weight]=(f,target)
ink='#0b0e10';ivory='#f1eee6';amber='#e9aa4b'
def make(name,fg,accent,bg=None,icon=False):
 W,H=(320,320) if icon else (880,224)
 im=Image.new('RGBA',(W*4,H*4),bg or (0,0,0,0));d=ImageDraw.Draw(im)
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><title>AtlasIQ {name}</title>']
 if bg:svg.append(f'<path fill="{bg}" d="M0 0H{W}V{H}H0Z"/>')
 x,y,s=(64,57.6,6.4) if icon else (48,48,4)
 pts=[(x+15*s,y),(x+30*s,y+32*s),(x+22.8*s,y+32*s),(x+15*s,y+15.36*s),(x+7.2*s,y+32*s),(x,y+32*s)]
 d.polygon([(round(a*4),round(b*4)) for a,b in pts],fill=accent)
 svg.append(f'<polygon fill="{accent}" points="'+ ' '.join(f'{a:g},{b:g}' for a,b in pts)+'"/>')
 if not icon:
  cursor=216; baseline=151; size=112
  for char in 'AtlasIQ':
   weight=500 if char in 'IQ' else 600
   f,path=fonts[weight];glyphs=f.getGlyphSet(); glyph=f.getBestCmap()[ord(char)]
   pen=SVGPathPen(glyphs);glyphs[glyph].draw(pen);scale=size/f['head'].unitsPerEm
   color=accent if char in 'IQ' else fg
   svg.append(f'<path fill="{color}" transform="translate({cursor:g} {baseline}) scale({scale:g} {-scale:g})" d="{pen.getCommands()}"/>')
   pf=ImageFont.truetype(str(path),size*4)
   d.text((round(cursor*4),baseline*4),char,font=pf,fill=color,anchor='ls')
   cursor+=f['hmtx'][glyph][0]*scale-size*.07
 svg.append('</svg>')
 p=root/'logos'/name
 p.with_suffix('.svg').write_text('\n'.join(svg))
 im.save(p.with_suffix('.png'))
 ET.parse(p.with_suffix('.svg'))
 if bg is None:
  assert im.getextrema()[3]==(0,255)
 return im
make('atlasiq-logo-dark-background',ivory,amber,ink)
make('atlasiq-logo-light-background',ink,amber,ivory)
a=make('atlasiq-logo-transparent-for-dark',ivory,amber)
b=make('atlasiq-logo-transparent-for-light',ink,amber)
make('atlasiq-logo-transparent-white','#ffffff','#ffffff')
make('atlasiq-logo-transparent-black','#000000','#000000')
make('atlasiq-mark-transparent',ink,amber,icon=True)
make('atlasiq-mark-dark-background',ivory,amber,ink,True)
# Contact sheet shows transparent assets against their intended backgrounds.
board=Image.new('RGB',(1760,1120),ivory)
for i,n in enumerate(['atlasiq-logo-dark-background','atlasiq-logo-light-background','atlasiq-logo-transparent-for-dark','atlasiq-logo-transparent-for-light']):
 tile=Image.new('RGBA',(880,280),ink if i%2==0 else ivory)
 pic=Image.open(root/'logos'/f'{n}.png');pic.thumbnail((880,224));tile.alpha_composite(pic,(0,20))
 ImageDraw.Draw(tile).text((48,250),n,fill=ivory if i%2==0 else ink,font=ImageFont.truetype(str(fonts[500][1]),16))
 board.paste(tile.convert('RGB'),((i%2)*880,(i//2)*560))
d=ImageDraw.Draw(board)
for i,(label,col) in enumerate([('Ink  #0B0E10',ink),('Ivory  #F1EEE6',ivory),('Amber  #E9AA4B',amber)]):
 x=60+i*550;d.rectangle((x,900,x+490,1010),fill=col,outline=ink);d.text((x,1030),label,fill=ink,font=ImageFont.truetype(str(fonts[500][1]),26))
board.save(root/'brand-kit-preview.png')
print('Created 8 SVG/PNG pairs; parsed all SVGs and checked alpha on all transparent PNGs.')
