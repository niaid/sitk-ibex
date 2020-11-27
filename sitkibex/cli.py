#
#  Copyright Bradley Lowekamp
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0.txt
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
""" Provides command line interfaces for sitkibex registration algorithms"""

import sitkibex.globals
import os
from os.path import basename
import SimpleITK as sitk
import click
import itertools
import logging

import sitkibex.registration_utilities as utils


class _Bunch(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


@click.group()
@click.option('--debug', 'logging_level', flag_value=logging.DEBUG,
              help="Maximum verbosity with debugging logging enabled.")
@click.option('-v', '--verbose', 'logging_level', flag_value=logging.INFO, default=True,
              help="Increased verbosity with information logging enabled.")
@click.option('-q', '--quiet', 'logging_level', flag_value=logging.WARNING,
              help="Minimal verbosity with only warning logging enabled.")
def cli(**kwargs):

    args = _Bunch(kwargs)

    logging.basicConfig(level=args.logging_level,
                        format='%(message)s')

    if "SITK_SHOW_EXTENSION" not in os.environ:
        os.environ["SITK_SHOW_EXTENSION"] = ".nrrd"


@cli.command(name="registration")
@click.option('-b', '--bin', default=1, type=int, show_default=True,
              help="Reduce the resolution of the input images in X and Y by this factor")
@click.option('-s', '--sigma', default=1.0, type=float, show_default=True)
@click.option('--affine/--no-affine',  default=False,
              help="Do affine registration in a second step.")
@click.option('--automask/--no-automask', default=False, show_default=True,
              help="Automatically compute a mask for the non-zero pixels of the input images")
@click.option('--ignore-spacing/--no-ignore-spacing', default=True, show_default=True,
              help="Ignore the magnitude of spacing, but preserve relative ratio.")
@click.option('--random/--no-random', default=False, show_default=True,
              help="Use wall-clock instead of a fixed seed for random initialization.")
@click.option('--samples-per-parameter', default=5000, type=int, show_default=True)
@click.argument('fixed_image',
                type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('moving_image',
                type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('output_transform',
                type=click.Path(exists=False, resolve_path=True))
def reg_cli(fixed_image, moving_image, output_transform, **kwargs):
    """Perform registration to solve for an OUTPUT_TRANSFORM mapping points from the FIXED_IMAGE to the MOVING_IMAGE."""
    global default_random_seed
    from sitkibex.registration import registration

    args = _Bunch(kwargs)

    if args.random:
        sitkibex.globals.default_random_seed = sitk.sitkWallClock

    fixed_image = sitk.BinShrink(sitk.ReadImage(fixed_image, sitk.sitkFloat32), [args.bin, args.bin, 1])
    moving_image = sitk.BinShrink(sitk.ReadImage(moving_image, sitk.sitkFloat32), [args.bin, args.bin, 1])

    tx = registration(fixed_image, moving_image,
                      sigma=args.sigma,
                      do_affine3d=args.affine,
                      auto_mask=args.automask,
                      ignore_spacing=args.ignore_spacing,
                      samples_per_parameter=args.samples_per_parameter)

    sitk.WriteTransform(tx, output_transform)


@cli.command(name="resample")
@click.option('-b', '--bin', default=1, type=int, show_default=True,
              help="Reduce the resolution of the input images in X and Y by this factor")
@click.option('--fusion/--no-fusion',  default=False, show_default=True,
              help="Blend fixed and moving images into RGB")
@click.option('--combine/--no-combine',  default=False, show_default=True,
              help="Combine fixed and moving images into multi-component")
@click.option('--invert/--no-invert', default=False, show_default=True,
              help="invert the transform")
@click.option('--projection/--no-projection', default=False, show_default=True,
              help="project the volume in the z-direction to create 2-d image")
@click.option('-o', '--output', default=None,
              help="filename for output image, if not provided the SimpleITK Show method is called",
              type=click.Path(exists=False, resolve_path=True))
@click.argument('fixed_image',
                type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('moving_image',
                type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('transform',
                required=False,
                type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def resample_cli(fixed_image, moving_image, transform, **kwargs):
    """Create new image by transforming the MOVING_IMAGE onto the FIXED_IMAGE.

    Apply the TRANSFORM results from registration to resample the MOVING_IMAGE onto the coordinate space defined by the
    MOVING_IMAGE.

    To apply the results of registration:

    >>> sitkibex resample -o fixed_onto_moving.nrrd fixed.nrrd moving.nrrd out.txt

    Additional options can produce a small 2D RGB image to quickly review registration results. For example:

    >>> sitkibex resample --bin 10 --fusion --projection -o preview.png fixed.nrrd moving.nrrd out.txt

    If the moving image has more than 3 dimensions each sub-3d volume will be iteratively resampled.

    """

    from .resample import resample

    args = _Bunch(kwargs)

    @utils.sub_volume_execute()
    def binner(image):
        if args.bin != 1:
            return sitk.BinShrink(image, [args.bin, args.bin, 1])
        else:
            return image

    moving_img = binner(sitk.ReadImage(moving_image))

    reader = sitk.ImageFileReader()
    reader.SetFileName(fixed_image)
    reader.ReadImageInformation()
    if reader.GetDimension() > 3:
        extract_size = reader.GetSize()
        extract_size[3:] = itertools.repeat(0, len(extract_size) - 3)
        reader.SetExtractSize(extract_size)

    fixed_img = binner(reader.Execute())

    tx = None
    if transform:
        tx = sitk.ReadTransform(transform)

    @utils.sub_volume_execute(inplace=True)
    def resample_sub_volume(mv_img):
        return resample(fixed_img, mv_img, tx,
                        fusion=args.fusion,
                        combine=args.combine,
                        invert=args.invert,
                        projection=args.projection)

    result = resample_sub_volume(moving_img)

    if args.output:
        sitk.WriteImage(result, args.output)
    else:
        sitk.Show(result, title="Resampling of {}".format(basename(fixed_image)))
