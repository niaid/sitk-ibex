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
from sitkibex import resample
import SimpleITK as sitk
import logging


logging.basicConfig(level=logging.DEBUG)


class TestResample(TestCase):
    def test_resample1(self):
        """Test permutation of options"""

        image1 = sitk.Image([64, 64, 11], sitk.sitkFloat32)
        image2 = sitk.Image([64, 32, 12], sitk.sitkFloat32)
        image2[32, 16, 6] = 254
        image2.SetOrigin([5, 2, -1])
        tx = sitk.AffineTransform(3)
        tx.SetTranslation([5, 2, -1])

        out = resample(image1, image2)
        self.assertEqual(254, out[37, 18, 5])
        out = resample(image1, image2, tx)
        self.assertEqual(254, out[32, 16, 6])

        out = resample(image1, image2, invert=True)
        self.assertEqual(254, out[37, 18, 5])
        out = resample(image1, image2, tx, invert=True)
        self.assertEqual(254, out[42, 20, 4])

        resample(image1, image2, tx, fusion=True)

        out = resample(image1, image2, tx, combine=True)
        self.assertEqual((0, 254), out[32, 16, 6])

        out = resample(image1, image2, tx, projection=True)
        self.assertAlmostEqual(254.0 / 11.0, out[32, 16], places=5)
        resample(image1, image2, tx, fusion=True, projection=True)
        out = resample(image1, image2, tx, combine=True, projection=True)
        self.assertEqual(0, out[32, 16][0])
        self.assertEqual(int(254.0 / 11.0), out[32, 16][1])
