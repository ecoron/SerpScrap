```{eval-rst}
:orphan:
```

# Alpha 2.0.0 UI Development Plan

## Status

This document is the implementation plan for the next History & analysis UI
increment. It is based on the requirements in `docs/alpha-2.0.0-ui.md`, the
current Flask/Jinja and native ES-module implementation, and live capability
checks against the `mcp-serpscrap` MCP server on 2026-08-05.

The plan is implementation-ready. It deliberately separates questions that
SerpScrap can answer from questions that require persisted history or new
analysis semantics.

## Capability Assessment

### Research method

Four representative questions were submitted through `start_search`, using
the `bing` engine, country code `DE`, one page, and ten results. Each job was
polled with `get_search_status` and its normalized rows were read with
`list_results`.

| User question | Current answerability | Evidence available | Required UI treatment |
| --- | --- | --- | --- |
| What are the current top results and which domains appear? | Yes, for the selected run | `serp_rank`, `canonical_url`, `serp_domain`, title, snippet, `result_kind`, provider, country | Result list with rank, canonical domain, type, provider, and a domain drill-down |
| How did results change between two runs? | Partly | Results are persisted and have stable canonical URLs; a single search job cannot establish a time comparison | Two-run comparison view with compatibility warnings and added/removed/shared rows |
| Which providers returned useful results and which failed? | Yes, when multiple providers are selected | Provider attribution, result count, run status, and failure category/correlation data | Provider coverage table with separate unused, empty, failed, and successful states |
| What content gaps and related queries can be identified? | Heuristic only | Titles, snippets, domains, result kinds, and query text; no reliable keyword volume, PAA, related-query, or site-inventory data | Label as SERP signals, not a definitive gap report; defer clustering and external site comparison |

The server configuration currently exposes multiple providers, but the
research run was intentionally bounded to one provider for deterministic
validation. Multi-provider UI claims must therefore use persisted runs whose
provider set is visible in the scope. The engine registry also reports
disabled providers and provider readiness, which must be reflected in the
configuration and coverage surfaces rather than inferred from result counts.

## Best-Practice Review

The plan was checked against three additional bounded `mcp-serpscrap` research
runs covering analytics API/time-series design, SERP snapshot comparison, and
accessible dashboard states. One search-history dashboard query was blocked by
the provider; that failure is itself relevant because the UI must expose a
provider failure rather than silently presenting an empty result.

| Area | Best-practice pattern | Plan status | Required refinement |
| --- | --- | --- | --- |
| Analytics API | Return scope, time granularity, timezone, freshness, and aggregation semantics | Partly covered | Make these mandatory in every analytics response and export |
| Filters | Group controls, preserve active filters, debounce free text, make reset obvious | Covered, but underspecified | Add filter groups, 250 ms debounce, cancellation, and scope announcement |
| Time series | Declare interval, deterministic buckets, missing-data policy, exact table values | Covered | Add interval, coverage bounds, freshness, and data status |
| SERP comparison | Check identical capture context before classifying ranking changes | Partly covered | Add compatibility fingerprint and URL/domain change classifications |
| Ranking identity | Normalize canonical URLs while retaining the provider URL | Covered | Version normalization with `identity_key_version` |
| Dashboard states | Standardize loading, empty, partial, stale, timeout, and failure states | Covered, but underspecified | Define one reusable component and state-specific actions |
| Accessible charts | Pair charts with labelled tables and non-color distinctions | Covered | Add automated table-parity, focus, and color-independence checks |
| Export | Show scope, generation time, schema, limit, and ordering | Partly covered | Add visible preflight and reproducibility manifest |

Discovery references returned by the MCP runs:

