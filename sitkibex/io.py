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

import SimpleITK as sitk

import os.path
import logging
from .xml_info import XMLInfo, OMEInfo

_logger = logging.getLogger(__name__)

_vector_to_scalar = {
    sitk.sitkVectorUInt8: sitk.sitkUInt8,
    sitk.sitkVectorInt8: sitk.sitkInt8,
    sitk.sitkVectorUInt16: sitk.sitkUInt16,
    sitk.sitkVectorInt16: sitk.sitkInt16,
    sitk.sitkVectorUInt32: sitk.sitkUInt32,
    sitk.sitkVectorInt32: sitk.sitkInt32,
    sitk.sitkVectorFloat32: sitk.sitkFloat32,
    sitk.sitkVectorFloat64: sitk.sitkFloat64,
}


def im_read_channel(filename, channel=None):  # noqa: C901
    """
    Read a channel from an image file.

    SimpleITK is used to read a channel from the file. Channel names can be used if the image file contains meta-data
    which can be parsed and provides names for the channels. Otherwise channel index should be used.

    :param filename: The path to an image file.
    :param channel: An integer for the channel index or string for the name of the channel. If None then all channel are
    read.

    :return: A SimpleITK Image.

    """

    reader = sitk.ImageFileReader()
    reader.SetFileName(filename)

    if channel is None:
        _logger.info('Reading whole "{}" image file.'.format(filename))
        return reader.Execute()

    ext = os.path.splitext(filename)[1].lower()
    if ext in [".tif", ".tiff"]:
        # OME TIFF files might be reader by the SCIFIOIMageIO, but that IO does not
        # share the OME XML in the meta data
        reader.SetImageIO("TIFFImageIO")

    reader.ReadImageInformation()

    _logger.debug(reader)

    if isinstance(channel, int):
        channel_number = channel

    else:

        IMAGE_DESCRIPTION = "ImageDescription"
        IMARIS_CHANNEL_INFORMATION = "imaris_channels_information"

        if IMAGE_DESCRIPTION in reader.GetMetaDataKeys():
            _logger.info('Found "{}" metadata field in {}.'.format(IMAGE_DESCRIPTION, filename))

            image_description = reader.GetMetaData(IMAGE_DESCRIPTION)
            _logger.debug(image_description)
            ome_info = OMEInfo(image_description)
            channel_names = ome_info.channel_names

        elif IMARIS_CHANNEL_INFORMATION in reader.GetMetaDataKeys():
            _logger.info('Found "{}" metadata field in {}.'.format(IMARIS_CHANNEL_INFORMATION, filename))
            imaris_data = reader.GetMetaData(IMARIS_CHANNEL_INFORMATION)
            _logger.debug(imaris_data)
            imaris_info = XMLInfo(imaris_data)

            channel_names = imaris_info.channel_names
        else:
            raise Exception(
                "No metadata information for channel names in file: {},"
                "reference channel by number not name.".format(filename)
            )

        if channel not in channel_names:
            raise Exception('Channel name "{0}" is not in filename marker list: {1}'.format(channel, channel_names))
        channel_number = channel_names.index(channel)
        _logger.debug('Channel name "{}" is channel number {}.'.format(channel, channel_number))

    if reader.GetImageIO() != "":
        reader.SetImageIO("")

    if reader.GetDimension() == 3:
        dimension_order = "XYZ"
    elif reader.GetDimension() == 4:
        dimension_order = "XYZC"
    elif reader.GetDimension() == 5:
        dimension_order = "XYZTC"
    else:
        raise Exception('File "{}" has unsupported dimension {}.'.format(filename, reader.GetDimension()))

    _logger.debug("dimension order: {} {}".format(dimension_order, reader.GetSize()))

    if reader.GetDimension() > 3 and reader.GetNumberOfComponents() > 1:
        _logger.warning(
            'File "{}" has {} dimensions and {} components. '
            "Ambiguous which contains the channels.".format(
                filename, reader.GetDimension(), reader.GetNumberOfComponents()
            )
        )

    # reduce dimensions
    extract_size = list(reader.GetSize())
    extract_index = [0] * len(extract_size)
    if reader.GetNumberOfComponents() == 1 and channel_number is not None:
        c_idx = dimension_order.upper().index("C")
        extract_index[c_idx] = channel_number

        if extract_index[c_idx] >= extract_size[c_idx]:
            raise Exception(
                "Channel index {} is dimension {} size {}.".format(channel_number, reader.GetDimension(), extract_size)
            )
        extract_size[c_idx] = 0

    # collapse time dimension
    if "T" in dimension_order:
        t_idx = dimension_order.upper().index("T")
        _logger.debug(
            'Dimension "T" ({}) has size {}, is being collapsed one first image.'.format(t_idx, extract_index[t_idx])
        )
        extract_size[t_idx] = 0

    reader.SetExtractSize(extract_size)
    reader.SetExtractIndex(extract_index)
    img = reader.Execute()

    if reader.GetNumberOfComponents() > 1 and channel_number is not None:
        if channel_number >= reader.GetNumberOfComponents():
            raise Exception(
                "Channel index {} is beyond the number of components {}".format(
                    channel_number, reader.GetNumberOfComponents()
                )
            )
        img = sitk.VectorIndexSelectionCast(img, channel_number)

    return img
