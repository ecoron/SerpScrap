const API_ROOT = '/api/v1';

async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: { Accept: 'application/json', ...(options.body ? {'Content-Type': 'application/json'} : {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

export const api = {
  get: path => request(path),
  send: (path, method, body = {}) => request(path, {method, body: JSON.stringify(body)}),
  configuration: () => request('/configuration'),
  analytics: query => request(`/history/analytics${query ? `?${new URLSearchParams(query)}` : ''}`),
  timeseries: query => request(`/history/timeseries?${new URLSearchParams(query || {})}`),
  providers: query => request(`/history/providers?${new URLSearchParams(query || {})}`),
  queries: query => request(`/history/queries?${new URLSearchParams(query || {})}`),
  domains: query => request(`/history/domains?${new URLSearchParams(query || {})}`),
  compare: (left, right) => request(`/history/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`),
  history: query => request(`/history/searches${query ? `?query=${encodeURIComponent(query)}` : ''}`),
  results: id => request(`/results?run_id=${encodeURIComponent(id)}`),
  failures: id => request(`/searches/${encodeURIComponent(id)}/failures`),
  status: id => request(`/searches/${encodeURIComponent(id)}`),
  engines: () => request('/engines'),
};
