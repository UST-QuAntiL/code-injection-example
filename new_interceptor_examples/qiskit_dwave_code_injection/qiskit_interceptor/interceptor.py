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


"""Module containing the qiskit and dwave interceptors and some helper classes."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Type


@dataclass
class ExecuteCallMetadata:
    """Class containing all metadata (and call arguments) of a call to an intercepted function.

    Attributes:
        method_name: the name of the intercepted function as defined by the framework specific interceptor
        args: the list of positional arguments of the specific function call; modify or replace this to update parameters
        kwargs: the keyword arguments of the specific function call; modify or replace this to update parameters
        extra_data: a dict to store data for later interceptors or final analysis
        interceptor_arguments: A dict containing arguments for the interceptors (e.g. whether to inject a specific execution backend)
        should_terminate: flag to tell the interceptor that the execution should be interrupted, set this to True to interrupt execution
        termination_result: a result tha will be used as the final result of the execution in case the execution was interrupted, set this together with the should_terminate flag
    """

    method_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    extra_data: Dict[Any, Any] = field(default_factory=dict)
    interceptor_arguments: Dict[str, Any] = field(default_factory=dict)
    should_terminate: bool = False
    termination_result: Optional[Any] = None

    def copy(self):
        """Create a shallow copy of the current metadata.

        Returns:
            ExecuteCallMetadata: the copied metadata
        """
        return ExecuteCallMetadata(
            method_name=self.method_name,
            args=self.args,
            kwargs=self.kwargs,
            extra_data=self.extra_data,
            interceptor_arguments=self.interceptor_arguments,
            should_terminate=self.should_terminate,
            termination_result=self.termination_result,
        )

    def __repr__(self) -> str:
        arguments = []
        if self.args:
            arguments.extend(repr(arg) for arg in self.args)
        if self.kwargs:
            arguments.extend(
                "{key}={value:r}".format(key=key, value=value)
                for key, value in self.kwargs.items()
            )

        call = "{func}({args})".format(func=self.method_name, args=", ".join(arguments))
        extra = "extra_data = {{ {extra_data} }}, interceptor_arguments = {{ {interceptor_arguments} }}, should_terminate = {should_terminate}, termination_result = {result}".format(
            should_terminate=self.should_terminate,
            result=repr(self.termination_result),
            extra_data=", ".join(
                "'{key}': ...".format(key=key) for key in self.extra_data.keys()
            ),
            interceptor_arguments=", ".join(
                "'{key}': ...".format(key=key)
                for key in self.interceptor_arguments.keys()
            ),
        )
        return "ExecuteCallMetadata(call='{call}', {extra})".format(
            call=call, extra=extra
        )


# A tuple containing the call metadata and the return value of that call
ExecuteResult = NamedTuple(
    "ExecuteResult", [("call_metadata", ExecuteCallMetadata), ("result", Any)]
)


class InterceptorInterrupt(Exception):
    """Exception raised when a call is terminated by an interceptor."""

    execute_metadata: ExecuteCallMetadata

    def __init__(self, execute_metadata: ExecuteCallMetadata, *args: object) -> None:
        super().__init__(*args)
        self.execute_metadata = execute_metadata


class BaseInterceptor:
    """Class to intercept calls to a quantum circuit execution function with."""

    __framework_interceptors: Dict[str, Type["BaseInterceptor"]] = {}

    _original_callables: Dict[str, Callable] = {}
    _execution_results: List[ExecuteResult]

    _interceptor_arguments: Dict[str, Any] = {}

    def __init_subclass__(cls, framework: str, **kwargs) -> None:
        """Register a new interceptor for a specific framework."""
        BaseInterceptor.__framework_interceptors[framework.upper()] = cls

    @staticmethod
    def get_supported_frameworks() -> List[str]:
        """Get a list of suported framework names. All names are converted to upper case."""
        return list(sorted(BaseInterceptor.__framework_interceptors.keys()))

    @staticmethod
    def get_intereceptor_for_framework(framework: str) -> Type["BaseInterceptor"]:
        """Get a framework specific interceptor class based on the given frmaework name."""
        return BaseInterceptor.__framework_interceptors[framework.upper()]

    @staticmethod
    def set_interceptor_arguments(arguments: Dict[str, Any]):
        """Set arguments for the interceptors. The arguments are available to all interceptors as part of the call metadata."""
        BaseInterceptor._interceptor_arguments = arguments

    @classmethod
    def _get_interceptors(cls):
        """Get all interceptors that should run for a specific framework. Must be implemented by the framework specific interceptors."""
        raise NotImplementedError()

    @staticmethod
    def load_interceptors():
        """Load all framework specific interceptor plugins. Must be implemented by the framework specific interceptors."""
        raise NotImplementedError()

    @staticmethod
    def load_dry_run_interceptor():
        """Load a special framework specific interceptor that prevents actual execution of quantum circuits. Must be implemented by the framework specific interceptors."""
        raise NotImplementedError()

    @staticmethod
    def patch_framework():
        """Apply the patch to the specific framework to intercept quantum circuit execution. Must be implemented by the framework specific interceptors."""
        raise NotImplementedError()

    @classmethod
    def get_execution_results(cls):
        """Get the list of execution results.

        This list will not contain the result of an interrupted execution!

        Returns:
            List[ExecuteResult]: the execution results
        """
        return cls._execution_results

    @classmethod
    def _set_intercepted_function(cls, method_name: str, func: Callable):
        """Set the intercepted callable.

        Args:
            method_name (str): the (unique) name of the origininal method
            func (Callable): the original/unpatched callable

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        cls._original_callables[method_name] = func

    @classmethod
    def _build_call_metadata(
        cls, method_name: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> ExecuteCallMetadata:
        """Build the basic call metadata from the method name and the function arguments."""
        return ExecuteCallMetadata(
            method_name=method_name,
            args=args,
            kwargs=kwargs,
            interceptor_arguments=BaseInterceptor._interceptor_arguments,
        )

    @classmethod
    def execute_interceptor(cls, method_name: str, *args, **kwargs):
        """Run all interceptors and call the original callable.

        Args:
            method_name (str): the (unique) name of the origininal method; used to find the original method

        Raises:
            InterceptorInterrupt: If the execution was terminated by an interceptor

        Returns:
            Any: the result of the original callable
        """
        func = cls._original_callables.get(method_name)
        if func is None:
            raise Exception(
                "Must call _set_intercepted_function before using execute_interceptor!"
            )

        execute_metadata = cls._build_call_metadata(
            method_name, args=args, kwargs=kwargs
        )

        interceptors = cls._get_interceptors()

        # run all intercept_execute interceptors
        for _, interceptor in interceptors:
            try:
                new_metadata = interceptor.intercept_execute(
                    execute_metadata=execute_metadata
                )
                if new_metadata is not None:
                    execute_metadata = new_metadata
            except NotImplementedError:
                pass

            if execute_metadata.should_terminate:
                raise InterceptorInterrupt(execute_metadata)

        # execute actual method
        result = func(*execute_metadata.args, **execute_metadata.kwargs)

        # run all intercept_execute_result interceptors
        for _, interceptor in interceptors:
            try:
                new_metadata = interceptor.intercept_execute_result(
                    result=result, execute_metadata=execute_metadata
                )
                if new_metadata is not None:
                    execute_metadata = new_metadata
            except NotImplementedError:
                pass

        # store result
        cls._execution_results.append(
            ExecuteResult(call_metadata=execute_metadata, result=result)
        )

        return result

    def intercept_execute(
        self, execute_metadata: ExecuteCallMetadata
    ) -> Optional[ExecuteCallMetadata]:
        """Intercept the execution of 'qiskit.execute' or 'DWaveSampler'.

        Args:
            execute_metadata (ExecuteCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[ExecuteCallMetadata]: a new or modified instance of the call metadata. Always copy 'execute_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()

    def intercept_execute_result(
        self, result: Any, execute_metadata: ExecuteCallMetadata
    ) -> Optional[ExecuteCallMetadata]:
        """Intercept the result of 'qiskit.execute' or 'DWaveSampler'.

        Args:
            result (Any): the result of the call to 'qiskit.execute' or 'DWaveSampler'.
            execute_metadata (ExecuteCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[ExecuteCallMetadata]: a new or modified instance of the call metadata. Always copy 'execute_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()
