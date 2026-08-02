"""Normalize provider result URLs without hiding the original provider value."""

# ruff: noqa: I001

from __future__ import annotations

import base64
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit


_WRAPPER_KEYS = ("url", "target", "dest", "destination", "redirect", "r", "ru", "uddg", "mediaurl", "imgurl", "adurl", "q")
_TRACKING_KEYS = {"gclid", "fbclid", "dclid", "msclkid", "ved", "ei", "oq", "form", "cvid", "sp", "ntb"}


def _clean_url(value: str) -> str | None:
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    host = (parsed.hostname or "").lower()
    if not host:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    netloc = host
    if parsed.username or parsed.password:
        return None
    if port and not ((parsed.scheme.lower() == "http" and port == 80) or (parsed.scheme.lower() == "https" and port == 443)):
        netloc += f":{port}"
    query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True) if key.lower() not in _TRACKING_KEYS and not key.lower().startswith("utm_")]
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", urlencode(query), ""))


def _unwrap(raw_url: str) -> str:
    parsed = urlsplit(raw_url)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    path = parsed.path.lower()
    # Bing's /ck/a redirect stores the target in a URL-safe base64 value prefixed by a1.
    encoded = params.get("u", "")
    if "/ck/a" in path and encoded.startswith("a1"):
        try:
            decoded = base64.urlsafe_b64decode(encoded[2:] + "=" * (-len(encoded[2:]) % 4)).decode()
            if decoded.startswith(("http://", "https://")):
                return decoded
        except (ValueError, UnicodeDecodeError):
            pass
    for key in _WRAPPER_KEYS:
        candidate = params.get(key)
        if candidate and candidate.startswith(("http://", "https://")) and (key != "q" or path in {"/url", "/aclk"} or "google" in (parsed.hostname or "")):
            return unquote(candidate)
    return raw_url


def normalize_result_url(raw_url: str | None, link_type: str | None = None) -> dict[str, str | None]:
    """Return a safe canonical URL and preserve the raw provider URL for diagnostics."""

    source_url = raw_url or ""
    if not source_url:
        return {"source_url": source_url, "canonical_url": None, "result_kind": "organic"}
    canonical_url = _clean_url(_unwrap(source_url))
    lowered_type = (link_type or "").lower()
    parsed = urlsplit(source_url)
    if any(token in lowered_type for token in ("image", "photo", "picture")) or any(token in parsed.path.lower() for token in ("/images", "/image")):
        result_kind = "image"
    elif "news" in lowered_type:
        result_kind = "news"
    elif any(token in lowered_type for token in ("video", "shopping", "product")):
        result_kind = "video" if "video" in lowered_type else "shopping"
    else:
        result_kind = "organic"
    return {"source_url": source_url, "canonical_url": canonical_url, "result_kind": result_kind}


def relevance_for_rank(rank: int) -> float:
    return round(1.0 / max(rank, 1), 6)
