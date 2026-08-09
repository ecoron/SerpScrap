==================
Docker application
==================

The Compose deployment runs the complete Version 2 alpha application:

* ``serpscrap-db`` stores runs, results, failures, and history in PostgreSQL.
* ``serpscrap-app`` provides the API and executes browser searches.
* ``serpscrap-ui`` provides the operator web interface.
* ``serpscrap-mcp`` provides the MCP-compatible JSON-RPC gateway.
* ``searxng`` provides the local metasearch service and web UI.
* ``searxng-valkey`` provides SearXNG's rate-limit/cache backend.

All three project services use the single image built by
``docker/Dockerfile``. Compose changes only the service command, ports,
health check, environment, and mounts; PostgreSQL continues to use its
official ``postgres:16-alpine`` image.

The current project version is **2.0.0-alpha.2**. It is an evaluation release;
pin the image tag or Git revision used in repeatable deployments.

Quick start
===========

From the repository root:

.. code-block:: bash

   mkdir -p data/postgres data/cache data/diagnostics data/exports logs
   docker compose -f docker/compose.yml up --build

The Flask/Jinja UI runs inside ``serpscrap-ui`` at ``http://localhost:8080``.
The bundled SearXNG UI is available at ``http://localhost:8888``; SerpScrap
reaches the same service internally at ``http://searxng:8080``.
The API is at
``http://localhost:8000/api/v1`` and the MCP gateway is at
``http://localhost:8001``.

The UI communicates with PostgreSQL indirectly through the shared API:
``serpscrap-ui`` calls ``serpscrap-app`` over the Compose network, while
``serpscrap-app`` uses the configured ``DATABASE_URL`` for search runs,
results, failures, configuration, and analytics. Start the complete Compose
stack; starting only the UI container cannot provide data or search actions.

The UI health endpoint is ``http://localhost:8080/healthz``. The shared image
contains the Flask UI module, Jinja templates, static assets, and API client;
Compose starts the UI with ``python -m ui.app``.

To build and run only the CLI image:

.. code-block:: bash

   docker build --file docker/Dockerfile -t serpscrap:2.0.0-alpha.2 .
   docker run --rm serpscrap:2.0.0-alpha.2 search \
     --keyword "example keyword" --pages 1 --no-history

Configuration
=============

Set deployment values in an environment file or the shell before starting
Compose. PostgreSQL and SearXNG secrets are required; Compose refuses to start
with placeholder credentials:

.. code-block:: bash

   $env:POSTGRES_PASSWORD = "use-a-secret-value"  # PowerShell
   $env:SEARXNG_SECRET = "use-another-secret-value"
   $env:MCP_AUTH_TOKEN = "use-a-third-secret-value"
   docker compose -f docker/compose.yml up -d

Important variables include ``POSTGRES_DB``, ``POSTGRES_USER``,
``POSTGRES_PASSWORD``, ``SERPSCRAP_MAX_ACTIVE_JOBS``, and
``SERPSCRAP_MAX_QUEUED_JOBS``. SearXNG uses ``SEARXNG_SECRET``.
``SERPSCRAP_SEARXNG_URL`` defaults to
``http://searxng:8080``. The MCP service uses ``SERPSCRAP_API_URL`` internally;
see :doc:`mcp` for client usage.

SearXNG is enabled by default when its URL is configured. Use the
configuration UI or the persisted ``searxng_enabled`` setting to disable it.
The Compose deployment mounts ``docker/searxng/settings.yml`` and
``docker/searxng/limiter.toml`` for the local instance.

Health and operations
=====================

.. code-block:: bash

   curl http://localhost:8000/healthz
   curl http://localhost:8000/readyz
   curl http://localhost:8001/healthz
   docker compose -f docker/compose.yml ps

``/healthz`` checks liveness. ``/readyz`` returns HTTP 503 while PostgreSQL is
unavailable or the application is shutting down. Jobs and pending queue slots
are bounded; a full queue returns an explicit error.

Stop gracefully and inspect logs with:

.. code-block:: bash

   docker compose -f docker/compose.yml logs -f serpscrap-app
   docker compose -f docker/compose.yml stop

Persistent data and backups
===========================

Compose mounts PostgreSQL data under ``data/postgres`` and application data
under ``data/cache``, ``data/diagnostics``, ``data/exports``, and ``logs``.
Back up the PostgreSQL volume with the database's normal dump tools and retain
exports/diagnostics separately. Do not commit these directories or real
browser artifacts.

Deployment boundaries
=====================

The API and UI bind to loopback by default; the MCP gateway also requires a
token. Keep all published ports private or place them behind an authenticated
reverse proxy. Override ``SERPSCRAP_API_BIND``, ``SERPSCRAP_UI_BIND``,
``SERPSCRAP_MCP_BIND``, or ``SEARXNG_BIND`` only when the network boundary is
intentional.
