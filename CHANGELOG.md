# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Captured and propagated screenshots for the multi-engine browser pipeline,
  including engine-specific artifact paths in MCP results.

- Added a Docker screenshot volume and configurable screenshot directory so
  browser artifacts are visible on the host under `data/screenshots`.

- Persisted Selenium screenshot paths in the SERP history schema so API and
  MCP result responses no longer lose the `screenshot` field.

- Enabled screenshots by default and changed their default directory to
  `C:\\tmp\\screenshots`.

- Made the default browser identity resolve to the installed Chrome major
  instead of pinning Chrome 150, preventing User-Agent drift on local Chrome
  updates. Added opt-in isolated Chrome profile support for controlled smoke
  diagnostics and documented headless/headful comparison guidance.

- Replaced the Windows-specific browser-version lookup with Selenium Manager's
  cross-platform installed-browser detection plus a generic executable
  fallback.

- Added a bounded post-input interaction settle delay for provider autocomplete
  and form validation. The existing headless toggle and opt-in disposable
  profile remain explicit diagnostic controls; WebDriver signals are not
  concealed.

- Recorded the next opt-in diagnostic TODO: compare identical Google/Ecosia
  runs in headless and visible Chrome using the same disposable profile and
  network conditions.

- Added an explicit opt-in `accept` consent action for controlled diagnostic
  searches, including validation, CLI/MCP schemas, provider acceptance labels,
  and regression coverage. The persisted default remains `necessary`.

- Added `docs/a2ui-search.md`, an implementation-ready plan for separating
  verified Google/Ecosia consent clearance from hidden stale DOM nodes and
  later provider access-control challenges in the Selenium browser flow.

- Fixed the homepage browser flow to continue after verified Google/Ecosia
  consent clearance even when hidden stale dialog markup remains in
  `page_source`; added regression coverage for post-consent success and typed
  provider blocking outcomes.

- Updated the live Google/Ecosia browser contracts for the current Ecosia
  textarea search field and Google autocomplete submit interception; live
  smoke now records provider blocking after consent instead of selector drift
  or malformed-state failures.

- Added `docs/a2ui-final.md`, the final Alpha 2.0.0 UI gap list and release
  gate, including English-language cleanup and the future Read the Docs
  exclusion requirement for internal `alpha-2.0.0-ui.md` and `a2ui-*.md`
  planning documents.

- Completed the Alpha 2.0.0 analytics hardening: consistent semantics metadata,
  insufficient-coverage states, comparison fingerprints and provenance,
  provider overlap, bounded comparison offsets, export preflight metadata,
  and Read the Docs exclusion of internal A2UI planning files.

- Implemented the grouped configuration UI and schema-driven configuration
  service: all supported `Config` values are represented, validated, persisted
  in the database, redacted where sensitive, and resettable to fresh initial
  defaults. Added deterministic service and UI contract tests.

- Added `docs/a2ui-configuration.md`, an implementation plan for exposing the
  complete SerpScrap configuration through grouped, accessible, database-backed
  settings with initial-default and reset semantics.

- Added the frontend polish plan and applied responsive, accessible CSS and
  JavaScript reliability improvements across the dashboard and History views.

- Implemented the Alpha 2.0.0 History & analysis increment: enriched
  analytics scope metadata, versioned canonical URL comparison, compatible
  SERP diff classifications, provider/query/domain coverage, cancellable
  grouped filters, explicit dashboard states, scoped exports, and 161 passing
  deterministic tests.

- Expanded `docs/a2ui-development.md` after a second `mcp-serpscrap`
  best-practice review with explicit scope/freshness metadata, grouped and
  cancellable filters, compatibility fingerprints, URL/domain change classes,
  export manifests, standardized UI states, and performance/observability
  tests.

- Added `docs/a2ui-development.md`, an implementation-ready Alpha 2.0.0 UI
  plan based on bounded `mcp-serpscrap` capability tests, with explicit
  answerability limits, interface requirements, API contracts, slices, tests,
  and acceptance gates.

- Updated the default active search engines to exclude disabled providers.

- Fixed Ruff CI errors in the history export and aggregation logic.

- Extended historical result detail fallbacks for provider-specific snippet
  fields such as `description`, `summary`, `text`, `content`, and
  `visible_link`, including legacy persisted Yandex results.

- Aligned History run statuses with Recent Activity badges and added a
  functional `Search again` action next to `Inspect` for every run.

- Improved History Compare with automatic loading, explicit empty/same-run
  states, and responsive selection updates. Replaced provider-count coverage
  with the provider's percentage share of attributed results.

