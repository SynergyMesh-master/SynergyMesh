"""
Module Registry - Auto-selection capability for governance modules.

This package provides:
- Automatic module discovery from governance dimensions
- Capability-based module selection
- Dependency resolution
- Governance policy enforcement
"""

__version__ = "1.0.0"
__author__ = "SynergyMesh Team"

from .selector import (
    ModuleSelector,
    Module,
    ModuleInfo,
    select_modules_by_capability,
    resolve_dependencies,
    discover_all_modules,
    validate_selection,
)
from .discovery import ModuleDiscovery
from .resolver import DependencyResolver

__all__ = [
    "ModuleSelector",
    "Module",
    "ModuleInfo",
    "ModuleDiscovery",
    "DependencyResolver",
    "select_modules_by_capability",
    "resolve_dependencies",
    "discover_all_modules",
    "validate_selection",
]
