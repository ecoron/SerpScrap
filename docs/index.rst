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

SEO python scraper to extract and analyze data from major search engine serps or text content of any other url.
Extract data like title, url, type, text- and richsnippet of searchresults for given keywords. detect ads, automated screenshots.
It might be usefull for SEO and research tasks.


Extract these result types
--------------------------

* ads_main - advertisements within regular search results
* image - result from image search
* news - news teaser within regular search results
* results - standard search result
* shopping - shopping teaser within regular search results

For each result in a resultspage get
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
It also possible to save the results as CSV for future analytics.
If required you can use your own proxylist.


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


Changes
=======
Notes about major changes between releases

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

SerpScrap is using `PhantomJs`_ a scriptable headless WebKit, which is installed automaticly on the first run (Linux, Windows)
The scrapcore is based on `GoogleScraper`_ with several improvements.

.. target-notes::

.. _`PhantomJs`: https://github.com/ariya/phantomjs
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html

