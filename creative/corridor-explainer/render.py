"""Editable vector-led AtlasIQ film. Layer functions are independent; 450 frames exactly."""
from pathlib import Path
import math,json,subprocess,wave,html,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parent
FF=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1920,1080,30
NAVY='#071522'; AMBER='#FFA028'; WHITE='#EAF0F9'; SLATE='#8193A5'; RED='#C46F72'; TEAL='#73BDB1'
FONT=ROOT/'assets/SpaceGrotesk.ttf'
fonts={}
def font(size,bold=False):
 key=(size,bold)
 if key not in fonts:
  f=ImageFont.truetype(str(FONT),size)
  f.set_variation_by_name('Bold' if bold else 'Regular');fonts[key]=f
 return fonts[key]
def ease(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def mix(a,b,p):return a+(b-a)*p
class Canvas:
 def __init__(self):
  self.im=Image.new('RGB',(W,H),NAVY);self.d=ImageDraw.Draw(self.im);self.svg=[]
 def group(self,name):self.svg.append(f'<g id="{name}">')
 def end(self):self.svg.append('</g>')
 def rect(self,box,fill,outline=None,r=0,width=2):
  x,y,x2,y2=box;self.d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
  self.svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" rx="{r}" fill="{fill or "none"}" stroke="{outline or "none"}" stroke-width="{width}"/>')
 def line(self,pts,fill=AMBER,width=3):
  self.d.line(pts,fill=fill,width=width,joint='curve');self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{fill}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
 def poly(self,pts,fill,outline=None):
  self.d.polygon(pts,fill=fill);self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="{fill}"/>')
  if outline:self.line(pts+[pts[0]],outline,2)
 def circle(self,x,y,r,fill=None,outline=None,width=2):
  self.d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=outline,width=width);self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{outline or "none"}" stroke-width="{width}"/>')
 def text(self,x,y,s,size=30,color=WHITE,bold=False,center=False):
  f=font(size,bold)
  if center:x-=self.d.textlength(s,font=f)/2
  self.d.text((x,y),s,font=f,fill=color)
  self.svg.append(f'<text x="{x}" y="{y+size*.95}" font-family="Space Grotesk" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(s)}</text>')
 def save_svg(self,path):
  path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><rect width="1920" height="1080" fill="'+NAVY+'"/>'+''.join(self.svg)+'</svg>')
# Natural Earth country geometry: geographic schematic, never a navigation product.
geo=json.loads((ROOT/'assets/countries.geojson').read_text())
AU=next(f['geometry'] for f in geo['features'] if f['properties']['ADMIN']=='Australia')
rings=[p[0] for p in AU['coordinates']]
def coord(lon,lat,cx=960,cy=545,scale=1):return (cx+(lon-134)*22*scale,cy+(-lat-28)*22*scale)
ROUTE=[(121.47,-30.75),(123.5,-30.9),(126.1,-30.9),(128.9,-30.8),(131.5,-30.7),(133.7,-32.1),(137.8,-32.5)]
ROAD=[(121.47,-30.75),(121.8,-32.2),(124.2,-32.6),(126.3,-32.3),(128.9,-31.9),(130.6,-31.5),(133.7,-32.1),(137.8,-32.5)]
def map_layer(c,t,cx=960,cy=510,scale=1,storm=False):
 c.group('map')
 for ring in rings:c.poly([coord(*p,cx,cy,scale) for p in ring],'#102737','#2A4050')
 # WA boundary and subtle state illumination
 c.line([coord(129,-14.9,cx,cy,scale),coord(129,-31.7,cx,cy,scale)],'#385263',2)
 c.text(cx-290*scale,cy-43*scale,'WESTERN AUSTRALIA',18,SLATE)
 c.text(cx+55*scale,cy-43*scale,'SOUTH AUSTRALIA',18,SLATE)
 rail=[coord(*p,cx,cy,scale) for p in ROUTE];road=[coord(*p,cx,cy,scale) for p in ROAD]
 c.line(rail,AMBER,4);c.line(road,'#A87C42',3)
 if storm:
  for j in range(4):
   xx,yy=coord(127+j*.45,-30.6,cx,cy,scale);rr=(35+ease(t-1)*20)*scale
   c.circle(xx,yy,rr,'#253948')
  c.line(rail[2:5],RED,5);c.line(road[2:5],RED,4)
  for j in range(7):
   xx,yy=coord(126.7+j*.4,-30.7,cx,cy,scale);c.line([(xx,yy-22),(xx-6,yy-10)],'#7794A5',2)
 for route in (rail,road):
  for j in range(3):
   p=(j*.21+t*.075)%1
   if storm:p=min(p,.36+max(0,t-1.3)*.006)
   i=min(len(route)-2,int(p*(len(route)-1)));f=p*(len(route)-1)-i
   x=mix(route[i][0],route[i+1][0],f);y=mix(route[i][1],route[i+1][1],f)
   c.rect((x-8,y-5,x+8,y+5),WHITE,r=2)
 for ix,label in [(0,'KALGOORLIE'),(-1,'PORT AUGUSTA')]:
  x,y=rail[ix];c.circle(x,y,5,WHITE);c.text(x,y+25,label,17,SLATE,center=True)
 c.end()
