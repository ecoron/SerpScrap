import { api } from '../api-client.js';
import { renderTrend } from '../charts.js';

const $ = selector => document.querySelector(selector);
const number = value => new Intl.NumberFormat().format(Number(value || 0));
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const labels = {from:'From', to:'To', query:'Query', provider:'Provider', status:'Status', result_kind:'Result kind', country:'Country', search_type:'Search type'};
let activeRequest;

function fields() {
  return {from:'from', to:'to', query:'filter', provider:'provider', status:'status', result_kind:'kind', country:'country', search_type:'search-type'};
}
function params() {
  return Object.fromEntries(Object.entries(fields()).map(([key, id]) => [key, $(`#history-${id}`)?.value?.trim() || '']).filter(([, value]) => value));
}
function syncUrl(extra = {}) {
  const url = new URL(location.href);
  const next = {...params(), ...extra};
  Object.entries(next).forEach(([key, value]) => value ? url.searchParams.set(key, value) : url.searchParams.delete(key));
  history.replaceState({}, '', url);
}
function restoreUrl() {
  const url = new URL(location.href);
  Object.entries(fields()).forEach(([key, id]) => { const value = url.searchParams.get(key); if (value && $(`#history-${id}`)) $(`#history-${id}`).value = value; });
}
function chips() {
  const root = $('#history-chips');
  if (!root) return;
  root.replaceChildren();
  Object.entries(params()).forEach(([key, value]) => {
    const chip = document.createElement('button');
    chip.className = 'filter-chip'; chip.type = 'button'; chip.title = `Remove ${labels[key] || key} filter`;
    chip.textContent = `${labels[key] || key}: ${value} ×`;
    chip.onclick = () => { const id = fields()[key]; if ($(`#history-${id}`)) $(`#history-${id}`).value = ''; refreshHistoryDashboard(); };
    root.append(chip);
  });
}
function state(root, title, detail, action) {
  if (!root) return;
  const body = `<strong>${esc(title)}</strong><span>${esc(detail)}</span>${action ? `<button class="button button-ghost state-action" type="button">${esc(action.label)}</button>` : ''}`;
  root.innerHTML = root.tagName === 'TBODY' ? `<tr><td colspan="8"><div class="dashboard-state">${body}</div></td></tr>` : `<div class="dashboard-state">${body}</div>`;
  if (action) root.querySelector('.state-action').onclick = action.run;
}
function rows(target, items, columns, empty = 'No data in this scope.') {
  if (!target) return;
  target.innerHTML = items.length ? items.map(item => `<tr>${columns.map(column => `<td>${esc(column(item))}</td>`).join('')}</tr>`).join('') : `<tr><td class="empty-cell" colspan="${columns.length}">${esc(empty)}</td></tr>`;
}
function scopeText(scope) {
  if (!scope) return '';
  const filters = Object.entries(scope.filters || {}).map(([key, value]) => `${labels[key] || key}: ${value}`);
  return `${filters.length ? filters.join(' · ') : 'All history'} · ${scope.interval || 'day'} · ${scope.timezone || 'UTC'} · data ${scope.data_status || 'unknown'}`;
}
function updateScope(scope) {
  document.querySelectorAll('[data-history-scope]').forEach(node => { node.textContent = scopeText(scope); });
  const status = $('#history-live-status');
  if (status) status.textContent = scopeText(scope);
}
async function openRun(run, row) {
  document.querySelectorAll('.history-detail-row').forEach(item => item.remove());
  const detail = document.createElement('tr'); detail.className = 'history-detail-row';
  detail.innerHTML = `<td colspan="6"><div class="inline-run-detail"><div class="workspace-header"><div><p class="eyebrow">Selected run</p><h3>${esc(run.query)}</h3><p class="muted">${number(run.result_count)} results · ${number(run.failure_count)} failures</p></div><button class="button button-ghost" type="button">Close</button></div><div class="history-inline-results" aria-live="polite"></div></div></td>`;
  row.after(detail); detail.querySelector('button').onclick = () => detail.remove();
  const target = detail.querySelector('.history-inline-results'); state(target, 'Loading results', 'Reading the persisted normalized results.');
  try {
    const payload = await api.results(run.id);
    target.innerHTML = payload.results.length ? payload.results.map(result => {
      const url = result.canonical_url || result.serp_url || result.url || result.link || '';
      const title = result.serp_title || result.title || url || 'Untitled result';
      const snippet = result.serp_snippet || result.snippet || result.description || result.summary || result.text || result.content || result.visible_link || 'No snippet available.';
      const domain = result.serp_domain || (() => { try { return new URL(url).hostname; } catch { return 'Unknown domain'; } })();
      return `<article class="result-card"><span class="result-source">${esc(result.search_engine || 'unknown')} · ${esc(domain)}</span><h3>${esc(title)}</h3><a class="result-url" href="${esc(url)}" target="_blank" rel="noreferrer">${esc(url || 'Unavailable')}</a><p class="result-snippet">${esc(snippet)}</p><div class="result-footer"><span class="result-badge">Type ${esc(result.result_kind || 'organic')}</span><span class="result-badge">Rank ${esc(result.serp_rank ?? '—')}</span></div></article>`;
    }).join('') : '<p class="empty-cell">No results persisted for this run.</p>';
  } catch (error) { state(target, 'Results unavailable', error.message, {label:'Retry', run:() => openRun(run, row)}); }
}
async function renderRuns(filters, signal) {
  const root = $('#runs'); state(root, 'Loading runs', 'Applying the current History scope.');
  try {
    const data = await api.history(filters, {signal});
    const runs = (data.searches || []).filter(run => (!filters.from || run.created_at.slice(0,10) >= filters.from) && (!filters.to || run.created_at.slice(0,10) <= filters.to) && (!filters.status || run.status === filters.status) && (!filters.country || run.options?.country_code?.toLowerCase() === filters.country.toLowerCase()) && (!filters.search_type || run.options?.search_type === filters.search_type));
    root.innerHTML = runs.length ? runs.map(run => `<tr data-run-id="${esc(run.id)}"><td>${esc(new Date(run.created_at).toLocaleString())}</td><td>${esc(run.query)}</td><td><span class="status-badge ${esc(run.status)}">${esc(run.status)}</span></td><td>${number(run.result_count)}</td><td>${number(run.failure_count)}</td><td><span class="toolbar-actions"><button class="button button-ghost inspect-run" type="button">Inspect</button><a class="button button-ghost search-again" href="/search?q=${encodeURIComponent(run.query)}">Search again</a></span></td></tr>`).join('') : '<tr><td class="empty-cell" colspan="6">No matching searches. Try clearing a filter or run a search first.</td></tr>';
    root.querySelectorAll('.inspect-run').forEach(button => { const run = runs.find(item => item.id === button.closest('tr').dataset.runId); button.onclick = () => openRun(run, button.closest('tr')); });
    const runId = new URLSearchParams(location.search).get('run'); if (runId) { const row = root.querySelector(`[data-run-id="${CSS.escape(runId)}"]`); const run = runs.find(item => item.id === runId); if (row && run) openRun(run, row); }
  } catch (error) { if (error.name !== 'AbortError') state(root, 'Runs unavailable', error.message, {label:'Retry', run:() => refreshHistoryDashboard()}); }
}
async function renderTrends(filters, signal) {
  const root = $('#trend-chart'); state(root, 'Loading trend', 'Preparing the daily activity view.');
  try {
    const data = await api.timeseries(filters, {signal});
    updateScope(data.scope); renderTrend(root, data.points || [], $('#trend-metric').value);
    rows($('#trend-table'), data.points || [], [point => point.date, point => number(point.searches), point => number(point.results), point => number(point.failures)], data.scope?.data_status === 'empty' ? 'No activity in this scope.' : 'No complete trend data available.');
  } catch (error) { if (error.name !== 'AbortError') state(root, 'Trend unavailable', error.message, {label:'Retry', run:() => refreshHistoryDashboard()}); }
}
async function renderCoverage(filters, signal) {
  const providerRoot = $('#provider-table'), domainRoot = $('#domain-table'); state(providerRoot, 'Loading coverage', 'Aggregating provider results.'); state(domainRoot, 'Loading domains', 'Aggregating canonical domains.');
  try {
    const [providers, queries, domains] = await Promise.all([api.providers(filters, {signal}), api.queries(filters, {signal}), api.domains(filters, {signal})]);
    updateScope(providers.scope); const total = (providers.items || []).reduce((sum, item) => sum + Number(item.result_count || 0), 0);
    rows(providerRoot, providers.items || [], [item => item.name, item => item.state || 'unused', item => number(item.run_count), item => number(item.result_count), item => number(item.failure_count), item => `${total ? (Number(item.result_count || 0) * 100 / total).toFixed(1) : '0.0'}%`]);
    rows($('#query-table'), queries.items || [], [item => item.name, item => number(item.run_count), item => number(item.result_count), item => number(item.failure_count), item => number(item.provider_count)]);
    rows(domainRoot, domains.items || [], [item => item.name, item => number(item.run_count), item => number(item.result_count), item => number(item.provider_count)]);
  } catch (error) { if (error.name !== 'AbortError') { state(providerRoot, 'Coverage unavailable', error.message, {label:'Retry', run:() => refreshHistoryDashboard()}); state(domainRoot, 'Domains unavailable', error.message); } }
}
async function renderCompare(filters, signal) {
  const runs = (await api.history(filters, {signal})).searches || [];
  const left = $('#compare-left'), right = $('#compare-right');
  const options = runs.map(run => `<option value="${esc(run.id)}">${esc(run.query)} · ${esc(new Date(run.created_at).toLocaleString())}</option>`).join('');
  left.innerHTML = right.innerHTML = options;
  const url = new URL(location.href); if (url.searchParams.get('left')) left.value = url.searchParams.get('left'); if (url.searchParams.get('right')) right.value = url.searchParams.get('right');
  const compare = async () => {
    if (!left.value || !right.value) return state($('#compare-summary'), 'Select two runs', 'Choose two persisted runs to compare.');
    syncUrl({left:left.value, right:right.value});
    if (left.value === right.value) return state($('#compare-summary'), 'Choose two different runs', 'A run cannot be compared with itself.');
    state($('#compare-summary'), 'Comparing runs', 'Checking capture context and canonical URLs.');
    try {
      const data = await api.compare(left.value, right.value, {signal}); updateScope(data.scope); const compatible = data.compatibility?.compatible;
      $('#compare-summary').innerHTML = `<div class="compare-compatibility ${compatible ? 'is-compatible' : 'is-incompatible'}"><strong>${compatible ? 'Compatible capture context' : 'Ranking deltas restricted'}</strong><span>${compatible ? 'Rank movements can be interpreted.' : esc((data.compatibility?.differences || []).join(', ') || 'Capture settings differ.')}</span></div>` + Object.entries(data.totals || {}).map(([key,value]) => `<article class="metric-card"><span>${esc(key)}</span><strong>${number(value)}</strong></article>`).join('');
      $('#compare-added').innerHTML = (data.added || []).map(item => `<li><a href="${esc(item.source_url || item.identity)}" target="_blank" rel="noreferrer">${esc(item.source_url || item.identity)}</a><small>New</small></li>`).join('') || '<li>No new URLs.</li>';
      $('#compare-removed').innerHTML = (data.removed || []).map(item => `<li><a href="${esc(item.source_url || item.identity)}" target="_blank" rel="noreferrer">${esc(item.source_url || item.identity)}</a><small>Lost</small></li>`).join('') || '<li>No lost URLs.</li>';
      $('#compare-moved').innerHTML = (data.moved || []).map(item => `<li>${esc(item.identity)} <small>${esc(item.before.rank ?? '—')} → ${esc(item.after.rank ?? '—')}</small></li>`).join('') || '<li>No moved URLs.</li>';
    } catch (error) { if (error.name !== 'AbortError') state($('#compare-summary'), 'Comparison unavailable', error.message, {label:'Retry', run:compare}); }
  };
  $('#compare-submit').onclick = compare; left.onchange = compare; right.onchange = compare; await compare();
}
function updateExportLinks(filters) {
  ['json','csv'].forEach(format => { const link = $(`#history-export-${format}`); if (link) link.href = `/api/v1/history/export?${new URLSearchParams({...filters, format})}`; });
}
export async function refreshHistoryDashboard() {
  if (activeRequest) activeRequest.abort(); activeRequest = new AbortController(); const signal = activeRequest.signal;
  const filters = params(); syncUrl(); chips(); updateExportLinks(filters);
  const view = new URLSearchParams(location.search).get('view') || 'runs';
  document.querySelectorAll('[id^="history-"]:not(.history-filters):not(#history-live-status)').forEach(section => { if (section.tagName === 'SECTION') section.hidden = section.id !== `history-${view}`; });
  document.querySelectorAll('[data-view]').forEach(link => link.classList.toggle('is-active', link.dataset.view === view));
  try { const analytics = await api.analytics(filters, {signal}); updateScope(analytics.scope); document.querySelectorAll('[data-analytics]').forEach(node => { node.textContent = number(analytics[node.dataset.analytics]); }); if (view === 'trends') return renderTrends(filters, signal); if (view === 'coverage') return renderCoverage(filters, signal); if (view === 'compare') return renderCompare(filters, signal); return renderRuns(filters, signal); }
  catch (error) { if (error.name !== 'AbortError') state($('#history-metrics'), 'History unavailable', error.message, {label:'Retry', run:refreshHistoryDashboard}); }
}
export function initHistoryDashboard() {
  restoreUrl();
  ['from','to','status','provider','kind','country','search-type'].forEach(id => $(`#history-${id}`)?.addEventListener('change', refreshHistoryDashboard));
  let debounce; $('#history-filter')?.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(refreshHistoryDashboard, 250); });
  $('#history-reset')?.addEventListener('click', () => { Object.values(fields()).forEach(id => { if ($(`#history-${id}`)) $(`#history-${id}`).value = ''; }); const url = new URL(location.href); ['from','to','query','provider','status','result_kind','country','search_type','left','right'].forEach(key => url.searchParams.delete(key)); history.replaceState({}, '', url); refreshHistoryDashboard(); });
  $('#trend-metric')?.addEventListener('change', refreshHistoryDashboard);
  return refreshHistoryDashboard();
}