- Fixed historical result detail rendering to use the normalized SERP fields
  (`serp_title`, `serp_snippet`, `canonical_url`, and ranking metadata), so
  inline History results no longer fall back to “Untitled result”.

- Restored History run inspection after the analytics navigation update:
  `Inspect` opens results inline below the run, and shared `?run=` links
  automatically expand the requested run. Added focused History layout styles.

- Completed the History dashboard foundation: date/query/status/provider/result
  filters now affect API-backed metrics and views; added Runs, Trends, Coverage,
  and Compare navigation with accessible trend tables and URL-preserved scope.

- Implemented the Alpha 2.0.0 History & analysis API foundation: versioned
  filtered analytics, daily timeseries, provider/query/domain aggregates,
  two-run comparison, and bounded CSV/JSON exports with deterministic tests.

- Added the Alpha 2.0.0 History & analysis expansion plan in
  `docs/alpha-2.0.0-ui.md`, covering research use cases, analytics contracts,
  trends, provider/query/domain views, run comparison, exports, tests, and
  acceptance criteria.

- Simplified the overview page around the primary search action and recent
  activity, removed redundant workflow/live-workspace panels, and fixed the
  provider metric to count enabled engines from the engine registry.
- Added provider coverage/health visibility, result and failure counts on
  recent searches, direct "Search again" actions, and a guided empty state.
- Aligned recent-search status/actions into one right-side group and clarified
  provider coverage with an attributed-results total matching analytics.

- Fixed UI polling races by awaiting status-update callbacks and refreshing
  completed-run results before overview/history data.
- Kept non-organic result kinds visible and added live/historical result detail
  panels with type, snippet, relevance, engine, and URL metadata.
- Fixed the UI API proxy to forward query parameters such as ``run_id`` and
  constrained result-table wrapping so historical inspection targets the
  selected run and remains readable.
- Replaced live and historical result tables with responsive result cards,
  visible snippets, relevance/engine badges, sorting, and a desktop
  master-detail workspace that stacks cleanly on smaller screens.
- Moved historical results inline below their selected run and moved advanced
  search controls into a settings overlay. Global ``q`` searches now start
  automatically after the search workspace loads.
- Fixed settings-overlay closing by honoring the HTML ``hidden`` attribute and
  prevented duplicate searches by locking the submit action until a run ends.

- Removed the internal ``refactoring2026.md`` planning document from the
  public documentation navigation and updated the URL-scraping example to use
  the stable SerpScrap documentation site.

- Standardized the example search terms around privacy-friendly search-engine
  research and renamed the related-results output file accordingly.

- Removed the obsolete ``docs/ressources.rst`` page from the Sphinx navigation.

- Split the UI into separate Flask/Jinja pages for overview, search, history,
  and configuration; added a persistent global header search and collapsible
  navigation with saved client preference.

- Implemented Refactoring Phase 10.2: replaced the static UI with a Flask/Jinja
  application running inside the Compose UI container, using a same-origin API
  proxy and `/healthz` endpoint.
- Added modular Jinja templates, design-token CSS layers, responsive layouts,
  native ES modules for API/state/polling/views, dynamic search progress,
  result grouping, history filtering, analytics metrics, configuration, and
  deletion safeguards.
- Added Flask runtime dependencies, UI server/asset tests, and updated Docker,
  development, and operator documentation for `python -m ui.app`.
- Added an end-to-end UI proxy test proving that history and analytics travel
  through Flask and the shared API to a database-backed history store; clarified
  that the complete Compose stack is required for a functional local UI.

- Added the Phase 10.2 rough UI product concept for a dynamic search and
  analysis workspace, including application shell, client state model, live
  result exploration, history analysis, visual direction, frontend setup, and
  staged delivery order.
- Added the Phase 10.2 template decision: Flask/Jinja for the UI shell and
  template inheritance, modular CSS/ES modules for interaction, and a
  Tabler-inspired static dashboard component system with CoreUI as fallback.
- Clarified that the final Flask/Jinja UI must run inside the Docker Compose
  project container on the configured UI port with a container healthcheck;
  host-only UI execution is not an accepted deployment mode.

- Implemented Refactoring Phase 10.1 with one shared `docker/Dockerfile` for
  the API, UI, and MCP services; removed the three service-specific
  Dockerfiles and aligned Compose, CI, tests, and Docker documentation.
- Added shared-image configuration through `SERPSCRAP_IMAGE`, service-specific
  runtime commands and health checks, UI assets in the image, and a non-root
  runtime user.

