```{eval-rst}
:orphan:
```

# Alpha 2.0.0 UI – History & Analysis Expansion

## Status

Implementation planned. This document defines the next UI/API increment for
the History & analysis workspace after the Alpha 2.0.0 homepage improvements.
No provider network search is required for the deterministic test suite.

## Implementation Status

- [x] Define the analytics contract and time-filter semantics
- [x] Add time-series, provider, query, domain, and comparison API views
- [x] Add history filters, run selection, charts, and drill-down navigation
- [x] Add canonical result diffs, bounded exports, accessible alternatives, and deep links
- [x] Add deterministic API/UI tests; browser visual smoke remains opt-in
- [x] Update user/developer documentation and record delivery in `CHANGELOG.md`

## Objective

Turn History & analysis from a searchable run archive into an explainable
research-analysis workspace. Users should be able to answer four questions
without exporting data first:

1. What did we search and when?
2. Which providers and domains contributed useful results?
3. What changed between two runs?
4. Where are failures, coverage gaps, or notable SERP changes?

The UI remains a client of the versioned API. Aggregation, comparison,
pagination, and data-scope decisions belong to the API/service layer; the
browser is responsible for interaction, presentation, and local view state.

## Research Findings

The `mcp-serpscrap` research covered SERP scraping use cases, SERP history
dashboards, ranking-monitoring tools, and analytics-dashboard UX. The results
consistently point to these use cases:

- rank and visibility monitoring over repeated searches;
- competitor and domain analysis;
- content-gap and query-discovery research;
- provider, regional, and result-type comparison;
- SERP change/volatility monitoring;
- provider-quality and failure monitoring;
- scheduled checks, exports, alerts, and downstream reporting.

Common presentation patterns are KPI cards, date-range filters, activity
time-series, provider bars, query/provider heatmaps, ranking distributions,
domain tables, side-by-side comparisons, and drill-down detail panels. The
research also emphasizes that filters, comparison periods, and chart values
must be explicit, while charts need accessible tabular alternatives.

Research references:

