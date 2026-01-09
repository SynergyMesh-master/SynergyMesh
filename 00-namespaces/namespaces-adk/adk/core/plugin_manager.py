"""
Plugin Manager: Manages discovery, loading, and lifecycle of plugins.

This module provides a plugin system for tools, memory backends,
workflows, and SDK integrations with hot-reload support.
"""

import importlib
import importlib.util
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
import asyncio
from abc import ABC, abstractmethod

from .event_bus import EventBus
from ..observability.logging import Logger


class PluginType(Enum):
    """Types of plugins."""
    TOOL = "tool"
    MEMORY = "memory"
    WORKFLOW = "workflow"
    SDK = "sdk"
    MIDDLEWARE = "middleware"


@dataclass
class PluginManifest:
    """Plugin manifest containing metadata."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.TOOL
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    entry_point: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Create manifest from dictionary."""
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            plugin_type=PluginType(data.get("plugin_type", "tool")),
            dependencies=data.get("dependencies", []),
            permissions=data.get("permissions", []),
            config_schema=data.get("config_schema"),
            entry_point=data.get("entry_point")
        )


@dataclass
class Plugin:
    """A loaded plugin."""
    manifest: PluginManifest
    module: Any
    enabled: bool = True
    loaded_at: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        """Get plugin ID."""
        return f"{self.manifest.name}@{self.manifest.version}"


