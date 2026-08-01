# SerpScrap Refactoring Plan 2026

## Objective

Modernize SerpScrap so that search engine result pages (SERPs) are retrieved reliably with Selenium 4 and headless Google Chrome, parsed into the existing result model, and covered by deterministic automated tests.

## 1. Establish the Baseline

- Document the supported Python versions, search engines, search types, configuration keys, CLI behavior, and public Python API.
- Add fixture-based regression tests for representative Google SERP HTML before changing parser behavior.
- Separate offline unit tests from network-dependent browser integration tests and mark the latter explicitly.
- Record the current output schema so the refactoring does not introduce accidental API changes.

## 2. Modernize Packaging and Dependencies

- Replace `setup.py` and `Pipfile` as the authoritative package metadata with a PEP 517/518-compatible `pyproject.toml`.
- Define bounded runtime and development dependency ranges and generate a reproducible lock file.
- Upgrade Selenium, SQLAlchemy, lxml, Beautiful Soup, bleach, cssselect, and the test toolchain to mutually compatible versions.
- Remove `chromedriver-autoinstaller`; use Selenium Manager by default and retain an optional explicit ChromeDriver path for controlled environments.
- Remove deprecated Selenium and SQLAlchemy APIs, including legacy `find_element_by_*` calls and `Query.get()`.

## 3. Isolate Browser Management

- Introduce a Chrome WebDriver factory responsible for `ChromeOptions`, Selenium `Service`, proxy settings, user agent, window size, page-load strategy, and timeouts.
- Run Chrome with the current headless implementation (`--headless=new` where supported) and container-safe flags configured explicitly.
- Model browser settings as validated configuration instead of reading loosely typed dictionary keys throughout the scraper.
- Guarantee `driver.quit()` with `try/finally` or a context manager, including startup, timeout, parsing, and cancellation failures.
- Replace fixed sleeps with explicit waits for document readiness and SERP-specific conditions.

## 4. Refactor the Scraping Pipeline

- Define one immutable scrape-job type containing query, search engine, search type, requested pages, proxy, and correlation ID.
- Replace the current factory/worker contract with a bounded worker pool that accepts complete jobs and returns typed scrape results or structured failures.
- Separate the pipeline into browser acquisition, navigation, HTML capture, parsing, persistence, and result serialization stages.
- Ensure database sessions, cache writes, progress reporting, and browser instances have explicit ownership and thread-safe lifecycles.
- Preserve partial results when a later page fails and report the affected query, page, URL, and failure category.

## 5. Implement Reliable Headless SERP Retrieval

- Build search URLs directly from validated query parameters instead of typing into the search form when the engine supports stable query URLs.
- Wait for a configurable set of SERP result-container selectors and detect consent pages, CAPTCHA pages, rate limiting, redirects, and empty-result pages separately.
- Capture `driver.page_source` after the readiness condition is satisfied; store screenshots and HTML only as opt-in diagnostics.
- Update pagination to use Selenium 4 locators and URL/state-change waits rather than stale CSS selectors plus fixed delays.
- Keep engine-specific navigation and selectors behind adapters so Google-specific changes do not affect the worker infrastructure.
- Treat anti-bot detection as a typed, non-retriable or policy-controlled result; do not attempt to bypass CAPTCHAs automatically.

## 6. Stabilize Parsing and Output

- Parse captured HTML independently of Selenium so parsers can be tested entirely from fixtures.
- Update Google selectors using ordered fallbacks and validate links, titles, snippets, ranks, result types, and pagination metadata.
- Normalize redirected result URLs and reject duplicate or malformed entries deterministically.
- Keep database entities and CSV/API serialization backward compatible unless a versioned schema migration is documented.

## 7. Verification and Delivery

- Add unit tests for configuration validation, URL construction, driver options, wait conditions, error mapping, parser fixtures, and worker scheduling.
- Add a mocked WebDriver lifecycle test proving that `quit()` runs on success and on every failure path.
- Add an opt-in end-to-end smoke test that launches headless Chrome and validates at least one parsed organic result without making it part of deterministic unit-test runs.
- Replace the legacy Chrome installation script with a pinned Chrome-for-Testing or distribution-package installation in Docker, and add a container health smoke test.
- Update CI to run linting, type checking, unit tests, packaging checks, and the Docker smoke test on supported Python versions.
- Update README, CLI help, configuration documentation, examples, and changelog with installation requirements and migration notes.

## Acceptance Criteria

- A clean installation launches headless Chrome without manually downloading ChromeDriver.
- A scrape job returns structured SERP results through the existing public API and CLI.
- Browser processes are terminated after successful, failed, and cancelled jobs.
- Offline unit tests require neither Chrome nor network access and pass deterministically.
- The opt-in browser smoke test passes locally and in the project container.
- Deprecated Selenium and SQLAlchemy APIs, `chromedriver-autoinstaller`, and the legacy Chrome installation flow are removed.
