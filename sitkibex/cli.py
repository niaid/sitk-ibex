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
import sys
from os.path import basename
import SimpleITK as sitk
import click
import logging
import re
from .io import im_read_channel
import sitkibex.registration_utilities as utils


_logger = logging.getLogger(__name__)


class _Bunch(object):
    def __init__(self, adict):
        self.__dict__.update(adict)


class ImagePathChannel(click.Path):
    """
    A custom click ParamType.

    This class parses channel name suffixes for command line parameters.
    The '@CHANNEL` suffix can be appended to extract one channel. The `CHANNEL` can be a 0-based
    number e.g `@0`, or `Ch` followed by a 1-based index e.g. `@Ch1`, or it can be a string identifier
    for the name of a channel.

    If the channel suffix  is an integer ( or with  "Ch" ), then an integer type is returned for a 1-based channel
    index.


    The converted output returned is a pair of the filename followed by the channel name or integer channel index.

    """

    name = "image_file[@channel]"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):

        m = re.match(r"(.*)@(.*)", value)

        channel_part = None
        if m:
            value = m.groups()[0]
            channel_part = m.groups()[1]

            m = re.match(r"(Ch)?(\d)", channel_part, re.IGNORECASE)
            if m:
                channel_part = int(m.groups()[1])
                # if "Ch" prefix it it 1 based index, so convert
                if m.groups()[0] is not None:
                    channel_part -= 1

        return super().convert(value, param, ctx), channel_part


@click.group()
@click.option(
    "--debug", "logging_level", flag_value=logging.DEBUG, help="Maximum verbosity with debugging logging enabled."
)
@click.option(
    "-v",
    "--verbose",
    "logging_level",
    flag_value=logging.INFO,
    default=True,
    help="Increased verbosity with information logging enabled.",
)
@click.option(
    "-q",
    "--quiet",
    "logging_level",
    flag_value=logging.WARNING,
    help="Minimal verbosity with only warning logging enabled.",
)
def cli(**kwargs):

    args = _Bunch(kwargs)

    # single app logger:
    log = sitkibex.globals.logger
    log.setLevel(args.logging_level)

    # Create handler to set everything at or below INFO to stdout
    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.NOTSET)
    h1.addFilter(lambda record: record.levelno <= logging.INFO)
    h1.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(h1)

    # Warnings and error go to stderr
    h2 = logging.StreamHandler(sys.stderr)
    h2.setLevel(logging.WARNING)
    h2.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    log.addHandler(h2)

    if "SITK_SHOW_EXTENSION" not in os.environ:
        os.environ["SITK_SHOW_EXTENSION"] = ".nrrd"


@cli.command(name="registration")
@click.option(
    "-b",
    "--bin",
    default=1,
    type=int,
    show_default=True,
    help="Reduce the resolution of the input images in X and Y by this factor",
)
@click.option("-s", "--sigma", default=1.0, type=float, show_default=True)
@click.option("--affine/--no-affine", default=False, help="Do affine registration in a second step.")
@click.option(
    "--automask/--no-automask",
    default=False,
    show_default=True,
    help="Automatically compute a mask for the non-zero pixels of the input images",
)
@click.option(
    "--ignore-spacing/--no-ignore-spacing",
    default=True,
    show_default=True,
    help="Ignore the magnitude of spacing, but preserve relative ratio.",
)
@click.option(
    "--random/--no-random",
    default=False,
    show_default=True,
    help="Use wall-clock instead of a fixed seed for random initialization.",
)
@click.option("--samples-per-parameter", default=5000, type=int, show_default=True)
@click.argument("fixed_image", type=ImagePathChannel(exists=True, dir_okay=True, resolve_path=True))
@click.argument("moving_image", type=ImagePathChannel(exists=True, dir_okay=True, resolve_path=True))
@click.argument("output_transform", type=click.Path(exists=False, resolve_path=True))
def reg_cli(fixed_image, moving_image, output_transform, **kwargs):
    """Perform registration to solve for an OUTPUT_TRANSFORM mapping points from the FIXED_IMAGE to the MOVING_IMAGE."""
    from sitkibex.registration import registration

    args = _Bunch(kwargs)

    fixed_image, fixed_channel_name = fixed_image
    moving_image, moving_channel_name = moving_image

    if args.random:
        sitkibex.globals.default_random_seed = sitk.sitkWallClock

    def r(img, channel_name, bin_xy):
        img = im_read_channel(img, channel_name)
        img = sitk.Cast(img, sitk.sitkFloat32)
        if bin != 1:
            img = sitk.BinShrink(img, [bin_xy, bin_xy, 1])
        return img

    fixed_image = r(fixed_image, fixed_channel_name, args.bin)
    moving_image = r(moving_image, moving_channel_name, args.bin)

    tx = registration(
        fixed_image,
        moving_image,
        sigma=args.sigma,
        do_affine3d=args.affine,
        auto_mask=args.automask,
        ignore_spacing=args.ignore_spacing,
        samples_per_parameter=args.samples_per_parameter,
    )

    sitk.WriteTransform(tx, output_transform)


@cli.command(name="resample")
@click.option(
    "-b",
    "--bin",
    default=1,
    type=int,
    show_default=True,
    help="Reduce the resolution of the input images in X and Y by this factor",
)
@click.option("--fusion/--no-fusion", default=False, show_default=True, help="Blend fixed and moving images into RGB")
@click.option(
    "--combine/--no-combine",
    default=False,
    show_default=True,
    help="Combine fixed and moving images into multi-component",
)
@click.option("--invert/--no-invert", default=False, show_default=True, help="invert the transform")
@click.option(
    "--projection/--no-projection",
    default=False,
    show_default=True,
    help="project the volume in the z-direction to create 2-d image",
)
@click.option(
    "-o",
    "--output",
    default=None,
    help="filename for output image, if not provided the SimpleITK Show method is called",
    type=click.Path(exists=False, resolve_path=True),
)
@click.argument("fixed_image", type=ImagePathChannel(exists=True, dir_okay=True, resolve_path=True))
@click.argument("moving_image", type=ImagePathChannel(exists=True, dir_okay=True, resolve_path=True))
@click.argument("transform", required=False, type=click.Path(exists=True, dir_okay=False, resolve_path=True))
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

    moving_image, moving_channel_name = moving_image
    fixed_image, fixed_channel_name = fixed_image

    moving_img = binner(im_read_channel(moving_image, moving_channel_name))

    if fixed_channel_name is None and os.path.isfile(fixed_image):
        reader = sitk.ImageFileReader()
        reader.SetFileName(fixed_image)
        reader.ReadImageInformation()
        if reader.GetDimension() > 3:
            if args.fusion:
                _logger.warning("Automatically selecting first channel with fusion enabled.")
            fixed_channel_name = 0

    fixed_img = im_read_channel(fixed_image, fixed_channel_name)
    fixed_img = binner(fixed_img)

    tx = None
    if transform:
        tx = sitk.ReadTransform(transform)

    @utils.sub_volume_execute(inplace=False)
    def resample_sub_volume(mv_img):
        return resample(
            fixed_img,
            mv_img,
            tx,
            fusion=args.fusion,
            combine=args.combine,
            invert=args.invert,
            projection=args.projection,
        )

    result = resample_sub_volume(moving_img)

    if args.output:
        sitk.WriteImage(result, args.output)
    else:
        sitk.Show(result, title="Resampling of {}".format(basename(fixed_image)))
