===========
Development
===========

This guide is for contributors extending the Python package, CLI, API, UI,
MCP gateway, provider plugins, and Docker deployment. Operators should start
with :doc:`docker`; MCP client authors should start with :doc:`mcp`.

Repository layout
=================

* ``serpscrap/`` contains the public API, configuration, application services,
  API server, MCP gateway, models, persistence, and plugin registry.
* ``scrapcore/`` contains browser setup and lower-level scraping integration.
* ``tests/`` contains deterministic unit, service, parser, fixture, and layout
  tests. Browser/network checks are explicitly marked and opt-in.
* ``docker/`` contains one shared runtime Dockerfile and the Compose file.
* ``ui/`` contains the Flask application, Jinja templates, modular CSS, and
  browser ES modules for the dynamic UI.
* ``docs/`` contains the user and developer documentation.

Local environment
=================

The supported development workflow uses Pipenv from the repository root:

.. code-block:: bash

   pipenv install --dev
   pipenv run python -m pip install -e .

The project targets Python 3.10 or newer. Documentation dependencies are in
``docs/requirements.txt``.

Validation
==========

Run the deterministic checks before submitting changes:

.. code-block:: bash

   pipenv run python -m ruff check serpscrap scrapcore tests
   pipenv run python -m pytest -m "not browser"
   pipenv run python -m build --no-isolation
   pipenv run python -m sphinx -W --keep-going -b html docs docs/_build/html

Run the complete application locally with Docker Compose so the Flask UI can
reach the API and PostgreSQL database through the internal network:

.. code-block:: bash

   docker compose -f docker/compose.yml up --build

The UI is served at ``http://localhost:8080``. The UI does not connect to
PostgreSQL directly; its same-origin ``/api`` proxy calls the shared API, and
the API persists searches, results, failures, configuration, and analytics in
PostgreSQL. Running only the UI process without the API service results in an
empty/non-functional workspace by design.

The browser smoke test requires Chrome and network access:

.. code-block:: bash

   SERPSCRAP_RUN_BROWSER=1 pipenv run python -m pytest -m browser

Architecture
============

The public ``SerpScrap`` facade creates validated requests. The application
service runs configured plugins through shared browser, retry, normalization,
fusion, history, and diagnostic contracts. The HTTP API and MCP gateway call
the same service and must not duplicate scraping or persistence logic.

Provider changes require a stable plugin ID, URL/interaction contract,
sanitized fixture, parser tests, failure-state tests, and updated metadata.
Provider-specific selectors stay in the provider registry; shared flow code
must remain provider-neutral.

Documentation changes
=====================

Keep user instructions current with the actual CLI help, public Python method
signatures, Compose ports, and MCP tool schemas. The historical implementation
plan is kept separately from these user-facing pages.

UI search-result contract
=========================

The search workspace keeps the active run ID as its source of truth. Polling
awaits each status update and, when a run reaches ``completed`` or ``failed``,
refreshes the current results before refreshing overview/history metrics. The
results endpoint is not restricted to ``kind=organic`` so image, news,
shopping, and video runs remain visible.

Each normalized result is grouped by canonical URL within its selected run.
Rows expose result type, relevance, contributing engines, and a ``Details``
action. The detail panel displays title, snippet, source engine, relevance,
and destination URL for live and historical runs.

The UI uses compact result cards with the title, domain, URL, snippet, result
type, relevance, and engine coverage visible in the listing. Desktop layouts
use a two-column master-detail workspace: only the result list scrolls while
the selected-result panel remains visible. At narrow widths the columns stack
and the detail panel becomes part of the normal mobile flow.

History inspection is rendered as an expandable row directly below the
selected search run. The archive list remains the primary navigation surface,
while the selected run's result cards and detail panel stay visually attached
to that row.

Advanced search options are opened through the settings control beside the
global search field. A global search query such as ``/search?q=research`` is
copied into the search form and submitted automatically after configuration
loads, so users do not need to press a second search button.

The same-origin UI proxy must preserve the incoming query string when
forwarding API requests. In particular, ``run_id`` is required for historical
results; dropping it causes the API to return the most recent results instead
of the selected run.
