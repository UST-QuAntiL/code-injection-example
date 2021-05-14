"""Module containing the qiskit interceptor and some helper classes."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union


from inspect import signature


# set of supported signatures
_SUPPORTED_SIGNATURES = {
    "(experiments, backend, basis_gates=None, coupling_map=None, backend_properties=None, initial_layout=None, seed_transpiler=None, optimization_level=None, pass_manager=None, qobj_id=None, qobj_header=None, shots=None, memory=False, max_credits=None, seed_simulator=None, default_qubit_los=None, default_meas_los=None, schedule_los=None, meas_level=None, meas_return=None, memory_slots=None, memory_slot_size=None, rep_time=None, rep_delay=None, parameter_binds=None, schedule_circuit=False, inst_map=None, meas_map=None, scheduling_method=None, init_qubits=None, **run_config)",
}

@dataclass
class ExecuteCallMetadata():
    """Class containing all metadata (and call arguments) of a call to 'qiskit.execute'."""
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    extra_data: Dict[Any, Any] = field(default_factory=dict)
    should_terminate: bool = False
    termination_result: Optional[Any] = None

    def copy(self):
        """Create a shallow copy of the current metadata.

        Returns:
            ExecuteCallMetadata: the copied metadata
        """
        return ExecuteCallMetadata(
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
        
        call = "qiskit.execute({args})".format(args=', '.join(arguments))
        extra = "extra_data = {{ {extra_data} }}, should_terminate = {should_terminate}, termination_result = {result}".format(
            should_terminate=self.should_terminate,
            result=repr(self.termination_result),
            extra_data=', '.join("'{key}': ...".format(key=key) for key in self.extra_data.keys())
        )
        return "ExecuteCallMetadata(call='{call}', {extra})".format(call=call, extra=extra)


# A tuple containing the call metadata and the return value of that call
ExecuteResult = NamedTuple("ExecuteResult", [("call_metadata", ExecuteCallMetadata), ("result", Any)])


class QiskitInterceptorInterrupt(Exception):
    """Exception raised when a call is terminated by an interceptor."""

    execute_metadata: ExecuteCallMetadata

    def __init__(self, execute_metadata: ExecuteCallMetadata, *args: object) -> None:
        super().__init__(*args)
        self.execute_metadata = execute_metadata


class QiskitInterceptor():
    """Class to intercept calls to 'qiskit.execute' with."""

    # the list of interceptors
    __interceptors: List[Tuple[Union[int, float], "QiskitInterceptor"]] = []
    __interceptors_sorted: bool = False # True if the list is sorted

    # the 'qiskit.execute' funktion
    __qiskit_execute: Callable
    _qiskit_execute_signature: str # the signature of 'qiskit.execute'

    # the execution results
    __execute_interception_results: List[ExecuteResult] = []

    def __init_subclass__(cls, priority=0, **kwargs) -> None:
        """Register a subclass with the given priority."""
        QiskitInterceptor.__interceptors.append((priority, cls()))

    @staticmethod
    def _get_interceptors():
        """Get a list of interceptors sorted by descending priority.

        Returns:
            List[Tuple[Union[int, float], QiskitInterceptor]]: the sorted interceptors
        """
        if not QiskitInterceptor.__interceptors_sorted:
            QiskitInterceptor.__interceptors_sorted = True
            QiskitInterceptor.__interceptors.sort(key=lambda x: x[0], reverse=True)
        return QiskitInterceptor.__interceptors

    @staticmethod
    def get_execution_results():
        """Get the list of execution results.

        This list will not contain the result of an interrupted execution!

        Returns:
            List[ExecuteResult]: the execution results
        """
        return QiskitInterceptor.__execute_interception_results

    @staticmethod
    def set_qiskit_execute(qiskit_execute: Callable):
        """Set the 'qiskit.execute' callable.

        Args:
            qiskit_execute (Callable): qiskit.execute

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        execute_signature = str(signature(qiskit_execute))
        if execute_signature not in _SUPPORTED_SIGNATURES:
            raise Warning("The given qiskit execute funktion has an unknown signature that may not be supported!")
        QiskitInterceptor.__qiskit_execute = qiskit_execute
        QiskitInterceptor._qiskit_execute_signature = execute_signature

    @staticmethod
    def execute_interceptor(*args, **kwargs):
        """Run all interceptors and call 'qiskit.execute'.

        Raises:
            QiskitInterceptorInterrupt: If the execution was terminated by an interceptor

        Returns:
            Any: the result of 'qiskit.execute'
        """
        qiskit_execute = QiskitInterceptor.__qiskit_execute
        if qiskit_execute is None:
            raise Exception("Must call set_qiskit_execute before using execute_interceptor!")

        execute_metadata = ExecuteCallMetadata(args=args, kwargs=kwargs)

        # run all intercept_execute interceptors
        for _, interceptor in QiskitInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_execute(execute_metadata=execute_metadata)
                if new_metadata is not None:
                    execute_metadata = new_metadata
            except NotImplementedError:
                pass

            if execute_metadata.should_terminate:
                raise QiskitInterceptorInterrupt(execute_metadata)

        # execute actual method
        result = qiskit_execute(*execute_metadata.args, **execute_metadata.kwargs)

        # run all intercept_execute_result interceptors
        for _, interceptor in QiskitInterceptor._get_interceptors():
            try:
                new_metadata = interceptor.intercept_execute_result(result=result, execute_metadata=execute_metadata)
                if new_metadata is not None:
                    execute_metadata = new_metadata
            except NotImplementedError:
                pass

        # store result
        QiskitInterceptor.__execute_interception_results.append(ExecuteResult(call_metadata=execute_metadata, result=result));

        return result

    def intercept_execute(self, execute_metadata: ExecuteCallMetadata) -> Optional[ExecuteCallMetadata]:
        """Intercept the execution of 'qiskit.execute'.

        Args:
            execute_metadata (ExecuteCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[ExecuteCallMetadata]: a new or modified instance of the call metadata. Always copy 'execute_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()

    def intercept_execute_result(self, result: Any, execute_metadata: ExecuteCallMetadata) -> Optional[ExecuteCallMetadata]:
        """Intercept the result of 'qiskit.execute'.

        Args:
            result (Any): the result of the call to 'qiskit.execute'.
            execute_metadata (ExecuteCallMetadata): The call metadata

        Raises:
            NotImplementedError: if not implemented, the interceptor will be skipped

        Returns:
            Optional[ExecuteCallMetadata]: a new or modified instance of the call metadata. Always copy 'execute_metadata.extra_data' to the new instance!
        """
        raise NotImplementedError()
