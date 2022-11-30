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
import numpy as np
from .registration_utilities import RegistrationCallbackManager
from . import image_utilities as imgf
import sitkibex.globals
import logging

_logger = logging.getLogger(__name__)


def register_3d(
    fixed_image,
    moving_image,
    initial_transform,
    sigma_base=1.0,
    fixed_image_mask=None,
    moving_image_mask=None,
    number_of_samples_per_parameter=5000,
):
    """Perform multi-resolution 3D registration, with parameters tuned for affine transformation.


    :param fixed_image: a 3D SimpleITK image
    :param moving_image: a 3D SimpleITK image
    :param initial_transform: a SimpleITK transform initialized with center of transform and/or the transformation
     from a previous stage.
    :param sigma_base: scalar to change the amount of Gaussian smoothing performed
    :param fixed_image_mask: (optional) a binary image of non-zeros for pixels to use
    :param moving_image_mask: (optional) a binary image of non-zeros for pixels to use
    :param number_of_samples_per_parameter: Number of sample points per number of transform parameter to use for metric
     evaluation.
    :return:
    """
    use_neighborhood_correlation = False
    scale_factors = [4, 2, 1]

    reg = sitk.ImageRegistrationMethod()

    reg.MetricUseMovingImageGradientFilterOff()
    reg.MetricUseFixedImageGradientFilterOff()

    reg.SetOptimizerAsGradientDescentLineSearch(
        learningRate=1.0,
        numberOfIterations=400,
        convergenceMinimumValue=1e-7,
        convergenceWindowSize=10,
        lineSearchLowerLimit=0,
        lineSearchUpperLimit=1.0,
        lineSearchMaximumIterations=5,
        maximumStepSizeInPhysicalUnits=1.0,
    )

    reg.SetOptimizerScalesFromIndexShift()

    sampling_percentage = (
        initial_transform.GetNumberOfParameters() * number_of_samples_per_parameter / fixed_image.GetNumberOfPixels()
    )

    if fixed_image_mask or moving_image_mask:
        mask = fixed_image_mask
        if moving_image_mask:
            mask = moving_image_mask
        stats = sitk.StatisticsImageFilter()
        stats.Execute(mask != 0)

        _logger.info("Unmasked sampling: {0}".format(sampling_percentage))
        _logger.info("\tmasked percentage: {0}%".format(100 * stats.GetMean()))
        # this scaling assumes that the size in pixels of the mask the the fixed image are about the same
        sampling_percentage /= stats.GetMean()
        # sampling_percentage *= 10

        _logger.info("Adjusted sampling: {0}".format(sampling_percentage))

    if use_neighborhood_correlation:
        neighborhood_radius = 4
        reg.SetMetricAsANTSNeighborhoodCorrelation(radius=neighborhood_radius)
        sampling_percentage *= 0.1
    else:
        reg.SetMetricAsCorrelation()

    sampling_percentage_per_level = [min(0.10, sampling_percentage * f * f) for f in scale_factors]
    _logger.info(
        "Sampling Percentage Per Level: {0} #{1}".format(
            sampling_percentage_per_level,
            [
                p * fixed_image.GetNumberOfPixels() / (f**3)
                for p, f in zip(sampling_percentage_per_level, scale_factors)
            ],
        )
    )

    reg.SetMetricSamplingPercentagePerLevel(sampling_percentage_per_level, sitkibex.globals.default_random_seed)
    reg.SetMetricSamplingStrategy(reg.REGULAR)
    reg.SetShrinkFactorsPerLevel([f for f in scale_factors])
    reg.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    smoothing_sigmas = [2.0 * sigma_base * f * fixed_image.GetSpacing()[0] for f in scale_factors]
    reg.SetSmoothingSigmasPerLevel(smoothing_sigmas)
    _logger.info("SmoothingSigmasPerLevel: {}".format(smoothing_sigmas))

    reg.SetInterpolator(sitk.sitkLinear)

    if moving_image_mask:
        reg.SetMetricMovingMask(moving_image_mask)

    if fixed_image_mask:
        reg.SetMetricFixedMask(fixed_image_mask)

    reg.SetInitialTransform(initial_transform)

    reg_callbacks = RegistrationCallbackManager(reg)
    reg_callbacks.add_command_callbacks(print_position=True)

    return reg.Execute(fixed_image, moving_image)


