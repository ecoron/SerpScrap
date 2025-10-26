# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
from random import randint
import re
import tempfile
import threading
import time
import signal
from urllib.parse import quote

from scrapcore.scraping import MaliciousRequestDetected
from scrapcore.scraping import SearchEngineScrape, SeleniumSearchError
from scrapcore.scraping import get_base_search_url_by_search_engine
from scrapcore.user_agent import random_user_agent
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__name__)


def get_selenium_scraper_by_search_engine_name(config, search_engine_name, *args, **kwargs):
    """Get the appropriate selenium scraper for the given search engine name.

    Args:
        search_engine_name: The search engine name.
        args: The arguments for the target search engine instance creation.
        kwargs: The keyword arguments for the target search engine instance.
    Returns;
        Either a concrete SelScrape instance specific for the given
        search engine or the abstract SelScrape object.
    """
    class_name = search_engine_name[0].upper() + search_engine_name[1:].lower() + 'SelScrape'
    ns = globals()
    if class_name in ns:
        return ns[class_name](config, *args, **kwargs)

    return SelScrape(config, *args, **kwargs)


class SelScrape(SearchEngineScrape, threading.Thread):
    """
    Selenium-basierter Scraper-Thread für verschiedene Suchmaschinen.
    Nutzt konfigurierbaren Chrome-Browser und unterstützt Proxies, Captcha-Locks und Screenshots.
    """

    next_page_selectors = {
        'google': '#pnnext',
        'yandex': '.pager__button_kind_next',
        'bing': '.sb_pagN',
        'yahoo': '.compPagination .next',
        'baidu': '.n',
        'ask': '#paging div a.txt3.l_nu',
        'duckduckgo': '',
        'googleimg': '#pnnext',
        'baiduimg': '.n',
    }

    input_field_selectors = {
        'google': (By.NAME, 'q'),
        'yandex': (By.NAME, 'text'),
        'bing': (By.NAME, 'q'),
        'yahoo': (By.NAME, 'p'),
        'baidu': (By.NAME, 'wd'),
        'duckduckgo': (By.NAME, 'q'),
        'ask': (By.NAME, 'q'),
        'google': (By.NAME, 'q'),
        'googleimg': (By.NAME, 'as_q'),
        'baiduimg': (By.NAME, 'word'),
    }

    param_field_selectors = {
        'googleimg': {
            'image_type': (By.ID, 'imgtype_input'),
            'image_size': (By.ID, 'imgsz_input'),
        },
    }

    search_params = {
        'googleimg': {
            'image_type': None,
            'image_size': None,
        },
    }

    normal_search_locations = {
        'google': 'https://www.google.com/',
        'yandex': 'http://www.yandex.ru/',
        'bing': 'http://www.bing.com/',
        'yahoo': 'https://yahoo.com/',
        'baidu': 'http://baidu.com/',
        'duckduckgo': 'https://duckduckgo.com/',
        'ask': 'http://ask.com/',
    }

    image_search_locations = {
        'google': 'https://www.google.com/imghp',
        'yandex': 'http://yandex.ru/images/',
        'bing': 'https://www.bing.com/?scope=images',
        'yahoo': 'http://images.yahoo.com/',
        'baidu': 'http://image.baidu.com/',
        'duckduckgo': None,  # duckduckgo doesnt't support direct image search
        'ask': 'http://www.ask.com/pictures/',
        'googleimg': 'https://www.google.com/advanced_image_search',
        'baiduimg': 'http://image.baidu.com/',
    }

    def __init__(self, config: dict, search_engine=None, query=None, *args, screenshot_dir=None, captcha_lock=None, browser_num: int = 1, **kwargs):
        self.query = query
        self.screenshot_dir = screenshot_dir
        self.search_input = None
        threading.Thread.__init__(self)
        # Fix: jobs-Key muss hashbar sein (z.B. String statt dict)
        if isinstance(query, dict):
            # Versuche, das Keyword zu extrahieren, sonst nutze repr(query)
            key = query.get('keyword') if 'keyword' in query else repr(query)
        else:
            key = query
        jobs = {key: [1]} if key else None
        SearchEngineScrape.__init__(
            self,
            config=config,
            search_engine=search_engine,
            jobs=jobs,
            **kwargs
        )
        self.browser_type = self.config.get('sel_browser', 'chrome').lower()
        self.browser_num = browser_num
        self.captcha_lock = captcha_lock
        self.scrape_method = 'selenium'
        self.xvfb_display = self.config.get('xvfb_display', None)
        self.search_param_values = self._get_search_param_values()
        self.base_search_url = get_base_search_url_by_search_engine(
            self.config,
            self.search_engine_name,
            self.scrape_method
        )
        super().instance_creation_info(self.__class__.__name__)

    def set_proxy(self):
        """Installiert einen Proxy auf dem Kommunikationskanal (Platzhalter)."""
        pass

    def switch_proxy(self, proxy):
        """Wechselt den Proxy auf dem Kommunikationskanal (Platzhalter)."""
        pass

    def proxy_check(self, proxy) -> bool:
        """Prüft, ob der Proxy online ist und korrekt verwendet wird."""
        assert self.proxy and self.webdriver, '''Scraper instance needs valid
        webdriver and proxy instance to make the proxy check'''

        online = False
        status = '''Proxy check failed: {host}:{port}
        is not used while requesting'''.format(
            host=self.proxy.host,
            port=self.proxy.port
        )
        ipinfo = {}

        try:
            self.webdriver.get(self.config.get('proxy_info_url'))
            time.sleep(2)
            try:
                text = re.search(
                    r'(\{.*?\})',
                    self.webdriver.page_source,
                    flags=re.DOTALL
                ).group(0)
                ipinfo = json.loads(text)
            except ValueError as v:
                logger.critical(v)

        except Exception as e:
            status = str(e)

        if 'ip' in ipinfo and ipinfo['ip']:
            online = True
            status = 'Proxy is working.'
        else:
            logger.warning(status)

        super().update_proxy_status(status, ipinfo, online)

        return online

    def _save_debug_screenshot(self):
        """Speichert einen Debug-Screenshot des Browserfensters."""
