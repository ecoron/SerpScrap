function cell(value) { const td = document.createElement('td'); td.textContent = value ?? ''; return td; }

export function groupResults(rows = []) {
  const groups = new Map();
  rows.forEach(row => {
    const url = row.canonical_url || row.serp_url || '';
    const group = groups.get(url) || {row, engines: new Set(), relevance: 0};
    group.engines.add(row.search_engine || 'unknown');
    group.relevance = Math.max(group.relevance, Number(row.relevance || row.relevance_score || 0));
    groups.set(url, group);
  });
  return [...groups.values()].sort((a, b) => b.relevance - a.relevance || String(a.row.serp_title || '').localeCompare(String(b.row.serp_title || '')));
}

export function renderResults(target, rows, onSelect) {
  target.replaceChildren();
  const grouped = groupResults(rows);
  if (!grouped.length) { const row = document.createElement('tr'); const empty = cell('No results yet.'); empty.colSpan = 6; empty.className = 'empty-cell'; row.append(empty); target.append(row); return; }
  grouped.forEach(group => {
    const row = group.row; const tr = document.createElement('tr'); tr.append(cell(row.serp_title || 'Untitled'));
    const link = document.createElement('a'); link.href = row.canonical_url || row.serp_url || '#'; link.target = '_blank'; link.rel = 'noopener'; link.textContent = row.canonical_url || row.serp_url || 'Unavailable';
    const urlCell = document.createElement('td'); urlCell.append(link); tr.append(urlCell, cell(row.result_kind || 'organic'), cell(group.relevance.toFixed(4)), cell([...group.engines].sort().join(', ')));
    const actionCell = document.createElement('td');
    if (onSelect) {
      const button = document.createElement('button'); button.className = 'button button-ghost'; button.type = 'button'; button.textContent = 'Details';
      button.addEventListener('click', () => onSelect(group)); actionCell.append(button);
    }
    tr.append(actionCell); target.append(tr);
  });
}

export function renderResultDetail(target, group) {
  if (!target || !group) return;
  const row = group.row || {};
  target.hidden = false;
  target.querySelector('[data-detail="title"]').textContent = row.serp_title || 'Untitled result';
  target.querySelector('[data-detail="kind"]').textContent = row.result_kind || 'organic';
  target.querySelector('[data-detail="engine"]').textContent = [...(group.engines || [])].sort().join(', ') || row.search_engine || 'unknown';
  target.querySelector('[data-detail="relevance"]').textContent = Number(group.relevance || row.relevance || row.relevance_score || 0).toFixed(4);
  target.querySelector('[data-detail="snippet"]').textContent = row.serp_snippet || 'No snippet available.';
  const link = target.querySelector('[data-detail="url"]');
  link.href = row.canonical_url || row.serp_url || '#';
  link.textContent = row.canonical_url || row.serp_url || 'Unavailable';
}

export function renderFailures(target, failures = []) { target.replaceChildren(); failures.forEach(failure => { const item = document.createElement('p'); item.textContent = `${failure.search_engine || 'unknown'} · ${failure.category}: ${failure.message || 'No details'}`; target.append(item); }); }
