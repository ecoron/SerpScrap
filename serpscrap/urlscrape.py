"""Safe, cache-aware enrichment of parsed result URLs."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chardet
import urllib3
from urllib3.exceptions import (
    ConnectTimeoutError,
    HTTPError,
    MaxRetryError,
    NameResolutionError,
    ReadTimeoutError,
    SSLError,
)
from urllib3.util import Retry, Timeout

from scrapcore.scraper.browser import ChromeIdentityProvider


class UrlFetchError(RuntimeError):
    """A classified URL-enrichment failure."""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    url: str
    headers: dict[str, str]
    body: bytes


class HttpClient:
    """Small injectable HTTP boundary with explicit representation limits."""

    accepted_content_types = ("text/html", "application/xhtml+xml")

    def __init__(self, config: dict[str, Any]):
        self.timeout = Timeout(
            connect=float(config.get("url_connect_timeout", 10)),
            read=float(config.get("url_read_timeout", 20)),
        )
        self.max_redirects = int(config.get("url_max_redirects", 5))
        self.max_bytes = int(config.get("url_max_response_bytes", 5 * 1024 * 1024))
        self.user_agent = ChromeIdentityProvider().resolve(
            config.get("user_agent") or None, config.get("chrome_binary") or None
        )
        configured_headers = dict(config.get("headers", {}))
        language = str(config.get("language", "en-US"))
        primary_language = language.split("-", 1)[0]
        self.headers = {
            "Accept": configured_headers.get(
                "Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": configured_headers.get(
                "Accept-Language", f"{language},{primary_language};q=0.9"
            ),
            "User-Agent": self.user_agent,
        }
        self.pool = urllib3.PoolManager(num_pools=max(1, int(config.get("url_threads", 6))))

    def fetch(self, url: str) -> HttpResponse:
        response = None
        reusable = False
        try:
            response = self.pool.request(
                "GET",
                url,
                headers=self.headers,
                timeout=self.timeout,
                redirect=True,
                retries=Retry(
                    total=self.max_redirects,
                    connect=0,
                    read=0,
                    redirect=self.max_redirects,
                    status=0,
                    raise_on_redirect=True,
                ),
                preload_content=False,
                decode_content=False,
            )
            status = int(response.status)
            if status >= 400:
                raise UrlFetchError("http", f"HTTP {status}")
            headers = {key: value for key, value in response.headers.items()}
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type not in self.accepted_content_types:
                raise UrlFetchError(
                    "unsupported_content", f"unsupported content type: {content_type or 'missing'}"
                )
            declared = response.headers.get("Content-Length")
            if declared:
                try:
                    declared_size = int(declared)
                except ValueError as exc:
                    raise UrlFetchError("malformed_response", "invalid Content-Length") from exc
                if declared_size > self.max_bytes:
                    raise UrlFetchError(
                        "oversized_response", "declared response size exceeds limit"
                    )
            body = response.read(amt=self.max_bytes + 1, decode_content=False)
            if len(body) > self.max_bytes:
                raise UrlFetchError("oversized_response", "response body exceeds limit")
            reusable = True
            encoding = response.headers.get("Content-Encoding", "").lower()
            if encoding in {"gzip", "deflate"}:
                window_bits = zlib.MAX_WBITS | 16 if encoding == "gzip" else zlib.MAX_WBITS
                try:
                    decompressor = zlib.decompressobj(window_bits)
                    body = decompressor.decompress(body, self.max_bytes + 1)
                    if decompressor.unconsumed_tail or len(body) > self.max_bytes:
                        raise UrlFetchError(
                            "oversized_response", "decompressed response exceeds limit"
                        )
                    body += decompressor.flush(self.max_bytes + 1 - len(body))
                    if len(body) > self.max_bytes:
                        raise UrlFetchError(
                            "oversized_response", "decompressed response exceeds limit"
                        )
                except zlib.error as exc:
                    raise UrlFetchError("decoding", "invalid compressed response") from exc
            elif encoding:
                raise UrlFetchError(
                    "unsupported_content", f"unsupported content encoding: {encoding}"
                )
            return HttpResponse(
                status=status,
                url=response.geturl(),
                headers=headers,
                body=body,
            )
        except UrlFetchError:
            raise
        except (ConnectTimeoutError, ReadTimeoutError) as exc:
            raise UrlFetchError("timeout", str(exc)) from exc
        except NameResolutionError as exc:
            raise UrlFetchError("dns", str(exc)) from exc
        except SSLError as exc:
            raise UrlFetchError("tls", str(exc)) from exc
        except MaxRetryError as exc:
            category = "redirect" if "redirect" in str(exc).lower() else "network"
            raise UrlFetchError(category, str(exc.reason)) from exc
        except HTTPError as exc:
            raise UrlFetchError("network", str(exc)) from exc
        finally:
            if response is not None:
                if reusable:
                    response.release_conn()
                else:
                    response.close()


class UrlScrape:
    """Fetch and cache result-page metadata through an injectable HTTP client."""

    meta_robots_pattern = re.compile(
        r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\'](.*?)["\'][^>]*>', re.I
    )
    meta_title_pattern = re.compile(r"<title[^>]*>([^<]+)</title>", re.I)

    def __init__(self, config: dict[str, Any] | None = None, http_client: Any = None):
        if config is None:
            from serpscrap.config import Config

            config = Config().get()
        self.config = config
        self.cache_dir = Path(config["cachedir"])
        self.url_threads = int(config["url_threads"])
        self.results: list[dict[str, Any]] = []
        self.http_client = http_client or HttpClient(config)
        self.assure_path_exists(self.cache_dir)

    @staticmethod
    def assure_path_exists(cache_dir: str | Path) -> None:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def adjust_encoding(data: bytes) -> dict[str, Any]:
        detected = chardet.detect(data).get("encoding") or "utf-8"
        try:
            text = data.decode(detected)
        except (LookupError, UnicodeDecodeError):
            text = data.decode("utf-8", "replace")
        return {"encoding": detected, "data": text}

    def _cache_path(self, url: str) -> Path:
        identity = getattr(self.http_client, "user_agent", "")
        language = getattr(self.http_client, "headers", {}).get("Accept-Language", "")
        digest = hashlib.sha256(f"{url}\0{identity}\0{language}".encode()).hexdigest()
        return self.cache_dir / f"url-{digest}.json"

    @staticmethod
    def _write_atomic(path: Path, result: dict[str, Any]) -> None:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
            ) as handle:
                temporary = Path(handle.name)
                json.dump(result, handle, ensure_ascii=False)
                handle.flush()
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def scrap_url(self, url: str) -> dict[str, Any]:
        cache_file = self._cache_path(url)
        try:
            result = json.loads(cache_file.read_text(encoding="utf-8"))
            result["cache_hit"] = True
        except (OSError, json.JSONDecodeError):
            try:
                result = self.fetch_url(url, cache_file)
            except UrlFetchError as exc:
                result = {
                    "status": "error",
                    "url": url,
                    "error_category": exc.category,
                    "error": str(exc),
                }
        self.results.append(result)
        return result

    def fetch_url(self, url: str, cache_file: str | Path) -> dict[str, Any]:
        response = self.http_client.fetch(url)
        encoded = self.adjust_encoding(response.body)
        html = encoded["data"]
        meta_robots = self.meta_robots_pattern.findall(html)
        meta_title = self.meta_title_pattern.findall(html)
        result = {
            "meta_robots": meta_robots[0][:15] if meta_robots else "",
            "meta_title": meta_title[0] if meta_title else "",
            "status": response.status,
            "url": response.url,
            "encoding": encoded["encoding"],
            "last_modified": response.headers.get("Last-Modified"),
            "cache_hit": False,
        }
        self._write_atomic(Path(cache_file), result)
        return result
