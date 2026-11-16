(() => {
  'use strict';
  const tabs = [...document.querySelectorAll('[data-view]')];
  const defaultTab = tabs.find(t => t.dataset.view === 'weather') || tabs[0];
  function activate(tab, remember=false) {
    if (!tab) return;
    for (const panel of document.querySelectorAll('main .view')) panel.hidden = panel.id !== tab.dataset.view;
    for (const item of tabs) {
      const panel = document.getElementById(item.dataset.view);
      if (!panel) continue;
      const active = item === tab;
      item.id = 'tab-' + item.dataset.view;
      item.setAttribute('aria-controls', panel.id);
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', item.id);
      panel.hidden = !active;
    }
    if (remember && location.hash !== '#' + tab.dataset.view) history.pushState(null, '', '#' + tab.dataset.view);
  }
  function restore() {
    const key = location.hash.slice(1);
    if (['overview','evidence','scenario','locations'].includes(key)) {
      activate({dataset:{view:key}});
      defaultTab.tabIndex = 0;
      document.querySelector('.regional-tools').open = true;
    } else activate(tabs.find(t => t.dataset.view === key) || defaultTab);
  }
  for (const [i, tab] of tabs.entries()) {
    tab.addEventListener('click', () => activate(tab, true));
    tab.addEventListener('keydown', e => {
      const offsets = {ArrowDown:1, ArrowRight:1, ArrowUp:-1, ArrowLeft:-1};
      let j = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length-1 : undefined;
      if (Object.hasOwn(offsets,e.key)) j = (i+offsets[e.key]+tabs.length)%tabs.length;
      if (j !== undefined) {e.preventDefault(); activate(tabs[j],true); tabs[j].focus();}
    });
  }
  window.addEventListener('popstate',restore);
  window.addEventListener('hashchange',restore);
  restore();
  const search=document.getElementById('evidence-search'),filter=document.getElementById('evidence-filter');function update(){let count=0;document.querySelectorAll('.feed').forEach(feed=>{const health=feed.dataset.health==='ok'?'ok':'other';feed.hidden=!(feed.textContent.toLowerCase().includes(search.value.toLowerCase())&&(filter.value==='all'||filter.value===health));if(!feed.hidden)count++;});document.getElementById('filter-count').textContent=`${count} sources shown`; }if(search){search.addEventListener('input',update);filter.addEventListener('change',update);update();}document.getElementById('export-result')?.addEventListener('click',()=>{const result=JSON.parse(document.getElementById('saved-result').textContent);const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='corridor-saved-assessment.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});})();