def register_as_2d_affine(
    fixed_image,
    moving_image,
    sigma_base=1.0,
    initial_translation=None,
    fixed_image_mask=None,
    moving_image_mask=None,
    number_of_samples_per_parameter=5000,
):
    """Perform 2D registration from 3D image projected in the z-direction.

    The fixed_image and moving_image are first projected along the z-dimension to generate 2D images. Then a
    transform to map points from the fixed_image to the moving_image is optimized for normalized
    correlation metric. First a Euler2D transform is optimized, then a 2D Affine.

    :param fixed_image: a 3D SimpleITK Image class
    :param moving_image: a 3D SimpelITK Image class
    :param sigma_base: scalar to change the amount of Gaussian smoothing performed
    :param initial_translation: (optional) initial translation for fixed points to map to moving.
    :param fixed_image_mask: (optional) a binary image of non-zeros for pixels to use
    :param moving_image_mask: (optional) a binary image of non-zeros for pixels to use
    :param number_of_samples_per_parameter: Number of sample points per number of transform parameter to use for metric
     evaluation.
    :return: a 3D SimpleITK AffineTransform mapping points from the fixed_image to the moving_image
    """

    do_affine = True
    verbose = True

    _logger.info("Initializing projected registration...")
    _logger.info("Sigma Base: {0}".format(sigma_base))

    fixed_2d = imgf.project(fixed_image)
    moving_2d = imgf.project(moving_image)

    if fixed_image_mask:
        fixed_mask_2d = imgf.project(fixed_image_mask, projection_func=sitk.MedianProjection)
    else:
        fixed_mask_2d = None

    if moving_image_mask:
        moving_mask_2d = imgf.project(moving_image_mask, projection_func=sitk.MedianProjection)
    else:
        moving_mask_2d = None

    # Initialize the center of transform and align the center of the volumes.
    # - Use Euler transform
    #

    initial_rigid = sitk.CenteredTransformInitializer(
        fixed_2d, moving_2d, sitk.Euler2DTransform(), sitk.CenteredTransformInitializerFilter.GEOMETRY
    )

    if initial_translation:
        initial_rigid = sitk.Euler2DTransform(initial_rigid)
        initial_rigid.SetTranslation(initial_translation)

    #
    # Setup Multi-scale 2D Multi-scale registration
    #
    R = sitk.ImageRegistrationMethod()

    R.SetMetricAsCorrelation()

    # Due to the sparse sampling the gradient on the whole image
    # is not needed, and it is more time efficient not to compute.
    R.MetricUseMovingImageGradientFilterOff()
    R.MetricUseFixedImageGradientFilterOff()

    R.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=500,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10,
        maximumStepSizeInPhysicalUnits=2.0,
    )

    R.SetOptimizerScalesFromIndexShift()

    scale_factors = [16, 8, 4]
    # We don't need more samples for larger image, so base the number of samples on the number of parameters
    sampling_percentage = (
        len(initial_rigid.GetParameters()) * number_of_samples_per_parameter / fixed_2d.GetNumberOfPixels()
    )
    R.SetMetricSamplingPercentagePerLevel(
        [min(0.10, sampling_percentage) for f in scale_factors], sitkibex.globals.default_random_seed
    )
    R.SetMetricSamplingStrategy(R.REGULAR)
    R.SetShrinkFactorsPerLevel([1 for f in scale_factors])
    R.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    R.SetSmoothingSigmasPerLevel([4.0 * sigma_base * f * fixed_2d.GetSpacing()[0] for f in scale_factors])

    R.SetInitialTransform(initial_rigid)
    R.SetInterpolator(sitk.sitkLinear)

    if fixed_mask_2d:
        _logger.info("Setting fixed mask")
        R.SetMetricFixedMask(fixed_mask_2d)

    if moving_mask_2d:
        _logger.info("Setting moving mask")
        R.SetMetricMovingMask(moving_mask_2d)

    R_callbacks = RegistrationCallbackManager(R)
    R_callbacks.add_command_callbacks(print_position=True, verbose=verbose)

    # R.DebugOn()

    rigid_result_2d = R.Execute(fixed_2d, moving_2d)

    # Perform a deep copy of the transform to convert a sitk.Transform to the actual Euler type
    rigid_result_2d = sitk.Euler2DTransform(rigid_result_2d)

    # Promote Euler to 2D Affine
    affine = sitk.AffineTransform(2)
    affine.SetMatrix(rigid_result_2d.GetMatrix())
    affine.SetTranslation(rigid_result_2d.GetTranslation())
    affine.SetCenter(rigid_result_2d.GetCenter())

    #
    # Setup Multi-Scale 2D Affine registration
    #
    R2 = sitk.ImageRegistrationMethod()
    R2.SetMetricAsCorrelation()
    R2.MetricUseMovingImageGradientFilterOff()
    R2.MetricUseFixedImageGradientFilterOff()
    R2.SetOptimizerAsGradientDescentLineSearch(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10,
        lineSearchLowerLimit=0,
        lineSearchUpperLimit=2.0,
        lineSearchMaximumIterations=5,
        maximumStepSizeInPhysicalUnits=2,
    )

    R2.SetOptimizerScalesFromIndexShift()

    scale_factors = [8, 4, 2]
    sampling_percentage = len(affine.GetParameters()) * number_of_samples_per_parameter / fixed_2d.GetNumberOfPixels()
    R2.SetMetricSamplingPercentagePerLevel(
        [min(0.10, sampling_percentage * f) for f in scale_factors], sitkibex.globals.default_random_seed
    )
    R2.SetMetricSamplingStrategy(R.RANDOM)
    R2.SetShrinkFactorsPerLevel([f for f in scale_factors])
    R2.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    R2.SetSmoothingSigmasPerLevel([sigma_base * f * fixed_2d.GetSpacing()[0] for f in scale_factors])

    R2.SetInitialTransform(affine)
    R2.SetInterpolator(sitk.sitkLinear)

    R2_callbacks = RegistrationCallbackManager(R2)
    R2_callbacks.add_command_callbacks(print_position=True, verbose=verbose)

    if do_affine:
        affine_result = R2.Execute(fixed_2d, moving_2d)
    else:
        affine_result = affine

    # Do explicit casting
    affine_result = sitk.AffineTransform(affine_result)

    #
    # Convert 2d matrix into 3d
    #
    matrix_3d = np.identity(3)
    matrix_3d[:2, :2] = np.asarray(affine_result.GetMatrix()).reshape(2, 2)

    idx_2d = moving_2d.TransformPhysicalPointToContinuousIndex(affine_result.GetCenter())
    idx_3d = idx_2d + (moving_image.GetSize()[2] / 2.0,)
    center_3d = moving_image.TransformContinuousIndexToPhysicalPoint(idx_3d)

    # The 2d projected images preserve the image spacing but have the direction matrix set to the identity.
    _logger.info("center 2d->3d: {0}->{1}".format(affine_result.GetCenter(), center_3d))

    result_3d = sitk.AffineTransform(3)
    result_3d.SetTranslation(affine_result.GetTranslation() + (0,))
    result_3d.SetMatrix(matrix_3d.flatten())
    result_3d.SetCenter(center_3d)

    return result_3d


