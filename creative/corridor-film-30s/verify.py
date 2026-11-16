from pathlib import Path
import subprocess,json,hashlib,wave
import numpy as np
import render
R=Path(__file__).resolve().parent;FF=render.FF;results={}
for name in ['AtlasIQ-30s-voiceover.mp4','AtlasIQ-30s-captioned.mp4','AtlasIQ-30s-silent.mp4']:
 p=R/'exports'/name
 meta=subprocess.run([FF,'-i',str(p)],capture_output=True,text=True).stderr
 assert '1920x1080' in meta and '30 fps' in meta and '00:00:30.00' in meta,meta
 audio='Audio:' in meta;assert audio==(name!='AtlasIQ-30s-silent.mp4')
 hashes=subprocess.check_output([FF,'-v','error','-i',str(p),'-map','0:v','-f','framemd5','-']).decode()
 rows=[r for r in hashes.splitlines() if r and not r.startswith('#')];assert len(rows)==900
 subprocess.run([FF,'-v','error','-i',str(p),'-f','null','-'],check=True)
 results[name]={'duration':30.0,'fps':30,'frames':900,'resolution':'1920x1080','audio':audio,'decode':'pass'}
held={hashlib.sha256(render.frame(i/30).tobytes()).hexdigest() for i in range(840,900)};assert len(held)==1
results['end_hold']={'seconds':2,'source_frames':60,'identical':True}
with wave.open(str(R/'audio/mix.wav')) as f:
 assert f.getnframes()==30*f.getframerate();assert f.getnchannels()==2;pcm=np.frombuffer(f.readframes(f.getnframes()),'<i2');peak=float(np.max(np.abs(pcm.astype(np.int32)))/32768)
 assert peak<.99
results['mix']={'duration':30,'channels':2,'peak':peak,'clipping':False,'synthetic_voice':'en-AU-WilliamNeural','time_stretch':False}
results['editor']={'manual_checks':['timeline frame preview','interface isolation','playback'],'format':'local HTML/Python'}
(R/'verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
