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
from unittest import TestCase

import SimpleITK as sitk
from sitkibex import registration
import logging
import math

logging.basicConfig(level=logging.DEBUG)


class TestReg(TestCase):
    @staticmethod
    def generate_blob(point, size):
        img = sitk.GaussianSource(
            mean=point, sigma=[s / 10.0 for s in size], scale=255, size=size, outputPixelType=sitk.sitkFloat32
        )

        # img.SetSpacing(2.1e-6, 2.1e-6, 1.1e-5)

        return img

    @staticmethod
    def generate_double_blobs(point1, point2, size):
        img2 = __class__.generate_blob(point1, size)
        img1 = __class__.generate_blob(point2, size)
        return img1 + img2

    def check_near(self, pt1, pt2, tolerance=1e-4):

        self.assertEqual(len(pt1), len(pt2))
        distance = math.sqrt(sum([(float(i) - float(j)) ** 2 for i, j in zip(pt1, pt2)]))

        fail_msg = "The distance between {0} and {1} exceeded tolerance".format(pt1, pt2)
        self.assertLess(distance, tolerance, msg=fail_msg)

    def test_reg0(self):
        pts = [[256, 256, 8]]
        # all registration options set to False, so no registration is
        # performed, returning the identity transformation.
        tx = registration(
            sitk.Image([32, 32], sitk.sitkUInt8),
            sitk.Image([32, 32], sitk.sitkUInt8),
            do_fft_initialization=False,
            do_affine2d=False,
            do_affine3d=False,
        )
        self.check_near(pts[0], tx.TransformPoint(pts[0]))

    def test_reg1(self):
        fixed_pts = [[256, 256, 8], [64, 64, 7]]
        fixed = self.generate_double_blobs(point1=fixed_pts[0], point2=fixed_pts[1], size=[512, 511, 16])

        moving_pts = [[240, 288, 8], [48, 96, 7]]
        moving = self.generate_double_blobs(point1=moving_pts[0], point2=moving_pts[1], size=[512, 511, 16])

        tx = registration(fixed, moving, do_affine3d=False, do_fft_initialization=True)

        self.check_near(moving_pts[0], tx.TransformPoint(fixed_pts[0]))
        self.check_near(moving_pts[1], tx.TransformPoint(fixed_pts[1]))

    def test_reg2(self):
        fixed = self.generate_double_blobs(point1=[256, 256, 8], point2=[64, 64, 7], size=[512, 511, 16])

        moving = self.generate_double_blobs(point1=[240, 288, 8], point2=[48, 96, 7], size=[512, 511, 16])

        registration(fixed, moving, do_affine3d=True, do_fft_initialization=False, samples_per_parameter=100)

    def test_reg3(self):
        fixed = self.generate_double_blobs(point1=[256, 256, 8], point2=[64, 64, 7], size=[512, 511, 16])

        moving = self.generate_double_blobs(point1=[240, 288, 8], point2=[48, 96, 7], size=[512, 511, 16])

        registration(
            fixed, moving, do_affine3d=False, do_affine2d=True, do_fft_initialization=False, samples_per_parameter=100
        )

    def test_reg2_with_fft(self):
        fixed = self.generate_double_blobs(point1=[256, 256, 8], point2=[64, 64, 7], size=[512, 511, 16])

        moving = self.generate_double_blobs(point1=[240, 288, 8], point2=[48, 96, 7], size=[512, 511, 16])

        registration(fixed, moving, do_affine3d=True, do_fft_initialization=True, samples_per_parameter=100)

    def test_reg3_with_fft(self):
        fixed = self.generate_double_blobs(point1=[256, 256, 8], point2=[64, 64, 7], size=[512, 511, 16])

        moving = self.generate_double_blobs(point1=[240, 288, 8], point2=[48, 96, 7], size=[512, 511, 16])

        registration(
            fixed, moving, do_affine3d=False, do_affine2d=True, do_fft_initialization=True, samples_per_parameter=100
        )

    def test_reg4_with_fft(self):
        fixed = self.generate_double_blobs(point1=[256, 256, 8], point2=[64, 64, 7], size=[512, 511, 16])

        moving = self.generate_double_blobs(point1=[240, 288, 8], point2=[48, 96, 7], size=[512, 511, 16])

        registration(
            fixed, moving, do_affine3d=True, do_affine2d=True, do_fft_initialization=True, samples_per_parameter=100
        )

    def test_reg5_with_mask(self):
        fixed = self.generate_double_blobs(point1=[256, 256, 8], point2=[64, 64, 7], size=[512, 511, 16])
        fixed *= sitk.Cast(fixed >= 0.1, sitk.sitkFloat32)

        moving = self.generate_double_blobs(point1=[240, 288, 8], point2=[48, 96, 7], size=[512, 511, 16])

        registration(
            fixed,
            moving,
            do_affine3d=True,
            do_affine2d=False,
            do_fft_initialization=True,
            auto_mask=True,
            samples_per_parameter=500,
        )
