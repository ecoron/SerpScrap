"""Standardized search-engine plugins and multi-engine result fusion."""

from serpscrap.plugins.searchengines.base import (
    BrowserInteraction,
    EnginePage,
    EngineResult,
    SearchEnginePlugin,
)
from serpscrap.plugins.searchengines.fusion import ResultFusion
from serpscrap.plugins.searchengines.registry import SearchEngineRegistry, default_registry

__all__ = [
    "EnginePage",
    "EngineResult",
    "BrowserInteraction",
    "ResultFusion",
    "SearchEnginePlugin",
    "SearchEngineRegistry",
    "default_registry",
]
