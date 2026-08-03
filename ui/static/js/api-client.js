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
  analytics: () => request('/history/analytics'),
  history: query => request(`/history/searches${query ? `?query=${encodeURIComponent(query)}` : ''}`),
  results: id => request(`/results?run_id=${encodeURIComponent(id)}&kind=organic`),
  failures: id => request(`/searches/${encodeURIComponent(id)}/failures`),
  status: id => request(`/searches/${encodeURIComponent(id)}`),
  engines: () => request('/engines'),
};
