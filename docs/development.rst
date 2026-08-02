-----------
Development
-----------

This guide is for contributors extending SerpScrap. Docker operators should
use the :doc:`docker` guide instead.

Repository and local setup
==========================

The project is developed in a Pipenv environment. From the repository root:

.. code-block:: bash

   pipenv install --dev
   pipenv run python -m pip install -e .

The main package and service/API code live under ``serpscrap/``; the scraping
core and browser integration live under ``scrapcore/``. Tests are in
``tests/``. Docker integration files are grouped under ``docker/``.

Validation
==========

Run deterministic checks before submitting changes:

.. code-block:: bash

   pipenv run ruff check serpscrap scrapcore tests
   pipenv run pytest -m "not browser"
   pipenv run python -m build --no-isolation
   pipenv run python -m sphinx -W --keep-going -b html docs docs/_build/html

Browser and provider checks are opt-in because they require Chrome and network
access. Keep provider behavior deterministic with fixtures and contract tests.

Architecture and performance
============================

The application service owns scraping and persistence contracts. The UI and
MCP gateway consume those contracts and must not duplicate scraping or history
logic. Keep concurrency, polling, pagination, cache retention, and diagnostic
artifacts bounded. Record reproducible measurements when changing a hot path.

For a local capacity check, keep the workload offline and configure explicit
limits rather than relying on host defaults:

.. code-block:: bash

   $env:SERPSCRAP_MAX_ACTIVE_JOBS = "2"
   $env:SERPSCRAP_MAX_QUEUED_JOBS = "4"
   pipenv run pytest tests/test_phase9_services.py -q

For a focused CPU/memory investigation, use Python's standard profiler around
an offline fixture or fake runner. Do not include live provider traffic in a
repeatable benchmark or CI gate.

See :doc:`refactoring2026` for the active Phase 9 plan and acceptance
criteria.