def logo_layer(c,x,y,s=1):
 # Original website CSS: mark 30x30/r9, inset 8px 9px, exact six-point clip-path.
 c.group('logo');c.rect((x,y,x+30*s,y+30*s),AMBER,r=9*s)
 c.poly([(x+15*s,y+8*s),(x+21*s,y+22*s),(x+17.16*s,y+22*s),(x+15*s,y+16.68*s),(x+12.84*s,y+22*s),(x+9*s,y+22*s)],NAVY)
 # Original wordmark: Space Grotesk bold, -0.02em tracking; separate IQ colour.
 xx=x+40*s
 for ch in 'AtlasIQ':
  c.text(xx,y+1*s,ch,int(20*s),AMBER if ch in 'IQ' else WHITE,True)
  xx+=c.d.textlength(ch,font=font(int(20*s),True))-.4*s
 c.end()
def icon(c,x,y,kind,size=32):
 if kind=='weather':
  c.circle(x-8,y,10,None,AMBER);c.line([(x-18,y+10),(x+20,y+10),(x+20,y-2),(x+10,y-8),(x+2,y-6)],AMBER,3)
 elif kind=='rain':
  for dx in [-12,0,12]:c.line([(x+dx,y-9),(x+dx-5,y+10)],AMBER,3)
 elif kind=='rail':
  c.rect((x-13,y-17,x+13,y+12),None,AMBER,r=5);c.line([(x-9,y+12),(x-16,y+22)],AMBER,3);c.line([(x+9,y+12),(x+16,y+22)],AMBER,3);c.line([(x-9,y-4),(x+9,y-4)],AMBER,3)
 elif kind=='truck':
  c.rect((x-28,y-12,x+5,y+10),None,AMBER,r=2);c.line([(x+5,y-6),(x+18,y-6),(x+28,y+4),(x+28,y+10),(x+5,y+10)],AMBER,3)
  for dx in [-16,17]:c.circle(x+dx,y+13,6,None,AMBER,3)
 elif kind=='warehouse':
  c.line([(x-28,y+20),(x-28,y-8),(x,y-25),(x+28,y-8),(x+28,y+20),(x-28,y+20)],AMBER,3);c.rect((x-12,y,x+12,y+20),None,AMBER)
 else:
  c.line([(x,y+24),(x,y-22)],AMBER,3)
  for j in range(3):
   yy=y-15+j*10;c.line([(x,yy+8),(x-13,yy),(x-13,yy-8)],AMBER,3);c.line([(x,yy+8),(x+13,yy),(x+13,yy-8)],AMBER,3)
def bg_layer(c,t):
 c.group('background-texture')
 # Restrained procedural ocean contour lines; no stock imagery.
 for j in range(22):
  yy=140+j*42;c.line([(x,yy+8*math.sin(x/140+j*.8+t*.08)) for x in range(0,1921,30)],'#0B1B29',1)
 c.end()
def type_layer(c,t):
 c.group('typography');c.text(960,64,'ATLASIQ  /  CORRIDOR LIFELINE',22,AMBER,center=True)
 scene=min(4,int(t/3));local=t-scene*3
 if scene<4:
  heads=['When the corridor stops…','Signals become foresight.','Know earlier. Plan ahead.','Paperwork prepared.']
  head=heads[scene]
  if scene==0 and local<.75:head='When the corridor'
  c.text(960,155+18*(1-ease(local/.6)),head,66,WHITE,True,True)
  if t>=3:c.text(960,938,'Concept preview',22,SLATE,center=True)
 c.end()
