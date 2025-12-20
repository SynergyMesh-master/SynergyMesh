"""
Language Islands - 語言島嶼系統

多語言協作的島嶼架構，每個語言島嶼負責特定的領域任務。
"""

import importlib.util
import sys
from pathlib import Path

def _import_kebab_module(module_name: str, file_name: str):
    """Import a module with a kebab-case filename"""
    module_path = Path(__file__).parent / file_name
    if not module_path.exists():
        raise ImportError(f"Module file not found: {module_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    raise ImportError(f"Could not load module from {module_path}")

# Import base classes
_base_island = _import_kebab_module('islands.base_island', 'base-island.py')
BaseIsland = _base_island.BaseIsland
IslandStatus = _base_island.IslandStatus
Colors = _base_island.Colors

# Import individual islands
_python_island = _import_kebab_module('islands.python_island', 'python-island.py')
PythonIsland = _python_island.PythonIsland

_rust_island = _import_kebab_module('islands.rust_island', 'rust-island.py')
RustIsland = _rust_island.RustIsland

_go_island = _import_kebab_module('islands.go_island', 'go-island.py')
GoIsland = _go_island.GoIsland

_typescript_island = _import_kebab_module('islands.typescript_island', 'typescript-island.py')
TypeScriptIsland = _typescript_island.TypeScriptIsland

_java_island = _import_kebab_module('islands.java_island', 'java-island.py')
JavaIsland = _java_island.JavaIsland

# Import utilities
_island_utils = _import_kebab_module('islands.island_utils', 'island-utils.py')
print_info = _island_utils.print_info
print_success = _island_utils.print_success
print_warn = _island_utils.print_warn
print_error = _island_utils.print_error

__all__ = [
    # Base classes
    "BaseIsland",
    "IslandStatus",
    "Colors",
    # Islands
    "PythonIsland",
    "RustIsland",
    "GoIsland",
    "TypeScriptIsland",
    "JavaIsland",
    # Utilities
    "print_info",
    "print_success",
    "print_warn",
    "print_error",
]
