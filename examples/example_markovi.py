from serpscrap.markovi import Markovi
from serpscrap.urlscrape import UrlScrape
from bs4 import BeautifulSoup
import pprint

config = {
    # 'use_own_ip': True,
    'search_engines': ['google'],
    'num_pages_for_keyword': 2,
    'scrape_method': 'http',  # selenium
    # 'sel_browser': 'chrome', uncomment if scrape_method is selenium
    # 'executable_path': 'path\to\chromedriver' or 'path\to\phantomjs',
    'do_caching': True,
    'cachedir': '/tmp/.serpscrap/',
    'database_name': '/tmp/serpscrap',
    'clean_cache_after': 24,
    'output_filename': None,
    # 'print_results': 'all',
    'scrape_urls': True,
    'url_threads': 3
}

url = 'https://www.lmz-bw.de/geschichte-internet.html'
    
urlscrape = UrlScrape(config)
content = urlscrape.scrap_url(url)
pprint.pprint(content['text_raw'])
# soup = BeautifulSoup(content['text_raw'], 'html.parser')

markovi=Markovi(config)
texts = markovi.generate(content['text_raw'], 2, 120)

pprint.pprint(texts)