def film(t,caption=False):
 c=Canvas();bg_layer(c,t);type_layer(c,t)
 scene=min(4,int(t/3));u=t-3*scene
 if scene==0:
  map_layer(c,t,cy=500,scale=1+.045*ease(u/3),storm=u>.9)
  c.group('interface');c.text(960,824,'NULLARBOR  ·  ROAD + RAIL',22,AMBER,center=True);c.text(960,864,'A connected corridor. A shared disruption.',27,SLATE,center=True);c.end()
 elif scene==1:
  map_layer(c,t,cx=960,cy=530,scale=.68)
  c.group('interface')
  for j,(label,kind) in enumerate([('Weather','weather'),('Rainfall','rain'),('Rail status','rail')]):
   p=ease((u-j*.17)/.55);x=545+j*290;y=350+35*(1-p)
   c.rect((x,y,x+250,y+120),'#112A3A','#2C4355',16);icon(c,x+33,y+36,kind);c.text(x+68,y+22,label,25,WHITE,True)
   c.line([(x+25+k*20,y+85+8*math.sin(k*1.4+t*3+j)) for k in range(11)],AMBER,2)
   c.line([(x+125,y+120),(960,590)],'#496174',2)
  c.circle(960,590,45,'#142D3B',AMBER,3);c.circle(960,590,53+8*math.sin(u*4),None,'#755A35');c.text(960,571,'AI',28,WHITE,True,True)
  scan=600+ease(u/3)*680;c.line([(scan,506),(scan,747)],'#55766F',2)
  c.rect((690,775,1230,866),'#122A38','#B07B36',16);c.circle(725,821,6,AMBER);c.text(760,799,'Corridor risk: Elevated',34,WHITE,True)
  c.end()
 elif scene==2:
  map_layer(c,t,cx=740,cy=530,scale=.65)
  c.group('interface');p=ease(u/.55)
  x=mix(690,950,p);y=mix(775,330,p);ww=mix(540,450,p);hh=mix(91,340,p)
  c.rect((x,y,x+ww,y+hh),'#142B3B','#546776',24);c.rect((x+ww/2-30,y+14,x+ww/2+30,y+20),'#516573',r=3)
  if p>.8:
   c.text(x+30,y+54,'AtlasIQ corridor alert',27,WHITE,True);c.line([(x+30,y+104),(x+ww-30,y+104)],'#425564',2)
   c.text(x+30,y+130,'Elevated disruption risk.',26,AMBER,True);c.text(x+30,y+171,'Review shipment plans.',26)
   c.text(x+30,y+260,'Shipment planning  →',22,SLATE)
  for j,(kind,label) in enumerate([('truck','Fleet'),('warehouse','Warehouse'),('grain','Grain')]):
   bx=670+j*290;by=780;c.line([(780,632),(bx,by-60)],'#4B5B64',2)
   c.circle(bx,by,52,'#112A38','#4B5B64');icon(c,bx,by,kind);c.text(bx,by+65,label,24,SLATE,center=True)
  q=ease((u-.5)/1.2);c.line([(560,907),(1360,907)],'#3F5362',3)
  for j in range(4):c.circle(620+j*210+q*25,907,5,AMBER)
  c.end()
 elif scene==3:
  c.group('interface');p=ease(u/.5);x=mix(950,630,p);y=mix(330,305,p)
  c.rect((x,y,x+620,y+570),'#122A3A','#4B6173',22)
  c.text(x+38,y+34,'Emergency permit draft',37,WHITE,True);c.text(x+38,y+89,'SAMPLE  /  HUMAN REVIEW REQUIRED',18,SLATE)
  for j,(label,value) in enumerate([('Operator','Sample operator'),('Vehicle','Vehicle 01'),('Shipment','Sample shipment'),('Requested movement','Sample request')]):
   yy=y+146+j*67;c.text(x+38,yy,label,20,SLATE)
   if u>j*.28+.35:c.text(x+290,yy,value,22)
   c.line([(x+38,yy+47),(x+580,yy+47)],'#2B4355',1)
  c.rect((x+38,y+463,x+582,y+532),'#183E40',TEAL,12);c.text(x+310,y+477,'Ready for review',31,TEAL,True,True)
  if u>.7:
   c.rect((1270,598,1510,746),'#193342','#496577',16);c.text(1295,620,'Risk summary',26,WHITE,True)
   for j in range(3):c.line([(1295,674+j*17),(1480-j*26,674+j*17)],SLATE,3)
  c.text(960,898,'Review before submission',26,SLATE,center=True);c.end()
 else:
  # Everything is static from 13.5 s onward, including ocean texture.
  if t>=13.5:
   c=Canvas();bg_layer(c,13.5)
  p=ease(u/1.1);c.group('interface')
  yy=mix(730,372,p);length=mix(720,330,p)
  c.line([(960-length/2,yy),(960+length/2,yy)],AMBER,3);c.circle(960-length/2,yy,4,AMBER);c.circle(960+length/2,yy,4,AMBER);c.end()
  if u>.4:
   logo_layer(c,720,440,4.3)
   c.group('typography');c.text(960,620,'Corridor Lifeline Agent',44,WHITE,True,True)
   c.text(960,707,'Anticipate disruption.',32,WHITE,center=True);c.text(960,752,'Prepare your response.',32,WHITE,center=True)
   c.text(960,842,'Explore the vision · atlasiqco.com',28,AMBER,center=True);c.text(960,915,'In development',22,SLATE,center=True);c.end()
 if caption and t<13.5:
  phrases=[(0,.0,3,'When freight routes face disruption,\npreparation matters.'),(1,3,6,'AtlasIQ’s Corridor Lifeline concept\nconnects risk signals,'),(2,6,9,'business alerts'),(3,9,12,'and emergency paperwork drafts—'),(4,12,13.5,'helping you prepare your response.')]
  for _,a,b,s in phrases:
   if a<=t<b:
    c.group('captions');c.rect((470,983,1450,1070),'#06111C',r=12)
    lines=s.split('\n')
    for j,line in enumerate(lines):c.text(960,995+j*31,line,26,WHITE,center=True)
    c.end()
 return c

