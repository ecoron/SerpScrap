# Refactoring 2026 Change Log

This file records the implementation work performed against
`docs/refactoring2026.md`.

## 2026-08-01

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
