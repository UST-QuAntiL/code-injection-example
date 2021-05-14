# Test repo for prototyping a runner for user provided python scripts that intercepts `qiskit.execute`

## Dependecies

The dependencies for this project can be installed manually or with [Poetry](https://python-poetry.org).

 *  Python `^3.7`
 *  `qiskit==0.26.0`
 *  `click==8.0.0`

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
```

Calling `python -m module_name` executes a python module's `__main__.py` file.

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
