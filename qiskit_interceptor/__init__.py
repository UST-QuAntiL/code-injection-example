"""Module for running a quantum circuit application and intercepting all calls of `qiskit.execute` of that application."""

from pathlib import Path
from typing import Union

from .interceptor import QiskitInterceptorInterrupt
from .analyze import analyze_interrupted_execution, analyze_execution_results
from .user_code_runner import run_user_code

def load_interceptors():
    """Load interceptor plugins."""
    # importing interceptors can happen dynamically later using importlib
    from . import extract_circuit_interceptor # importing already loads the plugin


def run(entry_point: Union[str, Path], intercept: bool=False):
    """Run the user code given by the entry point argument.

    Args:
        entry_point (Union[str, Path]): the path + qualified method of the code to run (e.g. 'path/to/code.py' or 'path/to/module.submodule:reun_method')
        intercept (bool, optional): Wether to actually intercept the calls to `qiskit.execute`. Defaults to False.
    """
    load_interceptors()
    if intercept:
        # import monkey patch to intercept all calls
        from . import qiskit_monkey_patch
    try:
        run_user_code(entry_point=entry_point)
    except QiskitInterceptorInterrupt as interrupt:
        analyze_interrupted_execution(interrupt=interrupt)
    finally:
        analyze_execution_results()
