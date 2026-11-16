(() => {
  const panel = document.getElementById('road-plan');
  if (!panel) return;
  const byId = suffix => document.getElementById('plan-' + suffix);
  const form = byId('form');
  const endpoint = '/api/road-watch';
  let configured = false, draft = '', busy = false;
  const time = stamp => stamp ? String(stamp).replace('T', ' ').replace(/(\.\d+)?(Z|\+00:00)$/, ' UTC') : 'Pending';
  function element(tag, value) {
    const node = document.createElement(tag);
    if (value != null) node.textContent = value;
    return node;
  }
  function matrix(sites) {
    const table = element('table');
    table.append(element('caption','Hourly weather exposure · amber watch / teal below threshold / grey unknown'));
    sites.forEach(site => {
      const row = element('tr');
      row.append(element('th', site.name));
      site.hours.forEach(hour => {
        const cell = element('td');
        cell.dataset.level = hour.exposure;
        cell.title = [time(hour.time),hour.exposure,(hour.rain_mm ?? '—')+' mm/h',(hour.wind_kmh ?? '—')+' km/h'].join(' · ');
        cell.setAttribute('aria-label',cell.title);
        row.append(cell);
      });
      table.append(row);
    });
    byId('grid').replaceChildren(...(sites.length ? [table] : []));
  }
  function drawRoad(data) {
    const svg = byId('map');
    svg.replaceChildren();
    const points = data.config.points;
    const line = data.route?.geometry?.coordinates || [];
    const all = [...line,...points.map(p=>[p.lon,p.lat])];
    if (!all.length) return;
    const c = Math.cos(points[0].lat*Math.PI/180);
    const xs=all.map(([lon])=>lon*c), ys=all.map(p=>p[1]);
    const west=Math.min(...xs),east=Math.max(...xs),south=Math.min(...ys),north=Math.max(...ys);
    const scale=Math.min(420/Math.max(.00001,east-west),76/Math.max(.00001,north-south));
    const pos=(lon,lat)=>[240+(lon*c-(west+east)/2)*scale,60-(lat-(south+north)/2)*scale];
    function add(tag,attrs,label) {
      const node=document.createElementNS('http://www.w3.org/2000/svg',tag);
      Object.entries(attrs).forEach(([name,val])=>node.setAttribute(name,val));
      if(label) node.textContent=label;
      svg.append(node);
    }
    if(line.length) add('polyline',{points:line.map(p=>pos(...p).join(',')).join(' '),stroke:'#4ed9d7','stroke-width':3,fill:'none'});
    points.forEach((p,i)=>{
      const [cx,cy]=pos(p.lon,p.lat),hours=data.current.sites?.find(s=>s.name===p.name)?.hours||[];
      const color=hours.some(h=>h.exposure==='watch')?'#ffbf66':hours.length&&hours.every(h=>h.exposure==='below threshold')?'#3dd1b3':'#aebac3';
      add('circle',{cx,cy,r:8,fill:color,stroke:'#fff'});
      add('text',{x:cx,y:cy+4,'text-anchor':'middle',fill:'#101e20','font-size':11},String(i+1));
    });
    byId('map-caption').textContent=(line.length?'Mapped road · ':'Planner sample points · ')+points.map((p,i)=>(i+1)+' '+p.name).join('  /  ');
  }
  function render(data) {
    const {config,current,history,interval_minutes} = data;
    if (!configured) {
      form.elements.road.value = config.road;
      form.elements.permit.value = config.permit;
      form.elements.points.value = config.points.map(p=>[p.name,p.lat,p.lon].join(', ')).join('\n');
      configured = true;
    }
    byId('name').textContent = config.road;
    byId('state').textContent = current.status === 'watch' ? 'Prepare access review' : current.status;
    byId('evidence').textContent = current.detail;
    const samples = current.cloud_samples || [];
    byId('cloud').textContent = 'Satellite IR image brightness (0–255) · '+(samples.map(p=>p.name+' '+(p.brightness ?? 'unavailable')).join(' / ') || 'Unavailable');
    drawRoad(data);
    matrix(current.sites || []);
    byId('windows').replaceChildren(...(current.windows||[]).map(w => element('p',
      w.point+' · '+time(w.start)+' to '+time(w.end)+' · peak rain '+(w.max_rain_mm ?? '—')+' mm/h · peak wind '+(w.max_wind_kmh ?? '—')+' km/h')));
    byId('times').textContent = 'Checked '+time(current.checked_at)+' · Satellite observation '+time(current.satellite_at)+' · Checks every '+interval_minutes+' min while local service runs';
    draft = current.draft || '';
    byId('download').disabled = !draft;
    byId('history').replaceChildren(...history.map(h=>{
      const row=element('li',[time(h.checked_at),h.status,h.detail,...(h.notes||[])].join(' · '));
      if(h.draft) {
        const button=element('button','Download original draft');
        button.onclick=()=>download(h.draft);
        row.append(' ',button);
      }
      return row;
    }));
    window.dispatchEvent(new CustomEvent('atlas-road-plan',{detail:data}));
  }
  async function refresh() {
    if (busy || document.hidden || panel.closest('[role=tabpanel]')?.hidden) return;
    busy = true;
    try {
      const response = await fetch(endpoint);
      if (!response.ok) throw Error();
      render(await response.json());
    } catch {
      byId('state').textContent = 'Current check unavailable';
      draft = '';
      byId('download').disabled = true;
      byId('evidence').textContent = 'Last displayed evidence may be old.';
    } finally { busy = false; }
  }
  form.onsubmit = async event => {
    event.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const points = form.elements.points.value.trim().split(/\r?\n/).map(line => {
        const fields = line.split(',').map(x=>x.trim());
        if (fields.length!==3 || fields.some(x=>!x) || !fields.slice(1).every(x=>Number.isFinite(Number(x)))) throw Error('Use point name, latitude, longitude on each line.');
        return {name:fields[0],lat:Number(fields[1]),lon:Number(fields[2])};
      });
      const token = JSON.parse(document.getElementById('workspace-settings').textContent).token;
      const response = await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-AtlasIQ-Token':token},body:JSON.stringify({road:form.elements.road.value,permit:form.elements.permit.value,points})});
      const result = await response.json();
      if (!response.ok) throw Error(result.error || 'Configuration rejected');
      byId('feedback').textContent = 'Saved. Checking new points.';
      configured = false;
      await refresh();
    } catch(e) { byId('feedback').textContent = e.message; }
    finally { button.disabled=false; }
  };
  function download(text) {
    if (!text) return;
    const url = URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));
    const a = element('a'); a.href=url; a.download='AtlasIQ-permit-preparation.txt';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  byId('download').onclick = () => download(draft);
  const tab = panel.closest('[role=tabpanel]');
  if (tab) new MutationObserver(refresh).observe(tab,{attributes:true,attributeFilter:['hidden']});
  document.addEventListener('visibilitychange',refresh);
  setInterval(refresh,15000);refresh();
})();
