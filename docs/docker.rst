------
Docker
------

The image uses Python 3.12 and pins matching Chrome for Testing and ChromeDriver
builds. Build it with:

.. code-block:: bash

   docker build -t serpscrap .

Run a query through the configured CLI entry point:

.. code-block:: bash

   docker run --rm serpscrap search --keyword "example keyword" --pages 1

Mount output directories when caching, databases, or screenshots must survive
the container. The image health check starts and closes headless Chrome without
accessing a search engine.
