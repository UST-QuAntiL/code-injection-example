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

from contextlib import nullcontext, redirect_stderr, redirect_stdout
from json import JSONDecodeError, loads
from os import devnull
from typing import Any, Dict, Optional

import click as c

from . import run


class JSONCallArgumentsParam(c.ParamType):
    name="json-call-arguments"

    def convert(self, value: str, param: Optional[c.Parameter], ctx: Optional[c.Context]) -> Optional[Dict[str, Any]]:
        if not value:
            return None
        try:
            decoded = loads(value)
            if isinstance(decoded, list):
                # use decoded list as list of positional arguments
                return {"args": decoded}
            elif isinstance(decoded, dict):
                if set(decoded.keys()) <= {"args", "kwargs"}:
                    # decoded dict specifies positional and keyword arguments
                    return decoded
                # decoded dict only specifies keyword arguments
                return {"kwargs": decoded}
            else:
                # decoded is a single value, use as single positional argument
                return {"args": [decoded]}
        except JSONDecodeError as err:
            self.fail(f"Value '{value}' is not a valid json string!", param=param, ctx=ctx)


JSON_CALL_ARGUMENTS = JSONCallArgumentsParam()


@c.command("main")
@c.option("--entry-point", help="The entry point of the user code to run. (Format: './path/to/code.py' or './path/to/package.relative.subpackage:method')")
@c.option("--entry-point-arguments", type=JSON_CALL_ARGUMENTS, default=None, help="Arguments for the entry point as a json list or a json object. Only used if the entry point is a function!")
@c.option("--no-intercept", type=bool, default=False, is_flag=True, help="Switch off interception of the qiskit.execute method.")
@c.option("--dry-run", type=bool, default=False, is_flag=True, help="Dry run without executing any quantum circuit.")
@c.option("--quiet", type=bool, default=False, is_flag=True, help="Suppress all console output of the quiskit runner.")
def main(entry_point: str, entry_point_arguments: Optional[Dict[str, Any]]=None, no_intercept: bool=False, dry_run: bool=False, quiet: bool=False):
    redirect_out, redirect_err = (redirect_stdout, redirect_stderr) if quiet else (nullcontext, nullcontext)
    with open(devnull, mode="w") as dev_null_file:
        with redirect_out(dev_null_file), redirect_err(dev_null_file):
            if no_intercept:
                c.echo("Running without intercepting 'qiskit.execute'.")
            else:
                c.echo("Intercepting 'qiskit.execute'.")
                from . import qiskit_monkey_patch
            if dry_run:
                c.echo("Performing dry run")
                from . import \
                    dry_run_interceptor  # importing already activates the interceptor
            c.echo("Running user code '{}'.".format(entry_point))
    run(entry_point, entry_point_arguments=entry_point_arguments, quiet=quiet)

# start cli
main()
