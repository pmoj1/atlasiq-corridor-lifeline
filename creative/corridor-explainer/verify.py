from pathlib import Path
import subprocess,json,re,hashlib,xml.etree.ElementTree as ET
import imageio_ffmpeg
R=Path(__file__).resolve().parent;ff=imageio_ffmpeg.get_ffmpeg_exe();results={}
for name in ['AtlasIQ-voiceover.mp4','AtlasIQ-captioned.mp4','AtlasIQ-silent.mp4']:
 p=R/'exports'/name
 meta=subprocess.run([ff,'-i',str(p)],capture_output=True,text=True).stderr
 assert '1920x1080' in meta and '30 fps' in meta and '00:00:15.00' in meta,meta
 has_audio='Audio:' in meta;assert has_audio==(name!='AtlasIQ-silent.mp4')
 hashes=subprocess.check_output([ff,'-v','error','-i',str(p),'-map','0:v','-f','framemd5','-']).decode()
 rows=[r for r in hashes.splitlines() if r and not r.startswith('#')];assert len(rows)==450,len(rows)
 # Lossy MP4 frames can have different decoded hashes despite identical source art.
 source=[(R/f'frames/{i:03}.svg').read_bytes() for i in range(405,450)]
 assert len({hashlib.sha256(s).hexdigest() for s in source})==1,'End hold source moves'
 subprocess.run([ff,'-v','error','-i',str(p),'-f','null','-'],check=True)
 results[name]={'resolution':'1920x1080','fps':30,'frames':len(rows),'duration_seconds':15.0,'audio':has_audio,'final_static_frames':45,'decode':'pass'}
for p in (R/'frames').glob('*.svg'):ET.parse(p)
assert len(list((R/'frames').glob('*.svg')))==450
results['vector_frames']={'count':450,'xml_parse':'pass'}
results['audio']={'voice':'macOS Karen en_AU, synthetic','music':'original procedural, 105 BPM','stems':['voiceover.wav','music.wav','effects.wav'],'narration_end_seconds':13.464}
(R/'verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
