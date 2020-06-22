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


class RegistrationCallbackManager:
    """An object with member functions for the callbacks of a sitk RegistrationMethod """

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
        print("===Registration Start===")
        self.start_time = time.time()

    def end_callback(self, message=None):
        end_time = time.time()
        if message is not None:
            print(message)

        print("Total elapsed time: {0:.4f}s".format(end_time-self.start_time))
        print("Optimizer stop condition: {0}".format(self.R.GetOptimizerStopConditionDescription()))
        print(" Iteration: {0}".format(self.R.GetOptimizerIteration()))
        print(" Final Metric value: {0}".format(self.R.GetMetricValue()))

        if self.R.GetInitialTransformInPlace():
            print(self.R.GetInitialTransform())

        print("===Registraion End===")

    def iteration_callback1(self, print_position=True):
        """
        A method to be added to a SimpleITK ImageRegistration method callback for the Iteration event.

        :param method: The SimpleITK.ImageRegistrationMethod object emitting the event.
        :param print_position: Disable printing the optimizer position or the transforms parameters.p
        """
        if self.R.GetOptimizerIteration() == 0 and len(self.R.GetOptimizerScales()):
            if self.R.GetOptimizerLearningRate() != 0:
                print("Learning Rate: {0}".format(self.R.GetOptimizerLearningRate()))

            if self.R.GetInitialTransform().IsLinear():
                print("Estimated Scales: {0}".format(self.R.GetOptimizerScales()))
            else:
                pass
                # print("Estimated Scales: {0}".format(self.R.GetOptimizerScales()[0]))

        number_of_valid_points = '?'
        try:
            number_of_valid_points = self.R.GetMetricNumberOfValidPoints()
        except AttributeError:
            # Ignore self.R not existing
            pass

        if print_position:
            print("{0:3} = {1:10.5f} : {2} ({3:10.5e}) [#{4}]".format(self.R.GetOptimizerIteration(),
                                                                      self.R.GetMetricValue(),
                                                                      self.R.GetOptimizerPosition(),
                                                                      self.R.GetOptimizerConvergenceValue(),
                                                                      number_of_valid_points
                                                                      ))

        else:
            print("{0:3} = {1:10.5f} ({2:10.5e}) [#{3}]".format(self.R.GetOptimizerIteration(),
                                                                self.R.GetMetricValue(),
                                                                self.R.GetOptimizerConvergenceValue(),
                                                                number_of_valid_points
                                                                ))

    def multi_resolution_callback(self, message=None):

        multi_time = time.time()
        if self.R.GetCurrentLevel() > 0:
            print("Elapsed time: {0:.4f}s".format(multi_time-self.prev_time))
            print("Optimizer stop condition: {0}".format(self.R.GetOptimizerStopConditionDescription()))
            print(" Total Iteration: {0}".format(self.R.GetOptimizerIteration()))
            print(" Metric value: {0}".format(self.R.GetMetricValue()))
            print(" Convergence value: {0}".format(self.R.GetOptimizerConvergenceValue()))

        self.prev_time = multi_time
        print("---Level {0} Start---".format(self.R.GetCurrentLevel()))