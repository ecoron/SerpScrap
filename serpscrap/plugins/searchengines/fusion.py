"""Deterministic, pure cross-engine result fusion."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def canonical_url(value: str) -> str:
    """Normalize only representation noise; never merge distinct paths."""

    parts = urlsplit(value.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return value
    query = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith(("utm_", "gclid", "fbclid"))]
    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


@dataclass(frozen=True, slots=True)
class FusionSettings:
    rrf_k: int = 60
    provider_family_cap: bool = False


class ResultFusion:
    """Fuse rows while retaining one representative and provenance metadata."""

    version = "phase4-rrf-v1"

    def __init__(self, settings: FusionSettings | None = None) -> None:
        self.settings = settings or FusionSettings()
        if self.settings.rrf_k < 1:
            raise ValueError("rrf_k must be positive")

    def fuse(self, rows: Iterable[dict[str, Any]], weights: dict[str, float], families: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
        families = families or {}
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            url = row.get("serp_url")
            if url:
                grouped[(str(row.get("query") or ""), canonical_url(str(url)))].append(row)
        ranked: list[dict[str, Any]] = []
        for (_, normalized), matches in grouped.items():
            best_by_engine: dict[str, dict[str, Any]] = {}
            for row in matches:
                engine = str(row["search_engine"])
                rank = int(row.get("serp_rank") or 0)
                current = best_by_engine.get(engine)
                if current is None or rank < int(current.get("serp_rank") or 0):
                    best_by_engine[engine] = row
            contributions = []
            seen_families: set[str] = set()
            for engine, row in best_by_engine.items():
                family = families.get(engine) or engine
                if self.settings.provider_family_cap and family in seen_families:
                    continue
                seen_families.add(family)
                rank = max(1, int(row.get("serp_rank") or 1))
                contributions.append(float(weights.get(engine, 0.0)) / (self.settings.rrf_k + rank))
            representative = min(
                matches,
                key=lambda row: (
                    -float(weights.get(str(row["search_engine"]), 0.0)) / (self.settings.rrf_k + max(1, int(row.get("serp_rank") or 1))),
                    int(row.get("serp_rank") or 0),
                    str(row.get("search_engine") or ""),
                    str(row.get("serp_url") or ""),
                ),
            ).copy()
            representative["serp_url"] = normalized
            representative["relevance_score"] = sum(contributions)
            representative["engine_match_count"] = len(best_by_engine)
            representative["independent_provider_count"] = len(seen_families)
            representative["best_rank"] = min(int(row.get("serp_rank") or 0) for row in matches)
            representative["matched_engines"] = sorted(best_by_engine)
            representative["fusion_id"] = sha256(normalized.encode("utf-8")).hexdigest()[:16]
            ranked.append(representative)
        ranked.sort(
            key=lambda row: (
                -float(row["relevance_score"]),
                -int(row["independent_provider_count"]),
                -int(row["engine_match_count"]),
                int(row["best_rank"]),
                str(row.get("search_engine") or ""),
                str(row.get("serp_url") or ""),
            )
        )
        return ranked
