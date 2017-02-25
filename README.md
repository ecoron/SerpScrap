# SerpScrap
A python module to scrape and extract data like links, titles, descriptions, ratings, from search engine result pages. 
It wraps a fork of [GoogleScraper](https://github.com/NikolaiT/GoogleScraper) with several improvements.

## Usage

SerpScrap in your applications

```
import serpscrap

keywords = ['one', 'two']
scrap = SerpScrap()
scrap.set_keyword_list(keywords)

result = scrap.scrap_serps()
```

you can also run serpscrap with an individual GoogleScraper configuartion

```
import serpscrap

config = {
    'search_engines': ['google'],
    'num_pages_for_keyword': 2, # number of searchresult pages
    'scrape_method': 'http',  # http, selenium
    # 'sel_browser': 'chrome',  # uncomment if scrape_method is selenium
    # 'executable_path': 'path\to\chromedriver', 'path\to\phantomjs',
    'do_caching': True,
    'cachedir': '/tmp/.serpscrap/',  # path to cache files
    'database_name': '/tmp/serpscrap',  # path SQLight db where scrape results are temporary stored
    'clean_cache_after': 48,  # hours - delete older cache entries
    'output_filename': None,  # stdout, filename.json, filename.csv
    # 'print_results': 'all', # summarize, all - if output_filename = stdout 
}
keywords = ['one', 'two']
scrap = SerpScrap(config)
scrap.set_keyword_list(keywords)

result = scrap.scrap_serps()
```

To run SerpScrap via command line provide one or more keywords as searchphrase.
In this example the searchphrase is "your keywords"

```
python serpscrap\serpscrap.py -k your keywords
```
