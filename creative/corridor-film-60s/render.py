"""AtlasIQ 60-second film. Editable scene functions, physical-image layers and exact typography."""
from pathlib import Path
from functools import lru_cache
import json,math,subprocess,wave,sys,hashlib,xml.etree.ElementTree as ET
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
cv2.setNumThreads(1)
R=Path(__file__).resolve().parent;A=R/'assets';E=R/'exports';E.mkdir(exist_ok=True)
CFG=json.loads((R/'film.json').read_text());W,H=1920,1080;FPS=30;N=1800;FF=imageio_ffmpeg.get_ffmpeg_exe()
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
STARTS=[0,6,12,18,24,30,37,43,50,56]
FILES=['dispatcher-before.png','freight-dawn.png','aerial.png','freight-storm.png','dispatcher-alert.png','laptop.png','decision.png','paper.png','rest.png',None]
def warp(panel,points):
 sw,sh=panel.size;m=cv2.getPerspectiveTransform(np.float32([[0,0],[sw,0],[sw,sh],[0,sh]]),np.float32(np.array(points)*[W/1672,H/941]))
 return Image.fromarray(cv2.warpPerspective(np.array(panel),m,(W,H),flags=cv2.INTER_LINEAR))
def screen(t):
 p=Image.new('RGBA',(1000,500),(*NAVY,255));d=ImageDraw.Draw(p)
 text(p,40,26,'AtlasIQ',30,WHITE,True);text(p,958,33,'CONCEPT PREVIEW',17,SLATE,False,'ra')
 d.line((40,80,960,80),fill=(57,76,94,255),width=1)
 text(p,40,104,'Corridor Lifeline',39,WHITE,True)
 text(p,40,163,'Nullarbor corridor · Illustrative signals',22,SLATE)
 labels=['Weather warning','Rainfall trend','Rail status']
 for j,label in enumerate(labels):
  x=40+j*310;q=out((t-24-j*.35)/.8)
  rr(p,(x,219,x+290,317),(20,40,56,255),10)
  text(p,x+20,235,label,23,WHITE,True,opacity=q)
  text(p,x+20,276,['Review warning','Review observations','Verify latest update'][j],18,AMBER,opacity=q)
 rr(p,(40,345,960,452),(42,42,38,255),12,(111,91,57,255))
 text(p,62,359,'Elevated disruption risk',32,AMBER,True)
 text(p,62,409,'Review shipment plans. Human assessment required.',21,WHITE)
 return p

def paper(t):
 p=Image.new('RGBA',(600,800));ink=(31,44,56);sub=(80,92,104)
 text(p,45,42,'ATLASIQ / CORRIDOR LIFELINE',19,(139,90,31),True)
 text(p,45,98,'Emergency',39,ink,True);text(p,45,145,'permit draft',39,ink,True)
 text(p,45,209,'SAMPLE · HUMAN REVIEW REQUIRED',16,(139,90,31),True)
 ImageDraw.Draw(p).line((45,250,555,250),fill=(*sub,120),width=1)
 for y,title,body in [(280,'Shipment plan','Review route, timing and alternatives.'),(382,'Risk summary','Weather · Rainfall · Rail status'),(484,'Supporting information','Confirm current source information.')]:
  text(p,45,y,title,25,ink,True);text(p,45,y+42,body,18,sub)
 text(p,45,635,'Prepared for review',27,ink,True)
 text(p,45,681,'Draft only. No permit approval implied.',18,sub)
 text(p,45,736,'Illustrative concept document',15,sub)
 return p

