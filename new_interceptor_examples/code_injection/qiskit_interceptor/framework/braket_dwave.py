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


"""Module containing the amazon braket dwave interceptor and some helper classes."""

from inspect import signature
from typing import Callable, List, Tuple, Union

from ..interceptor import BaseInterceptor, ExecuteResult

# set of supported signatures
_SUPPORTED_SIGNATURES_BRAKETDWAVE = {
    "(s3_destination_folder: 'AwsSession.S3DestinationFolder', device_arn: 'str' = None, aws_session: 'AwsSession' = None, logger: 'Logger' = <Logger braket.ocean_plugin.braket_dwave_sampler (WARNING)>)"
}

_SUPPORTED_SIGNATURES_EMBEDDING = {
    "(child_sampler, find_embedding, embedding_parameters, scale_aware, child_structure_search)",
}


class BraketDWaveInterceptor(BaseInterceptor, framework="amazon_braket_dwave"):
    """Class to intercept calls to 'DWaveSampler' with."""

    # the list of interceptors
    __interceptors: List[Tuple[Union[int, float], "BraketDWaveInterceptor"]] = []
    __interceptors_sorted: bool = False  # True if the list is sorted

    # the signature of 'DWaveSampler method'
    _dwave_execute_signature: str

    # the execution results
    _execution_results: List[ExecuteResult] = []

    def __init_subclass__(cls, priority=0, **kwargs) -> None:
        """Register a subclass with the given priority."""
        BraketDWaveInterceptor.__interceptors.append((priority, cls()))

    @staticmethod
    def _get_interceptors():
        """Get a list of interceptors sorted by descending priority.

        Returns:
            List[Tuple[Union[int, float], BraketDWaveInterceptor]]: the sorted interceptors
        """
        if not BraketDWaveInterceptor.__interceptors_sorted:
            BraketDWaveInterceptor.__interceptors_sorted = True
            BraketDWaveInterceptor.__interceptors.sort(key=lambda x: x[0], reverse=True)
        return BraketDWaveInterceptor.__interceptors

    @classmethod
    def _set_intercepted_function(cls, method_name: str, func: Callable):
        """Set the 'DWaveSampler' callable.

        Args:
            dwave_sampler (Callable): BraketDWaveSampler or EmbeddingComposite

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        execute_signature = str(signature(func))

        if method_name == "BraketDWaveSampler":
            if execute_signature not in _SUPPORTED_SIGNATURES_BRAKETDWAVE:
                raise Warning(
                    "The given braket dwave sampler method has an unknown signature that may not be supported!"
                )
        
        elif method_name == "EmbeddingComposite":

            execute_signature_list = [str(value.split("=")[0]) for value in execute_signature.strip('(').strip(')').split(",")]
            execute_signature = str('(' + ','.join(execute_signature_list) + ')')
            
            if execute_signature not in _SUPPORTED_SIGNATURES_EMBEDDING:
                raise Warning(
                    "The given dwave embedding composite method has an unknown signature that may not be supported!"
                )
        
        BraketDWaveInterceptor._dwave_execute_signature = execute_signature
        super()._set_intercepted_function(method_name, func)

    @staticmethod
    def load_interceptors():
        # import extra interceptors
        from . import (
            braket_dwave_extract_interceptor,
            braket_dwave_inject_backend_interceptor,
        )

    @staticmethod
    def load_dry_run_interceptor():
        # import dry run interceptor
        from . import braket_dwave_dry_run_interceptor

    @staticmethod
    def patch_framework():
        from functools import wraps

        # d-wave ocean sdk embedding composite method:
        from dwave.system import EmbeddingComposite

        # amazon braket DWave plugin for dwave sampler:
        from braket.ocean_plugin import BraketDWaveSampler


        # the name of the intercepted function (will be available in the call metadata object)
        method_name = "BraketDWaveSampler"

        # pass old DWaveSampler method to BraketDWaveInterceptor
        BraketDWaveInterceptor._set_intercepted_function(method_name, BraketDWaveSampler)

        @wraps(BraketDWaveSampler)
        def new_BraketDWaveSampler(*args, **kwargs):
            # the method name of the intercepted function must be the first argument
            return BraketDWaveInterceptor.execute_interceptor(method_name, *args, **kwargs)

        # patch in new method
        BraketDWaveSampler = new_BraketDWaveSampler


        # the name of the intercepted function (will be available in the call metadata object)
        method_name = "EmbeddingComposite"

        # pass old EmbeddingComposite method to BraketDWaveInterceptor
        BraketDWaveInterceptor._set_intercepted_function(method_name, EmbeddingComposite)

        @wraps(EmbeddingComposite)
        def new_EmbeddingComposite(*args, **kwargs):
            # the method name of the intercepted function must be the first argument
            return BraketDWaveInterceptor.execute_interceptor(method_name, *args, **kwargs)

        # patch in new method
        EmbeddingComposite = new_EmbeddingComposite
