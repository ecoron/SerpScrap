=======
Install
=======

SerpScrap requires Python >= 3.9 and Google Chrome (with chromedriver). The recommended way to manage dependencies is with pipenv.

.. code-block:: bash

   pip install pipenv
   pipenv install

On Linux, you must have Google Chrome installed. The provided script at scripts/install_chrome.sh can be used to install Chrome and its dependencies in Docker or on a fresh system:

.. code-block:: bash

   sh scripts/install_chrome.sh

Chromedriver is managed automatically by SerpScrap using chromedriver-autoinstaller.

Chrome headless is required
---------------------------

SerpScrap only supports headless Chrome. Other browsers (e.g., PhantomJS, Firefox) are not supported.

lxml
----

lxml is required and will be installed automatically with pipenv. On Windows, you may need the lxml binary from: http://www.lfd.uci.edu/~gohlke/pythonlibs/

In some cases, you may also need to install Microsoft Visual C++ Build Tools.

iOS
===
Not supported.

CLI encoding issues
-------------------

To avoid encoding issues in the Windows CLI, use:

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8

References
==========

.. target-notes::

.. _`lxml`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
.. _`Microsoft Visual C++ Build Tools`: http://landinghub.visualstudio.com/visual-cpp-build-tools
