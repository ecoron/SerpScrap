------
Docker
------

The image uses Python 3.12 and pins matching Chrome for Testing and ChromeDriver
builds. Build it with:

.. code-block:: bash

   docker build --file docker/app/Dockerfile -t serpscrap .

Run a query through the configured CLI entry point:

.. code-block:: bash

   docker run --rm serpscrap search --keyword "example keyword" --pages 1 --no-history

Phase 9 multicontainer deployment
---------------------------------

The repository includes a four-service Compose deployment:

* ``serpscrap-app`` runs the HTTP API, job orchestration, browser integration,
  and persistent search history.
* ``serpscrap-db`` runs PostgreSQL and stores jobs, results, and failures.
* ``serpscrap-ui`` serves the browser interface on port 8080.
* ``serpscrap-mcp`` exposes the MCP-compatible JSON-RPC gateway on port 8001.

Start the application locally with:

.. code-block:: bash

   mkdir -p data/postgres data/cache data/diagnostics data/exports logs
   docker compose -f docker/compose.yml up --build

Open ``http://localhost:8080`` for the UI. The API is available at
``http://localhost:8000/api/v1`` and MCP requests are sent to
``http://localhost:8001``. PostgreSQL, cache, diagnostic, export, and log data
are mounted below ``./data`` and ``./logs``. Set ``POSTGRES_PASSWORD`` in the
environment before deployment; the Compose default is intended only for local
development.

Health, readiness, and lifecycle
================================

The application exposes ``/healthz`` for liveness and ``/readyz`` for
readiness. Readiness is ``503`` until the database is reachable or while the
application is shutting down. Compose waits for the database health check
before starting the application. A graceful stop allows active jobs to finish:

.. code-block:: bash

   curl http://localhost:8000/healthz
   curl http://localhost:8000/readyz
   docker compose -f docker/compose.yml stop

The app accepts a bounded number of pending jobs. Configure
``SERPSCRAP_MAX_ACTIVE_JOBS`` and ``SERPSCRAP_MAX_QUEUED_JOBS`` in the Compose
environment when the host has different resource limits. A full queue returns
an explicit client error instead of growing memory without a bound.

Pagination is bounded by the API. Use ``limit`` and ``offset`` on
``/api/v1/results``; ``limit`` is capped at 1000.

Docker-specific files are grouped below ``docker/``. The app, UI, and MCP
Dockerfiles use the repository root as their build context, while Compose
mounts use ``../`` paths because they are resolved relative to
``docker/compose.yml``.

Mount output directories when JSON results, caches, databases, or screenshots
must survive the container. Use ``--output /output/results.json`` for local JSON
and mount ``/output``. The image health check starts and closes headless Chrome
without accessing a search engine.
