import { api } from '../api-client.js';
import { notify } from '../notifications.js';

const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
let loaded;
let initialForm;
let initialized = false;

function pathGet(object, path) { return path.split('.').reduce((value, key) => value?.[key], object); }
function pathSet(object, path, value) { const parts = path.split('.'); let target = object; parts.slice(0, -1).forEach(part => { target[part] ??= {}; target = target[part]; }); target[parts.at(-1)] = value; }
function valueText(field) {
  if (field.sensitive) return 'Hidden by policy';
  if (field.type === 'map-number' || field.type === 'json') return JSON.stringify(field.value ?? {}, null, 2);
  if (field.type === 'list-text') return (field.value || []).join(', ');
  return field.value ?? '';
}
function defaultText(field) {
  if (field.sensitive) return 'Hidden';
  if (field.type === 'map-number' || field.type === 'json') return JSON.stringify(field.default ?? {}, null, 2);
  if (field.type === 'list-text') return (field.default || []).join(', ');
  return field.default ?? '—';
}
function isChanged(field) { return JSON.stringify(field.value) !== JSON.stringify(field.default); }
function engineOption(engine, selected, readOnly = false, source = '') {
  const unavailable = engine.readiness !== undefined && engine.readiness !== 'enabled';
  const note = engine.readiness !== undefined
    ? (engine.readiness === 'enabled' ? engine.provider_family || 'Ready' : engine.disable_reason || 'Unavailable')
    : 'Available through SearXNG · no API key';
  return `<label class="engine-option ${unavailable ? 'is-disabled' : ''}"><input type="checkbox" value="${esc(engine.engine_id)}" data-engine-source="${esc(source)}" ${selected?.includes(engine.engine_id) ? 'checked' : ''} ${readOnly || unavailable ? 'disabled' : ''}><span><strong>${esc(engine.display_name || engine.engine_id)}</strong><small>${esc(note)}</small></span></label>`;
}
function renderField(field) {
  const id = `config-${field.key.replaceAll('.', '-')}`;
  const attrs = [`id="${esc(id)}"`, `data-config-key="${esc(field.key)}"`, `aria-describedby="${esc(id)}-help ${esc(id)}-default"`];
  if (field.required) attrs.push('required');
  if (field.min !== undefined) attrs.push(`min="${esc(field.min)}"`);
  if (field.max !== undefined) attrs.push(`max="${esc(field.max)}"`);
  if (field.read_only) attrs.push('disabled', 'aria-readonly="true"');
  let control;
  if (field.type === 'boolean') control = `<input type="checkbox" ${attrs.join(' ')} ${field.value ? 'checked' : ''}>`;
  else if (field.type === 'select') control = `<select ${attrs.join(' ')}>${(field.options || []).map(option => `<option value="${esc(option.value)}" ${String(option.value) === String(field.value) ? 'selected' : ''}>${esc(option.label)}</option>`).join('')}</select>`;
  else if (field.type === 'engine-list') { const options = loaded.engines || []; control = `<div class="config-engine-grid" ${attrs.slice(1).join(' ')}>${options.map(engine => engineOption(engine, field.value, field.read_only, 'direct')).join('')}</div>`; }
  else if (field.type === 'combined-engine-list') {
    const direct = (loaded.engines || []).filter(engine => engine.engine_id !== 'searxng');
    const searxng = loaded.searxng_engines || [];
    const groups = [...new Set(searxng.map(engine => engine.group || 'Other'))];
    const directOptions = direct.map(engine => engineOption(engine, field.value, field.read_only, 'direct')).join('');
    const searxngOptions = groups.map(group => `<h4 class="config-engine-group-title">${esc(group)}</h4>${searxng.filter(engine => (engine.group || 'Other') === group).map(engine => engineOption(engine, loaded.configuration.searxng_engines, field.read_only, 'searxng')).join('')}`).join('');
    control = `<div class="config-engine-grid config-combined-engine-grid" ${attrs.slice(1).join(' ')}><h4 class="config-engine-group-title config-engine-section-title">SerpScrap engines</h4>${directOptions}<h4 class="config-engine-group-title config-engine-section-title">SearXNG engines</h4>${searxngOptions}</div>`;
  }
  else if (field.type === 'map-number' || field.type === 'json') control = `<textarea class="config-control config-code" rows="4" ${attrs.join(' ')}>${esc(valueText(field))}</textarea>`;
  else control = `<input class="config-control" type="${field.type === 'url' ? 'url' : field.type === 'number' ? 'number' : 'text'}" value="${esc(valueText(field))}" ${attrs.join(' ')}>`;
  return `<div class="config-field ${field.read_only ? 'is-readonly' : ''}" data-field-wrapper="${esc(field.key)}"><label for="${esc(id)}"><span class="config-label">${esc(field.label)}${field.read_only ? ' <em>Read-only</em>' : ''}</span>${control}<small id="${esc(id)}-help" class="config-help">${esc(field.description)}</small><small id="${esc(id)}-default" class="config-default">Default: ${esc(defaultText(field))}${isChanged(field) ? ' · Changed from default' : ''}</small><small class="config-error" data-error-for="${esc(field.key)}" hidden></small></label></div>`;
}
function render() {
  const root = $('#configuration-groups'); root.replaceChildren();
  loaded.groups.forEach(group => {
    const details = document.createElement('details'); details.className = 'configuration-group'; details.open = Boolean(group.expanded);
    const fields = loaded.fields.filter(field => field.group === group.id && field.key !== 'searxng_engines');
    details.innerHTML = `<summary><span><strong>${esc(group.title)}</strong><small>${esc(group.description)}</small></span><span class="configuration-group-count">${fields.length} settings</span></summary><div class="configuration-group-body">${fields.map(renderField).join('')}</div>`;
    root.append(details);
  });
  initialForm = serialize(); updateDirty();
}
function serialize() {
  const result = structuredClone(loaded.configuration);
  document.querySelectorAll('[data-config-key]').forEach(control => {
    const key = control.dataset.configKey;
    if (control.disabled && control.type !== 'checkbox') return;
    if (control.classList.contains('config-engine-grid')) return;
    let value;
    if (control.type === 'checkbox' && control.closest('.config-engine-grid')) return;
    if (control.type === 'checkbox') value = control.checked;
    else if (control.classList.contains('config-code')) { try { value = JSON.parse(control.value); } catch { value = control.value; } }
    else if (control.type === 'number') value = control.value === '' ? '' : Number(control.value);
    else if (control.tagName === 'TEXTAREA' && control.dataset.configKey.includes('retryable')) value = control.value.split(',').map(item => item.trim()).filter(Boolean);
    else value = control.value;
    pathSet(result, key, value);
  });
  const engines = [...document.querySelectorAll('.config-combined-engine-grid input[data-engine-source="direct"]:checked')].map(input => input.value);
  const searxngEnabled = Boolean(result.searxng_enabled);
  if (searxngEnabled) engines.push('searxng');
  if (engines.length) result.search_engines = engines;
  result.searxng_engines = [...document.querySelectorAll('.config-combined-engine-grid input[data-engine-source="searxng"]:checked')].map(input => input.value);
  return result;
}
function updateDirty() {
  const dirty = JSON.stringify(serialize()) !== JSON.stringify(initialForm);
  $('#config-dirty-label').textContent = dirty ? 'Unsaved changes' : 'No unsaved changes';
  $('#config-dirty-label').classList.toggle('is-dirty', dirty);
  $('#save-config').disabled = !dirty;
}
function showErrors(message, fieldKeys = []) {
  fieldKeys.forEach(key => document.querySelector(`[data-field-wrapper="${CSS.escape(key)}"]`)?.closest('details')?.setAttribute('open', ''));
  const summary = $('#config-error-summary'); summary.textContent = message; summary.hidden = false;
  document.querySelectorAll('[data-error-for]').forEach(node => { const visible = fieldKeys.includes(node.dataset.errorFor); node.hidden = !visible; if (visible) node.textContent = message; });
  const target = fieldKeys[0] && document.querySelector(`[data-config-key="${CSS.escape(fieldKeys[0])}"]`); target?.focus();
}
function clearErrors() { $('#config-error-summary').hidden = true; document.querySelectorAll('[data-error-for]').forEach(node => { node.hidden = true; node.textContent = ''; }); }
function populateFromResponse(response) { loaded = response; $('#config-source').textContent = `${response.source === 'persisted' ? 'Saved override' : 'Initial defaults'} · revision ${response.revision}${response.updated_at ? ` · updated ${new Date(response.updated_at).toLocaleString()}` : ''}`; $('#config-scope-label').textContent = 'Applies to new searches only.'; render(); }
async function save(event) { event.preventDefault(); clearErrors(); const payload = serialize(); if (!payload.search_engines?.length) return showErrors('Select at least one search engine.', ['search_engines']); try { const response = await api.send('/configuration', 'PUT', payload); populateFromResponse(response); notify(`Configuration revision ${response.revision} saved.`); } catch (error) { const message = error.message || 'Configuration could not be saved.'; const fields = message.includes('proxy_file or proxy_sources') ? ['use_own_ip', 'proxy_sources'] : []; showErrors(message, fields); notify(message, 'error'); } }
async function resetDefaults() { if (!window.confirm('Reset all configuration settings to the initial SerpScrap defaults?')) return; try { populateFromResponse(await api.send('/configuration/reset', 'POST')); notify('Initial defaults restored.'); } catch (error) { showErrors(error.message || 'Defaults could not be restored.'); } }
async function load() { try { populateFromResponse(await api.configuration()); } catch (error) { $('#config-source').textContent = 'Configuration unavailable'; showErrors(error.message || 'Configuration could not be loaded.'); } }
function renderProxyStatus(status) { const root = $('#proxy-status'); if (!root) return; if (!status.enabled) { root.textContent = 'Proxy use is disabled. Enable proxy_enabled or disable use_own_ip to activate it.'; return; } const summary = status.summary || {}; const rows = (status.proxies || []).map(proxy => `<tr><td><code>${esc(proxy.endpoint)}</code></td><td class="proxy-source">${esc(proxy.source || '—')}</td><td><span class="proxy-status-badge ${proxy.online ? 'is-online' : 'is-offline'}"><span class="proxy-status-dot"></span>${proxy.online ? 'Healthy' : 'Offline'}</span></td><td>${proxy.latency_ms == null ? '—' : `${Number(proxy.latency_ms).toFixed(1)} ms`}</td><td>${Number(proxy.failure_count || 0)}</td><td>${esc(proxy.last_error || '—')}</td></tr>`).join(''); root.innerHTML = `<div class="proxy-summary-line"><p><strong>${summary.healthy || 0}</strong> healthy · <strong>${summary.offline || 0}</strong> offline · ${summary.total || 0} total</p></div><details class="proxy-list" open><summary>Proxy entries <span>${summary.total || 0}</span></summary><div class="table-scroll"><table><thead><tr><th>Endpoint</th><th>Source</th><th>Status</th><th>Latency</th><th>Failures</th><th>Last error</th></tr></thead><tbody>${rows || '<tr><td colspan="6">No proxies configured.</td></tr>'}</tbody></table></div></details>`; }
async function loadProxyStatus() { try { renderProxyStatus(await api.proxies()); } catch (error) { $('#proxy-status').textContent = error.message || 'Proxy status unavailable.'; } }
async function runProxyAction(button, action, successMessage, failureMessage) {
  if (!button || button.disabled) return;
  const original = button.textContent;
  button.disabled = true;
  button.textContent = 'Checking proxies…';
  try { renderProxyStatus(await action()); notify(successMessage); }
  catch (error) { notify(error.message || failureMessage, 'error'); }
  finally { button.disabled = false; button.textContent = original; }
}
async function testProxies() { return runProxyAction($('#test-proxies'), () => api.testProxies(), 'Proxy test completed.', 'Proxy test failed.'); }
async function refreshProxies() { return runProxyAction($('#refresh-proxies'), () => api.refreshProxies(), 'Proxy health refreshed and saved.', 'Proxy refresh failed.'); }
export function initConfigurationPage() {
  if (!initialized) {
    $('#config-form')?.addEventListener('submit', save);
    $('#reset-config')?.addEventListener('click', resetDefaults);
    $('#reset-changes')?.addEventListener('click', () => { if (loaded) { render(); notify('Unsaved changes discarded.'); } });
    $('#configuration-groups')?.addEventListener('input', updateDirty);
    $('#configuration-groups')?.addEventListener('change', updateDirty);
    $('#test-proxies')?.addEventListener('click', testProxies);
    $('#refresh-proxies')?.addEventListener('click', refreshProxies);
    window.addEventListener('beforeunload', event => { if ($('#config-dirty-label')?.classList.contains('is-dirty')) { event.preventDefault(); event.returnValue = ''; } });
    initialized = true;
  }
  return load().then(loadProxyStatus);
}
