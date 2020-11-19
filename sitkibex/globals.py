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

import logging

default_random_seed = 100
"""Random seed used for each registration called for reproducible results. If it is set to 0 the time will be used to
initialized a seed."""

logger = logging.getLogger(__name__).parent
"""The parent `logger` object for all sub-loggers. It can be used to control the level of output and how the
 warning, info, and debug messages are handled."""

__all__ = ["default_random_seed", "logger"]
