(() => {
  'use strict';
  const settings = JSON.parse(document.getElementById('workspace-settings').textContent);
  const mode = document.getElementById('assessment-mode');
  mode.value = settings.mode;
  mode.addEventListener('change', () => { location.href = '/?view=' + encodeURIComponent(mode.value) + '#overview'; });
  const button = document.getElementById('collect-now');
  const status = document.getElementById('collection-status');
  async function request(path, options) {
    const response = await fetch(path, options); const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed'); return data;
  }
  async function history() {
    const container = document.getElementById('assessment-history');
    try {
      const rows = await request('/api/history');
      container.replaceChildren();
      if (!rows.length) { container.textContent = 'No current collections saved yet.'; return; }
      const table = document.createElement('table');
      const caption = document.createElement('caption'); caption.textContent = 'Collection history · newest first'; table.append(caption);
      const head = document.createElement('tr');
      ['Assessed at', 'Score / 100', 'Level', 'Coverage'].forEach(text => { const cell = document.createElement('th'); cell.textContent = text; head.append(cell); }); table.append(head);
      rows.forEach(row => { const tr = document.createElement('tr'); [row.as_of, row.score, row.level, row.coverage].forEach(text => { const td = document.createElement('td'); td.textContent = String(text); tr.append(td); }); table.append(tr); });
      container.append(table);
    } catch (error) { container.textContent = 'History unavailable: ' + error.message; }
  }
  let polling = false;
  async function poll(navigate = false) {
    if (polling) return; polling = true;
    try {
      const state = await request('/api/status');
      button.disabled = state.running;
      if (state.running) { status.textContent = 'Checking configured sources… failures and stale feeds will remain visible.'; setTimeout(() => poll(navigate), 1500); }
      else if (state.error) status.textContent = 'Collection failed: ' + state.error + '. Check the saved assessment timestamp; collection or output may be incomplete.';
      else if (state.completed_at) {
        status.textContent = 'Collection finished at ' + state.completed_at + '. Review source gaps before using the result.';
        if (navigate) { location.href = '/?view=live#overview'; return; }
      }
    } catch (error) { button.disabled = false; status.textContent = 'Collection status unavailable: ' + error.message; }
    finally { polling = false; }
  }
  button.addEventListener('click', async () => {
    button.disabled = true;
    try { await request('/api/collect', { method: 'POST', headers: { 'X-AtlasIQ-Token': settings.token } }); await poll(true); }
    catch (error) { status.textContent = error.message; button.disabled = false; }
  });
  history(); poll();
})();
