"""AtlasIQ 30-second film. Editable scene functions, physical-image layers and exact typography."""
from pathlib import Path
from functools import lru_cache
import json,math,subprocess,wave,sys,hashlib,xml.etree.ElementTree as ET
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
cv2.setNumThreads(1)
R=Path(__file__).resolve().parent;A=R/'assets';E=R/'exports';E.mkdir(exist_ok=True)
CFG=json.loads((R/'film.json').read_text());W,H=1920,1080;FPS=30;N=900;FF=imageio_ffmpeg.get_ffmpeg_exe()
NAVY=(7,21,34);WHITE=(234,240,249);AMBER=(255,160,40);SLATE=(129,147,165);TEAL=(128,199,186);RED=(196,121,127)
def ease(x):
 x=max(0,min(1,x));return x*x*x*(x*(6*x-15)+10)
def out(x):return 1-(1-max(0,min(1,x)))**3
def lerp(a,b,p):return a+(b-a)*p
def colour(a,b,p):return tuple(int(lerp(x,y,p)) for x,y in zip(a,b))
@lru_cache(200)
def font(n,bold=False):
 f=ImageFont.truetype(str(A/'SpaceGrotesk.ttf'),int(n));f.set_variation_by_name('Bold' if bold else 'Regular');return f
@lru_cache(20)
def plate(name):return Image.open(A/name).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
@lru_cache(1)
def truck():
 im=Image.open(A/'truck-cutout.png').convert('RGBA');box=im.getchannel('A').getbbox();return im.crop(box)
def layer():return Image.new('RGBA',(W,H))
def text(im,x,y,s,size=34,color=WHITE,bold=False,anchor='la',opacity=1):
 d=ImageDraw.Draw(im);d.text((x,y),s,font=font(size,bold),fill=(*color,int(255*max(0,min(1,opacity)))),anchor=anchor)
def rr(im,box,fill=(15,32,47,245),radius=24,stroke=None,width=1):
 ImageDraw.Draw(im).rounded_rectangle(tuple(round(v) for v in box),radius=radius,fill=fill,outline=stroke,width=width)
def line(im,pts,color=AMBER,width=3,alpha=255):
 pts=np.array(pts,np.int32);pad=width+3
 x0=max(0,int(pts[:,0].min())-pad);y0=max(0,int(pts[:,1].min())-pad);x1=min(im.width,int(pts[:,0].max())+pad+1);y1=min(im.height,int(pts[:,1].max())+pad+1)
 if x1<=x0 or y1<=y0:return
 arr=np.array(im.crop((x0,y0,x1,y1)));cv2.polylines(arr,[pts-np.array([x0,y0])],False,(*color,alpha),width,cv2.LINE_AA);im.paste(Image.fromarray(arr),(x0,y0))
def circle(im,x,y,r,color=None,stroke=None,width=2):
 d=ImageDraw.Draw(im);d.ellipse((x-r,y-r,x+r,y+r),fill=color,outline=stroke,width=width)
def composite(base,over,opacity=1):
 if opacity<=0:return base
 if opacity<.999:
  over=over.copy();over.putalpha(over.getchannel('A').point(lambda a:int(a*opacity)))
 return Image.alpha_composite(base,over)
def shadow(im,box,radius=26,opacity=105,offset=(0,18),blur=26):
 sh=layer();x,y,x2,y2=box;rr(sh,(x+offset[0],y+offset[1],x2+offset[0],y2+offset[1]),(0,0,0,opacity),radius);return composite(im,sh.filter(ImageFilter.GaussianBlur(blur)))
def photograph(name,u,zoom=.06,dx=0,dy=0):
 im=plate(name);z=1+zoom*max(0,min(1,u));ww=W/z;hh=H/z;cx=W/2+dx*u;cy=H/2+dy*u
 return im.transform((W,H),Image.Transform.EXTENT,(cx-ww/2,cy-hh/2,cx+ww/2,cy+hh/2),Image.Resampling.BICUBIC).convert('RGBA')
