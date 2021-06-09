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

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union


from inspect import signature


# set of supported signatures
_SUPPORTED_SIGNATURES_DWAVE = {
    "(failover=False, retry_interval=-1, **config)",
}

_SUPPORTED_SIGNATURES_HYBRID = {
    "(solver=None, connection_close=True, **config)",
}

@dataclass
class SamplerCallMetadata():
    """Class containing all metadata (and call arguments) of a call to 'dwave sampler method'."""
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    extra_data: Dict[Any, Any] = field(default_factory=dict)
    should_terminate: bool = False
    termination_result: Optional[Any] = None

    def copy(self):
        """Create a shallow copy of the current metadata.

        Returns:
            SamplerCallMetadata: the copied metadata
        """
        return SamplerCallMetadata(
            args=self.args,
            kwargs=self.kwargs,
            extra_data=self.extra_data,
            should_terminate=self.should_terminate,
            termination_result=self.termination_result,
        )

    def __repr__(self) -> str:
        arguments = []
        if self.args:
            arguments.extend(repr(arg) for arg in self.args)
        if self.kwargs:
            arguments.extend("{key}={value:r}".format(key=key, value=value) for key, value in self.kwargs.items())
        
        call = "DWaveSampler({args})".format(args=', '.join(arguments))
        extra = "extra_data = {{ {extra_data} }}, should_terminate = {should_terminate}, termination_result = {result}".format(
            should_terminate=self.should_terminate,
            result=repr(self.termination_result),
            extra_data=', '.join("'{key}': ...".format(key=key) for key in self.extra_data.keys())
        )
        return "SamplerCallMetadata(call='{call}', {extra})".format(call=call, extra=extra)


# A tuple containing the call metadata and the return value of that call
SamplerResult = NamedTuple("SamplerResult", [("call_metadata", SamplerCallMetadata), ("result", Any)])


class DWaveInterceptorInterrupt(Exception):
    """Exception raised when a call is terminated by an interceptor."""

    sampler_metadata: SamplerCallMetadata

    def __init__(self, sampler_metadata: SamplerCallMetadata, *args: object) -> None:
        super().__init__(*args)
        self.sampler_metadata = sampler_metadata


class DWaveInterceptor():
    """Class to intercept calls to 'dwave sampler method' with."""

    # the list of interceptors
    __interceptors: List[Tuple[Union[int, float], "DWaveInterceptor"]] = []
    __interceptors_sorted: bool = False # True if the list is sorted

    # the 'dwave sampler method' function
    __dwave_sampler: Callable
    _dwave_sampler_signature: str # the signature of 'dwave sampler method'

    # the 'dwave sampler method' function
    __hybrid_sampler: Callable
    _hybrid_sampler_signature: str # the signature of 'hybrid sampler method'

    # the execution results
    __sampler_interception_results: List[SamplerResult] = []

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


    @staticmethod
    def get_execution_results():
        """Get the list of execution results.

        This list will not contain the result of an interrupted execution!

        Returns:
            List[SamplerResult]: the execution results
        """
        return DWaveInterceptor.__sampler_interception_results


    @staticmethod
    def set_dwave_sampler(dwave_sampler: Callable):
        """Set the 'dwave sampler method' callable.

        Args:
            dwave_sampler (Callable): DWaveSampler 

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        sampler_signature = str(signature(dwave_sampler))
        if sampler_signature not in _SUPPORTED_SIGNATURES_DWAVE:
            raise Warning("The given D-Wave Snmpler function has an unknown signature that may not be supported!")
        DWaveInterceptor.__dwave_sampler = dwave_sampler
        DWaveInterceptor._dwave_sampler_signature = sampler_signature


    @staticmethod
    def set_hybrid_sampler(hybrid_sampler: Callable):
        """Set the 'dwave sampler method' callable.

        Args:
            hybrid_sampler (Callable): LeapHybridSampler 

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        sampler_signature = str(signature(hybrid_sampler))
        if sampler_signature not in _SUPPORTED_SIGNATURES_HYBRID:
            raise Warning("The given D-Wave Snmpler function has an unknown signature that may not be supported!")
        DWaveInterceptor.__hybrid_sampler = hybrid_sampler
        DWaveInterceptor._hybrid_sampler_signature = sampler_signature


    @staticmethod
    def sampler_interceptor(*args, **kwargs):
        """Run all interceptors and call 'dwave sampler method'.

        Raises:
            DWaveInterceptorInterrupt: If the execution was terminated by an interceptor

        Returns:
            Any: the result of 'dwave sampler method'
        """
        dwave_sampler = DWaveInterceptor.__dwave_sampler
        if dwave_sampler is None:
            raise Exception("Must call set_dwave_sampler before using sampler_interceptor!")

        sampler_metadata = SamplerCallMetadata(args=args, kwargs=kwargs)

        # run all intercept_sampler interceptors
        for _, interceptor in DWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler(sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

            if sampler_metadata.should_terminate:
                raise DWaveInterceptorInterrupt(sampler_metadata)

        # perform actual method
        result = dwave_sampler(*sampler_metadata.args, **sampler_metadata.kwargs)

        # run all intercept_sampler_result interceptors
        for _, interceptor in DWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler_result(result=result, sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

        # store result
        DWaveInterceptor.__sampler_interception_results.append(SamplerResult(call_metadata=sampler_metadata, result=result));

        return result


    @staticmethod
    def hybrid_interceptor(*args, **kwargs):
        """Run all interceptors and call 'hybrid sampler method'.

        Raises:
            DWaveInterceptorInterrupt: If the execution was terminated by an interceptor

        Returns:
            Any: the result of 'hybrid sampler method'
        """
        hybrid_sampler = DWaveInterceptor.__hybrid_sampler
        if hybrid_sampler is None:
            raise Exception("Must call set_hybrid_sampler before using hybrid_interceptor!")

        sampler_metadata = SamplerCallMetadata(args=args, kwargs=kwargs)

        # run all intercept_sampler interceptors
        for _, interceptor in DWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler(sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

            if sampler_metadata.should_terminate:
                raise DWaveInterceptorInterrupt(sampler_metadata)

        # perform actual method
        result = hybrid_sampler(*sampler_metadata.args, **sampler_metadata.kwargs)

        # run all intercept_sampler_result interceptors
        for _, interceptor in DWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler_result(result=result, sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

        # store result
        DWaveInterceptor.__sampler_interception_results.append(SamplerResult(call_metadata=sampler_metadata, result=result));

        return result


    def intercept_sampler(self, sampler_metadata: SamplerCallMetadata) -> Optional[SamplerCallMetadata]:
        """Intercept the execution of 'sampler method'.

        Args:
            sampler_metadata (SamplerCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[SamplerCallMetadata]: a new or modified instance of the call metadata. Always copy 'sampler_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()


    def intercept_sampler_result(self, result: Any, sampler_metadata: SamplerCallMetadata) -> Optional[SamplerCallMetadata]:
        """Intercept the result of 'sampler method'.

        Args:
            result (Any): the result of the call to 'dwave or hybrid sampler method'.
            sampler_metadata (SamplerCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[SamplerCallMetadata]: a new or modified instance of the call metadata. Always copy 'sampler_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()