def shot(idx,t,hidden=()):
 end=STARTS[idx+1] if idx<9 else 60;u=(t-STARTS[idx])/(end-STARTS[idx])
 if idx==9:
  im=studio().copy();a=out((t-56)/1.3)
  if 'logo' not in hidden:im=logo(im,709,315,4.6,a)
  if 'typography' not in hidden:
   l=layer();text(l,960,510,'Corridor Lifeline Agent',44,WHITE,True,'ma',a)
   for j,ln in enumerate(CFG['scenes'][9]['headline'].split('\n')):text(l,960,625+j*50,ln,37,WHITE,False,'ma',a)
   text(l,960,814,'atlasiqco.com',32,AMBER,False,'ma',a);text(l,960,902,'In development',21,SLATE,False,'ma',a);im=composite(im,l)
  return im
 im=plate(FILES[idx]).convert('RGBA') if 'photographic-plates' not in hidden else studio().copy()
 if 'interface' not in hidden:
  if idx==4:im=composite(im,warp(screen(t),[(1125,453),(1414,479),(1348,730),(1050,676)]),.83)
  if idx==5:im=composite(im,warp(screen(t),[(494,225),(1305,225),(1321,636),(466,636)]),.9)
  if idx==7:im=composite(im,warp(paper(t),[(475,129),(1028,65),(1201,789),(562,870)]),.9)
 # A slow optical push; typography tracks physical screen/paper because it is composited first.
 z=1+.045*u;ww=W/z;hh=H/z;cx=W/2+(-12 if idx in [0,4,6] else 10)*u;cy=H/2
 im=im.transform((W,H),Image.Transform.EXTENT,(cx-ww/2,cy-hh/2,cx+ww/2,cy+hh/2),Image.Resampling.BICUBIC)
 im=composite(im,vignette,.5)
 if idx==3 and 'atmosphere-map' not in hidden:
  l=layer();d=ImageDraw.Draw(l)
  for j in range(100):
   x=(j*173.73+t*15)%W;y=(j*79.91+t*190)%H;d.line((x,y,x-6,y+20),fill=(191,205,215,23),width=1)
  im=composite(im,l)
 if 'typography' not in hidden:
  l=layer();h=CFG['scenes'][idx]['headline'];a=out((t-STARTS[idx]-.6)/1)
  if h:
   # Restrained lower-third titles, away from the face and laptop.
   for j,ln in enumerate(h.split('\n')):text(l,132,752+j*77,ln,68,WHITE,True,opacity=a)
  if idx==2:text(l,135,895,'ACROSS THE NULLARBOR',21,WHITE,True,opacity=.8*a)
  if 4<=idx<=7:text(l,135,980,'Illustrative concept · Human review required',20,WHITE,opacity=.8)
  im=composite(im,l)
 # A shallow anamorphic presentation within a full-HD deliverable.
 d=ImageDraw.Draw(im);d.rectangle((0,0,W,44),fill=(3,8,13,255));d.rectangle((0,1036,W,H),fill=(3,8,13,255))
 return im

SEGMENTS=[(0,3.619,.5),(3.619,7.647,6.15),(7.647,10.313,12.2),(10.313,12.536,18.35),(12.536,17.438,21.0),(17.438,21.063,26.15),(21.063,25.786,30.25),(25.786,31.397,36.6),(31.397,37.925,42.4),(37.925,42.897,49.0),(42.897,48.55,54.15)]
CAPS=[]
import re
blocks=(R/'audio/narration-neural.srt').read_text().strip().split('\n\n')
def seconds(s):
 h,m,s=s.replace(',','.').split(':');return float(h)*3600+float(m)*60+float(s)
for block in blocks:
 lines=block.splitlines();a,b=[seconds(x.strip()) for x in lines[1].split('-->')];words=' '.join(lines[2:])
 for x,y,at in SEGMENTS:
  if x-.001<=a<y-.001:
   import textwrap
   CAPS.append((at+a-x,at+min(b,y)-x,'\n'.join(textwrap.wrap(words,66))));break

def caption(im,t):
 im=im.convert('RGBA')
 for a,b,s in CAPS:
  if a<=t<b:
   l=layer();rows=s.split('\n');y=1010-32*(len(rows)-1);rr(l,(210,y-5,1710,1074),(3,10,17,237),9)
   for j,ln in enumerate(rows):text(l,960,y+j*32,ln,27,WHITE,False,'ma')
   im=composite(im,l)
 return im.convert('RGB')
def frame(t,captioned=False,hidden=()):
 t=min(59.999,max(0,t));idx=max(i for i,s in enumerate(STARTS) if t>=s);im=shot(idx,t,hidden)
 if idx in [4,5,7,9] and t<STARTS[idx]+.4:im=Image.blend(shot(idx-1,STARTS[idx]-.001,hidden),im,ease((t-STARTS[idx])/.4))
 if t<.6:im=Image.blend(Image.new('RGBA',(W,H),(*NAVY,255)),im,ease(t/.6))
 return caption(im,t) if captioned else im.convert('RGB')

