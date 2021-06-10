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


"""Command line application for running user code with the interceptor."""

from os import devnull
from contextlib import redirect_stderr, redirect_stdout, nullcontext
from typing import Union, Tuple

import click as c
from . import run


@c.command("main")
@c.option("--entry-point", help="The entry point of the user code to run. (Format: './path/to/code.py' or './path/to/package.relative.subpackage:method'")
@c.option("--backend", help="The selected quantum backend.")
@c.option("--no-intercept", type=bool, default=False, is_flag=True, help="Switch off interception of any of the dwave sampler methods.")
@c.option("--dry-run", type=bool, default=False, is_flag=True, help="Dry run without executing any sampler methods.")
@c.option("--quiet", type=bool, default=False, is_flag=True, help="Suppress all console output of the dwave runner.")
def main(entry_point: str, token: str, backend: str, s3_destination_folder: Tuple[str, str], device_arn: str, no_intercept: bool=False, dry_run: bool=False, quiet: bool=False, **kwargs):
    redirect_out, redirect_err = (redirect_stdout, redirect_stderr) if quiet else (nullcontext, nullcontext)
    with open(devnull, mode="w") as dev_null_file:
        with redirect_out(dev_null_file), redirect_err(dev_null_file):
            if no_intercept:
                c.echo("Running without intercepting 'quantum and hybrid sampler methods'.")
            else:
                c.echo("Intercepting 'quantum and hybrid sampler methods'.")
                from . import dwave_monkey_patch
            if dry_run:
                c.echo("Performing dry run")
                from . import dry_run_interceptor # importing already activates the interceptor
            c.echo("Running user code '{}'.".format(entry_point))
    run(entry_point, token, backend, s3_destination_folder, device_arn, quiet=quiet, **kwargs)

# start cli
main()
