const state = { view: 'overview', activeRunId: null, historicalRunId: null, configuration: null, history: [], analytics: null };
const listeners = new Set();

export function getState() { return state; }
export function setState(patch) { Object.assign(state, patch); listeners.forEach(listener => listener(state)); }
export function subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); }
