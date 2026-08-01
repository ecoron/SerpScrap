# Refactoring 2026 Change Log

This file records the implementation work performed against
`docs/refactoring2026.md`.

## 2026-08-01

### Refactoring Phase 5 - planning

- Added the Phase 5 plan for production integration of all eleven documented search-engine plugins, configurable engine selection and global/per-engine parallelism, concrete fixture-backed provider adapters, normalized JSON output, deterministic relevance fusion, cache/history migration, and provider-safe verification.
- Documented Python and CLI examples for four configured search engines with a maximum of four concurrent requests.
- Changed CLI option handling so omitted search options inherit the validated ``Config`` defaults.

### Refactoring Phase 4 - plugin registry and multi-engine execution

- Added the trusted `serpscrap.plugins.searchengines` contract and explicit registry for Google plus Bing, Yandex, Yahoo, DuckDuckGo, Ecosia, Qwant, Startpage, Brave Search, Swisscows, and Mojeek.
- Added country-aware engine URL construction, normalized engine rows with `search_engine` and ISO `country_code`, generic fixture-friendly organic-card parsing, response-state classification, and a Selenium capture adapter with per-call driver ownership.
- Added bounded concurrent fan-out through `MultiEngineRunner`, engine-scoped limits, structured partial failures, deterministic completion ordering, and compatibility routing that leaves the legacy Google ORM path intact for Google-only requests.
- Added pure URL canonicalization and versioned weighted reciprocal-rank fusion with engine frequency, position, market-share snapshots, provider-family metadata, fallback handling for StatCounter's `Other` bucket, and explainable provenance fields.
- Bumped the public report schema to version 2 and added engine/country provenance to legacy Google rows as well as plugin metadata to multi-engine failures.
- Updated the result contract documentation for engine provenance and fused multi-engine ranking fields.
- Extended configuration and CLI with registered engine validation, `--engine`, `--country`, engine workers, and market-weight settings; added Phase 4 contract/fan-out/fusion tests and updated the stale URL-enrichment language assertion to match the configured `de-DE` locale.

### Refactoring Phase 4 - planning and search-engine research

- Added the Phase 4 plan for a trusted in-package search-engine plugin registry, eleven initial engines, bounded multi-engine thread fan-out, country-aware result provenance, partial failures, deterministic weighted reciprocal-rank fusion, compatibility migration, and fixture-first verification.
- Added `docs/searchengines.md` with the July 2026 European market-share snapshot, transparent handling of StatCounter's unreported `Other` engines, the initial engine cohort, query/SERP reconnaissance, and source links.

### Refactoring Phase 3 - request identity and traffic policy

- Added a central `ChromeIdentityProvider` that resolves a non-headless desktop user agent from the installed Chrome major version and otherwise uses a dated Chrome 151 fallback based on Google's July 22, 2026 early-stable desktop release, with a test-enforced 120-day maintenance window; explicit desktop Chrome overrides remain supported and validated.
- Applied the effective identity consistently to Chrome command-line/CDP configuration and URL-enrichment `User-Agent`, `Accept`, and `Accept-Language` headers; Chrome language, viewport, and identity now come from one validated browser settings object.
- Added validated request pacing, jitter ranges, bounded transient retries with exponential backoff, attempt counts, conservative single-worker defaults, and a thread-safe run circuit breaker shared by browser workers.
- Preserved one Chrome session across pages of a query and retained cache-before-browser behavior. Explicit Google block/CAPTCHA, consent, and rate-limit states stop the affected job without automatic identity/proxy rotation or access-control bypass.
- Expanded Google state classification with CAPTCHA/interstitial signatures, rate-limit text, localized empty-result signals, and precedence before parsing; routine failure/retry logs now use correlation IDs instead of query contents.
- Extended cache representation keys with search type, language, and requested result count so incompatible SERP variants cannot collide.

### Refactoring Phase 3 - Google result formats

- Extended Google URL construction and validation with the `image`, `news`, `shopping`, and `videos` verticals alongside normal search and exposed the same values through CLI `--search-type`.
- Reworked the offline Google parser into a common result assembler plus isolated specialized selectors for canonical `results`, `image`, `news`, `shopping`, and `videos` types.
- Added mixed-SERP precedence, cross-format URL normalization/deduplication, deterministic per-type ranks, and observable warnings for unknown `data-serp-type` modules.
- Added optional source/date, price/merchant, duration, image URL, and thumbnail URL fields to parser values, SQLite link persistence, schema upgrade handling for existing databases, and canonical public JSON rows.

### Refactoring Phase 3 - URL enrichment

- Replaced direct unbounded `urllib.request.urlopen()` use with an injectable pooled `HttpClient` that reuses per-origin connections, sends the effective Chrome identity, applies separate connect/read timeouts and redirect limits, accepts only HTML/XHTML, and bounds compressed and decompressed response sizes.
- Declared urllib3 as a direct bounded runtime dependency for the pooled transport; the existing runtime lock already pins the verified urllib3 2.7.0 build.
- Added classified DNS, TLS, timeout, network, HTTP, redirect, unsupported-content, oversized-response, and decoding failures instead of collapsing every exception into an indistinguishable error.
- Changed URL-enrichment cache keys to include request identity and language, added explicit cache-hit metadata, and made cache writes atomic with temporary-file cleanup.
- Retained `SerpScrap.scrap_url()` and `UrlScrape.scrap_url()` compatibility boundaries while separating transport, decoding, metadata extraction, and cache behavior for deterministic testing.

