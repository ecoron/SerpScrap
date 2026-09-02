================
Command-line use
================

The installed ``serpscrap`` command writes result JSON to stdout and diagnostic
logs/progress to stderr. This makes it safe to pipe results into another tool.

Global options
==============

Global options must appear before the subcommand:

.. code-block:: console

   serpscrap --help
   serpscrap --log-level DEBUG --log-format json search --help

``--log-level`` accepts ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, and
``CRITICAL``. ``--log-format json`` emits structured log records on stderr.

Search
======

The ``search`` command requires one or more repeated ``--keyword`` options:

.. code-block:: bash

   serpscrap search --keyword "privacy friendly search"
   serpscrap search -k "seo tools" -k "seo news" --pages 2

Important options:

``-k, --keyword, --keywords``
   Query text; repeat for multiple queries. Required.
``--pages INTEGER``
   Number of pages per query, starting at 1.
``--workers INTEGER``
   Maximum concurrent workers.
``--engine ENGINE``
   Select a registered engine; repeat to select multiple engines.
``--country CODE``
   ISO 3166-1 alpha-2 market, for example ``DE``.
``--search-type TYPE``
   One of ``normal``, ``image``, ``news``, ``shopping``, or ``videos``.
``--visible``
   Show Chrome instead of running headless.
``--screenshots``
   Save screenshots for parsed results.
``--scrape-urls``
   Fetch bounded text metadata from result URLs.
``--output PATH``
   Atomically write the JSON result array to a file.
``--overwrite``
   Allow replacing an existing output file.
``--no-cache`` / ``--no-history``
   Disable local HTML caching or SQLite history for this run.
``--consent-action ACTION``
   Use ``necessary``, ``reject``, or ``disabled`` for provider consent.
``--progress/--no-progress``
   Enable or disable per-engine progress on stderr.
``--progress-format FORMAT``
   Use human-readable ``text`` or machine-readable ``jsonl``.
``--diagnostic-html``
   Save redacted rendered HTML for troubleshooting.
``--diagnostic-dir PATH``
   Choose the diagnostic artifact directory.

Examples:

.. code-block:: bash

   serpscrap search -k "renewable energy" --search-type news \
     --engine google --engine bing --country DE --workers 2

   serpscrap search -k "example" --output results.json --overwrite \
     --no-cache --no-history

   serpscrap search -k "provider diagnosis" --engine xprivo \
     --progress-format jsonl --diagnostic-html --diagnostic-dir logs/diagnostics \
     > results.json 2> progress.jsonl

Browser check
=============

Use ``browser-check`` to verify that Chrome can start and close without
contacting a provider:

.. code-block:: bash

   serpscrap browser-check
   serpscrap browser-check --visible

Topic search
============

The ``topic-search`` command runs the shared TopicService for the built-in
``news`` and ``shopping`` topics and writes a versioned report to stdout:

.. code-block:: bash

   serpscrap topic-search news "artificial intelligence" --language en --since 24h
   serpscrap topic-search shopping "noise cancelling headphones" --country DE

Use ``--source`` to provide a feed URL or source identifier. ``--country``
and ``--language`` are normalized before capability filtering. The command
does not bypass provider consent, CAPTCHA, robots, or rate-limit controls.
