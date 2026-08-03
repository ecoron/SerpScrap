function cell(value) { const td = document.createElement('td'); td.textContent = value ?? ''; return td; }

export function groupResults(rows = []) {
  const groups = new Map();
  rows.filter(row => row.result_kind !== 'image').forEach(row => {
    const url = row.canonical_url || row.serp_url || '';
    const group = groups.get(url) || {row, engines: new Set(), relevance: 0};
    group.engines.add(row.search_engine || 'unknown');
    group.relevance = Math.max(group.relevance, Number(row.relevance || row.relevance_score || 0));
    groups.set(url, group);
  });
  return [...groups.values()].sort((a, b) => b.relevance - a.relevance || String(a.row.serp_title || '').localeCompare(String(b.row.serp_title || '')));
}

export function renderResults(target, rows) {
  target.replaceChildren();
  const grouped = groupResults(rows);
  if (!grouped.length) { const row = document.createElement('tr'); const empty = cell('No results yet.'); empty.colSpan = 4; empty.className = 'empty-cell'; row.append(empty); target.append(row); return; }
  grouped.forEach(group => {
    const row = group.row; const tr = document.createElement('tr'); tr.append(cell(row.serp_title || 'Untitled'));
    const link = document.createElement('a'); link.href = row.canonical_url || row.serp_url || '#'; link.target = '_blank'; link.rel = 'noopener'; link.textContent = row.canonical_url || row.serp_url || 'Unavailable';
    const urlCell = document.createElement('td'); urlCell.append(link); tr.append(urlCell, cell(group.relevance.toFixed(4)), cell([...group.engines].sort().join(', '))); target.append(tr);
  });
}

export function renderFailures(target, failures = []) { target.replaceChildren(); failures.forEach(failure => { const item = document.createElement('p'); item.textContent = `${failure.search_engine || 'unknown'} · ${failure.category}: ${failure.message || 'No details'}`; target.append(item); }); }
