.. image:: https://raw.githubusercontent.com/ecoron/SerpScrap/master/docs/logo.png
    :target: https://github.com/ecoron/SerpScrap

=========
SerpScrap
=========

.. image:: https://img.shields.io/pypi/v/SerpScrap.svg
    :target: https://pypi.python.org/pypi/SerpScrap

.. image:: https://readthedocs.org/projects/serpscrap/badge/?version=latest
    :target: http://serpscrap.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://travis-ci.org/ecoron/SerpScrap.svg?branch=master
    :target: https://travis-ci.org/ecoron/SerpScrap

.. image:: https://img.shields.io/docker/pulls/ecoron/serpscrap.svg
    :target: https://hub.docker.com/r/ecoron/serpscrap

SEO python scraper to extract data from major searchengine result pages.
Extract data like url, title, snippet, richsnippet and the type from searchresults for given keywords. Detect Ads or make automated screenshots.
You can also fetch text content of urls provided in searchresults or by your own.
It's usefull for SEO and business related research tasks.


Extract these result types
--------------------------

* ads_main - advertisements within regular search results
* image - result from image search
* news - news teaser within regular search results
* results - standard search result
* shopping - shopping teaser within regular search results
* videos - video teaser within regular search results

For each result of a resultspage get
====================================

* domain
* rank
* rich snippet
* site links
* snippet
* title
* type
* url
* visible url

Also get a screenshot of each result page.
You can also scrape the text content of each result url.
It is also possible to save the results as CSV for future analytics.
If required you can also use your own proxylist.


Ressources
==========

See http://serpscrap.readthedocs.io/en/latest/ for documentation.

Source is available at https://github.com/ecoron/SerpScrap


Contents
--------
.. toctree::
   :maxdepth: 2
   
   install
   results
   configuration
   docker
   examples
   ressources


Usage
=====

SerpScrap in your applications

.. code-block:: python

   import serpscrap
   
   keywords = ['one', 'two']
   scrap = serpscrap.SerpScrap()
   scrap.init(keywords=keywords)
   result = scrap.scrap_serps()

More detailes in the `examples`_ section of the documentation.

Supported OS
------------

* SerpScrap should work on Linux, Windows and Mac OS with installed Python >= 3.4
* SerpScrap requieres lxml
* Doesn't work on iOS

Changes
=======
Notes about major changes between releases

0.12.0
------

I recommend an update to the latest version of SerpScrap, because the searchengine has updated the markup of search result pages(serp)

* Update and cleanup of selectors to fetch results
* new resulttype videos

0.11.0
------

* Chrome headless is now the default browser, usage of phantomJS is deprecated
* chromedriver is installed on the first run (tested on Linux and Windows. Mac OS should also work)
* behavior of scraping raw text contents from serp urls, and of course given urls, has changed
* run scraping of serp results and contents at once
* csv output format changed, now it's tab separated and quoted

0.10.0
------

* support for headless chrome, adjusted default time between scrapes

0.9.0
-----

* result types added (news, shopping, image)
* Image search is supported

0.8.0
-----

* text processing tools removed.
* less requirements


References
==========

SerpScrap is using `Chrome headless`_ and `lxml`_ to scrape serp results. For raw text contents of fetched URL's, it is using `beautifulsoup4`_ .
SerpScrap also supports `PhantomJs`_ ,which is deprecated, a scriptable headless WebKit, which is installed automaticly on the first run (Linux, Windows).
The scrapcore was based on `GoogleScraper`_ , an outdated project, and has many changes and improvements.

.. target-notes::

.. _`install`: http://serpscrap.readthedocs.io/en/latest/install.html
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html
.. _`Chrome headless`: http://chromedriver.chromium.org/
.. _`lxml`: https://lxml.de/
.. _`beautifulsoup4`: https://www.crummy.com/software/BeautifulSoup/
.. _`PhantomJs`: https://github.com/ariya/phantomjs
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html

