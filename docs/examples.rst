=====================
How to use - examples
=====================

Here we show you how to use SerpScrap. You can use it from command line
or as module in your application


Command Line
------------

.. code-block:: bash

  python serpscrap\serpscrap.py -k your keywords

As arguments provide one or more space separeted keywords.
the result is printed into your console.


Simple Example
--------------

.. code-block:: bash

   python examples\example_simple.py

In this example we scrape results for the keyword "computer since".
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


Text Generator Example
----------------------

For generating text we use markov chains, which are implemented in the Markovi modul.

.. code-block:: bash

   python examples\example_markovi.py

In this example we scrape a single url and use the text_raw of the result, to
generate 5 sentences.

.. code-block:: python
   
   from serpscrap.markovi import Markovi
   from serpscrap.config import Config
   from serpscrap.urlscrape import UrlScrape
   import pprint
   
   
   url = 'http://gutenberg.spiegel.de/buch/johann-wolfgang-goethe-gedichte-3670/231'
   config = Config().get()
   
   urlscrape = UrlScrape(config)
   contents = urlscrape.scrap_url(url)
   
   markovi = Markovi(config)
   texts = []
   for content in contents:
       for _ in range(5):
           texts.append(markovi.generate(content.__getitem__('text_raw'), 1))
   
   pprint.pprint(texts, width=120)


Example advanced
----------------

TODO
