
SITK-IBEX: Aligning images acquired with the IBEX microscopy imaging technique
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This Python package was implemented as part of the development of the
Iterative Bleaching Extends Multiplexity (IBEX) imaging technique. It enables
the alignment of multiple cycles of fluorescence images, acquired
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


Build Status
""""""""""""

.. image:: https://github.com/niaid/sitk-ibex/workflows/Python%20Test%20and%20Package/badge.svg?branch=master&event=push
   :target: https://github.com/niaid/sitk-ibex/actions?query=branch%3A+master+
   :alt: Master Build Status

Installation
------------


The Python module is distributed as a `wheel`_ binary package. Download the latest tagged release from the
`Github Releases`_ page. Then install::

 python -m pip install sitkibex-0.1-py3-none-any.whl

Wheels from the master branch can be download wheel from `Github Actions`_ in the
"python-package" artifact.


Dependencies are conventionally specified in `setup.py` and `requirements.txt` and therefore installed as
dependencies when the wheel is installed. This includes the SimpleITK 2.0 requirement.

Data
----

Sample data is available on zenodo/figshare - link to this.
?Specify links to the sample IBEX data from the manuscript.?

Any image and transform file format supported by `SimpleITK's IO <https://simpleitk.readthedocs.io/en/master/IO.html>`_
can be use by sitk-ibex. The 3D `nrrd` format, and `txt` transform file extension are recommended.

The sample data are in the `OME TIFF`_ format. An individual channel can be saved as `nrrd` with `Fiji`_ by using
"Image->Color->Split Channels" followed by "Save As->Nrrd".

Example
-------

The following examples uses CD4 marker channel extracted from the "IBEX4_spleen" data set with ImageJ. The panel 2 is
used as the reference coordinates or the "fixed image". The other panels are registered then resampled to the fixed
image. The following uses the sitk-ibex command line interface to perform image registration::

 python -m sitkibex registration --affine IBEX4B_Panel2_CD4_AF594.nrrd IBEX4B_Panel1_CD4_AF594.nrrd tx_p2_to_p1.txt
 python -m sitkibex registration --affine IBEX4B_Panel2_CD4_AF594.nrrd IBEX4B_Panel3_CD4_AF594.nrrd tx_p2_to_p3.txt

A quick 2D visualization of the results can be generated with::

 python -m sitkibex resample IBEX4B_Panel2_CD4_AF594.nrrd IBEX4B_Panel1_CD4_AF594.nrrd tx_p2_to_p1.txt \
        --bin 4 --fusion --projection -o IBEX4B_onto_p2_2d_Panel1_CD4_AF594.png
 python -m sitkibex resample IBEX4B_Panel3_CD4_AF594.nrrd IBEX4B_Panel1_CD4_AF594.nrrd tx_p3_to_p1.txt \
        --bin 4 --fusion --projection -o IBEX4B_onto_p2_2d_Panel3_CD4_AF594.png

Then apply the registration transform by resampling the input images onto panel 2::

 python -m sitkibex resample IBEX4B_Panel2_CD4_AF594.nrrd IBEX4B_Panel1_CD4_AF594.nrrd tx_p2_to_p1.txt \
        -o IBEX4B_onto_p2_Panel1_CD4_AF594.nrrd
 python -m sitkibex resample IBEX4B_Panel3_CD4_AF594.nrrd IBEX4B_Panel1_CD4_AF594.nrrd tx_p3_to_p1.txt \
        -o IBEX4B_onto_p2_Panel3_CD4_AF594.nrrd


How to Cite
-----------

If you use the SITK-IBEX package in your work, please cite it as:

 A. J. Radtke, E. Kandov, B. C. Lowekamp et al.,
 "Characterization and deep spatial profiling of the mammalian
 immune system using a highly multi-plexed optical imaging approach".

Documentation
-------------

The published Sphinx documentation is available here: https://niaid.github.io/sitk-ibex/

The master built Sphinx documentation is available for download from
`Github Actions`_ under the build as "sphinx-docs".


Contact
-------

Please use the `GitHub Issues`_ for support and code issues related to the sitk-ibex project.

Additionally, we can be emailed at: bioinformatics@niaid.nih.gov Please include "sitk-ibex" in the subject line.


.. _SimpleITK toolkit: https://simpleitk.org
.. _Fiji: https://fiji.sc
.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _Github Actions: https://github.com/niaid/sitk-ibex/actions?query=branch%3Amaster
.. _OME TIFF: https://docs.openmicroscopy.org/ome-model/latest/ome-tiff/
.. _GitHub Issues:  https://github.com/niaid/sitk-ibex
.. _wheel: https://www.python.org/dev/peps/pep-0427/
.. _Github Releases: https://github.com/niaid/sitk-ibex/releases
