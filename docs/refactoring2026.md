# Refactoring Phase 9.1 - Google and Ecosia Consent and Browser-Flow Completion

## Status

Implementation in progress. The semantic consent contract, provider-specific
selectors, explicit verification, fixture coverage, and mocked-browser tests
are implemented. The dated live-smoke evidence remains open. This phase keeps
provider protections intact: SerpScrap must
not bypass CAPTCHA, rate limits, access controls, or a consent decision that
cannot be verified through the rendered browser state.

## Implementation Status

- [x] Semantic, provider-scoped consent labels and selectors
- [x] Explicit consent progress states and overlay-clear verification
- [x] Removal of undocumented Google/Ecosia JavaScript consent shortcuts from
  the default success path; Google's artifact-backed `W0wltc` fallback remains
  scoped and requires the visible rejection label
- [x] Sanitized Google/Ecosia consent fixtures and mocked-browser regression tests
- [ ] Dated low-volume live smoke evidence for Google and Ecosia

## Research Findings

- Google's official Custom Search JSON API is not a general replacement for
  the public Google SERP. It requires an API key and a configured Programmable
  Search Engine, and Google's current documentation says the API is closed to
  new customers with existing customers transitioning by 1 January 2027.
  See the [official overview](https://developers.google.com/custom-search/v1/overview)
  and [REST reference](https://developers.google.com/custom-search/v1/reference/rest).
- Ecosia documents that results may come from Bing, Google, or EUSP depending
  on region, device, and cookie/privacy permissions. Its provider setting is
  only exposed when multiple providers are available and after cookie
  preferences are set. See Ecosia's [provider documentation](https://support.ecosia.org/article/579-search-results-providers)
  and [settings documentation](https://support.ecosia.org/article/349-ecosia-settings).
- Selenium's supported approach is explicit, observable waiting for visibility,
  state changes, and interaction readiness. Consent work must use these waits,
  not fixed sleeps. See Selenium's [expected conditions guide](https://www.selenium.dev/documentation/webdriver/support_features/expected_conditions/).
  A dedicated Chrome profile is technically supported, but profile/cookie
  reuse must remain isolated, opt-in, and user-controlled; see the [ChromeDriver
  profile documentation](https://developer.chrome.com/docs/chromedriver/capabilities).

## Objective

Complete and verify the Google and Ecosia homepage flows for the supported
privacy-preserving consent action. The implementation must recognize consent
as a stateful provider interaction, confirm that the overlay is gone before
search input, preserve a typed `consent_required` outcome when confirmation is
not possible, and record enough sanitized evidence to diagnose selector drift.

## Solution Decision

| Option | Decision | Rationale |
| --- | --- | --- |
| Visible, semantic consent controls with explicit waits | **Preferred** | Follows the rendered user flow and can be fixture-tested without relying on private provider APIs. |
| Isolated reusable Chrome profile or pre-seeded consent state | Conditional fallback | May reduce repeated prompts, but must be opt-in, disposable, documented, and never commit cookies or user data. |
| Google Custom Search JSON API | Not part of 9.1 | It does not provide the public SERP contract and is closed to new customers. Evaluate only as a separate future integration for configured Programmable Search Engines. |
| Ecosia provider/API shortcut | Rejected for 9.1 | Ecosia's documented provider selection depends on region, device, and consent; no stable public search API contract was found. |
| Continue after an unverified overlay | Rejected | It would make result provenance and privacy behavior ambiguous. Return `consent_required` instead. |

Undocumented element IDs, private JavaScript consent APIs, and guessed cookie
names may be retained only as quarantined diagnostic observations. The
artifact-backed Google `W0wltc` selector is an explicit exception: it is
scoped to the observed consent button and still requires a visible semantic
rejection label plus overlay-clear verification. It must not silently alter
consent state.

## Provider-Specific Implementation Plan

### Google

1. Capture a new, low-volume, opt-in artifact for each supported country/
   language combination where the consent overlay appears. Record URL, dialog
   role, accessible name, button text/ARIA label, frame/shadow-root location,
   and the post-action URL/state without query text or cookies.
2. Define ordered, semantic consent candidates scoped to the active dialog:
   reject/necessary actions first, then a documented locale mapping. Use
   visibility, enabled state, clickability, and overlay disappearance as the
   success contract; do not treat a click alone as success.
3. Handle consent pages reached through `consent.google.*` as a bounded state
   transition back to the configured Google homepage/SERP route. Stop with
   `consent_required` when the transition or overlay-cleared check times out.
4. Keep search input and SERP readiness separate from consent handling. A
   successful consent action must still pass the existing homepage, submit,
   URL/state-change, and organic-card contracts.

### Ecosia

1. Capture consent overlays for the relevant region/device combinations and
   identify whether the controls are in the main DOM, an iframe, or a shadow
   root. Promote only sanitized, date-stamped evidence.
2. Implement a visible-control flow for necessary-only consent, including a
   bounded `Manage cookies` step when the provider requires a preference page.
   Verify both overlay removal and the persisted state needed for the next
   navigation; do not call an undocumented Didomi method as the primary path.
3. After consent, detect the actual result route and organic cards. Preserve
   the Ecosia engine ID while recording an optional provider-family/source
   attribution only when the page exposes it unambiguously.
4. Treat a missing provider choice, changed provider family, or unavailable
   consent control as an observable diagnostic outcome, not as evidence that
   Ecosia is equivalent to Bing or Google.

## Shared State Machine and Safety Rules

- Model `consent_not_present`, `consent_visible`, `consent_action_started`,
  `consent_cleared`, and `consent_required` as explicit states.
- Scope selectors to the observed dialog/frame/root and keep locale variants
  in provider metadata rather than broadening to arbitrary page buttons.
- Use explicit Selenium waits for element visibility/clickability, frame or
  shadow-root availability, URL transitions, and overlay disappearance.
- Keep consent action, browser profile path, cookie state, and provider source
  out of normalized result rows unless they are safe, typed metadata.
- Never persist real user profiles, authentication cookies, raw consent
  payloads, query text, or third-party page content in fixtures or CI artifacts.
- Preserve partial-success semantics: one unresolved provider consent state
  must not discard results from other engines.

## Implementation Slices

1. Refresh the Google/Ecosia artifact matrix with sanitized, dated,
   opt-in observations and explicit country/device assumptions.
2. Extend the browser interaction contract with provider-specific consent
   states, locale labels, frame/shadow-root metadata, and verification rules.
3. Replace undocumented consent shortcuts as primary paths with semantic,
   explicit-wait handlers and a typed fallback outcome.
4. Add isolated-profile support only if artifacts show that it is necessary;
   document lifecycle, cleanup, opt-in configuration, and cookie safety.
5. Add offline DOM fixtures and mocked-WebDriver tests for every consent state,
   timeout, frame/root variation, post-action transition, and partial failure.
6. Run one low-volume live smoke per provider and supported market, compare
   result/provenance metadata, and record selector decisions in the changelog.

## Test and Acceptance Strategy

- Unit tests cover locale label matching, selector scoping, state transitions,
  explicit wait timeouts, overlay disappearance, and redaction.
- Mocked Selenium tests prove that consent is handled before input, success is
  not declared before verification, drivers are closed, and unresolved states
  become `consent_required`.
- Fixture tests cover normal, consent-present, consent-cleared, blocked,
  rate-limited, empty, and malformed Google/Ecosia pages.
- Live browser checks remain opt-in, low-volume, dated, and outside the default
  CI gate. They must not bypass provider controls.

## Acceptance Criteria

- Google and Ecosia each have a documented, fixture-backed consent contract
  with explicit success and safe failure states.
- No undocumented provider JavaScript API or guessed cookie is required for
  the default success path.
- Consent actions are verified by rendered state and do not leak user data.
- Ecosia result provenance remains honest when its upstream provider changes.
- Existing provider, parser, partial-success, diagnostic-redaction, and
  browser-cleanup tests remain green.
- The live TODO is closed only after dated smoke evidence and changelog entries
  are recorded; otherwise the provider remains explicitly `consent_required`.

# Refactoring Phase 9 - Project Quality, Performance, and Documentation Structure

## Status

Implementation completed for the service hardening, documentation split, and
deterministic quality checks described below. The remaining release decision
and broader performance profiling are still follow-up work. This phase does
not make Version 2 available on PyPI yet.

## Implementation Status

- [x] Separate Docker operator and developer documentation
- [x] Bounded API job workers and pending-job capacity
- [x] Database-backed readiness and graceful service shutdown
- [x] Bounded result pagination and deterministic service regression tests
- [x] Compose lifecycle settings and documented runtime limits
- [ ] Host-specific performance baseline and full multi-container smoke run

## Objective

Improve project and code structure, establish predictable performance for the
Docker application, and provide documentation for both Docker operators and
developers. Version 2 is a complete reworking of SerpScrap. Pre-release builds
may be distributed as Docker images or installed from the Git repository; the
Version 2 PyPI release is intentionally deferred until the refactoring and
release checks are complete.

## Documentation Audience and Structure

Documentation must clearly distinguish between the people running the Docker
application and the people developing or extending SerpScrap:

- **Docker application users** need task-oriented guidance for image selection,
  Compose startup, configuration, persistent mounts, health checks, upgrades,
  backups, troubleshooting, and safe shutdown.
- **Developers and contributors** need a separate guide for repository layout,
  local Pipenv setup, service boundaries, coding and testing conventions,
  performance profiling, documentation builds, and contribution workflow.
- The project README remains the public entry point and links to the relevant
  user and developer documentation without duplicating operational details.

The Docker user guide remains in `docs/docker.rst`; developer-facing material
is maintained separately. Examples must identify whether they target a
released package, a pre-release Docker image, or the Git checkout.

## Quality and Project-Structure Goals

- Define ownership of API, application, persistence, provider, UI, MCP, and
  Docker integration boundaries.
- Remove duplicated configuration, lifecycle, and error-handling paths where
  they can be replaced by shared typed services and contracts.
- Keep public APIs, CLI behavior, normalized result models, and Docker service
  contracts stable unless a deliberate Version 2 change is documented.
- Keep formatting, linting, typing, deterministic tests, documentation builds,
  and package builds reproducible in Pipenv and CI workflows.
- Distinguish generated files, local data, logs, caches, secrets, and build
  artifacts clearly from source-controlled project files.

## Performance and Reliability Goals

- Measure startup time, memory use, request latency, job throughput, and
  polling behavior for the application, UI, and MCP containers.
- Bound browser concurrency, polling backoff, result pagination, cache growth,
  and diagnostic artifact retention.
- Avoid unnecessary browser creation, repeated configuration loading, duplicate
  serialization, and unbounded in-memory result accumulation.
- Add health/readiness and graceful-shutdown checks for normal and degraded
  database conditions while retaining useful partial-success behavior.
- Record a reproducible baseline and investigate regressions before optimizing
  provider-specific behavior.

## Release and Version 2 Communication

The README and Docker documentation must state prominently that Version 2 is
being completely reworked. During this phase:

- stable users should use the released PyPI package where applicable;
- Version 2 pre-releases are offered through published Docker image tags;
- developers may install Version 2 directly from the Git repository in an
  isolated Pipenv environment;
- Version 2 is not presented as a PyPI release until a later release step.

Examples must include an explicit image tag or Git revision for reproducibility.

## Implementation Slices

1. Audit repository and service boundaries; document ownership, supported entry
   points, and generated or deployment-local files.
2. Establish developer documentation and a focused Docker user workflow.
3. Add deterministic performance baselines and targeted tests for startup,
   bounded concurrency, pagination, polling backoff, health, and shutdown.
4. Simplify duplicated project/configuration paths and align CI, Pipenv,
   packaging, and documentation-build instructions.
5. Rewrite the README as a concise public landing page with installation
   choices, examples, documentation links, project status, and the Version 2
   release note.
6. Validate docs, tests, lint, typing, package, and Docker checks; record
   findings and remaining release work in both changelogs.

## Test and Acceptance Strategy

- Documentation tests verify the Phase 9 plan, README release messaging,
  installation paths, and user/developer documentation links.
- Existing unit, service, API, UI, MCP, Docker-layout, lint, type, and Sphinx
  warning-as-error checks remain green.
- Performance checks are deterministic and local; live provider searches are
  opt-in and are not required for CI acceptance.
- A Docker smoke check covers startup, readiness, bounded lifecycle, persistent
  mounts, and clean shutdown.

## Acceptance Criteria

- Docker users and developers have explicitly separated documentation.
- The README identifies Version 2 as a complete rework, explains deferred PyPI
  availability, and documents Docker/Git pre-release paths.
- Quality and performance baselines are reproducible and have a regression
  test or diagnostic path.
- CI and local Pipenv workflows validate code, docs, packaging, and Docker
  layout without network-dependent provider searches.
- The plan, implementation status, test evidence, and release decisions are
  recorded in `docs/refactoring2026.md`, `CHANGELOG.md`, and
  `docs/changelog-refactoring2026.md`.

# SerpScrap Refactoring Plan 2026

## Refactoring Phase 8 - Multicontainer Application and Search Archive Analysis

### Status

Initial implementation completed. The API, persistent job service, UI,
MCP gateway, Compose topology, local mounts, and deterministic service tests
are available. PostgreSQL migrations, production authentication, and full
Compose smoke coverage remain follow-up hardening work.

### Implementation Status

- [x] Shared versioned HTTP API for search submission, status, results, history,
  analytics, health, and readiness
- [x] Asynchronous job service with persistent run, result, and failure records
- [x] SQLAlchemy history store with SQLite offline fallback and PostgreSQL URL
  support
- [x] Functional static UI container for starting searches and inspecting
  results and history analytics
- [x] MCP-compatible JSON-RPC gateway delegating to the shared API
- [x] Four-service Docker Compose topology with documented local mounts
- [x] Focused service and API tests without browser or network access
- [ ] Production authentication, migrations, backup/restore automation, and
  full container smoke tests

### Objective

SerpScrap will run as a flexible multicontainer application. The central
SerpScrap application container retains the search and interaction logic. A
separate database container stores search history durably, a user-interface
container provides an intuitive workflow, and an MCP server container exposes
the same capabilities to MCP-compatible clients. The UI and MCP server must
not duplicate scraping or persistence logic; both use the same application and
repository layers.

The result must run locally with Docker Compose and in a small server
environment. Users can start searches, monitor them continuously, view
results, and filter, compare, and aggregate historical searches and hits.

### Architecture and Responsibilities

The target topology consists of four containers connected through a shared
internal Compose network:

| Container | Responsibility | Exposure |
| --- | --- | --- |
| `serpscrap-app` | HTTP API, job orchestration, browser/provider integration, result normalization, and domain services | Internal API network only; optional administrative health port |
| `serpscrap-db` | PostgreSQL database for searches, jobs, hits, failure states, and analysis indexes | Internal database network only |
| `serpscrap-ui` | User interface for searches, run status, result lists, details, and historical analysis | Operator-configurable host port |
| `serpscrap-mcp` | MCP transport and tools/resources for searches, status, results, and historical analysis | Internal by default; optionally published separately |

The application container is the only place that executes the existing
scraping pipeline and provider adapters. The database is connected through a
configurable PostgreSQL URL. Existing SQLite history remains available for
local/offline CLI and library use; container deployments use versioned
PostgreSQL migrations.

The first release does not introduce a fifth queue or cache database
container. Running jobs are managed by the application service and persisted
in PostgreSQL with status, progress, correlation ID, and timestamps. A later
move to an external queue must remain possible without changing the UI or MCP
contracts.

### Shared Application and API Contract

Interaction logic is modeled as a versioned service contract (`/api/v1`). The
UI and MCP server use the same endpoints or service methods:

- Start a search with a query, engines, search type, page count, and optional
  runtime options (`POST /searches`).
- Retrieve run status, progress, partial results, and structured failures by
  job ID and correlation ID (`GET /searches/{id}` and
  `GET /searches/{id}/events`).
- Load paginated and sorted results with engine and outcome filters
  (`GET /results`).
- Filter historical runs by time range, query, engine, outcome, and result
  count (`GET /history/searches`).
- Analyze historical hits by frequency, engine comparison, success/failure
  distribution, time trends, duplicates, and top domains
  (`GET /history/analytics`).
- Provide health and readiness checks for the application and database.

All responses retain the existing normalized result contract, structured
provider outcomes, partial-success behavior, and safe failure details. API and
MCP schemas are derived from typed models and versioned. Browser diagnostics
and sensitive inputs remain redacted and opt-in.

### User Interface

The UI must be usable without knowledge of the CLI or internal containers. The
first version includes:

- a search form with sensible defaults, engine selection, search type, page
  count, and validation feedback;
- a live run view with status, progress, correlation ID, partial results, and
  understandable provider failures;
- a paginated result list with engine/outcome filters, title, URL, snippet,
  rank, timestamp, and a detail view;
- a history page with run, time-range, and query filters plus comparable
  result and failure metrics;
- empty, failed, blocked, and running states with responsive and accessible
  forms.

The UI communicates only with the application API service. Robust polling with
backoff is planned initially; a later move to SSE/WebSocket must not require a
data-model change. Authentication, CORS, rate limits, and an optional reverse
proxy are deployment security configuration, not UI domain logic.

### MCP Server

The MCP container provides a small, stable tool surface based on the API
contract. Planned tools/resources are `start_search`, `get_search_status`,
`list_results`, `list_search_history`, and `analyze_history`. Tool inputs are
validated like API inputs; large result sets are paginated and sensitive
diagnostic content is never returned unfiltered. The server remains
stateless: job and result state live in the application and database.
Transport, authentication, and enabled MCP tools are configured through
environment variables.

### Persistence and Local Mounts

All durable data is retained through explicit, documented mounts from the
project or deployment directory. The Compose file uses no anonymous volumes
for domain data:

| Local directory | Container path | Contents |
| --- | --- | --- |
| `./data/postgres` | `/var/lib/postgresql/data` | PostgreSQL data and migration state |
| `./data/cache` | `/var/lib/serpscrap/cache` | Versioned HTML/result caches |
| `./data/diagnostics` | `/var/lib/serpscrap/diagnostics` | Opt-in, redacted diagnostic artifacts only |
| `./data/exports` | `/var/lib/serpscrap/exports` | User-requested JSON and analysis exports |
| `./logs` | `/var/log/serpscrap` | Structured app/UI/MCP logs as configured |

Directories are created at startup with appropriate permissions. Secrets,
passwords, and tokens are not committed to images, Compose files, or mounts;
they are injected through environment or secret mechanisms. PostgreSQL backup
and restore are documented operational procedures; caches and diagnostic
artifacts can be cleaned independently.

### Docker and Operations Design

- A slim, reproducible application image serves as the base for the app and
  MCP containers; UI dependencies are built separately.
- `docker/compose.yml` defines health checks,
  startup dependencies, restart policy, resource limits, non-root execution
  where compatible with Chrome, and internal networks.
- The app and MCP server wait for database readiness and exit with a clear
  message when configuration is invalid.
- Provider access, Chrome resources, concurrency, and diagnostic limits remain
  configurable; provider protections are never bypassed.
- Container logs are JSONL by default and do not expose search terms or URLs
  that should be protected by the existing redaction rules.

### Implementation Slices

1. Extract an API/service layer from the existing application and repository
   logic; define versioned job, result, and history models.
2. Add the PostgreSQL adapter, migrations, indexes, and idempotent startup
   checks while protecting SQLite offline mode and existing CLI contracts.
3. Build the application container with Chrome, cache/diagnostic mounts, and
   health checks.
4. Build the UI container with search, status, result, and analysis views and
   test it against the API contract.
5. Build the MCP container with validated tools, pagination, and access
   controls.
6. Complete the Compose setup, local directories, example environment,
   backup/restore procedure, and operations documentation.
7. Run integration and smoke tests in CI; live provider searches remain opt-in
   and are not part of deterministic tests.

### Test and Acceptance Strategy

- API contract tests cover validation, job lifecycle, polling/event data,
  pagination, partial success, and structured failures without a browser or
  network.
- Repository tests cover the PostgreSQL schema, migrations, indexes,
  transaction boundaries, restart behavior, and analysis queries; SQLite
  regression coverage remains in place.
- UI tests cover search, loading/error/empty states, filters, historical
  analysis, and accessible interaction against a mocked API service.
- MCP tests cover tool schemas, delegation to shared application logic,
  pagination, and sensitive-data redaction.
- Compose smoke tests start all four containers, wait for health checks, run a
  deterministic stub search, read results through the UI/API and MCP, and
  verify restart persistence through the PostgreSQL mount.
- Mount, secret, non-root, port, and network checks prevent data from being
  written accidentally to the container layer or database ports from being
  exposed publicly.

### Acceptance Criteria

- `docker compose -f docker/compose.yml up` starts the app, database, UI, and
  MCP containers reproducibly and reports the correct readiness state.
- A search can be started through the UI and MCP; both paths produce the same
  job/result contract and history.
- Run status, partial results, provider outcomes, and failures are clearly
  visible and remain in the database after an application restart.
- Historical hits can be filtered, paginated, and analyzed using defined
  metrics.
- Cache, diagnostics, exports, logs, and PostgreSQL data reside in the
  documented local directories and survive container restarts.
- Offline tests require neither Chrome nor network access; Compose tests use
  stubs and are deterministic. An opt-in browser smoke test remains separate.
- The API, UI, and MCP server contain no duplicated scraping or persistence
  logic; Phase 7 security and provider-protection rules remain effective.

## Refactoring Phase 8.1 - Persisted Engine Configuration and Automatic Result Refresh

### Status

Implementation completed. This phase extends the Phase-8 runtime with a
persisted user configuration, complete available-engine defaults, a
configuration page, MCP configuration tools, and automatic result refresh. It
does not introduce a second scraping path or move provider selection into the
UI.

### Implementation Status

- [x] Registry-backed engine metadata and all-enabled default selection
- [x] Versioned database configuration record with atomic save and reset
- [x] Explicit-search, persisted-configuration, and default precedence
- [x] Configuration, reset, and engine-discovery API endpoints
- [x] UI configuration page with accessible engine selection and safe defaults
- [x] Automatic result/history refresh with bounded polling and request locking
- [x] MCP configuration and engine-discovery tools
- [x] Service and API regression tests for defaults, persistence, validation,
  and explicit overrides

### Objective

Make the default search behavior cover every currently available and enabled
search-engine plugin. Let users select a subset of those engines through a
dedicated configuration page, store that selection in the database, and use
the persisted selection for later searches. If no configuration exists, the
application must use the SerpScrap defaults, with the effective engine list
derived from the trusted registry rather than duplicated in frontend code.

Search results and job status must refresh automatically in the UI while a
search is running and after new results are persisted. Manual refresh remains
available as a fallback, but users should not need to reload the page to see
new results.

### Source of Truth and Default Semantics

The `default_registry()` and its enabled plugin metadata are the authoritative
source for available engines. The configuration service must expose stable
engine IDs, display names, enabled/disabled state, disable reasons, supported
search types, and provider metadata to the UI.

The effective engine selection follows this precedence:

1. An explicit engine list in the current search request, if valid.
2. A persisted user configuration for the active configuration scope.
3. The SerpScrap default configuration, filtered to currently available and
   enabled registry plugins.

An empty persisted selection is invalid for normal searches and must be
rejected with a clear validation message. A provider disabled in the registry
cannot be re-enabled by the UI. Engines removed from or disabled in the
registry are excluded from the effective selection even if an old database
configuration still contains their IDs.

### Persisted Configuration Model

Add a versioned configuration record to the application database. The first
version should contain:

- configuration scope/key and schema version;
- selected engine IDs in deterministic registry order;
- search defaults that are safe for the UI, including country code, search
  type, page count, and result-page size;
- created/updated timestamps;
- optional optimistic-concurrency revision.

The record must be stored as structured, validated data rather than an
unbounded frontend blob. Sensitive values, proxy credentials, browser paths,
and diagnostic secrets are not editable through this page and are never
stored in the UI configuration record. The existing `Config` defaults remain
the fallback and library/CLI behavior remains backward compatible.

Configuration writes must be atomic. Invalid engine IDs, duplicate IDs,
disabled engines, unsupported search types, and invalid numeric values return
structured validation errors without replacing the last valid configuration.

### API Contract

Extend `/api/v1` with configuration endpoints:

- `GET /configuration` returns the effective configuration, its source
  (`persisted` or `defaults`), revision, and available engine metadata.
- `PUT /configuration` validates and atomically persists the selected engines
  and UI-safe defaults.
- `POST /configuration/reset` removes the persisted override and returns the
  complete registry-based defaults.
- `GET /engines` exposes the available registry metadata independently for
  UI and MCP clients.

Search submission must resolve omitted engine options through this service.
The response should include the effective engine list and configuration
revision used by the job so historical runs remain explainable after a later
configuration change.

The configuration endpoints use the same validation and service layer for the
UI, CLI integrations, and MCP. MCP should expose `get_configuration`,
`update_configuration`, `reset_configuration`, and `list_engines` only after
the same authorization boundary is applied as the HTTP API.

### Configuration Page

Add a dedicated configuration view to the UI:

- list every available registry engine with a stable label and current state;
- select or deselect enabled engines using accessible checkboxes;
- mark disabled engines as unavailable with a non-editable reason;
- show the active source, current revision, and effective engine count;
- edit safe search defaults such as country, type, pages, and page size;
- save atomically, display validation errors, and preserve the last valid
  state on failure;
- provide a reset-to-defaults action with confirmation;
- reflect a successful configuration change in the next search without a full
  browser reload.

The search form must load its engine choices from `/configuration` or
`/engines`, not from a hardcoded JavaScript list. By default, all available
enabled engines are selected. The user may narrow the selection for an
individual search, while the persisted configuration remains unchanged unless
the user saves it explicitly on the configuration page.

### Automatic Result Refresh

The UI must refresh active jobs and result/history views automatically:

- poll the job status and event endpoint with bounded backoff while a job is
  queued or running;
- refresh result rows when the persisted result count or job revision changes;
- refresh the history summary after a terminal job state;
- stop polling on completion, failure, cancellation, or a bounded timeout;
- avoid duplicate requests when manual refresh and polling overlap;
- retain the current filter, selected engine, pagination, and scroll position
  when rows are replaced.

The initial implementation may use HTTP polling. The API contract should
retain a revision or event cursor so a later SSE/WebSocket implementation can
replace polling without changing UI semantics. Polling errors must be visible
but must not erase already displayed results.

### Implementation Slices

1. Add a registry metadata service and explicit default-selection resolver.
2. Add the versioned configuration table/repository, validation, atomic update,
   reset behavior, and configuration-source metadata.
3. Apply persisted configuration during API search submission and include the
   effective engine list/revision in job records and responses.
4. Add configuration and engine API endpoints plus API contract tests.
5. Add the UI configuration page, accessible engine selection, safe defaults,
   save/reset flows, and validation feedback.
6. Replace the current one-shot UI refresh with bounded automatic polling and
   result/history refresh while preserving filters and active job context.
7. Add MCP configuration tools and registry discovery backed by the same
   service, then update Compose/API/UI documentation and examples.

### Test and Acceptance Strategy

- Registry tests verify that all enabled plugins are discoverable and disabled
  plugins cannot be selected.
- Configuration repository tests verify defaults, persistence, atomic writes,
  reset behavior, schema versioning, and restart persistence using SQLite;
  PostgreSQL integration coverage uses the Compose database.
- API tests verify precedence of explicit request, persisted configuration,
  and defaults; validation errors must leave the previous valid record intact.
- UI tests verify complete default engine selection, individual selection,
  disabled-engine display, save/reset behavior, and accessible error states.
- Refresh tests verify polling backoff, terminal stop conditions, revision-
  based result updates, filter preservation, and no duplicate concurrent
  refresh requests.
- MCP tests verify configuration-tool schemas and delegation to the shared
  configuration service without duplicating validation.
- A deterministic Compose smoke test starts with no configuration, confirms
  that all available engines are selected, persists a reduced selection,
  restarts the app, and confirms that the selection and search behavior remain
  available from both UI/API and MCP.

### Acceptance Criteria

- A fresh installation searches all currently available and enabled registry
  engines when no persisted configuration exists.
- The UI configuration page lists registry-backed engines and allows users to
  save a valid subset without editing source code.
- Persisted configuration survives app/container restarts and is used by
  searches that omit an explicit engine list.
- Explicit per-search engine selection overrides persisted defaults only for
  that search.
- Disabled, unknown, duplicate, or empty selections are rejected safely.
- Configuration changes are visible in the next search and are explainable in
  job/history records through the effective engine list and revision.
- Active jobs and result/history views refresh automatically, stop polling at a
  terminal state, and preserve the user's current filters.
- API, UI, MCP, SQLite, and PostgreSQL paths use one shared configuration and
  registry service; no engine list is duplicated in frontend code.

## Refactoring Phase 8.2 - Current and Historical Result Views with Canonical URLs

### Status

Implemented. This phase improves result presentation and normalization without
changing the provider adapters' safety rules.

### Objective

Provide two clear result views: results from the current search and results
from historical searches. Every displayed failure must identify the affected
search engine. Result tables must use the order `Title`, `URL`, `Relevance`,
`Engine`.

Displayed URLs must be canonical destination URLs. Provider redirect wrappers,
tracking parameters, search-result routes, and image-detail URLs must not be
presented as if they were the destination page. Image results must either be
shown in a separate typed view or excluded from the standard web-result table.

### Implementation Steps

1. Extend the normalized result contract with `canonical_url`, `source_url`,
   `result_kind`, and an explicit relevance value while retaining the raw
   provider URL for diagnostics.
2. Add one shared URL normalizer that unwraps known provider redirect formats,
   removes tracking parameters safely, validates the destination scheme/host,
   and never guesses when the target cannot be proven.
3. Classify image, news, video, shopping, and organic results explicitly;
   prevent image-detail URLs from entering the standard organic-results view.
4. Extend history/API queries with `current` and `historical` scopes,
   run/query/engine filters, and structured engine-attributed failures.
5. Add separate UI views/tabs for the active search and historical archive.
   Render the standard table in the fixed order Title, URL, Relevance, Engine;
   keep snippets and diagnostics in an optional detail view.
6. Refresh only the current-search view while a job is active, then move the
   completed run into the historical view without losing its engine/failure
   attribution.

### Test and Acceptance Criteria

- Current and historical results are separate, selectable views with stable
  filters and pagination.
- Every failure row or failure summary names its search engine and retains the
  provider category/message.
- The standard table columns appear exactly as Title, URL, Relevance, Engine.
- Provider redirects and tracking wrappers resolve to the canonical target URL
  where the target is unambiguous; raw URLs remain available only in details.
- Image-detail URLs are excluded from organic results and covered by fixtures.
- Offline fixtures cover redirect wrappers, tracking parameters, canonical
  URLs, image results, malformed URLs, and engine-specific failures.
- API, UI, and persistence tests verify current/history separation and stable
  result ordering without browser or network access.

### Implementation Notes

- Result payloads retain `source_url` and expose a validated `canonical_url`,
  typed `result_kind`, and rank-derived `relevance` value.
- Google, DuckDuckGo, and Bing-style redirect wrappers are unwrapped only when
  their destination is explicit; tracking parameters are removed from the
  displayed URL while raw provider URLs remain available for diagnostics.
- The API exposes run-scoped results and failures, and the UI provides current
  and historical views with engine-attributed failure tables and the fixed
  `Title`, `URL`, `Relevance`, `Engine` result order.

## Refactoring Phase 8.3 - Compact Result Workspace and Result Retention Controls

### Status

Implemented. The UI now uses a compact responsive workspace, groups results by
canonical URL, lists all contributing engines, and provides explicit deletion
controls for individual searches or the complete result archive.

### Implementation Notes

- Desktop views use a fixed viewport shell with independently scrollable data
  panels; narrow screens fall back to natural page flow for accessibility.
- Results are grouped by canonical URL in the UI. The displayed engine column
  contains the sorted set of all engines contributing that URL.
- Group ordering uses the maximum stored relevance value per URL, preserving
  the relevance values produced by SerpScrap's ranking and fusion pipeline.
- The API and history store support deleting one search run, its results and
  failures, or all persisted search runs atomically from the application's
  perspective.

## Refactoring Phase 8.4 - Search Progress and Visible Result Panels

### Status

Implemented. Active searches now expose persisted progress metadata and the UI
renders a visible progress bar with job counts, current engine, elapsed-time
based remaining-time estimates, and a terminal state.

The result panels use a grid/flex layout with normal document flow. Current and
historical result tables remain visible in their containers, and long result
sets extend the page naturally. The browser's vertical scrollbar is the only
scroll mechanism on desktop, avoiding nested scrollbars or clipped content;
narrow screens retain the same accessible behavior.

## Phase 7 - Abschlussstatus

Phase 7 ist abgeschlossen. Die homepage-basierte Selenium-Suche, die
engine-spezifischen Browser-Verträge, sichtbare Fortschrittsmeldungen,
korrelierte Diagnoseartefakte, typed Provider-/Empty-/Malformed-Outcomes,
partielle Ergebnisse und die artefaktgestützten Selector-Korrekturen sind
implementiert und dokumentiert.

Der praktische Lauf bestätigt stabile erfolgreiche Pfade für Bing, Yahoo,
DuckDuckGo, Startpage, Brave, Swisscows und Mojeek. Yandex und Qwant werden
als blockiert erkannt. Die automatische Consent-Ausführung für Google und
Ecosia bleibt ein bewusst dokumentiertes TODO für eine spätere Phase: Die
Provider liefern die Consent-Struktur dynamisch beziehungsweise über
nachgelagerte Komponenten, die im aktuellen Selenium-Lauf nicht zuverlässig
interagierbar sind. Das Verhalten bleibt deshalb sicher als
`consent_required` klassifiziert.

### Abschluss-Checkliste

- [x] Homepage-zu-SERP-Flow mit per Engine dokumentierten Verträgen
- [x] Fortschritt, Korrelation, redigierte HTML-Artefakte und Manifeste
- [x] Provider-Zustände, Empty-/Malformed-Semantik und Terminal-Summaries
- [x] Fixture- und Regressionstests für die Phase-7-Korrekturen
- [x] Konfiguration, CLI-Beispiele und Changelogs aktualisiert
- [ ] Google-/Ecosia-Consent-Automation in einer späteren Phase stabilisieren

## Refactoring Phase 7.3 - Produktionsreife Provider-Zustände und Browser-Flow-Härtung

### Objective

Turn the artifact findings from the latest Phase-7 run into deterministic,
provider-aware terminal behavior. Phase 7.3 closes the gap between what the
rendered browser page shows and what the public result/failure contract
reports: a valid SERP must remain parseable, an explicit provider control must
remain a typed failure, an empty or malformed response must not look like a
successful populated search, and a post-submit navigation problem must expose
its actual state instead of becoming an unexplained timeout.

This phase is an implementation-hardening phase. It keeps provider controls
non-bypassable, keeps diagnostic capture opt-in, preserves partial results
from healthy engines, and makes engine-specific behavior configurable without
weakening the shared flow or broadening selectors globally.

### Implementation Status

The first implementation slice is complete: the shared flow now exposes
post-submit navigation/state events, recognized empty pages are terminal
`empty` outcomes, unrecognized zero-card pages are `malformed`, terminal
category summaries are included in reports, and retryable engine categories
are validated through configuration. Provider-specific fixture promotion and
the remaining live-state corrections continue to be verified through the
focused Phase-7 test suite.

The subsequent artifact review also promoted current selectors for Brave,
Startpage, Swisscows, and Mojeek and added explicit Qwant HTTP-403 blocking;
each change is backed by a sanitized fixture and a parser/classifier
regression test.

### Evidence and Scope from the Latest Run

- Bing, Yahoo, and DuckDuckGo completed with 2, 7, and 12 parsed results;
  progress, terminal artifacts, result counts, and correlation IDs are now
  available for these successful paths.
- Yandex was correctly observed at `/showcaptcha` and reported as `blocked`.
- Mojeek reached a SERP-ready state but produced zero parsed cards and was
  still reported as a successful job. This must become an explicit `empty` or
  `malformed` outcome according to fixture evidence.
- Brave and Ecosia still ended as `selector_drift` before a usable input was
  found. The next step is provider-specific DOM/URL evidence, not broader
  input selectors: Brave must be distinguished between a real challenge and a
  normal localized homepage, while Ecosia's consent overlay must be detected
  even when its text is not exposed through Selenium body text.
- Qwant and Startpage reached or retained their post-submit routes but ended
  in timeouts; Swisscows also timed out despite the known rate-limit/privacy
  mixture. Their state transitions and wait predicates are not yet explicit
  enough for reliable terminal classification.
- The current run produced 14 results across ten jobs. Phase 7.3 must retain
  this partial-success behavior while making the six non-populated outcomes
  individually actionable.

### Production Principles

- Use a finite, observable browser state machine: homepage requested, homepage
  ready, input available, submitted, navigation observed, SERP/empty state
  ready, classified failure, parsed, and terminal.
- Evaluate provider-specific URL and DOM evidence before generic timeout or
  selector-drift fallbacks. Do not infer a block or rate limit from hidden
  scripts, metadata, privacy footers, or unrelated localized text.
- Treat `blocked`, `consent_required`, `rate_limited`, `empty`, `malformed`,
  `selector_drift`, and `timeout` as distinct public outcomes with stable
  retry policy. A zero-result page is never a populated success.
- Keep all access-control responses non-bypassable. The implementation may
  report, stop, or apply a configured bounded retry policy, but it must not
  solve challenges, evade rate limits, or invent consent interaction.
- Keep provider-specific contracts in registry metadata and fixtures. Shared
  flow code may orchestrate states and diagnostics, but must not accumulate
  provider-specific selector exceptions.

### 1. Introduce an Explicit Provider-State Machine

- Define the allowed lifecycle states and transitions for one engine/page job,
  including the distinction between waiting for a state and classifying a
  state.
- Add a typed terminal outcome carrying category, final URL host/path,
  result count, selector key, elapsed time, and correlation ID. Keep the
  existing normalized result rows and public JSON shape compatible.
- Make wait predicates observe three independent signals: URL transition,
  provider-specific DOM readiness/empty markers, and visible rendered state.
  A timeout is emitted only after these signals have been checked and the
  last observed state is recorded.
- Emit a final `state_classified` event before `results_parsed` or failure, so
  progress and manifests explain why a page was accepted or rejected.
- Ensure driver cleanup and artifact terminal recording execute for every
  state-machine exit, including malformed HTML and unexpected WebDriver
  exceptions.

### 2. Correct Empty, Malformed, and Zero-Result Semantics

- Add an engine contract for recognized empty-result markers and for the
  minimum valid organic-card evidence required for a populated SERP.
- Change Mojeek handling so a SERP-ready page with no recognized organic cards
  is reported as `empty` only when its empty fixture/state matches; otherwise
  report `malformed` or `selector_drift` with the attempted card selector.
- Prevent `result_count=0` from being represented as an unconditional
  successful terminal job. Preserve the distinction between a valid provider
  empty state and a parser that failed to find cards.
- Add result-count and outcome fields consistently to progress events,
  `FailureRecord`, terminal manifests, and the final operator summary while
  retaining successful results from other engines.

### 3. Resolve Brave and Ecosia Homepage Classification

- Promote sanitized rendered artifacts from the latest run into narrowly
  scoped fixtures after manual review; retain raw artifacts only under local
  `logs/`.
- For Brave, define a provider-specific challenge signal based on reliable
  visible DOM/URL evidence and test it against both a blocked fixture and a
  normal homepage fixture. Hidden locale/script mentions alone must not cause
  `blocked`.
- For Ecosia, identify the consent overlay's stable role/attribute/container
  evidence and classify `consent_required` before input lookup. A normal page
  with no overlay must continue to use the normal input contract.
- Record the selector candidate and observed DOM evidence in diagnostics, but
  do not fall back to arbitrary inputs or click consent controls implicitly.

### 4. Make Post-Submit Handling Deterministic for Qwant, Startpage, and Swisscows

- Split submit into explicit click/Enter, navigation-observed, and result-
  state-wait phases. Capture the URL after each phase and include it in the
  terminal artifact and failure record.
- For Qwant, classify challenge/consent pages before reporting timeout and
  report a homepage-stuck response as a dedicated navigation/state failure
  when no SERP or empty marker appears.
- For Startpage, distinguish the legitimate `/sp/search` route from a
  challenge/consent response and verify the documented organic-card selector
  against sanitized fixture variants.
- For Swisscows, add a deterministic rate-limit predicate with precedence over
  generic privacy/consent markup; preserve a bounded timeout only when no
  explicit provider state is visible.
- Add per-engine timeout and readiness configuration where needed, with
  documented defaults and validation against unsafe/unbounded values.

### 5. Configuration, Retry, and Operator Feedback

- Document and validate per-engine enablement, page limits, timeout values,
  retry policy, progress format, and diagnostic capture settings as one
  coherent configuration surface.
- Define retryability by terminal category: access-control and consent states
  remain non-bypassable by default, while transient navigation/timeouts may
  use the existing bounded policy. Never retry a selector failure as if it
  were a rate limit.
- Extend the final summary with counts by terminal category and a compact
  per-engine table containing result count, final URL path, and next operator
  action.
- Keep stdout limited to the result contract; send progress and diagnostic
  summaries to stderr or the manifest. Ensure redaction and correlation
  behavior remains unchanged.

### 6. Fixtures, Tests, and Verification

- Add sanitized fixtures for Mojeek empty and malformed responses, Brave
  blocked versus normal homepage, Ecosia consent versus normal homepage,
  Qwant homepage-stuck/challenge, Startpage route/challenge, and Swisscows
  rate-limit/privacy precedence.
- Add state-machine tests for every legal terminal path, repeated polling,
  URL-only transitions, DOM-only transitions, mixed visible markers, and
  cleanup after exceptions.
- Add integration-style mocked-WebDriver tests proving that a valid SERP is
  parsed before incidental hidden markers are considered, that zero cards do
  not become populated success, and that post-submit URLs reach the public
  failure metadata.
- Verify configuration validation, retry classification, progress/result
  separation, artifact manifests, correlation propagation, and partial-result
  retention.
- Run the offline suite with diagnostics disabled and the focused diagnostic
  suite with mocked drivers. Execute one low-volume live run only for the
  providers whose state remains fixture-insufficient; do not make live access
  part of the default test gate.

### Phase 7.3 Acceptance Criteria

- Every job ends in a documented typed outcome; no provider-control response
  is reported as unexplained selector drift or timeout when evidence exists.
- Mojeek zero-card behavior is explicitly `empty` or `malformed`, never an
  unconditional successful populated parse.
- Brave and Ecosia distinguish challenge/consent states from normal homepage
  selector drift using fixture-backed provider evidence.
- Qwant, Startpage, and Swisscows expose post-submit URL/state and classify
  challenge, consent, rate-limit, empty, malformed, and timeout outcomes
  deterministically.
- Valid Bing/Yandex-style SERPs remain parseable even when raw HTML contains
  incidental hidden marker text.
- Progress, artifacts, manifests, failure records, and operator summaries
  agree on category, result count, final URL path, and correlation ID.
- Existing successful results, normalized output, driver cleanup, and
  diagnostic redaction behavior remain regression-free.

## Refactoring Phase 7.2 - Provider-State-Klassifizierung und Selector-Korrekturen aus Artefaktbefunden

### Objective

Use the rendered HTML artifacts from the latest Phase-7.1 run to correct provider-state classification and engine-specific browser behavior without weakening access-control handling or broadening selectors indiscriminately. Separate genuine `rate_limited`, `blocked`, and `consent_required` responses from false positives caused by hidden scripts or generic privacy text, classify Brave/Ecosia challenges before waiting for a search input, and make every terminal failure traceable through its correlation ID.

Phase 7.2 is evidence-driven adapter hardening. It preserves partial results and the normalized result contract, keeps diagnostic HTML opt-in, and promotes selectors only when captured artifacts and offline fixtures support the change.

### Evidence and Scope from the Latest Run

- The latest run completed all ten configured engine jobs with visible `10/10` progress and retained partial results.
- Brave's failure artifact contains CAPTCHA/challenge signals while the homepage input is unavailable. This is an access-control state, not selector drift.
- Ecosia's failure artifact contains a large consent overlay and no usable search input. Consent must be classified before input lookup.
- Bing's failure artifact contains a normal page title and many `b_algo` cards, while the job was classified as `rate_limited`; hidden JavaScript/consent text is likely producing a false positive.
- Yandex's failure artifact contains a normal result title and many `.serp-item` cards, while the job was also classified as `rate_limited`; the same raw-HTML false-positive risk applies.
- Qwant remains on the homepage after submit and its failure artifact contains CAPTCHA/consent signals. Startpage reaches `/sp/search` but its artifact contains CAPTCHA/consent content. Swisscows contains `too many requests` alongside privacy/consent text and needs deterministic precedence.
- The run manifest contains correlation IDs, but final CLI `FailureRecord` warnings still print `correlation_id=None`; the correlation must be propagated into the report boundary.

### Production Principles

- State classification uses a strict precedence and evidence boundary: explicit provider block/challenge URL or visible marker, explicit rate-limit status, explicit consent interstitial, SERP-ready success, empty result, then timeout/malformed. Generic words in scripts, metadata, privacy footers, or hidden JSON do not determine a terminal state.
- A page that contains a valid SERP-ready container and organic cards is not rejected solely because unrelated hidden markup contains `privacy`, `consent`, `captcha`, or `rate limit` strings.
- Access-control responses are observed and reported; the implementation does not solve CAPTCHA, rotate identities, bypass consent, or retry rate limits outside the configured policy.
- Selector changes are provider-specific, fixture-backed, and narrowly scoped. A challenge/consent page is classified before selector fallback so it is not mislabeled as selector drift.
- Correlation IDs are generated at job creation and survive browser events, artifact manifests, `FailureRecord`, logging, and the public report metadata.

### 1. Refine the Shared Response-State Classifier

- Split classification into URL evidence, visible rendered-text evidence, DOM-state evidence, and raw-HTML diagnostics. Only the first three may produce an operational state; raw HTML remains diagnostic context.
- Add a classifier input for rendered body text or an equivalent provider-scoped visible-text snapshot. Exclude script/style contents, embedded JSON, metadata, tracking payloads, and privacy-policy footer text from state detection.
- Define a typed precedence table: provider challenge/CAPTCHA or access-denied URL/visible marker -> `blocked`; provider-specific HTTP/DOM rate-limit marker or visible `too many requests` state -> `rate_limited`; consent interstitial/overlay preventing search -> `consent_required`; recognized result container with valid organic cards -> parseable SERP; recognized empty-result state -> `empty`; otherwise timeout or malformed according to the wait outcome.
- Make the precedence deterministic for mixed pages such as Swisscows, where rate-limit evidence must not be hidden by generic consent/privacy text.
- Keep provider-specific markers in adapter metadata rather than adding more global keyword matches.

### 2. Correct Brave and Ecosia Pre-Input Handling

- Run an early homepage-state classification immediately after navigation and before `_wait_for_input()`.
- Add Brave challenge/CAPTCHA URL and visible-marker fixtures from `brave-p1-failure-4f3d7e67e328.html`; return `blocked` instead of `selector_drift` when the challenge page owns the DOM.
- Add Ecosia consent-overlay selectors/markers from `ecosia-p1-failure-1d98ee9ecca1.html`; return `consent_required` before looking for the input field.
- Preserve selector drift for a genuine normal homepage with no matching input, and include the attempted selector key in diagnostics.
- Update registry metadata and `docs/searchengines.md` with the observed challenge/consent states, not with broader input selectors that could target unrelated page controls.

### 3. Validate Bing and Yandex SERP Success Before Rejecting

- Reproduce Bing from `bing-p1-failure-a7d617316762.html` and Yandex from `yandex-p1-failure-038c1fc08485.html` using sanitized fixtures.
- Assert that Bing's `#b_results`/`li.b_algo` and Yandex's `.serp-item` organic containers are evaluated before generic hidden-text markers.
- Add provider-scoped visible markers for genuine rate limits and remove or narrow raw HTML matches that occur in JavaScript, analytics payloads, privacy links, or unrelated modules.
- Ensure the browser flow waits for a result container and parser output before issuing a rate-limit failure when both SERP cards and incidental rate-limit text are present.
- Keep genuine provider rate limits as non-bypassable typed failures and preserve retryability only where the configured request policy permits it.

### 4. Fix Qwant, Startpage, and Swisscows State/Submit Diagnostics

- For Qwant, capture the post-submit URL and DOM transition; classify challenge/consent when present and report a submit/navigation failure when the page remains on the homepage without a recognized terminal state.
- For Startpage, distinguish the legitimate `/sp/search` result route from its CAPTCHA/consent response and retain the artifact URL path in the failure record.
- For Swisscows, add a specific rate-limit fixture and precedence test for `too many requests` plus privacy/consent markup; do not silently retry or treat it as a selector failure.
- Add post-submit state events for `submit_clicked`, `navigation_started`, `serp_waiting`, and `state_classified` so provider behavior can be diagnosed without relying only on timestamps.

### 5. Correlation, Results, and Operator Feedback

- Pass each `EngineJob.correlation_id` into `FailureRecord.correlation_id`, CLI warning fields, progress events, and final report metadata.
- Include `result_count` and the selected terminal category in human-readable progress output; a `results_parsed` event with zero rows must be visible and distinguishable from a successful populated parse.
- Add a per-engine terminal summary to the run manifest containing state, result count, failure category, artifact paths, and final URL host/path without query parameters.
- Preserve the existing stdout JSON contract; all progress and diagnostic summaries remain on stderr or in the manifest.

### 6. Fixtures, Tests, and Verification

- Promote sanitized artifacts into fixtures only after removing queries, tracking IDs, cookies, tokens, and unrelated third-party content.
- Add classification fixtures for Brave blocked, Ecosia consent, Bing valid SERP with incidental hidden markers, Yandex valid SERP with incidental hidden markers, Qwant challenge/consent, Startpage challenge/consent, and Swisscows rate limit.
- Add contract tests for pre-input classification, classifier precedence, visible-text extraction, SERP-before-rate-limit behavior, Qwant/Startpage navigation outcomes, correlation propagation, zero-result reporting, and driver cleanup.
- Run the offline suite with diagnostic capture disabled and the focused artifact/classifier suite with capture enabled. Repeat one low-volume live diagnostic run only for providers whose fixture evidence remains insufficient.
- Verify that no raw HTML under `logs/` is committed and that all promoted fixtures are stored under engine-specific fixture directories.

### Phase 7.2 Acceptance Criteria

- Brave and Ecosia challenges are reported as `blocked`/`consent_required`, not `selector_drift`.
- Bing and Yandex valid SERP artifacts are parsed successfully when incidental hidden markup contains privacy/rate-limit terms.
- Swisscows rate limits are classified deterministically as `rate_limited` when the explicit marker is present.
- Qwant and Startpage failures expose the actual post-submit state and final URL path; no homepage-stuck case is reported as an unexplained timeout.
- Every terminal failure has a non-null correlation ID in progress events, artifacts, `FailureRecord`, and CLI output.
- Progress output shows populated versus zero-result parses, and the run manifest summarizes every engine/page terminal state.
- Offline tests cover all artifact-derived states, while provider controls remain non-bypassable and live testing remains opt-in.

## Refactoring Phase 7.1 - Laufdiagnostik, sichtbarer Fortschritt und HTML-Artefakte

### Objective

Make Phase-7 browser runs diagnosable without turning normal scraping into noisy or unsafe logging. Every configured query/engine/page job must expose visible, structured progress through its lifecycle, while an explicit diagnostic mode may save sanitized, fully rendered homepage and SERP HTML under `logs/` for selector analysis. The recorded artifacts must make the Brave/Ecosia selector drift and the observed blocked, consent, and rate-limited states from `docs/phase7.log` reproducible and distinguishable without leaking query data, cookies, headers, credentials, or unrelated page content.

Phase 7.1 is an observability and selector-research phase. It does not bypass provider controls, retry blocked requests aggressively, or make HTML capture the default. Existing partial-success behavior remains: one diagnostic or provider failure is attached to its engine/page and does not discard successful results from other jobs.

### Evidence from the Phase-7 Practical Run

- The run started one query with four workers and completed with ten parsed fused results, so concurrent execution and partial-result retention are working at a high level.
- Brave and Ecosia failed before submission with `selector_drift: search input not available`; their homepage DOM, consent state, and hydration timing must be captured before changing selectors.
- Two engines returned `blocked`, one returned `consent_required`, and two returned `rate_limited`; these states must be tied to the engine, phase, URL, timing, and correlation ID rather than reported as indistinguishable failures.
- The log has no correlation IDs and does not show per-engine state transitions or elapsed time, which prevents reliable mapping from a warning to a rendered page and selector candidate.
- The existing result output contains provider overlap (for example Yahoo/DuckDuckGo matches). Diagnostic work must not alter fusion, ranking, or normalized result semantics.

### Current State and Constraints

- Phase 7 already has a declarative selector contract and a shared homepage-to-SERP flow, but progress is currently visible only as start/completion and partial-failure log messages.
- A Selenium `page_source` snapshot is needed after JavaScript rendering and after each relevant state transition; raw HTTP responses are insufficient for hydrated providers such as Brave and Ecosia.
- HTML can contain the keyword, account identifiers, consent tokens, cookies, hidden form values, result-page content, and tracking URLs. Capture must be opt-in, bounded, redacted, and excluded from normal artifacts and version control.
- Concurrent workers may finish out of order. Progress output must remain thread-safe, structured, and correlated without exposing the keyword in log messages or filenames.
- Provider blocks, consent pages, rate limits, empty results, selector drift, timeouts, and successful extraction are different states and must remain different in both logs and failure records.

### Production Principles

- Emit one structured progress event for each state transition: job accepted, driver created, homepage requested, homepage ready, input found, keyword submitted, SERP requested/ready, HTML captured, results parsed, provider state classified, job completed, or job failed.
- Every event carries a correlation ID, engine, page, worker/job identity, state, elapsed duration, attempt number, and redacted URL metadata; query text, cookies, authorization headers, and full page content are never logged by default.
- Human-readable progress is enabled for interactive CLI runs, while machine-readable JSON Lines remains available for CI and post-run analysis. Progress must not corrupt the final JSON result written to stdout or the configured output file.
- HTML capture is disabled by default and enabled only through an explicit diagnostic setting/CLI flag. It has a bounded per-artifact size, a bounded total run size, deterministic retention/cleanup behavior, and a clear warning that captured pages may contain sensitive third-party content.
- Capture happens at meaningful boundaries, not on every polling tick: at minimum homepage-ready, pre-submit, SERP-ready, and classified failure. Failed jobs retain the last available rendered snapshot when capture is enabled.
- Artifact naming uses a non-reversible query/job digest plus engine, page, state, timestamp or run ID, and correlation ID. The original query is stored only in the in-memory job/report context and is not written into the filename or diagnostic HTML metadata.

### 1. Progress Event Model and CLI Presentation

- Define an immutable `ProgressEvent` with `run_id`, `correlation_id`, `query_index`, `engine`, `page`, `state`, `attempt`, `elapsed_ms`, `url_host/path` (without query parameters), `selector_key`, and optional `artifact_path`.
- Add a thread-safe progress sink protocol with a console implementation and a JSONL implementation. The sink must tolerate worker completion order and preserve a monotonic event sequence per run.
- Extend the CLI start message with total jobs and worker count, then render compact updates such as `[3/11] brave page=1 homepage_ready` and terminal summaries with success/failure counts. Keep progress on stderr so stdout remains valid JSON.
- Include the selected diagnostic mode, artifact directory, retention limits, and redaction policy in the run summary without printing keywords or sensitive values.
- Preserve correlation IDs in `FailureRecord`, structured logger fields, progress events, and diagnostic artifact manifests so one engine failure can be traced end to end.

### 2. Rendered HTML Capture and Safe Artifact Store

- Add a dedicated artifact store rooted at `logs/phase7/<run_id>/` or a configured equivalent; never write diagnostic pages into source, fixture, cache, or package directories.
- Capture `driver.page_source` after the homepage-ready and SERP-ready waits, immediately before submit when requested, and on classified failure. Store a small JSON manifest beside each page with engine, state, page, correlation ID, observation time, current URL host/path, byte count, redaction version, and selector metadata.
- Redact before writing: query values in URLs/forms, cookies, authorization or proxy data, account identifiers, session/CSRF tokens, unique request IDs where practical, and configured secret patterns. Use a conservative fallback that refuses to write an artifact when redaction fails.
- Enforce maximum bytes per HTML file, maximum artifacts per job, maximum total run bytes, and an explicit retention policy. Write atomically through a temporary file and remove incomplete artifacts on failure.
- Add an index/manifest for the run that maps engine/page/state/correlation ID to artifact paths and records missing snapshots. Do not make the manifest depend on the final result JSON.
- Add `.gitignore` coverage and documentation so `logs/` remains local diagnostic output; sanitized fixtures promoted for tests belong under `tests/fixtures/searchengines/<engine>/` only after manual review.

### 3. Selector-Drift Investigation Workflow

- Reproduce the practical run with a fixed low-volume query set, one engine at a time and then with the configured worker count, using diagnostic capture and visible progress enabled.
- For Brave and Ecosia, compare homepage-ready snapshots, input candidate matches, hydration timing, consent/block states, and post-submit SERP snapshots before changing selectors. Record the observed DOM attributes and selector decision in `docs/searchengines.md`.
- For blocked, consent, and rate-limited engines, inspect the rendered page and URL classification without attempting bypasses. Decide whether the correct action is a typed failure, a provider-specific consent workflow allowed by policy, a longer bounded wait, or an engine readiness downgrade.
- Promote a selector from `candidate` to `fixture-verified` only after the captured HTML is sanitized, a parser/flow fixture test passes, and the selector is scoped to the intended form/card rather than a broad page element.
- Keep an evidence table for each changed selector: run ID, observation date, country/language, viewport/browser identity, old selector, new selector, fixture path, and reason for the change.

### 4. Tests and Verification

- Add unit tests for event ordering, thread-safe sinks, monotonic run sequence, redacted URLs/messages, progress-on-failure, and stdout/stderr separation.
- Add artifact-store tests for opt-in behavior, naming without query text, HTML/manifest atomicity, redaction, size limits, retention, incomplete-write cleanup, and concurrent writers.
- Add mocked-WebDriver contract tests proving snapshots occur after readiness and failure classification, artifact paths are included in progress events, and `quit()` still executes on every path.
- Add regression fixtures for Brave and Ecosia once a sanitized rendered homepage/SERP is reviewed; add explicit fixtures for blocked, consent, and rate-limited states observed in `docs/phase7.log`.
- Run the existing offline suite with diagnostics disabled, then run a focused diagnostic suite with mocked drivers. Keep live provider reproduction opt-in, low-volume, and outside the default CI gate.

### 5. Documentation and Operations

- Document the CLI/configuration switches for progress format, diagnostic HTML capture, output directory, redaction, size limits, retention, and cleanup.
- Add a troubleshooting section linking `docs/phase7.log`, the run manifest, progress events, failure records, and the selector matrix in `docs/searchengines.md`.
- Add a safe operator procedure: stop capture after evidence is collected, review artifacts locally, sanitize selected fixtures manually, delete raw artifacts, and never attach raw third-party pages to tickets or commits.
- Record the first diagnostic run, selector decisions, disabled/experimental engines, and unresolved provider-control responses in the Phase 7.1 changelog.

### Phase 7.1 Acceptance Criteria

- Interactive runs show each job's engine/page state transition and a final success/failure summary without contaminating JSON stdout.
- Every failure in the practical-run classes can be traced by correlation ID to a structured event and, when explicitly enabled and safely captured, a rendered HTML artifact.
- Brave and Ecosia have an evidence-backed selector decision or an explicit `experimental`/`disabled` status; no selector is widened blindly.
- HTML diagnostics are opt-in, redacted, bounded, atomically written, ignored by Git, and never required for normal tests or production scraping.
- Offline tests cover progress, artifact safety, failure-state classification, and driver cleanup; live reproduction remains opt-in and provider-policy compliant.
- The Phase 7.1 plan, implementation status, practical findings, and selector changes are recorded in both changelogs.

## Refactoring Phase 7 - Browser-Based Search Flow and Per-Engine Selector Contracts

### Objective

Implement and verify the complete browser interaction for every registered search engine. A scrape starts on the engine's homepage, waits for the document to become usable, enters the keyword into the engine-specific search field, submits the form, waits for the search-result page, and extracts only the supported organic results. The homepage URLs, input/submit selectors, result-ready conditions, organic-card selectors, pagination hooks, and consent/block states are documented in `docs/searchengines.md` and promoted to code only after fixture-backed verification.

Phase 7 is provider-adapter work. It keeps the shared browser lifecycle, normalized result contract, concurrency limits, failure model, and provider-safety rules from earlier phases. It does not bypass CAPTCHAs, consent controls, rate limits, robots guidance, or other access controls, and it does not make live provider access part of the default test suite.

### Current State and Constraints

- `docs/searchengines.md` currently documents direct result-page URL baselines and broad result-page reconnaissance, but not the homepage-to-form-to-submit interaction required for browser-driven scraping.
- Search forms and SERP markup are dynamic and can vary by country, language, consent state, viewport, and experiment. Selectors are therefore ordered candidates with observation dates, not permanent provider guarantees.
- Some providers render the form or result cards after JavaScript hydration; others expose a server-rendered or HTML-friendly surface. Each adapter must declare its readiness condition and classify an unusable page instead of waiting indefinitely.
- The shared driver factory owns browser settings and teardown. Engine adapters own navigation, form interaction, provider-specific waits, selector fallback order, pagination state, and response classification.
- Offline tests must use sanitized HTML fixtures and mocked WebDriver behavior. Live smoke tests remain opt-in, low-volume, and policy-compliant.

### Production Principles

- Every engine follows one observable state machine: `homepage_requested` -> `homepage_ready` -> `query_entered` -> `submitted` -> `serp_ready` -> `results_extracted`, with typed terminal states for empty, consent, CAPTCHA/block, rate-limit, timeout, malformed, and unsupported-country responses.
- Homepage navigation is explicit and precedes form interaction. Direct result URLs remain a separate optimization only when the adapter contract and provider policy allow them.
- Selectors are stored in adapter metadata in priority order, scoped to the intended form or organic result container, and covered by at least one normal fixture plus relevant fallback/error fixtures.
- Submission must use the provider's accessible form semantics (submit control or keyboard submission) and must be followed by a URL, DOM, or state-change wait; fixed sleeps are not a readiness strategy.
- Parsers receive captured HTML independently of Selenium and return the same normalized fields defined by the Phase 5/6 contract. Ads, AI answers, knowledge panels, navigation, duplicate sitelinks, and unrelated modules are excluded.
- A selector drift or access-control response disables only the affected engine/page and preserves successful results from other engines.

### 1. Shared Browser Interaction Contract

- Add an immutable engine interaction descriptor containing homepage URL, search-field selector candidates, submit selector candidates, SERP-ready conditions, organic-card selectors, pagination strategy, locale/country mapping, and fixture/research metadata.
- Add adapter methods for `open_homepage()`, `wait_for_homepage()`, `enter_keyword()`, `submit_search()`, `wait_for_serp()`, `capture_serp()`, and `classify_response()` with correlation IDs and redacted diagnostics.
- Define explicit wait primitives for document readiness, visible/enabled input, successful keyword insertion, URL or DOM change after submit, result container visibility, empty-result state, and provider block/consent states.
- Preserve one driver/session ownership per scrape job and guarantee teardown on successful extraction, timeout, parse failure, cancellation, and classified provider failure.

### 2. Document and Verify Every Search Engine

- Complete the Phase 7 entry-point and selector matrix in `docs/searchengines.md` for Google, Bing, Yandex, Yahoo, DuckDuckGo, Ecosia, Qwant, Startpage, Brave Search, Swisscows, and Mojeek.
- For each engine, record the observed homepage URL, search input locator, submit locator or keyboard fallback, SERP-ready locator/state, organic-card locator, title/link/snippet locators, pagination locator/state, country/locale behavior, and known consent/block signatures.
- Mark each locator as `candidate`, `fixture-verified`, or `live-smoke-verified`; include observation date and provider/plugin version so stale selectors are discoverable.
- Prefer stable attributes such as `name`, `id`, accessible labels, semantic form actions, and provider-owned result classes. Avoid positional XPath, generated CSS class hashes, and broad selectors that can match ads or navigation.
- Keep a documented fallback order and define the failure threshold at which an engine moves to `experimental` or `disabled` instead of silently returning incomplete results.

### 3. Engine Adapter Implementation

- Implement homepage/form/submit/serp behavior behind the existing plugin registry; orchestration must not branch on engine names.
- Add provider-specific consent and empty-result handling before organic parsing, including safe early termination for CAPTCHA, bot, rate-limit, and access-denied pages.
- Add pagination only after the first-page flow is stable. Reuse the adapter's observed next-page/cursor state and validate that the page or result set changed before parsing the next page.
- Normalize redirect links and visible domains through the existing canonicalization boundary, and retain engine, country, query, page, and rank provenance.
- Add bounded diagnostics (URL, state, selector key, timing, and sanitized HTML/screenshot paths when explicitly enabled) without logging keywords, cookies, headers, or page contents by default.

### 4. Fixtures, Tests, and Verification

- Add sanitized fixtures under `tests/fixtures/searchengines/<engine>/` for homepage-ready, query-filled, normal SERP, empty SERP, consent, CAPTCHA/block, rate-limit, malformed, and selector-fallback states where observed.
- Add adapter contract tests proving homepage navigation precedes input, the keyword is entered exactly once, submit is performed, SERP readiness is awaited, organic cards are parsed, and the driver is closed on every terminal path.
- Add selector tests for each documented locator and fallback order, including protection against ads, answer modules, duplicate cards, unsafe redirects, and stale page state.
- Add deterministic tests for country/locale mapping, pagination state changes, timeout/error classification, structured partial failures, redacted diagnostics, and registry import isolation.
- Keep one opt-in, low-volume browser smoke test per provider family or engine risk group; never require live search traffic for unit, CI, packaging, or documentation builds.

### 5. Documentation, Operations, and Migration

- Update the public configuration and contributor documentation with the browser flow, selector metadata lifecycle, fixture refresh process, opt-in smoke-test command, and provider-safety limitations.
- Add a selector review checklist to `docs/searchengines.md`; require a fresh observation date and fixture update before enabling a changed adapter.
- Record disabled/experimental engines and reasons in registry diagnostics, release notes, and the refactoring changelog.
- Roll out in risk order: server-rendered/HTML-friendly engines first, then engines with consent or hydration complexity, and finally engines whose result cards require extensive live verification.

### Phase 7 Acceptance Criteria

- All eleven registered engines have documented homepage URLs and selector contracts with status, observation date, and fallback behavior.
- A normal browser scrape executes homepage load, readiness wait, keyword entry, submit, SERP readiness wait, and organic extraction through the shared adapter contract.
- Every engine has deterministic fixture coverage for normal results and its relevant empty, consent/block, malformed, and selector-fallback states.
- Selector drift, provider access controls, timeouts, and parse failures produce typed engine-scoped failures without discarding successful results from other engines.
- Default tests, linting, type checks, packaging, and documentation builds remain offline and browser-independent; live smoke tests are explicitly opt-in.
- The Phase 7 plan, selector research, implementation status, and any disabled-engine decisions are recorded in both project changelogs.

## Refactoring Phase 6 - Reproducible Read-the-Docs Documentation Build

### Objective

Make the Sphinx documentation build reproducibly on Read the Docs and locally. Add the repository-root `.readthedocs.yaml` required by the current Read the Docs platform, align `docs/conf.py`, `docs/Makefile`, the legacy `docs/_config.yml`, and documentation dependencies, and ensure the published documentation reflects the current Phase-5 API and configuration defaults.

Phase 6 is documentation infrastructure work. It does not change the public search API or provider behavior. The build must remain offline, deterministic, warning-clean, and independent of Chrome, Selenium, network access, SQLite state, and live search providers.

### Current State and Constraints

- No `.readthedocs.yaml` exists in the repository root. Read the Docs expects this file at the top level and currently uses configuration version 2.
- `docs/conf.py` is a legacy Sphinx quickstart configuration with `source_suffix = ['.rst', '.md']`, but the repository has no declared documentation requirements and no explicit Markdown parser dependency.
- `docs/Makefile` is usable for local Sphinx builds but assumes the Sphinx executable is already installed and uses `docs/` as its source directory when invoked from that directory.
- `docs/_config.yml` is a Jekyll-style theme configuration and is not a valid replacement for `.readthedocs.yaml`; its ownership and removal/retention must be decided explicitly.
- The current documentation includes Phase-5 Markdown planning/research files and RST user documentation, so both source formats and their cross-references must be validated.

### Production Principles

- Read the Docs configuration is explicit, version-controlled, and pinned to a supported Ubuntu/Python/Sphinx toolchain.
- Documentation dependencies are declared in one reproducible requirements file; documentation builds never install the full runtime stack or start browser/network services.
- Warnings are treated as build failures in CI and on Read the Docs wherever the selected builder supports it.
- Local `make` builds, CI builds, and Read the Docs use the same `docs/conf.py`, source directory, builder, dependency versions, and environment assumptions.
- Legacy configuration files are either migrated, clearly documented as obsolete, or removed only after references and deployment behavior are checked.

### 1. Read-the-Docs Configuration

- Add a root-level `.readthedocs.yaml` using configuration `version: 2`.
- Configure a supported Linux image and a project-supported Python version, with the selected versions documented as the Phase-6 build baseline.
- Point the Sphinx builder at `docs/conf.py` and explicitly select the HTML builder; decide whether PDF/ePub artifacts are required and enable them only when their dependencies are verified.
- Install the documentation requirements file through the Read the Docs `python.install.requirements` setting.
- Decide whether the package itself must be installed for autodoc/imports; if so, use the supported package installation path without installing Chrome or launching runtime services.
- Add YAML/schema validation coverage so malformed configuration is caught before publication.

### 2. Sphinx and Source-Format Alignment

- Modernize `docs/conf.py` to the current package version, stable project metadata, supported extensions, source paths, theme, static assets, and exclusion patterns.
- Add and pin the Markdown parser needed for `.md` sources, or remove Markdown from `source_suffix` and migrate the published Markdown pages to RST after checking all links and headings.
- Ensure `docs/refactoring2026.md`, `docs/searchengines.md`, and `docs/changelog-refactoring2026.md` are either intentionally included in the toctree or explicitly excluded from the published user documentation.
- Resolve duplicate labels, broken internal references, missing static directories, outdated HTTP links, and stale Google-only wording exposed by a strict Sphinx build.
- Keep the existing `docs/Makefile` as a thin local wrapper around the same Sphinx configuration used by Read the Docs, adding explicit `html`, `linkcheck`, and clean/help behavior only where useful.

### 3. Documentation Dependencies and Local Workflow

- Create `docs/requirements.txt` with a compatible pinned/ranged Sphinx version, Markdown parser/theme dependencies, and any extensions used by `conf.py`.
- Document the supported local commands from the Pipenv environment, including a warning-clean HTML build and an optional link check.
- Keep documentation dependencies separate from runtime and development lock files unless the project deliberately adopts one synchronized lock strategy.
- Verify that local builds do not write outside `docs/_build` and do not require network access after dependencies are installed.

### 4. Content and Navigation Review

- Update `docs/index.rst` and the user-facing pages for current multi-engine defaults, CLI Config inheritance, the four-worker default, normalized results, partial failures, and provider-safety behavior.
- Add navigation for configuration, results, search-engine status, refactoring notes, and changelog content according to the intended public/private documentation boundary.
- Replace stale Read the Docs HTTP links and old package/version references with canonical HTTPS links and current project metadata.
- Add a short contributor section explaining how to build the docs locally and how Read the Docs selects the configuration file.

### 5. Verification and Operations

- Run the complete offline test suite, Ruff, and a clean Sphinx HTML build with warnings treated as errors.
- Run Sphinx link checking with network access disabled where possible; classify unavoidable external-link checks and keep them out of the default deterministic gate if necessary.
- Build at least one additional configured artifact only if it is part of the publication contract.
- Test the build from a clean temporary checkout or clean build directory so stale `_build` output cannot hide missing files.
- Verify the generated output contains the new Phase-5 configuration examples and that no credentials, query contents, browser state, or cache artifacts are included.
- Record the Read the Docs project settings and first successful remote build result in the Phase-6 changelog.

### Phase 6 Acceptance Criteria

- A root-level `.readthedocs.yaml` is valid, uses configuration version 2, and points to `docs/conf.py`.
- Read the Docs can install the declared documentation dependencies and build the HTML documentation without Chrome, Selenium, network search requests, or SQLite setup.
- The same warning-clean Sphinx build succeeds locally through the documented Makefile/Pipenv workflow and in CI.
- All intentionally published RST and Markdown pages parse correctly, appear in the intended navigation, and have no unresolved internal references.
- `docs/_config.yml` is either removed as obsolete or explicitly documented and verified as belonging to a separate workflow.
- The documentation describes current Phase-5 defaults and CLI behavior, and the Phase-6 changes are recorded in both changelogs.

## Refactoring Phase 5 - Production Integration of Configurable Search-Engine Plugins

### Objective

Turn the Phase 4 registry and multi-engine prototype into the supported production path. Integrate the eleven engines listed in `docs/searchengines.md` as independently testable plugins, make the active engine set and the global parallel-request limit straightforward configuration values in both Python and CLI interfaces, and return one stable normalized JSON result list. A configured search must fan out one request per query/engine/page within the configured thread budget, preserve partial results and structured failures, and apply the already defined relevance fusion using result frequency, position, market-share weight, and provider-family safeguards.

Phase 5 does not introduce another public result shape. It completes the Phase 4 contract, replaces reconnaissance adapters and placeholder selectors with fixture-backed engine implementations, and makes configuration behavior explicit, validated, observable, and backwards compatible for Google-only callers.

### Production Principles

- The plugin registry is the only source of truth for supported engine IDs, capabilities, URL construction, parsing, response states, and provider metadata. Application orchestration must never branch on a hard-coded engine name.
- Configuration describes intent (`search_engines`, `country_code`, pages, and parallelism); plugins own provider-specific query parameters, locale mappings, pagination/cursors, selectors, and redirect decoding.
- `num_workers` is the global maximum number of in-flight search-engine requests. `engine_workers` is an optional per-engine ceiling; the effective limit is the lower of both constraints, and URL enrichment has a separate limit.
- One failed, blocked, consent-gated, rate-limited, malformed, or unsupported engine/page produces a structured failure and does not discard successful rows from other engines.
- Every successful row has the same normalized fields regardless of provider, including `search_engine`, uppercase ISO `country_code`, query, page, rank, result type, title, snippet, visible URL/domain, and canonical target URL.
- Fusion is a pure post-processing stage. It never changes provider rows in place, performs network requests, or uses completion order as a ranking signal.
- Live provider behavior is never required for default tests. A plugin can be disabled independently when its contract or provider policy changes.

### Supported Plugin Set and Readiness

- Implement and register concrete plugins for `google`, `bing`, `yandex`, `yahoo`, `duckduckgo`, `ecosia`, `qwant`, `startpage`, `brave`, `swisscows`, and `mojeek` exactly as named in `docs/searchengines.md`.
- Replace the Phase 4 generic/template adapters with provider-specific modules or strategy objects. Each plugin must have its own URL builder, country/locale mapping, pagination implementation, response classifier, organic-card parser, and sanitized fixtures.
- Keep provider-family metadata separate from the public engine ID. Record known upstream relationships and review dates so frequency is not accidentally counted as independent evidence twice.
- Define plugin capabilities for `normal` web search first. A plugin must explicitly declare additional verticals (`image`, `news`, `shopping`, `videos`) before the request validator accepts them for that engine.
- Add a readiness state (`experimental`, `enabled`, `disabled`) and a disable reason to registry metadata. Disabled plugins remain importable for fixture maintenance but cannot be selected in normal configuration.
- Verify wheel/sdist discovery and import isolation: importing the registry must not start Chrome, open a network connection, create a database, or write files.

### 1. User Configuration and Public API

- Add a validated `SearchSettings`/configuration section with:
  - `search_engines`: ordered list or tuple of registered IDs;
  - `country_code`: uppercase ISO 3166-1 alpha-2 result market;
  - `num_pages_for_keyword` and `num_results_per_page`;
  - `num_workers`: global in-flight search request ceiling;
  - optional `engine_workers`: per-engine ceiling or mapping;
  - engine-specific overrides under a namespaced mapping, never as ad-hoc top-level keys;
  - ranking settings (`rrf_k`, provider-family cap, weight snapshot/overrides); and
  - existing cache, retry, pacing, proxy, screenshot, and output settings.
- Preserve `search_engine="google"`/legacy `Config` compatibility by translating it to `search_engines=["google"]`. Do not silently replace an explicitly configured engine list with the legacy default.
- Define an explicit default. The Phase 5 recommended profile is alternative-first and must be documented; a compatibility profile may continue Google-only behavior when a caller supplies no Phase 4 options. The chosen default must be covered by CLI and API tests.
- Validate duplicate engine IDs, unknown/disabled IDs, empty lists, uppercase country codes, positive worker/page bounds, per-engine limits not exceeding the global ceiling, unsupported search types, malformed weight overrides, and impossible provider-family settings before any capture starts.
- Keep user order for deterministic tie breaks while deduplicating repeated engine IDs with an actionable validation error.
- Add CLI options `--engine ENGINE` (repeatable), `--country ISO2`, `--workers INTEGER`, and a clear per-engine limit option or configuration file mapping. Help text must describe that workers are concurrent search requests, not URL-enrichment threads.
- Ensure Python and CLI composition roots construct the same validated settings, registry, runner, cache policy, and fusion service. No CLI-only defaults or API-only engine semantics are allowed.

### 2. Implement Each Engine Against the Shared Contract

- For every engine, freeze a request descriptor containing canonical URL template, encoded query, country/locale parameters, page/cursor semantics, result count, timeout, pacing, retry classification, and request identity.
- Capture normal, localized/country-specific, empty, consent, CAPTCHA/block, rate-limit, malformed, and pagination fixtures under `tests/fixtures/searchengines/<engine>/` with observation date and plugin version metadata.
- Parse only organic web results in the initial production profile. Exclude ads, AI answers, knowledge panels, navigation, related searches, duplicate sitelinks, and provider-specific redirect wrappers unless represented by an explicitly documented result type.
- Normalize result links to HTTP(S), decode only recognized provider redirects, remove tracking fragments/parameters according to the shared canonicalization policy, and retain the original provider URL only in diagnostics.
- Assign ranks from the provider's organic sequence, not DOM order polluted by ads or modules. Preserve provider page number and result type.
- Implement per-engine empty-result and access-control precedence. A page classified as blocked, consent, rate-limited, or malformed must never be parsed as a successful empty page.
- Test every engine through the same conformance suite plus provider-specific edge cases. A selector change must update a fixture and a focused parser test before the plugin is re-enabled.

### 3. Parallel Request Orchestration

- Build immutable jobs for `(query, engine, country_code, page)` in request order and submit them to one bounded executor. The global `num_workers` is the hard upper bound on active capture calls.
- Enforce per-engine semaphores without creating one executor per engine. A single slow engine must not starve other engines when global capacity is available; a per-engine limit of one must still serialize that provider's requests.
- Acquire cache/deduplication before a worker slot and request pacing before network/browser capture. Include plugin version, country, locale, page/cursor, search type, result count, and relevant identity in cache keys.
- Gather futures by job identity, not completion order. Convert all expected plugin/transport exceptions to `FailureRecord` values containing engine, plugin version, country, page, category, retryability, correlation ID, and attempt count.
- Retry only plugin-declared transient failures with bounded backoff. Never retry CAPTCHA, proof-of-work, consent, explicit blocking, authentication, or unsupported-country outcomes automatically.
- Scope circuit breakers to an engine and run. Opening one provider circuit cancels only its pending jobs and leaves other engines running; caller cancellation still shuts down the whole executor safely.
- Guarantee browser, response, semaphore, executor, cache temporary-file, and repository cleanup on success, partial failure, timeout, cancellation, and process interruption.
- Emit structured debug metrics without query contents or credentials: submitted/completed/failed jobs, active workers, cache hits, per-engine latency, retries, circuit state, and parser counts.

### 4. Normalize and Fuse Results

- Convert every plugin result through one assembler into the existing flat JSON-compatible schema. Required common fields remain stable; missing provider fields are `None`, not omitted or stringified.
- Canonicalize URLs conservatively by scheme/host/path/query rules. Group by `(query, canonical_url)` so identical targets from separate queries never influence each other's relevance.
- Use the Phase 4 weighted reciprocal-rank formula as the production baseline:
  `score(url) = sum(weight(engine) / (rrf_k + best_rank_from_engine))`.
  Count at most one best occurrence per engine and optionally cap one contribution per provider family according to validated settings.
- Load a versioned market-share snapshot from `docs/searchengines.md`/the machine-readable configuration. Normalize active-engine weights at run start, expose the snapshot date and fallback `Other` weights in report metadata, and permit explicit operator overrides.
- Select one deterministic representative row per canonical target and add `relevance_score`, `engine_match_count`, `independent_provider_count`, `best_rank`, `matched_engines`, and fusion/version metadata without losing engine/country provenance.
- Sort deterministically by query order, descending score, independent-provider count, engine-match count, best rank, configured engine order, and canonical URL. Results must be invariant under future completion-order changes.
- Preserve raw per-engine rows and per-engine contribution details only through an explicit diagnostic/report API. Saved JSON and CLI stdout use the normalized ranked list only.
- Test permutation invariance, duplicate URLs, tracking parameters, provider-family overlap, missing/fallback weights, rank ties, multiple queries, empty engines, and numeric precision.

### 5. Cache, History, and Schema Migration

- Version cache entries with plugin ID/version and all request dimensions so a parser or URL-policy change cannot reuse incompatible HTML.
- Keep raw captured HTML and normalized fused results separate. Cache hits must carry engine, country, plugin version, page, and cache origin into the parser and diagnostics.
- Decide whether normalized fused rows, raw engine rows, or both are persisted in SQLite history. The public `list[dict]` remains normalized; historical records must retain enough provenance to reproduce ranking.
- Add an explicit schema migration from Phase 4 report version 2. Define behavior for old Google-only rows that have no engine/country/fusion metadata and test reads of pre-Phase-5 cache/history artifacts.
- Make market-share snapshots immutable by run. Updating `docs/searchengines.md` must not silently reorder an existing cached or historical report.

### 6. Documentation, Operations, and Provider Safety

- Update `docs/searchengines.md` from reconnaissance to a plugin status matrix containing implementation status, fixture version/date, supported countries/search types, pagination mode, provider family, terms/API review date, and disable reason.
- Update configuration, results, CLI, README, examples, and installation documentation with multi-engine examples, `--workers` semantics, alternative-first/compatibility profiles, normalized fields, fusion metadata, and partial-failure behavior.
- Document that provider terms, robots guidance, consent flows, rate limits, and result layouts change. No plugin may bypass access controls or rotate identity/proxy automatically to evade them.
- Provide an opt-in low-volume smoke command/matrix with one worker per provider, a harmless query, strict timeouts, and accepted outcomes for honest blocks/consent. It must never run in CI's default test job.
- Add operational metrics and logs sufficient to disable one engine quickly without hiding failures or discarding successful alternatives.

### Migration Sequence

1. Freeze the Phase 4 public row/fusion behavior and add the Phase 5 settings, schema-migration, and concurrency characterization tests.
2. Replace the Phase 4 template adapters with concrete Google, Bing, DuckDuckGo, Yandex, Yahoo, and Ecosia plugins, each passing fixtures and the shared conformance suite.
3. Integrate Qwant, Startpage, Brave, Swisscows, and Mojeek with country/pagination fixtures, provider-family metadata, and independent disable switches.
4. Wire the validated engine list and global/per-engine worker settings through Python, CLI, cache keys, and the shared composition root.
5. Enable normalized result assembly and production fusion, including immutable market snapshots, canonical URL grouping, deterministic tie breaks, and report diagnostics.
6. Complete history/cache/schema migration, documentation, packaging, metrics, provider-safety review, and opt-in smoke coverage.
7. Run the full offline suite, lint/type/build checks, installed-wheel discovery test, and documentation/schema checks; run live provider smoke tests only after all offline gates pass.

### Verification Strategy

- Run all commands from `C:\Users\space\workspace\SerpScrap` in the Pipenv environment (`pipenv run ...` or `pipenv shell`).
- Contract-test all eleven plugins for URL encoding, country/locale mapping, capabilities, pagination, organic parsing, redirect safety, rank assignment, empty/access-control/malformed states, and JSON-compatible values.
- Test `SearchSettings` and both composition roots for defaults, explicit engine lists, legacy Google compatibility, duplicate/unknown/disabled engines, country validation, worker ceilings, per-engine limits, and ranking overrides.
- Use barriers/fakes to prove no more than `num_workers` capture calls are active, per-engine limits are respected, completion order does not change output, one failure preserves other engines, and all resources close on cancellation.
- Run fixture-backed parser tests for every engine and search page state. Live network/Chrome tests remain opt-in and never establish parser correctness.
- Test canonical URL grouping and fusion as pure functions, including market-share snapshots, fallback `Other` weights, provider-family caps, multiple queries, ties, deterministic representatives, and exact JSON round trips.
- Verify cache/history migrations, old schema reads, cache-hit metadata, atomic writes, and absence of credentials/cookies/query contents in diagnostics.
- Run Ruff, focused mypy for new modules, the complete offline pytest suite, wheel/sdist builds, installed-wheel registry discovery, and documentation link/schema validation.

### Phase 5 Acceptance Criteria

- All eleven engines in `docs/searchengines.md` have concrete registered plugins, versioned fixtures, conformance tests, readiness metadata, and independently controllable enable/disable state.
- Users can select engines in Python configuration or CLI and set the global parallel search-request limit; the same validated settings are honored by both interfaces and documented clearly.
- A configured run issues one bounded job per query/engine/page, preserves successful results when another engine fails, and records structured engine/country/plugin failure metadata.
- Every returned row uses the normalized JSON contract with `search_engine`, uppercase `country_code`, canonical URL, rank, and nullable common fields; multi-engine rows include explainable fusion metadata.
- Results are grouped per query and ranked deterministically with the documented frequency/position/market-weight formula, immutable weight snapshot, provider-family policy, and fallback handling.
- Phase 4 Google-only callers remain compatible, while alternative-first configuration is available without source changes or engine-specific orchestration branches.
- Offline tests, linting, focused typing, package discovery, cache/history migration, documentation, and opt-in smoke procedures all pass the Phase 5 gates.

## Refactoring Phase 4 - Pluggable Multi-Engine Search and Relevance Fusion

### Objective

Shift the primary retrieval strategy from a Google-only pipeline to a configurable portfolio of search engines. Add a standardized search-engine plugin directory, initially supporting the ten alternative engines selected in `docs/searchengines.md` plus Google. For every query, run the configured engines concurrently in bounded threads, preserve partial results and failures independently, add `search_engine` and ISO 3166-1 alpha-2 `country_code` provenance to every result, and produce one deterministic JSON-compatible result list ordered by a documented relevance score derived from cross-engine frequency, result position, and versioned European market-share weights.

Google remains supported but is no longer architecturally privileged or required in the default alternative-first configuration. Phase 3 request safety remains mandatory for every plugin: SerpScrap must detect and report blocking, consent, CAPTCHA, and rate limiting, never bypass access controls automatically.

### Architectural Principles

- Keep engine-specific URL construction, country/locale mapping, response classification, and parsing inside one plugin package; the application pipeline depends only on a small shared contract.
- Treat plugins as trusted, packaged Python components discovered through an explicit registry. Do not scan and execute arbitrary files from writable directories.
- Separate raw engine results from cross-engine normalization and ranking so each stage is independently testable and raw provenance is never lost.
- Apply bounded concurrency at two levels: a global request limit and a per-engine limit/policy. A slow, blocked, or broken engine must not prevent successful engines from completing.
- Keep one browser driver owned by one worker at a time. Never share Selenium drivers, parser instances, mutable request state, or database sessions between threads.
- Make engine selection, country, timeouts, weights, and ranking constants explicit, validated configuration. Identical captured inputs and configuration must produce byte-for-byte stable JSON ordering.
- Prefer captured fixtures and plugin contract tests over live SERP tests. Live requests remain opt-in, low-volume, and subject to each provider's current terms and access controls.

### Target Plugin Layout and Contract

- Create `serpscrap/plugins/searchengines/` with a shared contract and registry plus one package per engine: `google`, `bing`, `yandex`, `yahoo`, `duckduckgo`, `ecosia`, `qwant`, `startpage`, `brave`, `swisscows`, and `mojeek`.
- Define an immutable `SearchEnginePlugin` contract exposing stable metadata (`engine_id`, display name, supported countries/locales, supported result types and market-share record), request URL construction, response classification, organic result parsing, and optional engine-specific pacing/capability declarations.
- Keep transport behind an injected capture interface. A plugin describes and interprets a request but does not construct executors, write caches/history/JSON, or own global browser lifecycle.
- Use a central explicit registry mapping normalized engine IDs to plugin factories. Reject duplicate IDs, missing required metadata, unsupported countries/search types, invalid URL templates, and incompatible plugin contract versions during startup.
- Give every plugin a version and fixture provenance date so selector drift and market-data changes can be diagnosed without changing the public engine ID.
- Preserve the possibility of external entry-point plugins later, but do not make third-party discovery part of the first Phase 4 slice.

### Target Request, Result, and Failure Contract

- Extend `SearchRequest` with ordered `search_engines: tuple[str, ...]`, a required/defaulted ISO alpha-2 `country_code`, optional engine weight overrides, global and per-engine concurrency bounds, and ranking configuration.
- Interpret `country_code` as the requested result market, not the scraper host location. Each plugin maps it to its own region/locale parameters and reports an actionable unsupported-country error when no honest mapping exists.
- Add `search_engine` and `country_code` to every canonical successful result row. Add `relevance_score`, `engine_match_count`, `best_rank`, and `matched_engines` only after the schema-version and compatibility decision is recorded; all values remain native JSON types.
- Keep raw per-engine rows internally through ranking. Group only normalized, canonical HTTP(S) target URLs; strip fragments and known tracking parameters, normalize host/port/path conservatively, and never merge different URLs merely because titles or snippets are similar.
- Select a deterministic representative row for each canonical URL: highest individual weighted contribution, then best rank, configured engine order, normalized URL, and title. Preserve all contributing engines and country codes in structured provenance.
- Extend failures with plugin ID/version and country code while retaining query, page, URL, category, retryability, correlation ID, and attempt count. One engine failure does not erase other engines' rows.
- Increment the persisted schema version if the public result row changes. Document the exact migration from the Phase 2/3 flat schema before implementation.

### 1. Establish the Plugin Boundary

- Freeze current Google URL, classification, parser, and output behavior with characterization tests, then move it behind the new contract without rewriting its internals in the same slice.
- Extract generic result assembly, URL normalization, cache key construction, and failure conversion from Google-specific modules. Plugin code returns typed engine results and never SQLAlchemy entities.
- Add registry validation and a small plugin conformance suite reusable by all eleven engines.
- Include plugin Python packages and any non-code metadata in wheel/sdist checks; keep HTML fixtures under `tests/fixtures/searchengines/<engine>/` rather than in the installed package.
- Remove `if engine == "google"` factories and URL-regex parser dispatch only after all composition paths use the registry and compatibility tests pass.

### 2. Implement the Initial Eleven Engines in Risk-Based Slices

- First migrate Google and add Bing plus DuckDuckGo to prove the contract across distinct SERP structures and preserve Phase 3 behavior.
- Add Yandex and Yahoo next because StatCounter reports them individually in Europe; include localized, empty, consent/block, and redirect fixtures.
- Add Ecosia, Qwant, and Startpage as the first European alternative cohort, explicitly accounting for upstream-provider overlap without treating identical upstream indexes as independent proof of relevance.
- Add Brave, Swisscows, and Mojeek after their URL, pagination, country mapping, response-state, and organic-card fixtures have been captured and reviewed.
- Limit the first implementation to organic web results unless an engine declares and tests another common result type. Unsupported verticals must fail validation rather than silently falling back to organic search.
- For every engine, document the verified query template, pagination mechanism, country mapping, result-card boundaries, redirect-link decoding, empty state, and block/consent state in fixture metadata. Treat selectors in `docs/searchengines.md` as reconnaissance, not as the parser contract.

### 3. Fan Out Requests with Bounded Thread Concurrency

- Build one immutable job per `(query, engine, country, page)` from the ordered request and submit it to a bounded `ThreadPoolExecutor` through the existing application service.
- Enforce both a global worker ceiling and plugin-declared per-engine ceilings. Google keeps its conservative policy; alternative engines receive independent pacing, retry, and circuit-breaker state.
- Apply cache lookup and in-run request deduplication before acquiring an engine rate slot or starting a browser. Cache keys include plugin ID/version, query, page, country, locale, search type, result count, and request-relevant identity.
- Collect futures by job identity rather than completion order. Convert unexpected plugin exceptions into structured failures and assemble successful rows in deterministic request/engine/page/rank order before ranking.
- Cancel only pending jobs covered by the same engine circuit breaker. Global cancellation remains reserved for caller cancellation or resource failure.
- Guarantee driver, response, executor, cache temporary-file, and repository cleanup for success, partial failure, timeout, cancellation, and circuit-breaker paths.

### 4. Normalize, Aggregate, and Rank Results

- Introduce a pure `ResultFusion` service that accepts raw canonical engine rows plus an immutable weight snapshot and returns ranked rows without network, browser, filesystem, database, or clock access.
- Use weighted reciprocal-rank fusion as the initial transparent algorithm. For a canonical URL `u`, compute `score(u) = sum(weight(engine) / (rrf_k + rank))` over at most one best occurrence per engine. Repeated presence increases the score, high positions contribute more, and the configured market weight scales each engine's contribution.
- Default `rrf_k` to a documented constant and make it validated/configurable. Round only the serialized display score; sort using full precision.
- Normalize configured market shares to weights across the active engines. Use the dated values in `docs/searchengines.md`; for engines hidden in StatCounter's `Other` bucket, use a clearly labelled fallback policy or an explicit operator override, never a fabricated measured share.
- Prevent upstream syndication from inflating frequency by optionally defining provider families (for example Bing-backed or mixed-provider services). Deliver the first release with both `engine_match_count` and a diagnostic `independent_provider_count`; decide through tests whether provider-family capping participates in the production score.
- Define deterministic tie breaks: descending relevance score, descending independent provider count, descending engine match count, ascending best rank, configured engine order, then canonical URL.
- Keep ranking explainable in report metadata: algorithm/version, `rrf_k`, weight snapshot/as-of date, active engines, fallback weights, canonicalization version, and per-result contributions when diagnostics are enabled.

### 5. Configuration, CLI, and Compatibility

- Accept repeated/list engine selection in Python and CLI, validate it against the registry, preserve user order for tie-breaking, and reject an empty selection.
- Ship all eleven plugins as supported, but define and document an alternative-first default separately from the supported set. Google must be explicitly disableable and its failure must never abort alternatives.
- Add `--country ISO2`, repeated `--engine ENGINE`, global `--workers`, and clearly named per-engine concurrency/weight configuration without overloading the existing URL-enrichment thread setting.
- Keep `search_engine="google"` and legacy `Config` calls working during a documented compatibility period by translating them into the new engine tuple.
- Validate that output files and CLI stdout contain the same ranked JSON data and logs remain on stderr. Expose unranked/raw engine data only through an explicit diagnostic/report API, not a second accidental public schema.
- Update README, configuration, result schema, examples, CLI help, package data, `docs/searchengines.md`, and the refactoring changelog together with each migration slice.

### 6. Research and Maintenance Workflow

- Treat `docs/searchengines.md` as a dated registry-design input containing selection rationale, measured/proxy market data, query entry points, SERP delivery notes, country/pagination research, and primary sources.
- Refresh market-share data on a scheduled release cadence and retain the previous snapshot for reproducibility. A market update changes ranking metadata and tests deliberately; it must not silently alter historical cached runs.
- Before enabling a plugin, review current provider terms, robots guidance where applicable, consent behavior, and availability of a supported API. Record the review date; do not encode bypasses for CAPTCHA, proof-of-work, login, or geographic restrictions.
- Capture sanitized HTML fixtures manually or through an opt-in maintenance command with a distinctive low-volume query. Never run live capture in the default test suite.
- Add a selector/fixture maintenance checklist and plugin ownership/status table so one broken engine can be disabled without removing or destabilizing the registry.

### Migration Sequence

1. Freeze Phase 3 behavior and add schema, concurrency, canonicalization, and ranking characterization tests.
2. Add the plugin contract, registry, plugin metadata, and conformance suite; migrate Google unchanged behind it.
3. Add Bing and DuckDuckGo, implement multi-engine job fan-out, partial failures, deterministic collection, and engine/country provenance.
4. Add pure URL canonicalization and weighted reciprocal-rank fusion with a versioned July 2026 market snapshot and explicit `Other` fallback policy.
5. Add Yandex, Yahoo, and Ecosia with fixtures and per-engine request policies.
6. Add Qwant, Startpage, Brave, Swisscows, and Mojeek only after fixture-backed URL, country, pagination, state-classification, and parser contracts pass.
7. Complete public schema/CLI compatibility, documentation, packaging, cache migration, changelog, and full offline verification; run the opt-in live matrix last and at low volume.

### Verification Strategy

- Run all development and verification commands from `C:\Users\space\workspace\SerpScrap` through `pipenv run ...` or an active `pipenv shell`.
- Contract-test every plugin for metadata, URL encoding, country mapping, pagination, result parsing, URL decoding, rank assignment, JSON types, empty results, block/consent/rate states, and malformed responses.
- Maintain at least normal, localized, empty, blocked/consent, and selector-fallback fixtures per engine. Fixtures must contain no cookies, account data, proxy credentials, or personally identifying queries.
- Test executor bounds, per-engine limits, cache-before-capture, no shared drivers, completion-order independence, partial failure preservation, engine-scoped circuit breaking, cancellation, and cleanup with fake plugins and barriers rather than wall-clock sleeps.
- Property-test or table-test URL canonicalization and result fusion for duplicates, tracking parameters, redirects, ranks, missing weights, provider-family overlap, tie breaks, precision, and permutation invariance.
- Contract-test every public row for `search_engine`, uppercase ISO alpha-2 `country_code`, rank, relevance fields, canonical URL, deterministic provenance, and exact JSON round trips.
- Keep all default tests offline. Use separate opt-in smoke markers per engine, one worker per provider, a harmless query, strict request budgets, and successful classification of honest blocks as an acceptable outcome.
- Run the full Phase 1-3 regression suite, Ruff, focused mypy, wheel/sdist builds, installed-wheel plugin discovery, and documentation link/schema checks before Phase 4 acceptance.

### Phase 4 Acceptance Criteria

- The installed package exposes a validated registry with standardized plugins for Google and the ten alternatives listed in `docs/searchengines.md`; adding an in-tree engine requires no edits to application orchestration or ranking code.
- A configured multi-engine search fans out in bounded threads, applies independent engine policies, uses no shared driver/session state, returns partial successes, and records structured failures without one engine aborting the run.
- Every successful JSON row contains its engine and uppercase ISO alpha-2 country provenance, and the public schema/version/migration behavior is documented and identical across Python, CLI stdout, and saved JSON.
- Results are conservatively canonicalized, grouped, and deterministically ordered by a versioned, explainable combination of cross-engine frequency, position, and market weight; ties and unreported market shares follow documented policies.
- Offline fixtures and conformance tests cover normal, localized, empty, blocked/consent, and layout-fallback behavior for all eleven engines without network or Chrome.
- Google can be disabled, is not a special orchestration dependency, and retains all Phase 3 request-safety behavior when enabled.
- `docs/searchengines.md`, configuration/results documentation, examples, package artifacts, tests, and `docs/changelog-refactoring2026.md` agree with the delivered plugin set and ranking snapshot.

## Refactoring Phase 3 - Resilient Google Requests and Complete SERP Formats

### Objective

Harden the Google request and scraping path so normal use does not trigger avoidable blocking through stale browser identity, bursty traffic, inconsistent request state, or unnecessary repeat navigation. Use a current desktop Google Chrome user agent consistently for Chrome-driven SERP retrieval and HTTP URL enrichment, while keeping explicit overrides possible. Extend capture and parsing to cover every search-result format documented in `docs/results.rst`: organic `results`, `image`, `news`, `shopping`, and `videos`. CAPTCHA and other Google access controls must be detected and reported, never bypassed automatically.

### Request and Scraping Principles

- Present one internally consistent Chrome identity: user agent, browser version, language, viewport, and request headers must not contradict each other.
- Prefer a user agent derived from the installed current Chrome version; retain a centrally maintained, tested current stable desktop Chrome fallback instead of the stale random lists in `scrapcore/user_agent.py`.
- Reduce avoidable request volume through caching, request deduplication, controlled pagination, and reuse of one browser session per scrape job.
- Apply bounded concurrency and configurable pacing with jitter between Google navigations. Defaults must favor reliability over maximum throughput and remain deterministic in tests through injected clocks and randomness.
- Retry only failures classified as transient, with bounded exponential backoff and server-provided delay hints where available. Never retry CAPTCHA, consent, or explicit blocking in a tight loop, rotate identities automatically, or claim that blocking can be prevented completely.
- Keep request policy, Google navigation, HTML capture, response classification, parsing, and URL enrichment separate so each can be verified offline.
- Treat documented result types as a public contract with stable names and a shared base schema, not as incidental selector matches.

### Target Request and Result Contract

- Introduce a validated request-policy value containing user agent, locale, timeouts, pacing range, retry limit, backoff bounds, concurrency limit, and proxy policy.
- Resolve the effective user agent once per request. By default it must be a current desktop Chrome user agent matching the installed Chrome major version; an explicit `user_agent` remains supported and is recorded in diagnostic metadata without leaking it into result rows.
- Apply the effective user agent and compatible `Accept`, `Accept-Language`, and navigation headers to both Selenium Chrome options and HTTP URL-enrichment requests.
- Keep Google query URLs deterministic and correctly encoded. Validate page offsets and the vertical-specific parameters used for normal, image, news, shopping, and video retrieval.
- Preserve the canonical Phase 2 `list[dict]` output. Every row keeps the documented common fields and uses exactly one stable `serp_type`: `results`, `image`, `news`, `shopping`, or `videos`; type-specific values are nullable and JSON-compatible.
- Define typed outcomes for success, empty results, consent required, CAPTCHA/block, rate limiting, timeout, network failure, malformed response, and parser failure. Include retryability and attempted-request count in structured failures.

### 1. Centralize Browser and HTTP Request Identity

- Replace implicit or random user-agent selection with one `ChromeIdentityProvider` used by the composition root, Chrome driver factory, and URL-enrichment client.
- Detect the installed Chrome product version without launching an extra browser where the platform exposes it, build the corresponding desktop Chrome user agent, and validate that it contains a supported non-headless Chrome version token.
- Provide a centrally defined stable Chrome fallback whose freshness policy and update procedure are documented and covered by a test that fails when the fallback exceeds the agreed maintenance window.
- Continue to accept an explicit user-agent override for controlled environments, but validate blank, malformed, mobile, and browser/version-inconsistent values with actionable errors.
- Replace direct `urllib.request.urlopen()` calls with an injectable HTTP client that builds an explicit `Request`, applies the effective headers and timeout, follows a documented redirect policy, bounds response size, and always closes the response.
- Remove `scrapcore/user_agent.py` after all consumers use the centralized identity provider and compatibility tests confirm that no public behavior depends on its random lists.

### 2. Add Responsible Request Pacing and Session Reuse

- Reuse one Chrome session for all pages of a scrape job and keep cookies, consent state, locale, and identity stable throughout that job.
- Add a configurable delay range with jitter before subsequent Google navigations, plus a longer bounded backoff after transient rate or network failures. The first request must not incur an unnecessary delay.
- Set conservative defaults for Google worker concurrency and prevent multiple workers from issuing simultaneous requests for the same query, page, search type, locale, and result count.
- Consult the captured-page cache before acquiring a rate-limit slot or starting Chrome, so cache hits produce no Google traffic.
- Stop the affected job immediately when blocking, CAPTCHA, or mandatory consent is detected. Preserve prior pages, emit a structured failure, and do not rotate proxies, user agents, or sessions automatically.
- Expose pacing and retry decisions through structured debug logs with correlation IDs, while excluding query contents, proxy credentials, cookies, and full response bodies from routine logs.

### 3. Strengthen Google Response Classification

- Expand classification beyond URL fragments and English body text to recognize Google CAPTCHA/interstitial markup, HTTP-style rate signals exposed by the driver, consent pages, redirect loops, localized empty-result pages, and incomplete shell pages.
- Run classification before parsing and after each navigation/state transition so an anti-bot or consent page cannot be misreported as an empty successful SERP.
- Define one precedence order for ambiguous states: block/CAPTCHA, consent, rate limit, navigation failure, empty results, recognizable SERP, then malformed response.
- Capture HTML and screenshots only when diagnostics are explicitly enabled; sanitize filenames and avoid persisting cookies, headers, or proxy credentials.
- Add a circuit breaker scoped to a run: after a configurable number of block or rate-limit outcomes, cancel pending Google jobs and return partial results instead of increasing traffic.

### 4. Cover All Documented Google Result Formats

- Create fixture-backed parser adapters or components for organic `results`, `image`, `news`, `shopping`, and `videos`, sharing URL normalization, deduplication, rank assignment, and common-field assembly.
- Add ordered selector fallbacks based on semantic structure and stable attributes where possible. Keep format-specific selectors isolated so one Google layout change does not disable unrelated formats.
- Parse mixed normal SERPs into their actual documented `serp_type` values rather than flattening every card into `results`; prevent a card from being emitted twice by general and specialized selectors.
- Define and document type-specific extraction: source/date for news, price/merchant/rating for shopping, duration/source/date for videos, and image/source/thumbnail metadata for images, while retaining the Phase 2 common row fields.
- Add explicit Google search vertical routing where needed and reconcile it with the public `search_type` option. Validation and documentation must use the same supported values.
- Treat an unknown Google module as an observable unsupported format in diagnostics, not as a parser crash or silently malformed organic result.

### 5. Refactor URL Enrichment Safely

- Move URL fetching, decoding, metadata extraction, and cache persistence out of `UrlScrape` into small testable components while retaining the public `scrap_url()` compatibility adapter during the migration.
- Send the same effective current Chrome user agent and compatible request headers used by the scrape request; allow per-origin connection reuse without sharing Google cookies with result sites.
- Add explicit connect/read timeout behavior, redirect limits, maximum response bytes, accepted content types, and decompression limits so a result URL cannot hold a worker indefinitely or exhaust memory.
- Classify DNS, TLS, timeout, HTTP, unsupported-content, decoding, and parse failures without collapsing all exceptions into `status: error`.
- Make cache keys include request-relevant representation inputs and write enrichment cache files atomically, so stale data from a previous identity or partial writes cannot masquerade as a current response.

### 6. Migrate in Vertical Slices

1. Freeze current Google URL construction, Chrome options, response classification, organic/image parsing, failures, caching, and URL enrichment with characterization tests.
2. Add the central Chrome identity and request-policy values, route Chrome and the injectable HTTP client through them, and remove the random legacy user-agent source.
3. Add cache-aware pacing, session reuse, bounded retry/backoff, and the run-scoped circuit breaker using fake clocks, deterministic jitter, and fake drivers.
4. Add fixtures and parser contracts for `news`, `shopping`, and `videos`, then tighten mixed-SERP precedence and deduplication across all documented types.
5. Refactor URL enrichment behind the HTTP client, preserve its compatibility entry points, and add response-size, content-type, redirect, encoding, and atomic-cache protections.
6. Update configuration, results, examples, installation notes, and changelog; run the offline suite first and the opt-in live Chrome smoke matrix only after it passes.

### Verification Strategy

- Run development and verification commands from `C:\Users\space\workspace\SerpScrap` inside the Pipenv environment, using `pipenv shell` or the non-interactive equivalent `pipenv run ...`.
- Unit-test installed-Chrome version detection, current fallback selection, explicit overrides, header consistency, and rejection of stale or contradictory identities without requiring Chrome or network access.
- Test pacing, jitter bounds, rate-limit slot ordering, cache-before-navigation behavior, retries, circuit breaking, cancellation, and session cleanup with injected fakes and deterministic time.
- Maintain captured HTML fixtures for every documented result format and for mixed, empty, localized, consent, CAPTCHA, rate-limited, malformed, and layout-fallback pages.
- Contract-test that organic `results`, `image`, `news`, `shopping`, and `videos` rows have stable `serp_type` values, common fields, deterministic ranks, normalized URLs, no duplicates, and JSON-compatible type-specific fields.
- Test URL enrichment with a local HTTP server or fake transport for headers, redirects, compression, encodings, oversized responses, unsupported content, timeouts, TLS/network failures, cache hits, and atomic writes.
- Keep live Google tests opt-in, low-volume, single-worker, and tolerant of an honestly classified block or consent outcome. They must never be the only evidence for parser correctness.
- Verify browser, response, executor, and cache-file cleanup on every success, retry, failure, cancellation, and circuit-breaker path.

### Phase 3 Acceptance Criteria

- Every Selenium Google navigation and HTTP URL-enrichment request uses one validated, current desktop Chrome user agent by default, matching the installed Chrome major version when detectable and using a documented maintained fallback otherwise.
- Default request behavior reuses sessions, checks the cache before navigation, limits concurrency, spaces subsequent requests, and uses bounded retries only for transient failures.
- Blocking, CAPTCHA, consent, rate limiting, empty results, malformed responses, and network failures are distinguished and exposed as structured outcomes; detected access controls are never bypassed automatically.
- Fixture tests prove parsing and canonical serialization for all formats promised by `docs/results.rst`: `results`, `image`, `news`, `shopping`, and `videos`, including mixed SERPs and selector fallbacks.
- URL enrichment has explicit headers, timeouts, redirect, response-size, content-type, decoding, error, and atomic-cache behavior and remains callable through the documented public API.
- Offline Phase 1 and Phase 2 suites remain deterministic and pass without Chrome or network access; opt-in browser smoke tests run successfully from the repository's Pipenv environment.

## Refactoring Phase 2 - Slim Architecture and JSON Results

### Objective

Simplify the architecture introduced during Phase 1 without weakening browser cleanup, partial-result handling, caching, or deterministic parsing. The primary user-facing result is one stable `list[dict]` in Python and the equivalent JSON array on stdout or in a local `.json` file. CSV is removed as a result format. A normal search should require as little setup as possible, while advanced users can still inject configuration and infrastructure components explicitly.

### Architectural Principles

- Keep one canonical result schema and one serialization path for the Python API, CLI stdout, and local files.
- Return plain Python data from the public boundary; do not expose SQLAlchemy entities, sessions, browser objects, or parser internals.
- Keep orchestration independent from Selenium, SQLite, the filesystem, and Click through small explicit interfaces.
- Prefer composition and stateless services over parallel legacy abstractions, mutable controller state, and implicit side effects.
- Make optional infrastructure fail predictably: a scrape result must not depend on stdout printing or an unrelated export writer, and all opened resources must have one clear owner.
- Preserve the reliable Phase 1 capture and parser behavior while changing the surrounding architecture in small, testable steps.

### Target Request and Result Contract

- Define a validated `SearchRequest` value containing queries, pages, workers, engine, search type, proxy/browser options, cache policy, and optional output path.
- Define canonical typed internal result values for a result row, related keyword, page metadata, and structured failure. Convert them to JSON-compatible dictionaries only at the public boundary.
- Specify and document the canonical flat result-row schema, including field names, types, nullable values, rank semantics, page metadata, and optional URL-scrape fields.
- Preserve native JSON types (`int`, `float`, `bool`, `null`, lists, and dictionaries); remove the current blanket conversion of database values to strings.
- Make result ordering deterministic by request order, page number, result type, and rank, including concurrent runs and cache hits.
- Keep the primary Python response as `list[dict]`. Expose run metadata, related keywords, and failures through an explicit report object or dedicated accessor without changing the shape of successful result rows.
- Add a schema version to persisted run metadata so future incompatible result changes can be migrated deliberately.

### 1. Introduce a Small Public Facade

- Add a direct convenience entry point such as `SerpScrap.search(keywords, **options) -> list[dict]`; users should not need a mandatory `init()`/`run()` sequence for a normal search.
- Allow configuration through validated keyword arguments or a typed settings object, while retaining `Config` input during a documented compatibility period.
- Make repeated calls on the same facade independent; remove mutable request and result state where it is not required for compatibility.
- Keep `init()`, `run()`, `get_related()`, and other existing public calls as thin compatibility adapters initially, emit clear deprecation guidance where appropriate, and test their behavior until removal in a future major release.
- Export only the intentional public API from `serpscrap`; keep application and infrastructure classes internal.

### 2. Split the Application Pipeline from Infrastructure

- Replace the all-in-one `Core` workflow with an application service that coordinates explicit stages: build jobs, obtain cached pages, capture missing pages, parse, assemble results, and optionally persist artifacts.
- Define small protocols for page capture, cache access, result-history storage, and JSON output. Supply Selenium, filesystem cache, SQLite, and local JSON implementations at the composition root.
- Move SQLAlchemy model construction and session handling into a repository adapter. The application service must operate on domain/result values and remain testable without a database.
- Make cache and historical database storage independently configurable. Neither should be required merely to return results in memory.
- Retain bounded browser concurrency, but gather and order worker outcomes before serialization. Keep browser, executor, session, and file lifecycles scoped with context managers.
- Remove or consolidate superseded paths such as the legacy `scrapcore.scraping` workflow, duplicate result writers, and unused compatibility aliases only after import and behavior tests prove they are no longer reachable.

### 3. Establish JSON as the Only Result Output Format

- Replace `CsvWriter`, `CsvStreamWriter`, CSV branches in `ResultWriter`, and `SerpScrap.as_csv()` with one JSON serializer operating on the canonical dictionaries.
- Add an explicit local-save API such as `save_json(path, results=None)` and a CLI `--output PATH` option. Require or append `.json` consistently and return the written path from the Python API.
- Write UTF-8 JSON with `ensure_ascii=False`; use a JSON array whose deserialized value equals the Python API's `list[dict]` result.
- Write local files atomically through a temporary file in the destination directory followed by replacement. Define parent-directory creation, overwrite behavior, and serialization errors explicitly.
- Keep CLI result JSON on stdout and logs on stderr. When `--output` is used, define whether stdout contains the same result array or a small machine-readable file acknowledgement and cover that contract with tests.
- Remove CSV configuration, examples, exports, imports, and documentation. Document the migration from `as_csv(path)` to JSON and treat accidental `.csv` output requests as actionable validation errors.

### 4. Simplify Configuration and Composition

- Separate user-facing search settings from infrastructure settings and derived defaults; stop passing one mutable dictionary through every layer.
- Validate paths, supported engines/search types, page and worker bounds, proxy settings, and output policy once when constructing `SearchRequest`.
- Centralize dependency construction in one composition root used by both the Python facade and Click CLI, so both interfaces execute the same application service.
- Use `pathlib.Path` for local cache, database, diagnostics, and JSON output paths, with platform-safe defaults and no import-time filesystem writes.
- Make optional persistence explicit (`cache`, `history`, and `output`) and document which local artifacts are created for each choice.
- Preserve dependency injection for capture, clock, cache, repository, and writer so tests do not require Chrome, network access, or a real user directory.

### 5. Make Failures and Partial Results Predictable

- Keep successful rows when another page or query fails. Do not encode failures as fake successful SERP rows or only as database status strings.
- Use a stable failure schema containing query, engine, page, URL, category, message, retryability, and correlation ID.
- Define which errors fail the whole request (invalid configuration or inability to start any requested job) and which produce a partial report (page timeout, block, parse failure, or optional persistence failure).
- Ensure optional JSON or history persistence reports its own error without corrupting an already assembled in-memory result.
- Maintain the Phase 1 rule that CAPTCHA and anti-bot responses are classified and reported but never bypassed automatically.

### 6. Migrate in Vertical Slices

1. Freeze the current public behavior with characterization tests for Python results, related keywords, CLI JSON, cache hits, partial failures, and local database writes.
2. Add canonical result models and a single serializer, then route existing Python and CLI output through them without changing capture or parsing.
3. Add the application service and infrastructure protocols; first move orchestration, then cache access, and finally SQLAlchemy persistence behind adapters.
4. Introduce the convenience API and local JSON writer, keeping compatibility wrappers around the old lifecycle during the transition.
5. Switch examples and documentation to the new API and JSON files, then remove CSV and confirmed-dead legacy modules.
6. Run the full offline suite, package checks, focused typing/linting, and opt-in browser smoke test after each slice; record completed work in `docs/changelog-refactoring2026.md`.

### Verification Strategy

- Contract-test that the Python response is a `list[dict]`, is JSON serializable without custom encoders, and round-trips exactly through a saved JSON file.
- Add golden-schema tests for normal, image, related-keyword, URL-enriched, empty, failed, partial, multi-query, multi-page, and cached runs.
- Test deterministic ordering under deliberately out-of-order worker completion.
- Test atomic JSON replacement, Unicode, nested values, nulls, invalid destinations, overwrite policy, and cleanup of temporary files after failures.
- Test that the application service runs with in-memory fakes and imports without Selenium or SQLAlchemy objects crossing its boundary.
- Keep lifecycle tests proving browser shutdown, executor completion, transaction rollback, session closure, and file closure on every error path.
- Add compatibility tests for retained Phase 1 API calls and explicit tests that removed CSV entry points/configuration produce the documented migration error.
- Keep CLI snapshots for stdout JSON, stderr logs, exit codes, `--output`, and partial-result reporting.

### Phase 2 Acceptance Criteria

- A user can execute a search with one direct Python call and receive a deterministic `list[dict]` containing only JSON-compatible values.
- The CLI emits valid JSON independently of logging, and the same result data can be saved locally as a UTF-8 `.json` file.
- Loading the local JSON file produces data equal to the in-memory result, without type loss caused by ORM serialization.
- CSV writers, CSV output configuration, `as_csv()`, CSV examples, and CSV documentation are removed with migration guidance.
- The application orchestration is testable without Chrome, network access, SQLite, or filesystem output; concrete infrastructure is selected only in the composition root.
- Cache, SQLite history, diagnostics, and JSON output are independently optional and have explicit resource ownership.
- Partial successes and structured failures remain observable and deterministically associated with their query and page.
- Phase 1 offline tests and browser-cleanup guarantees remain intact, and all new Phase 2 contract and architecture tests pass.

## Refactoring Phase 1 - Selenium 4 and Reliable SERP Retrieval

### Objective

Modernize SerpScrap so that search engine result pages (SERPs) are retrieved reliably with Selenium 4 and headless Google Chrome, parsed into the existing result model, and covered by deterministic automated tests.

### 1. Establish the Baseline

- Document the supported Python versions, search engines, search types, configuration keys, CLI behavior, and public Python API.
- Add fixture-based regression tests for representative Google SERP HTML before changing parser behavior.
- Separate offline unit tests from network-dependent browser integration tests and mark the latter explicitly.
- Record the current output schema so the refactoring does not introduce accidental API changes.

### 2. Modernize Packaging and Dependencies

- Replace `setup.py` and `Pipfile` as the authoritative package metadata with a PEP 517/518-compatible `pyproject.toml`.
- Define bounded runtime and development dependency ranges and generate a reproducible lock file.
- Upgrade Selenium, SQLAlchemy, lxml, Beautiful Soup, bleach, cssselect, and the test toolchain to mutually compatible versions.
- Remove `chromedriver-autoinstaller`; use Selenium Manager by default and retain an optional explicit ChromeDriver path for controlled environments.
- Remove deprecated Selenium and SQLAlchemy APIs, including legacy `find_element_by_*` calls and `Query.get()`.

### 3. Isolate Browser Management

- Introduce a Chrome WebDriver factory responsible for `ChromeOptions`, Selenium `Service`, proxy settings, user agent, window size, page-load strategy, and timeouts.
- Run Chrome with the current headless implementation (`--headless=new` where supported) and container-safe flags configured explicitly.
- Model browser settings as validated configuration instead of reading loosely typed dictionary keys throughout the scraper.
- Guarantee `driver.quit()` with `try/finally` or a context manager, including startup, timeout, parsing, and cancellation failures.
- Replace fixed sleeps with explicit waits for document readiness and SERP-specific conditions.

### 4. Refactor the Scraping Pipeline

- Define one immutable scrape-job type containing query, search engine, search type, requested pages, proxy, and correlation ID.
- Replace the current factory/worker contract with a bounded worker pool that accepts complete jobs and returns typed scrape results or structured failures.
- Separate the pipeline into browser acquisition, navigation, HTML capture, parsing, persistence, and result serialization stages.
- Ensure database sessions, cache writes, progress reporting, and browser instances have explicit ownership and thread-safe lifecycles.
- Preserve partial results when a later page fails and report the affected query, page, URL, and failure category.

### 5. Implement Reliable Headless SERP Retrieval

- Build search URLs directly from validated query parameters instead of typing into the search form when the engine supports stable query URLs.
- Wait for a configurable set of SERP result-container selectors and detect consent pages, CAPTCHA pages, rate limiting, redirects, and empty-result pages separately.
- Capture `driver.page_source` after the readiness condition is satisfied; store screenshots and HTML only as opt-in diagnostics.
- Update pagination to use Selenium 4 locators and URL/state-change waits rather than stale CSS selectors plus fixed delays.
- Keep engine-specific navigation and selectors behind adapters so Google-specific changes do not affect the worker infrastructure.
- Treat anti-bot detection as a typed, non-retriable or policy-controlled result; do not attempt to bypass CAPTCHAs automatically.

### 6. Stabilize Parsing and Output

- Parse captured HTML independently of Selenium so parsers can be tested entirely from fixtures.
- Update Google selectors using ordered fallbacks and validate links, titles, snippets, ranks, result types, and pagination metadata.
- Normalize redirected result URLs and reject duplicate or malformed entries deterministically.
- Keep database entities and CSV/API serialization backward compatible unless a versioned schema migration is documented.

### 7. Verification and Delivery

- Add unit tests for configuration validation, URL construction, driver options, wait conditions, error mapping, parser fixtures, and worker scheduling.
- Add a mocked WebDriver lifecycle test proving that `quit()` runs on success and on every failure path.
- Add an opt-in end-to-end smoke test that launches headless Chrome and validates at least one parsed organic result without making it part of deterministic unit-test runs.
- Replace the legacy Chrome installation script with a pinned Chrome-for-Testing or distribution-package installation in Docker, and add a container health smoke test.
- Update CI to run linting, type checking, unit tests, packaging checks, and the Docker smoke test on supported Python versions.
- Update README, CLI help, configuration documentation, examples, and changelog with installation requirements and migration notes.

### Acceptance Criteria

- A clean installation launches headless Chrome without manually downloading ChromeDriver.
- A scrape job returns structured SERP results through the existing public API and CLI.
- Browser processes are terminated after successful, failed, and cancelled jobs.
- Offline unit tests require neither Chrome nor network access and pass deterministically.
- The opt-in browser smoke test passes locally and in the project container.
- Deprecated Selenium and SQLAlchemy APIs, `chromedriver-autoinstaller`, and the legacy Chrome installation flow are removed.
# Refactoring Phase 9.2 - Developer-Friendly Search-Engine Plugin Structure

## Objective

Make the search-engine plugin layer easy to extend for developers while keeping
runtime behavior explicit, deterministic, and safe. Adding a new engine should
require one isolated plugin implementation, a registry entry, documented
capabilities, sanitized fixtures, and contract tests; it must not require
changes to orchestration, browser flow, result normalization, or fusion.

## Architectural Principles

- Keep one narrow, transport-independent plugin contract for URL construction,
  parsing, classification, metadata, and optional browser interaction.
- Separate provider-specific behavior from shared execution policy. Browser
  navigation, retries, consent safety, diagnostics, pagination orchestration,
  and result normalization remain shared services.
- Prefer explicit immutable specifications and typed values over ad-hoc class
  attributes and stringly-typed dictionaries.
- Treat capabilities as declarations (`search_types`, pagination, country or
  language support, browser/API transport, readiness) and validate them before
  a job starts.
- Keep unavailable or experimental engines importable and diagnosable, but
  prevent accidental selection unless their readiness state allows it.
- Make plugin failures typed and observable. A selector drift, unsupported
  search type, malformed page, block, consent page, and rate limit must remain
  distinguishable.

## Target Plugin Contract

1. Introduce small value objects/protocols for `EngineId`, plugin metadata,
   search capabilities, pagination strategy, browser interaction, and parser
   output. Preserve the current public plugin methods through a compatibility
   adapter during migration.
2. Define a single `SearchEnginePlugin` contract with explicit methods for
   `build_url`, `parse`, `classify`, and capability validation. Provider code
   may customize selectors and markers, but may not own retries, sleeps,
   driver lifecycle, persistence, or cross-engine ranking.
3. Replace the generic template plugin's growing conditional branches with
   composable provider specifications and small provider adapters. Shared
   helpers cover URL encoding, common organic-card extraction, canonical URL
   normalization, rank assignment, and safe text cleanup.
4. Give each plugin a stable ID, semantic display name, plugin version,
   contract version, provider family, readiness state, fixture version, and
   verification metadata. Metadata must be JSON serializable and suitable for
   diagnostics and CLI/API discovery.
5. Extend the registry with explicit registration/validation errors, stable
   ordering, capability queries, and optional discovery hooks. Duplicate IDs,
   invalid IDs, incomplete contracts, unsupported capabilities, and invalid
   readiness transitions fail early with actionable messages.

## Implementation Slices

1. Freeze the current behavior with characterization tests for every registered
   engine, URL/pagination output, parser output, outcome classification, and
   registry metadata.
2. Add the typed capability and metadata models plus contract validation;
   adapt the existing Google and alternative plugins without changing results.
3. Extract shared URL, pagination, text, card, and result-normalization helpers
   and migrate providers incrementally, keeping provider-specific selectors in
   provider modules/data rather than shared flow code.
4. Refactor `default_registry()` into declarative registration and add an
   ergonomic extension path for an in-tree plugin. Define the policy for
   optional external entry-point discovery without making it mandatory for the
   first implementation.
5. Make browser flow and application validation consume capabilities instead
   of engine-name conditionals; preserve typed terminal outcomes and partial
   result behavior.
6. Add a new minimal fixture-backed example engine in tests (not necessarily a
   production provider) to prove that extension work is isolated and documented.
7. Update developer documentation, examples, API/CLI diagnostics, and the
   changelog; remove obsolete compatibility branches only after the migration
   tests pass.

## Verification Strategy

- Contract-test every plugin for stable identity, metadata, supported search
  types, URL encoding, deterministic pagination, parse output, and JSON-safe
  serialization.
- Test registry registration, duplicate/invalid IDs, disabled and experimental
  readiness, selection validation, capability queries, and deterministic order.
- Use sanitized offline fixtures for normal, empty, malformed, consent,
  blocked, rate-limited, selector-drift, and provider-specific result pages.
- Test that adding a fixture-backed plugin does not require changes to shared
  browser flow, multi-engine execution, fusion, or result normalization.
- Keep browser tests opt-in and verify that shared flow still classifies typed
  outcomes without bypassing provider controls.
- Run `pipenv run pytest` and focused typing/linting checks from the repository
  root; no network access is required for the contract suite.

## Phase 9.2 Acceptance Criteria

- A developer can add a search-engine plugin by implementing the documented
  contract, registering it, adding fixtures, and adding contract tests.
- No engine-specific branch is required in shared orchestration, browser flow,
  multi-search, fusion, or result normalization for a normal web plugin.
- Unsupported search types, invalid pagination/country combinations, disabled
  plugins, and incomplete contracts fail before navigation with clear errors.
- Registry and plugin metadata expose capabilities, readiness, versions, and
  verification status deterministically through existing diagnostics surfaces.
- Existing engines retain their current parsed results and terminal outcome
  semantics, and the complete offline test suite remains green.

## Phase 9.2 European Candidate Rollout Plan

### Objective

Evaluate and add further European search providers without weakening the
plugin contract, provider-control safety, or result provenance. The candidate
research and reconnaissance matrix is maintained in
`docs/searchengines.md`; it is the source of truth for the information required
before an engine is enabled.

### Prioritization

1. **Wave A — activated public no-auth browser candidates:** GOOD, xPrivo,
   Marginalia, and eTools.ch are included in the default configuration and
   remain covered by fixture/parser contracts. MetaGer remains registered but
   disabled until a public no-auth route is available.
2. **Wave B — experimental public-instance candidate:** SearXNG, only through an explicitly
   configured and reviewed public or self-hosted instance.
3. API-only, login-protected, subscription-only, pre-launch, and research-only
   candidates are excluded from this rollout. This explicitly excludes the
   Marginalia API, OpenWebSearch.eu/OWI, EU Search, and Kagi.

### Implementation steps

1. Freeze the candidate metadata and verify each provider’s operator, index
   family, current host, terms/usage constraints, and transport choice.
2. Confirm that every selected endpoint is usable without API keys, login, or
   authentication; fail the discovery slice if the provider introduces one.
3. Implement MetaGer and GOOD as isolated browser adapters using sanitized
   homepage/SERP fixtures. Verify search forms, organic cards, pagination,
   consent/login states, empty pages, and upstream attribution.
4. Implement xPrivo only after a dated artifact confirms its current route,
   input, web-result cards, AI/module exclusions, pagination, and provenance.
5. Implement Marginalia and eTools.ch as public browser/form adapters; do not
   use their credentialed or API-key routes.
6. Implement SearXNG as an instance-profile adapter, not a global provider.
   Require explicit base URL/trust metadata, support self-hosted fixtures, and
   classify limiter/upstream failures without rotating instances.
7. Add contract tests per candidate for URL/query encoding, capabilities,
   transport, parser schema, pagination, empty/malformed/control states,
   deterministic metadata, and partial-result behavior.
8. Update the engine matrix, verification timestamps, examples, diagnostics,
   and changelog after each provider promotion. Run offline tests before any
   opt-in live smoke observation.

### Acceptance criteria

- Every selected candidate has a documented operator/index model, baseline URL,
  pagination/country assumptions, selector/API contract, risks, sanitized
  fixtures, and a passing provider contract test.
- Every selected endpoint is usable without an API key, login, or
  authentication; credentialed alternatives are not silently used as fallback.
- HTTP and browser plugins expose the same normalized result and typed failure
  semantics; transport-specific concerns remain behind the plugin boundary.
- Upstream provider provenance is never guessed or silently collapsed into the
  plugin’s own identity.
- SearXNG selection is instance-scoped and does not rotate public instances or
  bypass limiters/CAPTCHAs.
- SearXNG selection is instance-scoped and does not rotate public instances or
  bypass limiters/CAPTCHAs.
- Existing eleven-engine behavior and the complete offline suite remain green.
