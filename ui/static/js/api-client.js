const API_ROOT = '/api/v1';

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeout || 30000);
  const externalSignal = options.signal;
  const abortFromCaller = () => controller.abort();
  externalSignal?.addEventListener('abort', abortFromCaller, {once:true});
  try {
    const response = await fetch(`${API_ROOT}${path}`, {
      headers: { Accept: 'application/json', ...(options.body ? {'Content-Type': 'application/json'} : {}) },
      ...options,
      signal: controller.signal,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener('abort', abortFromCaller);
  }
}

export const api = {
  get: path => request(path),
  send: (path, method, body = {}) => request(path, {method, body: JSON.stringify(body)}),
  configuration: () => request('/configuration'),
  analytics: (query, options = {}) => request(`/history/analytics${query ? `?${new URLSearchParams(query)}` : ''}`, options),
  timeseries: (query, options = {}) => request(`/history/timeseries?${new URLSearchParams(query || {})}`, options),
  providers: (query, options = {}) => request(`/history/providers?${new URLSearchParams(query || {})}`, options),
  queries: (query, options = {}) => request(`/history/queries?${new URLSearchParams(query || {})}`, options),
  domains: (query, options = {}) => request(`/history/domains?${new URLSearchParams(query || {})}`, options),
  compare: (left, right, options = {}) => request(`/history/compare?${new URLSearchParams({left, right, ...(options.limit ? {limit: options.limit} : {}), ...(options.offset ? {offset: options.offset} : {})})}`, options),
  exportPreflight: (query, options = {}) => request(`/history/export/preflight?${new URLSearchParams(query || {})}`, options),
  history: (query, options = {}) => request(`/history/searches${query ? `?${new URLSearchParams(query)}` : ''}`, options),
  results: id => request(`/results?run_id=${encodeURIComponent(id)}`),
  failures: id => request(`/searches/${encodeURIComponent(id)}/failures`),
  status: id => request(`/searches/${encodeURIComponent(id)}`),
  engines: () => request('/engines'),
  topics: () => request('/topics'),
  topicSearch: payload => request('/topics/search', {method: 'POST', body: JSON.stringify(payload), timeout: 120000}),
  proxies: () => request('/proxies'),
  refreshProxies: () => request('/proxies/refresh', {method: 'POST', body: '{}', timeout: 130000}),
  testProxies: () => request('/proxies/test', {method: 'POST', body: '{}', timeout: 130000}),
};
