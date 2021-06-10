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


"""Module containing the braket dwave interceptor and some helper classes."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union

from inspect import signature

# from braket.aws import AwsSession


# set of supported signatures
# _SUPPORTED_SIGNATURES_EMBEDDING = {
#     "(child_sampler, find_embedding, embedding_parameters=None, scale_aware=False, child_structure_search)",
# }
_SUPPORTED_SIGNATURES_EMBEDDING = {
    "(child_sampler, find_embedding, embedding_parameters, scale_aware, child_structure_search)",
}

_SUPPORTED_SIGNATURES_BRAKETDWAVE = {
    "(s3_destination_folder: 'AwsSession.S3DestinationFolder', device_arn: 'str' = None, aws_session: 'AwsSession' = None, logger: 'Logger' = <Logger braket.ocean_plugin.braket_dwave_sampler (WARNING)>)"
}


@dataclass
class SamplerCallMetadata():
    """Class containing all metadata (and call arguments) of a call to 'braket dwave sampler method'."""
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
        
        call = "BraketDWaveSampler({args})".format(args=', '.join(arguments))
        extra = "extra_data = {{ {extra_data} }}, should_terminate = {should_terminate}, termination_result = {result}".format(
            should_terminate=self.should_terminate,
            result=repr(self.termination_result),
            extra_data=', '.join("'{key}': ...".format(key=key) for key in self.extra_data.keys())
        )
        return "SamplerCallMetadata(call='{call}', {extra})".format(call=call, extra=extra)


# A tuple containing the call metadata and the return value of that call
SamplerResult = NamedTuple("SamplerResult", [("call_metadata", SamplerCallMetadata), ("result", Any)])


class BraketDWaveInterceptorInterrupt(Exception):
    """Exception raised when a call is terminated by an interceptor."""

    sampler_metadata: SamplerCallMetadata

    def __init__(self, sampler_metadata: SamplerCallMetadata, *args: object) -> None:
        super().__init__(*args)
        self.sampler_metadata = sampler_metadata


class BraketDWaveInterceptor():
    """Class to intercept calls to 'braket dwave sampler method' with."""

    # the list of interceptors
    __interceptors: List[Tuple[Union[int, float], "BraketDWaveInterceptor"]] = []
    __interceptors_sorted: bool = False # True if the list is sorted

    # the 'embedding composite method' function
    __embedding_composite: Callable
    _embedding_composite_signature: str # the signature of 'embedding composite method'

    # the 'braket dwave sampler method' function
    __braketdwave_sampler: Callable
    _braketdwave_sampler_signature: str # the signature of 'braket dwave sampler method'

    # the execution results
    __sampler_interception_results: List[SamplerResult] = []

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


    @staticmethod
    def get_execution_results():
        """Get the list of execution results.

        This list will not contain the result of an interrupted execution!

        Returns:
            List[SamplerResult]: the execution results
        """
        return BraketDWaveInterceptor.__sampler_interception_results


    @staticmethod
    def set_embedding_composite(embedding_composite: Callable):
        """Set the 'dwave sampler method' callable.

        Args:
            embedding_composite (Callable): EmbeddingComposite

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        sampler_signature_complete = str(signature(embedding_composite))
        sampler_signature_list = [str(value.split("=")[0]) for value in sampler_signature_complete.strip('(').strip(')').split(",")]
        sampler_signature = str('(' + ','.join(sampler_signature_list) + ')')
        if sampler_signature not in _SUPPORTED_SIGNATURES_EMBEDDING:
            raise Warning("The given Embedding Composite function has an unknown signature that may not be supported!")
        BraketDWaveInterceptor.__embedding_composite = embedding_composite
        BraketDWaveInterceptor._embedding_composite_signature = sampler_signature


    @staticmethod
    def set_braketdwave_sampler(braketdwave_sampler: Callable):
        """Set the 'braket dwave sampler method' callable.

        Args:
            braketdwave_sampler (Callable): BraketDWaveSampler 

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        sampler_signature = str(signature(braketdwave_sampler))
        if sampler_signature not in _SUPPORTED_SIGNATURES_BRAKETDWAVE:
            raise Warning("The given Amazon Braket D-Wave Sampler function has an unknown signature that may not be supported!")
        BraketDWaveInterceptor.__braketdwave_sampler = braketdwave_sampler
        BraketDWaveInterceptor._braketdwave_sampler_signature = sampler_signature


    @staticmethod
    def embedding_interceptor(*args, **kwargs):
        """Run all interceptors and call 'embedding composite method'.

        Raises:
            DWaveInterceptorInterrupt: If the execution was terminated by an interceptor

        Returns:
            Any: the result of 'embedding composite method'
        """
        embedding_composite = BraketDWaveInterceptor.__embedding_composite
        if embedding_composite is None:
            raise Exception("Must call set_embedding_composite before using embedding_interceptor!")

        sampler_metadata = SamplerCallMetadata(args=args, kwargs=kwargs)

        # run all intercept_sampler interceptors
        for _, interceptor in BraketDWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler(sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

            if sampler_metadata.should_terminate:
                raise BraketDWaveInterceptorInterrupt(sampler_metadata)

        # perform actual method
        result = embedding_composite(*sampler_metadata.args, **sampler_metadata.kwargs)

        # run all intercept_sampler_result interceptors
        for _, interceptor in BraketDWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler_result(result=result, sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

        # store result
        BraketDWaveInterceptor.__sampler_interception_results.append(SamplerResult(call_metadata=sampler_metadata, result=result));

        return result


    @staticmethod
    def sampler_interceptor(*args, **kwargs):
        """Run all interceptors and call 'braket dwave sampler method'.

        Raises:
            BraketDWaveInterceptorInterrupt: If the execution was terminated by an interceptor

        Returns:
            Any: the result of 'braket dwave sampler method'
        """
        braketdwave_sampler = BraketDWaveInterceptor.__braketdwave_sampler
        if braketdwave_sampler is None:
            raise Exception("Must call set_braketdwave_sampler before using sampler_interceptor!")

        sampler_metadata = SamplerCallMetadata(args=args, kwargs=kwargs)

        # run all intercept_sampler interceptors
        for _, interceptor in BraketDWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler(sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

            if sampler_metadata.should_terminate:
                raise BraketDWaveInterceptorInterrupt(sampler_metadata)

        # perform actual method
        result = braketdwave_sampler(*sampler_metadata.args, **sampler_metadata.kwargs)

        # run all intercept_sampler_result interceptors
        for _, interceptor in BraketDWaveInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_sampler_result(result=result, sampler_metadata=sampler_metadata)
                if new_metadata is not None:
                    sampler_metadata = new_metadata
            except NotImplementedError:
                pass

        # store result
        BraketDWaveInterceptor.__sampler_interception_results.append(SamplerResult(call_metadata=sampler_metadata, result=result));

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
            result (Any): the result of the call to 'braket dwave or hybrid sampler method'.
            sampler_metadata (SamplerCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[SamplerCallMetadata]: a new or modified instance of the call metadata. Always copy 'sampler_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()
