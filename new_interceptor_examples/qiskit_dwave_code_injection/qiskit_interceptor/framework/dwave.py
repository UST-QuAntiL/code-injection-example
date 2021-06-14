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


"""Module containing the dwave interceptor and some helper classes."""

from inspect import signature
from typing import Callable, List, Tuple, Union

from ..interceptor import BaseInterceptor, ExecuteResult

# set of supported signatures
_SUPPORTED_SIGNATURES_DWAVE = {
    "(failover=False, retry_interval=-1, **config)",
}

_SUPPORTED_SIGNATURES_HYBRID = {
    "(solver=None, connection_close=True, **config)",
}

_SUPPORTED_SIGNATURES_EMBEDDING = {
    "(child_sampler, find_embedding, embedding_parameters, scale_aware, child_structure_search)",
}


class DWaveInterceptor(BaseInterceptor, framework="dwave"):
    """Class to intercept calls to 'DWaveSampler' with."""

    # the list of interceptors
    __interceptors: List[Tuple[Union[int, float], "DWaveInterceptor"]] = []
    __interceptors_sorted: bool = False  # True if the list is sorted

    # the signature of 'DWaveSampler method'
    _dwave_execute_signature: str

    # the execution results
    _execution_results: List[ExecuteResult] = []

    def __init_subclass__(cls, priority=0, **kwargs) -> None:
        """Register a subclass with the given priority."""
        DWaveInterceptor.__interceptors.append((priority, cls()))

    @staticmethod
    def _get_interceptors():
        """Get a list of interceptors sorted by descending priority.

        Returns:
            List[Tuple[Union[int, float], DWaveInterceptor]]: the sorted interceptors
        """
        if not DWaveInterceptor.__interceptors_sorted:
            DWaveInterceptor.__interceptors_sorted = True
            DWaveInterceptor.__interceptors.sort(key=lambda x: x[0], reverse=True)
        return DWaveInterceptor.__interceptors

    @classmethod
    def _set_intercepted_function(cls, method_name: str, func: Callable):
        """Set the 'DWaveSampler' callable.

        Args:
            dwave_sampler (Callable): DWaveSampler, LeapHybridSampler, or EmbeddingComposite

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        execute_signature = str(signature(func))

        if method_name == "DWaveSampler":
            if execute_signature not in _SUPPORTED_SIGNATURES_DWAVE:
                raise Warning(
                    "The given dwave sampler method has an unknown signature that may not be supported!"
                )

        elif method_name == "LeapHybridSampler":
            if execute_signature not in _SUPPORTED_SIGNATURES_HYBRID:
                raise Warning(
                    "The given dwave leap hybid sampler method has an unknown signature that may not be supported!"
                )
        
        elif method_name == "EmbeddingComposite":

            execute_signature_list = [str(value.split("=")[0]) for value in execute_signature.strip('(').strip(')').split(",")]
            execute_signature = str('(' + ','.join(execute_signature_list) + ')')
            
            if execute_signature not in _SUPPORTED_SIGNATURES_EMBEDDING:
                raise Warning(
                    "The given dwave embeddingh composite method has an unknown signature that may not be supported!"
                )
        
        DWaveInterceptor._dwave_execute_signature = execute_signature
        super()._set_intercepted_function(method_name, func)

    @staticmethod
    def load_interceptors():
        # import extra interceptors
        from . import (
            dwave_extract_interceptor,
            dwave_inject_backend_interceptor,
        )

    @staticmethod
    def load_dry_run_interceptor():
        # import dry run interceptor
        from . import dwave_dry_run_interceptor

    @staticmethod
    def patch_framework():
        from functools import wraps

        from dwave.system import EmbeddingComposite, DWaveSampler, LeapHybridSampler


        # the name of the intercepted function (will be available in the call metadata object)
        method_name = "DWaveSampler"

        # pass old DWaveSampler method to DWaveInterceptor
        DWaveInterceptor._set_intercepted_function(method_name, DWaveSampler)

        @wraps(DWaveSampler)
        def new_DWaveSampler(*args, **kwargs):
            # the method name of the intercepted function must be the first argument
            return DWaveInterceptor.execute_interceptor(method_name, *args, **kwargs)

        # patch in new method
        DWaveSampler = new_DWaveSampler


        # the name of the intercepted function (will be available in the call metadata object)
        method_name = "LeapHybridSampler"

        # pass old LeapHybridSampler method to DWaveInterceptor
        DWaveInterceptor._set_intercepted_function(method_name, LeapHybridSampler)

        @wraps(LeapHybridSampler)
        def new_LeapHybridSampler(*args, **kwargs):
            # the method name of the intercepted function must be the first argument
            return DWaveInterceptor.execute_interceptor(method_name, *args, **kwargs)

        # patch in new method
        LeapHybridSampler = new_LeapHybridSampler


        # the name of the intercepted function (will be available in the call metadata object)
        method_name = "EmbeddingComposite"

        # pass old EmbeddingComposite method to DWaveInterceptor
        DWaveInterceptor._set_intercepted_function(method_name, EmbeddingComposite)

        @wraps(EmbeddingComposite)
        def new_EmbeddingComposite(*args, **kwargs):
            # the method name of the intercepted function must be the first argument
            return DWaveInterceptor.execute_interceptor(method_name, *args, **kwargs)

        # patch in new method
        EmbeddingComposite = new_EmbeddingComposite
