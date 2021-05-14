"""Command line application for running user code with the interceptor."""

import click as c
from . import run

@c.command("main")
@c.option("--entry-point", help="The entry point of the user code to run. (Format: './path/to/code.py' or './path/to/package.relative.subpackage:method'")
@c.option("--no-intercept", type=bool, default=False, is_flag=True, help="Switch off interception of the qiskit.execute method.")
@c.option("--dry-run", type=bool, default=False, is_flag=True, help="Dry run without executing any quantum circuit.")
def main(entry_point: str, no_intercept: bool=False, dry_run: bool=False):
    if no_intercept:
        c.echo("Running without intercepting 'qiskit.execute'.")
    else:
        c.echo("Intercepting 'qiskit.execute'.")
        from . import qiskit_monkey_patch
    if dry_run:
        c.echo("Performing dry run")
        from . import dry_run_interceptor # importing already activates the interceptor
    c.echo("Running user code '{}'.".format(entry_point))
    run(entry_point)

# start cli
main()
