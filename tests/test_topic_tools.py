from datetime import timezone

import pytest

from serpscrap.history_store import SearchHistoryStore
from serpscrap.mcp_server import TOOLS
from serpscrap.topic_plugins import (
    AllegroShoppingPlugin,
    AnsaNewsPlugin,
    BilligerShoppingPlugin,
    DeutscheWelleNewsPlugin,
    EtsyShoppingPlugin,
    EuronewsNewsPlugin,
    France24NewsPlugin,
    FruugoShoppingPlugin,
    GeizhalsShoppingPlugin,
    GuardianNewsPlugin,
    IdealoShoppingPlugin,
    KauflandShoppingPlugin,
    LeMondeNewsPlugin,
    NewsSourcePlugin,
    ShoppingSourcePlugin,
)
from serpscrap.topic_registry import TopicPluginRegistry
from serpscrap.topic_service import TopicBrowserError, TopicBrowserTransport, TopicService
from serpscrap.topics import TopicRequest, canonical_url, deduplicate

RSS = """<rss><channel>
<item><title>AI Durchbruch</title><link>https://news.example/a?utm_source=x</link>
<description>Neue Forschung</description><pubDate>Mon, 10 Aug 2026 12:00:00 GMT</pubDate><source>Example News</source></item>
<item><title>AI Durchbruch</title><link>https://news.example/a?utm_medium=y</link>
<pubDate>Mon, 10 Aug 2026 12:00:00 GMT</pubDate></item>
</channel></rss>"""


def test_request_relative_since_and_validation():
    request = TopicRequest.create(" KI ", topic="news", since="24h", country="de", language="DE")
    assert request.query == "KI"
    assert request.country == "DE"
    assert request.language == "de"
    assert request.since.tzinfo == timezone.utc
    with pytest.raises(ValueError):
        TopicRequest.create("x", topic="news", since="2026-08-11", until="2026-08-10")


def test_registry_validates_and_filters():
    registry = TopicPluginRegistry((NewsSourcePlugin(), ShoppingSourcePlugin()))
    assert [item.topic_id for item in registry.find(topic="news", transport="feed")] == ["news"]
    assert {item["topic_id"] for item in registry.metadata()} == {"news", "shopping"}


def test_news_feed_parsing_preserves_metadata_and_filters_duplicates():
    plugin = NewsSourcePlugin()
    request = TopicRequest.create("ai", topic="news")
    rows = [plugin.normalize(row) for row in plugin.parse(RSS, request=request, page=1)]
    assert rows[0].published_at is not None
    assert rows[0].source == "Example News"
    assert rows[0].raw_url.endswith("utm_source=x")
    assert len(deduplicate(rows)) == 1
    assert canonical_url(rows[0].url) == "https://news.example/a"


def test_news_source_id_does_not_get_used_as_feed_url():
    plugin = NewsSourcePlugin()
    request = TopicRequest.create("eu policy", topic="news", sources=("news", "ansa"))
    assert plugin.build_url(request, page=1) == "https://news.google.com/rss/search?q=eu+policy"


def test_news_source_accepts_explicit_custom_feed_url():
    plugin = NewsSourcePlugin()
    request = TopicRequest.create(
        "eu policy", topic="news", sources=("news", "https://example.test/feed.xml")
    )
    assert plugin.build_url(request, page=1) == "https://example.test/feed.xml"


def test_shopping_parser_extracts_locale_independent_price_fields():
    payload = '<div><a href="https://shop.example/p">Kopfhörer</a> 129,99 EUR auf Lager</div>'
    rows = ShoppingSourcePlugin().parse(
        payload, request=TopicRequest.create("headphones", topic="shopping"), page=1
    )
    assert rows[0].extras["price"] == "129,99 EUR"
    assert rows[0].extras["currency"] == "EUR"
    assert rows[0].extras["availability"] == "in_stock"
    assert rows[0].snippet


def test_shopping_parser_prefers_card_meta_description():
    payload = "<article><a href='https://shop.example/p'><h2>Headphones</h2></a><meta name='description' content='Wireless over-ear headphones with noise cancellation.'></article>"
    rows = ShoppingSourcePlugin().parse(
        payload, request=TopicRequest.create("headphones", topic="shopping"), page=1
    )
    assert rows[0].snippet == "Wireless over-ear headphones with noise cancellation."


