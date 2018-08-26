=======
Install
=======

.. code-block:: python

   pip uninstall SerpScrap -y
   pip install SerpScrap --upgrade

On the first run SerpScrap will try to install the required Chromedriver or PhantomJS binary on Windows and Linux instances.
If self install doesnt work you can configure your custom path to the chromedriver or phantomjs binary.
For Linux SerpScrap provides https://github.com/ecoron/SerpScrap/blob/master/install_chrome.sh, this should be executed automaticly on the first run.

Chrome headless is recommended
------------------------------

By default SerpScrap is using the headless Chrome.
You can also use phantomJS, but it is deprecated and it is also blocked very fast by the searchengine.
We recommend to use headless Chrome.

lxml
----

lxml is required.

Windows
=======
for windows you may need the lxml binary form here: http://www.lfd.uci.edu/~gohlke/pythonlibs/
For your convenience here are the direct links:
* `lxml`_

In some cases you may need also `Microsoft Visual C++ Build Tools`_ installed.

iOS
===
is not supported yet


cli encoding issues
-------------------

To avoid encode/decode issues use this command before you start using SerpScrap in your cli.

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8


References
==========

.. target-notes::

.. _`lxml`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
.. _`Microsoft Visual C++ Build Tools`: http://landinghub.visualstudio.com/visual-cpp-build-tools