### Refactoring Phase 3 - tests, documentation, and verification

- Added captured mixed-SERP and image fixtures plus deterministic tests for all five documented result formats, type-specific fields, vertical query parameters, installed/fallback Chrome identity, fallback expiry, pacing, circuit breaking, retry counts, and no-retry block handling.
- Added URL-enrichment tests for effective headers, timeout propagation, content-type and response-size rejection, classified failures, representation-aware cache separation, cache hits, and atomic temporary-file cleanup.
- Updated configuration, result schema, examples, installation guidance, CLI help, and README for the Phase 3 request policy and search formats.
- Verified 57 deterministic offline tests with the bundled workspace Python, Ruff with no findings, and focused mypy checks for the new browser/request and URL-enrichment modules. `pipenv` was not available on this execution host, so the same commands could not be launched through `pipenv run`; the supported `pipenv shell` and `pipenv run` workflows remain documented.
- Built the Phase 3 source distribution and wheel successfully without build isolation; the browser/network smoke test remains opt-in and was not invoked to avoid generating an unnecessary live Google request.

### Refactoring Phase 2 - public contract and architecture

- Added deeply immutable, validated `SearchRequest` values and a `SearchApplication` boundary that returns a canonical `SearchReport` without exposing ORM, session, browser, or parser objects publicly.
- Added the direct `SerpScrap.search()` API with friendly page, worker, visibility, screenshot, URL-scrape, output, and overwrite options; retained `init()`/`run()` and low-level `scrap()` as Phase 1 compatibility adapters.
- Standardized successful Python results as a deterministic `list[dict]` containing native JSON types and stable ordering across queries, pages, result types, ranks, concurrency, and cache hits.
- Separated structured page failures and related keywords from successful result rows through `get_failures()`, `get_related()`, and `SearchReport` metadata.
- Propagated worker correlation IDs into persisted failure outcomes and retained successful rows for partial requests.
- Added an injectable runner protocol so application behavior can be tested with in-memory fakes independently of Chrome, network access, SQLite, or filesystem output.
- Isolated public exceptions and lazy-loaded the default composition root; importing `serpscrap` no longer imports Selenium or SQLAlchemy.

### Refactoring Phase 2 - JSON persistence and cleanup

- Added a single `JsonResultWriter` that writes UTF-8 JSON arrays with native types, Unicode preservation, automatic `.json` suffixes, parent-directory creation, temporary-file cleanup, atomic replacement, and explicit overwrite protection.
- Added `SerpScrap.save_json()` and CLI `--output`/`--overwrite`; CLI stdout continues to contain the same JSON result array while logs remain on stderr.
- Removed `CsvWriter`, `CsvStreamWriter`, `SerpScrap.as_csv()`, CSV output branches, and obsolete `output_filename`/`print_results` configuration. Legacy output settings and `.csv` paths now produce actionable migration errors.
- Removed the duplicate `ResultWriter` and unreachable legacy `scrapcore.scraping` workflow after confirming there were no remaining imports.
- Removed output side effects from `Core` and `CacheManager`; result serialization now happens once at the public boundary.
- Added independently configurable SQLite history through `store_history`; disabling it uses an in-memory database while cache and JSON output remain independently selectable.
- Moved SQLite history into a post-assembly repository adapter. Result parsing always uses an isolated in-memory session, and optional history failures are reported without discarding successful rows.

### Refactoring Phase 2 - tests and documentation

- Added contract tests for native JSON types, deterministic ordering, partial failures, correlation IDs, direct API use, exact file round trips, Unicode, extension validation, overwrite protection, removed CSV APIs, CLI output options, and history-free execution.
- Migrated README, result/configuration/Docker documentation, and all examples to the direct API and JSON output; replaced the CSV example with `example_json.py`.
- Preserved the Phase 1 offline suite and browser lifecycle guarantees while increasing deterministic offline coverage from 18 to 31 tests.

### Refactoring Phase 2 - verification

- Verified 31 deterministic offline tests locally; the browser/network smoke test remains opt-in.
- Verified Ruff across application, infrastructure, tests, and examples with no findings.
- Verified focused mypy checks for the six new Phase 2 public/application and repository modules with no findings.
- Verified that a clean public package import loads neither Selenium nor SQLAlchemy.
- Built the source distribution and wheel successfully without build isolation using the installed locked toolchain.

### Baseline and architecture

- Audited the public API, CLI, configuration, cache, parser, database, worker factory, and Selenium implementation.
- Identified and removed the eager debug WebDriver startup from `SerpScrap.init()`; initialization is side-effect free again.
- Replaced mutable, incomplete worker jobs with immutable `ScrapeJob` values and structured `CapturedPage`, `ScrapeFailure`, and `ScrapeJobResult` outcomes.
- Separated concurrent browser capture from single-threaded parsing, caching, database persistence, and result serialization.

