"""Analysis code called after the user code finished executing."""

from .interceptor import QiskitInterceptorInterrupt, QiskitInterceptor

def analyze_execution_results():
    """Demo analyze method, gets called after user code finished."""
    results = QiskitInterceptor.get_execution_results() # get all results
    for index, call in enumerate(results):
        print("\nCall {}:\n".format(index + 1))
        for circuit in call.call_metadata.extra_data.get("circuits", []):
            print(circuit.draw())


def analyze_interrupted_execution(interrupt: QiskitInterceptorInterrupt):
    """Demo analyze method, gets called when the Qiskit interceptor interrupted normal execution."""
    # interrupt contains the call metadata of the call that was interrupted
    print("\nInterrupted call:\n")
    print(repr(interrupt.execute_metadata))
    try:
        circuit = interrupt.execute_metadata.termination_result
        print(circuit.draw())
    except Exception:
        pass
