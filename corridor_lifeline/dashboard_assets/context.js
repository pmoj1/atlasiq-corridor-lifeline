(() => {
  'use strict';
  const root = document.getElementById('context-events');
  if (!root) return;
  const settings = JSON.parse(document.getElementById('workspace-settings').textContent);
  const button = document.getElementById('context-refresh');
  const status = document.getElementById('context-status');
  let saved = null, timer = null, busy = false, page = 0;
  const pageSize = 12;
  const el = (tag, text, className) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = String(text); if(className) n.className=className; return n; };
  function link(label, url) {
    try { const u = new URL(url); if (!['http:', 'https:'].includes(u.protocol)) throw new Error(); const a=el('a', label); a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a; }
    catch { return el('span', label); }
  }
  function when(value) { const d=new Date(value); return value && Number.isFinite(d.getTime()) ? d.toLocaleString() : 'Not reported'; }
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const hazard=e=>e.source_id==='dea_hotspots'?'hotspot':e.kind==='rail_notice'?'rail':e.source_id==='usgs'?'earthquake':e.kind==='road_incident'?'road':/fire/i.test(e.title)?'fire':/flood/i.test(e.title)?'flood':'warning';
  function plot(rows,filter) {
    const container=document.getElementById('context-plot');container.replaceChildren();
    const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 800 300');svg.style.width='100%';svg.style.background='#f5f3ed';svg.style.borderRadius='18px';svg.setAttribute('role','img');svg.setAttribute('aria-label','Reported event coordinate grid');
    const bounds=filter==='all'?[-180,180,-90,90]:[105,165,-50,-5];
    const x=v=>40+(v-bounds[0])/(bounds[1]-bounds[0])*720, y=v=>270-(v-bounds[2])/(bounds[3]-bounds[2])*240;
    function node(tag,attrs,text){const n=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));if(text)n.textContent=text;return n;}
    for(let i=0;i<=4;i++){const lon=bounds[0]+i*(bounds[1]-bounds[0])/4,lat=bounds[2]+i*(bounds[3]-bounds[2])/4;svg.append(node('line',{x1:x(lon),x2:x(lon),y1:30,y2:270,stroke:'#d7dcd4'}),node('line',{x1:40,x2:760,y1:y(lat),y2:y(lat),stroke:'#d7dcd4'}),node('text',{x:x(lon),y:290,'font-size':11,'text-anchor':'middle',fill:'#58635b'},Math.round(lon)+'°'),node('text',{x:3,y:y(lat),'font-size':11,fill:'#58635b'},Math.round(lat)+'°'));}
    rows.forEach(e=>{if(typeof e.lon!=='number'||typeof e.lat!=='number'||!Number.isFinite(e.lon)||!Number.isFinite(e.lat)||e.lon<bounds[0]||e.lon>bounds[1]||e.lat<bounds[2]||e.lat>bounds[3])return;const c=node('circle',{cx:x(e.lon),cy:y(e.lat),r:5,fill:e.near_corridor?'#b57215':'#426d66',opacity:.8});c.append(node('title',{},e.title+' · '+when(e.observed_at)));svg.append(c);});container.append(svg);
  }
  function bars(id,items,select,selected){
    const host=document.getElementById(id),max=Math.max(1,...items.map(item=>item.count));
    host.replaceChildren();
    for(const item of items){
      const row=el(select?'button':'div',undefined,'signal-row');
      if(select){row.type='button';row.setAttribute('aria-pressed',String(item.key===selected));row.addEventListener('click',()=>select(item));}
      const track=el('span',undefined,'signal-track'),bar=el('i');
      bar.style.width=(100*item.count/max)+'%';track.append(bar);
      row.append(el('span',item.label),track,el('b',item.count.toLocaleString()));host.append(row);
    }
  }
  function events() {
    root.replaceChildren();
    const filter=document.getElementById('context-filter').value;
    const selected=document.getElementById('context-hazard').value;
    const inRegion=(saved?.events || []).filter(e => filter==='all' || (filter==='near' ? e.near_corridor===true : ['WA','SA','NT','TAS','QLD','VIC','NSW','ACT','Australia','AU'].includes(e.region) || finite(e.lat)&&finite(e.lon)&&e.lat>=-50&&e.lat<=-5&&e.lon>=105&&e.lon<=165));
    const rows=inRegion.filter(e=>selected==='all' || hazard(e)===selected);
    if(saved){
      document.getElementById('context-count').textContent=rows.length.toLocaleString();
      document.getElementById('context-near').textContent=rows.filter(e=>e.near_corridor===true).length.toLocaleString();
      const selector=document.getElementById('context-hazard');
      const types=[...selector.options].filter(o=>o.value!=='all').map(o=>({key:o.value,label:o.textContent,count:inRegion.filter(e=>hazard(e)===o.value).length}));
      bars('signals-types',types,item=>{selector.value=selected===item.key?'all':item.key;page=0;events();},selected);
      const buckets=['Under 6 h','6–24 h','1–3 days','Over 3 days','Unknown time'].map(label=>({label,count:0}));
      for(const row of rows){
        const age=(Date.parse(saved.fetched_at)-Date.parse(row.observed_at))/3600000;
        buckets[!Number.isFinite(age)||age<0?4:age<6?0:age<24?1:age<=72?2:3].count++;
      }
      bars('signals-age',buckets);
    }
    const unmapped=rows.filter(e=>!finite(e.lat)||!finite(e.lon)).length;
    document.getElementById('context-unmapped').textContent=unmapped+' notice(s) have no usable coordinates and are omitted from the plot. Near-corridor filtering uses coordinates only; place-name candidates remain unconfirmed.';
    rows.sort((a,b)=>Number(b.near_corridor===true)-Number(a.near_corridor===true)||Number(!!b.candidate_places?.length)-Number(!!a.candidate_places?.length)||Number(a.source_id==='usgs')-Number(b.source_id==='usgs')||(Date.parse(b.observed_at)||0)-(Date.parse(a.observed_at)||0));
    if(document.getElementById('context-map-detail').open)plot(rows,filter);
    page = Math.max(0,Math.min(page, Math.ceil(rows.length/pageSize)-1));
    const start=page*pageSize;
    document.getElementById('context-pager').hidden=!rows.length;
    document.getElementById('context-page').textContent=rows.length?(start+1)+'–'+Math.min(start+pageSize,rows.length)+' of '+rows.length+' reports':'';
    document.getElementById('context-prev').disabled=!page;
    document.getElementById('context-next').disabled=start+pageSize>=rows.length;
    if (!rows.length) { root.append(el('p','No events in this view. This does not establish safe conditions or complete coverage.')); return; }
    const table=el('table'), caption=el('caption','Sorted by route relevance, then report type and time');table.append(caption);
    const head=el('thead'), tr=el('tr');['Event / evidence','Reported time','Coordinates','Hazard / detail','Corridor screening'].forEach(s=>{const h=el('th',s);h.scope='col';tr.append(h);});head.append(tr);table.append(head);const body=el('tbody');
    rows.slice(start,start+pageSize).forEach(e=>{
      const row=el('tr'), evidence=el('td');evidence.append(link(e.title || 'Untitled event',e.url),el('div',e.source || e.source_id || 'Source unspecified','muted'));
      const time=el('td',when(e.observed_at));if(e.updated_at)time.append(el('div','Updated: '+when(e.updated_at),'muted'));
      const coords=el('td',finite(e.lat)&&finite(e.lon)?e.lat.toFixed(3)+', '+e.lon.toFixed(3):'Not reported');
      const distance=el('td',e.near_corridor===true?'Within 50 km of mapped rail':e.near_corridor===false?'Outside screening buffer':'Location relevance unknown');if(finite(e.distance_km))distance.append(el('div',e.distance_km.toLocaleString(undefined,{maximumFractionDigits:1})+' km · '+(e.mapped_section||'mapped freight route'),'muted'));
      const matches=e.candidate_places || e.place_matches || [];
      if(matches.length)distance.append(el('div','Place-name candidate only: '+matches.map(p=>typeof p==='string'?p:p.name||p.id).join(', ')+'. Location and operational impact require review.','muted'));
      const detail=el('td',hazard(e));if(hazard(e)==='earthquake'&&finite(e.magnitude))detail.append(el('div','Magnitude '+e.magnitude));
      if(e.detail){const more=el('details');more.append(el('summary','Report detail'),el('p',e.detail));evidence.append(more);}row.append(evidence,time,coords,detail,distance);body.append(row);
    });table.append(body);root.append(table);
  }
  function sourceState(source) {
    const base=source.status || 'unknown';
    if (base === 'error' || base === 'unconnected') return base;
    const max=finite(source.max_age_minutes)?source.max_age_minutes:30;
    const stamp=source.freshness_basis==='fetched_at'?source.fetched_at:source.generated_at;
    const generated=stamp?Date.parse(stamp):NaN;
    if(!Number.isFinite(generated))return base+' · freshness unknown';
    const age=Date.now()-generated;
    if(age < -300000)return base+' · timestamp in future';
    if(age>max*60000)return (base==='partial'?'partial · ':'')+'stale · older than '+max+' minutes';
    return base;
  }
  function render(data) {
    document.getElementById("signals-stamp").textContent="Collected "+when(data.fetched_at)+" · checks every 10 min while open";
    saved=data;document.getElementById('context-gaps').textContent=(data.sources||[]).filter(s=>sourceState(s)!=='ok').length;document.getElementById('context-count').textContent=data.events?.length ?? '—';document.getElementById('context-near').textContent=(data.events||[]).filter(e=>e.near_corridor===true).length;document.getElementById('context-fetched').textContent=when(data.fetched_at);
    const sources=document.getElementById('context-sources');sources.replaceChildren();
    const wm=data.world_monitor || {status:'unconfigured',detail:'World Monitor access is not configured.'};const card=el('div',undefined,'context-source');card.append(el('h3','World Monitor'),el('p',String(wm.status).replaceAll('_',' '),'context-state'),el('p',wm.detail || 'No World Monitor data received.'));if(wm.docs_url)card.append(link('World Monitor documentation ↗',wm.docs_url));sources.append(card);
    (data.sources||[]).forEach(s=>{const c=el('div',undefined,'context-source');c.append(el('h3',s.name||s.id),el('p',sourceState(s),'context-state'),el('p','Feed generated: '+when(s.generated_at),'muted'),el('p','Fetched: '+when(s.fetched_at),'muted'));if(s.coverage)c.append(el('p',s.coverage));if(s.limitations&&typeof s.limitations==='string')c.append(el('p',s.limitations));if(s.licence_note)c.append(el('p',s.licence_note,'muted'));if(s.error)c.append(el('p',s.error));if(s.url)c.append(link('Original source ↗',s.url));sources.append(c);});
    (data.limitations||[]).forEach(s=>sources.append(el('p',s,'muted')));events();
  }
  async function request(path, options) {const r=await fetch(path,options);const d=await r.json();if(!r.ok)throw new Error(d.error||'Request failed');return d;}
  async function poll() {
    clearTimeout(timer);
    try {const state=await request('/api/context');if(state.data)render(state.data);busy=Boolean(state.running);button.disabled=busy;
      status.textContent=busy?'Checking event sources…':state.error?'Collection failed: '+state.error+'. Any displayed results are from the last saved response.':state.data?'Collection complete.':'No event collection yet. Select “Refresh notices” to fetch the configured public sources.';
      if(busy)timer=setTimeout(poll,1500);
    } catch(error){busy=false;button.disabled=false;status.textContent='Event context unavailable: '+error.message+'. Any displayed data may be old.';}
  }
  let lastAttempt=0;
  async function refresh(){if(busy)return;lastAttempt=Date.now();busy=true;button.disabled=true;status.textContent='Starting event collection…';try {await request('/api/context-refresh',{method:'POST',headers:{'X-AtlasIQ-Token':settings.token}});await poll();}catch(error){busy=false;button.disabled=false;status.textContent='Unable to refresh: '+error.message;}}
  button.addEventListener('click',refresh);
  document.getElementById('context-filter').addEventListener('change',()=>{page=0;events();});
  document.getElementById('context-hazard').addEventListener('change',()=>{page=0;events();});
  document.getElementById('context-prev').addEventListener('click',()=>{page--;events();});document.getElementById('context-next').addEventListener('click',()=>{page++;events();});
  document.getElementById('context-map-detail').addEventListener('toggle',()=>{if(document.getElementById('context-map-detail').open)events();});
  setInterval(() => { if (saved && !document.hidden && !document.getElementById('context').hidden){document.getElementById('context-gaps').textContent=(saved.sources||[]).filter(s=>sourceState(s)!=='ok').length;document.querySelectorAll('#context-sources .context-state').forEach((n,i)=>{if(i>0&&saved.sources[i-1])n.textContent=sourceState(saved.sources[i-1]);});} }, 60000);
  function refreshVisible(){
    if(document.hidden||document.getElementById('context').hidden||busy)return;
    const fetched=Date.parse(saved?.fetched_at)||0;
    if(Date.now()-Math.max(lastAttempt,fetched)>600000)refresh();
  }
  poll().then(()=>{
    new MutationObserver(refreshVisible).observe(document.getElementById('context'),{attributes:true,attributeFilter:['hidden']});
    document.addEventListener('visibilitychange',refreshVisible);
    setInterval(refreshVisible,30000);refreshVisible();
  });
})();
