/** Accessible dependency-free SVG trend chart; the table remains the source of exact values. */
export function renderTrend(root, points, metric = 'results') {
  root.replaceChildren(); root.setAttribute('role', 'img'); root.setAttribute('aria-label', `${metric} per day`);
  const max = Math.max(1, ...points.map(point => Number(point[metric] || 0))); const line = points.map((point, index) => `${index * 100 / Math.max(1, points.length - 1)},${100 - Number(point[metric] || 0) * 90 / max}`).join(' ');
  root.innerHTML = `<svg viewBox="0 0 100 100" preserveAspectRatio="none"><polyline points="${line}" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`;
}
