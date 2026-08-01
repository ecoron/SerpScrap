=============
Configuration
=============

``Config`` retains dictionary access for compatibility. Values passed to
``SerpScrap.init`` are merged over the defaults and validated before a scrape.

Core settings
-------------

* ``search_engines``: currently ``['google']`` only.
* ``search_type``: ``normal`` or ``image``.
* ``num_pages_for_keyword``: positive page count per query.
* ``num_results_per_page``: positive value up to 100.
* ``num_workers``: maximum concurrent Chrome instances.
* ``chrome_headless``: use headless Chrome; defaults to ``True``.
* ``chrome_binary``: optional explicit Chrome executable.
* ``executable_path``: optional explicit ChromeDriver executable. Empty uses Selenium Manager.
* ``page_load_timeout``: WebDriver navigation timeout in seconds.
* ``wait_timeout``: maximum wait for a recognizable SERP state.
* ``window_width`` and ``window_height``: Chrome viewport dimensions.
* ``language``: Google ``hl`` query parameter.
* ``screenshot``: save diagnostic screenshots; defaults to ``False``.
* ``dir_screenshot``: base directory for screenshots.
* ``do_caching`` and ``cachedir``: enable and locate captured-HTML caching.
* ``database_name``: SQLite database path without the ``.db`` suffix.
* ``scrape_urls``: fetch the text content of parsed result URLs.

Example
-------

.. code-block:: python

   import serpscrap

   config = serpscrap.Config()
   config.apply({
       'num_pages_for_keyword': 2,
       'num_workers': 2,
       'screenshot': True,
   })

   scraper = serpscrap.SerpScrap()
   scraper.init(config=config.get(), keywords=['example query'])
   results = scraper.run()

Proxy file
----------

Set ``use_own_ip`` to ``False`` and provide ``proxy_file``. Each non-comment
line uses one of these formats:

.. code-block:: text

   http 192.0.2.10:8080
   socks5 192.0.2.11:1080

Authenticated proxies are rejected by the Chrome factory because they require
an external extension. They are not silently started without authentication.

