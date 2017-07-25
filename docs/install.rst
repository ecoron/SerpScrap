=======
Install
=======

.. code-block:: python

   pip uninstall SerpScrap -y
   pip install SerpScrap --upgrade

On the first run SerpScrap will try to install the required PhantomJS binary on Windows and Linux instances.
If self install doesnt work you can configure your custom path to the phantomjs binary.

In some cases it is required to install python-scipy first

.. code-block:: bash

   sudo apt-get build-dep python-scipy

Requirements Windows
--------------------

for windows some dependecies are provided as binaries for python extension packages.
you can find them under: http://www.lfd.uci.edu/~gohlke/pythonlibs/
For your convenience here are the direct links:

* `lxml`_

maybe you need also `Microsoft Visual C++ Build Tools`_ installed.

cli encoding issues
-------------------

To avoid encode/decode issues use this command before you start using SerpScrap in your cli.

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8


References

.. target-notes::

.. _`Microsoft Visual C++ Build Tools`: http://landinghub.visualstudio.com/visual-cpp-build-tools
.. _`lxml`: http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml