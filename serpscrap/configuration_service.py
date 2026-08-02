"""Registry-backed, database-persisted UI and search configuration."""

# ruff: noqa: I001

from __future__ import annotations

import re
from typing import Any

from serpscrap.config import Config
from serpscrap.history_store import SearchHistoryStore
from serpscrap.plugins.searchengines.registry import default_registry, SearchEngineRegistry


SAFE_KEYS = ("country_code", "search_type", "num_pages_for_keyword", "num_results_per_page")


class SearchConfigurationService:
    def __init__(
        self,
        store: SearchHistoryStore,
        registry: SearchEngineRegistry | None = None,
    ) -> None:
        self.store = store
        self.registry = registry or default_registry()

    def engines(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.registry.metadata()]

    def _default_payload(self) -> dict[str, Any]:
        defaults = Config().get()
        return {
            # Keep the Docker/API configuration aligned with the public
            # defaults from Config instead of silently enabling every plugin.
            "search_engines": [
                engine_id
                for engine_id in defaults["search_engines"]
                if self.registry.get(engine_id).enabled
            ],
            "country_code": defaults["country_code"],
            "search_type": defaults["search_type"],
            "num_pages_for_keyword": defaults["num_pages_for_keyword"],
            "num_results_per_page": defaults["num_results_per_page"],
        }

    def _validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("configuration must be an object")
        if "search_engines" not in payload:
            raise ValueError("search_engines is required")
        selected = payload["search_engines"]
        if not isinstance(selected, list) or not selected:
            raise ValueError("at least one search engine must be selected")
        selected_ids = tuple(str(engine).strip().lower() for engine in selected)
        self.registry.validate_selection(selected_ids)
        country = str(payload.get("country_code", self._default_payload()["country_code"])).upper()
        if not re.fullmatch(r"[A-Z]{2}", country):
            raise ValueError("country_code must be an ISO alpha-2 code")
        search_type = str(payload.get("search_type", "normal"))
        for engine in self.registry.validate_selection(selected_ids):
            if search_type not in engine.search_types:
                raise ValueError(f"{engine.engine_id} does not support search type {search_type}")
        pages = int(payload.get("num_pages_for_keyword", 1))
        page_size = int(payload.get("num_results_per_page", 10))
        if not 1 <= pages <= 20:
            raise ValueError("num_pages_for_keyword must be between 1 and 20")
        if not 1 <= page_size <= 100:
            raise ValueError("num_results_per_page must be between 1 and 100")
        return {
            "search_engines": list(selected_ids),
            "country_code": country,
            "search_type": search_type,
            "num_pages_for_keyword": pages,
            "num_results_per_page": page_size,
        }

    def get(self) -> dict[str, Any]:
        record = self.store.get_configuration()
        if record is None:
            payload = self._default_payload()
            return {
                "source": "defaults",
                "revision": 0,
                "configuration": payload,
                "engines": self.engines(),
            }
        try:
            payload = self._validate(record["payload"])
        except (TypeError, ValueError):
            raw = record["payload"] if isinstance(record["payload"], dict) else {}
            available = {plugin.engine_id for plugin in self.registry if plugin.enabled}
            retained = [engine for engine in raw.get("search_engines", []) if engine in available]
            if not retained:
                payload = self._default_payload()
            else:
                payload = self._validate({**self._default_payload(), **raw, "search_engines": retained})
        return {
            "source": "persisted",
            "revision": record["revision"],
            "configuration": payload,
            "engines": self.engines(),
            "updated_at": record["updated_at"],
        }

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated = self._validate(payload)
        record = self.store.save_configuration(validated)
        return {
            "source": "persisted",
            "revision": record["revision"],
            "configuration": validated,
            "engines": self.engines(),
            "updated_at": record["updated_at"],
        }

    def reset(self) -> dict[str, Any]:
        self.store.reset_configuration()
        return self.get()

    def resolve_options(self, options: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
        explicit = dict(options or {})
        current = self.get()
        if "search_engines" in explicit:
            selected = self._validate({**current["configuration"], "search_engines": explicit["search_engines"]})
            revision = current["revision"]
        else:
            selected = dict(current["configuration"])
            revision = current["revision"]
        selected.update({key: value for key, value in explicit.items() if key != "search_engines"})
        validated = self._validate(selected)
        validated.update({key: value for key, value in explicit.items() if key not in validated})
        return validated, {"source": "explicit" if "search_engines" in explicit else current["source"], "revision": revision}
