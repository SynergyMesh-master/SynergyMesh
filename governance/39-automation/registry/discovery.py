"""
Module Discovery - Automatic module discovery from governance dimensions.

This module provides functionality to discover modules from:
- governance/36-modules/*.yaml
- core/modules/__init__.py MODULE_REGISTRY
- governance/37-behavior-contracts/*.yaml for capabilities
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)


@dataclass
class DiscoveredModule:
    """Represents a discovered module with its metadata."""
    name: str
    version: str
    status: str
    description: str
    entry_point: str
    capabilities: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    source_path: str = ""
    source_type: str = "yaml"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "description": self.description,
            "entry_point": self.entry_point,
            "capabilities": self.capabilities,
            "provides": self.provides,
            "dependencies": self.dependencies,
            "optional_dependencies": self.optional_dependencies,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "metadata": self.metadata,
        }


class ModuleDiscovery:
    """
    Discovers modules from governance dimensions and core registries.
    
    Scans:
    - governance/36-modules/*.yaml for module specifications
    - governance/37-behavior-contracts/*.yaml for behavior contracts
    - core/modules/__init__.py for the MODULE_REGISTRY
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize the module discovery system."""
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.modules_path = self.project_root / "governance" / "36-modules"
        self.contracts_path = self.project_root / "governance" / "37-behavior-contracts"
        self.core_modules_path = self.project_root / "core" / "modules"
        self._cache: dict[str, DiscoveredModule] = {}
        self._capability_index: dict[str, list[str]] = {}

    def discover_all(self) -> dict[str, DiscoveredModule]:
        """
        Discover all modules from all sources.
        
        Returns:
            Dictionary mapping module names to DiscoveredModule objects.
        """
        self._cache.clear()
        self._capability_index.clear()
        
        self._discover_from_yaml_modules()
        self._discover_from_core_registry()
        self._enrich_with_behavior_contracts()
        self._build_capability_index()
        
        logger.info(f"Discovered {len(self._cache)} modules")
        return self._cache.copy()

    def _discover_from_yaml_modules(self) -> None:
        """Discover modules from governance/36-modules/*.yaml files."""
        if not self.modules_path.exists():
            logger.warning(f"Modules path not found: {self.modules_path}")
            return

        for yaml_file in self.modules_path.glob("*.yaml"):
            if yaml_file.name in ("dimension.yaml", "schema.json"):
                continue
            
            try:
                self._parse_module_yaml(yaml_file)
            except Exception as e:
                logger.error(f"Failed to parse {yaml_file}: {e}")

    def _parse_module_yaml(self, yaml_file: Path) -> None:
        """Parse a module YAML file and extract module information."""
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        module_name = data.get("module", yaml_file.stem)
        
        capabilities = []
        provides = []
        if "capabilities" in data:
            for cap in data["capabilities"]:
                cap_id = cap.get("id", "")
                if cap_id:
                    capabilities.append(cap_id)
        
        if "provides" in data:
            provides = data["provides"] if isinstance(data["provides"], list) else []

        dependencies = []
        optional_deps = []
        if "depends_on" in data:
            deps = data["depends_on"]
            if isinstance(deps, dict):
                for req in deps.get("required", []):
                    if isinstance(req, dict):
                        dependencies.append(req.get("module", ""))
                    else:
                        dependencies.append(str(req))
                for opt in deps.get("optional", []):
                    if isinstance(opt, dict):
                        optional_deps.append(opt.get("module", ""))
                    else:
                        optional_deps.append(str(opt))

        entry_point = ""
        if "tech_stack" in data:
            entry_point = f"{module_name.replace('.', '/')}"

        module = DiscoveredModule(
            name=module_name,
            version=data.get("version", "1.0.0"),
            status=data.get("status", "active"),
            description=data.get("role_description", data.get("description", "")),
            entry_point=entry_point,
            capabilities=capabilities,
            provides=provides,
            dependencies=[d for d in dependencies if d],
            optional_dependencies=[d for d in optional_deps if d],
            source_path=str(yaml_file),
            source_type="yaml",
            metadata={
                "role": data.get("role", ""),
                "owner": data.get("ownership", {}).get("primary_owner", ""),
                "lifecycle": data.get("lifecycle", {}),
            }
        )
        
        self._cache[module_name] = module

    def _discover_from_core_registry(self) -> None:
        """Discover modules from core/modules/__init__.py MODULE_REGISTRY."""
        try:
            from core.modules import MODULE_REGISTRY
            
            for name, info in MODULE_REGISTRY.items():
                if name in self._cache:
                    continue
                
                module = DiscoveredModule(
                    name=name,
                    version="1.0.0",
                    status="active",
                    description=info.get("description", ""),
                    entry_point=info.get("entry_point", ""),
                    capabilities=[],
                    provides=[],
                    dependencies=info.get("dependencies", []),
                    optional_dependencies=[],
                    source_path=str(self.core_modules_path / "__init__.py"),
                    source_type="python",
                    metadata={}
                )
                self._cache[name] = module
                
        except ImportError as e:
            logger.warning(f"Could not import core.modules: {e}")

    def _enrich_with_behavior_contracts(self) -> None:
        """Enrich modules with behavior contract information."""
        if not self.contracts_path.exists():
            return

        for yaml_file in self.contracts_path.glob("*.yaml"):
            if yaml_file.name in ("dimension.yaml", "schema.json"):
                continue
            
            try:
                self._parse_behavior_contract(yaml_file)
            except Exception as e:
                logger.error(f"Failed to parse contract {yaml_file}: {e}")

    def _parse_behavior_contract(self, yaml_file: Path) -> None:
        """Parse a behavior contract and enrich corresponding module."""
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        contract = data.get("contract", {})
        module_name = contract.get("module", yaml_file.stem)
        
        if module_name not in self._cache:
            return

        module = self._cache[module_name]
        
        if "api" in data:
            api_data = data["api"]
            endpoints = api_data.get("endpoints", [])
            for endpoint in endpoints:
                name = endpoint.get("name", "")
                if name:
                    cap_id = name.lower().replace(" ", "_")
                    if cap_id not in module.capabilities:
                        module.capabilities.append(cap_id)

        if "events" in data:
            for event in data["events"]:
                event_name = event.get("name", "")
                if event_name and event_name not in module.provides:
                    module.provides.append(event_name)

    def _build_capability_index(self) -> None:
        """Build an index mapping capabilities to modules."""
        self._capability_index.clear()
        
        for module_name, module in self._cache.items():
            for capability in module.capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = []
                self._capability_index[capability].append(module_name)
            
            for provided in module.provides:
                if provided not in self._capability_index:
                    self._capability_index[provided] = []
                if module_name not in self._capability_index[provided]:
                    self._capability_index[provided].append(module_name)

    def get_modules_by_capability(self, capability: str) -> list[str]:
        """
        Get module names that provide a specific capability.
        
        Args:
            capability: The capability to search for.
            
        Returns:
            List of module names providing the capability.
        """
        if not self._cache:
            self.discover_all()
        
        return self._capability_index.get(capability, [])

    def get_module(self, name: str) -> DiscoveredModule | None:
        """
        Get a specific module by name.
        
        Args:
            name: Module name to look up.
            
        Returns:
            DiscoveredModule if found, None otherwise.
        """
        if not self._cache:
            self.discover_all()
        
        return self._cache.get(name)

    def get_all_capabilities(self) -> list[str]:
        """Get a list of all available capabilities."""
        if not self._cache:
            self.discover_all()
        
        return list(self._capability_index.keys())

    def search_modules(
        self, 
        query: str = "", 
        status: str | None = None,
        has_capability: str | None = None
    ) -> list[DiscoveredModule]:
        """
        Search for modules matching criteria.
        
        Args:
            query: Text to search in name/description.
            status: Filter by status (active, deprecated, etc).
            has_capability: Filter by capability.
            
        Returns:
            List of matching modules.
        """
        if not self._cache:
            self.discover_all()
        
        results = []
        for module in self._cache.values():
            if query and query.lower() not in module.name.lower():
                if query.lower() not in module.description.lower():
                    continue
            
            if status and module.status != status:
                continue
            
            if has_capability and has_capability not in module.capabilities:
                if has_capability not in module.provides:
                    continue
            
            results.append(module)
        
        return results
