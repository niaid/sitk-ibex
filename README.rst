
SITK-IBEX: Aligning images acquired with the IBEX microscopy imaging technique
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


This Python package was implemented as part of the development of the
Iterative Bleaching Extends Multiplexity (IBEX) imaging technique. It enables
the alignment of multiple panels, low multiplexity fluorescence images, acquired
using IBEX. A repeated marker is used to register all panels to a
selected panel (in the registration nomenclature this is the fixed image).
After registration all panels are resampled onto the fixed image.

While this method was developed for a specific imaging protocol, it will likely
work for other sequential protocols that contain a repeated marker.
The registration approach is implemented using the
`SimpleITK toolkit`_ registration framework.

The key implementation aspects include:

1. Multi-phase based approach with robust initialization.
2. Multi-resolution and point sampling.
3. Affine transformation model.
4. Use of correlation as optimized similarity metric.

Installation
------------

Download wheel from `Github Actions`_ under the latest master build in the
"python-package" artifacts. Then install::

 $ python -m pip install sitkibex-0.0.1-py3-none-any.whl

SITK-IBEX requires SimpleITK version 2.0 which is still under development.
For now, use the `latest`_ development version of SimpleITK::

    $ python -m pip install --upgrade --pre SimpleITK --find-links https://github.com/SimpleITK/SimpleITK/releases/tag/latest

Other dependencies are conventionally specified in `setup.py` and `requirements.txt`.

Data
----
Sample data is available on zenodo/figshare - link to this.
?Specify links to the sample IBEX data from the manuscript.?

You can use any image and transform file format supported
by `SimpleITK's IO <https://simpleitk.readthedocs.io/en/master/IO.html>`_.
We recommend using the 3D `nrrd` format, and `txt` transform file extension.

If your panels are in `OME TIFF`_ format you can readily extract a channel and
save it as a 3D `nrrd` file using `Fiji`_.

Example
-------
Using the downloaded data, run the registration as follows:


How to Cite
-----------

If you use the SITK-IBEX package in your work, please cite it as:

 A. J. Radtke, E. Kandov, B. C. Lowekamp et al.,
 "Characterization and deep spatial profiling of the mammalian
 immune system using a highly multi-plexed optical imaging approach".

Documentation
-------------

Currently, the Sphinx documentation is available for download from
`Github Actions`_ under the latest master build as
"sphinx-docs".


.. _SimpleITK toolkit: https://simpleitk.org
.. _Fiji: https://fiji.sc
.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _Github Actions: https://github.com/niaid/sitk-ibex/actions/runs/140067646
.. _OME TIFF: https://docs.openmicroscopy.org/ome-model/latest/ome-tiff/
.. _latest: https://github.com/SimpleITK/SimpleITK/releases
