#!/usr/bin/python3
from serpscrap.config import Config
from serpscrap.exceptions import ConfigurationError, SerpScrapError
from serpscrap.models import FailureRecord, SearchReport, SearchRequest
from serpscrap.output import JsonOutputError, JsonResultWriter
from serpscrap.serpscrap import SerpScrap
from serpscrap.topic_plugins import (
    AllegroShoppingPlugin,
    AnsaNewsPlugin,
    DeutscheWelleNewsPlugin,
    EtsyShoppingPlugin,
    EuronewsNewsPlugin,
    France24NewsPlugin,
    FruugoShoppingPlugin,
    GuardianNewsPlugin,
    KauflandShoppingPlugin,
    LeMondeNewsPlugin,
    NewsSourcePlugin,
    SearchTopicPlugin,
    ShoppingSourcePlugin,
)
from serpscrap.topic_registry import TopicPluginRegistry
from serpscrap.topic_service import TopicService, default_topic_registry
from serpscrap.topics import TopicCapabilities, TopicPlugin, TopicReport, TopicRequest, TopicResult
from serpscrap.urlscrape import UrlScrape

__all__ = [
    "Config",
    "ConfigurationError",
    "FailureRecord",
    "JsonOutputError",
    "JsonResultWriter",
    "SearchReport",
    "SearchRequest",
    "SerpScrap",
    "SerpScrapError",
    "UrlScrape",
    "TopicCapabilities",
    "TopicPlugin",
    "TopicPluginRegistry",
    "TopicReport",
    "TopicRequest",
    "TopicResult",
    "TopicService",
    "default_topic_registry",
    "NewsSourcePlugin",
    "AnsaNewsPlugin",
    "DeutscheWelleNewsPlugin",
    "EuronewsNewsPlugin",
    "France24NewsPlugin",
    "GuardianNewsPlugin",
    "LeMondeNewsPlugin",
    "SearchTopicPlugin",
    "ShoppingSourcePlugin",
    "FruugoShoppingPlugin",
    "KauflandShoppingPlugin",
    "AllegroShoppingPlugin",
    "EtsyShoppingPlugin",
]
