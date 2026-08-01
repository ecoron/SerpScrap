# SerpScrap Refactoring Plan 2026

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
