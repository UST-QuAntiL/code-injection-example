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


from functools import wraps

from dwave.system import EmbeddingComposite, DWaveSampler, LeapHybridSampler

from .interceptor import DWaveInterceptor


# pass old dwave sampler methods to DWaveInterceptor
# DWaveInterceptor.set_embedding_composite(EmbeddingComposite)
DWaveInterceptor.set_dwave_sampler(DWaveSampler)
DWaveInterceptor.set_hybrid_sampler(LeapHybridSampler)

# @wraps(EmbeddingComposite)
# def new_EmbeddingComposite(*args, **kwargs):
# 	return DWaveInterceptor.sampler_interceptor(*args, **kwargs)

@wraps(DWaveSampler)
def new_DWaveSampler(*args, **kwargs):
    return DWaveInterceptor.sampler_interceptor(*args, **kwargs)

@wraps(LeapHybridSampler)
def new_LeapHybridSampler(*args, **kwargs):
    return DWaveInterceptor.hybrid_interceptor(*args, **kwargs)

# patch in new method
# EmbeddingComposite = new_EmbeddingComposite
DWaveSampler = new_DWaveSampler
LeapHybridSampler = new_LeapHybridSampler
