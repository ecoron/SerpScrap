=============
Configuration
=============

Here we describe how you can configure SerpScrap to fit your needs.
But it is also possible to run SerpScrap with the default settings.

Permissions
-----------

By default all needed or generated files are written into the local /tmp/ folder.
The location can changed by configuration.
Ensure the executing user has read/write permissions for this folder.

Default configuration
---------------------

* cachedir: '/tmp/.serpscrap/'                        - path cachefiles
* chrome_headless: True                               - run chrome in headless mode, default is True
* clean_cache_after: 24                               - clean cached files older then x hours
* database_name: '/tmp/serpscrap'                     - path and name sqlite db (stores scrape results)
* dir_screenshot: '/tmp/screenshots'                  - basedir for saved screenshots
* do_caching: True                                    - enable / disable caching
* executable_path: '/usr/local/bin/chromedriver'      - path to chromedriver, should detected automaticly
* google_search_url: 'https://www.google.com/search?' - base search url, modify for other countries
* headers:                                            - dict to customize request header, see below
* num_pages_for_keyword: 2                            - number of result pages to scrape
* num_results_per_page: 10                            - number results per searchengine page
* results_age: 'Any'                                  - specify age of results default Any, y - last year, m - last month, w - last week, d - last 24h, h - last hour
* proxy_file: ''                                      - path to proxy file, see below
* sel_browser: 'chrome'                               - browser (chrome, phantomjs)
* scrape_urls: False                                  - scrape urls of search results
* screenshot: True                                    - enable screenshots for each query
* search_engines: ['google']                          - search engines (google)
* sleeping_max: 15                                    - max seconds to sleep between scrapes
* sleeping_min: 5                                     - min seconds to sleep between scrapes
* url_threads: 3                                      - number of threads if scrape_urls is true
* use_own_ip: True                                    - if using proxies set to False

Custom configuration
--------------------

Change some config params.

.. code-block:: python

   import serpscrap
   
   config = serpscrap.Config()
   config.set('scrape_urls', False)
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)

You can apply your own config dictionary. It is not required to provide any possible
config key. by applying the default config values will be overwritten by the new values.
for not provided config keys the deault values still exists.

.. code-block:: python

   import serpscrap
   
   config = serpscrap.Config()
   config_new = {
      'cachedir': '/tmp/.serpscrap/',
      'clean_cache_after': 24,
      'database_name': '/tmp/serpscrap',
      'do_caching': True,
      'num_pages_for_keyword': 2,
      'scrape_urls': True,
      'search_engines': ['google'],
      'google_search_url': 'https://www.google.com/search?',
      'executable_path', '/usr/local/bin/chromedriver',
   }
   
   config.apply(config_new)
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   # scrap.init(config=config_new, keywords=keywords)


Headers
-------

You can customize your searchengine request headers if you are using phantomJS
by providing a dict in your configuration. If you
don't customize this setting, the default is used.

.. code-block:: python

   config = {
     ...
     'headers': {
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
         'Accept-Encoding': 'gzip, deflate, sdch',
         'Connection': 'keep-alive',
     },
     ...


Proxy file
----------

This feature works not stable in versions <= 0.9.1, if you use more then one worker
and have more then one proxy in your file.

You can provide a list of proxies which should used for scraping the search engines.
For this you have to create a proxy_file and to set the path to the file in the configuration.

The proxy_file should look like this

.. code-block:: bash

   http XX.XXX.XX.XX:80
   socks4 XX.XXX.XX.XX:80 username:password
   socks5 XX.XXX.XX.XX:1080 username:password


In the configuration you need the following settings:

.. code-block:: python

   config.set('use_own_ip', False)
   config.set('proxy_file', 'path_to_your_file')



