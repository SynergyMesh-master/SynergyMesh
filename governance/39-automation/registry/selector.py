"""
Module Selector - Capability-based module selection with auto-resolution.

Governance Namespace: governance.39-automation.registry.selector
Reference: governance/00-governance-mapping-matrix.yaml
Namespace Conventions: governance/25-principles/namespace-conventions.yaml

This module provides the main selector API for:
- Selecting modules by capability using governance namespaces
- Resolving dependencies automatically with dimension awareness
- Validating selections against governance policies
- Discovering all available modules with canonical namespace references

Namespace Format: governance.[dimension-id].[module-name].[component]
Example: governance.39-automation.registry.selector
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from .discovery import ModuleDiscovery, DiscoveredModule
    from .resolver import DependencyResolver, ResolutionResult, ResolutionStatus
except ImportError:
    from discovery import ModuleDiscovery, DiscoveredModule
    from resolver import DependencyResolver, ResolutionResult, ResolutionStatus


logger = logging.getLogger(__name__)

__governance_namespace__ = "governance.39-automation.registry.selector"
__governance_dimension__ = "39-automation"


@dataclass
class Module:
    """Represents a selected module ready for activation.
    
    Attributes:
        name: Module identifier
        version: Module version string
        entry_point: Governance-aligned Python import path
        capabilities: List of capabilities this module provides
        dependencies: List of required module names
        status: Module status (active, deprecated, etc.)
        metadata: Additional module metadata
        governance_namespace: Canonical governance namespace (e.g., governance.30-agents.mind_matrix)
        governance_dimension: Governance dimension ID (e.g., 30-agents)
    """
    name: str
    version: str
    entry_point: str
    capabilities: list[str]
    dependencies: list[str]
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    governance_namespace: str = ""
    governance_dimension: str = ""

    @classmethod
    def from_discovered(cls, discovered: DiscoveredModule) -> "Module":
        """Create a Module from a DiscoveredModule with governance namespace."""
        return cls(
            name=discovered.name,
            version=discovered.version,
            entry_point=discovered.entry_point,
            capabilities=discovered.capabilities.copy(),
            dependencies=discovered.dependencies.copy(),
            status=discovered.status,
            metadata=discovered.metadata.copy(),
            governance_namespace=discovered.metadata.get("canonical_namespace", ""),
            governance_dimension=discovered.metadata.get("governance_dimension", ""),
        )


@dataclass
class ModuleInfo:
    """Information about a module in the registry.
    
    Attributes:
        name: Module identifier
        version: Module version string
        description: Human-readable module description
        capabilities: List of capabilities this module provides
        provides: List of capabilities exposed by this module
        dependencies: List of required module names
        status: Module status (active, deprecated, etc.)
        source: Source type identifier
        governance_namespace: Canonical governance namespace
        governance_dimension: Governance dimension ID
    """
    name: str
    version: str
    description: str
    capabilities: list[str]
    provides: list[str]
    dependencies: list[str]
    status: str
    source: str
    governance_namespace: str = ""
    governance_dimension: str = ""

    @classmethod
    def from_discovered(cls, discovered: DiscoveredModule) -> "ModuleInfo":
        """Create ModuleInfo from a DiscoveredModule with governance namespace."""
        return cls(
            name=discovered.name,
            version=discovered.version,
            description=discovered.description,
            capabilities=discovered.capabilities.copy(),
            provides=discovered.provides.copy(),
            dependencies=discovered.dependencies.copy(),
            status=discovered.status,
            source=discovered.source_type,
            governance_namespace=discovered.metadata.get("canonical_namespace", ""),
            governance_dimension=discovered.metadata.get("governance_dimension", ""),
        )


@dataclass
class SelectionResult:
    """Result of a module selection operation."""
    success: bool
    modules: list[Module]
    activation_order: list[str]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    policy_violations: list[str] = field(default_factory=list)


class ModuleSelector:
    """
    Main module selector with capability-based selection and auto-resolution.
    
    Provides:
    - Capability-based module selection
    - Automatic dependency resolution
    - Governance policy enforcement
    - Module discovery and registry
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize the module selector."""
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.discovery = ModuleDiscovery(self.project_root)
        self.resolver = DependencyResolver(self.discovery)
        self._governance_policies: dict[str, Any] = {}
        self._manifest: dict[str, Any] = {}
        self._load_manifest()
        self._load_governance_policies()

    def _load_manifest(self) -> None:
        """Load the registry manifest configuration."""
        manifest_path = Path(__file__).parent / "manifest.yaml"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    self._manifest = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}")

    def _load_governance_policies(self) -> None:
        """Load governance policies for validation."""
        policies_path = self.project_root / "governance" / "23-policies"
        if not policies_path.exists():
            return
        
        for policy_file in policies_path.glob("**/*.yaml"):
            try:
                with open(policy_file, "r", encoding="utf-8") as f:
                    policy = yaml.safe_load(f)
                    if policy:
                        policy_name = policy_file.stem
                        self._governance_policies[policy_name] = policy
            except Exception as e:
                logger.debug(f"Could not load policy {policy_file}: {e}")

    def select_by_capability(
        self, 
        capabilities: list[str],
        include_dependencies: bool = True,
        include_optional: bool = False,
        validate: bool = True,
    ) -> SelectionResult:
        """
        Select modules that provide the requested capabilities.
        
        Args:
            capabilities: List of capability identifiers to select.
            include_dependencies: Whether to include required dependencies.
            include_optional: Whether to include optional dependencies.
            validate: Whether to validate against governance policies.
            
        Returns:
            SelectionResult with selected modules and activation order.
        """
        result = SelectionResult(
            success=True,
            modules=[],
            activation_order=[],
        )
        
        modules_to_activate: set[str] = set()
        
        for capability in capabilities:
            module_names = self.discovery.get_modules_by_capability(capability)
            
            if not module_names:
                result.warnings.append(f"No module provides capability: {capability}")
                continue
            
            best_match = self._select_best_module(module_names, capability)
            if best_match:
                modules_to_activate.add(best_match)

        if not modules_to_activate:
            result.success = False
            result.errors.append("No modules found for requested capabilities")
            return result

        if include_dependencies:
            resolution = self.resolver.resolve_multiple(
                list(modules_to_activate), 
                include_optional
            )
            
            if resolution.status == ResolutionStatus.CIRCULAR_DEPENDENCY:
                result.success = False
                result.errors.append("Circular dependencies detected")
                for cycle in resolution.circular_dependencies:
                    result.errors.append(f"Cycle: {' -> '.join(cycle)}")
                return result
            
            if resolution.status == ResolutionStatus.FAILED:
                result.success = False
                result.errors.extend(resolution.warnings)
                return result
            
            result.activation_order = resolution.resolved_order
            result.warnings.extend(resolution.warnings)
            
            if resolution.missing_dependencies:
                result.warnings.append(
                    f"Missing dependencies: {', '.join(resolution.missing_dependencies)}"
                )
        else:
            result.activation_order = list(modules_to_activate)

        for module_name in result.activation_order:
            discovered = self.discovery.get_module(module_name)
            if discovered:
                result.modules.append(Module.from_discovered(discovered))

        if validate:
            violations = self._validate_selection(result.activation_order)
            result.policy_violations = violations
            if violations:
                result.warnings.extend(
                    f"Policy violation: {v}" for v in violations
                )

        return result

    def _select_best_module(
        self, 
        candidates: list[str], 
        capability: str
    ) -> str | None:
        """
        Select the best module from candidates for a capability.
        
        Uses priority from manifest or defaults to first match.
        """
        if not candidates:
            return None
        
        priority_list = self._manifest.get("module_priority", {}).get(capability, [])
        
        for priority_module in priority_list:
            if priority_module in candidates:
                return priority_module
        
        for candidate in candidates:
            module = self.discovery.get_module(candidate)
            if module and module.status == "active":
                return candidate
        
        return candidates[0]

    def _validate_selection(self, modules: list[str]) -> list[str]:
        """Validate module selection against governance policies."""
        violations = []
        
        forbidden = self._manifest.get("forbidden_combinations", [])
        for combo in forbidden:
            if all(m in modules for m in combo):
                violations.append(
                    f"Forbidden combination: {', '.join(combo)}"
                )
        
        for policy_name, policy in self._governance_policies.items():
            if not isinstance(policy, dict):
                continue
            
            spec = policy.get("spec", {})
            required = spec.get("required_modules", [])
            for req in required:
                if isinstance(req, dict):
                    req_name = req.get("module", "")
                    condition = req.get("when_using", [])
                    if any(c in modules for c in condition):
                        if req_name and req_name not in modules:
                            violations.append(
                                f"Policy '{policy_name}' requires '{req_name}'"
                            )

        return violations

    def discover_all(self) -> dict[str, ModuleInfo]:
        """
        Discover and return all available modules.
        
        Returns:
            Dictionary mapping module names to ModuleInfo objects.
        """
        discovered = self.discovery.discover_all()
        return {
            name: ModuleInfo.from_discovered(module)
            for name, module in discovered.items()
        }

    def resolve_dependencies(
        self, 
        module_name: str, 
        include_optional: bool = False
    ) -> list[str]:
        """
        Resolve dependencies for a module.
        
        Args:
            module_name: Name of the module to resolve.
            include_optional: Whether to include optional dependencies.
            
        Returns:
            List of module names in activation order.
        """
        result = self.resolver.resolve(module_name, include_optional)
        return result.resolved_order

    def validate(self, modules: list[str]) -> bool:
        """
        Validate a list of modules against governance policies.
        
        Args:
            modules: List of module names to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        violations = self._validate_selection(modules)
        return len(violations) == 0

    def get_capability_matrix(self) -> dict[str, list[str]]:
        """
        Get a matrix of capabilities to modules.
        
        Returns:
            Dictionary mapping capabilities to lists of module names.
        """
        self.discovery.discover_all()
        
        matrix: dict[str, list[str]] = {}
        for capability in self.discovery.get_all_capabilities():
            matrix[capability] = self.discovery.get_modules_by_capability(capability)
        
        return matrix