- [Google Cloud time-series aggregation](https://docs.cloud.google.com/monitoring/api/v3/aggregation)
- [Analytics dashboard API best practices](https://developer.loopwork.co/docs/best-practices-for-building-your-analytics-dashboard)
- [Dashboard filter design](https://www.aufaitux.com/blog/dashboard-filter-design-guide/)
- [SERP snapshot comparison](https://dev.to/talordata_elowen/how-to-compare-two-serp-snapshots-and-detect-ranking-changes-1aij)
- [Canonical URL guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [SERP monitoring patterns](https://nightwatch.io/blog/serp-monitoring/)
- [Accessible dashboard guidance](https://help.tableau.com/current/pro/desktop/en-us/accessibility_dashboards.htm)

These references reinforce the existing direction but do not justify adding a
third-party charting or analytics library. Native SVG, HTML tables, and the
existing service layer remain the default.

### Product conclusions

1. The primary value of Alpha 2.0.0 is explainable evidence: every metric,
   chart point, and comparison row must link back to a run and provider.
2. `canonical_url` is the comparison key; provider redirect URLs and visible
   links are provenance fields, not identity keys.
3. Result-type coverage must remain visible. The research returned both
   organic and image rows, so filtering to organic rows would hide meaningful
   SERP changes.
4. A successful job with zero rows is different from a failed provider. The
   UI needs explicit state labels and failure categories.
5. Content-gap recommendations cannot be presented as a native answer until
   the service has query expansion, site inventory, or SERP-feature contracts.

## Current Baseline to Preserve

The implementation must extend, not replace, the current architecture:

- `serpscrap/history_store.py` owns persisted runs, result normalization,
  analytics, aggregates, comparison, and bounded export.
- `serpscrap/api_service.py` and `serpscrap/api_server.py` expose the versioned
  API consumed by the UI.
- `ui/templates/pages/history.html` remains the History entry point.
- `ui/static/js/analytics.js` owns URL-backed filters, while
  `ui/static/js/views/history.js` renders runs, trends, coverage, and compare.
- `ui/static/js/charts.js` provides the dependency-free SVG chart and the
  adjacent table remains the exact-value source.
- Existing deletion safeguards, same-origin proxy behavior, and normalized
  result fallbacks must remain intact.

Before implementation, inventory the exact response shapes and add schema
examples to the API tests. Do not introduce a client-side aggregate as the
source of truth for an export or comparison.

## Target Information Architecture

History has four URL-addressable modes:

1. **Runs**: searchable archive, status, query, timestamps, provider scope,
   result/failure counts, inspect, search again, and run selection.
2. **Trends**: scoped KPI cards and daily searches, results, failures, and
   success-rate values.
3. **Coverage**: provider, result-kind, query, and canonical-domain views.
4. **Compare**: two compatible runs, shared/added/removed results, rank and
   provider changes, and provenance details.

The URL is the shareable view model. At minimum, preserve `view`, `from`,
`to`, `query`, `provider`, `status`, `result_kind`, `country`, `search_type`,
`left`, and `right`. Reset removes filter parameters but keeps `view`.

## Detailed Functional Requirements

### Scope and filters

- Use inclusive ISO dates in the persisted run timezone, normalized to UTC for
  storage and rendered in the user's locale.
- Group controls into **Time** (date range), **Search context** (country,
  search type, provider), and **Result context** (query, status, result kind).
- Support date range, query, provider, status, result kind, country, and
  search type. The API must apply all filters; the Runs table must not be the
  only filtered surface.
- Debounce free-text query changes by 250 ms and cancel superseded requests.
  Announce the updated scope in a polite live region without stealing focus.
- Render every active filter as a removable chip and expose a single reset
  action.
- Show the applied scope, data freshness, and interval above every card, table,
  chart, and export action.
- Add loading, empty, partial, stale, failed, and deleted-data states with
  actionable text and no misleading zero values.

### Summary cards

Implement cards for searches, normalized results, failures, active providers,
average results per run, success rate, and last activity. Each card must
include its aggregation scope and a link to the most relevant filtered view.
Counts must identify whether they are run-scoped, deduplicated result-scoped,
or provider-attributed.

### Trends

- Add metric selection for searches, results, failures, and success rate.
- Declare the selected `interval` and timezone in the response and UI. The
  first release supports `day`; intervals must never be mixed silently.
- Fill missing days with zero only when the archive is known to cover the
  requested interval; otherwise show an unavailable marker.
- Include `coverage_start`, `coverage_end`, and `data_status` so the UI can
  distinguish no activity from incomplete collection.
- Add previous-period comparison only when both periods have sufficient data.
- Keep the SVG chart keyboard-safe and provide a labelled table with exact
  dates and values beside or below it.
- Respect `prefers-reduced-motion`; no animation is required for the first
  delivery.

### Coverage, queries, and domains

- Provider rows show selected/enabled state, run count, attributed result
  count, failure count/rate, and the reason for zero results.
- Result-kind rows distinguish organic, image, news, shopping, video, and
  other normalized kinds.
- Query rows show run count, result count, failure rate, and provider count.
- Domain rows use canonical host/domain extraction and show appearances,
  queries, best rank when available, and provider count.
- Each row has a drill-down link that preserves the active filters and adds
  the selected provider, query, domain, or result kind.
- Do not call a domain a competitor or a content gap without a user-provided
  site/domain baseline. The Alpha UI may expose “SERP domain signal” only.

### Two-run comparison

- Start with exactly two runs. Require different run IDs and show both query
  and capture scope in the selector.
- Reject or visibly warn on incompatible query, country, search type, page
  depth, provider set, or result-kind scopes. Ranking deltas are not valid
  across incompatible scopes. Compute and display a compatibility fingerprint
  before allowing rank deltas.
- Compare by canonical URL and retain left/right run IDs, provider, rank,
  result kind, title, and snippet provenance in every row.
- Show `stable`, `moved`, `new`, and `lost` URL totals. Add a separate domain
  summary with `entered`, `exited`, and `rank_changed` classifications. A
  missing rank is shown as unavailable, never as zero.
- Add provider overlap and domain movement after the base URL diff is stable.
- Encode `left` and `right` in the URL and restore them on refresh.

### Export and deletion refresh

- Export the current server-applied scope only, with a visible row limit and
  format (`CSV` or `JSON`) before download.
- Show an export preflight containing filters, interval, timezone, freshness,
  row limit, format, and estimated row count.
- Use deterministic ordering matching the visible table and include schema
  version, scope metadata, generation timestamp, and `identity_key_version`.
- Never export credentials, cookies, diagnostic HTML, or unbounded snippets.
- After deleting a run, refresh cards, charts, tables, compare selections,
  chips, and any deep-linked selection. A deleted selection must become an
  explicit empty state.

## API and Data Contract Work

Implement or verify additive `/api/v1/history/*` contracts:

```text
GET /history/analytics
GET /history/timeseries
GET /history/providers
GET /history/queries
GET /history/domains
GET /history/compare?left=&right=&limit=&offset=
GET /history/export?format=csv|json&...filters
```

Every payload must include `schema_version`, `scope`, and an explicit
`semantics` object. `scope` must contain normalized filters, timezone, interval,
coverage bounds, freshness timestamp, and `data_status`. Aggregate payloads
must include bounded totals and stable ordering. Comparison payloads must
include compatibility metadata, a fingerprint, change classifications, and
provenance-preserving rows. Validate date, pagination, filter lengths, run-ID
format, and export limits at the API boundary.

Canonical identity must be versioned. `identity_key_version=1` should strip
provider redirect wrappers, normalize scheme/host casing, remove fragments,
and apply the repository's existing trailing-slash/query normalization rules.
The original `source_url` remains untouched for provenance. Any normalization
that could merge distinct resources requires a fixture before the version is
changed.

Add a separate future contract note for query expansion, SERP features, and
site inventory. Do not implement AI narratives, automatic query clustering,
or authoritative content-gap scoring in this increment.

## Implementation Slices

### Slice 1: Contract and fixtures

- Document date inclusivity, timezone conversion, attribution,
  deduplication, failure-rate denominator, ranking availability, and empty
  state semantics.
- Add deterministic fixtures containing multiple providers, duplicate
  canonical URLs, organic and non-organic kinds, zero-result providers, and
  failures with categories.
- Add response schema examples and compatibility cases.
- Add scope/freshness/interval fixtures, normalization collision fixtures, and
  canonical identity version assertions.

### Slice 2: Service and API

- Complete server-side filtering for every History endpoint.
- Implement or harden timeseries, provider/query/domain aggregates,
  compatibility-aware comparison, pagination, and bounded export.
- Keep ordering deterministic and preserve existing repository abstractions.

### Slice 3: History foundation

- Refine `analytics.js` and `views/history.js` into focused view-state and
  rendering helpers without duplicating API semantics.
- Add URL restoration for all filters and both compare IDs.
- Add unified status components for loading, partial, stale, failed, empty,
  and unavailable data.
- Implement grouped filters, 250 ms query debounce, request cancellation,
  polite scope announcements, and a shared state component with recovery
  actions (`Retry`, `Clear filters`, or `Inspect failures`).

### Slice 4: Trends and coverage

- Add scoped cards, metric switching, previous-period state, SVG chart/table,
  provider and result-kind coverage, query/domain tables, and drill-downs.
- Add responsive table/card layouts and accessible names, descriptions,
  focus order, and keyboard actions.

### Slice 5: Comparison

- Add compatible two-run selection, URL state, summary totals, diff tables,
  provider/domain changes, and provenance detail panel.
- Add the compatibility fingerprint gate and stable/moved/new/lost
  classifications before exposing any rank-delta chart.
- Test same-run, incompatible-run, missing-rank, deleted-run, and no-overlap
  states.

### Slice 6: Export and hardening

- Add scoped CSV/JSON controls, server-limit messaging, deletion refresh,
  reduced-motion behavior, responsive review, and browser smoke evidence.
- Verify that every chart has an equivalent table and every drill-down keeps
  the scope.
- Add export preflight, manifest metadata, focus-visible review,
  color-independent status indicators, and a performance budget for filtered
  dashboard refreshes.

### Slice 7: Documentation and release evidence

- Update `docs/alpha-2.0.0-ui.md` status checkboxes as slices land.
- Keep this plan, API behavior, user documentation, tests, and
  `CHANGELOG.md` synchronized.

## Test Plan

All tests must run through Pipenv and must not require live provider searches.

### Service and API tests

- Filter intersection and inclusive date boundaries.
- UTC persistence and local rendering scope.
- Run-scoped versus provider-attributed versus deduplicated counts.
- Missing days, insufficient history, partial provider failure, and zero
  results.
- Provider/query/domain deterministic ordering and pagination bounds.
- Compare shared/added/removed URLs, rank changes, incompatible scopes,
  duplicate canonical URLs, and missing ranks.
- Export scope, row limit, schema version, stable ordering, and sensitive-field
  exclusion, plus export manifest and identity-key version.
- Deletion refresh data and deleted compare IDs.
- Scope freshness, interval, timezone, coverage bounds, and stale/partial
  status are present and consistent across endpoints.
- URL normalization is deterministic and does not merge protected collision
  fixtures.

### UI and browser tests

- URL restoration, filter chips, reset behavior, and view navigation.
- Grouped filter interaction, debounced query input, request cancellation, and
  polite scope announcements.
- Exact table alternatives for trend and coverage visualizations.
- Accessible labels, keyboard operation, focus order, reduced motion, and
  responsive layout behavior.
- Loading, empty, partial, stale, failed, unavailable, and deleted states.
- Deep links for run inspection, coverage drill-down, and comparison.
- Comparison compatibility gate and stable/moved/new/lost labels at URL and
  domain level.
- No live provider call in deterministic tests; retain the opt-in browser
  smoke marker for end-to-end checks.

### Performance and observability tests

- Set a deterministic fixture budget for filtered refreshes and verify that
  superseded query requests do not update the DOM.
- Log endpoint latency, result count, partial-provider count, and correlation
  IDs without logging credentials or sensitive provider payloads.
- Verify that provider block, timeout, malformed response, and empty result
  each map to the correct UI state and recovery action.

## Acceptance Gates

The increment is ready only when:

- all four views use one URL-preserved scope model;
- all metrics have documented semantics and server-side tests;
- all responses expose normalized scope, freshness, interval, timezone, and
  data-status metadata;
- all charts have exact accessible tables;
- provider success, empty, unused, and failure states are distinguishable;
- two compatible runs can be compared with canonical-URL provenance and
  stable/moved/new/lost classifications;
- heuristic content-gap signals are clearly labelled and not overstated;
- exports are bounded, filtered, reproducible, safe, and accompanied by a
  preflight/manifest;
- filter refreshes are cancellable and state transitions are observable;
- deterministic tests, lint, build, and Sphinx warning-as-error checks pass;
- `docs/alpha-2.0.0-ui.md`, this plan, implementation status, and
  `CHANGELOG.md` describe the same delivered scope.

## Deferred Decisions

- Query clustering and related-query expansion require a dedicated normalized
  query/feature contract.
- Authoritative content-gap analysis requires a site inventory or external
  search-console integration.
- Scheduled checks, alerts, geographic grids, backlink crawling, and page
  content auditing remain outside Alpha 2.0.0.
- A chart library is deferred until native SVG/CSS cannot meet accessibility,
  interaction, or maintenance requirements.
