from pathlib import Path
import json,base64,zipfile
R=Path(__file__).resolve().parent
frames=[p.read_text() for p in sorted((R/'frames').glob('*.svg'))]
font=base64.b64encode((R/'assets/SpaceGrotesk.ttf').read_bytes()).decode()
template='''<!doctype html><meta charset="utf-8"><title>AtlasIQ — editable motion project</title>
<style>@font-face{font-family:'Space Grotesk';src:url(data:font/ttf;base64,FONT)}*{box-sizing:border-box}body{margin:0;background:#071522;color:#eaf0f9;font:15px 'Space Grotesk',sans-serif}main{max-width:1300px;margin:auto;padding:25px}h1{font-size:23px}#stage{width:100%;aspect-ratio:16/9;background:#071522}svg{width:100%;height:100%}.bar{display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin:18px 0}button,input,select{font:inherit}button{background:#ffa028;border:0;border-radius:7px;padding:10px 18px;cursor:pointer}input[type=range]{flex:1;min-width:250px}input[type=text]{width:360px;padding:9px;background:#142b3b;color:white;border:1px solid #8193a5}details{background:#102737;padding:16px;border-radius:8px}.muted{color:#8193a5}a{color:#ffa028}</style>
<main><h1>AtlasIQ · Corridor Lifeline — editable motion project</h1><p class="muted">15.000 seconds · 1920 × 1080 · 30 fps · vector frames + independent audio stems</p>
<div id="stage"></div><div class="bar"><button id="play">Play</button><input id="time" type="range" min="0" max="449" value="0"><span id="clock">0.00 / 15.00</span><button id="save">Export current SVG</button></div>
<details open><summary>Layers</summary><div class="bar" id="layers"></div><p class="muted">Toggle independent map, interface, typography, logo and texture groups. Export any frame as an editable SVG. Edit render.py for motion, layout and global styles, then re-render the MP4s.</p></details>
<details><summary>Edit exact typography</summary><div class="bar"><select id="original"></select><input id="replacement" type="text" aria-label="Replacement text"><button id="apply">Apply to project</button></div><p class="muted">Text edits persist in this browser. Download an SVG to retain an edited frame; update render.py to retain edits in future renders.</p></details>
<div class="bar"><label><input id="voice" type="checkbox" checked> Australian synthetic voice</label><label><input id="music" type="checkbox" checked> Original music</label><label><input id="effects" type="checkbox" checked> Sound effects</label></div>
<p><a href="exports/AtlasIQ-voiceover.mp4">Voiceover MP4</a> · <a href="exports/AtlasIQ-captioned.mp4">Captioned MP4</a> · <a href="exports/AtlasIQ-silent.mp4">Silent MP4</a></p>
<p class="muted">Concept preview. Drafts require review. No operational prediction, accuracy claim or permit approval is depicted. Branding preserved from atlasiqco.com’s CSS logo design.</p></main>
<script>
const frames=FRAMES,stage=document.querySelector('#stage'),slider=document.querySelector('#time');
const names=['background-texture','map','interface','typography','logo'];let hidden=new Set(),edits=JSON.parse(localStorage.getItem('atlas-motion-edits')||'{}');let playing=false,start=0;
const audio=['voiceover','music','effects'].map(n=>new Audio('audio/'+n+'.wav'));
function draw(){const f=+slider.value;stage.innerHTML=frames[f];for(const name of hidden)stage.querySelectorAll('[id="'+name+'"]').forEach(el=>el.style.display='none');stage.querySelectorAll('text').forEach(el=>{if(edits[el.textContent]!==undefined)el.textContent=edits[el.textContent]});document.querySelector('#clock').textContent=(f/30).toFixed(2)+' / 15.00'}
for(const name of names){const label=document.createElement('label');label.innerHTML='<input type="checkbox" checked> '+name;label.querySelector('input').onchange=e=>{if(e.target.checked)hidden.delete(name);else hidden.add(name);draw()};document.querySelector('#layers').append(label)}
const textSet=new Set();for(const s of frames){const d=new DOMParser().parseFromString(s,'image/svg+xml');d.querySelectorAll('text').forEach(el=>textSet.add(el.textContent))}const sel=document.querySelector('#original');for(const s of textSet){const o=document.createElement('option');o.textContent=s;sel.append(o)}
document.querySelector('#apply').onclick=()=>{edits[sel.value]=document.querySelector('#replacement').value;localStorage.setItem('atlas-motion-edits',JSON.stringify(edits));draw()};
function stop(){playing=false;audio.forEach(a=>a.pause());document.querySelector('#play').textContent='Play'}
function tick(now){if(!playing)return;const f=Math.floor((now-start)*30/1000);if(f>=450){slider.value=449;draw();stop();return}slider.value=f;draw();requestAnimationFrame(tick)}
document.querySelector('#play').onclick=()=>{if(playing){stop();return}if(+slider.value>=449)slider.value=0;playing=true;start=performance.now()-(+slider.value/30)*1000;audio.forEach((a,i)=>{a.currentTime=+slider.value/30;a.muted=!document.querySelector('#'+['voice','music','effects'][i]).checked;a.play().catch(()=>{})});document.querySelector('#play').textContent='Pause';requestAnimationFrame(tick)};
slider.oninput=()=>{stop();draw()};['voice','music','effects'].forEach((n,i)=>document.querySelector('#'+n).onchange=e=>audio[i].muted=!e.target.checked);
document.querySelector('#save').onclick=()=>{const svg=stage.querySelector('svg').cloneNode(true),style=document.createElementNS('http://www.w3.org/2000/svg','style');style.textContent=document.querySelector('style').textContent.split('*{')[0];svg.prepend(style);const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([svg.outerHTML],{type:'image/svg+xml'}));a.download='AtlasIQ-frame-'+slider.value+'.svg';a.click();URL.revokeObjectURL(a.href)};draw();
</script>'''
(R/'project.html').write_text(template.replace('FONT',font).replace('FRAMES',json.dumps(frames)))
(R/'exports/captions.srt').write_text('''1
00:00:00,100 --> 00:00:02,800
When freight routes face disruption,
preparation matters.

2
00:00:03,030 --> 00:00:05,960
AtlasIQ’s Corridor Lifeline concept
connects risk signals,

3
00:00:06,130 --> 00:00:07,550
business alerts

4
00:00:09,030 --> 00:00:11,600
and emergency paperwork drafts—

5
00:00:11,670 --> 00:00:13,464
helping you prepare your response.
''')
with zipfile.ZipFile(R/'AtlasIQ-editable-project.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in R.rglob('*'):
  if p.is_file() and p.suffix!='.zip' and '__pycache__' not in str(p):z.write(p,p.relative_to(R))
print('Packaged',len(frames),'vector frames')
