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

# amazon braket DWave plugin for dwave sampler:
from braket.ocean_plugin import BraketDWaveSampler

# necessary D-Wave Ocean SDK libraries
from dwave.system import EmbeddingComposite

from .interceptor import BraketDWaveInterceptor


# pass old BraketDWave sampler methods to BraketDWaveInterceptor
BraketDWaveInterceptor.set_embedding_composite(EmbeddingComposite)
BraketDWaveInterceptor.set_braketdwave_sampler(BraketDWaveSampler)

@wraps(EmbeddingComposite)
def new_EmbeddingComposite(*args, **kwargs):
    return BraketDWaveInterceptor.embedding_interceptor(*args, **kwargs)

@wraps(BraketDWaveSampler)
def new_BraketDWaveSampler(*args, **kwargs):
    return BraketDWaveInterceptor.sampler_interceptor(*args, **kwargs)

# patch in new method
EmbeddingComposite = new_EmbeddingComposite
BraketDWaveSampler = new_BraketDWaveSampler
