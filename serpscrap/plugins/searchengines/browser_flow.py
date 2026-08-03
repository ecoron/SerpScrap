"""Safe, fixture-testable homepage-to-SERP browser interaction."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from selenium.common.exceptions import (
    ElementNotInteractableException,
    InvalidElementStateException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from serpscrap.plugins.searchengines.base import EnginePage, SearchEnginePlugin


class BrowserFlowError(RuntimeError):
    """A typed failure while driving a search form or waiting for its SERP."""

    def __init__(
        self,
        category: str,
        message: str,
        *,
        url: str | None = None,
        result_count: int | None = None,
    ) -> None:
        super().__init__(f"{category}: {message}")
        self.category = category
        self.url = url
        self.result_count = result_count


class HomepageSearchFlow:
    """Execute one provider's documented homepage search flow."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    @staticmethod
    def _elements(driver: Any, selectors: tuple[str, ...]) -> list[Any]:
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return elements
        return []

    @staticmethod
    def _usable(element: Any) -> bool:
        displayed = getattr(element, "is_displayed", lambda: True)()
        enabled = getattr(element, "is_enabled", lambda: True)()
        return bool(displayed and enabled)

    @staticmethod
    def _visible_text(driver: Any) -> str:
        try:
            return str(driver.find_element(By.TAG_NAME, "body").text or "")
        except (AttributeError, WebDriverException):
            return SearchEnginePlugin.visible_text_from_html(getattr(driver, "page_source", "") or "")

    def _classify(self, driver: Any, plugin: SearchEnginePlugin, *, homepage: bool = False) -> str | None:
        visible_text = self._visible_text(driver)
        if homepage:
            return plugin.classify_homepage(
                getattr(driver, "current_url", ""),
                html=getattr(driver, "page_source", "") or "",
                visible_text=visible_text,
            )
        return plugin.classify(
            getattr(driver, "current_url", ""),
            getattr(driver, "page_source", "") or "",
            visible_text=visible_text,
        )

    def _wait_for_input(self, driver: Any, plugin: SearchEnginePlugin) -> Any:
        def locate(_: Any) -> Any:
            return next(
                (element for element in self._elements(driver, plugin.browser_interaction.search_input_selectors)
                 if self._usable(element)),
                False,
            )

        try:
            return WebDriverWait(driver, self.timeout).until(locate)
        except TimeoutException as exc:
            raise BrowserFlowError(
                "selector_drift", f"search input not available for {plugin.engine_id}",
                url=getattr(driver, "current_url", None),
            ) from exc

    def _enter_query(self, driver: Any, plugin: SearchEnginePlugin, query: str) -> Any:
        """Enter the query into the first usable, actually interactable field.

        A rendered page can expose more than one matching element (Google, for
        example, may retain a hidden/transitioning search control).  Visibility
        alone is not sufficient for Selenium interaction, so each candidate is
        focused and tried independently before reporting selector drift.
        """
        spec = plugin.browser_interaction
        assert spec is not None
        for selector in spec.search_input_selectors:
            for field in driver.find_elements(By.CSS_SELECTOR, selector):
                try:
                    if not self._usable(field):
                        continue
                    field.clear()
                    field.send_keys(query)
                    value = getattr(field, "get_attribute", lambda *_: query)("value")
                    if value in {query, None}:
                        return field
                except (
                    ElementNotInteractableException,
                    InvalidElementStateException,
                    StaleElementReferenceException,
                ):
                    continue
        raise BrowserFlowError(
            "selector_drift",
            f"search input is not interactable for {plugin.engine_id}",
            url=getattr(driver, "current_url", None),
        )

    @staticmethod
    def _dismiss_overlays(driver: Any, plugin: SearchEnginePlugin) -> None:
        spec = plugin.browser_interaction
        assert spec is not None
        for selector in spec.dismiss_selectors:
            for element in driver.find_elements(By.CSS_SELECTOR, selector):
                try:
                    if HomepageSearchFlow._usable(element):
                        element.click()
                        return
                except WebDriverException:
                    continue

    def _apply_consent(
        self,
        driver: Any,
        plugin: SearchEnginePlugin,
        action: str,
        *,
        progress: Callable[..., Any] | None = None,
    ) -> bool:
        spec = plugin.browser_interaction
        assert spec is not None
        if action == "disabled":
            return False
        labels = tuple(label.lower() for label in spec.consent_reject_labels)

        if progress is not None:
            progress("consent_action_started")

        def consent_cleared(_: Any) -> bool:
            current_url = getattr(driver, "current_url", "")
            visible_text = HomepageSearchFlow._visible_text(driver)
            # Do not use raw homepage HTML for post-click verification: Google
            # and consent managers can leave a hidden dialog in the DOM after
            # the visible control has successfully closed it.
            if plugin.classify_homepage(
                current_url,
                html="",
                visible_text=visible_text,
            ) == "consent_required":
                return False
            for selector in plugin.homepage_consent_selectors:
                if any(self._usable(element) for element in driver.find_elements(By.CSS_SELECTOR, selector)):
                    return False
            return True

        def wait_until_cleared() -> bool:
            try:
                WebDriverWait(driver, self.timeout).until(consent_cleared)
            except TimeoutException:
                return False
            return True

        def locate(_: Any) -> Any:
            for selector in spec.consent_button_selectors:
                for element in driver.find_elements(By.CSS_SELECTOR, selector):
                    try:
                        text = " ".join(str(getattr(element, "text", "") or "").lower().split())
                        aria_label = " ".join(
                            str(element.get_attribute("aria-label") or "").lower().split()
                        )
                        semantic_text = f"{text} {aria_label}".strip()
                        semantic_match = any(label in semantic_text for label in labels)
                        if semantic_match and HomepageSearchFlow._usable(element):
                            return element
                    except WebDriverException:
                        continue
            return False

        try:
            element = WebDriverWait(driver, self.timeout).until(locate)
        except (TimeoutException, WebDriverException):
            element = None
            for selector in spec.consent_manage_selectors:
                for manage in driver.find_elements(By.CSS_SELECTOR, selector):
                    try:
                        if HomepageSearchFlow._usable(manage):
                            manage.click()
                            element = WebDriverWait(driver, self.timeout).until(locate)
                            break
                    except (TimeoutException, WebDriverException):
                        continue
                if element is not None:
                    break
            if element is None:
                return False
        try:
            element.click()
        except WebDriverException:
            return False
        if plugin.engine_id == "google" and "consent.google." in str(getattr(driver, "current_url", "")):
            driver.get(spec.homepage_url)
        if not wait_until_cleared():
            return False
        if progress is not None:
            progress("consent_cleared")
        return True

    def _wait_for_serp(self, driver: Any, plugin: SearchEnginePlugin, *, submitted_url: str) -> None:
        def ready(_: Any) -> bool:
            if any(self._classify(driver, plugin) == state
                   for state in ("blocked", "consent_required", "rate_limited")):
                return True
            if plugin.classify_empty(
                getattr(driver, "current_url", ""),
                getattr(driver, "page_source", "") or "",
                visible_text=self._visible_text(driver),
            ):
                return True
            return bool(self._elements(driver, plugin.browser_interaction.serp_ready_selectors))

        try:
            WebDriverWait(driver, self.timeout).until(ready)
        except TimeoutException as exc:
            current_url = getattr(driver, "current_url", None)
            category = "malformed" if current_url and current_url != submitted_url else "navigation_state"
            raise BrowserFlowError(
                category,
                f"post-submit state not recognized for {plugin.engine_id}",
                url=current_url,
            ) from exc
        state = self._classify(driver, plugin)
        if state in {"blocked", "consent_required", "rate_limited"}:
            raise BrowserFlowError(state, f"provider returned {state}", url=driver.current_url)

    def capture(
        self,
        driver: Any,
        plugin: SearchEnginePlugin,
        query: str,
        country_code: str,
        page: int,
        search_type: str,
        *,
        correlation_id: str | None = None,
        progress: Callable[..., Any] | None = None,
        artifact_store: Any | None = None,
        consent_action: str = "necessary",
    ) -> EnginePage:
        spec = plugin.browser_interaction
        if spec is None:
            raise BrowserFlowError("configuration", f"{plugin.engine_id} has no browser contract")
        if search_type != "normal":
            raise BrowserFlowError("unsupported", "homepage flow currently supports normal web search only")
        started = time.monotonic()

        def emit(state: str, *, selector_key: str | None = None, terminal: bool = False, error_category: str | None = None, result_count: int | None = None) -> None:
            artifact_path = None
            if artifact_store is not None and state in {
                "homepage_ready",
                "consent_visible",
                "consent_action_started",
                "consent_cleared",
                "pre_submit",
                "serp_ready",
                "failure",
            }:
                artifact_path = artifact_store.capture(
                    html=getattr(driver, "page_source", "") or "",
                    query=query,
                    engine=plugin.engine_id,
                    page=page,
                    state=state,
                    correlation_id=correlation_id or "unknown",
                    url=getattr(driver, "current_url", None),
                    selector_key=selector_key,
                )
            if progress is not None:
                progress(
                    state,
                    url=getattr(driver, "current_url", None),
                    selector_key=selector_key,
                    artifact_path=artifact_path,
                    elapsed_ms=int((time.monotonic() - started) * 1000),
                    terminal=terminal,
                    error_category=error_category,
                    result_count=result_count,
                )

        try:
            emit("homepage_requested")
            driver.get(spec.homepage_url)
            homepage_state = self._classify(driver, plugin, homepage=True)
            if homepage_state == "consent_required":
                emit("consent_visible")
                if not self._apply_consent(driver, plugin, consent_action, progress=emit):
                    raise BrowserFlowError(
                        "consent_required",
                        f"provider homepage returned consent_required for {plugin.engine_id}",
                        url=getattr(driver, "current_url", None),
                )
                homepage_state = self._classify(driver, plugin, homepage=True)
            elif homepage_state is None:
                emit("consent_not_present")
            if homepage_state in {"blocked", "consent_required", "rate_limited"}:
                raise BrowserFlowError(
                    homepage_state,
                    f"provider homepage returned {homepage_state}",
                    url=getattr(driver, "current_url", None),
                )
            self._wait_for_input(driver, plugin)
            emit("homepage_ready", selector_key=spec.search_input_selectors[0])
            self._dismiss_overlays(driver, plugin)
            field = self._enter_query(driver, plugin, query)
            emit("query_entered")

            submit = next(
                (element for element in self._elements(driver, spec.submit_selectors) if self._usable(element)),
                None,
            )
            submitted_url = getattr(driver, "current_url", "")
            emit("pre_submit", selector_key=spec.submit_selectors[0] if submit is not None else "keyboard-enter")
            if submit is not None:
                submit.click()
            else:
                field.send_keys(Keys.ENTER)
            if plugin.engine_id == "etools" and getattr(driver, "current_url", "") == submitted_url:
                # eTools documents both POST and GET. Some browser sessions
                # leave the POST form on the homepage; retry the documented
                # GET URL before classifying the run as navigation_state.
                driver.get(plugin.build_url(query, page, country_code, search_type))
            emit("navigation_started")
            emit("serp_waiting")
            self._wait_for_serp(driver, plugin, submitted_url=submitted_url)
            emit("serp_ready", selector_key=spec.serp_ready_selectors[0])
            if page > 1:
                # The current registry has deterministic URL pagination but no
                # shared next-page selector contract yet. Preserve the full
                # homepage flow, then use the provider URL for the requested page.
                driver.get(plugin.build_url(query, page, country_code, search_type))
                emit("navigation_started")
                emit("serp_waiting")
                self._wait_for_serp(driver, plugin, submitted_url=submitted_url)
                emit("serp_ready", selector_key=spec.serp_ready_selectors[0])
        except BrowserFlowError as exc:
            emit(
                "state_classified",
                error_category=exc.category,
                result_count=exc.result_count,
            )
            emit("failure", error_category=exc.category)
            raise
        except WebDriverException as exc:
            emit("state_classified", error_category="webdriver")
            emit("failure", error_category="webdriver")
            raise BrowserFlowError("webdriver", str(exc), url=getattr(driver, "current_url", None)) from exc
        return EnginePage(
            url=getattr(driver, "current_url", None) or spec.homepage_url,
            html=getattr(driver, "page_source", "") or "",
            query=query,
            engine=plugin.engine_id,
            country_code=country_code,
            page=page,
            visible_text=self._visible_text(driver),
        )
