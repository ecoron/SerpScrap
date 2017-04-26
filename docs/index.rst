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


A python scraper to extract, analyze data from search engine result pages and urls. It might be usefull
for SEO and research tasks. Also some text processing tools are available.

* Extract position, url, title, description, related keywords and other details of searchresults for the given keywords.
* use a list of proxies for scraping.
* scrape also the origin url of the searchresult, the cleaned raw text content from this url would be extracted.
* write results as csv for future analytics
* use some text processing tools like tfidf analyzer or a markovy a text generator to generate new sentences.


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

More detailed informations in the examples section of this documentation.
Source code is also available in the `examples`_ on the github page.

To run SerpScrap via command line provide one or more keywords as searchphrase.
In this example the searchphrase is "your keywords"

.. code-block:: bash

  python serpscrap\serpscrap.py -k your keywords


References
----------

SerpScrap is using `PhantomJs`_ a scriptable headless WebKit, which is installed automaticly on the first run (Linux, Windows)
The scrapcore is based on `GoogleScraper`_ with several improvements.

.. target-notes::

.. _`PhantomJs`: https://github.com/ariya/phantomjs
.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
.. _`serpscrap.readthedocs.io`: http://serpscrap.readthedocs.io/en/latest/
.. _`Microsoft Visual C++ Build Tools`: http://landinghub.visualstudio.com/visual-cpp-build-tools
.. _`lxml`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
.. _`numpy`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
.. _`scipy`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy
.. _`scikit-learn`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-learn
.. _`examples`: https://github.com/ecoron/SerpScrap/tree/master/examples

