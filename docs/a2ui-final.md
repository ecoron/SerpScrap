```{eval-rst}
:orphan:
```

# Alpha 2.0.0 UI Finalization Plan

## Status

Open. This document records the remaining implementation, verification, and
release-documentation work identified when checking the Alpha 2.0.0 UI plans
against the code base. The deterministic suite is green, but the increment is
not fully complete until the gates below are closed.

This is an internal delivery document. The files `docs/alpha-2.0.0-ui.md`,
`docs/a2ui-development.md`, `docs/a2ui-configuration.md`,
`docs/a2ui-frontend-polish.md`, and this file must not be included in the
published Read the Docs navigation or build output.

## Verified Baseline

The following areas are implemented and covered by the current code and tests:

- History analytics, filters, URL-backed views, trends, coverage, and compare;
- canonical URL identities and stable/moved/new/lost result classes;
- configuration schema, grouped UI, persistence, validation, redaction, and reset;
- cancellable requests, query debounce, responsive layout, reduced motion, and
  accessible table alternatives;
- deterministic tests, Ruff, and Sphinx warning-as-error validation.

The opt-in browser visual smoke test remains separate and requires Chrome and
network access.

## Remaining Alpha 2.0.0 Work

### Analytics response contract

- Include a `semantics` object in every analytics, timeseries, provider,
  query, and domain response.
- Keep normalized filters, timezone, interval, coverage bounds, freshness, and
  `data_status` consistent across all endpoints.
- Distinguish an empty archive from insufficient or incomplete historical
  coverage. Missing buckets may be rendered as zero only when coverage is
  known to be complete.
- Add tests for these metadata rules and for inclusive date boundaries.

### Coverage and aggregation

- Distinguish provider states as selected/enabled, unused, empty, failed, and
  successful.
- Add failure rate, best available rank, and provider readiness information
  where the persisted data supports it.
- Ensure canonical domain extraction is used consistently and drill-down links
  preserve the complete active scope.
- Add deterministic ordering, pagination bounds, and aggregation-semantics
  tests for every aggregate endpoint.

### Comparison

- Add provider overlap and domain-level `rank_changed` classification.
- Preserve left/right run, provider, result kind, rank, title, snippet, and
  source URL provenance for every comparison row.
- Implement and validate explicit `offset` pagination at the API boundary.
- Test incompatible contexts, duplicate canonical URLs, missing ranks,
  deleted runs, and no-overlap comparisons.

### Export and deletion

- Provide a visible export preflight containing filters, interval, timezone,
  freshness, format, row limit, and estimated row count.
- Make CSV and JSON exports carry equivalent scope, schema, timestamp, stable
  ordering, and `identity_key_version` metadata.
- Keep exports bounded and exclude credentials, cookies, diagnostics, and
  unbounded snippets.
- Verify that deleting a run refreshes cards, charts, tables, selections,
  chips, comparison state, and deep-linked deleted selections.

### UI and observability hardening

- Complete tests for loading, partial, stale, failed, unavailable, timeout,
  empty, and deleted-data states with actionable recovery controls.
- Verify polite scope announcements, focus order, keyboard behavior, and
  color-independent status indicators.
- Add the planned deterministic refresh-performance test and ensure stale
  superseded requests cannot update the DOM.
- Keep provider block, timeout, malformed response, and empty-result outcomes
  distinguishable without exposing secrets or provider payloads.

## Documentation and Language Cleanup

- Translate all existing German passages in documentation into English,
  including historical plans, user/developer docs, and explanatory notes.
- Translate German code comments and inline documentation into English while
  preserving code behavior and public API terminology.
- Keep implementation status, API behavior, tests, and `CHANGELOG.md`
  synchronized with the actual delivered scope.

## Read the Docs Exclusion Gate

The Alpha UI planning documents are internal engineering records. Before the
next Read the Docs release:

- exclude `docs/alpha-2.0.0-ui.md` and every `docs/a2ui-*.md` file from the
  Sphinx source/build configuration;
- remove them from generated navigation and toctrees;
- verify that they are absent from published HTML, the search index, and
  downloadable documentation artifacts;
- retain them in the repository for implementation history and review.

## Verification Gates

The final increment is complete only when:

- `pipenv run pytest -q` passes without live provider access;
- the opt-in browser smoke result is recorded separately when available;
- Ruff, package build, and Sphinx warning-as-error checks pass;
- every item in this document has implementation and test evidence;
- all German documentation prose and code comments in scope are translated;
- Read the Docs output contains none of the internal Alpha UI planning files;
- `CHANGELOG.md` describes the final delivered scope accurately.

## Deferred Scope

Query clustering, related-query expansion, authoritative content-gap scoring,
scheduled checks, alerts, geographic grids, backlink crawling, page-content
auditing, and external search-console integrations remain outside this final
Alpha 2.0.0 increment.
