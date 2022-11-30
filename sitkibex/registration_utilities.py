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
import time
from functools import reduce
import itertools
from functools import wraps
import logging

_logger = logging.getLogger(__name__)


class RegistrationCallbackManager:
    """An object with member functions for the callbacks of a sitk RegistrationMethod"""

    def __init__(self, registration_method):
        self.R = registration_method
        self.start_time = None
        self.prev_time = None

    def add_command_callbacks(self, print_position=False, verbose=True):
        """Registers all callbacks with registration method"""

        if verbose:
            self.R.AddCommand(sitk.sitkIterationEvent, lambda: self.iteration_callback1(print_position=print_position))
        self.R.AddCommand(sitk.sitkEndEvent, lambda: self.end_callback())
        self.R.AddCommand(sitk.sitkStartEvent, lambda: self.start_callback())
        self.R.AddCommand(sitk.sitkMultiResolutionIterationEvent, lambda: self.multi_resolution_callback())

    def start_callback(self):
        _logger.info("===Registration Start===")
        self.start_time = time.time()

    def end_callback(self, message=None):
        end_time = time.time()
        if message is not None:
            _logger.info(message)

        _logger.info("Total elapsed time: {0:.4f}s".format(end_time - self.start_time))
        _logger.info("Optimizer stop condition: {0}".format(self.R.GetOptimizerStopConditionDescription()))
        _logger.info(" Iteration: {0}".format(self.R.GetOptimizerIteration()))
        _logger.info(" Final Metric value: {0}".format(self.R.GetMetricValue()))

        if self.R.GetInitialTransformInPlace():
            _logger.info(self.R.GetInitialTransform())

        _logger.info("===Registraion End===")

    def iteration_callback1(self, print_position=True):
        """
        A method to be added to a SimpleITK ImageRegistration method callback for the Iteration event.

        :param method: The SimpleITK.ImageRegistrationMethod object emitting the event.
        :param print_position: Disable printing the optimizer position or the transforms parameters.p
        """
        if self.R.GetOptimizerIteration() == 0 and len(self.R.GetOptimizerScales()):
            if self.R.GetOptimizerLearningRate() != 0:
                _logger.info("Learning Rate: {0}".format(self.R.GetOptimizerLearningRate()))

            if self.R.GetInitialTransform().IsLinear():
                _logger.info("Estimated Scales: {0}".format(self.R.GetOptimizerScales()))
            else:
                pass
                # _logger.info("Estimated Scales: {0}".format(self.R.GetOptimizerScales()[0]))

        number_of_valid_points = "?"
        try:
            number_of_valid_points = self.R.GetMetricNumberOfValidPoints()
        except AttributeError:
            # Ignore self.R not existing
            pass

        if print_position:
            _logger.info(
                "{0:3} = {1:10.5f} : {2} ({3:10.5e}) [#{4}]".format(
                    self.R.GetOptimizerIteration(),
                    self.R.GetMetricValue(),
                    self.R.GetOptimizerPosition(),
                    self.R.GetOptimizerConvergenceValue(),
                    number_of_valid_points,
                )
            )

        else:
            _logger.info(
                "{0:3} = {1:10.5f} ({2:10.5e}) [#{3}]".format(
                    self.R.GetOptimizerIteration(),
                    self.R.GetMetricValue(),
                    self.R.GetOptimizerConvergenceValue(),
                    number_of_valid_points,
                )
            )

    def multi_resolution_callback(self, message=None):

        multi_time = time.time()
        if self.R.GetCurrentLevel() > 0:
            _logger.info("Elapsed time: {0:.4f}s".format(multi_time - self.prev_time))
            _logger.info("Optimizer stop condition: {0}".format(self.R.GetOptimizerStopConditionDescription()))
            _logger.info(" Total Iteration: {0}".format(self.R.GetOptimizerIteration()))
            _logger.info(" Metric value: {0}".format(self.R.GetMetricValue()))
            _logger.info(" Convergence value: {0}".format(self.R.GetOptimizerConvergenceValue()))

        self.prev_time = multi_time
        _logger.info("---Level {0} Start---".format(self.R.GetCurrentLevel()))


def sub_volume_execute(inplace=True):
    """
    A function decorator which executes func on each sub-volume and *in-place* pastes the output input the
    input image.

    :param inplace:
    :param func: A function which take a SimpleITK Image as it's first argument and returns the results.
    :return: A wrapped function.
    """

    def wrapper(func):
        @wraps(func)
        def slice_by_slice(image, *args, **kwargs):

            dim = image.GetDimension()

            if dim <= 3:
                image = func(image, *args, **kwargs)
                return image

            extract_size = list(image.GetSize())
            extract_size[3:] = itertools.repeat(0, dim - 3)

            extract_index = [0] * dim
            paste_idx = [slice(None, None)] * dim

            extractor = sitk.ExtractImageFilter()
            extractor.SetSize(extract_size)
            if inplace:
                for high_idx in itertools.product(*[range(s) for s in image.GetSize()[3:]]):
                    extract_index[3:] = high_idx
                    extractor.SetIndex(extract_index)

                    paste_idx[3:] = high_idx
                    image[paste_idx] = func(extractor.Execute(image), *args, **kwargs)

            else:
                img_list = []
                for high_idx in itertools.product(*[range(s) for s in image.GetSize()[3:]]):
                    extract_index[3:] = high_idx
                    extractor.SetIndex(extract_index)

                    paste_idx[3:] = high_idx

                    img_list.append(func(extractor.Execute(image), *args, **kwargs))

                for d in range(3, dim):
                    step = reduce((lambda x, y: x * y), image.GetSize()[d + 1 :], 1)
                    img_list = [sitk.JoinSeries(img_list[i::step], image.GetSpacing()[d]) for i in range(step)]

                assert len(img_list) == 1
                image = img_list[0]

            return image

        return slice_by_slice

    return wrapper
