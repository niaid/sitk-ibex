
=====================================
Welcome to sitk-ibex's documentation!
=====================================

.. include:: ../README.rst

Command Line Interface Reference
--------------------------------

Documentation for command line usage of the Python module.

.. toctree::
   :maxdepth: 2

   commandline


API Reference
-------------

Documentation for directly using the Python functions.

.. toctree::
   :maxdepth: 2

   api


Development
-----------

The required packages for development are specified in `requirements-dev.txt`. The sitk-ibex project must be install for
it to function properly. Specifically, because semantic versioning is done with `setuptools-scm` it must be installed. To setup for development::

  python -m pip install requirements-dev.txt
  python -m pip install --editable .

After changes are made check that flake8 and the test pass with out warning or errors::

  python -m flake8
  python -m pytest

Pull requests should be made on GitHub for new contributions, where the CI will automatically run flake8 and pytest.