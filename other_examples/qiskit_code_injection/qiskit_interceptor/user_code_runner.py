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


from pathlib import Path
from typing import Any, Optional, Tuple, Union

def _find_user_code(entry_point: Union[str, Path]) -> Tuple[Path, Optional[str], Optional[str]]:
    """Generate a (path, package, method) triple from the given entry point.
    Args:
        entry_point (Union[str, Path]): the entry point to execute
    Raises:
        ValueError: If the entry point could not be parsed
    Returns:
        Tuple[Path, Optional[str], Optional[str]]: the (path, package, method) triple
    """
    if isinstance(entry_point, Path):
        if not entry_point.is_file():
            raise ValueError("If entry pint is a Path object it must point to a file!")
        path = entry_point.parent
        package = entry_point.name
        if package.endswith(".py"):
            package = package[:-3]
        return path, package, None
    
    *path, rest = entry_point.replace("\\", "/").split("/")
    if not rest:
        raise ValueError("Cannot parse entry point '{}'".format(entry_point))
    if rest.count(':') > 1:
        raise ValueError("Cannot parse entry point '{}'".format(entry_point))
    
    package, *method_list = rest.split(":", maxsplit=1)

    method = method_list[0] if method_list else None
 
    if package.endswith('.py'):
        package = package[:-3]
    return Path('/'.join(path)), package, method

def _run_package_as_main(package: str):
    """Run the given package as __main__.
    Args:
        package (str): the package to import and run
    """
    import runpy
    runpy.run_module(package, init_globals={}, run_name="__main__")

def _run_method_in_package(package: str, method: str, backend: str, *args, **kwargs) -> Any:
    """Run a specific method of a package.
    Args:
        package (str): The package to import
        method (str): the method to run in that package
    """
    from importlib import import_module
    imported_package = import_module(package)
    run_method = getattr(imported_package, method)
    return run_method(backend, *args, **kwargs)

def run_user_code(entry_point: Union[str, Path], backend: str, *args, **kwargs) -> Optional[Any]:
    """Run user code from the given entry_point.
    Args:
        entry_point (Union[str, Path]): the entry point of the code to run
    Raises:
        ValueError: If the entry point could not be parsed or found on disk
    """
    path, package, method = _find_user_code(entry_point=entry_point)

    if not path.exists() or not path.is_dir():
        raise ValueError("Path {} of entry point {} not found!".format(path, entry_point))

    if not package:
        raise ValueError("Cannot run empty package.")
    
    if path != Path("."):
        # update python path to make imports of the user code succeed
        import sys
        sys.path.insert(0, str(path.absolute()))
    
    if not method:
        _run_package_as_main(package)
        return None
    else:
        return _run_method_in_package(package, method=method, backend=backend, *args, **kwargs)