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


from .interceptor import SamplerCallMetadata, BraketDWaveInterceptor

class DryRunInterceptor(BraketDWaveInterceptor, priority=0):
    """Interrupt the execution and return the experiments as result.

    Args:
        priority (int): The priority of this interceptor, this interceptor has a low priority so other interceptors can run first.
    """

    def intercept_sampler(self, sampler_metadata: SamplerCallMetadata) -> SamplerCallMetadata:
        sampler_metadata.should_terminate = True
        sampler_metadata.termination_result = sampler_metadata.kwargs.get("solver") or sampler_metadata.args[0]
        return sampler_metadata