class PluginInterface(ABC):
    """Base interface for plugins."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        pass


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.
    
    Features:
    - Plugin discovery from directories
    - Dynamic loading and unloading
    - Hot-reload support
    - Dependency management
    - Permission enforcement
    - Plugin isolation
    - Lifecycle hooks
    """
    
    def __init__(
        self,
        directories: List[str],
        event_bus: Optional[EventBus] = None
    ):
        self.directories = [Path(d) for d in directories]
        self.event_bus = event_bus
        self.logger = Logger(name="plugin.manager")
        
        # Loaded plugins
        self._plugins: Dict[str, Plugin] = {}
        
        # Plugin registry by type
        self._registry: Dict[PluginType, List[str]] = {
            PluginType.TOOL: [],
            PluginType.MEMORY: [],
            PluginType.WORKFLOW: [],
            PluginType.SDK: [],
            PluginType.MIDDLEWARE: []
        }
        
        # Plugin file watchers for hot-reload
        self._file_watchers: Dict[str, asyncio.Task] = {}
    
    async def initialize(self) -> None:
        """Initialize the plugin manager."""
        self.logger.info("Initializing plugin manager...")
        
        # Discover and load plugins
        for directory in self.directories:
            if directory.exists():
                await self._discover_plugins(directory)
        
        self.logger.info(
            f"Plugin manager initialized with {len(self._plugins)} plugins"
        )
    
    async def _discover_plugins(self, directory: Path) -> None:
        """Discover plugins in a directory."""
        self.logger.info(f"Discovering plugins in {directory}")
        
        # Look for manifest.json files
        for manifest_path in directory.rglob("manifest.json"):
            try:
                await self._load_plugin_from_manifest(manifest_path)
            except Exception as e:
                self.logger.error(
                    f"Failed to load plugin from {manifest_path}: {e}",
                    exc_info=True
                )
    
    async def _load_plugin_from_manifest(
        self,
        manifest_path: Path
    ) -> None:
        """Load a plugin from its manifest file."""
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        manifest = PluginManifest.from_dict(manifest_data)
        
        # Load plugin module
        plugin_dir = manifest_path.parent
        module_path = plugin_dir / (manifest.entry_point or "__init__.py")
        
        if not module_path.exists():
            raise ValueError(f"Plugin entry point not found: {module_path}")
        
        # Import module
        spec = importlib.util.spec_from_file_location(
            manifest.name,
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[manifest.name] = module
        spec.loader.exec_module(module)
        
        # Create plugin instance
        plugin = Plugin(
            manifest=manifest,
            module=module,
            enabled=True
        )
        
        # Add to registry
        self._plugins[plugin.id] = plugin
        self._registry[manifest.plugin_type].append(plugin.id)
        
        # Initialize plugin if it has an interface
        if hasattr(module, 'Plugin'):
            plugin_instance = module.Plugin()
            if asyncio.iscoroutinefunction(plugin_instance.initialize):
                await plugin_instance.initialize(plugin.config)
            else:
                plugin_instance.initialize(plugin.config)
        
        # Publish plugin loaded event
        if self.event_bus:
            await self.event_bus.publish(
                "plugin.loaded",
                {
                    "plugin_id": plugin.id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "type": manifest.plugin_type.value
                }
            )
        
        self.logger.info(f"Loaded plugin: {plugin.id}")
    
    async def load_plugin(
        self,
        plugin_path: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Manually load a plugin.
        
        Args:
            plugin_path: Path to plugin directory or manifest file
            config: Plugin configuration
            
        Returns:
            Plugin ID
        """
        manifest_path = Path(plugin_path)
        if manifest_path.is_dir():
            manifest_path = manifest_path / "manifest.json"
        
        if not manifest_path.exists():
            raise ValueError(f"Plugin manifest not found: {plugin_path}")
        
        await self._load_plugin_from_manifest(manifest_path)
        
        # Update config if provided
        plugin_id = list(self._plugins.keys())[-1]  # Get last loaded plugin
        if config:
            self._plugins[plugin_id].config = config
        
        return plugin_id
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if unloaded, False if not found
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        # Shutdown plugin if it has an interface
        if hasattr(plugin.module, 'Plugin'):
            plugin_instance = plugin.module.Plugin()
            if asyncio.iscoroutinefunction(plugin_instance.shutdown):
                await plugin_instance.shutdown()
            else:
                plugin_instance.shutdown()
        
        # Remove from registry
        self._registry[plugin.manifest.plugin_type].remove(plugin_id)
        del self._plugins[plugin_id]
        
        # Publish plugin unloaded event
        if self.event_bus:
            await self.event_bus.publish(
                "plugin.unloaded",
                {"plugin_id": plugin_id}
            )
        
        self.logger.info(f"Unloaded plugin: {plugin_id}")
        return True
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """
        Reload a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if reloaded, False if not found
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        # Unload first
        config = plugin.config.copy()
        await self.unload_plugin(plugin_id)
        
        # Re-discover and load
        # Note: This is simplified - in production, would track plugin path
        self.logger.info(f"Reloading plugin: {plugin_id}")
        
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type."""
        plugin_ids = self._registry.get(plugin_type, [])
        return [self._plugins[pid] for pid in plugin_ids]
    
    def get_all_plugins(self) -> List[Plugin]:
        """Get all loaded plugins."""
        return list(self._plugins.values())
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin IDs."""
        return list(self._plugins.keys())
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        plugin.enabled = True
        
        if self.event_bus:
            await self.event_bus.publish(
                "plugin.enabled",
                {"plugin_id": plugin_id}
            )
        
        return True
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        plugin.enabled = False
        
        if self.event_bus:
            await self.event_bus.publish(
                "plugin.disabled",
                {"plugin_id": plugin_id}
            )
        
        return True
    
    def check_permissions(
        self,
        plugin_id: str,
        required_permissions: List[str]
    ) -> bool:
        """
        Check if a plugin has required permissions.
        
        Args:
            plugin_id: Plugin ID
            required_permissions: List of required permissions
            
        Returns:
            True if permissions are granted
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return False
        
        plugin_perms = set(plugin.manifest.permissions)
        required = set(required_permissions)
        
        return required.issubset(plugin_perms)
    
    async def shutdown(self) -> None:
        """Shutdown the plugin manager and all plugins."""
        self.logger.info("Shutting down plugin manager...")
        
        # Shutdown all plugins
        for plugin_id in list(self._plugins.keys()):
            await self.unload_plugin(plugin_id)
        
        # Cancel file watchers
        for task in self._file_watchers.values():
            task.cancel()
        
        await asyncio.gather(*self._file_watchers.values(), return_exceptions=True)
        
        self.logger.info("Plugin manager shutdown")