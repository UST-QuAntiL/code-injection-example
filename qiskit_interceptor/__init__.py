"""Module for running a quantum circuit application and intercepting all calls of `qiskit.execute` of that application."""

from os import devnull
from contextlib import redirect_stderr, redirect_stdout, nullcontext
from pathlib import Path
from typing import Union

from .interceptor import QiskitInterceptorInterrupt
from .analyze import analyze_interrupted_execution, analyze_execution_results
from .user_code_runner import run_user_code

def load_interceptors():
    """Load interceptor plugins."""
    # importing interceptors can happen dynamically later using importlib
    from . import extract_circuit_interceptor # importing already loads the plugin


def run(entry_point: Union[str, Path], intercept: bool=False, quiet: bool=False):
    """Run the user code given by the entry point argument.

    Args:
        entry_point (Union[str, Path]): the path + qualified method of the code to run (e.g. 'path/to/code.py' or 'path/to/module.submodule:reun_method')
        intercept (bool, optional): Wether to actually intercept the calls to `qiskit.execute`. Defaults to False.
        quiet (bool, optional): If True only output stdout and stderr of the user code. Defaults to False.
    """
    redirect_out, redirect_err = (redirect_stdout, redirect_stderr) if quiet else (nullcontext, nullcontext)
    with open(devnull, mode="w") as dev_null_file:
        with redirect_out(dev_null_file), redirect_err(dev_null_file):
            load_interceptors()
            if intercept:
                # import monkey patch to intercept all calls
                from . import qiskit_monkey_patch
        run_result = None
        try:
            run_result = run_user_code(entry_point=entry_point)
        except QiskitInterceptorInterrupt as interrupt:
            with redirect_out(dev_null_file), redirect_err(dev_null_file):
                analyze_interrupted_execution(interrupt=interrupt)
        finally:
            with redirect_out(dev_null_file), redirect_err(dev_null_file):
                analyze_execution_results(result=run_result)
