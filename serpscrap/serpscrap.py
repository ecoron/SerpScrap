#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
SerpScrap.SerpScrap
"""
import argparse
import chromedriver_autoinstaller
import os
import pprint
import shutil

from scrapcore.core import Core
from scrapcore.logger import Logger
from serpscrap.config import Config
from serpscrap.csv_writer import CsvWriter
from serpscrap.urlscrape import UrlScrape

logger = Logger()
logger.setup_logger()
logger = logger.get_logger()


class SerpScrap:
    """Main module to execute SERP and URL scrape tasks."""
    def __init__(self):
        self.args = []
        self.serp_query = None
        self.results = []
        self.related = []
        self.config = None
        self.driver = None

    def cli(self, args=None):
        """Method called if executed on command line."""
        parser = argparse.ArgumentParser(prog='serpscrap')
        parser.add_argument('-k', '--keyword', help='keyword for scraping', nargs='*')
        self.args = parser.parse_args()
        if self.args.keyword:
            keywords = ' '.join(self.args.keyword)
        else:
            raise ValueError('No keywords provided via CLI.')
        self.init(config=None, keywords=keywords)
        return self.run()

    def _setup_webdriver(self):
        import chromedriver_autoinstaller
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        chromedriver_autoinstaller.install()
        logger.info("Verified chromedriver installation via chromedriver-autoinstaller.")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Anti-Detection: weitere Optionen
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1366,768')
        # Gängige User-Agents
        import random
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        executable_path = self.config.get('executable_path', '')
        if executable_path:
            service = Service(executable_path)
        else:
            service = Service()
        self.driver = webdriver.Chrome(service=service, options=options)
        # Set window size to typical notebook resolution
        self.driver.set_window_size(1366, 768)
        import time
        try:
            self.driver.get('https://www.google.com/')
            # Consent-Banner Handling (auch in iFrames)
            consent_clicked = False
            try:
                # Versuche im Hauptdokument
                consent_selectors = [
                    (By.XPATH, "//button[.//div[contains(text(), 'Ich stimme zu')]]"),
                    (By.XPATH, "//button[.//div[contains(text(), 'Alle akzeptieren')]]"),
                    (By.XPATH, "//button[contains(text(), 'Ich stimme zu') or contains(text(), 'Alle akzeptieren') or contains(text(), 'Accept all') or contains(text(), 'Zustimmen') or contains(text(), 'Akzeptieren') or contains(text(), 'OK') or contains(text(), 'Einverstanden') or contains(text(), 'Zulassen') or contains(text(), 'Allow all') or contains(text(), 'AGREE') or contains(text(), 'accept all') or contains(text(), 'accept')]"),
                    (By.XPATH, "//div[contains(text(), 'Ich stimme zu') or contains(text(), 'Alle akzeptieren') or contains(text(), 'Accept all') or contains(text(), 'Zustimmen') or contains(text(), 'Akzeptieren') or contains(text(), 'OK') or contains(text(), 'Einverstanden') or contains(text(), 'Zulassen') or contains(text(), 'Allow all') or contains(text(), 'AGREE') or contains(text(), 'accept all') or contains(text(), 'accept')]")
                ]
                for by, selector in consent_selectors:
                    elements = self.driver.find_elements(by, selector)
                    if elements:
                        elements[0].click()
                        consent_clicked = True
                        logger.info("Consent-Banner im Hauptdokument akzeptiert.")
                        break
                # Falls nicht gefunden, prüfe iFrames
                if not consent_clicked:
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        self.driver.switch_to.frame(iframe)
                        for by, selector in consent_selectors:
                            elements = self.driver.find_elements(by, selector)
                            if elements:
                                elements[0].click()
                                consent_clicked = True
                                logger.info("Consent-Banner im iFrame akzeptiert.")
                                break
                        self.driver.switch_to.default_content()
                        if consent_clicked:
                            break
            except Exception as ce:
                logger.info(f"Kein Consent-Banner gefunden oder Fehler beim Klicken: {ce}")
            # Nach Consent-Klick ggf. auf Reload warten
            if consent_clicked:
                logger.info("Warte auf Reload nach Consent-Klick...")
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.NAME, "q"))
                )
                time.sleep(2)
            # Warte auf das Suchfeld
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.NAME, "q"))
            )
            time.sleep(2)
            # Befülle das Suchfeld per JavaScript
            try:
                search_box = self.driver.find_element(By.NAME, "q")
                self.driver.execute_script("arguments[0].focus();", search_box)
                search_box.click()
                search_box.clear()
                self.driver.execute_script("arguments[0].value = 'python selenium screenshot';", search_box)
                # Formular absenden per JavaScript
                self.driver.execute_script("arguments[0].form.submit();", search_box)
                logger.info("Suchfeld wurde per JavaScript fokussiert, geleert, befüllt und das Formular wurde abgesendet.")
                # Warte auf Ergebnisseite und speichere Screenshot
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "search"))
                )
                self.driver.save_screenshot('debug_google_results.png')
                logger.info("Screenshot der Suchergebnisseite gespeichert.")
            except Exception as focus_exc:
                logger.error(f"Suchfeld konnte nicht per JS fokussiert/geleert/befüllt/abgesendet werden: {focus_exc}")
            self.driver.save_screenshot('debug_google.png')
        except Exception as e:
            logger.error(f"Fehler beim Laden von Google oder beim Finden des Suchfelds: {e}")
            self.driver.save_screenshot('debug_google_error.png')
            raise

    def init(self, config=None, keywords=None):
        """Initialize config and serp_query."""
        if config is not None:
            self.config = config
        else:
            self.config = Config().get()
        self._setup_webdriver()
        # Cleanup screenshot dir on init
        if os.path.exists(self.config['dir_screenshot']):
            shutil.rmtree(self.config['dir_screenshot'], ignore_errors=True)
        screendir = f"{self.config['dir_screenshot']}/{self.config['today']}"
        if not os.path.exists(screendir):
            os.makedirs(screendir)
        if isinstance(keywords, str):
            self.serp_query = [keywords]
        elif isinstance(keywords, list) and keywords:
            self.serp_query = keywords
        else:
            raise ValueError('No keywords given')

    def run(self):
        """Main method to run scrap_serps and scrap_url."""
        self.results = []
        if self.serp_query is not None:
            self.results = self.scrap_serps()
        if self.config.get('scrape_urls'):
            for index, result in enumerate(self.results):
                if 'serp_type' in result and 'serp_url' in result:
                    logger.info('Scraping URL: ' + result['serp_url'])
                    result_url = self.scrap_url(result['serp_url'])
                    if 'status' in result_url:
                        self.results[index].update(result_url)
        return self.results if isinstance(self.results, list) else [self.results]

    def as_csv(self, file_path: str):
        writer = CsvWriter()
        self.results = self.run()
        writer.write(file_path + '.csv', self.results)

    def scrap_serps(self):
        """Call scrap method and append SERP results to list."""
        search = self.scrap()
        self.results = []
        # Fix: Eagerly load all serps before session is closed
        serps = list(getattr(search, 'serps', [])) if search is not None else []
        if serps:
            for serp in serps:
                self.related = []
                for related_keyword in getattr(serp, 'related_keywords', []):
                    self.related.append({
                        'keyword': related_keyword.keyword,
                        'rank': related_keyword.rank
                    })
                for link in getattr(serp, 'links', []):
                    self.results.append({
                        'query_num_results_total': getattr(serp, 'num_results_for_query', ''),
                        'query_num_results_page': getattr(serp, 'num_results', 0),
                        'query_page_number': getattr(serp, 'page_number', -1),
                        'query': getattr(serp, 'query', ''),
                        'serp_rank': getattr(link, 'rank', None),
                        'serp_type': getattr(link, 'link_type', None),
                        'serp_url': getattr(link, 'link', None),
                        'serp_rating': getattr(link, 'rating', None),
                        'serp_title': getattr(link, 'title', None),
                        'serp_domain': getattr(link, 'domain', None),
                        'serp_visible_link': getattr(link, 'visible_link', None),
                        'serp_snippet': getattr(link, 'snippet', None),
                        'serp_sitelinks': getattr(link, 'sitelinks', None),
                        'screenshot': os.path.join(f"{self.config['dir_screenshot']}/{self.config['today']}/google_{serp.query}-{serp.page_number}.png")
                    })
            return self.results
        else:
            raise Exception('No Results')

    def scrap(self):
        """Call Core().run with the current config and keywords."""
        self.config['keywords'] = self.serp_query if isinstance(self.serp_query, list) else [self.serp_query]
        return Core().run(self.config)

    def scrap_url(self, url: str):
        """Call UrlScrape for a given URL."""
        urlscrape = UrlScrape(self.config)
        return urlscrape.scrap_url(url)

    def get_related(self):
        return self.related
