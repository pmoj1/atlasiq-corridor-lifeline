(() => {
  const root = document.querySelector('.wx-workspace');
  if (!root) return;
  const id = name => document.getElementById('wx-' + name);
  const el = (tag, text) => { const n = document.createElement(tag); if (text != null) n.textContent=text; return n; };
  const link = (host,label,url) => { host.replaceChildren(); if (!url || !url.startsWith('https://')) return; const a=el('a',label); a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; host.append(a); };
  const time = value => value ? String(value).replace('T',' ').replace(/:\d\d(?:\.\d+)?(?:Z|\+00:00)$/,' UTC') : 'Time unavailable';
  const exposure = h => h?.exposure === 'watch' ? 'watch' : h?.exposure === 'below threshold' ? 'below' : 'unknown';
  let sites=[],loading=false,lastAttempt=0,observed='',tileIssues=0,tileCount=0,updateAge=null,layout=null;
  const svgNS='http://www.w3.org/2000/svg';
  function shape(tag,attrs,text) { const n=document.createElementNS(svgNS,tag); for(const [k,v] of Object.entries(attrs)) n.setAttribute(k,v); if(text!=null)n.textContent=text;return n; }
  let roadPlan = null;
  const forecastValue = (n, unit) => Number.isFinite(n) ? n+' '+unit : 'unknown';
  function roadOverlay(){
    const host=id('image');
    host.querySelector('.wx-road-overlay')?.remove();
    if(!layout || !roadPlan?.config) return;
    const svg=shape('svg',{viewBox:'0 0 100 100',preserveAspectRatio:'none','aria-hidden':'true'});
    svg.classList.add('wx-road-overlay');
    const n=2**layout.zoom;
    function project(lon,lat){
      return [((lon+180)/360*n-layout.x)*100/layout.cols,
        ((1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)*n/2-layout.y)*100/layout.rows];
    }
    const line=roadPlan.route?.geometry?.coordinates;
    if(line?.length) svg.append(shape('polyline',{points:line.map(p=>project(...p).join(',')).join(' '),fill:'none',stroke:'#4ef3fe','stroke-width':3,'vector-effect':'non-scaling-stroke'}));
    for(const point of roadPlan.config.points){
      const site=roadPlan.current?.sites?.find(s=>s.name===point.name);
      const level=site?.hours?.some(h=>h.exposure==='watch')?'watch':site?.hours?.length&&site.hours.every(h=>h.exposure==='below threshold')?'below':'unknown';
      const [cx,cy]=project(point.lon,point.lat);
      svg.append(shape('circle',{cx,cy,r:0.65,fill:{watch:'#ffae41',below:'#31c9ae',unknown:'#a0a4ab'}[level],stroke:'#fff','stroke-width':1,'vector-effect':'non-scaling-stroke'}));
    }
    host.append(svg);
  }
  window.addEventListener('atlas-road-plan',event=>{roadPlan=event.detail;roadOverlay();});
  function drawCharts() {
    const hours=sites[Number(id('site').value)]?.hours || [];
    const host=id('charts');host.replaceChildren();
    const kpis=id('kpis');kpis.replaceChildren();
    for(const [key,label,unit,fn] of [
      ['temp_c','Temperature range','°C',a=>Math.min(...a).toFixed(0)+'–'+Math.max(...a).toFixed(0)],
      ['rain_mm','48 h rain','mm',a=>a.reduce((x,y)=>x+y,0).toFixed(1)],
      ['wind_kmh','Peak wind','km/h',a=>Math.max(...a).toFixed(0)]]){
      const vals=hours.map(h=>h[key]).filter(Number.isFinite),card=el('div');
      card.append(el('small',label),el('strong',vals.length===48?fn(vals)+' '+unit:'—'));kpis.append(card);
    }
    for(const [key,label,color] of [['rain_mm','Hourly precipitation · mm','#6ce1da'],['wind_kmh','Sustained wind · km/h','#f7bb72'],['temp_c','Air temperature · °C','#f29d9e']]){
      const fig=el('figure');fig.className='wx-chart';fig.append(el('figcaption',label));host.append(fig);
      const vals=hours.map(h=>h[key]).filter(Number.isFinite);
      if(!vals.length){fig.append(el('small','No values available'));continue;}
      const low=Math.min(0,...vals), high=Math.max(low+1,...vals);
      const x=i=>40+340*i/Math.max(hours.length-1,1),y=v=>64-49*(v-low)/(high-low);
      const svg=shape('svg',{viewBox:'0 0 410 84',role:'img','aria-label':label+' range '+Math.min(...vals)+' to '+Math.max(...vals)});
      for(const val of [low,high]){svg.append(shape('line',{x1:40,x2:380,y1:y(val),y2:y(val),stroke:'#324456'}),shape('text',{x:2,y:y(val)+3,'font-size':10,fill:'#aec0cc'},Number(val.toFixed(1))));}
      let previous=false,path='';
      hours.forEach((h,i)=>{const v=h[key];if(!Number.isFinite(v)){previous=false;return;}if(key==='rain_mm'){svg.append(shape('rect',{x:x(i)-2,y:y(v),width:4,height:Math.max(0,y(0)-y(v)),fill:color}));}
      else {path+=(previous?' L':' M')+x(i)+' '+y(v);svg.append(shape('circle',{cx:x(i),cy:y(v),r:1.3,fill:color}));previous=true;}});
      if(path)svg.append(shape('path',{d:path,fill:'none',stroke:color,'stroke-width':2}));
      [0,hours.length-1].forEach((i,j)=>svg.append(shape('text',{x:x(i),y:80,'text-anchor':j?'end':'start','font-size':10,fill:'#aec0cc'},time(hours[i].time).slice(5,16)+' UTC')));
      fig.append(svg);
    }
  }
  function grid() {
    const host=id('grid');host.replaceChildren();
    const times=[...new Set(sites.flatMap(s=>s.hours.map(h=>h.time)))].sort();
    if(!times.length){host.append(el('p','Forecast exposure unavailable.'));return;}
    const table=el('table');table.className='wx-gridtable';const header=table.createTHead().insertRow();header.append(el('th','UTC hour'));
    times.forEach((t,i)=>{const th=el('th',i%6===0?t.slice(11,13):'');th.title=time(t);header.append(th);});
    const metric=id('measure').value;
    const scales={
      rain_mm:{limits:[0.1,1,5,15],unit:'mm/h',colors:['#273a48','#456e85','#5b9eb0','#7fd5ce','#c1f8df']},
      wind_kmh:{limits:[10,25,40,50],unit:'km/h',colors:['#273a48','#526875','#77969d','#b8b28d','#f7b064']},
      temp_c:{limits:[10,20,30,40],unit:'°C',colors:['#477589','#5e9c9e','#a4b58c','#d7ac76','#e67953']}
    };
    const scale=scales[metric],legend=id('key');legend.replaceChildren();
    const bands=scale?['< '+scale.limits[0],...scale.limits.slice(0,-1).map((v,i)=>v+'–<'+scale.limits[i+1]),'≥ '+scale.limits.at(-1)]:['Below threshold','Watch','Unknown'];
    bands.forEach((label,i)=>{const item=el('span',label+(scale?' '+scale.unit:''));item.style.setProperty('--chip',scale?scale.colors[i]:['#75aea0','#d68a27','#89949b'][i]);legend.append(item);});
    const body=table.createTBody();sites.forEach(s=>{const row=body.insertRow(), byTime=new Map(s.hours.map(h=>[h.time,h]));const th=el('th'),btn=el('button',s.name+' · '+(s.state||''));btn.type='button';btn.onclick=()=>selectSite(sites.indexOf(s));th.append(btn);row.append(th);times.forEach(t=>{const cell=row.insertCell(),h=byTime.get(t);cell.className=exposure(h);cell.title=s.name+' · '+time(t)+' · '+(h?.exposure||'unknown');if(scale){
        cell.className='unknown';
        if(Number.isFinite(h?.[metric])){
          const value=h[metric],bin=scale.limits.filter(limit=>value>=limit).length;
          cell.style.background=scale.colors[bin];cell.title=s.name+' · '+time(t)+' · '+value+' '+scale.unit;
        }else cell.title=s.name+' · '+time(t)+' · unavailable';
      }
      cell.setAttribute('aria-label',cell.title);});});host.append(table);
  }
  function selectSite(index, broadcast=true){
    id('site').value=String(index);drawCharts();markers();
    if(broadcast){
      const name=sites[index]?.name;if(!name)return;
      sessionStorage.setItem('atlas-site',name);window.dispatchEvent(new CustomEvent('atlas-site',{detail:name}));
    }
  }
  function markers(){
    const host=id('image');host.querySelector('.wx-markers')?.remove();if(!layout)return;
    const overlay=el('div');overlay.className='wx-markers';
    sites.forEach((s,i)=>{
      const r=s.lat*Math.PI/180,n=2**layout.zoom;
      const x=100*((s.lon+180)/360*n-layout.x)/layout.cols;
      const y=100*((1-Math.asinh(Math.tan(r))/Math.PI)*n/2-layout.y)/layout.rows;
      if(x<0||y<0||x>100||y>100)return;
      const btn=el('button');btn.type='button';const upcoming=s.hours.find(h=>h.exposure==='watch')||s.hours[0];
      btn.dataset.watch=s.hours.some(h=>h.exposure==='watch')?'true':s.hours.length===48&&s.hours.every(h=>h.exposure==='below threshold')?'false':'unknown';
      btn.title=s.name+(upcoming?' · '+forecastValue(upcoming.rain_mm,'mm/h')+' · '+forecastValue(upcoming.wind_kmh,'km/h')+' · '+time(upcoming.time):'');
      btn.setAttribute('aria-label','Select '+s.name);btn.setAttribute('aria-pressed',String(i===Number(id('site').value)));
      btn.style.left=x+'%';btn.style.top=y+'%';btn.onclick=()=>selectSite(i);
      overlay.append(btn);
    });roadOverlay();host.append(overlay);
  }
  function displayWeather(d){
    sites=d.sites||[];const select=id('site'),old=sessionStorage.getItem('atlas-site')||select.selectedOptions[0]?.textContent;select.replaceChildren();
    sites.forEach((s,i)=>{const opt=el('option',s.name);opt.value=i;opt.selected=old===s.name;select.append(opt);});select.disabled=!sites.length;drawCharts();grid();markers();
    id('state').textContent=[d.model,d.status,d.fetched_at?'Fetched '+time(d.fetched_at):'',d.error].filter(Boolean).join(' · ');
    link(id('source'),'Forecast source and model documentation',d.source_url);
  }
  function displaySatellite(d){
    const f=(d.frames||[]).slice(-1)[0],host=id('image');
    link(id('sat-source'),d.source||'Satellite source',d.source_url);
    if(!f?.tiles?.length){host.replaceChildren();observed='';layout=null;updateAge=null;id('sat-state').textContent=d.detail||'Imagery unavailable.';return;}
    const g=d.grid;
    layout={zoom:g.zoom,x:g.x,y:g.y,cols:g.columns,rows:g.rows};
    function state(){
      const age=Math.max(0,Math.floor((Date.now()-Date.parse(f.observed_at))/60000));
      id('sat-state').textContent=time(f.observed_at)+' · '+age+' min old · '+(d.status==='stale'?'Stale scan · ':'')+
        (tileIssues?'Incomplete mosaic':tileCount===f.tiles.length?'Latest received scan':'Loading scan');
    }
    updateAge=state;
    if(observed===f.observed_at&&!tileIssues){state();return;}
    observed=f.observed_at;tileIssues=0;tileCount=0;host.replaceChildren();
    host.style.aspectRatio=layout.cols+'/'+layout.rows;
    const tiles=el('div');tiles.className='wx-tiles';tiles.style.gridTemplateColumns='repeat('+layout.cols+',1fr)';tiles.style.gridTemplateRows='repeat('+layout.rows+',1fr)';host.append(tiles);
    f.tiles.forEach(url=>{const img=el('img');img.alt='';
      const done=failed=>{if(!tiles.isConnected)return;tileCount++;if(failed)tileIssues++;state();};
      img.onload=()=>done(false);img.onerror=()=>done(true);img.src=url;tiles.append(img);
    });markers();state();
  }
  async function request(url,display,errorKey){try{const response=await fetch(url);if(!response.ok)throw Error();display(await response.json());}catch{display({status:'unavailable',error:'Forecast unavailable.',detail:'Imagery unavailable.'});id(errorKey).textContent='Feed unavailable. Refresh to retry.';}}
  async function refresh(){if(loading)return;loading=true;lastAttempt=Date.now();id('refresh').disabled=true;id('refresh').textContent='Refreshing…';try{await Promise.all([request('/api/weather',displayWeather,'state'),request('/api/satellite',displaySatellite,'sat-state')]);}finally{loading=false;id('refresh').disabled=false;id('refresh').textContent='Refresh feeds';}}
  window.addEventListener('atlas-site',event=>{
    const i=sites.findIndex(s=>s.name===event.detail);
    if(i>=0&&Number(id('site').value)!==i)selectSite(i,false);
  });
  id('refresh').onclick=refresh;id('measure').onchange=grid;id('site').onchange=()=>selectSite(Number(id('site').value));
  const tab=root.closest('[role=tabpanel]');function visible(){if(tab?.hidden||document.hidden)return;if(updateAge)updateAge();if(Date.now()-lastAttempt>=300000)refresh();}
  if(tab)new MutationObserver(visible).observe(tab,{attributes:true,attributeFilter:['hidden']});
  document.addEventListener('visibilitychange',visible);setInterval(visible,30000);visible();
})();
