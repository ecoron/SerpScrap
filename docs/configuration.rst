=============
Configuration
=============

``Config`` retains dictionary access for Phase 1 compatibility. New code can
pass friendly options directly to ``SerpScrap.search``. Settings are copied and
validated once for every independent request.

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
* ``store_history``: persist SQLite run history; defaults to ``True``.
* ``database_name``: SQLite history path without the ``.db`` suffix.
* ``scrape_urls``: fetch the text content of parsed result URLs.

Example
-------

.. code-block:: python

   import serpscrap

   scraper = serpscrap.SerpScrap()
   results = scraper.search(
       ['example query'],
       pages=2,
       workers=2,
       screenshots=True,
       store_history=False,
   )

Cache, SQLite history, screenshots, and JSON output are independent. JSON
output is selected with ``output=`` or ``save_json()`` rather than a Config
key. The removed ``output_filename`` and ``print_results`` settings raise a
migration error.

Proxy file
----------

Set ``use_own_ip`` to ``False`` and provide ``proxy_file``. Each non-comment
line uses one of these formats:

.. code-block:: text

   http 192.0.2.10:8080
   socks5 192.0.2.11:1080

Authenticated proxies are rejected by the Chrome factory because they require
an external extension. They are not silently started without authentication.