- [Web Scraping for SEO](https://use-apify.com/blog/web-scraping-for-seo-guide)
- [SEO & SERP Web Scraping](https://scrapfly.io/use-case/seo-and-serp-web-scraping)
- [SERP Monitoring Tools](https://visualping.io/blog/best-serp-monitoring-tools)
- [SEO SERP Tracking Dashboard](https://portermetrics.com/en/examples/seo-serp-tracking-porter-example/)
- [Dashboard Filter Design](https://www.aufaitux.com/blog/dashboard-filter-design-guide/)

## Product Scope

### In scope

- time-filtered history metrics and activity trends;
- provider, query, domain, and result-kind aggregations;
- multi-run comparison and normalized-result diffs;
- filterable, deep-linkable analysis views;
- CSV/JSON export of bounded, filtered data;
- accessible tables behind every visualization;
- explicit empty, partial, stale, and failed analytics states.

### Deferred

- automatic query clustering or AI-generated narratives;
- backlink crawling and page-content auditing;
- scheduled jobs and notifications;
- external integrations such as Google Search Console;
- geographic grids beyond the existing country-code contract;
- unbounded raw-provider or diagnostic-data exploration.

## Proposed Information Architecture

History remains the entry point and gains four analysis modes:

1. **Runs** – searchable archive with status, query, date, engines, results,
   failures, duration, and selection controls.
2. **Trends** – searches, normalized results, failures, and success rate over
   a selected time range.
3. **Coverage** – provider, query, result-kind, and domain distributions.
4. **Compare** – two or more selected runs with overlap, additions,
   removals, ranking changes, and provider differences.

The selected mode, date range, filters, sort, and run IDs must be represented
in the URL so that a view can be refreshed or shared safely:

```text
/history?view=trends&from=2026-07-01&to=2026-08-05
/history?view=coverage&provider=bing
/history?view=compare&left=run-a&right=run-b
```

## Functional Design

### Summary cards

Add time-scoped cards for searches, normalized results, failures, active
providers, average results per run, success rate, and last activity. Each card
must show its scope (`7 days`, `30 days`, or `All time`) and link to a filtered
view where meaningful.

### Filters

Provide a compact filter bar with date range, query, status, provider, result
kind, country, and search type. Active filters render as removable chips.
Reset must restore the default scope without losing the selected view.

### Trends

Start with a lightweight SVG or CSS chart for daily searches, results, and
failures. Provide metric switching, comparison to the previous period, and a
tabular equivalent with exact values. Missing days must be represented as zero
or explicitly labelled as unavailable; they must never be silently omitted.

### Provider coverage

Show enabled and unavailable providers, result volume, run coverage, failure
count/rate, and average best rank where ranking data exists. Providers with no
results remain visible and explain whether they were unused, empty, or failed.

### Query and domain views

The query view ranks queries by run count, result volume, failure rate, and
provider coverage. The domain view ranks canonical domains by appearances,
queries, best rank, and provider count. Both views drill down to filtered runs
or results.

### Run comparison

Allow two runs initially; add multi-run comparison only after the two-run
contract is stable. Show shared URLs, added URLs, removed URLs, rank changes,
domain changes, and provider overlap. Every difference must retain provenance
to the originating run and provider.

### Export and deletion

Exports use the current filters and are bounded by server-side limits. The
export scope is shown before download. Existing deletion safeguards remain in
place and must refresh all affected cards, charts, tables, and selections.

## API Contract Extensions

Prefer additive, versioned endpoints or query parameters:

```text
GET /api/v1/history/analytics?from=&to=&query=&provider=&status=
GET /api/v1/history/timeseries?interval=day&metric=results&from=&to=
GET /api/v1/history/providers?from=&to=&query=
GET /api/v1/history/queries?from=&to=&provider=
GET /api/v1/history/domains?from=&to=&query=
GET /api/v1/history/compare?left=&right=&limit=&offset=
GET /api/v1/history/export?format=csv&...filters
```

Every response must include the applied scope, pagination totals where
relevant, and a schema version. Aggregates must document whether counts are
run-scoped, result-scoped, provider-attributed, or deduplicated. This avoids
confusing a normalized-result total with the sum of provider attributions.

The service must use bounded parameters, deterministic ordering, safe query
filters, and existing repository abstractions. No UI-only aggregation should
become the source of truth for metrics used in exports or comparisons.

## Technical Direction

Keep Flask/Jinja, native ES modules, and the existing design-token CSS system.
Add focused modules rather than expanding the existing monolithic page logic:

```text
ui/static/js/
  analytics.js
  charts.js
  views/history.js
  views/history-trends.js
  views/history-coverage.js
  views/history-compare.js
```

Use native SVG/CSS first. A chart library is only justified if accessibility,
interaction, or maintenance requirements cannot be met with local modules.
Charts must expose an adjacent table, labelled axes, focusable data points
where practical, and reduced-motion behavior.

## Implementation Slices

1. **Contract and semantics** – inventory current history/result models; define
   time zones, date inclusivity, attribution, deduplication, failure rate,
   ranking availability, bounds, schema examples, and empty-state semantics.
2. **Analytics service** – implement time-filtered summaries, timeseries,
   provider/query/domain aggregates, deterministic ordering, and API tests.
3. **History foundation** – add URL-backed view state, date/filter controls,
   active-filter chips, run selection, loading/error/partial states, and
   responsive table behavior.
4. **Trends and coverage** – add summary cards, activity trend, provider
   table/chart, query/domain tables, drill-down links, and accessible table
   alternatives.
5. **Comparison** – implement two-run selection, overlap/diff API, result
   diff presentation, provider/domain changes, and deep links.
6. **Export and hardening** – add bounded CSV/JSON export, deletion refresh,
   keyboard/accessibility checks, responsive review, and visual smoke evidence.
7. **Documentation and release evidence** – update user/developer docs,
   examples, API schemas, tests, and `CHANGELOG.md` for each delivered slice.

## Acceptance Criteria

- Users can filter History & analysis by date, query, provider, status, and
  result kind without a full page reload.
- Summary metrics clearly state their scope and aggregation semantics.
- Trends, provider coverage, query, and domain views have exact tabular
  alternatives and accessible labels.
- Provider entries with zero results or failures are distinguishable from
  providers that were not selected.
- Two runs can be compared with deterministic shared/added/removed results
  and provenance-preserving details.
- Chart/table drill-downs preserve the active filters and use deep links.
- Exports are bounded, filtered, reproducible, and show their scope.
- Empty, loading, partial, stale, failed, and deleted-data states are tested.
- API, UI, and browser smoke tests pass without live provider searches.
- Documentation, implementation status, API behavior, and `CHANGELOG.md`
  describe the same delivered scope.

## Risks and Open Decisions

- Existing history data may not contain enough snapshots for meaningful trend
  analysis; the UI must show insufficient-history messaging instead of
  inventing a trend.
- Provider-attributed result counts can overlap after fusion; labels must
  distinguish attributed counts from deduplicated normalized totals.
- Ranking comparisons are only valid when query, country, search type, page
  depth, and provider set are compatible; incompatible runs must be flagged.
- Large archives may require server-side aggregation, caching, or indexes
  before charts are enabled by default.
- Export and comparison endpoints must not expose unbounded snippets,
  diagnostics, credentials, cookies, or other sensitive runtime data.