def audio():
 sr=48000;n=sr*15;times=np.arange(n)/sr;voice=np.zeros(n);music=np.zeros(n);fx=np.zeros(n)
 slots=[(.10,2.80),(3.03,5.96),(6.13,7.55),(9.03,11.60),(11.67,13.45)]
 for j,(a,b) in enumerate(slots,1):
  data=subprocess.check_output([FF,'-v','error','-i',str(ROOT/f'audio/voice-{j:02}.aiff'),'-f','f32le','-ac','1','-ar',str(sr),'-'])
  raw=np.frombuffer(data,dtype='<f4');duration=len(raw)/sr;target=min(duration,b-a)
  # Preserve pitch through ffmpeg's tempo filter when compression is required.
  if duration>target:
   ratio=duration/target
   filters=[]
   while ratio>2:filters.append('atempo=2');ratio/=2
   filters.append(f'atempo={ratio}')
   raw=np.frombuffer(subprocess.check_output([FF,'-v','error','-i',str(ROOT/f'audio/voice-{j:02}.aiff'),'-af',','.join(filters),'-f','f32le','-ac','1','-ar',str(sr),'-']),dtype='<f4')
  start=int(a*sr);voice[start:start+len(raw)]+=raw[:n-start]
  print('VO',j,'original',round(duration,3),'placed',round(len(raw)/sr,3),'start',a,flush=True)
 # Original electronic cue at 105 BPM, ducked beneath narration.
 beat=60/105
 for k,tt in enumerate(np.arange(0,14.6,beat)):
  st=int(tt*sr);length=min(int(sr*.43),n-st);z=np.arange(length)/sr
  music[st:st+length]+=.065*np.sin(2*np.pi*(110 if k%4 else 82.41)*z)*np.exp(-z*13)
 for frequency in [164.81,220,329.63]:music+=.009*np.sin(2*np.pi*frequency*times)*np.minimum(1,times/2)*np.minimum(1,(15-times)/1.5)
 def chime(at,freq,level=.05,dur=.55):
  st=int(at*sr);l=min(int(dur*sr),n-st);z=np.arange(l)/sr;fx[st:st+l]+=level*(np.sin(2*np.pi*freq*z)+.3*np.sin(2*np.pi*freq*2*z))*np.exp(-z*7)
 for at in [3.1,3.3,3.5,9.4,9.7,10,10.3]:chime(at,900,.022,.18)
 chime(6.2,659.25,.045);chime(6.34,880,.03);chime(12.5,440,.04);chime(12.7,554.37,.04);chime(12.9,659.25,.04)
 z=times-1;fx+=.015*np.sin(2*np.pi*55*times)*np.exp(-((z-.7)/.6)**2)
 def save(name,arr):
  with wave.open(str(ROOT/'audio'/name),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(arr,-1,1)*32767).astype('<i2').tobytes())
 voice*=.88;save('voiceover.wav',voice);save('music.wav',music);save('effects.wav',fx);save('mix.wav',voice+music+fx)
 print('Peak',np.max(np.abs(voice+music+fx)),flush=True)
def render():
 (ROOT/'frames').mkdir(exist_ok=True);audio()
 def encode(name,caption=False):
  cmd=[FF,'-v','error','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'exports'/name)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  for i in range(450):
   c=film(i/30,caption);proc.stdin.write(c.im.tobytes())
   if not caption:
    c.save_svg(ROOT/f'frames/{i:03}.svg')
    if i in [65,145,235,325,420]:c.im.save(ROOT/f'exports/scene-{i//90+1}.png')
   if i%90==0:print(name,'frame',i,flush=True)
  proc.stdin.close();assert proc.wait()==0
 encode('AtlasIQ-silent.mp4');encode('caption-picture.mp4',True)
 for picture,name in [('AtlasIQ-silent.mp4','AtlasIQ-voiceover.mp4'),('caption-picture.mp4','AtlasIQ-captioned.mp4')]:
  subprocess.run([FF,'-v','error','-y','-i',str(ROOT/'exports'/picture),'-i',str(ROOT/'audio/mix.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-t','15','-movflags','+faststart',str(ROOT/'exports'/name)],check=True)
 (ROOT/'exports/caption-picture.mp4').unlink()
if __name__=='__main__':render()
