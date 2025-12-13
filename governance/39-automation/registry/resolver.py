"""
Dependency Resolver - Resolve module dependencies with topological sorting.

This module provides functionality to:
- Resolve dependencies for a given module
- Detect circular dependencies
- Provide ordered activation sequence
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from .discovery import ModuleDiscovery, DiscoveredModule
except ImportError:
    from discovery import ModuleDiscovery, DiscoveredModule


logger = logging.getLogger(__name__)


class ResolutionStatus(Enum):
    """Status of dependency resolution."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CIRCULAR_DEPENDENCY = "circular_dependency"


@dataclass
class ResolutionResult:
    """Result of a dependency resolution operation."""
    status: ResolutionStatus
    resolved_order: list[str] = field(default_factory=list)
    missing_dependencies: list[str] = field(default_factory=list)
    circular_dependencies: list[list[str]] = field(default_factory=list)
    optional_available: list[str] = field(default_factory=list)
    optional_missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "resolved_order": self.resolved_order,
            "missing_dependencies": self.missing_dependencies,
            "circular_dependencies": self.circular_dependencies,
            "optional_available": self.optional_available,
            "optional_missing": self.optional_missing,
            "warnings": self.warnings,
        }


class DependencyResolver:
    """
    Resolves module dependencies using topological sorting.
    
    Features:
    - Topological sort for activation order
    - Circular dependency detection
    - Optional dependency handling
    - Missing dependency reporting
    """

    def __init__(self, discovery: ModuleDiscovery | None = None):
        """Initialize the dependency resolver."""
        self.discovery = discovery or ModuleDiscovery()
        self._modules: dict[str, DiscoveredModule] = {}

    def _ensure_modules_loaded(self) -> None:
        """Ensure modules are loaded from discovery."""
        if not self._modules:
            self._modules = self.discovery.discover_all()

    def resolve(self, module_name: str, include_optional: bool = False) -> ResolutionResult:
        """
        Resolve dependencies for a module.
        
        Args:
            module_name: Name of the module to resolve dependencies for.
            include_optional: Whether to include optional dependencies.
            
        Returns:
            ResolutionResult with the resolution status and ordered modules.
        """
        self._ensure_modules_loaded()
        
        result = ResolutionResult(status=ResolutionStatus.SUCCESS)
        
        if module_name not in self._modules:
            result.status = ResolutionStatus.FAILED
            result.missing_dependencies.append(module_name)
            result.warnings.append(f"Module '{module_name}' not found in registry")
            return result

        visited: set[str] = set()
        in_stack: set[str] = set()
        order: list[str] = []
        
        def visit(name: str, path: list[str]) -> bool:
            if name in in_stack:
                cycle = path[path.index(name):] + [name]
                result.circular_dependencies.append(cycle)
                result.status = ResolutionStatus.CIRCULAR_DEPENDENCY
                return False
            
            if name in visited:
                return True
            
            if name not in self._modules:
                result.missing_dependencies.append(name)
                return True
            
            in_stack.add(name)
            module = self._modules[name]
            
            for dep in module.dependencies:
                if not visit(dep, path + [name]):
                    return False
            
            if include_optional:
                for opt_dep in module.optional_dependencies:
                    if opt_dep in self._modules:
                        result.optional_available.append(opt_dep)
                        visit(opt_dep, path + [name])
                    else:
                        result.optional_missing.append(opt_dep)
            
            in_stack.remove(name)
            visited.add(name)
            order.append(name)
            return True

        if not visit(module_name, []):
            return result

        result.resolved_order = order

        if result.missing_dependencies:
            if result.status == ResolutionStatus.SUCCESS:
                result.status = ResolutionStatus.PARTIAL
            result.warnings.append(
                f"Missing dependencies: {', '.join(result.missing_dependencies)}"
            )

        return result

    def resolve_multiple(
        self, 
        module_names: list[str], 
        include_optional: bool = False
    ) -> ResolutionResult:
        """
        Resolve dependencies for multiple modules.
        
        Args:
            module_names: List of module names to resolve.
            include_optional: Whether to include optional dependencies.
            
        Returns:
            Combined ResolutionResult for all modules.
        """
        self._ensure_modules_loaded()
        
        combined_result = ResolutionResult(status=ResolutionStatus.SUCCESS)
        seen: set[str] = set()
        
        for module_name in module_names:
            result = self.resolve(module_name, include_optional)
            
            for mod in result.resolved_order:
                if mod not in seen:
                    combined_result.resolved_order.append(mod)
                    seen.add(mod)
            
            combined_result.missing_dependencies.extend(
                d for d in result.missing_dependencies 
                if d not in combined_result.missing_dependencies
            )
            combined_result.circular_dependencies.extend(result.circular_dependencies)
            combined_result.optional_available.extend(
                d for d in result.optional_available 
                if d not in combined_result.optional_available
            )
            combined_result.optional_missing.extend(
                d for d in result.optional_missing 
                if d not in combined_result.optional_missing
            )
            combined_result.warnings.extend(result.warnings)
            
            if result.status == ResolutionStatus.CIRCULAR_DEPENDENCY:
                combined_result.status = ResolutionStatus.CIRCULAR_DEPENDENCY
            elif result.status == ResolutionStatus.FAILED:
                if combined_result.status != ResolutionStatus.CIRCULAR_DEPENDENCY:
                    combined_result.status = ResolutionStatus.FAILED
            elif result.status == ResolutionStatus.PARTIAL:
                if combined_result.status == ResolutionStatus.SUCCESS:
                    combined_result.status = ResolutionStatus.PARTIAL

        return combined_result

    def get_dependents(self, module_name: str) -> list[str]:
        """
        Get modules that depend on the given module.
        
        Args:
            module_name: Module to find dependents for.
            
        Returns:
            List of module names that depend on this module.
        """
        self._ensure_modules_loaded()
        
        dependents = []
        for name, module in self._modules.items():
            if module_name in module.dependencies:
                dependents.append(name)
            if module_name in module.optional_dependencies:
                dependents.append(name)
        
        return dependents

    def get_dependency_tree(self, module_name: str, max_depth: int = 10) -> dict[str, Any]:
        """
        Get the dependency tree for a module.
        
        Args:
            module_name: Module to build tree for.
            max_depth: Maximum depth to traverse.
            
        Returns:
            Nested dictionary representing the dependency tree.
        """
        self._ensure_modules_loaded()
        
        def build_tree(name: str, depth: int, visited: set[str]) -> dict[str, Any]:
            if depth > max_depth or name in visited:
                return {"name": name, "truncated": True}
            
            visited = visited | {name}
            
            if name not in self._modules:
                return {"name": name, "missing": True}
            
            module = self._modules[name]
            
            children = []
            for dep in module.dependencies:
                children.append(build_tree(dep, depth + 1, visited))
            
            return {
                "name": name,
                "version": module.version,
                "status": module.status,
                "dependencies": children,
            }

        return build_tree(module_name, 0, set())

    def check_compatibility(self, modules: list[str]) -> dict[str, Any]:
        """
        Check if a set of modules are compatible with each other.
        
        Args:
            modules: List of module names to check.
            
        Returns:
            Compatibility report.
        """
        self._ensure_modules_loaded()
        
        report = {
            "compatible": True,
            "issues": [],
            "conflicts": [],
        }
        
        for module_name in modules:
            if module_name not in self._modules:
                report["compatible"] = False
                report["issues"].append(f"Module not found: {module_name}")
                continue
            
            result = self.resolve(module_name)
            
            if result.status == ResolutionStatus.CIRCULAR_DEPENDENCY:
                report["compatible"] = False
                for cycle in result.circular_dependencies:
                    report["conflicts"].append({
                        "type": "circular_dependency",
                        "modules": cycle,
                    })
            
            for missing in result.missing_dependencies:
                if missing in modules:
                    continue
                report["issues"].append(
                    f"Module '{module_name}' requires missing dependency: {missing}"
                )

        return report
