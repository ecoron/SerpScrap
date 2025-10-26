# -*- coding: utf-8 -*-
import logging
import threading
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

class SelScrape(threading.Thread):
    """Threaded Selenium-based headless browser scraper for search engines."""
    next_page_selectors = {
        'google': '#pnnext',
        'bing': '.sb_pagN'
    }
    input_field_selectors = {
        'google': (By.NAME, 'q'),
        'bing': (By.NAME, 'q')
    }
    normal_search_locations = {
        'google': 'https://www.google.com/',
        'bing': 'https://www.bing.com/'
    }

    def __init__(self, config: dict, search_engine_name: str, query: str, browser_num: int = 1, screenshot_dir: str = None):
        super().__init__()
        self.config = config
        self.search_engine_name = search_engine_name
        self.query = query
        self.browser_num = browser_num
        self.screenshot_dir = screenshot_dir
        self.webdriver = None

    def _get_webdriver(self) -> None:
        """Initialize a headless Chrome WebDriver instance."""
        from chromedriver_autoinstaller import install as chrome_install
        chrome_install()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.webdriver = webdriver.Chrome(options=options)

    def search(self) -> str:
        """Perform a search and return the HTML of the results page."""
        self._get_webdriver()
        url = self.normal_search_locations[self.search_engine_name]
        self.webdriver.get(url)
        search_input = WebDriverWait(self.webdriver, 10).until(
            EC.presence_of_element_located(self.input_field_selectors[self.search_engine_name])
        )
        search_input.send_keys(self.query + Keys.ENTER)
        time.sleep(1)
        html = self.webdriver.page_source
        logger.info(f"Suchanfrage '{self.query}' auf {self.search_engine_name}.")
        if self.screenshot_dir:
            try:
                self.webdriver.save_screenshot(f"{self.screenshot_dir}/screenshot_{self.search_engine_name}_{self.browser_num}.png")
            except Exception as e:
                logger.warning(f"Screenshot konnte nicht gespeichert werden: {e}")
        return html

    def go_to_next_page(self) -> str:
        """Navigate to the next page of results and return the HTML, or None if not found."""
        try:
            next_selector = self.next_page_selectors[self.search_engine_name]
            next_button = WebDriverWait(self.webdriver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, next_selector))
            )
            next_button.click()
            time.sleep(1)
            return self.webdriver.page_source
        except (TimeoutException, WebDriverException):
            logger.info("Keine weitere Seite gefunden.")
            return None

    def quit(self) -> None:
        """Quit the WebDriver instance if it exists."""
        if self.webdriver:
            self.webdriver.quit()
