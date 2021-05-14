
from typing import List, Sequence, Union
from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.pulse.schedule import Schedule

from .interceptor import ExecuteCallMetadata, QiskitInterceptor

class ExtractCircuitInterceptor(QiskitInterceptor, priority=100):
    """Extract all quantum circuits and schedules from the call arguments.

    Args:
        priority (int): The priority of this interceptor, this interceptor has a high priority so it runs before other interceptors.
            Later interceptors could use the circuit data stored in 'execute_metadata.extra_data'.
    """

    def intercept_execute(self, execute_metadata: ExecuteCallMetadata) -> ExecuteCallMetadata:
        experiments_arg = execute_metadata.kwargs.get("experiments")
        if experiments_arg is None:
            experiments_arg = execute_metadata.args[0]

        circuits: List[QuantumCircuit] = []
        schedules: List[Schedule] = []

        def _append(experiment):
            # append to the right list based on type
            if isinstance(experiments_arg, QuantumCircuit):
                circuits.append(experiments_arg)
            elif isinstance(experiments_arg, Schedule):
                schedules.append(experiments_arg)
        
        if isinstance(experiments_arg, Sequence):
            # if argument contains multiple experiments add them to the list individually
            for experiment in experiments_arg:
                _append(experiment)
        else:
            _append(experiments_arg)

        # store extracted circuits in extra_data for analysis and later interceptors
        execute_metadata.extra_data["circuits"] = circuits
        execute_metadata.extra_data["schedules"] = schedules

        return execute_metadata
