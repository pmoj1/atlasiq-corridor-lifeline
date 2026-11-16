(()=>{'use strict';
const root=document.getElementById('locations');if(!root)return;
const $=id=>document.getElementById(id);let catalog=null,points=[],lines=[],selected=null,revision=0;
const node=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;};
const number=x=>typeof x==='number'&&Number.isFinite(x);
const coord=p=>({lat:Number(p.lat??p.latitude),lon:Number(p.lon??p.longitude)});
function draw(){const host=$('location-map');host.replaceChildren();if(!points.length&&!lines.length)return;const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 800 360');svg.setAttribute('role','img');svg.setAttribute('aria-label','Freight railway, original town route and selected point');const all=points.map(coord).concat(lines.flat());if(selected)all.push(selected);const west=Math.min(...all.map(p=>p.lon))-1,east=Math.max(...all.map(p=>p.lon))+1,south=Math.min(...all.map(p=>p.lat))-1,north=Math.max(...all.map(p=>p.lat))+1;const xy=p=>[55+(p.lon-west)/(east-west)*690,35+(north-p.lat)/(north-south)*265];const make=(tag,attrs)=>{const el=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));svg.append(el);return el;};for(let y=70;y<330;y+=65)make('line',{x1:30,x2:770,y1:y,y2:y,stroke:'#ffffff09'});for(const segment of catalog?.segments||[]){const a=points.find(p=>p.id===segment.from),b=points.find(p=>p.id===segment.to);if(!a||!b)continue;make('polyline',{points:[a,b].map(p=>xy(coord(p)).join(',')).join(' '),fill:'none',stroke:'#e9aa4b','stroke-width':3,'stroke-dasharray':'7 7',opacity:'.65'});}for(const line of lines){make('polyline',{points:line.map(p=>xy(p).join(',')).join(' '),fill:'none',stroke:'#85e6ce','stroke-width':3});}points.forEach((p,i)=>{const [x,y]=xy(coord(p));make('circle',{cx:x,cy:y,r:6,fill:'#e9aa4b',stroke:'#222b2a','stroke-width':3});const label=make('text',{x,y:y+(i%2?24:-16),fill:'#e1e5df','text-anchor':'middle','font-size':12});label.textContent=p.name;});if(selected){const[x,y]=xy(selected);make('circle',{cx:x,cy:y,r:16,fill:'#e9aa4b33',stroke:'#fff','stroke-width':1});make('circle',{cx:x,cy:y,r:5,fill:'#fff'});}host.append(svg);}
function list(){const q=$('location-search').value.toLowerCase();const host=$('location-list');host.replaceChildren();const filtered=points.filter(p=>`${p.name} ${p.id}`.toLowerCase().includes(q));filtered.forEach(p=>{const button=node('button',p.name);button.type='button';button.addEventListener('click',()=>{const c=coord(p);$('location-lat').value=c.lat;$('location-lon').value=c.lon;check();});host.append(button);});if(!filtered.length)host.append(node('p','No reference places match. You can enter coordinates below.','muted'));}
function field(host,label,value){const item=node('div');item.append(node('dt',label),node('dd',value));host.append(item);}
function result(data){const host=$('location-result');host.replaceChildren();host.hidden=false;host.append(node('p','LOCATION CHECK','eyebrow'),node('h2',data.label||'Distance to the corridor'));const metrics=node('dl',undefined,'location-metrics');const waypoint=data.nearest_waypoint||{};const segment=data.nearest_segment||{};const mapped=data.mapped||{};
field(metrics,'Distance to mapped freight rail',number(mapped.distance_km)?mapped.distance_km.toFixed(2)+' km':'Unavailable');
field(metrics,'Nearest mapped section',mapped.section||'Unavailable');
field(metrics,'Original town route',number(segment.distance_km)?segment.distance_km.toFixed(2)+' km · '+segment.name:'Unavailable');
field(metrics,'Nearest reference place',waypoint.name||'Unknown');
host.append(metrics);
const inside=mapped.within_screening_buffer;
host.append(node('p',typeof inside==='boolean'?(inside?'Within':'Outside')+' the '+data.screening_buffer_km+' km mapped rail screening area.':'Mapped screening result unavailable.','location-screening'));
const details=node('details');details.append(node('summary','Inspect location evidence'),node('pre',JSON.stringify(data,null,2)));host.append(details);const sources=data.provenance||data.sources||catalog?.provenance||[];for(const source of sources){const url=typeof source==='string'?source:source.url||source.source_url;if(!url)continue;try{const u=new URL(url);if(!['http:','https:'].includes(u.protocol))continue;const a=node('a',source.title||source.name||'Reference source');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';host.append(a,node('span',' · '));}catch{}}
}
async function check(){const mine=++revision;$('location-result').hidden=true;const lat=Number($('location-lat').value),lon=Number($('location-lon').value);if(!$('location-lat').value.trim()||!$('location-lon').value.trim()||!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180){$('location-status').textContent='Enter latitude −90 to 90 and longitude −180 to 180.';return;}$('location-result').hidden=true;$('location-status').textContent='Checking both routes…';selected={lat,lon};draw();try{const response=await fetch(`/api/location-check?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);const data=await response.json();if(!response.ok)throw Error(data.error||'Location check unavailable');if(mine!==revision)return;result(data);$('location-status').textContent=`Checked ${lat.toFixed(5)}, ${lon.toFixed(5)}. Geometry check only.`;}catch(error){if(mine===revision)$('location-status').textContent=`Check unavailable: ${error.message}. No coverage or safety conclusion can be made.`;}}
$('location-search').addEventListener('input',list);$('location-form').addEventListener('submit',e=>{e.preventDefault();check();});$('use-location').addEventListener('click',()=>{if(!navigator.geolocation){$('location-status').textContent='Location access is unavailable. Enter coordinates manually.';return;}const mine=++revision;$('location-result').hidden=true;$('location-status').textContent='Waiting for your browser location permission…';navigator.geolocation.getCurrentPosition(position=>{if(mine!==revision)return;$('location-lat').value=position.coords.latitude;$('location-lon').value=position.coords.longitude;check();},()=>{if(mine===revision)$('location-status').textContent='Could not get your position. You can enter coordinates manually.';},{enableHighAccuracy:false,timeout:12000,maximumAge:0});});
fetch('/api/locations').then(async response=>{if(!response.ok)throw Error('Reference catalogue unavailable');return response.json();}).then(data=>{catalog=data;points=(data.points||data.waypoints||data.locations||[]).filter(p=>{const c=coord(p);return number(c.lat)&&number(c.lon);});$('location-status').textContent=`${points.length} reference places available. Choose a place or enter coordinates.`;list();draw();}).catch(error=>{$('location-status').textContent=error.message;});
fetch('/api/mapped-route').then(async response=>{
    if(!response.ok)throw Error('Mapped railway unavailable.');
    const data=await response.json();
    const parts=data.features.flatMap(({geometry})=>{
        if(geometry.type==='LineString')return [geometry.coordinates];
        if(geometry.type==='MultiLineString')return geometry.coordinates;
        throw Error('Unexpected railway geometry.');
    });
    if(!parts.length)throw Error('Mapped rail geometry is empty.');
    lines=parts.map(part=>{
        if(part.length<2)throw Error('Incomplete rail section.');
        return part.map(([lon,lat])=>{
            if(!number(lon)||!number(lat)||Math.abs(lon)>180||Math.abs(lat)>90)throw Error('Invalid rail coordinate.');
            return {lat,lon};
        });
    });
    $('catalog-note').textContent='Australian Government National Key Freight Routes · rail layer 6. The original town route starts in central Perth.';
    draw();
}).catch(()=>{
    $('catalog-note').textContent='Mapped rail could not be displayed. The dashed town route remains available as a reference.';
});
})();
