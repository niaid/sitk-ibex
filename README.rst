
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


The Python module is distributed on `PyPI - The Python Package Index`_. The package can be installed by running:

 python -m pip install sitkibex

Wheels from the master branch can be download wheel from `Github Actions`_ in the
"python-package" artifact.

Dependencies are conventionally specified in `setup.py` and `requirements.txt` and therefore installed as
dependencies when the wheel is installed. This includes the SimpleITK 2.0 requirement.

Data
----

Sample data is available and described on Zenodo:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4304786.svg
   :target: https://doi.org/10.5281/zenodo.4304786

Any image and transform file format supported by `SimpleITK's IO <https://simpleitk.readthedocs.io/en/master/IO.html>`_
can be use by sitk-ibex. The 3D `nrrd` format, and `txt` transform file extension are recommended.


Example
-------

The following examples uses CD4 marker channel extracted from the "IBEX4_spleen" data set with ImageJ. The panel 2 is
used as the reference coordinates or the "fixed image". The other panels are registered then resampled to the fixed
image. The following uses the sitk-ibex command line interface to perform image registration::

 python -m sitkibex registration --affine "spleen_panel2.nrrd@CD4 AF594" "spleen_panel1.nrrd@CD4 AF594" tx_p2_to_p1.txt
 python -m sitkibex registration --affine "spleen_panel2.nrrd@CD4 AF594" "spleen_panel3.nrrd@CD4 AF594" tx_p2_to_p3.txt

A quick 2D visualization of the results can be generated with::

 python -m sitkibex resample "spleen_panel2.nrrd@CD4 AF594" "spleen_panel1.nrrd@CD4 AF594" tx_p2_to_p1.txt \
        --bin 4 --fusion --projection -o spleen_onto_p2_2d_Panel1.png
 python -m sitkibex resample "spleen_panel2.nrrd@CD4 AF594" "spleen_panel3.nrrd@CD4 AF594" tx_p2_to_p3.txt \
        --bin 4 --fusion --projection -o spleen_onto_p2_2d_Panel3.png

The above image fusion renders the fixed image as magenta and the moving as cyan, so when the two are aligned the
results are white.

Then apply the registration transform by resampling all channels of the the input images onto panel 2::

 python -m sitkibex resample "spleen_panel2.nrrd@CD4 AF594" spleen_panel2.nrrd tx_p2_to_p1.txt \
        -o spleen_onto_p2_panel1.nrrd
 python -m sitkibex resample "spleen_panel2.nrrd@CD4 AF594" spleen_panel3.nrrd tx_p2_to_p3.txt \
        -o spleen_onto_p2_panel3.nrrd


How to Cite
-----------

If you use the SITK-IBEX package in your work, please cite us:

 A. J. Radtke, E. F. Kandov, B. C. Lowekamp, E. Speranza, C. Chu,
 A. Gola, N. Thakur, R. Shih, L. Yao, Z. R. Yaniv, R. Beuschel,
 J. Kabat, J. Croteau, J. Davis, J. M. Hernandez, R. N. Germain
 "IBEX - A versatile multi-plex optical imaging approach
 for deep phenotyping and spatial analysis of cells in complex tissues",
 Proc Natl Acad Sci, 117(52):33455-33465, 2020, doi:`10.1073/pnas.2018488117`_.



Documentation
-------------

The published Sphinx documentation is available here: https://niaid.github.io/sitk-ibex/

The master built Sphinx documentation is available for download from
`Github Actions`_ under the build as "sphinx-docs".


Contact
-------

Please use the `GitHub Issues`_ for support and code issues related to the sitk-ibex project.



.. _SimpleITK toolkit: https://simpleitk.org
.. _Fiji: https://fiji.sc
.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _Github Actions: https://github.com/niaid/sitk-ibex/actions?query=branch%3Amaster
.. _NRRD: http://teem.sourceforge.net/nrrd/format.html
.. _GitHub Issues:  https://github.com/niaid/sitk-ibex
.. _wheel: https://www.python.org/dev/peps/pep-0427/
.. _`PyPI - The Python Package Index`: https://pypi.org/project/sitkibex/
.. _Github Releases: https://github.com/niaid/sitk-ibex/releases
.. _10.1073/pnas.2018488117: https://www.pnas.org/doi/10.1073/pnas.2018488117
