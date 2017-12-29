=============
Example Usage
=============

Here we show how you can use SerpScrap for your SEO and research tasks.
You can use it from command line or as module in your application.
Take also a look into the `examples`_ on github.


Simple Example
--------------

.. code-block:: bash

   python examples\example_simple.py

In this example (`example_simple.py`_) we scrape results for the keyword "computer since".
Also the serp result pages are crawled to scrape the raw text content of it.
You can disable url scraping by setting the config value scrape_urls to False.

.. code-block:: python

   import serpscrap
  
   keywords = ['computer since']
   
   config = serpscrap.Config()
   config.set('scrape_urls', True)
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   results = scrap.run()
   
   for result in results:
       print(result)

Simple Example - custom phantomjs path
--------------------------------------

If phantomjs could not installed, configure your
custom path to the binary.

.. code-block:: python

   import serpscrap
   
   keywords = ['seo trends', 'seo news', 'seo tools']
   
   config = serpscrap.Config()
   # only required if phantomjs binary could not detected
   config.set('executable_path', '../phantomjs/phantomjs.exe')
   config.set('num_workers', 1)
   config.set('scrape_urls', False)
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   results = scrap.run()
   for result in results:
       if 'serp_title' in result and len(result['serp_title']) > 1:
           print(result['serp_title'])

Using Chrome
------------

.. code-block:: bash

   python examples\example_chrome.py

It is possible to use Chrome, but we recomment PhantomJs, which is installed by default.
For using Chrome u need to download the latest `chromedriver`_ and to set the executable_path.

.. code-block:: bash

   import pprint
   import serpscrap
   
   keywords = ['berlin']
   
   config = serpscrap.Config()
   config.set('sel_browser', 'chrome')
   config.set('chrome_headless', True)
   config.set('executable_path', '/tmp/chromedriver_win32/chromedriver.exe')
   # linux
   # config.set('executable_path', '/usr/local/bin/chromedriver')
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   results = scrap.run()
   
   for result in results:
       pprint.pprint(result)
       print()

Image search
------------

.. code-block:: bash

   python examples\example_image.py

To scrape the image search instead the standard serps, it's just enough to change
the change the search_type in the config.

.. code-block:: bash

   import pprint
   import serpscrap
   
   keywords = ['lost places']
   
   config = serpscrap.Config()
   config.set('search_type', 'image')
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   results = scrap.run()
   
   for result in results[:10]:
       pprint.pprint(result)
       print()

Url Scrape Example
------------------

.. code-block:: bash

   python examples\example_url.py

In this example we scrape only an url, without crawling any searchengine.

.. code-block:: python

   import serpscrap
   
   url = 'https://en.wikipedia.org/wiki/Special:Random'
   
   config = serpscrap.Config()
   
   urlscrape = serpscrap.UrlScrape(config.get())
   results = urlscrape.scrap_url(url)
   
   for result in results:
       print(result)
       print()


Command Line
------------

.. code-block:: bash

  python serpscrap\serpscrap.py -k your keywords

As arguments provide one or more space separeted keywords.
the result is printed into your console.


Example as_csv()
----------------

save the results for later seo analytics by using the
as_csv() method. this method needs as argument the path
to the file.

.. code-block:: python

   import serpscrap
   
   keywords = ['seo tools', 'seo news']
   
   config = serpscrap.Config()
   config.set('scrape_urls', False)
   
   scrap = serpscrap.SerpScrap()
   scrap.init(config=config.get(), keywords=keywords)
   results = scrap.as_csv('/tmp/seo-research')

Example related
---------------
If you are interested in related keywords
for additional research tasks take a look
into `example_related.py`_ on github.


References

.. target-notes::

.. _`examples`: https://github.com/ecoron/SerpScrap/tree/master/examples
.. _`example_simple.py`: https://github.com/ecoron/SerpScrap/blob/master/examples/example_simple.py
.. _`example_related.py`: https://github.com/ecoron/SerpScrap/blob/master/examples/example_related.py
.. _`chromedriver`: https://sites.google.com/a/chromium.org/chromedriver/downloads