### Packaging and dependencies

- Added PEP 517/518 package metadata in `pyproject.toml` with Python 3.10+ support, bounded runtime dependencies, development extras, a CLI entry point, and pytest/ruff configuration.
- Updated the supported dependency ranges for Selenium 4, SQLAlchemy 2, lxml 6, Beautiful Soup, bleach, cssselect, and the test toolchain.
- Removed the runtime dependency on `chromedriver-autoinstaller`; Selenium Manager now resolves ChromeDriver when no explicit path is configured.
- Removed legacy `setup.py` and `Pipfile` metadata after verifying that they conflicted with the PEP 517/639 build configuration.

### Configuration and browser management

- Expanded the backward-compatible `Config` facade with explicit Chrome binary, headless, window, timeout, language, and container settings.
- Added boundary validation for browser type, engines, search type, worker/page counts, proxy configuration, cache paths, and Chrome settings.
- Added an injectable `ChromeDriverFactory`, immutable `BrowserSettings`, Google URL adapter, and filesystem-safe diagnostic artifact names.
- Configured modern headless Chrome with `--headless=new`; explicit ChromeDriver and Chrome binary paths remain supported for controlled environments.

### Scraping pipeline

- Replaced form interaction and fixed sleeps with direct, encoded Google query URLs and explicit SERP-state waits.
- Added typed classification for blocked traffic, consent requirements, timeouts, WebDriver failures, and browser startup failures.
- Narrowed block detection to explicit rejection URLs and messages so ordinary pages that load reCAPTCHA support code are not misclassified.
- Guaranteed `driver.quit()` in all successful and exceptional worker paths.
- Added bounded browser concurrency while keeping SQLAlchemy sessions and cache writes out of worker threads.
- Preserved captured pages when a later requested page fails and persisted structured failure SERPs for diagnostics.

### Parsing and persistence

- Replaced the non-functional mixed parser implementation with an offline lxml Google parser using ordered selector fallbacks.
- Added deterministic URL normalization, deduplication, organic rank assignment, result-stat extraction, and image result parsing.
- Updated SQLAlchemy declarative imports for 2.x and disabled commit expiration so fully materialized public results can be safely detached.
- Fixed cache directory creation for nested paths and corrected bleach tag handling for modern immutable allowlists.

### Tests and delivery

- Added deterministic offline tests for configuration validation, Google URL construction, SERP-state classification, parser fixtures, URL deduplication, Core persistence, partial worker results, startup errors, and WebDriver cleanup.
- Added an opt-in Chrome/network smoke test marked `browser`; deterministic test runs exclude it explicitly.
- Added exact runtime and development lock files based on the verified 2026 dependency set.
- Replaced Travis CI with a GitHub Actions Python 3.10-3.14 matrix covering lint, focused type checking, offline tests, and package builds.
- Replaced the legacy Chrome installer with a Docker image pinned to Chrome for Testing and ChromeDriver 151.0.7922.71, plus a browser-startup container smoke test.
- Updated the CLI, README, and installation guide for Selenium Manager, headless Chrome, pages, workers, and diagnostics.
- Preserved cache-hit request metadata (engine, scrape method, page, and cache origin) when reparsing stored HTML.

### Verification

- Verified 18 deterministic offline tests locally; the separate browser smoke test remains opt-in.
- Verified Ruff with no findings and focused mypy checks with no findings under the Python 3.10 target.
- Built both the source distribution and wheel successfully with the locked build toolchain.
- Launched and terminated local headless Chrome successfully. The live Google smoke request was rejected by Google with an explicit unusual-traffic response in this execution environment; the scraper returned the expected non-retryable `blocked` failure and did not attempt CAPTCHA bypass.
- Docker execution could not be run locally because Docker is unavailable in the current environment; CI contains a deterministic Chrome-startup container smoke test.

### Compatibility and Click CLI follow-up

- Restored `setup.py` as a metadata-free Setuptools compatibility shim; `pyproject.toml` remains authoritative.
- Restored `Pipfile` as an editable development frontend without duplicating runtime dependency declarations.
- Added Click 8.4 as a bounded and locked runtime dependency.
- Replaced argparse with Click commands: `search` for SERP retrieval and `browser-check` for a network-free Chrome health check.
- Added global `--log-level` and `--log-format text|json` options. Logs use stderr while machine-readable search results remain on stdout.
- Added Click CLI tests for command discovery, JSON output, and JSON-formatted log output.
### Refactoring Phase 5 - production integration

- Added readiness, disable-reason, fixture-version, provider-family, capability, and review metadata to every registered engine, with validated duplicate/unknown/disabled selections.
- Added validated per-engine worker ceilings, ranking settings, provider capability checks, and cache identity dimensions for country and plugin version.
- Made cache writes atomic and added deterministic fusion/report metadata containing the immutable snapshot ID, normalized weights, fallback share, provider families, and plugin metadata.
- Added Phase 5 plugin status documentation and offline configuration/cache regression tests while retaining Google-only compatibility.