# Optical masks are static, cached, and composited separately from the photographic plates.
yy,xx=np.mgrid[0:H,0:W];edge=((xx-W*.5)/(W*.76))**2+((yy-H*.5)/(H*.85))**2
vignette=Image.new('RGBA',(W,H),(0,6,15));vignette.putalpha(Image.fromarray(np.uint8(np.clip(edge*.39,0,.58)*255)))
leftmask=Image.new('RGBA',(W,H),(4,13,23));leftmask.putalpha(Image.fromarray(np.uint8((.10+.48*(1-xx/W)**1.4)*255)))
@lru_cache(1)
def studio():
 radial=np.exp(-(((xx-1060)/850)**2+((yy-510)/460)**2));arr=np.zeros((H,W,4),np.uint8)
 for ch,(lo,hi) in enumerate(zip((3,9,16),(15,34,49))):arr[:,:,ch]=lo+radial*(hi-lo)
 arr[:,:,3]=255;return Image.fromarray(arr)
def flare(im,x,y,strength=1,width=400):
 l=layer();d=ImageDraw.Draw(l)
 for j in range(6,0,-1):
  d.ellipse((x-width,y-j*2,x+width,y+j*2),fill=(255,185,88,int(3*strength)))
 d.line((x-width*.45,y,x+width*.45,y),fill=(255,204,139,int(35*strength)),width=1)
 circle(l,x,y,5,(255,223,175,int(110*strength)));return composite(im,l.filter(ImageFilter.GaussianBlur(2)))
def logo(im,x,y,scale=1,alpha=1):
 l=layer();d=ImageDraw.Draw(l);d.rounded_rectangle((x,y,x+30*scale,y+30*scale),radius=9*scale,fill=AMBER)
 points=[(15,8),(21,22),(17.16,22),(15,16.68),(12.84,22),(9,22)]
 d.polygon([(x+a*scale,y+b*scale) for a,b in points],fill=NAVY)
 xpos=x+40*scale
 for ch in 'AtlasIQ':
  text(l,xpos,y+.8*scale,ch,int(20*scale),AMBER if ch in 'IQ' else WHITE,True)
  xpos+=d.textlength(ch,font=font(int(20*scale),True))-.4*scale
 return composite(im,l,alpha)
def header(im,label='CORRIDOR LIFELINE',alpha=1):
 l=layer();text(l,150,70,'ATLASIQ',22,AMBER,True);text(l,275,70,'/  '+label,20,WHITE,opacity=.70);return composite(im,l,alpha)
def headline(im,s,t,x=960,y=140,size=78,centre=True):
 p=out(t/.9);l=layer()
 for j,ln in enumerate(s.split('\n')):
  q=out((t-j*.15)/.9);text(l,x,y+j*(size+5)+(1-q)*30,ln,size,WHITE,True,'ma' if centre else 'la',q)
 return composite(im,l)
def concept(im):
 l=layer();circle(l,847,980,3,(*AMBER,220));text(l,865,963,'Concept preview',21,SLATE);return composite(im,l)
def icon(im,x,y,kind):
 if kind=='weather':
  circle(im,x-9,y,10,None,(*AMBER,255),2);line(im,[(x-15,y+12),(x+19,y+12),(x+22,y+4),(x+15,y-5),(x+6,y-4)],AMBER,2)
 elif kind=='rain':
  for j in [-12,0,12]:line(im,[(x+j,y-11),(x+j-6,y+11)],AMBER,2)
 elif kind=='rail':
  rr(im,(x-13,y-17,x+13,y+13),None,5,(*AMBER,255),2);line(im,[(x-9,y+13),(x-16,y+23)],AMBER,2);line(im,[(x+9,y+13),(x+16,y+23)],AMBER,2)
  line(im,[(x-8,y-4),(x+8,y-4)],AMBER,2)
 else:
  line(im,[(x-12,y),(x-2,y+10),(x+17,y-12)],TEAL,3)