#         if self.config.get('sel_browser') == 'chrome' and self.config.get('chrome_headless') is True:
#             """screenshots in headless chrome does not work at the moment"""
#             logger.info('no screenshot for chrome headless possible, may be working in the future')
#             return

        screendir = '{}/{}'.format(
            self.config['dir_screenshot'],
            self.config['today']
        )

        if not os.path.exists(screendir):
            os.makedirs(screendir)

        location = os.path.join(
            screendir, '{}_{}-p{}.png'.format(
                self.search_engine_name,
                self.query,
                str(self.page_number),
            )
        )

        if self.config.get('sel_browser') == 'chrome' and self.config.get('chrome_headless') is True:
            self._enable_download_in_headless_chrome(self.webdriver, screendir)
            total_height = self.webdriver.execute_script("return document.body.parentNode.scrollHeight")
            self.webdriver.set_window_size('1024', total_height)
        try:
            self.webdriver.get_screenshot_as_file(location)
        except Exception as err:
            logger.error(err)

    def _set_xvfb_display(self):
        """Setzt das Xvfb-Display, falls konfiguriert."""
        if self.xvfb_display:
            os.environ['DISPLAY'] = self.xvfb_display

    def _get_webdriver(self):
        """Gibt eine konfigurierte Webdriver-Instanz zurück."""
        if self.browser_type == 'chrome':
            return self._get_Chrome()
        return False

    def _enable_download_in_headless_chrome(self, browser, download_dir):
        """Aktiviert Downloads im Headless-Chrome-Modus."""
        #add missing support for chrome "send_command"  to selenium webdriver
        browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        browser.execute("send_command", params)

    def _get_Chrome(self) -> bool:
        try:
            from selenium.webdriver.chrome.service import Service
            chrome_ops = webdriver.ChromeOptions()
            if self.proxy:
                chrome_ops = webdriver.ChromeOptions()
                chrome_ops.add_argument(
                    '--proxy-server={}://{}:{}'.format(
                        self.proxy.proto,
                        self.proxy.host,
                        self.proxy.port
                    )
                )
                service = Service(self.config['executable_path'])
                self.webdriver = webdriver.Chrome(
                    service=service,
                    options=chrome_ops
                )
            else:
                service = Service(self.config['executable_path'])
            if self.config.get('chrome_headless') is True:
                chrome_ops.add_argument('--headless')
            chrome_ops.add_argument('--no-sandbox')
            chrome_ops.add_argument('--start-maximized')
            chrome_ops.add_argument('--disable-gpu')
            chrome_ops.add_argument('--verbose')
            chrome_ops.add_argument(
                '--window-position={},{}'.format(
                    randint(10, 30),
                    randint(10, 30)
                )
            )
            chrome_ops.add_argument(
                '--window-size={},{}'.format(
                    randint(800, 1024),
                    randint(600, 900)
                )
            )
            self.webdriver = webdriver.Chrome(
                service=service,
                options=chrome_ops
            )
            return True
        except WebDriverException as e:
            logger.error(e)
            raise
        return False

    def handle_request_denied(self, status_code):
        """Behandelt blockierte Requests (z.B. Captcha)."""
        # selenium webdriver objects have no status code :/
        super().handle_request_denied('400')

        needles = self.malicious_request_needles[self.search_engine_name]

        if needles and needles['inurl'] in self.webdriver.current_url \
                and needles['inhtml'] in self.webdriver.page_source:

            if self.config.get('manual_captcha_solving', False):
                with self.captcha_lock:
                    # import tempfile

                    tf = tempfile.NamedTemporaryFile('wb')
                    tf.write(self.webdriver.get_screenshot_as_png())
                    import webbrowser

                    webbrowser.open('file://{}'.format(tf.name))
                    solution = input('enter the captcha please...')
                    self.webdriver.find_element_by_name('submit').send_keys(solution + Keys.ENTER)
                    try:
                        self.search_input = WebDriverWait(self.webdriver, 5).until(
                            EC.visibility_of_element_located(self._get_search_input_field()))
                    except TimeoutException:
                        raise MaliciousRequestDetected('Requesting with this ip is not possible at the moment.')
                    tf.close()

            else:
                # Just wait until the user solves the captcha in the browser window
                # 10 hours if needed :D
                logger.info('Waiting for user to solve captcha')
                return self._wait_until_search_input_field_appears(10 * 60 * 60)

    def build_search(self):
        """Baut die Such-URL für den aktuellen Suchmaschinentyp."""
        assert self.webdriver, 'Webdriver needs to be ready to build the search'

        if self.config.get('search_type', 'normal') == 'image':
            starting_point = self.image_search_locations[self.search_engine_name]
        else:
            starting_point = self.base_search_url
            # logger.info('results_age: ' + self.config.get('results_age'))
            if self.config.get('num_results_per_page', 10) > 10:
                starting_point = '{}num={}'.format(starting_point, str(self.config.get('num_results_per_page', 10)))
            if 'Any' not in self.config.get('results_age'):
                starting_point = '{}&tbs=qdr:={}'.format(starting_point, str(self.config.get('results_age', 'y')))
            logger.info(starting_point)

        self.webdriver.get(starting_point)

    def _get_search_param_values(self) -> dict:
        """Liest die Suchparameter aus der Konfiguration aus."""
        search_param_values = {}
        if self.search_engine_name in self.search_params:
            for param_key in self.search_params[self.search_engine_name]:
                cfg = self.config.get(param_key, None)
                if cfg:
                    search_param_values[param_key] = cfg
        return search_param_values

    def _get_search_input_field(self):
        """Gibt das Locator-Tuple für das Suchfeld zurück."""
        return self.input_field_selectors[self.search_engine_name]

    def _get_search_param_fields(self) -> dict:
        """Gibt die Locator-Tuples für Suchparameter-Felder zurück."""
        if self.search_engine_name in self.param_field_selectors:
            return self.param_field_selectors[self.search_engine_name]
        else:
            return {}

    def _wait_until_search_input_field_appears(self, max_wait: int = 10):
        """Wartet, bis das Suchfeld sichtbar ist."""

        def find_visible_search_input(driver):
            input_field = driver.find_element(*self._get_search_input_field())
            return input_field

        try:
            search_input = WebDriverWait(self.webdriver, max_wait).until(find_visible_search_input)
            return search_input
        except TimeoutException as e:
            logger.error('{}: TimeoutException waiting for search input field: {}'.format(self.name, e))
            return False

    def _wait_until_search_param_fields_appears(self, max_wait: int = 5):
        """Wartet, bis alle Suchparameter-Felder sichtbar sind."""
        def find_visible_search_param(driver):
            for _, field in self._get_search_param_fields().items():
                input_field = driver.find_element(*field)
                if not input_field:
                    return False
            return True

        try:
            fields = WebDriverWait(self.webdriver, max_wait).until(find_visible_search_param)
            return fields
        except TimeoutException as e:
            logger.error('{}: TimeoutException waiting for search param field: {}'.format(self.name, e))
            return False

    def _goto_next_page(self):
        """Klickt auf das Element für die nächste Seite und gibt die URL zurück."""
        next_url = ''
        element = self._find_next_page_element()

        if hasattr(element, 'click'):
            next_url = element.get_attribute('href')
            try:
                element.click()
            except WebDriverException:
                # See http://stackoverflow.com/questions/11908249/debugging-element-is-not-clickable-at-point-error
                # first move mouse to the next element, some times the element is not visibility
                selector = self.next_page_selectors[self.search_engine_name]
                if selector:
                    try:
                        next_element = WebDriverWait(self.webdriver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        webdriver.ActionChains(self.webdriver).move_to_element(next_element).perform()
                        # wait until the next page link emerges
                        WebDriverWait(self.webdriver, 8).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                        element = self.webdriver.find_element_by_css_selector(selector)
                        next_url = element.get_attribute('href')
                        element.click()
                    except WebDriverException:
                        pass

        # wait until the next page was loaded

        if not next_url:
            return False
        else:
            return next_url

    def _find_next_page_element(self):
        """Findet das Element für die nächste Seite."""
        if self.search_type == 'normal':
            selector = self.next_page_selectors[self.search_engine_name]
            try:
                # wait until the next page link is clickable
                WebDriverWait(self.webdriver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            except (WebDriverException, TimeoutException):
                self._save_debug_screenshot()
                # raise Exception('{}: Cannot locate next page element: {}'.format(self.name, str(e)))
            try:
                return self.webdriver.find_element_by_css_selector(selector)
            except Exception:
                logger.error('failed find_element_by_css_selector, sleep 30 sec')
                time.sleep(30)
                pass

        elif self.search_type == 'image':
            self.page_down()
            if self.search_engine_name == 'google':
                return self.webdriver.find_element_by_css_selector('input._kvc')
            else:
                return True

    def wait_until_serp_loaded(self):
        """Wartet, bis die SERP-Seite geladen ist."""

        if self.search_type == 'normal':

            if self.search_engine_name == 'google':
                selector = '#resultStats'
            elif self.search_engine_name == 'yandex':
                selector = '.pager__item_current_yes font font'
            elif self.search_engine_name == 'bing':
                selector = 'nav li a.sb_pagS'
            elif self.search_engine_name == 'yahoo':
                selector = '.compPagination strong'
            elif self.search_engine_name == 'baidu':
                selector = '#page .fk_cur + .pc'
            elif self.search_engine_name == 'duckduckgo':
                # no pagination in duckduckgo
                pass
            elif self.search_engine_name == 'ask':
                selector = '#paging .pgcsel .pg'

            try:
                WebDriverWait(self.webdriver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            except NoSuchElementException:
                logger.error('No such element. Seeing if title matches before raising SeleniumSearchError')
                self._save_debug_screenshot()
                try:
                    self.wait_until_title_contains_keyword()
                except TimeoutException:
                    self.quit()
                    raise SeleniumSearchError('Stop Scraping, seems we are blocked')
            except Exception as e:
                logger.error('Scrape Exception pass. Selector: ' + str(selector))
                logger.error('Error: ' + str(e))
                self._save_debug_screenshot()
                pass

        else:
            self.wait_until_title_contains_keyword()

    def wait_until_title_contains_keyword(self):
        """Wartet, bis der Seitentitel das Keyword enthält."""
        try:
            WebDriverWait(self.webdriver, 5).until(EC.title_contains(self.query))
        except TimeoutException:
            logger.debug(SeleniumSearchError(
                '{}: Keyword "{}" not found in title: {}'.format(self.name, self.query, self.webdriver.title)))

    def search(self):
        """Führt die Suche mit dem Webdriver aus."""
        self.search_input = self._wait_until_search_input_field_appears()
        time.sleep(.25)

        if self.search_input is False and self.config.get('stop_on_detection'):
            self.status = 'Malicious request detected'
            return

        if self.search_input is False:
            # @todo: pass status_code
            self.search_input = self.handle_request_denied()

        if self.search_input:
            try:
                if self.config.get('sel_browser') != 'chrome' or (self.config.get('sel_browser') == 'chrome' and self.config.get('chrome_headless') is False):
                    self.search_input.clear()
            except Exception as e:
                logger.error('Possible blocked search, sleep 30 sec, Scrape Exception: ' + str(e))
                self._save_debug_screenshot()
                time.sleep(30)
            time.sleep(.25)

            self.search_param_fields = self._get_search_param_fields()

            if self.search_param_fields:
                wait_res = self._wait_until_search_param_fields_appears()
                if wait_res is False:
                    self.quit()
                    raise Exception('Waiting search param input fields time exceeds')

                for param, field in self.search_param_fields.items():
                    if field[0] == By.ID:
                        js_tpl = '''
                        var field = document.getElementById("%s");
                        field.setAttribute("value", "%s");
                        '''
                    elif field[0] == By.NAME:
                        js_tpl = '''
                        var fields = document.getElementsByName("%s");
                        for (var f in fields) {
                            f.setAttribute("value", "%s");
                        }
                        '''
                    js_str = js_tpl % (field[1], self.search_param_values[param])
                    self.webdriver.execute_script(js_str)

            try:
                self.search_input.send_keys(self.query + Keys.ENTER)
            except ElementNotVisibleException:
                time.sleep(2)
                try:
                    self.search_input.send_keys(self.query + Keys.ENTER)
                except Exception:
                    logger.error('send keys not possible, maybe page cannot loaded')
                    self.quit()
            except Exception:
                logger.error('send keys not possible')
                pass

            self.requested_at = datetime.datetime.utcnow()
        else:
            logger.debug('{}: Cannot get handle to the input form for keyword {}.'.format(self.name, self.query))

        super().detection_prevention_sleep()
        super().keyword_info()

        for self.page_number in self.pages_per_keyword:

            self.wait_until_serp_loaded()

            try:
                if self.config.get('screenshot') is True:
                    self._save_debug_screenshot()
                    time.sleep(.5)
                self.html = self.webdriver.execute_script('return document.body.innerHTML;')
            except (ConnectionError, ConnectionRefusedError, ConnectionResetError) as err:
                logger.error(err)
            except WebDriverException:
                self.html = self.webdriver.page_source
            except Exception as err:
                logger.error(err)

            super().after_search()

            # Click the next page link not when leaving the loop
            # in the next iteration.
            if self.page_number + 1 in self.pages_per_keyword:
                logger.info('Requesting the next page')
                next_url = self._goto_next_page()
                self.requested_at = datetime.datetime.utcnow()

                if not next_url:
                    break

    def page_down(self):
        """Scrollt die Seite nach unten (z.B. für Bildersuche)."""
        js = 'window.scrollTo(0,document.body.scrollHeight);'

        time.sleep(5)
        self.webdriver.execute_script(js)

    def run(self):
        """Startet den Scraper-Thread für alle Keywords/JOBS."""

        for self.query, self.pages_per_keyword in self.jobs.items():
            # for each keyword request a fresh webdriver instance
            # with random useragent and window_size
            self._set_xvfb_display()

            if not self._get_webdriver():
                raise Exception('{}: Aborting due to no available selenium webdriver.'.format(self.name))

            try:
                x = randint(800, 1024)
                y = randint(600, 900)
                self.webdriver.set_window_size(x, y)
                # self.webdriver.set_window_position(x * (self.browser_num % 4), y * (math.floor(self.browser_num // 4)))
                self.webdriver.set_window_position(x * (self.browser_num % 4), randint(1, 10))
            except WebDriverException as e:
                logger.error('Cannot set window size: {}'.format(e))

            super().before_search()

            if self.startable:
                self.build_search()
                self.search()

            self.quit()

    def quit(self):
        """Beendet und schließt den Webdriver."""
        if self.webdriver:
            self.webdriver.close()
            self.webdriver.quit()


"""
For most search engines, the normal SelScrape works perfectly, but sometimes
the scraping logic is different for other search engines.

Duckduckgo loads new results on the fly (via ajax) and doesn't support any "next page"
link. Other search engines like gekko.com have a completely different SERP page format.

That's why we need to inherit from SelScrape for specific logic that only applies for the given
search engine.

The following functionality may differ in particular:

    - _goto_next_page()
    - _get_search_input()
    - _wait_until_search_input_field_appears()
    - _handle_request_denied()
    - wait_until_serp_loaded()
"""


class DuckduckgoSelScrape(SelScrape):
    """
    Duckduckgo ist etwas speziell, da neue Ergebnisse per Ajax geladen werden.
    Die nächste Seite wird durch Scrollen nach unten erreicht.
    """

    def __init__(self, *args, **kwargs):
        SelScrape.__init__(self, *args, **kwargs)
        self.largest_id = 0

    def _goto_next_page(self):
        super().page_down()
        return 'No more results' not in self.html

    def wait_until_serp_loaded(self):
        super()._wait_until_search_input_field_appears()


class AskSelScrape(SelScrape):
    def __init__(self, *args, **kwargs):
        SelScrape.__init__(self, *args, **kwargs)

    def wait_until_serp_loaded(self):

        def wait_until_keyword_in_url(driver):
            try:
                return quote(self.query) in driver.current_url or \
                    self.query.replace(' ', '+') in driver.current_url
            except WebDriverException:
                pass

        WebDriverWait(self.webdriver, 5).until(wait_until_keyword_in_url)
