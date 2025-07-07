
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

  python -m pip install -r requirements-dev.txt
  python -m pip install --editable .

New contributions must come from pull requests on GitHub. New features should start as local branch with a name
starting with "feature-" followed by a description. After changes, verify flake8 and the tests pass
without warnings or errors::

  python -m flake8
  python -m pytest

Since the repository is internal, the feature branch needs to be
pushed to the *upstream* repository. Next a pull request is made against main, where the CI will automatically run
flake8, pytest and sphinx. When merging the branch with rebased onto the origin, and the feature branch is deleted.