- Added the Refactoring Phase 10.1 single-image Docker implementation plan,
  including Compose consolidation, Docker tests, documentation freshness, and
  changelog evidence requirements.
- Added the Refactoring Phase 10.2 professional UI implementation plan,
  including responsive/accessibility goals, explicit state handling, UI tests,
  documentation freshness, and changelog evidence requirements.
- Renumbered the existing MCP hardening plan as Phase 10.3 to make the Phase 10
  Docker/UI/MCP split unambiguous.

- Implemented Phase 10.3 MCP hardening: strict bounded tool schemas with
  read-only/mutation annotations, versioned structured responses, argument
  validation, bounded untrusted SERP content, paginated result/history reads,
  JSON-RPC error classification, and non-loopback authentication safeguards.
- Secured the Compose MCP deployment by requiring ``MCP_AUTH_TOKEN`` and
  documented loopback-only unauthenticated local startup.
- Added project-local ``.env`` loading for direct MCP startup, with explicit
  process environment variables taking precedence and a safe ``.env.example``.

- Added the Phase 10.3 MCP server best-practice hardening plan covering
  agent-oriented tool schemas, versioned structured responses, asynchronous
  polling and pagination, untrusted-content boundaries, least-privilege
  configuration changes, transport security, and protocol verification.

- Added MCP configuration examples for Claude Code, JSON-configured clients,
  the OpenAI Responses API, and the Anthropic Messages API, including local
  versus hosted transport and authentication caveats.

- Reworked the Sphinx documentation into a complete user/developer structure
  with Python, CLI, Docker, MCP, configuration, results, and provider guides;
  updated the README for the `2.0.0-alpha.1` release and removed obsolete
  refactoring fragments from user-facing pages.

- Fixed xPrivo browser input detection for its rendered `Privat suchen`
  placeholder, preventing false `selector_drift` failures before submission.
- Updated xPrivo SERP readiness and organic-card selectors for its hydrated
  `div.group` / `a.block.py-3` result layout, preventing post-submit state
  classification failures.

- Updated stale registry and configuration expectations to include the new
  plugins while keeping disabled MetaGer out of active defaults.

- Fixed Ruff import-order and formatting violations in the API service,
  search-engine exports, and phase-plan tests.

- Fixed the Phase 9.1 and Phase 9 documentation heading hierarchy so strict
  Sphinx builds no longer report non-consecutive header-level warnings.

- Implemented the Phase 9.2 plugin foundation: typed plugin capabilities and
  metadata, contract validation, registry registration/capability discovery,
  pre-navigation request validation, fixture-backed contract tests, and a
  developer guide for adding search engines.
- Implemented publicly available, no-auth European plugins (GOOD, xPrivo,
  Marginalia web UI, and eTools.ch) with URL builders, browser contracts,
  sanitized fixtures, and parser contract tests; MetaGer remains registered but
  disabled because its current public route requires a key.
- Added an explicit SearXNG instance factory without a default public-instance
  dependency, plus authentication metadata that prevents credentialed routes
  from being treated as no-auth plugins.
- Activated GOOD, xPrivo, Marginalia, and eTools.ch in the default
  search-engine configuration; Google, Ecosia, Qwant, and MetaGer remain
  supported or registered but are no longer part of the active defaults.
- Updated the Docker/API configuration endpoint and UI to use the active
  `Config` defaults, making the five new engines selectable without silently
  selecting every registered plugin.
- Hardened the Phase 9 live candidates: GOOD and Marginalia now parse their
  current result-card layouts, xPrivo starts on its dedicated search route,
  and eTools retries its documented GET endpoint when a POST remains on the
  homepage. MetaGer is disabled until a public no-auth route is available
  because the current service requires a MetaGer key.
- Documented the six-candidate no-auth rollout, exclusions, provenance rules,
  and readiness gates for Phase 9.2.
- Implemented the Phase 9.1 consent foundation: semantic Google/Ecosia
  controls, explicit consent progress states, overlay-clear verification,
  removal of undocumented JavaScript consent shortcuts, and mocked-browser /
  fixture regression tests.
- Fixed consent verification to ignore hidden post-click dialog nodes and use
  the rendered browser state for Google/Ecosia overlay clearance.
- Added the artifact-backed Google `div.GzLjMd button#W0wltc` consent fallback,
  still gated by the visible rejection label and post-click verification.
- Added the artifact-backed Ecosia `#didomi-notice-disagree-button` fallback,
  gated by the visible `Nicht essenzielle Cookies ablehnen` label.
