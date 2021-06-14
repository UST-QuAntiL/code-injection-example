# Copyright 2021 code-injection-example contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import List, Sequence, Union

from ..interceptor import ExecuteCallMetadata

from .dwave import DWaveInterceptor

class ExtractDWaveInterceptor(DWaveInterceptor, priority=100):
    """Extract all quantum circuits and schedules from the call arguments.

    Args:
        priority (int): The priority of this interceptor, this interceptor has a high priority so it runs before other interceptors.
            Later interceptors could use the circuit data stored in 'execute_metadata.extra_data'.
    """

    def intercept_execute(self, execute_metadata: ExecuteCallMetadata) -> ExecuteCallMetadata:
        experiments_arg = execute_metadata.kwargs.get("experiments")
        if experiments_arg is None:
            experiments_arg = execute_metadata.args[0]

        return execute_metadata
