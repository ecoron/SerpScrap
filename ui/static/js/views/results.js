function text(value) { return value == null ? '' : String(value); }

export function groupResults(rows = []) {
  const groups = new Map();
  rows.forEach(row => {
    const url = row.canonical_url || row.serp_url || `result-${groups.size}`;
    const group = groups.get(url) || {row, engines: new Set(), relevance: 0, matches: []};
    group.engines.add(row.search_engine || 'unknown');
    group.relevance = Math.max(group.relevance, Number(row.relevance || row.relevance_score || 0));
    group.matches.push(row);
    if (!group.row.serp_snippet && row.serp_snippet) group.row = row;
    groups.set(url, group);
  });
  return [...groups.values()].sort((a, b) => b.relevance - a.relevance || text(a.row.serp_title).localeCompare(text(b.row.serp_title)));
}

function badge(label, value) {
  const span = document.createElement('span');
  span.className = 'result-badge';
  span.textContent = `${label} ${value}`;
  return span;
}

export function renderResults(target, rows, onSelect, sort = 'relevance') {
  target.replaceChildren();
  const grouped = groupResults(rows);
  if (sort === 'title') grouped.sort((a, b) => text(a.row.serp_title).localeCompare(text(b.row.serp_title)));
  if (sort === 'engine') grouped.sort((a, b) => b.engines.size - a.engines.size || b.relevance - a.relevance);
  if (!grouped.length) {
    const empty = document.createElement('div'); empty.className = 'empty-state';
    const strong = document.createElement('strong'); strong.textContent = 'No results found';
    const hint = document.createElement('span'); hint.textContent = 'Try another query, engine or search type.';
    empty.append(strong, hint); target.append(empty); return;
  }
  grouped.forEach(group => {
    const row = group.row;
    const card = document.createElement('article'); card.className = 'result-card';
    const source = document.createElement('div'); source.className = 'result-source'; source.textContent = `${row.search_engine || 'unknown'} · ${text(row.serp_domain || row.canonical_url || row.serp_url)}`;
    const title = document.createElement('h3');
    const titleLink = document.createElement('a'); titleLink.href = row.canonical_url || row.serp_url || '#'; titleLink.target = '_blank'; titleLink.rel = 'noopener'; titleLink.textContent = row.serp_title || 'Untitled result'; title.append(titleLink);
    const url = document.createElement('div'); url.className = 'result-url'; url.textContent = row.canonical_url || row.serp_url || 'Unavailable';
    const snippet = document.createElement('p'); snippet.className = 'result-snippet'; snippet.textContent = row.serp_snippet || 'No snippet available.';
    const footer = document.createElement('div'); footer.className = 'result-footer';
    footer.append(badge('Relevance', group.relevance.toFixed(4)), badge('Type', row.result_kind || 'organic'), badge('Engines', group.engines.size));
    const details = document.createElement('button'); details.className = 'button button-ghost result-details'; details.type = 'button'; details.textContent = 'Details';
    details.addEventListener('click', () => { target.querySelectorAll('.result-card.is-selected').forEach(item => item.classList.remove('is-selected')); card.classList.add('is-selected'); onSelect?.(group); });
    footer.append(details); card.append(source, title, url, snippet, footer); target.append(card);
  });
}

export function renderResultDetail(target, group) {
  if (!target || !group) return;
  const row = group.row || {};
  target.replaceChildren();
  const header = document.createElement('div'); header.className = 'detail-heading';
  const eyebrow = document.createElement('p'); eyebrow.className = 'eyebrow'; eyebrow.textContent = 'Selected result';
  const title = document.createElement('h3'); title.textContent = row.serp_title || 'Untitled result'; header.append(eyebrow, title);
  const source = document.createElement('p'); source.className = 'detail-source'; source.textContent = `${row.search_engine || 'unknown'} · ${row.serp_domain || 'Unknown domain'}`;
  const snippet = document.createElement('p'); snippet.className = 'detail-snippet'; snippet.textContent = row.serp_snippet || 'No snippet available.';
  const metadata = document.createElement('div'); metadata.className = 'detail-metadata'; metadata.append(badge('Type', row.result_kind || 'organic'), badge('Relevance', Number(group.relevance || 0).toFixed(4)), badge('Engines', [...(group.engines || [])].sort().join(', ')));
  const url = document.createElement('a'); url.className = 'detail-url'; url.href = row.canonical_url || row.serp_url || '#'; url.target = '_blank'; url.rel = 'noopener'; url.textContent = row.canonical_url || row.serp_url || 'Unavailable';
  const action = document.createElement('a'); action.className = 'button button-primary detail-open'; action.href = url.href; action.target = '_blank'; action.rel = 'noopener'; action.textContent = 'Open destination';
  target.append(header, source, snippet, metadata, url, action);
}

export function renderFailures(target, failures = []) { target.replaceChildren(); failures.forEach(failure => { const item = document.createElement('p'); item.textContent = `${failure.search_engine || 'unknown'} · ${failure.category}: ${failure.message || 'No details'}`; target.append(item); }); }
