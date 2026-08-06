/** URL-backed, bounded history analytics state shared by views. */
export function historyFilters() {
  const params = new URLSearchParams(location.search);
  return Object.fromEntries(['from', 'to', 'query', 'provider', 'status', 'result_kind', 'country', 'search_type'].filter(key => params.get(key)).map(key => [key, params.get(key)]));
}
export function setHistoryFilter(key, value) {
  const url = new URL(location.href); if (value) url.searchParams.set(key, value); else url.searchParams.delete(key); history.replaceState({}, '', url); return historyFilters();
}
