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


"""Module for running a quantum circuit application and intercepting all calls of `BraketDWave sampler methods` of that application."""

from os import devnull
from contextlib import redirect_stderr, redirect_stdout, nullcontext
from pathlib import Path
from typing import Union, Tuple, NamedTuple

from .interceptor import BraketDWaveInterceptorInterrupt
from .analyze import analyze_interrupted_execution, analyze_execution_results
from .user_code_runner import run_user_code

def load_interceptors():
    """Load interceptor plugins."""
    # importing interceptors can happen dynamically later using importlib
    from . import extract_sampler_interceptor # importing already loads the plugin


def run(entry_point: Union[str, Path], s3_destination_folder: Tuple[str,str], device_arn:str, intercept: bool=False, quiet: bool=False, \
    **kwargs):
    """Run the user code given by the entry point argument.

    Args:
        entry_point (Union[str, Path]): the path + qualified method of the code to run (e.g. 'path/to/code.py' or 'path/to/module.submodule:reun_method')
        intercept (bool, optional): Wether to actually intercept the calls to `braket dave sampler methods`. Defaults to False.
        quiet (bool, optional): If True only output stdout and stderr of the user code. Defaults to False.
    """
    redirect_out, redirect_err = (redirect_stdout, redirect_stderr) if quiet else (nullcontext, nullcontext)
    with open(devnull, mode="w") as dev_null_file:
        with redirect_out(dev_null_file), redirect_err(dev_null_file):
            load_interceptors()
            if intercept:
                # import monkey patch to intercept all calls
                from . import braket_monkey_patch
        run_result = None
        try:
            run_result = run_user_code(entry_point=entry_point, s3_destination_folder=s3_destination_folder, device_arn=device_arn, **kwargs)
        except BraketDWaveInterceptorInterrupt as interrupt:
            with redirect_out(dev_null_file), redirect_err(dev_null_file):
                analyze_interrupted_execution(interrupt=interrupt)
        finally:
            with redirect_out(dev_null_file), redirect_err(dev_null_file):
                analyze_execution_results(result=run_result)
                
        return run_result