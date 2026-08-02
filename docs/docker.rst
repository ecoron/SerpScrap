==================
Docker application
==================

The Compose deployment runs the complete Version 2 alpha application:

* ``serpscrap-db`` stores runs, results, failures, and history in PostgreSQL.
* ``serpscrap-app`` provides the API and executes browser searches.
* ``serpscrap-ui`` provides the operator web interface.
* ``serpscrap-mcp`` provides the MCP-compatible JSON-RPC gateway.

The current project version is **2.0.0-alpha.1**. It is an evaluation release;
pin the image tag or Git revision used in repeatable deployments.

Quick start
===========

From the repository root:

.. code-block:: bash

   mkdir -p data/postgres data/cache data/diagnostics data/exports logs
   docker compose -f docker/compose.yml up --build

Open the UI at ``http://localhost:8080``. The API is at
``http://localhost:8000/api/v1`` and the MCP gateway is at
``http://localhost:8001``.

To build and run only the CLI image:

.. code-block:: bash

   docker build --file docker/app/Dockerfile -t serpscrap:2.0.0-alpha.1 .
   docker run --rm serpscrap:2.0.0-alpha.1 search \
     --keyword "example keyword" --pages 1 --no-history

Configuration
=============

Set deployment values in an environment file or the shell before starting
Compose. The database password must be changed outside local development:

.. code-block:: bash

   $env:POSTGRES_PASSWORD = "use-a-secret-value"  # PowerShell
   docker compose -f docker/compose.yml up -d

Important variables include ``POSTGRES_DB``, ``POSTGRES_USER``,
``POSTGRES_PASSWORD``, ``SERPSCRAP_MAX_ACTIVE_JOBS``, and
``SERPSCRAP_MAX_QUEUED_JOBS``. The MCP service uses ``SERPSCRAP_API_URL``
internally; see :doc:`mcp` for client usage.

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

The API and MCP gateway currently have no authentication layer. Keep ports
private or place them behind an authenticated reverse proxy. The MCP
configuration tools can change persisted engine selection, so expose port
8001 only to trusted clients.
