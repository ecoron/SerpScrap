=======
Install
=======

.. code-block:: python

   pip uninstall SerpScrap -y
   pip install SerpScrap --upgrade

On the first run SerpScrap will try to install the required PhantomJS binary on Windows and Linux instances.
If self install doesnt work you can configure your custom path to the phantomjs binary.

Chrome headless is recommended
------------------------------
* `Chrome headless`_

execute the install_chrome.sh to use headless chrome. It's recommended by me, because it's working well (phantomJS is blocked very fast).

lxml
----

lxml is required.

Windows
=======
for windows you may need the lxml binary form here: http://www.lfd.uci.edu/~gohlke/pythonlibs/
For your convenience here are the direct links:
* `lxml`_

maybe you need also `Microsoft Visual C++ Build Tools`_ installed.

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

.. target-notes::

.. _`Chrome headless`: https://github.com/ecoron/SerpScrap/blob/master/install_chrome.sh
.. _`Microsoft Visual C++ Build Tools`: http://landinghub.visualstudio.com/visual-cpp-build-tools
.. _`lxml`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml