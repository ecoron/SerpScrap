from pathlib import Path

import pytest

from serpscrap.plugins.searchengines.base import BrowserInteraction, GenericHtmlPlugin
from serpscrap.plugins.searchengines.browser_flow import BrowserFlowError, HomepageSearchFlow
from serpscrap.plugins.searchengines.registry import default_registry


class _ConsentElement:
    def __init__(self, driver, text: str, displayed: bool = True):
        self.driver = driver
        self.text = text
        self.displayed = displayed
        self.clicks = 0

    def is_displayed(self):
        return self.displayed

    def is_enabled(self):
        return True

    def get_attribute(self, name):
        return self.text if name == "aria-label" else None

    def click(self):
        self.clicks += 1
        self.driver.overlay = False
        self.driver.page_source = "<html><body><input name='q'></body></html>"


class _ConsentDriver:
    def __init__(self, html: str):
        self.page_source = html
        self.current_url = "https://www.ecosia.org/"
        self.overlay = True
        self.execute_script_called = False

    def find_elements(self, _by, selector):
        if self.overlay and ("didomi-host" in selector or "didomi-notice-disagree" in selector):
            elements = [_ConsentElement(self, "Alle annehmen")]
            if "Nicht essenzielle Cookies ablehnen" in self.page_source:
                elements.append(_ConsentElement(self, "Nicht essenzielle Cookies ablehnen"))
            return elements
        return []

    def execute_script(self, *_args):
        self.execute_script_called = True
        raise AssertionError("provider JavaScript shortcuts must not be used")


class _ConsentPlugin(GenericHtmlPlugin):
    engine_id = "ecosia"
    search_url = "https://www.ecosia.org/search?q={query}"
    browser_interaction = BrowserInteraction(
        homepage_url="https://www.ecosia.org/",
        search_input_selectors=("input[name='q']",),
        submit_selectors=("button[type='submit']",),
        serp_ready_selectors=("main",),
        organic_card_selectors=("article",),
        consent_button_selectors=("#didomi-host button",),
    )

    def _build_url(self, query, page, country_code):
        return self.search_url.format(query=query)


class _PostConsentFlowDriver(_ConsentDriver):
    """Minimal driver that retains hidden consent markup after dismissal."""

    def __init__(self, html: str, *, blocked_after_submit: bool = False):
        super().__init__(html)
        self.blocked_after_submit = blocked_after_submit
        self.body_text = "Consent dialog"
        self.input = _FlowElement(self, "")
        self.submit = _FlowElement(self, "Submit")

    def get(self, url):
        self.current_url = url

    def find_elements(self, by, selector):
        if self.overlay and ("didomi-host" in selector or "didomi-notice-disagree" in selector):
            return [_FlowElement(self, "Nicht essenzielle Cookies ablehnen")]
        if selector == "input[name='q']":
            return [self.input]
        if selector == "button[type='submit']":
            return [self.submit]
        if selector == "main" and "results" in self.page_source:
            return [_FlowElement(self, "results")]
        return []

    def find_element(self, _by, selector):
        if selector == "body":
            return type("Body", (), {"text": self.body_text})()
        raise AttributeError(selector)


class _FlowElement(_ConsentElement):
    def clear(self):
        self.text = ""

    def send_keys(self, value):
        if isinstance(value, str):
            self.text = value

    def get_attribute(self, name):
        if name == "value":
            return self.text
        return super().get_attribute(name)

    def click(self):
        self.clicks += 1
        if self.text == "Submit":
            if self.driver.blocked_after_submit:
                self.driver.current_url = "https://www.ecosia.org/challenge"
                self.driver.body_text = "Verify you are human"
                self.driver.page_source = "<html><body>Verify you are human</body></html>"
            else:
                self.driver.current_url = "https://www.ecosia.org/search?q=query"
                self.driver.body_text = "results"
                self.driver.page_source = "<html><body><main id='results'>results</main></body></html>"
            return
        self.driver.overlay = False
        self.driver.body_text = "Search page"
        self.driver.page_source = (
            "<html><body><div id='didomi-host' hidden>"
            "<button>Reject all</button></div><input name='q'>"
            "<button type='submit'>Search</button></body></html>"
        )


