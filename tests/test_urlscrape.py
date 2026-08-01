import gzip
from email.message import Message
from pathlib import Path

import pytest

from serpscrap.config import Config
from serpscrap.urlscrape import HttpClient, HttpResponse, UrlFetchError, UrlScrape


class FakeHttpClient:
    user_agent = "Mozilla/5.0 Chrome/151.0.0.0 Safari/537.36"
    headers = {"Accept-Language": "en-US,en;q=0.9"}

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def fetch(self, url):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


def _config(tmp_path: Path):
    config = Config().get()
    config["cachedir"] = str(tmp_path)
    return config


def test_url_scrape_fetches_metadata_and_reuses_representation_cache(tmp_path):
    response = HttpResponse(
        status=200,
        url="https://example.com/final",
        headers={"Last-Modified": "today"},
        body=b"<html><head><title>Example</title><meta name='robots' content='index'></head></html>",
    )
    client = FakeHttpClient(response=response)
    scraper = UrlScrape(_config(tmp_path), http_client=client)

    first = scraper.scrap_url("https://example.com")
    second = scraper.scrap_url("https://example.com")

    assert first["meta_title"] == "Example"
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert client.calls == 1
    assert not list(tmp_path.glob("*.tmp"))


def test_url_scrape_exposes_classified_failure(tmp_path):
    client = FakeHttpClient(error=UrlFetchError("timeout", "read timed out"))

    result = UrlScrape(_config(tmp_path), http_client=client).scrap_url(
        "https://example.com"
    )

    assert result["status"] == "error"
    assert result["error_category"] == "timeout"


def test_url_cache_key_changes_with_request_identity(tmp_path):
    first = FakeHttpClient()
    second = FakeHttpClient()
    second.user_agent = "Mozilla/5.0 Chrome/152.0.0.0 Safari/537.36"

    assert UrlScrape(_config(tmp_path), first)._cache_path("https://example.com") != UrlScrape(
        _config(tmp_path), second
    )._cache_path("https://example.com")


class FakeResponse:
    def __init__(
        self, body=b"<html></html>", content_type="text/html", content_encoding=None
    ):
        self.body = body
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if content_encoding:
            self.headers["Content-Encoding"] = content_encoding
        self.released = False
        self.closed = False

    def read(self, amt, decode_content=False):
        return self.body[:amt]

    def geturl(self):
        return "https://example.com/final"

    def release_conn(self):
        self.released = True

    def close(self):
        self.closed = True


def test_http_client_sends_chrome_identity_and_explicit_headers():
    captured = {}

    class Pool:
        def request(self, method, url, **options):
            captured.update({"method": method, "url": url, **options})
            return FakeResponse()

    client = HttpClient(Config().get())
    client.pool = Pool()

    response = client.fetch("https://example.com")

    assert "Chrome/" in captured["headers"]["User-Agent"]
    assert captured["headers"]["Accept-Language"] == "en-US,en;q=0.9"
    assert captured["timeout"].connect_timeout == 10
    assert captured["timeout"].read_timeout == 20
    assert captured["retries"].redirect == 5
    assert response.status == 200


@pytest.mark.parametrize(
    ("response", "category"),
    [
        (FakeResponse(b"too large"), "oversized_response"),
        (FakeResponse(content_type="application/pdf"), "unsupported_content"),
    ],
)
def test_http_client_rejects_unsafe_representations(response, category):
    class Pool:
        def request(self, method, url, **options):
            return response

    config = Config().get()
    config["url_max_response_bytes"] = 4
    client = HttpClient(config)
    client.pool = Pool()

    with pytest.raises(UrlFetchError) as captured:
        client.fetch("https://example.com")

    assert captured.value.category == category
    assert response.released or response.closed


def test_http_client_bounds_and_decodes_gzip_after_transport_read():
    response = FakeResponse(gzip.compress(b"<html>compressed</html>"), content_encoding="gzip")

    class Pool:
        def request(self, method, url, **options):
            return response

    client = HttpClient(Config().get())
    client.pool = Pool()

    result = client.fetch("https://example.com")

    assert result.body == b"<html>compressed</html>"
    assert response.released is True
