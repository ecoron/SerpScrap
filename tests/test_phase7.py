from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from selenium.common.exceptions import ElementNotInteractableException

from serpscrap.diagnostics import DiagnosticArtifactStore, ProgressCoordinator
from serpscrap.plugins.searchengines.base import BrowserInteraction, EnginePage, GenericHtmlPlugin, _clean_text
from serpscrap.plugins.searchengines.browser_flow import BrowserFlowError, HomepageSearchFlow
from serpscrap.plugins.searchengines.registry import default_registry


HTML = """
<html><body><div id="b_results"><li class="b_algo"><h2><a href="https://example.test/a">Result</a></h2><p>Snippet</p></li></div></body></html>
"""


class DemoPlugin(GenericHtmlPlugin):
    engine_id = "demo"
    search_url = "https://example.test/search?q={query}"
    browser_interaction = BrowserInteraction(
        homepage_url="https://example.test/",
        search_input_selectors=("input[name='q']",),
        submit_selectors=("button[type='submit']",),
        serp_ready_selectors=("#b_results",),
        organic_card_selectors=("li.b_algo",),
    )
    card_selectors = ("li.b_algo",)

    def _build_url(self, query: str, page: int, country_code: str) -> str:
        return self.search_url.format(query=query)


class FakeElement:
    def __init__(self, *, value: str = "") -> None:
        self.value = value
        self.clicks = 0
        self.keys: list[Any] = []

    def is_displayed(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    def clear(self) -> None:
        self.value = ""

    def send_keys(self, value: Any) -> None:
        self.keys.append(value)
        if isinstance(value, str):
            self.value = value

    def get_attribute(self, name: str) -> str | None:
        return self.value if name == "value" else None

    def click(self) -> None:
        self.clicks += 1


class FakeDriver:
    def __init__(self, *, ready: bool = True) -> None:
        self.input = FakeElement()
        self.submit = FakeElement()
        self.current_url = "about:blank"
        self.page_source = HTML if ready else "<html><body></body></html>"
        self.get_calls: list[str] = []

    def get(self, url: str) -> None:
        self.get_calls.append(url)
        self.current_url = url

    def find_elements(self, by: str, selector: str) -> list[FakeElement]:
        if selector == "input[name='q']":
            return [self.input]
        if selector == "button[type='submit']":
            return [self.submit]
        if selector == "#b_results" and "b_results" in self.page_source:
            return [FakeElement()]
        return []


def test_homepage_flow_enters_submits_waits_and_returns_page():
    driver = FakeDriver()
    page = HomepageSearchFlow(timeout=1).capture(driver, DemoPlugin(), "phase seven", "DE", 1, "normal")

    assert isinstance(page, EnginePage)
    assert driver.get_calls == ["https://example.test/"]
    assert driver.input.value == "phase seven"
    assert driver.submit.clicks == 1


def test_homepage_flow_uses_provider_pagination_for_later_pages():
    driver = FakeDriver()
    page = HomepageSearchFlow(timeout=1).capture(driver, DemoPlugin(), "phase seven", "DE", 2, "normal")

    assert page.page == 2
    assert driver.get_calls == ["https://example.test/", "https://example.test/search?q=phase seven"]


def test_homepage_flow_reports_navigation_state_when_serp_never_ready():
    driver = FakeDriver(ready=False)
    with pytest.raises(BrowserFlowError) as error:
        HomepageSearchFlow(timeout=0.01).capture(driver, DemoPlugin(), "query", "DE", 1, "normal")
    assert error.value.category == "navigation_state"


def test_homepage_flow_falls_back_to_enter_when_submit_control_is_missing():
    driver = FakeDriver()
    driver.page_source = HTML
    original = driver.find_elements

    def without_submit(by: str, selector: str) -> list[FakeElement]:
        if selector == "button[type='submit']":
            return []
        return original(by, selector)

    driver.find_elements = without_submit  # type: ignore[method-assign]
    HomepageSearchFlow(timeout=1).capture(driver, DemoPlugin(), "query", "DE", 1, "normal")

    assert driver.input.keys


def test_homepage_flow_retries_when_first_search_field_is_not_interactable():
    class TemporarilyHiddenField(FakeElement):
        def clear(self) -> None:
            raise ElementNotInteractableException("transitioning field")

    driver = FakeDriver()
    fallback = driver.input
    original = driver.find_elements

    def with_transitioning_field(by: str, selector: str) -> list[FakeElement]:
        if selector == "input[name='q']":
            return [TemporarilyHiddenField(), fallback]
        return original(by, selector)

    driver.find_elements = with_transitioning_field  # type: ignore[method-assign]
    HomepageSearchFlow(timeout=1).capture(driver, DemoPlugin(), "query", "DE", 1, "normal")

    assert fallback.value == "query"


def test_homepage_flow_dismisses_declared_overlay_before_query_entry():
    driver = FakeDriver()
    overlay_close = FakeElement()
    original = driver.find_elements

    def with_overlay(by: str, selector: str) -> list[FakeElement]:
        if selector == ".overlay-close":
            return [overlay_close]
        return original(by, selector)

    driver.find_elements = with_overlay  # type: ignore[method-assign]
    plugin = DemoPlugin()
    contract = plugin.browser_interaction
    assert contract is not None
    plugin.browser_interaction = BrowserInteraction(
        contract.homepage_url,
        contract.search_input_selectors,
        contract.submit_selectors,
        contract.serp_ready_selectors,
        contract.organic_card_selectors,
        dismiss_selectors=(".overlay-close",),
    )

    HomepageSearchFlow(timeout=1).capture(driver, plugin, "query", "DE", 1, "normal")

    assert overlay_close.clicks == 1


def test_consent_action_uses_privacy_preserving_button_label():
    driver = FakeDriver()
    reject = FakeElement()
    reject.text = "Alle ablehnen"  # type: ignore[attr-defined]
    original = driver.find_elements

    def with_consent(by: str, selector: str) -> list[FakeElement]:
        if selector == "div[role='dialog'][aria-modal='true'] button":
            return [reject]
        return original(by, selector)

    driver.find_elements = with_consent  # type: ignore[method-assign]
    plugin = DemoPlugin()
    contract = plugin.browser_interaction
    assert contract is not None
    plugin.browser_interaction = BrowserInteraction(
        contract.homepage_url,
        contract.search_input_selectors,
        contract.submit_selectors,
        contract.serp_ready_selectors,
        contract.organic_card_selectors,
        consent_button_selectors=("div[role='dialog'][aria-modal='true'] button",),
    )

    assert HomepageSearchFlow()._apply_consent(driver, plugin, "necessary") is True
    assert reject.clicks == 1


def test_clean_text_repairs_common_utf8_mojibake():
    assert _clean_text("Solarenergie erklÃ¤rt â€“ kompakt") == "Solarenergie erklärt – kompakt"


def test_selenium_page_capture_always_quits_driver(monkeypatch: pytest.MonkeyPatch):
    from serpscrap.plugins.searchengines.multi import SeleniumPageCapture

    driver = FakeDriver()
    driver.quit_calls = 0
    original_quit = getattr(driver, "quit", None)

    def quit_driver() -> None:
        driver.quit_calls += 1
        if original_quit:
            original_quit()

    driver.quit = quit_driver  # type: ignore[attr-defined]
    monkeypatch.setattr(
        "scrapcore.scraper.browser.ChromeDriverFactory.from_config",
        lambda config: type("Factory", (), {"create": lambda self: driver})(),
    )

    SeleniumPageCapture()(DemoPlugin(), "query", "DE", 1, {"wait_timeout": 1})
    assert driver.quit_calls == 1


def test_all_registered_engines_expose_phase7_browser_contracts():
    plugins = tuple(default_registry())
    assert len(plugins) == 11
    assert all(plugin.browser_interaction is not None for plugin in plugins)
    assert all(plugin.browser_interaction.homepage_url.startswith("https://") for plugin in plugins)
    assert all(plugin.metadata()["browser_interaction"]["observed_at"] == "2026-08-02" for plugin in plugins)


def test_progress_coordinator_orders_events_and_counts_terminal_jobs():
    events = []

    class Sink:
        def emit(self, event):
            events.append(event)

    coordinator = ProgressCoordinator("run-1", 2, Sink())
    coordinator.emit(correlation_id="a", engine="bing", page=1, state="started")
    coordinator.emit(correlation_id="a", engine="bing", page=1, state="completed", terminal=True)
    coordinator.emit(correlation_id="b", engine="google", page=1, state="failed", terminal=True)

    assert [event.sequence for event in events] == [1, 2, 3]
    assert [event.completed_jobs for event in events] == [0, 1, 2]
    assert coordinator.completed_jobs == 2


def test_diagnostic_artifact_store_redacts_query_and_sensitive_values(tmp_path):
    store = DiagnosticArtifactStore(tmp_path, "run-1", max_bytes_per_file=10000)
    path = store.capture(
        html='<form action="/search?q=secret+term"><input name="csrf" value="token123">secret term</form>',
        query="secret term",
        engine="brave",
        page=1,
        state="homepage_ready",
        correlation_id="corr-1",
        url="https://search.brave.com/search?q=secret+term",
    )

    assert path is not None
    content = Path(path).read_text(encoding="utf-8")
    assert "secret term" not in content
    assert "token123" not in content
    manifest = (tmp_path / "run-1" / "manifest.json").read_text(encoding="utf-8")
    assert "secret term" not in manifest
    assert "q=" not in manifest


def test_diagnostic_artifact_store_enforces_file_limit_and_manifest(tmp_path):
    store = DiagnosticArtifactStore(tmp_path, "run-2", max_bytes_per_file=10)
    path = store.capture(
        html="01234567890",
        query="query",
        engine="ecosia",
        page=1,
        state="failure",
        correlation_id="corr-2",
    )

    assert path is None
    manifest = (tmp_path / "run-2" / "manifest.json").read_text(encoding="utf-8")
    assert "max_bytes_per_file" in manifest


@pytest.mark.parametrize(
    ("engine", "fixture", "expected_results"),
    [
        ("bing", "bing/valid_serp_hidden_markers.html", 1),
        ("yandex", "yandex/valid_serp_hidden_markers.html", 1),
    ],
)
def test_visible_serp_is_not_rejected_by_hidden_marker_text(engine, fixture, expected_results):
    plugin = default_registry().get(engine)
    html = Path("tests/fixtures/searchengines").joinpath(fixture).read_text(encoding="utf-8")
    visible = plugin.visible_text_from_html(html)

    assert plugin.classify(f"https://{engine}.example/search", html, visible_text=visible) is None
    assert len(plugin.parse(html, query="fixture", page=1, search_type="normal")) == expected_results


@pytest.mark.parametrize(
    ("engine", "fixture"),
    [
        ("brave", "brave/valid_serp_current.html"),
        ("mojeek", "mojeek/valid_serp_current.html"),
        ("swisscows", "swisscows/valid_serp_current.html"),
        ("startpage", "startpage/valid_serp_current.html"),
    ],
)
def test_current_artifact_selectors_parse_organic_cards(engine, fixture):
    plugin = default_registry().get(engine)
    html = Path("tests/fixtures/searchengines").joinpath(fixture).read_text(encoding="utf-8")

    parsed = plugin.parse(html, query="fixture", page=1, search_type="normal")

    assert len(parsed) == 1
    assert parsed[0].url == f"https://example.test/{engine}"


def test_qwant_http403_is_classified_as_blocked():
    plugin = default_registry().get("qwant")
    html = Path("tests/fixtures/searchengines/qwant/blocked_http403.html").read_text(encoding="utf-8")

    assert plugin.classify(
        "https://www.qwant.com/",
        html,
        visible_text=plugin.visible_text_from_html(html),
    ) == "blocked"


def test_brave_current_homepage_searchbox_is_documented():
    plugin = default_registry().get("brave")
    html = Path("tests/fixtures/searchengines/brave/homepage_searchbox.html").read_text(encoding="utf-8")

    assert "textarea#searchbox" in plugin.browser_interaction.search_input_selectors
    assert plugin.visible_text_from_html(html) == ""


def test_homepage_challenge_and_consent_are_classified_before_input_lookup():
    registry = default_registry()
    brave = registry.get("brave")
    ecosia = registry.get("ecosia")
    brave_html = Path("tests/fixtures/searchengines/brave/blocked_homepage.html").read_text(encoding="utf-8")
    ecosia_html = Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(encoding="utf-8")

    assert brave.classify_homepage(
        "https://search.brave.com/", html=brave_html,
        visible_text=brave.visible_text_from_html(brave_html)
    ) == "blocked"
    assert ecosia.classify_homepage(
        "https://www.ecosia.org/", html=ecosia_html,
        visible_text=ecosia.visible_text_from_html(ecosia_html)
    ) == "consent_required"


def test_rate_limit_precedes_generic_consent_text():
    plugin = default_registry().get("swisscows")
    html = Path("tests/fixtures/searchengines/swisscows/rate_limited.html").read_text(encoding="utf-8")

    assert plugin.classify("https://swisscows.com/en/web", html, visible_text=plugin.visible_text_from_html(html)) == "rate_limited"


def test_empty_state_is_distinguished_from_malformed_zero_card_page():
    plugin = default_registry().get("mojeek")
    empty_html = "<html><body><main><h1>No results found</h1></main></body></html>"
    malformed_html = "<html><body><main><h1>Search</h1></main></body></html>"

    assert plugin.classify_empty("https://www.mojeek.com/search", empty_html)
    assert not plugin.classify_empty("https://www.mojeek.com/search", malformed_html)


def test_post_submit_route_without_serp_is_typed_as_malformed():
    class NavigatingSubmit(FakeElement):
        def __init__(self, driver):
            super().__init__()
            self.driver = driver

        def click(self) -> None:
            super().click()
            self.driver.current_url = "https://example.test/search"
            self.driver.page_source = "<html><body><main><h1>Challenge</h1></main></body></html>"

    class NavigatingDriver(FakeDriver):
        def __init__(self):
            super().__init__(ready=False)
            self.submit = NavigatingSubmit(self)

    driver = NavigatingDriver()
    with pytest.raises(BrowserFlowError) as error:
        HomepageSearchFlow(timeout=0.01).capture(driver, DemoPlugin(), "query", "DE", 1, "normal")

    assert error.value.category == "malformed"
    assert error.value.url == "https://example.test/search"


def test_multi_engine_zero_results_are_failures():
    from serpscrap.models import SearchRequest
    from serpscrap.plugins.searchengines.multi import MultiEngineRunner

    def empty_capture(plugin, query, country_code, page, config):
        return EnginePage(
            url=plugin.build_url(query, page, country_code, "normal"),
            html="<html><body><h1>No results found</h1></body></html>",
            query=query,
            engine=plugin.engine_id,
            country_code=country_code,
            page=page,
            visible_text="No results found",
        )

    report = MultiEngineRunner(capture=empty_capture).execute(
        SearchRequest.create("fixture", search_engines=["mojeek"], num_workers=1)
    )

    assert report.results == []
    assert report.failures[0].category == "empty"
    assert report.failures[0].to_dict()["correlation_id"]
    assert report.report_metadata["outcome_counts"] == {"empty": 1}


def test_retryable_engine_categories_are_validated():
    from serpscrap.exceptions import ConfigurationError
    from serpscrap.models import SearchRequest

    with pytest.raises(ConfigurationError, match="unsupported retryable engine category"):
        SearchRequest.create(
            "fixture",
            search_engines=["mojeek"],
            retryable_engine_categories=["captcha_bypass"],
        )


def test_failure_records_keep_engine_job_correlation_id():
    from serpscrap.models import SearchRequest
    from serpscrap.plugins.searchengines.browser_flow import BrowserFlowError
    from serpscrap.plugins.searchengines.multi import MultiEngineRunner

    def failing_capture(plugin, query, country_code, page, config):
        raise BrowserFlowError("blocked", "fixture block", url=plugin.build_url(query, page, country_code, "normal"))

    report = MultiEngineRunner(capture=failing_capture).execute(
        SearchRequest.create("fixture", search_engines=["bing"], num_workers=1)
    )

    assert report.failures[0].correlation_id