def test_open_shopping_sources_build_query_urls():
    request = TopicRequest.create("noise cancelling headphones", topic="shopping")
    assert "fs=noise+cancelling+headphones" in GeizhalsShoppingPlugin().build_url(request, page=1)
    assert "q=noise+cancelling+headphones" in IdealoShoppingPlugin().build_url(request, page=1)
    assert "searchTerm=noise+cancelling+headphones" in BilligerShoppingPlugin().build_url(request, page=1)


def test_european_news_sources_expose_stable_feed_urls():
    request = TopicRequest.create("eu policy", topic="news", language="en")
    sources = (AnsaNewsPlugin(), EuronewsNewsPlugin(), France24NewsPlugin(), LeMondeNewsPlugin(), GuardianNewsPlugin())
    assert {source.source_id for source in sources} == {"ansa", "euronews", "france24", "lemonde", "guardian"}
    assert all(source.build_url(request, page=1).startswith("https://") for source in sources)
    assert DeutscheWelleNewsPlugin().build_url(TopicRequest.create("KI", topic="news", language="de"), page=1).startswith("https://")


def test_default_news_registry_contains_named_sources():
    from serpscrap.topic_service import default_topic_registry

    assert {item["source_id"] for item in default_topic_registry().metadata()} >= {
        "news", "ansa", "dw", "euronews", "france24", "lemonde", "guardian"
    }


def test_open_shopping_source_selection_is_independent():
    service = TopicService(fetcher=lambda url: "<article><a href='https://shop.example/p'>Product</a> 12,99 EUR</article>")
    request = TopicRequest.create("headphones", topic="shopping", sources=("geizhals",))
    report = service.execute(request)
    assert set(report.source_status) == {"geizhals"}
    assert report.source_status["geizhals"]["status"] == "ok"


def test_european_marketplace_sources_build_localized_public_urls():
    request = TopicRequest.create("handmade lamp", topic="shopping", country="DE")
    assert "fruugo.de" in FruugoShoppingPlugin().build_url(request, page=1)
    assert "kaufland.de" in KauflandShoppingPlugin().build_url(request, page=1)
    assert "allegro.pl" in AllegroShoppingPlugin().build_url(request, page=1)
    assert "etsy.com/search?q=handmade+lamp" in EtsyShoppingPlugin().build_url(request, page=1)


def test_topic_service_uses_shared_report_and_source_status():
    service = TopicService(fetcher=lambda url: RSS)
    report = service.execute(TopicRequest.create("ai", topic="news"))
    assert report.to_dict()["schema_version"] == 1
    assert report.source_status["news"]["status"] == "ok"
    assert len(report.results) == 1


def test_shopping_sources_use_shared_browser_transport():
    assert GeizhalsShoppingPlugin.capabilities.transport == "browser"
    assert IdealoShoppingPlugin.capabilities.transport == "browser"
    assert BilligerShoppingPlugin.capabilities.transport == "browser"


def test_topic_browser_transport_classifies_provider_blocks():
    class Driver:
        current_url = "https://shop.example/search"
        page_source = "<html><body>Access denied</body></html>"

        def get(self, _url):
            pass

        def find_element(self, *_args):
            return type("Body", (), {"text": "Access denied"})()

        def quit(self):
            pass

    class Factory:
        def create(self):
            return Driver()

    transport = TopicBrowserTransport({"request_delay_min": 0, "request_delay_max": 0, "block_threshold": 2})
    transport.driver_factory = Factory()
    with pytest.raises(TopicBrowserError, match="rejected"):
        transport.fetch("https://shop.example/search")


def test_mcp_exposes_topic_tools_with_strict_schemas():
    tools = {item["name"]: item for item in TOOLS}
    assert {"list_topics", "topic_search"}.issubset(tools)
    assert tools["topic_search"]["inputSchema"]["additionalProperties"] is False


def test_topic_report_can_be_persisted_in_shared_history(tmp_path):
    store = SearchHistoryStore(f"sqlite:///{tmp_path / 'history.db'}")
    request = TopicRequest.create("headphones", topic="shopping")
    report = TopicService(fetcher=lambda url: "<article><a href='https://shop.example/p'>Product</a> 12,99 EUR</article>").execute(request)
    store.create_run("topic-run", request.query, {"topic": request.topic})
    store.store_topic_report("topic-run", report)
    run = store.get_run("topic-run")
    assert run["status"] == "completed"
    assert run["result_count"] == 1
    result = store.list_results(run_id="topic-run")[0]
    assert result["result_kind"] == "shopping"
    assert result["search_engine"] == "topic:Geizhals"
    store.close()
