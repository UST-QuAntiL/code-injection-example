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


"""Analysis code called after the user code finished executing."""

from typing import Any, Optional

from pathlib import Path
from json import dumps

from .interceptor import QiskitInterceptorInterrupt, QiskitInterceptor

def analyze_execution_results(result: Optional[Any]):
    """Demo analyze method, gets called after user code finished."""
    results = QiskitInterceptor.get_execution_results() # get all results
    for index, call in enumerate(results):
        print("\nCall {}:\n".format(index + 1))
        for circuit in call.call_metadata.extra_data.get("circuits", []):
            print(circuit.draw())

    if result is None:
        return  # no result

    serialized_result: str

    if isinstance(result, str):
        print(result)  # string is directly serializable (base64)
        serialized_result = result
    elif isinstance(result, (dict, list, tuple)):
        serialized_result = dumps(result)
    else:
        print("Unserializable result type!")
        return

    with Path("./run_result.json").open(mode="w") as run_result_file:
        run_result_file.write(serialized_result)


def analyze_interrupted_execution(interrupt: QiskitInterceptorInterrupt):
    """Demo analyze method, gets called when the Qiskit interceptor interrupted normal execution."""
    # interrupt contains the call metadata of the call that was interrupted
    print("\nInterrupted call:\n")
    print(repr(interrupt.sampler_metadata))
    try:
        circuit = interrupt.sampler_metadata.termination_result
        print(circuit.draw())
    except Exception:
        pass