def make_audio():
 from scipy.signal import butter,sosfilt
 sr=48000;n=sr*60;raw=np.frombuffer(subprocess.check_output([FF,'-v','error','-i',str(R/'audio/narration-neural.mp3'),'-f','f32le','-ac','1','-ar',str(sr),'-']),'<f4').copy();voice=np.zeros(n)
 for a,b,at in SEGMENTS:
  clip=raw[int(a*sr):int(b*sr)].copy();ln=min(len(clip),n-int(at*sr));clip=clip[:ln];clip[:120]*=np.linspace(0,1,120);clip[-120:]*=np.linspace(1,0,120);voice[int(at*sr):int(at*sr)+ln]+=clip
 voice=sosfilt(butter(2,80,fs=sr,btype='highpass',output='sos'),voice);voice*=.69/max(.01,np.max(np.abs(voice)))
 ts=np.arange(n)/sr;music=np.zeros((n,2));fx=np.zeros((n,2));rng=np.random.default_rng(52)
 chords=[[146.83,220,329.63],[130.81,196,293.66],[116.54,174.61,261.63],[146.83,220,349.23],[130.81,196,293.66],[174.61,220,329.63]]
 for k,start in enumerate([0,10,20,30,40,50]):
  dur=min(12,60-start);z=np.arange(int(dur*sr))/sr;env=np.minimum(1,z/2.5)*np.minimum(1,(dur-z)/2)
  for j,f in enumerate(chords[k]):
   for ch,d in enumerate([-.10,.10]):music[int(start*sr):int(start*sr)+len(z),ch]+=.010*env*(np.sin(2*np.pi*(f+d)*z)+.13*np.sin(2*np.pi*(f*2+d)*z))
 for k,at in enumerate(np.arange(1,58,1.5)):
  ln=min(int(3*sr),n-int(at*sr));z=np.arange(ln)/sr;f=chords[min(5,int(at/10))][k%3]*2;v=.026*(np.sin(2*np.pi*f*z)+.2*np.sin(2*np.pi*f*2.003*z))*np.exp(-z*2.4)*np.minimum(1,z/.012)
  music[int(at*sr):int(at*sr)+ln,k%2]+=v;delay=int(.22*sr);ll=min(ln,n-int(at*sr)-delay);music[int(at*sr)+delay:int(at*sr)+delay+ll,1-k%2]+=v[:ll]*.25
 noise=rng.normal(0,1,n);low=sosfilt(butter(2,180,fs=sr,output='sos'),noise);rain=sosfilt(butter(2,[900,4500],fs=sr,btype='bandpass',output='sos'),noise)
 atmosphere=low*(.06*np.exp(-((ts-9)/4)**2)+.09*np.exp(-((ts-21)/4)**2))+.009*rain*np.exp(-((ts-22)/4)**2)
 fx+=atmosphere[:,None]
 for at,f in [(24.8,659.25),(25.02,880),(56.2,440)]:
  st=int(at*sr);z=np.arange(min(int(2*sr),n-st))/sr;v=.025*np.sin(2*np.pi*f*z)*np.exp(-z*5)*np.minimum(1,z/.01);fx[st:st+len(v),:]+=v[:,None]
 env=np.convolve(np.abs(voice)[::480],np.ones(20)/20,mode='same');env=np.interp(np.arange(n),np.arange(len(env))*480,env);music*=(1-.4*np.minimum(1,env/.05))[:,None]
 fade=np.minimum(1,ts/1.2)*np.minimum(1,(60-ts)/1.4);music*=fade[:,None];fx*=fade[:,None];v=np.repeat(voice[:,None],2,axis=1);mix=v+music+fx
 for name,data in [('voiceover',v),('music',music),('effects',fx),('mix',mix)]:
  with wave.open(str(R/'audio'/f'{name}.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())
 (R/'audio/audio-report.json').write_text(json.dumps({'synthetic_voice':'en-AU-WilliamNeural','time_stretch':False,'peak':float(np.max(np.abs(mix))),'segments':SEGMENTS},indent=2))
 print('Audio peak',np.max(np.abs(mix)),flush=True)
def render():
 make_audio()
 def stamp(t):
  ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (E/'AtlasIQ-captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for i,(a,b,s) in enumerate(CAPS))+'\n')
 paths=[E/'AtlasIQ-60s-silent.mp4',E/'caption-picture.mp4'];ps=[]
 for p in paths:ps.append(subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(p)],stdin=subprocess.PIPE))
 for i in range(N):
  t=i/FPS;im=frame(t);ps[0].stdin.write(im.tobytes());ps[1].stdin.write(caption(im,t).tobytes())
  if i%90==0:print(f'Rendered {i}/{N}',flush=True)
 for p in ps:p.stdin.close();assert p.wait()==0
 for picture,name in [('AtlasIQ-60s-silent.mp4','AtlasIQ-60s-voiceover.mp4'),('caption-picture.mp4','AtlasIQ-60s-captioned.mp4')]:subprocess.run([FF,'-v','error','-y','-i',str(E/picture),'-i',str(R/'audio/mix.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','256k','-t','60','-movflags','+faststart',str(E/name)],check=True)
 (E/'caption-picture.mp4').unlink()
if __name__=='__main__':
 if '--stills' in sys.argv:
  for t in [3,9,15,21,27,34,40,47,53,59]:frame(t).save(E/f'frame-{t:02}.jpg')
 else:render()
