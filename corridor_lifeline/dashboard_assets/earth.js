(() => {
  const panel = document.getElementById('earth');
  const select = document.getElementById('earth-site');
  const status = document.getElementById('earth-status');
  let sites = [], loading = false, revision = 0;
  function render() {
    const site = sites[select.selectedIndex];
    if (!site) return;
    const version = ++revision;
    let completed = 0, failures = 0;
    status.textContent = 'Loading imagery…';
    const lat = site.lat, lon = site.lon, dx = 0.145 / Math.cos(lat * Math.PI / 180);
    for (const [id, style] of [['earth-rgb','simple_rgb'],['earth-ir','infrared_green']]) {
      const img = document.getElementById(id);
      function finish(error) {
        if (version !== revision) return;
        failures += Number(error);
        if (++completed === 2) status.textContent = failures ? 'Incomplete imagery · '+failures+' layer(s) unavailable.' : site.name+' · Both spectral views loaded. Colours describe surface reflectance.';
      }
      img.onload = () => finish(false);
      img.onerror = () => finish(true);
      const params = new URLSearchParams({service:'WMS',version:'1.3.0',request:'GetMap',layers:'ga_ls8cls9c_gm_cyear_3',styles:style,crs:'EPSG:4326',bbox:[lat-.113,lon-dx,lat+.113,lon+dx].join(','),width:512,height:400,format:'image/png',time:'2025-01-01'});
      img.src = 'https://ows.dea.ga.gov.au/?'+params;
    }
  }
  async function enter() {
    if (panel.hidden || loading) return;
    if (!sites.length) {
      loading = true;
      try {
        const response = await fetch('/api/weather');
        sites = (await response.json()).sites || [];
        if (!sites.length) throw Error();
        for (const site of sites) select.add(new Option(site.name,site.name));
      } catch { status.textContent = 'Location network unavailable. Reopen this view to retry.'; return; }
      finally { loading = false; }
    }
    const saved = sessionStorage.getItem('atlas-site');
    if (sites.some(s=>s.name===saved)) select.value = saved;
    render();
  }
  select.onchange = () => {sessionStorage.setItem('atlas-site',select.value); window.dispatchEvent(new CustomEvent('atlas-site',{detail:select.value})); render();};
  new MutationObserver(enter).observe(panel,{attributes:true,attributeFilter:['hidden']});
  enter();
})();
