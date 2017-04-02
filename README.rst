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


A python module to scrape, extract, analyze data from search engine result pages and urls.
Extract data, like url, title, snippet of results or ratings for given keywords.
Extract the cleaned raw text content from urls.
Get the tfidf of the text content, or generate with the text generator new sentences.

See http://serpscrap.readthedocs.io/en/latest/ for documentation.

Source is available at https://github.com/ecoron/SerpScrap.


Install
=======

The easiest way to do

.. code-block:: python

   pip install SerpScrap


In some cases it is required to install python-scipy first

.. code-block:: bash

   sudo apt-get build-dep python-scipy


Requirements Windows
--------------------

on Windows you might need also `Microsoft Visual C++ Build Tools`_ installed.

* `lxml`_
* `numpy`_
* `scipy`_
* `scikit-learn`_

avoid encode/decode issues by running this command before starting python in your cli

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8

Usage
=====

SerpScrap in your applications

.. code-block:: python

   import serpscrap
   
   keywords = ['one', 'two']
   scrap = serpscrap.SerpScrap()
   scrap.init(keywords=keywords)
   result = scrap.scrap_serps()

You find more `examples`_ on the github page.

To run SerpScrap via command line provide one or more keywords as searchphrase.
In this example the searchphrase is "your keywords"

.. code-block:: bash

  python serpscrap\serpscrap.py -k your keywords


References
----------

The scrapcore is based on `GoogleScraper`_ with several improvements.

.. target-notes::

.. _`GoogleScraper`: https://github.com/NikolaiT/GoogleScraper
.. _`serpscrap.readthedocs.io`: http://serpscrap.readthedocs.io/en/latest/
.. _`Microsoft Visual C++ Build Tools`: http://landinghub.visualstudio.com/visual-cpp-build-tools
.. _`lxml`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
.. _`numpy`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
.. _`scipy`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy
.. _`scikit-learn`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-learn
.. _`examples`: https://github.com/ecoron/SerpScrap/tree/master/examples

