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

import sitkibex.registration_utilities as utils
import logging


logging.basicConfig(level=logging.DEBUG)


@utils.sub_volume_execute(inplace=True)
def do_add(img):
    img += 1.0
    return img


@utils.sub_volume_execute(inplace=False)
def do_add2(img):
    return img + 1.0


def test_sve_decorator_inplace_3d():
    img = sitk.Image([2, 3, 4], sitk.sitkUInt8)

    img_out = do_add(img)

    assert all([v == 1 for v in img_out])
    assert all([v == 1 for v in img])
    assert img.GetSize() == img_out.GetSize()


def test_sve_decorator_inplace_4d():
    img = sitk.Image([2, 3, 4, 5], sitk.sitkUInt8)

    img_out = do_add(img)

    assert all([v == 1 for v in img_out])
    assert all([v == 1 for v in img])
    assert img.GetSize() == img_out.GetSize()


def test_sve_decorator_inplace_5d():
    img = sitk.Image([2, 3, 4, 5, 6], sitk.sitkUInt8)

    img_out = do_add(img)

    assert all([v == 1 for v in img_out])
    assert all([v == 1 for v in img])
    assert img.GetSize() == img_out.GetSize()


def test_sve_decorator_3d():
    img = sitk.Image([2, 3, 4], sitk.sitkUInt8)

    img_out = do_add2(img)

    assert all([v == 1 for v in img_out])
    assert all([v == 0 for v in img])
    assert img.GetSize() == img_out.GetSize()


def test_sve_decorator_4d():
    img = sitk.Image([2, 3, 4, 5], sitk.sitkUInt8)

    img_out = do_add2(img)

    assert all([v == 1 for v in img_out])
    assert all([v == 0 for v in img])
    assert img.GetSize() == img_out.GetSize()


def test_sve_decorator_5d():
    img = sitk.Image([2, 3, 4, 5, 6], sitk.sitkUInt8)

    for c in range(img.GetSize()[4]):
        for t in range(img.GetSize()[3]):
            img[:, :, :, t, c] = 10 * t + c

    img_out = do_add2(img)

    assert all([v1 + 1 == v2 for v1, v2 in zip(img, img_out)])
    assert img.GetSize() == img_out.GetSize()