def registration(
    fixed_image: sitk.Image,  # noqa: C901
    moving_image: sitk.Image,
    *,
    do_fft_initialization=True,
    do_affine2d=False,
    do_affine3d=True,
    ignore_spacing=True,
    sigma=1.0,
    auto_mask=False,
    samples_per_parameter=5000,
    expand=None
) -> sitk.Transform:
    """Robust multi-phase registration for multi-panel confocal microscopy images.

    The fixed and moving image are expected to be the same molecular labeling, and the same imaged regioned.

    The phase available are:
      - fft initialization for translation estimation
      - 2D affine which can correct rotational acquisition problems, this phase is done on z-projections to optimize a \
       2D similarity transform followed by 2D affine
      - 3D affine robust mulit-level registration


    :param fixed_image: a scalar SimpleITK 3D Image
    :param moving_image: a scalar SimpleITK 3D Image
    :param do_fft_initialization: perform FFT based cross correlation for initialize translation
    :param do_affine2d: perform registration on 2D images from z-projection
    :param do_affine3d: multi-level affine transform
    :param ignore_spacing: internally adjust spacing magnitude to be near 1 to avoid numeric stability issues with \
    micro sized spacing
    :param sigma: scalar to change the amount of Gaussian smoothing performed
    :param auto_mask: ignore zero valued pixels connected to the image boarder
    :param samples_per_parameter: the number of image samples to used per transform parameter at full resolution
    :param expand: Perform super-sampling to increase number of z-slices by an integer factor. Super-sampling is \
    automatically performed when the number of z-slices is less than 5.
    :return: A SimpleITK transform mapping points from the fixed image to the moving. This may be a CompositeTransform.

    """
    # Identity transform will be returned if all registration steps are disabled by
    # the calling function.
    result = sitk.Transform()

    initial_translation_3d = True

    moving_mask = None
    fixed_mask = None

    number_of_samples_per_parameter = samples_per_parameter

    expand_factors = None

    if expand:
        expand_factors = [1, 1, expand]

    if fixed_image.GetPixelID() != sitk.sitkFloat32:
        fixed_image = sitk.Cast(fixed_image, sitk.sitkFloat32)

    # expand the image if at least 5 in any dimension
    if not expand_factors:
        expand_factors = [-(-5 // s) for s in fixed_image.GetSize()]

    if any([e != 1 for e in expand_factors]):
        _logger.warning(
            "Fixed image under sized in at lease one dimension!"
            "\tApplying expand factors {0} to image size.".format(expand_factors)
        )
        fixed_image = sitk.Expand(fixed_image, expandFactors=expand_factors)

    if moving_image.GetPixelID() != sitk.sitkFloat32:
        moving_image = sitk.Cast(moving_image, sitk.sitkFloat32)

    expand_factors = [-(-5 // s) for s in moving_image.GetSize()]
    if any([e != 1 for e in expand_factors]):
        _logger.warning(
            "WARNING: Moving image under sized in at lease one dimension!"
            "\tApplying expand factors {0} to image size.".format(expand_factors)
        )
        moving_image = sitk.Expand(moving_image, expandFactors=expand_factors)

    if auto_mask:
        fixed_mask = imgf.make_auto_mask(fixed_image)
        moving_mask = imgf.make_auto_mask(moving_image)

    if ignore_spacing:

        #
        # FORCE THE SPACING magnitude to be normalized near 1.0
        #

        spacing_magnitude = imgf.spacing_average_magnitude(fixed_image)

        _logger.info("Adjusting image spacing by {0}...".format(1.0 / spacing_magnitude))

        new_spacing = [s / spacing_magnitude for s in fixed_image.GetSpacing()]
        _logger.info("\tFixed Image Spacing: {0}->{1}".format(fixed_image.GetSpacing(), new_spacing))
        fixed_image.SetSpacing(new_spacing)
        fixed_image.SetOrigin([o / spacing_magnitude for o in fixed_image.GetOrigin()])

        new_spacing = [s / spacing_magnitude for s in moving_image.GetSpacing()]
        _logger.info("\tMoving Image Spacing: {0}->{1}".format(moving_image.GetSpacing(), new_spacing))
        moving_image.SetSpacing(new_spacing)
        moving_image.SetOrigin([o / spacing_magnitude for o in moving_image.GetOrigin()])

        if moving_mask:
            moving_mask.SetSpacing(new_spacing)
            moving_mask.SetOrigin([o / spacing_magnitude for o in moving_mask.GetOrigin()])

        if fixed_mask:
            fixed_mask.SetSpacing(new_spacing)
            fixed_mask.SetOrigin([o / spacing_magnitude for o in fixed_mask.GetOrigin()])

    #
    #
    # Do FFT based translation initialization
    #
    #
    initial_translation = None
    if do_fft_initialization:
        initial_translation = imgf.fft_initialization(
            moving_image, fixed_image, bin_shrink=8, projection=(not initial_translation_3d)
        )
        result = sitk.TranslationTransform(len(initial_translation), initial_translation)

    #
    # Do 2D registration first
    #
    if do_affine2d:
        result = register_as_2d_affine(
            fixed_image,
            moving_image,
            sigma_base=sigma,
            initial_translation=initial_translation,
            fixed_image_mask=fixed_mask,
            moving_image_mask=moving_mask,
        )

    if do_affine3d:

        _logger.info("Initializing Affine Registration...")

        if do_affine2d:
            # set the FFT xcoor initial z translation
            if do_fft_initialization and len(initial_translation) >= 3:

                # take the z-translation from the FFT
                translation = list(result.GetTranslation())
                translation[2] = initial_translation[2]
                result.SetTranslation(translation)

                _logger.info("Initialized 3D affine with z-translation... {0}".format(translation))

            affine = result
        else:
            affine = sitk.CenteredTransformInitializer(
                fixed_image, moving_image, sitk.AffineTransform(3), sitk.CenteredTransformInitializerFilter.GEOMETRY
            )
            affine = sitk.AffineTransform(affine)

            if do_fft_initialization:
                if len(initial_translation) >= 3:
                    affine.SetTranslation(list(initial_translation))
                    _logger.info("Initialized 3D affine with z-translation... {0}".format(initial_translation))
                else:
                    affine.SetTranslation(
                        list(initial_translation)
                        + [
                            0,
                        ]
                    )

        affine_result = register_3d(
            fixed_image,
            moving_image,
            initial_transform=affine,
            sigma_base=sigma,
            fixed_image_mask=fixed_mask,
            moving_image_mask=moving_mask,
            number_of_samples_per_parameter=number_of_samples_per_parameter,
        )

        result = affine_result

    if ignore_spacing:

        # Compose the scaling Transform into a single affine transform

        # The spacing of the image was modified to do registration, so we need to apply the appropriate scaling to
        # transform to the space the registration was done in.r

        scale = spacing_magnitude

        scale_transform = sitk.ScaleTransform(3)
        scale_transform.SetScale([scale] * 3)

        result = sitk.CompositeTransform([sitk.Transform(scale_transform), result, scale_transform.GetInverse()])

        # if result was a composite transform then we have nested composite
        # transforms white need to be flattened for writing.

        result.FlattenTransform()

        _logger.info(result)

    return result
