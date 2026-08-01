=======
Install
=======

SerpScrap requires Python 3.10 or newer and Google Chrome.

Create a virtual environment and install the package:

.. code-block:: bash

   python -m venv .venv
   .venv/bin/python -m pip install .

On Windows, use ``.venv\Scripts\python`` instead.

ChromeDriver
------------

Selenium Manager locates or downloads a compatible ChromeDriver automatically.
No separate driver installer is required. Controlled or offline environments can
set ``executable_path`` and ``chrome_binary`` explicitly or use the environment
variables ``SERPSCRAP_CHROMEDRIVER`` and ``SERPSCRAP_CHROME_BINARY``.

Development
-----------

Install the exact development dependency set and the local package:

.. code-block:: bash

   python -m pip install -r requirements-dev.lock
   python -m pip install --no-deps -e .
   python -m pytest -m "not browser"

Pipenv remains supported as a development frontend. The editable package in
``Pipfile`` reads its metadata and runtime dependencies from ``pyproject.toml``:

.. code-block:: bash

   pipenv install --dev
   pipenv shell
   pipenv run serpscrap --help

The browser smoke test is opt-in because it requires Chrome and network access:

.. code-block:: bash

   SERPSCRAP_RUN_BROWSER=1 python -m pytest -m browser

iOS is not supported.
