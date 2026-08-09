from datetime import datetime, timezone
from pathlib import Path

import pytest

from scrapcore.core import Core
from scrapcore.database import SearchEngineProxyStatus, fixtures, get_session
from scrapcore.proxy import (
    DirectoryProxySource,
    FileProxySource,
    ProxyEndpoint,
    ProxyHealth,
    ProxyPool,
    parse_proxy_line,
)


def test_parse_proxy_formats_and_redacts_identity():
    assert parse_proxy_line("http://127.0.0.1:8080").key == "http://127.0.0.1:8080"
    endpoint = parse_proxy_line("socks5 10.0.0.2:1080 user:secret", "fixture")
    assert endpoint == ProxyEndpoint("socks5", "10.0.0.2", 1080, "user", "secret", "fixture")
    assert endpoint.redacted == "socks5://10.0.0.2:1080"


def test_parse_proxy_rejects_invalid_protocol_and_port():
    with pytest.raises(ValueError, match="unsupported proxy protocol"):
        parse_proxy_line("ftp://127.0.0.1:21")
    with pytest.raises(ValueError, match="invalid proxy endpoint"):
        parse_proxy_line("http 127.0.0.1:not-a-port")


def test_file_and_directory_sources_are_deduplicated(tmp_path: Path):
    first = tmp_path / "first.txt"
    first.write_text("http 127.0.0.1:8080\n# ignored\n", encoding="utf-8")
    directory = tmp_path / "sources"
    directory.mkdir()
    (directory / "second.list").write_text("http 127.0.0.1:8080\nsocks5 127.0.0.2:1080\n", encoding="utf-8")

    endpoints = FileProxySource(str(first)).load() + DirectoryProxySource(str(directory)).load()
    pool = ProxyPool(endpoints)

    assert [endpoint.key for endpoint in pool.endpoints] == [
        "http://127.0.0.1:8080",
        "socks5://127.0.0.2:1080",
    ]


def test_json_csv_sources_and_country_protocol_filters(tmp_path: Path):
    json_source = tmp_path / "proxies.json"
    json_source.write_text(
        '[{"ip":"10.0.0.1","port":8080,"protocol":"http","country_code":"DE","last_checked":"2026-08-09T12:00:00Z"},'
        '{"ip":"10.0.0.2","port":1080,"protocol":"socks5","country_code":"FR"}]',
        encoding="utf-8",
    )
    csv_source = tmp_path / "proxies.csv"
    csv_source.write_text("ip,port,protocol,country_code\n10.0.0.3,8080,http,US\n", encoding="utf-8")

    config = {
        "proxy_sources": [
            {"type": "file", "location": str(json_source)},
            {"type": "file", "location": str(csv_source)},
        ],
        "proxy_allowed_protocols": ["http", "socks5"],
        "proxy_allowed_countries": ["DE", "FR"],
        "proxy_max_endpoints": 10,
        "check_proxies": False,
    }
    pool = ProxyPool.from_config(config)

    assert [endpoint.host for endpoint in pool.endpoints] == ["10.0.0.1", "10.0.0.2"]
    assert pool.endpoints[0].last_checked == datetime(2026, 8, 9, 12, tzinfo=timezone.utc)


def test_json_source_skips_unsupported_protocols_and_parses_unix_timestamps():
    from scrapcore.proxy import _parse_payload

    payload = b'[{"ip":"10.0.0.1","port":8080,"protocol":"https","last_checked":1786276800},{"ip":"10.0.0.2","port":1080,"protocol":"socks5"}]'
    endpoints = _parse_payload(payload, "https://example.test/proxies.json")

    assert [endpoint.host for endpoint in endpoints] == ["10.0.0.2"]


def test_remote_source_uses_cache_within_configured_ttl(tmp_path: Path, monkeypatch):
    from scrapcore.proxy import UrlProxySource

    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            calls.append(limit)
            return b"http 10.0.0.1:8080"

    monkeypatch.setattr("scrapcore.proxy.urllib.request.urlopen", lambda *args, **kwargs: Response())
    source = UrlProxySource("https://example.test/proxies.txt", cache_dir=str(tmp_path), cache_ttl=900)

    source.load()
    source.load()

    assert len(calls) == 1


def test_pool_selects_per_engine_and_does_not_use_unhealthy_proxy():
    endpoints = [ProxyEndpoint("http", "127.0.0.1", 8000), ProxyEndpoint("http", "127.0.0.2", 8000)]
    pool = ProxyPool(endpoints)
    pool.health[endpoints[0].key] = ProxyHealth(online=False, cooldown_until=9999999999)
    pool.health[endpoints[1].key] = ProxyHealth(online=True)

    assert pool.select("google") == endpoints[1]
    assert pool.select("bing") == endpoints[1]


def test_proxy_enabled_is_a_modern_alias_for_legacy_own_ip_switch(tmp_path: Path):
    source = tmp_path / "proxies.txt"
    source.write_text("http 127.0.0.1:8080\n", encoding="utf-8")
    config = {
        "proxy_enabled": True,
        "use_own_ip": True,
        "proxy_sources": [{"type": "file", "location": str(source)}],
        "check_proxies": False,
    }

    pool = Core._get_proxy_pool(config)

    assert pool is not None
    assert pool.endpoints[0].key == "http://127.0.0.1:8080"


def test_pool_persists_and_restores_health_and_engine_status(tmp_path: Path):
    endpoint = ProxyEndpoint("http", "127.0.0.1", 8080, source="fixture")
    pool = ProxyPool([endpoint])
    pool.health[endpoint.key] = ProxyHealth(
        online=True,
        latency_ms=12.5,
        failures=0,
        last_error="",
        checked_at=None,
    )
    config = {"supported_search_engines": ["google"], "database_name": str(tmp_path / "db")}
    session = get_session(config)()
    try:
        fixtures(config, session)
        pool.persist(session, ["google"])
        restored = ProxyPool([endpoint])
        restored.restore_from_db(session)

        health = restored.health[endpoint.key]
        assert health.online is True
        assert health.latency_ms == 12.5
        assert session.query(SearchEngineProxyStatus).count() == 1
        assert session.query(SearchEngineProxyStatus).one().available is True
    finally:
        session.close()