- Added the Phase 9.1 plan for artifact-backed Google and Ecosia consent
  handling, explicit waits, provider provenance, and safe `consent_required`
  fallbacks.
- Implemented Phase 9 service hardening: bounded API job capacity, database
  readiness checks, graceful service shutdown, bounded result pagination, and
  deterministic regression tests.
- Expanded Docker operator documentation with health/readiness, lifecycle,
  queue-capacity, and pagination guidance.
- Added the Phase 9 plan for project/code quality, bounded performance,
  separate Docker-user and developer documentation, and the Version 2
  pre-release/PyPI communication model.
- Reworked the project README as a public landing page and added a dedicated
  developer guide alongside the Docker operator guide.
- Resolved CI Ruff import-block failures for the Phase 8 service, MCP,
  normalization, and Docker-layout test modules.
- Fixed the Phase 8.2 failure-persistence test fixture to provide the complete
  `FailureRecord` contract.
- Implemented Phase 8.3: compact responsive result workspace, canonical URL
  grouping with all contributing engines, relevance-based ordering, and API/UI
  deletion controls for one search or the complete result archive.
- Implemented Phase 8.4: persisted search progress, visible progress/ETA
  status, and independently scrollable result panels with initial results kept
  in the viewport.
- Fixed History action-column overflow and enabled cross-origin DELETE
  requests for individual and bulk result deletion.
- Fixed History column sizing and disabled historical deletion until a search
  is explicitly selected.
- Added the Phase 8.2 implementation plan for separate current and historical
  result views, engine-attributed failures, fixed result-column ordering, and
  canonical destination URL handling.
- Implemented Phase 8.2 result normalization, run-scoped current and historical
  views, canonical destination URLs, typed image exclusion, relevance values,
  and engine-attributed failure display.
- Implemented Phase 8.1: registry-backed all-engine defaults, persisted and
  validated UI configuration with reset support, configuration/engine APIs,
  MCP configuration tools, registry-driven engine selection, and automatic
  result/history refresh with bounded polling.
- Added the Phase 8.1 implementation plan for all-enabled default engine
  searches, registry-backed UI selection, persisted configuration, and
  automatic result refresh.
- Grouped Docker-specific files under `docker/`: app, UI, and MCP Dockerfiles,
  `compose.yml`, and Docker layout documentation; updated CI and all Compose
  mount/build paths accordingly.
- Implemented the initial Phase 8 multicontainer runtime: shared search API,
  persistent job/result/failure history, PostgreSQL-compatible storage with
  SQLite fallback, functional UI, MCP-compatible gateway, Compose topology,
  local mounts, health checks, and service/API tests.
- Added the Phase 8 concept for a four-container SerpScrap deployment with a
  shared application/API layer, PostgreSQL persistence, functional UI, MCP
  access, explicit local mounts, historical analysis, and a deterministic
  container test strategy.
