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
* ``docker/`` contains the app, UI, MCP Dockerfiles and Compose file.
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
