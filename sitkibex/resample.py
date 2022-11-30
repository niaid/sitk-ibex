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


def _combine_images(fixed_image, moving_image, transform, virtual_image=None, tx2=None, fusion=False):
    """Combine two scalar images into multi-component images.

    The default operation is to compose the two input images into a 2 channel vector image.

    If fusion is True, then the images are combined into RGB.

    """

    output_pixel_type = sitk.sitkUInt8
    if (fixed_image.GetNumberOfComponentsPerPixel() > 1) or (moving_image.GetNumberOfComponentsPerPixel() > 1):
        output_pixel_type = sitk.VectorUInt8

    if virtual_image is not None:
        moving_resampled = sitk.Resample(
            moving_image, referenceImage=virtual_image, transform=transform, outputPixelType=output_pixel_type
        )
        fixed_resampled = sitk.Resample(fixed_image, virtual_image, transform=tx2, outputPixelType=output_pixel_type)
    else:
        moving_resampled = sitk.Resample(
            moving_image, referenceImage=fixed_image, transform=transform, outputPixelType=output_pixel_type
        )
        fixed_resampled = sitk.Cast(fixed_image, output_pixel_type)

    if fusion:
        moving_resampled = sitk.RescaleIntensity(moving_resampled)
        fixed_resampled = sitk.RescaleIntensity(fixed_resampled)
        return sitk.Compose([fixed_resampled, moving_resampled, fixed_resampled // 2.0 + moving_resampled // 2.0])

    return sitk.Compose([fixed_resampled, moving_resampled])


def resample(
    fixed_image: sitk.Image,
    moving_image: sitk.Image,
    transform: sitk.Transform = None,
    *,
    fusion=False,
    projection=False,
    combine=False,
    invert=False
) -> sitk.Image:
    """Resample fixed_image onto the coordinates of moving_image with transform results from registration.

    The registration process results in a transform which maps points from the coordinates of the fixed_image to the
    moving_image. This method is next used to resample the the fixed_image with the transform to produce an image with
    the fixed_image aligned with the moving_image.

    If no transform is provided, then an identity transform is assumed and the moving_image is still resampled onto the
    fixed_image. This operation is useful to see alignment of images before registration.



    :param fixed_image: A 3D SimpleITK Image whose pixel values are resampled
    :param moving_image: A 3D SimpleITK Image whose coordinates are used for the output image
    :param transform: (optional) A 3D SimpleITK Transform mapping from points from the fixed_image to the moving_image.
    :param fusion: Enable fusing the resampled moving_image and the fixed_image into a RGB image.
    :param projection: Enable perform a z-projection to reduce the dimensionality to 2D.
    :param combine: Enable combining the resampled moving_image and the fixed_image into a 2-channel vector image.
    :param invert: Invert the input transform.
    :return: The processed SimpleITK Image.
    """

    if not transform:
        transform = sitk.Transform(3, sitk.sitkIdentity)

    if invert:
        transform = transform.GetInverse()

    if fusion or combine:

        _logger.info("Fusing images...")
        resampled_image = _combine_images(fixed_image, moving_image, transform, fusion=fusion)

    else:
        output_pixel_type = moving_image.GetPixelID()

        _logger.info("Resampling image...")

        resampler = sitk.ResampleImageFilter()
        resampler.SetOutputDirection(fixed_image.GetDirection())
        resampler.SetOutputOrigin(fixed_image.GetOrigin())
        resampler.SetOutputSpacing(fixed_image.GetSpacing())
        resampler.SetSize(fixed_image.GetSize())
        resampler.SetOutputPixelType(output_pixel_type)
        resampler.SetDefaultPixelValue(0)
        resampler.SetInterpolator(sitk.sitkLinear)
        resampler.SetTransform(transform)

        resampled_image = resampler.Execute(moving_image)

    if projection:
        _logger.info("Projecting image...")
        proj_size = resampled_image.GetSize()[:2] + (0,)
        output_pixel_type = resampled_image.GetPixelID()
        projection_image = sitk.Cast(sitk.MeanProjection(resampled_image, projectionDimension=2), output_pixel_type)
        resampled_image = sitk.Extract(
            projection_image,
            size=proj_size,
            directionCollapseToStrategy=sitk.ExtractImageFilter.DIRECTIONCOLLAPSETOIDENTITY,
        )

    return resampled_image
