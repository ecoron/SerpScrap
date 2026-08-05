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
  analytics: (query, options = {}) => request(`/history/analytics${query ? `?${new URLSearchParams(query)}` : ''}`, options),
  timeseries: (query, options = {}) => request(`/history/timeseries?${new URLSearchParams(query || {})}`, options),
  providers: (query, options = {}) => request(`/history/providers?${new URLSearchParams(query || {})}`, options),
  queries: (query, options = {}) => request(`/history/queries?${new URLSearchParams(query || {})}`, options),
  domains: (query, options = {}) => request(`/history/domains?${new URLSearchParams(query || {})}`, options),
  compare: (left, right, options = {}) => request(`/history/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`, options),
  history: (query, options = {}) => request(`/history/searches${query ? `?${new URLSearchParams(query)}` : ''}`, options),
  results: id => request(`/results?run_id=${encodeURIComponent(id)}`),
  failures: id => request(`/searches/${encodeURIComponent(id)}/failures`),
  status: id => request(`/searches/${encodeURIComponent(id)}`),
  engines: () => request('/engines'),
};