def project_surface(panel,x,y,width,height,yaw=0,tilt=0):
 """Perspective warp a independently editable, rectangular interface surface."""
 sw,sh=panel.size;src=np.float32([[0,0],[sw,0],[sw,sh],[0,sh]])
 dst=np.float32([[x+yaw,y+tilt],[x+width-yaw,y],[x+width,y+height],[x,y+height-tilt]])
 m=cv2.getPerspectiveTransform(src,dst);arr=cv2.warpPerspective(np.array(panel),m,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
 return Image.fromarray(arr)
def shot_connection(t,hidden):
 u=t/4.8;im=photograph('road-clean.png',u,.05,-18,-10) if 'photographic-plates' not in hidden else studio().copy()
 if 'vehicle' not in hidden:
  # Road train advances in the perspective of the highway; background has its own camera move.
  q=out(u*.68);tw=int(395+110*q);tr=truck();th=int(tw*tr.height/tr.width);tx=int(1130-110*q);ty=int(480+45*q)
  sh=layer();ImageDraw.Draw(sh).ellipse((tx+10,ty+th-30,tx+tw-5,ty+th+12),fill=(0,0,0,110));im=composite(im,sh.filter(ImageFilter.GaussianBlur(11)))
  tr=tr.resize((tw,th),Image.Resampling.LANCZOS);l=layer();l.alpha_composite(tr,(tx,ty));im=composite(im,l)
  im=flare(im,tx+tw*.22,ty+th*.66,.50,140)
 im=composite(im,leftmask);im=composite(im,vignette)
 if 'typography' not in hidden:
  im=header(im,'BEFORE THE DISRUPTION',out(t/.5));im=headline(im,CFG['scenes'][0]['headline'],t-.3,x=190,y=258,size=105,centre=False)
  l=layer();text(l,196,865,'NULLARBOR, AUSTRALIA',22,WHITE,opacity=out((t-1.1)/.8)*.75);im=composite(im,l)
 return im
def shot_storm(t,hidden):
 u=(t-4.8)/4.2;im=photograph('freight-storm.png',u,.065,20,10) if 'photographic-plates' not in hidden else studio().copy()
 im=composite(im,leftmask,.8);im=composite(im,vignette)
 if 'atmosphere-map' not in hidden:
  l=layer();d=ImageDraw.Draw(l)
  # Rain is a moving atmosphere layer, not baked into the photographic plate.
  for j in range(85):
   x=(j*131.37+u*90)%W;y=(j*59.83+u*540)%H
   if y<780:d.line((x,y,x-12,y+35),fill=(173,190,207,15+int(15*u)),width=1)
  a=out((u-.25)*2)*.75;points=[(240,965),(730,755),(1115,585),(1465,444)]
  for i in range(3):line(l,points[i:i+2],RED if i==1 else AMBER,3,int(180*a))
  im=composite(im,l)
 if 'typography' not in hidden:
  im=header(im);im=headline(im,CFG['scenes'][1]['headline'],t-4.8,x=190,y=230,size=100,centre=False)
 return im
GEO=json.loads((A/'countries.geojson').read_text());AU=next(f['geometry'] for f in GEO['features'] if f['properties']['ADMIN']=='Australia');RINGS=[p[0] for p in AU['coordinates']]
def mappoint(lon,lat,t,dy=0):
 # A schematic continent set on a shallow dimensional plane.
 zoom=1+.06*out((t-9)/5.5);x=(lon-134)*28*zoom;z=(-lat-28)*25*zoom
 return (960+x+z*.32,685+z*.49+dy)
def map_layer(t):
 im=layer();d=ImageDraw.Draw(im)
 for depth in range(13,0,-3):
  for ring in RINGS:d.polygon([mappoint(*p,t,depth) for p in ring],fill=(9,21,31,255))
 for ring in RINGS:
  pts=[mappoint(*p,t) for p in ring];d.polygon(pts,fill=(24,43,55,255));line(im,pts+[pts[0]],(69,88,101),1,220)
 rail=[(121.47,-30.75),(124,-30.9),(128,-30.8),(131.5,-30.7),(133.7,-32.1),(137.8,-32.5)]
 road=[(121.47,-30.75),(121.8,-32.2),(126.3,-32.3),(130.6,-31.5),(133.7,-32.1),(137.8,-32.5)]
 for route in [road,rail]:
  pts=[mappoint(*p,t) for p in route];line(im,pts,(92,76,48),9,80);line(im,pts,AMBER,3,255)
  for j in range(5):
   q=(t*.17+j*.19)%1;i=min(4,int(q*5));p=q*5-i;x=lerp(pts[i][0],pts[i+1][0],p);y=lerp(pts[i][1],pts[i+1][1],p);circle(im,x,y,3,(*WHITE,245))
 return im

def shot_signals(t,hidden):
 u=t-9;im=studio().copy()
 if 'atmosphere-map' not in hidden:
  im=composite(im,map_layer(t),out(u/.75))
 if 'interface' not in hidden:
  l=layer()
  for j,(name,kind) in enumerate([('Weather','weather'),('Rainfall','rain'),('Rail status','rail')]):
   q=out((u-j*.23)/1);x=500+j*320;y=345+45*(1-q);w=280;h=135
   line(l,[(x+w/2,y+h),(960,606)],(72,92,105),2,int(180*q))
   for k in range(3):
    r=(u*.55+k/3)%1;xx=lerp(x+w/2,960,r);yy=lerp(y+h,606,r);circle(l,xx,yy,2,(*AMBER,int(190*q)))
   rr(l,(x,y,x+w,y+h),(22,40,55,int(245*q)),19,(86,107,120,int(120*q)),1)
   icon(l,x+38,y+39,kind);text(l,x+73,y+18,name,29,WHITE,True,opacity=q)
   pts=[(x+24+k*17,y+101+8*math.sin(k*.9+u*1.3+j)) for k in range(14)];line(l,pts,AMBER,2,int(230*q))
  # Agent node: a materially lit surface; source branding geometry remains unchanged.
  circle(l,960,606,61,(17,33,45,255),(219,156,64,200),2);circle(l,960,606,70+5*math.sin(u*2),None,(111,87,53,90),1)
  text(l,960,585,'AtlasIQ',23,WHITE,True,'ma')
  if u>2.3:
   q=out((u-2.3)/.7);x=655;y=838+20*(1-q)
   rr(l,(x,y,x+610,y+84),(26,37,46,245),18,(154,111,62,190),1);circle(l,x+38,y+41,5,(*AMBER,255));text(l,x+67,y+18,'Corridor risk: Elevated',33,WHITE,True)
  im=composite(im,l)
 if 'typography' not in hidden:im=header(im);im=headline(im,CFG['scenes'][2]['headline'],u,x=960,y=150,size=86);im=concept(im)
 return im

def notification(t):
 p=Image.new('RGBA',(740,420));d=ImageDraw.Draw(p)
 d.rounded_rectangle((0,0,739,419),radius=30,fill=(17,32,46,247),outline=(114,133,148,220),width=2)
 # Two quiet edge reflections distinguish material from a flat card.
 d.line((34,2,690,2),fill=(194,209,216,100),width=2);d.line((2,35,2,345),fill=(185,203,216,80),width=2)
 text(p,42,37,'ATLASIQ CORRIDOR ALERT',24,AMBER,True);d.line((42,96,695,96),fill=(65,81,96,200),width=1)
 text(p,42,130,'Elevated disruption risk.',40,WHITE,True);text(p,42,192,'Review shipment plans.',36,WHITE)
 rr(p,(42,287,697,373),(32,48,61,255),14,(77,97,112,140),1);text(p,69,306,'Review the risk',27,WHITE,True);text(p,647,301,'→',35,AMBER,True)
 return p

def shot_response(t,hidden):
 u=t-14.5;im=photograph('operations.png',u/5.5,.055,-10,0) if 'photographic-plates' not in hidden else studio().copy()
 dim=Image.new('RGBA',(W,H),(4,11,20,115));im=composite(im,dim);im=composite(im,vignette)
 if 'interface' not in hidden:
  q=out(u/.9);x=lerp(655,585,q);y=lerp(838,330,q);w=lerp(610,750,q);h=lerp(84,425,q)
  im=shadow(im,(x,y,x+w,y+h),30,130,blur=35)
  im=composite(im,project_surface(notification(t),x,y,w,h,22*(1-q)+8,12*(1-q)+4))
  l=layer();progress=ease((u-1.5)/2);y=867
  text(l,485,805,'SHIPMENT PLAN',18,WHITE,True,opacity=.68)
  line(l,[(485,y),(1410,y)],(100,112,123),2,150)
  text(l,490,899,'Review',20,SLATE);text(l,910,899,'Prepare',20,SLATE);text(l,1322,899,'Respond',20,SLATE)
  for j,xc in enumerate([530,950,1380]):circle(l,xc,y,5,(*WHITE,200))
  centre=lerp(675,1045,progress);rr(l,(centre-72,y-22,centre+72,y+22),(*AMBER,255),22);text(l,centre,y-14,'Plan ahead',21,NAVY,True,'ma')
  im=composite(im,l)
 if 'typography' not in hidden:im=header(im);im=headline(im,CFG['scenes'][3]['headline'],u,x=960,y=150,size=83);im=concept(im)
 return im

def document(t):
 u=t-20;p=Image.new('RGBA',(650,620));d=ImageDraw.Draw(p)
 q=out(u/.9);bg=colour((17,32,46),(234,238,241),q);ink=colour(WHITE,(26,42,57),q);sub=colour(SLATE,(88,104,117),q)
 d.rounded_rectangle((0,0,649,619),radius=22,fill=(*bg,255),outline=(200,211,220,255),width=1)
 text(p,40,27,'ATLASIQ / PREPARATION',18,(137,91,30),True)
 text(p,40,71,'Emergency permit draft',37,ink,True);text(p,40,128,'Sample document · Human review required',20,sub)
 for j,(k,v) in enumerate([('Operator','Sample operator'),('Vehicle','Vehicle 01'),('Shipment','Sample shipment'),('Requested movement','For review')]):
  y=198+j*64;text(p,40,y,k,22,sub)
  d.line((40,y+46,610,y+46),fill=(186,198,206,255),width=1)
  a=out((u-.7-j*.31)/.5)
  if a>0:text(p,298,y,v,24,ink,False,opacity=a)
 if u>2:
  a=out((u-2)/.6);rr(p,(40,493,610,572),(215,234,229,255),13,(159,193,182,255),1)
  text(p,325,513,'Ready for review',31,(33,99,81),True,'ma',a)
 return p

def shot_documents(t,hidden):
 u=t-20;im=studio().copy()
 if 'photographic-plates' not in hidden:
  op=photograph('operations.png',.7,.04);im=Image.blend(im,op,.11)
 if 'interface' not in hidden:
  q=out(u/1);x=lerp(585,606,q);y=lerp(330,290,q);w=lerp(750,650,q);h=lerp(425,620,q)
  im=shadow(im,(x,y,x+w,y+h),25,140,blur=32)
  im=composite(im,project_surface(document(t),x,y,w,h,lerp(8,11,q),lerp(4,7,q)))
  a=out((u-1.35)/.7)
  if a:
   l=layer();xx=1220+24*(1-a);yy=580
   rr(l,(xx,yy,xx+300,yy+212),(24,43,57,250),21,(96,118,133,150),1)
   text(l,xx+29,yy+25,'Risk summary',30,WHITE,True)
   for j in range(3):line(l,[(xx+29,yy+94+j*27),(xx+251-j*29,yy+94+j*27)],SLATE,3,170)
   im=composite(im,l,a)
  l=layer();text(l,960,933,'Review before submission',23,SLATE,anchor='ma');im=composite(im,l)
 if 'typography' not in hidden:im=header(im);im=headline(im,CFG['scenes'][4]['headline'],u,x=960,y=145,size=84);im=concept(im)
 return im

def shot_end(t,hidden):
 u=t-25.5;t=min(t,28);u=min(u,2.5);im=studio().copy()
 if 'atmosphere-map' not in hidden:
  l=layer();p=out(u/1.2);length=lerp(1180,350,p);y=lerp(670,365,p);line(l,[(960-length/2,y),(960+length/2,y)],AMBER,2,230)
  for x in [960-length/2,960+length/2]:circle(l,x,y,3,(*AMBER,255))
  im=composite(im,l);im=flare(im,lerp(380,1135,p),y,.3*(1-p),350)
 if 'logo' not in hidden:im=logo(im,709,441,4.6,out((u-.35)/1))
 if 'typography' not in hidden:
  l=layer();a=out((u-.75)/1)
  text(l,960,620,'Corridor Lifeline Agent',43,WHITE,True,'ma',a)
  for j,ln in enumerate(CFG['scenes'][5]['headline'].split('\n')):text(l,960,712+j*47,ln,34,WHITE,False,'ma',a)
  text(l,960,859,'atlasiqco.com',32,AMBER,False,'ma',a);text(l,960,941,'In development',22,SLATE,False,'ma',a)
  im=composite(im,l)
 return im
SHOTS=[shot_connection,shot_storm,shot_signals,shot_response,shot_documents,shot_end];STARTS=[0,4.8,9,14.5,20,25.5];ENDS=[4.8,9,14.5,20,25.5,30]
CAPS=[(.55,4.45,'Across the Nullarbor, every shipment\ndepends on a connection.'),(5.15,7.22,'But conditions can change.'),(8.1,10.62,"AtlasIQ’s Corridor Lifeline concept"),(10.62,14.37,'brings weather, rainfall and rail signals into focus.'),(15.1,18.35,'So your team can review the risk,\nplan its response,'),(18.35,21.22,'and prepare emergency paperwork drafts.'),(22.8,24.21,'Clear signals.'),(24.4,25.9,'Prepared people.'),(26.2,27.73,'AtlasIQ.')]
def frame(t,caption=False,hidden=()):
 idx=max(i for i,s in enumerate(STARTS) if t>=s);im=SHOTS[idx](t,hidden)
 # Short cinematic dissolves connect photographic scenes and their shared amber motif.
 if idx>0 and t<STARTS[idx]+.5:
  p=ease((t-STARTS[idx])/.5);prev=SHOTS[idx-1](STARTS[idx]-.001,hidden)
  im=Image.blend(prev,im,p)
 if t<.55:im=Image.blend(Image.new('RGBA',(W,H),(*NAVY,255)),im,ease(t/.55))
 if caption and 'captions' not in hidden:
  for a,b,s in CAPS:
   if a<=t<b:
    l=layer();n=len(s.split('\n'));rr(l,(380,1018-(n-1)*32,1540,1074),(3,10,17,225),11)
    for j,ln in enumerate(s.split('\n')):text(l,960,1024-(n-1)*32+j*32,ln,27,WHITE,False,'ma')
    im=composite(im,l)
 return im.convert('RGB')

def make_audio():
 sr=48000;n=sr*30
 raw=np.frombuffer(subprocess.check_output([FF,'-v','error','-i',str(R/'audio/narration-neural.mp3'),'-f','f32le','-ac','1','-ar',str(sr),'-']),'<f4').copy()
 voice=np.zeros(n);segments=[(.0,3.904,.55),(3.904,5.922,5.15),(5.922,12.185,8.1),(12.185,18.305,15.1),(18.305,19.711,22.8),(19.711,21.208,24.4),(21.208,22.80,26.2)]
 for a,b,at in segments:
  clip=raw[int(a*sr):int(b*sr)].copy();fade=min(150,len(clip)//3);clip[:fade]*=np.linspace(0,1,fade);clip[-fade:]*=np.linspace(1,0,fade)
  start=int(at*sr);voice[start:start+len(clip)]+=clip
 # Neutral speech EQ and soft normalisation, no tempo alteration.
 from scipy.signal import butter,sosfilt
 voice=sosfilt(butter(2,80,fs=sr,btype='highpass',output='sos'),voice)
 voice*=.71/max(.01,np.max(np.abs(voice)))
 ts=np.arange(n)/sr;music=np.zeros((n,2));fx=np.zeros((n,2));rng=np.random.default_rng(42)
 bpm=102;beat=60/bpm
 # Bespoke chord sequence: D minor(add9), B-flatmaj7, F(add9), C sus2.
 chords=[[146.83,174.61,220,329.63],[116.54,146.83,174.61,220],[130.81,174.61,220,261.63],[130.81,146.83,196,261.63]]
 for k,start in enumerate([0,7.5,15,22.5]):
  dur=min(8.4,30-start);length=int(dur*sr);z=np.arange(length)/sr;env=np.minimum(1,z/2)*np.minimum(1,(dur-z)/1.8)
  for j,freq in enumerate(chords[k]):
   for ch,detune in enumerate([-.13,.13]):
    tone=np.sin(2*np.pi*(freq+detune)*z)+.22*np.sin(2*np.pi*(freq*2+detune)*z)
    music[int(start*sr):int(start*sr)+length,ch]+=.010*env*tone
 for k,at in enumerate(np.arange(1.2,28.2,beat)):
  st=int(at*sr);ln=min(int(.48*sr),n-st);z=np.arange(ln)/sr
  pulse=.035*np.sin(2*np.pi*(65.4+35*np.exp(-z*20))*z)*np.exp(-z*12)
  music[st:st+ln,:]+=pulse[:,None]
  if k%2==0:
   f=chords[min(3,int(at/7.5))][k%4]*2;note=.009*np.sin(2*np.pi*f*z)*np.exp(-z*9)
   music[st:st+ln,k%2]+=note
 # Quiet freight ambience and atmosphere swell, all original procedural sound.
 noise=rng.normal(0,1,n);low=sosfilt(butter(2,180,fs=sr,output='sos'),noise)
 amb=low*.032*np.exp(-((ts-3.5)/3)**2);storm=low*.043*np.exp(-((ts-6.8)/1.9)**2)
 fx+=np.stack([amb+storm,amb+storm],axis=1)
 def tone(at,f,amp=.025,duration=.7,pan=.5):
  st=int(at*sr);ln=min(int(duration*sr),n-st);z=np.arange(ln)/sr;v=amp*(np.sin(2*np.pi*f*z)+.2*np.sin(2*np.pi*2*f*z))*np.exp(-z*6)*np.minimum(1,z/.012)
  fx[st:st+ln,0]+=v*math.sqrt(1-pan);fx[st:st+ln,1]+=v*math.sqrt(pan)
 for j,at in enumerate([9.3,9.6,9.9]):tone(at,720+j*90,.019,.35,.2+j*.3)
 tone(15.25,659.25,.035);tone(15.42,880,.02)
 for j in range(4):tone(20.75+j*.31,700+j*90,.012,.22,.35+j*.1)
 for j,f in enumerate([146.83,220,293.66,440]):tone(26.6+j*.08,f,.028,2.8,.3+j*.13)
 # Speech centred; music ducked using a smooth envelope.
 env=np.convolve(np.abs(voice)[::480],np.ones(14)/14,mode='same');env=np.interp(np.arange(n),np.arange(len(env))*480,env);duck=1-.35*np.minimum(1,env/.055)
 music*=duck[:,None];fade=np.minimum(1,ts/1.2)*np.minimum(1,(30-ts)/1.2);music*=fade[:,None];fx*=fade[:,None]
 stereo_voice=np.repeat(voice[:,None],2,axis=1);mix=stereo_voice+music+fx
 def save(name,data):
  with wave.open(str(R/'audio'/name),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())
 save('voiceover.wav',stereo_voice);save('music.wav',music);save('effects.wav',fx);save('mix.wav',mix)
 (R/'audio/audio-report.json').write_text(json.dumps({'voice':'en-AU-WilliamNeural','synthetic':True,'time_stretch':False,'peak':float(np.max(np.abs(mix))),'voice_end':27.792,'bpm':102,'segments':segments},indent=2))
 print('Audio peak:',round(float(np.max(np.abs(mix))),3),flush=True)

def srt():
 def stamp(t):
  ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (E/'AtlasIQ-captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for i,(a,b,s) in enumerate(CAPS))+'\n')

def render():
 make_audio();srt()
 paths=[E/'AtlasIQ-30s-silent.mp4',E/'caption-picture.mp4'];procs=[]
 for path in paths:
  cmd=[FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
  procs.append(subprocess.Popen(cmd,stdin=subprocess.PIPE))
 stills={84:'01-connection',205:'02-conditions',374:'03-signals',520:'04-response',705:'05-preparation',870:'06-brand'}
 for i in range(N):
  t=i/FPS;im=frame(t);procs[0].stdin.write(im.tobytes());cap=im.copy().convert('RGBA')
  for a,b,s in CAPS:
   if a<=t<b:
    l=layer();n=len(s.split('\n'));rr(l,(380,1018-(n-1)*32,1540,1074),(3,10,17,225),11)
    for j,ln in enumerate(s.split('\n')):text(l,960,1024-(n-1)*32+j*32,ln,27,WHITE,False,'ma')
    cap=composite(cap,l)
  procs[1].stdin.write(cap.convert('RGB').tobytes())
  if i in stills:im.save(E/(stills[i]+'.png'))
  if i%60==0:print(f'Rendered {i}/{N} frames',flush=True)
 for proc in procs:proc.stdin.close();assert proc.wait()==0
 for picture,name in [('AtlasIQ-30s-silent.mp4','AtlasIQ-30s-voiceover.mp4'),('caption-picture.mp4','AtlasIQ-30s-captioned.mp4')]:
  subprocess.run([FF,'-v','error','-y','-i',str(E/picture),'-i',str(R/'audio/mix.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','256k','-t','30','-movflags','+faststart',str(E/name)],check=True)
 (E/'caption-picture.mp4').unlink()
if __name__=='__main__':
 if '--stills' in sys.argv:
  for t,name in [(2.8,'01-connection'),(6.8,'02-conditions'),(12.47,'03-signals'),(17.33,'04-response'),(23.5,'05-preparation'),(29,'06-brand')]:frame(t).save(E/(name+'.png'))
 else:render()
