"""
Language Islands - 語言島嶼系統

多語言協作的島嶼架構，每個語言島嶼負責特定的領域任務。
"""

import importlib.util
import sys
from pathlib import Path

def _import_kebab_module(module_alias: str, file_name: str, legacy_alias: str | None = None):
    """
    Import a module from a kebab-case filename and register module aliases.

    This helper loads a module object from ``file_name`` (e.g. ``"python-island.py"``)
    and registers it in ``sys.modules`` under two possible names:

    * ``qualified_name`` – the primary name, built as ``f"{__name__}.{module_alias}"``.
      Here ``module_alias`` is the underscore-based short name of the island
      (e.g. ``"python_island"``), not a full module path.
    * ``legacy_alias`` – an optional fully qualified import path used for
      backwards compatibility (e.g. ``"islands.python_island"``). When provided,
      it is also mapped to the same module object in ``sys.modules``.

    This ensures that both the new namespaced form (``qualified_name``) and any
    older dotted-path aliases continue to resolve to the same module.
    """
    module_path = Path(__file__).parent / file_name
    if not module_path.exists():
        raise ImportError(f"Module file not found: {module_path}")
    qualified_name = f"{__name__}.{module_alias}"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        if legacy_alias:
            sys.modules[legacy_alias] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            # Clean up partially-initialized modules from sys.modules on failure
            sys.modules.pop(qualified_name, None)
            if legacy_alias:
                sys.modules.pop(legacy_alias, None)
            raise
        return module
    raise ImportError(f"Could not load module from {module_path}")

# Import base classes
_base_island = _import_kebab_module('base_island', 'base-island.py', legacy_alias='islands.base_island')
BaseIsland = _base_island.BaseIsland
IslandStatus = _base_island.IslandStatus
Colors = _base_island.Colors

# Import individual islands
_python_island = _import_kebab_module('python_island', 'python-island.py', legacy_alias='islands.python_island')
PythonIsland = _python_island.PythonIsland

_rust_island = _import_kebab_module('rust_island', 'rust-island.py', legacy_alias='islands.rust_island')
RustIsland = _rust_island.RustIsland

_go_island = _import_kebab_module('go_island', 'go-island.py', legacy_alias='islands.go_island')
GoIsland = _go_island.GoIsland

_typescript_island = _import_kebab_module('typescript_island', 'typescript-island.py', legacy_alias='islands.typescript_island')
TypeScriptIsland = _typescript_island.TypeScriptIsland

_java_island = _import_kebab_module('java_island', 'java-island.py', legacy_alias='islands.java_island')
JavaIsland = _java_island.JavaIsland

# Import utilities
_island_utils = _import_kebab_module('island_utils', 'island-utils.py', legacy_alias='islands.island_utils')
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
