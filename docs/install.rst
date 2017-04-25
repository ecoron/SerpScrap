=======
Install
=======

.. code-block:: python

   pip uninstall SerpScrap -y
   pip install SerpScrap --upgrade

On the first run SerpScrap will try to install the required PhantomJS binary on Windows and Linux instances.
But you can also configure the path to the binary.

Requirements Windows
--------------------

on Windows you might need also `Microsoft Visual C++ Build Tools`_ installed.

* `lxml`_
* `numpy`_
* `scipy`_
* `scikit-learn`_

avoid encode/decode issues by running this command before starting python in your cli

.. code-block:: bash

   chcp 65001
   set PYTHONIOENCODING=utf-8
