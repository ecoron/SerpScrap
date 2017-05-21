=============
Configuration
=============

Here we describe how you can configure SerpScrap to fit your needs.
But it is also possible to run SerpScrap with the default settings.

Default configuration
---------------------

* cachedir: '/tmp/.serpscrap/'        - path cachefiles
* clean_cache_after: 24               - clean cached files older then x hours
* database_name: '/tmp/serpscrap'     - path and name sqlite db (stores scrape results)
* do_caching: True                    - enable / disable caching
* headers:                            - dict to customize request header, see below
* num_pages_for_keyword: 2            - number of result pages to scrape
* num_results_per_page: 10            - number results per searchengine page
* proxy_file: ''                      - path to proxy file, see below
* scrape_urls: False                  - scrape urls of search results
* search_engines: ['google']          - search engines (google)
* url_threads: 3                      - number of threads if scrape_urls is true
* use_own_ip: True                    - if using proxies set to False
* sleeping_min: 5                     - min seconds to sleep between scrapes
* sleeping_max: 15                    - max seconds to sleep between scrapes
* screenshot: True                    - enable screenshots for each query
* dir_screenshot: '/tmp/screenshots'  - basedir for saved screenshots
        
Custom configuration
--------------------

Change some config params.

.. code-block:: python

   import serpscrap
   
   config = serpscrap.Config()
   config.set('scrape_urls', False)
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)

Using your own configuration

.. code-block:: python

   import serpscrap
   
   config = serpscrap.Config()
   config_new = {
      'cachedir': '/tmp/.serpscrap/',
      'clean_cache_after': 24,
      'database_name': '/tmp/serpscrap',
      'do_caching': True,
      'num_pages_for_keyword': 2,
      'proxy_file': '',
      'scrape_urls': True,
      'search_engines': ['google'],
      'url_threads': 3,
   }
   
   config.apply(config_new)
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   # scrap.init(config=config_new, keywords=keywords)


Headers
-------

You can customize your searchengine request headers
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

You can provide a list of proxys which should used for scraping the search engines.
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



