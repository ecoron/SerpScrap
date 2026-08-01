"""Public exceptions without infrastructure dependencies."""


class SerpScrapError(Exception):
    """Base class for public SerpScrap failures."""


class ConfigurationError(SerpScrapError):
    """Raised when a search request or setting is invalid."""