def test_google_fixture_and_registry_use_semantic_consent_contract():
    registry = default_registry()
    plugin = registry.get("google")
    fixture = Path("tests/fixtures/searchengines/google/consent_homepage.html").read_text(
        encoding="utf-8"
    )

    assert plugin.classify_homepage(
        "https://www.google.com/",
        html=fixture,
        visible_text=plugin.visible_text_from_html(fixture),
    ) == "consent_required"
    assert "div.GzLjMd button#W0wltc" in plugin.browser_interaction.consent_button_selectors
    assert "reject all" in plugin.browser_interaction.consent_reject_labels
    assert plugin.classify("https://www.google.com/sorry/index", "") == "blocked"


def test_ecosia_consent_uses_visible_label_and_verifies_overlay_clear():
    driver = _ConsentDriver(
        Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(
            encoding="utf-8"
        )
    )
    events = []
    assert HomepageSearchFlow(timeout=0.1)._apply_consent(
        driver,
        _ConsentPlugin(),
        "necessary",
        progress=lambda state, **_: events.append(state),
    )
    assert events == ["consent_action_started", "consent_cleared"]
    assert not driver.overlay
    assert not driver.execute_script_called
    interaction = default_registry().get("ecosia").browser_interaction
    assert interaction is not None
    assert "#didomi-notice-disagree-button" in interaction.consent_button_selectors


def test_ecosia_cloudflare_challenge_is_classified_as_blocked():
    plugin = default_registry().get("ecosia")
    interaction = plugin.browser_interaction

    html = "<html><body><h1>Confirm you're not a robot</h1><script src='/cdn-cgi/challenge-platform/x'></script></body></html>"

    assert plugin.classify("https://www.ecosia.org/search", html) == "blocked"
    assert interaction is not None
    assert "nicht essenzielle cookies ablehnen" in interaction.consent_reject_labels


def test_unmatched_consent_does_not_report_success():
    driver = _ConsentDriver(
        "<html><body><div id='didomi-host'><button>Accept all</button></div></body></html>"
    )
    assert not HomepageSearchFlow(timeout=0.01)._apply_consent(
        driver, _ConsentPlugin(), "necessary"
    )


def test_hidden_consent_node_after_click_is_not_treated_as_active_overlay():
    class HiddenDialogDriver(_ConsentDriver):
        def find_elements(self, by, selector):
            if "didomi-host" in selector and not self.overlay:
                return [_ConsentElement(self, "Reject all", displayed=False)]
            return super().find_elements(by, selector)

        def find_element(self, _by, selector):
            if selector == "body":
                return type("Body", (), {"text": ""})()
            raise AttributeError(selector)

    driver = HiddenDialogDriver(
        Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(
            encoding="utf-8"
        )
    )
    assert HomepageSearchFlow(timeout=0.1)._apply_consent(
        driver, _ConsentPlugin(), "necessary"
    )


def test_capture_continues_after_consent_when_dialog_markup_remains_hidden():
    driver = _PostConsentFlowDriver(
        Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(
            encoding="utf-8"
        )
    )

    page = HomepageSearchFlow(timeout=0.1).capture(
        driver, _ConsentPlugin(), "query", "DE", 1, "normal"
    )

    assert page.url == "https://www.ecosia.org/search?q=query"
    assert driver.input.text == "query"
    assert driver.submit.clicks == 1


def test_capture_applies_bounded_interaction_settle_delay(monkeypatch):
    driver = _PostConsentFlowDriver(
        Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(
            encoding="utf-8"
        )
    )
    delays = []
    monkeypatch.setattr("serpscrap.plugins.searchengines.browser_flow.time.sleep", delays.append)

    HomepageSearchFlow(timeout=0.1).capture(
        driver,
        _ConsentPlugin(),
        "query",
        "DE",
        1,
        "normal",
        interaction_settle_delay=0.35,
    )

    assert delays == [0.35]


def test_capture_rejects_unbounded_interaction_settle_delay():
    driver = _PostConsentFlowDriver(
        Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(
            encoding="utf-8"
        )
    )

    with pytest.raises(BrowserFlowError, match="between 0 and 5"):
        HomepageSearchFlow(timeout=0.1).capture(
            driver,
            _ConsentPlugin(),
            "query",
            "DE",
            1,
            "normal",
            interaction_settle_delay=6,
        )


def test_capture_preserves_blocked_outcome_after_consent_is_cleared():
    driver = _PostConsentFlowDriver(
        Path("tests/fixtures/searchengines/ecosia/consent_homepage.html").read_text(
            encoding="utf-8"
        ),
        blocked_after_submit=True,
    )

    with pytest.raises(BrowserFlowError) as error:
        HomepageSearchFlow(timeout=0.1).capture(
            driver, _ConsentPlugin(), "query", "DE", 1, "normal"
        )

    assert error.value.category == "blocked"
