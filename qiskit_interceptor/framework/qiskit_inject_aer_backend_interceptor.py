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


from typing import List, Sequence, Union

from qiskit import Aer
from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.pulse.schedule import Schedule

from ..interceptor import ExecuteCallMetadata
from .qiskit import QiskitInterceptor


class InjectAerBackendInterceptor(QiskitInterceptor, priority=10):
    """Inject a qiskit backend from the interceptor arguments into the call arguments.

    Args:
        priority (int): The priority of this interceptor, this interceptor has a low priority so it runs after most other interceptors.
    """

    def intercept_execute(self, execute_metadata: ExecuteCallMetadata) -> ExecuteCallMetadata:
        backend = execute_metadata.interceptor_arguments.get("backend")
        if backend:
            # inject new backend
            injected_backend = Aer.get_backend(backend)
            if len(execute_metadata.args) >= 2:
                old_backend = execute_metadata.args[1]
                execute_metadata.args = (execute_metadata.args[0], injected_backend, *execute_metadata.args[2:])
            elif "backend" in execute_metadata.kwargs:
                old_backend = execute_metadata.kwargs["backend"]
                execute_metadata.kwargs["backend"] = injected_backend
            else:
                old_backend = None
                execute_metadata.kwargs["backend"] = injected_backend
            
            if old_backend:
                execute_metadata.extra_data["replaced_backend"] = old_backend

        return execute_metadata
