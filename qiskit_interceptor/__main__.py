"""Command line application for running user code with the interceptor."""

from os import devnull
from contextlib import redirect_stderr, redirect_stdout, nullcontext

import click as c
from . import run



@c.command("main")
@c.option("--entry-point", help="The entry point of the user code to run. (Format: './path/to/code.py' or './path/to/package.relative.subpackage:method'")
@c.option("--no-intercept", type=bool, default=False, is_flag=True, help="Switch off interception of the qiskit.execute method.")
@c.option("--dry-run", type=bool, default=False, is_flag=True, help="Dry run without executing any quantum circuit.")
@c.option("--quiet", type=bool, default=False, is_flag=True, help="Suppress all console output of the quiskit runner.")
def main(entry_point: str, no_intercept: bool=False, dry_run: bool=False, quiet: bool=False):
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
                from . import dry_run_interceptor # importing already activates the interceptor
            c.echo("Running user code '{}'.".format(entry_point))
    run(entry_point, quiet=quiet)

# start cli
main()
