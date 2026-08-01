# SerpScrap Refactoring Plan 2026

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
