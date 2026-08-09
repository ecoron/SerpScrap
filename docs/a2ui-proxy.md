# Public Proxy Source and Selection Plan

## Status

This document describes the current implementation plan for controlled proxy
use in SerpScrap. It covers migration from the legacy `proxy_file` parser and
global proxy cycle to validated sources, health checks, and engine-aware
selection.

Public proxies are unreliable and can inspect traffic. They must only be used
for permitted, rate-limited requests. CAPTCHAs and explicit access controls
must not be bypassed through unlimited proxy rotation.

## Existing fragments and target architecture

The current code already contains a local-file parser in `scrapcore/tools.py`,
global proxy assignment in `scrapcore/core.py`, database models for `Proxy` and
`SearchEngineProxyStatus`, and Chrome support for unauthenticated HTTP/SOCKS
proxies. Source refresh, health checks, and engine-specific status handling
were missing.

The target flow is:

```text
ProxySource -> ProxyParser -> ProxyPool -> ProxyHealthChecker
                                      -> ProxySelector -> SearchJob/Selenium
```

Sources provide candidates only. A proxy is eligible for a search job only
after validation and a successful health check.

## Implementation phases

### Phase 1: Contracts and compatibility

- Document acceptable use, request limits, cooldowns, and data-protection
  requirements.
- Keep `proxy_file` working as a legacy source during migration.
- Separate transient network failures from blocks, CAPTCHAs, and consent
  states.
- Decide whether public proxies are a manual fallback or an automatic,
  bounded network-error fallback.

### Phase 2: Typed model and parser

Add a dedicated `scrapcore/proxy.py` module containing:

- `ProxyEndpoint` with protocol, host, port, optional credentials, and source;
- strict protocol, host, port, IPv6, and credential parsing;
- normalized keys and redacted log representations.

Supported input should include `proto://host:port`, `host:port`, and the legacy
`proto host:port [user:password]` format.

### Phase 3: Proxy sources

The first implementation provides:

- `FileProxySource` for one explicit file;
- `DirectoryProxySource` for files in one explicit directory;
- `UrlProxySource` for explicitly configured HTTPS lists.

Directory sources are not searched outside their configured directory. File
and URL sources support newline, JSON, and CSV records. URL sources use HTTPS,
timeouts, response-size limits, and a filesystem cache. A failed source is
logged without discarding successful sources.

Configuration is based on `proxy_sources`, for example:

```python
{
    "proxy_sources": [
        {"type": "file", "location": "data/proxies.txt"},
        {"type": "directory", "location": "data/proxy-sources"},
        {"type": "url", "location": "https://example.test/proxies.json"},
    ],
    "proxy_source_timeout": 10,
    "proxy_cache_ttl": 900,
    "proxy_allowed_protocols": ["http", "socks5"],
    "proxy_allowed_countries": ["DE", "FR", "NL", "BE", "AT", "PL"],
    "proxy_max_age_seconds": 86400,
    "proxy_max_endpoints": 500,
}
```

JSON records may use `ip` or `host`, `port`, `protocol` or `type`,
`country_code` or `country`, and `last_checked`. CSV records use the same
field names. Newline records retain the legacy `proto host:port` format.

### Recommended public-list sources

The source URLs remain deployment configuration and are not baked into the
image. Candidates for a first EU-filtered setup are:

- [ProxyScrape Free Proxy List](https://proxyscrape.com/free-proxy-list) and
  its [machine-readable repository](https://github.com/ProxyScrape/free-proxy-list);
- [IPLocate Free Proxy List](https://github.com/iplocate/free-proxy-list);
- [Stormsia Proxy List](https://stormsia.github.io/proxy-list/);
- [Databay Free Proxy List](https://databay.com/free-proxy-list).

Treat all public lists as untrusted candidate feeds. Apply country and protocol
filters, retain a bounded number of candidates, check freshness, then run the
SerpScrap health check before a candidate can reach Chrome. Do not transmit
credentials, cookies, or sensitive data through these public endpoints.

### Phase 4: Pool and health checks

`ProxyPool` and `ProxyHealthChecker` load, normalize, deduplicate, and check
proxies through `proxy_check_url`. They track online state, latency, failures,
cooldown, and the last error. HTTP proxies are checked through the configured
HTTP(S) endpoint; SOCKS endpoints receive a bounded TCP reachability check in
this increment.

The database persists source, latency, failure count,
cooldown, and last-error metadata, while `SearchEngineProxyStatus` stores
engine-specific availability. Health checks require SSRF protection,
response-size limits, and an allowlist for check endpoints.

### Phase 5: Engine-aware selection

Replace the global cycle in `Core._group_jobs()` with `ProxyPool.select()`.
Selection must consider search engine, cooldown, failure rate, latency, and
parallel-use limits. Initial strategies are `round_robin` and
`least_failures`. A proxy changes only at a defined retry boundary, not for
every navigation.

### Phase 6: Selenium and retry integration

- Keep a stable proxy identity on `ScrapeJob`.
- Report network, startup, and provider failures to the pool.
- Retry transient network failures only within configured limits.
- Stop on explicit blocks, CAPTCHAs, and consent requirements unless an
  explicit provider fallback is configured.
- Keep authenticated proxies disabled until a secure Chrome extension or CDP
  solution is implemented and tested.

### Phase 7: API, UI, and operations

Expose source refresh, healthy/blocked/unverified counts, engine availability,
last error, and cooldown without credentials. Add manual refresh and test
operations only after the backend contracts are stable. Do not bake public
proxy lists into Docker images.

## Background refresh

The API service runs a daemon proxy refresh worker when
`proxy_auto_refresh_enabled` is true. It reloads the configured file,
directory, and HTTPS sources, checks the bounded endpoint pool in parallel,
and persists health state. The default interval is 900 seconds (15 minutes)
and can be changed with `proxy_auto_refresh_interval_seconds` (minimum 60
seconds). The manual **Test proxies** and **Refresh and save** actions remain
available; the latter persists an immediate refresh.

## Test and acceptance strategy

Required tests include parser formats and invalid entries, file/directory/URL
sources with mocked HTTP, timeout and response-size handling, health states,
engine-aware selection, cooldown and parallel limits, Selenium retry behavior,
bounded block handling, credential redaction, and legacy `proxy_file`
compatibility.

The tests run in the Pipenv environment. Every implementation increment must
update `CHANGELOG.md` under `[Unreleased]`.

Acceptance requires that no unvalidated proxy reaches Chrome, proxy status is
engine-aware, blocks cannot cause endless rotation, legacy configuration still
works, credentials never reach logs/API/UI, and unit/integration/regression
tests are green.

## Recommended order

1. Implement contracts, typed endpoints, and parsers.
2. Add file, directory, JSON, CSV, and HTTPS sources.
3. Add health checks and pool state.
4. Integrate selection into `Core`.
5. Add database status and bounded Selenium fallback behavior.
6. Complete tests, API/UI, and operations documentation.
7. Enable selected public sources only after local integration tests pass.
