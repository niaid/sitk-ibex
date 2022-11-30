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
import SimpleITK as sitk
import logging

_logger = logging.getLogger(__name__)


def spacing_average_magnitude(image):
    """
    Compute the log_10 magnitude to the image spacing should be scaled by to be near unit size.

    :param image: Input return.
    :return: a floating point number representing the magnitude
    """
    from math import log10

    average_spacing = sum(image.GetSpacing()) / float(image.GetDimension())
    return pow(10, round(log10(average_spacing)))


def project(image_3d, projection_func=sitk.MeanProjection):
    """ "
    Do projection from 3D to 2D along z-axis
    The direction cosine matrix is explicitly set to the identity to enable conversion of the 2-D transform back to 3D

    :param image_3d: As 3D SimpleITK Image
    :param projection_func: A SimpleITK function from the "Projection" family
    :return:
    """
    dim = 2
    size_2d = image_3d.GetSize()[:2] + (0,)

    projected_image = projection_func(image_3d, projectionDimension=dim)
    return sitk.Extract(
        projected_image, size=size_2d, directionCollapseToStrategy=sitk.ExtractImageFilter.DIRECTIONCOLLAPSETOIDENTITY
    )


def make_auto_mask(feature_image):
    """
    :param feature_image: a gray scale image
    :return: a binary ( 1's and 0's ) representing a mask of the none-zero pixels in the feature image.
    """
    return sitk.BinaryFillhole(feature_image != 0)


def fft_initialization(moving, fixed, bin_shrink=8, projection=True):
    """

    :param moving:
    :param fixed:
    :return:
    """

    if projection:
        moving = project(moving)
        fixed = project(fixed)

    try:
        moving + fixed
    except RuntimeError:
        # The addition operator will throw an exception of the images don't occupy the same space like the
        # MaskedFFTNormalizedCorrelation filter. If an exception is thrown resample onto the fixed image with the
        # identity transform. With the 3d->2d projection already making the direction matrix identity, only the origin,
        # spacing will be considered. Additionally, moth images will be the same number of pixels as required.
        resampler = sitk.ResampleImageFilter()
        resampler.SetReferenceImage(fixed)
        moving = resampler.Execute(moving)

    fraction_overlap = 0.5
    sigma = bin_shrink * fixed.GetSpacing()[0]
    pixel_type = sitk.sitkFloat32
    bin_shrink_list = [bin_shrink] * 2
    if moving.GetDimension() == 3:
        bin_shrink_list += [1]

    fft_moving = sitk.Cast(sitk.SmoothingRecursiveGaussian(sitk.BinShrink(moving, bin_shrink_list), sigma), pixel_type)
    fft_fixed = sitk.Cast(sitk.SmoothingRecursiveGaussian(sitk.BinShrink(fixed, bin_shrink_list), sigma), pixel_type)

    _logger.info("FFT Correlation...")
    out = sitk.MaskedFFTNormalizedCorrelation(
        fft_fixed,
        fft_moving,
        sitk.Cast(fft_fixed != 0, pixel_type),
        sitk.Cast(fft_moving != 0, pixel_type),
        requiredFractionOfOverlappingPixels=fraction_overlap,
    )

    _logger.info("Smoothing...")
    out = sitk.SmoothingRecursiveGaussian(out)
    _logger.info("Detecting peak...")
    _logger.info("\tConnected components and maxima...")
    cc = sitk.ConnectedComponent(sitk.RegionalMaxima(out, fullyConnected=True))
    _logger.info("\tLabel statistics...")
    stats = sitk.LabelStatisticsImageFilter()
    stats.Execute(out, cc)
    labels = sorted(stats.GetLabels(), key=lambda l_id: stats.GetMean(l_id))

    peak_idx = stats.GetBoundingBox(labels[-1])[::2]
    peak_idx = [i + 0.5 for i in peak_idx]
    peak_pt = out.TransformContinuousIndexToPhysicalPoint(peak_idx)
    peak_value = stats.GetMean(labels[-1])

    center_pt = out.TransformContinuousIndexToPhysicalPoint([p / 2.0 for p in out.GetSize()])

    translation = [c - p for c, p in zip(center_pt, peak_pt)]
    translation += [0] * (moving.GetDimension() - len(translation))

    _logger.info("FFT peak correlation of {0} at translation of {1}".format(peak_value, translation))

    return translation
