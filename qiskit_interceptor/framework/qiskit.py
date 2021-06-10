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


"""Module containing the qiskit interceptor and some helper classes."""

from inspect import signature
from typing import Any, Callable, Dict, List, Tuple, Union

from ..interceptor import BaseInterceptor, ExecuteResult

# set of supported signatures
_SUPPORTED_SIGNATURES = {
    "(experiments, backend, basis_gates=None, coupling_map=None, backend_properties=None, initial_layout=None, seed_transpiler=None, optimization_level=None, pass_manager=None, qobj_id=None, qobj_header=None, shots=None, memory=False, max_credits=None, seed_simulator=None, default_qubit_los=None, default_meas_los=None, schedule_los=None, meas_level=None, meas_return=None, memory_slots=None, memory_slot_size=None, rep_time=None, rep_delay=None, parameter_binds=None, schedule_circuit=False, inst_map=None, meas_map=None, scheduling_method=None, init_qubits=None, **run_config)",
}


class QiskitInterceptor(BaseInterceptor, framework="qiskit"):
    """Class to intercept calls to 'qiskit.execute' with."""

    # the list of interceptors
    __interceptors: List[Tuple[Union[int, float], "QiskitInterceptor"]] = []
    __interceptors_sorted: bool = False # True if the list is sorted

    # the signature of 'qiskit.execute'
    _qiskit_execute_signature: str 

    # the execution results
    _execution_results: List[ExecuteResult] = []

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


    @classmethod
    def _set_intercepted_function(cls, func: Callable):
        """Set the 'qiskit.execute' callable.

        Args:
            qiskit_execute (Callable): qiskit.execute

        Raises:
            Warning: if the signature does not match any supported signatures
        """
        execute_signature = str(signature(func))
        if execute_signature not in _SUPPORTED_SIGNATURES:
            raise Warning("The given qiskit execute funktion has an unknown signature that may not be supported!")
        QiskitInterceptor._qiskit_execute_signature = execute_signature
        super()._set_intercepted_function(func)

    @staticmethod
    def load_interceptors():
        # import extra interceptors
        from . import qiskit_extract_circuit_interceptor, qiskit_inject_aer_backend_interceptor

    @staticmethod
    def load_dry_run_interceptor():
        # import dry run interceptor
        from . import qiskit_dry_run_interceptor

    @classmethod
    def _build_call_metadata(cls, args: Tuple[Any], kwargs: Dict[str, Any]):
        metadata = super()._build_call_metadata(args=args, kwargs=kwargs)
        metadata.func = "qiskit.execute"
        return metadata

    @staticmethod
    def patch_framework():
        from functools import wraps

        import qiskit

        # pass old qiskit.execute method to QiskitInterceptor
        QiskitInterceptor._set_intercepted_function(qiskit.execute)

        @wraps(qiskit.execute)
        def new_execute(*args, **kwargs):
            return QiskitInterceptor.execute_interceptor(*args, **kwargs)

        # patch in new method
        qiskit.execute = new_execute

