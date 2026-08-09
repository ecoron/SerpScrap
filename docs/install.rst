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

Consent and live provider smoke tests
--------------------------------------

Google and Ecosia consent is handled through visible, provider-scoped browser
controls. A successful ``consent_cleared`` event only proves that the visible
overlay is gone; it does not guarantee that the provider will allow a later
SERP request. Google ``/sorry`` pages and Ecosia challenge pages are reported
as typed ``blocked`` outcomes and are not bypassed or retried as consent.

For a local Pipenv smoke run, Chrome and ChromeDriver must be available. With
Selenium Manager enabled, the first run may download a compatible driver from
the official Chrome-for-Testing source. Controlled environments can instead
provide explicit paths:

.. code-block:: powershell

   $env:SERPSCRAP_CHROME_BINARY = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
   $env:SERPSCRAP_CHROMEDRIVER = 'C:\tools\chromedriver.exe'
   pipenv run python -m pytest -m browser

Live runs are low-volume and opt-in. Do not commit browser profiles, cookies,
local storage, raw provider pages, or query-bearing diagnostic artifacts.
For repeated consent diagnostics, set ``SERPSCRAP_CHROME_PROFILE_DIR`` to a
dedicated disposable directory. To compare headless and visible execution,
use the existing CLI ``--visible`` option with the same network and profile
conditions; this is a diagnostic comparison, not an access-control bypass.
The default ``interaction_settle_delay`` only synchronizes the rendered form
before submission. It is intentionally bounded and does not attempt to hide
WebDriver automation signals.

iOS is not supported.