_selector_instance: ModuleSelector | None = None


def _get_selector() -> ModuleSelector:
    """Get or create the global selector instance."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = ModuleSelector()
    return _selector_instance


def select_modules_by_capability(
    capabilities: list[str],
    include_dependencies: bool = True,
) -> list[Module]:
    """
    Select modules by capability (module-level function).
    
    Args:
        capabilities: List of capabilities to select.
        include_dependencies: Whether to resolve dependencies.
        
    Returns:
        List of Module objects to activate.
    """
    selector = _get_selector()
    result = selector.select_by_capability(
        capabilities, 
        include_dependencies=include_dependencies
    )
    return result.modules


def resolve_dependencies(module_name: str) -> list[str]:
    """
    Resolve dependencies for a module (module-level function).
    
    Args:
        module_name: Module to resolve dependencies for.
        
    Returns:
        List of module names in activation order.
    """
    selector = _get_selector()
    return selector.resolve_dependencies(module_name)


def discover_all_modules() -> dict[str, ModuleInfo]:
    """
    Discover all available modules (module-level function).
    
    Returns:
        Dictionary of module names to ModuleInfo.
    """
    selector = _get_selector()
    return selector.discover_all()


def validate_selection(modules: list[str]) -> bool:
    """
    Validate a module selection (module-level function).
    
    Args:
        modules: List of module names to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    selector = _get_selector()
    return selector.validate(modules)
