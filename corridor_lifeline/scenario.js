/* Local assumptions calculator. No network, company data or predictive model. */
(function () {
  'use strict';
  function calculate(stock, use, eta, delay, safety) {
    return { cover: stock / use, buffer: stock / use - eta - delay - safety,
      shortfall: Math.max(0, (eta + delay) * use - stock), arrival: eta + delay };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = calculate;
  if (typeof document === 'undefined') return;
  function init() {
    const root = document.getElementById('scenario-tool');
    if (!root) return;
    const ids = ['stock', 'use', 'eta', 'delay', 'safety'];
    const inputs = ids.map(id => document.getElementById('sc-' + id));
    const fmt = n => n.toLocaleString(undefined, {maximumFractionDigits: 1});
    function update() {
      const valid = inputs.every(el => el.value.trim() !== '' && Number.isFinite(Number(el.value)) && el.checkValidity());
      document.getElementById('sc-error').hidden = valid;
      document.getElementById('sc-output').hidden = !valid;
      if (!valid) return;
      const [stock,use,eta,delay,safety] = inputs.map(el => Number(el.value));
      const r = calculate(stock,use,eta,delay,safety);
      document.getElementById('sc-cover').textContent = fmt(r.cover) + ' days';
      document.getElementById('sc-buffer').textContent = fmt(r.buffer) + ' days';
      document.getElementById('sc-shortfall').textContent = fmt(r.shortfall) + ' t';
      const days = [...new Set([0,1,3,7,14,delay])].sort((a,b)=>a-b);
      document.getElementById('sc-sensitivity').innerHTML = days.map(d => {
        const v = calculate(stock,use,eta,d,safety);
        return `<tr><th scope="row">${fmt(d)} days${d === delay ? ' · selected' : ''}</th><td>${fmt(v.buffer)} d</td><td>${fmt(v.shortfall)} t</td></tr>`;
      }).join('');
      const horizon = Math.max(1,r.arrival * 1.25,Math.min(r.cover * 1.2,Math.max(14,r.arrival * 1.5)));
      const maxStock = Math.max(1,stock), x = d => 64 + 544*d/horizon, y = s => 218 - 168*s/maxStock;
      const end = Math.min(r.cover,horizon), arrivalX = x(r.arrival);
      let ticks = '';
      for(let i=0;i<=4;i++) { const d=horizon*i/4; ticks += `<text x="${x(d)}" y="242" text-anchor="middle">${fmt(d)}</text>`; }
      document.getElementById('sc-chart').innerHTML = `<title id="sc-chart-title">Stock remaining against elapsed days</title><desc id="sc-chart-desc">Initial stock ${fmt(stock)} tonnes. Stock cover ${fmt(r.cover)} days. Arrival after ${fmt(r.arrival)} days. Shortfall ${fmt(r.shortfall)} tonnes.</desc><g font-family="system-ui,sans-serif" font-size="11" fill="#64717a"><text x="64" y="22">Tonnes · ${fmt(stock)} at day 0</text><path d="M64 50V218H608" fill="none" stroke="#cdd7de"/><path d="M64 ${y(stock)} L${x(end)} ${y(Math.max(0,stock-use*end))} L608 ${y(Math.max(0,stock-use*horizon))} L608 218 H64 Z" fill="#e5f1fb"/><path d="M64 ${y(stock)} L${x(end)} ${y(Math.max(0,stock-use*end))} L608 ${y(Math.max(0,stock-use*horizon))}" fill="none" stroke="#0071e3" stroke-width="3"/><path d="M${arrivalX} 40V218" stroke="#a86317" stroke-dasharray="5 4"/><text x="${arrivalX}" y="35" text-anchor="middle" fill="#88500e">Arrival · ${fmt(r.arrival)}d</text><text x="52" y="222" text-anchor="end">0</text>${ticks}<text x="608" y="264" text-anchor="end">Elapsed days</text></g>`;
    }
    inputs.forEach(el => el.addEventListener('input',update)); update();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
