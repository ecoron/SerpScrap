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
* use a list of proxies for scraping.
* scrape also the origin url of the searchresult, the cleaned raw text content from this url is extracted.
* save results as csv for future analytics
* use some text processing tools like tfidf analyzer or a markovy a text generator to generate new sentences.

See http://serpscrap.readthedocs.io/en/latest/ for documentation.

Source is available at https://github.com/ecoron/SerpScrap.


Install
=======

The easy way to do:

.. code-block:: python

   pip uninstall SerpScrap -y
   pip install SerpScrap --upgrade


In some cases it is required to install python-scipy first

.. code-block:: bash

   sudo apt-get build-dep python-scipy

More details in the `install`_ section of the documentation.

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