- Fixed CI regressions in Ruff formatting, documentation indentation, Bing fixture parsing, sensitive form redaction, text decoding, and malformed post-submit classification.
- Closed Refactoring Phase 7 with the homepage-driven browser flow, provider contracts, diagnostics, typed outcomes, fixtures, tests, documentation, and practical-run status consolidated; Google/Ecosia live consent automation remains a documented future TODO.
- Added default Google consent handling using stable dialog attributes; `consent_action=necessary` selects the privacy-preserving rejection action, with `reject` and `disabled` alternatives plus CLI support.
- Waited for Google's asynchronous consent-dialog dismissal before locating and using the search field.
- Added a scoped Google consent-button fallback for Selenium renders that expose no button text.
- Added delayed Didomi consent-button discovery for Ecosia and a scoped Google DOM fallback.
- Extended consent discovery to 15 seconds and added direct Google ID/DOM lookup for the observed rejection control.
- Added Google DOM and Ecosia Didomi API fallbacks for privacy-preserving consent rejection with post-action verification.
- Fixed Google and Swisscows overlay interference by avoiding an unnecessary input click and dismissing the observed Swisscows popup through the browser contract; normalized common result-text mojibake.
- Fixed the latest Google homepage run by retrying visible but temporarily non-interactable search fields and added typed selector-drift handling plus regression coverage.
- Made CLI JSON output safe for non-ASCII result data on legacy Windows console encodings.
- Implemented Phase 7.3 provider-state hardening: explicit empty/malformed outcomes, post-submit navigation classification, terminal outcome summaries, configurable retry categories, and regression tests for zero-result and route-state handling.
- Corrected Phase 7.3 selectors and provider classification from the latest rendered artifacts for Brave, Qwant, Startpage, Swisscows, and Mojeek; added sanitized parser fixtures and regression tests.
- Refined the current-run SERP handling for Brave, Startpage, and Swisscows with artifact-backed card/readiness selectors and additional parser fixtures.
- Implemented Phase 7.2 provider-state hardening, visible-DOM classification, Brave/Ecosia pre-input handling, Bing/Yandex false-positive protection, correlation propagation, and updated configuration examples.
- Added the Phase 7.2 plan for artifact-driven provider-state classification, selector correction, correlation propagation, and Bing/Yandex false-positive handling.
- Implemented Phase 7.1 correlated progress reporting, JSONL stderr output, opt-in redacted rendered-HTML artifacts with bounded manifests, and diagnostic safety tests.
- Added the Phase 7.1 plan for visible correlated progress, opt-in redacted rendered-HTML diagnostics, bounded artifact storage, and selector-drift analysis based on the practical Phase-7 run.
- Implemented Phase 7 homepage-driven Selenium search flow with declarative per-engine selector contracts, submit/readiness handling, typed provider failures, lifecycle cleanup, and contract tests.
- Added the Phase 7 refactoring plan and documented the homepage-driven search flow plus per-engine selector baselines and verification rules.
- Added the Phase 6 plan for reproducible Read-the-Docs documentation builds and Sphinx configuration alignment.
- Added a root-level Read the Docs version-2 build configuration, reproducible Sphinx requirements, MyST Markdown support, and warning-clean build settings.
- Aligned the local documentation Makefile/navigation and removed the obsolete Jekyll configuration.
- Added a dedicated CI job for the warning-as-error Sphinx HTML build.
- Fixed Linux CI mypy validation for the Windows-only `winreg` browser detection path.
- Made the browser identity fallback test platform-aware for Linux CI runners.
- Completed Phase 5 production integration for the registered multi-engine plugins, including validated readiness/capability metadata, per-engine concurrency ceilings, versioned country-aware cache identities, atomic cache writes, and explainable deterministic fusion report metadata.
- Added documentation examples for multi-engine searches capped at four concurrent requests.
- CLI searches now inherit all omitted option values from ``serpscrap/config.py``; ``search -k`` no longer replaces configured defaults.
- Added the direct ``SerpScrap.search()`` API with canonical JSON-compatible ``list[dict]`` results.
- Added atomic UTF-8 JSON file output and CLI ``--output``/``--overwrite`` options.
- Made HTML caching and SQLite history independently optional.
- Moved optional SQLite history behind a post-assembly repository so persistence failures retain successful in-memory results.
- Removed CSV output, duplicate result writers, and the unreachable legacy scraping workflow.
- Added current Chrome identity resolution, paced Google navigation, bounded transient retries, access-control/rate-limit classification, and a run circuit breaker.
- Added canonical parsing and vertical routing for organic, image, news, shopping, and video result formats.
- Hardened URL enrichment with explicit headers, limits, classified failures, and atomic identity-aware caching.

## [0.14.0] - 2025-10-26
### Changed
- Removed support for Firefox and PhantomJS. Only Chrome is supported.
- Updated dependencies and improved error handling.
- Refactored cache management and Selenium integration.
- Modernized Dockerfile (now based on python:3.10-slim).
- Updated documentation and README for pipenv and Docker usage.
- Added clear pipenv CLI usage examples to README and docs.

## [0.13.0]
### Changed
- Updated dependencies: chromedriver >= 76.0.3809.68, sqlalchemy>=1.3.7
- Minor changes to install_chrome.sh

## [0.12.0]
### Changed
- Update and cleanup of selectors to fetch results
- New result type: videos

## [0.11.0]
### Changed
- Chrome headless is now the default browser, PhantomJS is no longer supported
- Chromedriver is installed on the first run (Linux, Windows, Mac OS)
- Scraping of raw text contents from SERP URLs and given URLs improved
- Scraping of SERP results and contents can be run at once
- CSV output format changed (now tab-separated and quoted)

## [0.10.0]
### Changed
- Support for headless Chrome, adjusted default time between scrapes

## [0.9.0]
### Added
- Result types added (news, shopping, image)
- Image search is supported

## [0.8.0]
### Changed
- Text processing tools removed
- Fewer requirements
## Unreleased

- Added the Phase 9.2 implementation plan for a typed, capability-driven,
  developer-friendly search-engine plugin structure, including registry
  validation, fixture contracts, migration slices, and acceptance criteria.
