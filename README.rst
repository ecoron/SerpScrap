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
----------

See http://serpscrap.readthedocs.io/en/latest/ for documentation.

Source is available at https://github.com/ecoron/SerpScrap


Install
-------

The easy way to do:

.. code-block:: python

   pip uninstall SerpScrap -y
   pip install SerpScrap --upgrade

More details in the `install`_ section of the documentation.


Usage
=====

SerpScrap in your applications

.. code-block:: python
  
  #!/usr/bin/python3
  # -*- coding: utf-8 -*-
  import pprint
  import serpscrap
  
  keywords = ['example']
  
  config = serpscrap.Config()
  config.set('scrape_urls', False)
  
  scrap = serpscrap.SerpScrap()
  scrap.init(config=config.get(), keywords=keywords)
 results = scrap.run()
  
  for result in results:
      pprint.pprint(result)

More detailes in the `examples`_ section of the documentation.

To avoid encode/decode issues use this command before you start using SerpScrap in your cli.

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8


.. image:: https://raw.githubusercontent.com/ecoron/SerpScrap/master/docs/logo.png
    :target: https://github.com/ecoron/SerpScrap


Changes
-------
Notes about major changes between releases

0.10.0
======

* support for headless chrome, adjusted default time between scrapes

0.9.0
=====

* result types added (news, shopping, image)
* Image search is supported

0.8.0
=====

* text processing tools removed.
* less requirements


References
----------

SerpScrap is using `PhantomJs`_ a scriptable headless WebKit, which is installed automaticly on the first run (Linux, Windows).
The scrapcore is based on `GoogleScraper`_ with several improvements.

.. target-notes::

.. _`install`: http://serpscrap.readthedocs.io/en/latest/install.html
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html
.. _`PhantomJs`: https://github.com/ariya/phantomjs
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper

