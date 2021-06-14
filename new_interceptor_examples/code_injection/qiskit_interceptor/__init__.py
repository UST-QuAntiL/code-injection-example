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


"""Module for running a quantum circuit application and intercepting all calls of `qiskit.execute` of that application
or for running q quantuym annealing sampling application and intercepting all calls of `EmbeddingComposite(DWaveSampler)` .
or `EmbeddingComposite(BraketDWaveSampler), respectively` 
"""

from contextlib import nullcontext, redirect_stderr, redirect_stdout
from os import devnull
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

from .analyze import analyze_execution_results, analyze_interrupted_execution
# import framework specific interceptors
from .framework import qiskit, dwave, braket_dwave  # noqa
from .interceptor import BaseInterceptor, InterceptorInterrupt
from .user_code_runner import run_user_code


def run(entry_point: Union[str, Path], entry_point_arguments: Optional[Dict[str, Union[Sequence[Any], Dict[str, Any]]]]=None, framework: str="qiskit", intercept: bool=False, dry_run: bool=False, quiet: bool=False):
    """Run the user code given by the entry point argument.

    Args:
        entry_point (Union[str, Path]): the path + qualified method of the code to run (e.g. 'path/to/code.py' or 'path/to/module.submodule:reun_method')
        entry_point_arguments ({"args": Sequence[Any], "kwargs": Dict[str, Any]}): A dict containing the positional and keyword arguments to pass to the entry point function. Defaults to None.
        framework (str): the quantum framework used by the user code
        intercept (bool, optional): Wether to actually intercept the calls to the framework execute function. Defaults to False.
        intercept (bool, optional): Wether to actually run the quantum circuit. If true the dry run interceptor for the framework is loaded. Defaults to False.
        quiet (bool, optional): If True only output stdout and stderr of the user code. Defaults to False.
    """
    interceptor = BaseInterceptor.get_interceptor_for_framework(framework=framework)
    redirect_out, redirect_err = (redirect_stdout, redirect_stderr) if quiet else (nullcontext, nullcontext)
    with open(devnull, mode="w") as dev_null_file:
        with redirect_out(dev_null_file), redirect_err(dev_null_file):
            interceptor.load_interceptors()
            if intercept:
                interceptor.patch_framework()
            if dry_run:
                interceptor.load_dry_run_interceptor()
        run_result = None
        try:
            run_result = run_user_code(entry_point=entry_point, entry_point_arguments=entry_point_arguments)
        except InterceptorInterrupt as interrupt:
            with redirect_out(dev_null_file), redirect_err(dev_null_file):
                analyze_interrupted_execution(interrupt=interrupt, interceptor=interceptor)
        finally:
            with redirect_out(dev_null_file), redirect_err(dev_null_file):
                analyze_execution_results(result=run_result, interceptor=interceptor)
        return run_result
