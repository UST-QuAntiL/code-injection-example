# Test repo for prototyping a runner for user provided python scripts that intercepts `qiskit.execute`

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Dependecies

The dependencies for this project can be installed manually or with [Poetry](https://python-poetry.org).

 *  Python `^3.7`
 *  `qiskit==0.26.2`
 *  `click==8.0.1`

Install with Poetry: `poetry install`

## Running the interceptor

If installed with poetry either run `poetry shell` to enter the venv or prefix all commands with `poetry run`.

```
# show cmd options
python -m qiskit-interceptor --help

# run the single file user code demo
python -m qiskit_interceptor --entry-point=user_code/test_file/user_code.py

# run the package user code demo as main package
python -m qiskit_interceptor --entry-point=user_code/test_package/user_code

# run the package user code demo with a custom entry point
python -m qiskit_interceptor --entry-point=user_code/test_package/user_code:run_circuit

# provide arguments for the entry point function (positional only, keyword only, both types)
python -m qiskit_interceptor --entry-point=user_code/test_package/user_code:run_circuit --entry-point-arguments='[1, 2, 3]'
python -m qiskit_interceptor --entry-point=user_code/test_package/user_code:run_circuit --entry-point-arguments='{"arg_one": "value", "arg_two": 2}'
python -m qiskit_interceptor --entry-point=user_code/test_package/user_code:run_circuit --entry-point-arguments='{"args": [1, 2, 3], "kwargs": {"arg_one": "value", "arg_two": 2}}'
```

Calling `python -m module_name` executes a python module's `__main__.py` file.

The `--quiet` flag can be used to suppress all output on stdout and stderr that is *not* from the user code.

If the entry point is a function that returned a serializable result (e.g. a string, a tuple, a list, or a dict) then the result will be written to `run_result.json`.

The interceptor can pass arguments to an entry point function with the `--entry-point-arguments` option.
The option must be a valid json object.
A list is mapped to the positional parameters of the function while a dict is mapped to the keyword arguments of the function.
If the dict contains only the keys `"args"` and `"kwargs"` then the value of `"args"` must be a list and is mapped to the positional arguments and `"kwargs"` must be a dict and is mapped to keyword arguments.


## How it works

### The qiskit monkey patch

File: `qiskit_interceptor/qiskit_monkey_patch.py`

Registers the original execute method with the `QiskitInterceptor` and sets `qiskit.execute` to a new method that calls `QiskitInterceptor.execute_interceptor`.
The new method is decorated with `functools.wraps` to copy all relevant metadata to the new method.

### The QiskitInterceptor

File: `qiskit_interceptor/interceptor.py`

The interceptor gathers all Interceptor plugins using the `__init_subclass__` hook (see [`object.__init_subclass__`](https://docs.python.org/3/reference/datamodel.html?highlight=__init_subclass__#object.__init_subclass__)).

The interceptors are sorted by a given priority (default is 0), higher priority interceptors witll be run first.

The execution results of all calls to `QiskitInterceptor.execute_interceptor` can be accessed by calling `QiskitInterceptor.get_execution_results()`.
In concurrent programs the order of the execution results may vary.

### The interceptor subclasses

Files: `qiskit_interceptor/extract_circuit_interceptor.py` and `qiskit_interceptor/dry_run_interceptor.py`

An interceptor plugin is a python class that extends `QiskitInterceptor`.
The subclass is **registered on import** by the `__init_subclass__` hook (see [`object.__init_subclass__`](https://docs.python.org/3/reference/datamodel.html?highlight=__init_subclass__#object.__init_subclass__)) of the `QiskitInterceptor`.
The priority of the interceptor can be given as a keyword argument to the class call.

An interceptor plugin can define the methods `intercept_execute` and `intercept_execute_result` which get called before and after the execution of `qiskit.execute`.
Raising a `NotImplementedError` will simply skip the interceptor.

The interceptor gets a metadata object that contains the arguments to call `qiskit.execute` with (`args` and `kwargs`), an `extra_data` dict to store data for analysis of the `intercept_execute_result` call, and `should_terminate` and `termination_result` to terminate normal execution with the termination result.
The metadata can be modified in place or a new instance can be returned.
If `should_terminate` is `True` after calling the `intercept_execute` method, then the `QiskitInterceptor` will raise a `QiskitInterceptorInterrupt` immediately.

### The user code runner

File: `qiskit_interceptor/user_code_runner.py`

The user code runner first parses the entry point and locates the user code to run.
If the entry point does not contain a method to call, then the package is imported and run as the `"__main__"` package with runpy.
Otherwise the package is imported with `importlib.import_module` and the specified method is called.

Before the user code is executed, the path the user code is in is added to the current python path.
This should allow most imports to succeed as if the module was direktly executed with python.

### Redirecting `stdout` and `stderr` for the quiet flag

This is done with the context managers provided by the python standard library: <https://docs.python.org/3/library/contextlib.html#contextlib.redirect_stdout>

Another way to use this feature would be to redirect the user code output into files.



## Acknowledgements

Current development is supported by the [Federal Ministry for Economic Affairs and Energy](http://www.bmwi.de/EN) as part of the [PlanQK](https://planqk.de) project (01MK20005N).

## Haftungsausschluss

Dies ist ein Forschungsprototyp.
Die Haftung für entgangenen Gewinn, Produktionsausfall, Betriebsunterbrechung, entgangene Nutzungen, Verlust von Daten und Informationen, Finanzierungsaufwendungen sowie sonstige Vermögens- und Folgeschäden ist, außer in Fällen von grober Fahrlässigkeit, Vorsatz und Personenschäden, ausgeschlossen.

## Disclaimer of Warranty

Unless required by applicable law or agreed to in writing, Licensor provides the Work (and each Contributor provides its Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied, including, without limitation, any warranties or conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A PARTICULAR PURPOSE.
You are solely responsible for determining the appropriateness of using or redistributing the Work and assume any risks associated with Your exercise of permissions under this License.
