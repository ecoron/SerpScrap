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


A python scraper to extract, analyze data from search engine result pages and urls. It might be usefull
for SEO and research tasks. Also some text processing tools are available.

* Extract position, url, title, description, related keywords and other details of searchresults for the given keywords.
* get screenshots of each resultpage.
* use a list of proxies for scraping.
* scrape also the origin url of the searchresult, the cleaned raw text content from this url would be extracted.
* save results as csv for future analytics

Changes
=======
in version 0.8.0 the text processing tools was removed. this will be part of a new project. This changes helps to
reduce the requirements and to make it more easy to setup and run SerpScrap.

See http://serpscrap.readthedocs.io/en/latest/ for documentation.

Source is available at https://github.com/ecoron/SerpScrap.


Install
=======

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

References
----------

SerpScrap is using `PhantomJs`_ a scriptable headless WebKit, which is installed automaticly on the first run (Linux, Windows).
The scrapcore is based on `GoogleScraper`_ with several improvements.

.. target-notes::

.. _`install`: http://serpscrap.readthedocs.io/en/latest/install.html
.. _`examples`: http://serpscrap.readthedocs.io/en/latest/examples.html
.. _`PhantomJs`: https://github.com/ariya/phantomjs
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper

