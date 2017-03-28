=============
Configuration
=============

Here we describe how you can configure SerpScrap to fit your needs.
But it is also possible to run SerpScrap with the default settings.

Default configuration
---------------------

* cachedir: '/tmp/.serpscrap/'    - path cachefiles
* clean_cache_after: 24           - clean cached files older then x hours
* database_name: '/tmp/serpscrap' - path and name sqlite db (stores scrape results)
* do_caching: True                - enable / disable caching
* num_pages_for_keyword: 2        - number of result pages to scrape
* output_filename: None           - store output in filename.csv or filename.json
* proxy_file: ''                  - path to proxy file
* scrape_urls: True               - scrape urls of search results
* search_engines: ['google']      - search engines (google,bing,baidu,yahoo,yandex)
* url_threads: 3                  - number of threads if scrape_urls is true
* use_own_ip: True                - by using proxies set to False

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
      'output_filename': None,
      'proxy_file': '',
      'scrape_urls': True,
      'search_engines': ['google'],
      'url_threads': 3,
   }
   
   config.apply(config_new)
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   # scrap.init(config=config_new, keywords=keywords)

Proxy file
----------

You can provide a list of proxys which should used for scraping the search engines.
For this you have to create a proxy_file and to set the path to the file in the configuration.

The proxy_file should look like this:

.. code-block:: bash
      http XX.XXX.XX.XX:80
      socks4 XX.XXX.XX.XX:80 username:password
      socks5 XX.XXX.XX.XX:1080 username:password

In the configuration you need the following settings:

.. code-block:: python
      config.set('use_own_ip', False)
      config.set('proxy_file', 'path_to_your_file')



