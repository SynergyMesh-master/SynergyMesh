#!/usr/bin/env python3
"""Lightweight plugin loading primitives used across SynergyMesh.

The module exposes a minimal interface for discovering Python-based plugins,
loading them dynamically, and keeping track of active plugins in a registry.
It is intentionally small so it can be reused by both experimental scripts and
production services without pulling in additional dependencies.

Key concepts
------------
* :class:`Plugin` – base class that plugin authors inherit from. The core
  system never subclasses this type; it simply treats any class exposing the
  same interface as a plugin.
* :class:`PluginRegistry` – in-memory store of loaded plugin instances keyed by
  their ``name`` attribute.
* :class:`PluginLoader` – performs filesystem discovery for ``.py`` files and
  imports them using ``importlib``. A discovered module is expected to expose a
  ``Plugin`` class that can be instantiated without arguments.
* :class:`PluginSystem` – thin coordination wrapper that wires configuration
  into a loader instance and triggers discovery on startup.

The helpers here are intentionally opinionated: plugins are single files,
expected to define a ``Plugin`` class, and are instantiated eagerly. These
assumptions should be documented explicitly so future contributors understand
what guarantees callers rely upon.
"""
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class Plugin:
    """Base class representing a loadable unit of functionality.

    Concrete plugins should subclass this and override ``execute`` at minimum
    to implement their behavior. ``initialize`` and ``cleanup`` are provided as
    lifecycle hooks for setup/teardown, and the default implementation
    expresses the least-opinionated behavior (no-op setup and cleanup).

    Attributes
    ----------
    name:
        Human-readable identifier used as the registry key.
    version:
        Semantic or arbitrary version string advertised in logs.
    """
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
    
    def initialize(self) -> bool:
        """Prepare the plugin for use.

        Returns
        -------
        bool
            Whether initialization succeeded. The default implementation
            always returns ``True`` so subclasses only need to override this
            method when they perform work that can fail.
        """

        return True
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """Perform the plugin's primary action.

        Parameters
        ----------
        context:
            Arbitrary payload supplied by the caller. The structure of this
            data is not enforced by the framework and is defined by the plugin
            contract between caller and implementation.

        Returns
        -------
        Any
            Implementation-defined result payload.
        """

        raise NotImplementedError()
    
    def cleanup(self):
        """Release any resources allocated during execution.

        The default implementation performs no action, allowing plugins that
        do not manage external resources to remain minimal.
        """

        pass

class PluginRegistry:
    """In-memory registry of active plugins keyed by their ``name`` attribute."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
    
    def register(self, plugin: Plugin):
        """Add a plugin instance to the registry.

        Plugins are stored by name, so registering another plugin with the same
        name will overwrite the previous entry. This mirrors the expectation
        that plugin names are unique identifiers within the process.
        """

        self._plugins[plugin.name] = plugin
        logger.info(f"Plugin registered: {plugin.name} v{plugin.version}")
    
    def get(self, name: str) -> Optional[Plugin]:
        """Retrieve a plugin by its registered name."""

        return self._plugins.get(name)
    
    def list_all(self) -> List[Plugin]:
        """Return a list of all registered plugin instances."""

        return list(self._plugins.values())

class PluginLoader:
    """Filesystem-based loader responsible for discovering plugin modules."""

    def __init__(self, plugin_dirs: List[str]):
        """Create a loader configured to search the given directories."""

        self.plugin_dirs = plugin_dirs
        self.registry = PluginRegistry()
    
    def discover_plugins(self) -> List[str]:
        """Return filesystem paths to discoverable plugin modules.

        The loader searches each configured directory for ``.py`` files that do
        not start with an underscore. This allows packages to keep helper
        modules private using the conventional ``_`` prefix while still storing
        them alongside publicly loadable plugins.
        """

        discovered = []
        for plugin_dir in self.plugin_dirs:
            path = Path(plugin_dir)
            if path.exists():
                for file in path.glob("*.py"):
                    if not file.name.startswith("_"):
                        discovered.append(str(file))
        return discovered
    
    def load_plugin(self, plugin_path: str) -> Optional[Plugin]:
        """Import a plugin module and register its ``Plugin`` class instance.

        Parameters
        ----------
        plugin_path:
            Absolute or relative path to a ``.py`` file previously discovered.

        Returns
        -------
        Optional[Plugin]
            The instantiated plugin if import succeeds and the module exposes a
            ``Plugin`` attribute; otherwise ``None``. All import errors are
            logged for debugging but not raised, allowing discovery to continue
            scanning additional modules.
        """

        try:
            spec = importlib.util.spec_from_file_location("plugin", plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "Plugin"):
                plugin = module.Plugin()
                self.registry.register(plugin)
                return plugin
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
        return None

class PluginSystem:
    """Convenience wrapper that wires configuration into the plugin loader."""

    def __init__(self, config: Dict[str, Any]):
        """Create a plugin system using configuration mapping.

        Expected configuration keys
        ---------------------------
        plugin_directories:
            List of directories to scan for plugins. Non-existent paths are
            ignored so callers can share configurations across environments.
        """

        self.config = config
        self.loader = PluginLoader(config.get("plugin_directories", []))
        
    def initialize(self):
        """Discover and load plugins based on the configured directories."""

        plugins = self.loader.discover_plugins()
        logger.info(f"Discovered {len(plugins)} plugins")
        for plugin_path in plugins:
            self.loader.load_plugin(plugin_path)
