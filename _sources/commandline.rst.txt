Command Line Interface
======================

The SITK-IBEX packages contains a command line executable to running at the command prompt or for batch processing. This
command line interface provides sub-commands. It can be invoke directly as an executable:

.. code-block :: bash

    sitkibex --help

Or the preferred way using the `python` executable to execute the module entry point:

.. code-block :: bash

    python -m sitkibex --help

With either method of invoking the command line interface, the following sections descripts the sub-command available
and the command line options available.

.. click:: sitkibex.cli:cli
   :prog: sitkibex
   :show-nested: