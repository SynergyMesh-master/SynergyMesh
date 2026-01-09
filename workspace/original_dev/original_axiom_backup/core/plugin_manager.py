"""
AXIOM Plugin Manager - Core Implementation
Provides hot-swappable, thread-safe plugin management with zero downtime.
"""

import importlib.util
import inspect
import threading
import time
import traceback
import weakref
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for loaded plugins"""
    plugin_id: str
    version: str
    priority: int
    enabled: bool
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    load_time: float = field(default_factory=time.time)
    module_path: str = ""
    plugin_class: Optional[Type] = None


@dataclass
class PluginExecutionResult:
    """Result of plugin execution"""
    plugin_id: str
    status: str
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class PluginValidationError(Exception):
    """Raised when plugin fails validation"""
    pass


class PluginLoadError(Exception):
    """Raised when plugin fails to load"""
    pass


class AxiomPluginManager:
    """
    Core plugin manager with hot-swap capabilities and thread safety.
    Supports dynamic loading/unloading without system restart.
    """
    
    def __init__(self, max_workers: int = 32):
        self.plugins: Dict[str, PluginMetadata] = {}
        self.plugin_instances: Dict[str, Any] = {}
        self.lock = threading.RLock()  # Reentrant lock for nested operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.interface_spec = self._load_interface_spec()
        self.dependency_graph = {}
        self.hot_swap_enabled = True
        self._setup_weak_references()
        
    def _setup_weak_references(self):
        """Setup weak references for automatic cleanup"""
        self._instance_refs = weakref.WeakValueDictionary()
        
    def _load_interface_spec(self) -> dict:
        """Load plugin interface specification"""
        spec_path = Path(__file__).parent.parent / "standards" / "plugin_interface_v1.yaml"
        try:
            with open(spec_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load interface spec: {e}")
            raise
            
    def load_plugin(self, plugin_path: str, config: dict) -> bool:
        """
        Dynamically load a plugin with validation and hot-swap support.
        
        Args:
            plugin_path: Path to plugin file
            config: Plugin configuration
            
        Returns:
            bool: True if plugin loaded successfully
        """
        with self.lock:
            start_time = time.time()
            
            try:
                # Validate configuration
                self._validate_plugin_config(config)
                
                # Check if plugin already loaded
                plugin_id = config['plugin_id']
                if plugin_id in self.plugins:
                    if self.hot_swap_enabled:
                        logger.info(f"Hot-swapping plugin: {plugin_id}")
                        self._unload_plugin_internal(plugin_id)
                    else:
                        raise PluginLoadError(f"Plugin {plugin_id} already loaded")
                
                # Load plugin module
                plugin_instance = self._load_plugin_module(plugin_path, config)
                
                # Validate plugin interface
                self._validate_plugin_interface(plugin_instance.__class__)
                
                # Initialize plugin
                init_start = time.time()
                if not plugin_instance.initialize(config):
                    raise PluginLoadError(f"Plugin {plugin_id} initialization failed")
                
                init_time = time.time() - init_start
                
                # Validate performance constraints
                if init_time > 0.1:  # 100ms limit
                    logger.warning(f"Plugin {plugin_id} init time {init_time:.3f}s exceeds 100ms limit")
                
                # Store plugin metadata and instance
                metadata = PluginMetadata(
                    plugin_id=plugin_id,
                    version=config['version'],
                    priority=config['priority'],
                    enabled=config['enabled'],
                    dependencies=config.get('dependencies', []),
                    config=config,
                    module_path=plugin_path,
                    plugin_class=plugin_instance.__class__
                )
                
                self.plugins[plugin_id] = metadata
                self.plugin_instances[plugin_id] = plugin_instance
                self._instance_refs[plugin_id] = plugin_instance
                
                # Update dependency graph
                self._update_dependency_graph(plugin_id, metadata.dependencies)
                
                load_time = time.time() - start_time
                logger.info(f"Plugin {plugin_id} loaded successfully in {load_time:.3f}s")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_path}: {e}")
                logger.debug(traceback.format_exc())
                return False
                
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Safely unload a plugin with cleanup and dependency checking.
        
        Args:
            plugin_id: ID of plugin to unload
            
        Returns:
            bool: True if plugin unloaded successfully
        """
        with self.lock:
            return self._unload_plugin_internal(plugin_id)
            
    def _unload_plugin_internal(self, plugin_id: str) -> bool:
        """Internal unload method (requires lock)"""
        if plugin_id not in self.plugins:
            logger.warning(f"Plugin {plugin_id} not found for unload")
            return False
            
        # Check for dependent plugins
        dependents = self._find_dependent_plugins(plugin_id)
        if dependents:
            logger.warning(f"Cannot unload {plugin_id}: has dependents {dependents}")
            return False
            
        try:
            # Teardown plugin
            plugin_instance = self.plugin_instances.get(plugin_id)
            if plugin_instance:
                teardown_start = time.time()
                
                if hasattr(plugin_instance, 'teardown'):
                    teardown_success = plugin_instance.teardown()
                    if not teardown_success:
                        logger.warning(f"Plugin {plugin_id} teardown failed")
                
                teardown_time = time.time() - teardown_start
                
                # Validate teardown time constraint
                if teardown_time > 0.05:  # 50ms limit
                    logger.warning(f"Plugin {plugin_id} teardown time {teardown_time:.3f}s exceeds 50ms limit")
            
            # Remove from registry
            del self.plugins[plugin_id]
            if plugin_id in self.plugin_instances:
                del self.plugin_instances[plugin_id]
                
            # Update dependency graph
            self._remove_from_dependency_graph(plugin_id)
            
            logger.info(f"Plugin {plugin_id} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
            
    def execute_plugin(self, plugin_id: str, context: dict, timeout: Optional[float] = None) -> PluginExecutionResult:
        """
        Execute a plugin with context and timeout support.
        
        Args:
            plugin_id: ID of plugin to execute
            context: Execution context
            timeout: Execution timeout in seconds
            
        Returns:
            PluginExecutionResult: Execution result
        """
        if plugin_id not in self.plugin_instances:
            return PluginExecutionResult(
                plugin_id=plugin_id,
                status="FAILED",
                result={},
                execution_time=0.0,
                error="Plugin not found"
            )
            
        try:
            # Validate context
            self._validate_execution_context(context)
            
            plugin_instance = self.plugin_instances[plugin_id]
            start_time = time.time()
            
            # Execute with timeout if specified
            if timeout:
                future = self.executor.submit(plugin_instance.execute, context)
                result = future.result(timeout=timeout)
            else:
                result = plugin_instance.execute(context)
            
            execution_time = time.time() - start_time
            
            # Validate result format
            self._validate_execution_result(result)
            
            return PluginExecutionResult(
                plugin_id=plugin_id,
                status=result.get('status', 'FAILED'),
                result=result,
                execution_time=execution_time,
                error=result.get('error'),
                warnings=result.get('warnings', [])
            )
            
        except TimeoutError:
            return PluginExecutionResult(
                plugin_id=plugin_id,
                status="FAILED",
                result={},
                execution_time=timeout or 0.0,
                error=f"Execution timeout after {timeout}s"
            )
        except Exception as e:
            logger.error(f"Plugin {plugin_id} execution failed: {e}")
            return PluginExecutionResult(
                plugin_id=plugin_id,
                status="FAILED",
                result={},
                execution_time=time.time() - start_time if 'start_time' in locals() else 0.0,
                error=str(e)
            )
            
    def execute_plugin_chain(self, plugin_ids: List[str], context: dict, 
                           parallel: bool = False) -> List[PluginExecutionResult]:
        """
        Execute a chain of plugins with dependency resolution.
        
        Args:
            plugin_ids: List of plugin IDs to execute
            context: Shared execution context
            parallel: Execute plugins in parallel (if no dependencies)
            
        Returns:
            List[PluginExecutionResult]: Results for each plugin
        """
        with self.lock:
            # Resolve execution order
            execution_order = self._resolve_execution_order(plugin_ids)
            
            results = []
            
            if parallel and len(execution_order) == 1:
                # Parallel execution for independent plugins
                futures = {}
                for plugin_id in execution_order[0]:
                    future = self.executor.submit(self.execute_plugin, plugin_id, context.copy())
                    futures[plugin_id] = future
                
                for plugin_id, future in futures.items():
                    result = future.result()
                    results.append(result)
                    
            else:
                # Sequential execution respecting dependencies
                for level_plugins in execution_order:
                    for plugin_id in level_plugins:
                        result = self.execute_plugin(plugin_id, context.copy())
                        results.append(result)
                        
                        # Stop on failure
                        if result.status == "FAILED":
                            logger.error(f"Stopping execution chain due to failure in {plugin_id}")
                            break
                            
            return results
            
    def validate_plugin(self, plugin_id: str) -> dict:
        """
        Validate plugin health and status.
        
        Args:
            plugin_id: ID of plugin to validate
            
        Returns:
            dict: Validation result
        """
        if plugin_id not in self.plugin_instances:
            return {"status": "FAILED", "error": "Plugin not found"}
            
        try:
            plugin_instance = self.plugin_instances[plugin_id]
            validation_result = plugin_instance.validate()
            
            # Add metadata to validation result
            metadata = self.plugins[plugin_id]
            validation_result.update({
                "plugin_id": plugin_id,
                "version": metadata.version,
                "load_time": metadata.load_time,
                "dependencies": metadata.dependencies,
                "enabled": metadata.enabled
            })
            
            return validation_result
            
        except Exception as e:
            return {
                "status": "FAILED",
                "error": f"Validation failed: {str(e)}",
                "plugin_id": plugin_id
            }
            
    def list_plugins(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all loaded plugins with metadata.
        
        Args:
            enabled_only: Show only enabled plugins
            
        Returns:
            List of plugin metadata dictionaries
        """
        plugins_list = []
        
        for plugin_id, metadata in self.plugins.items():
            if enabled_only and not metadata.enabled:
                continue
                
            plugins_list.append({
                "plugin_id": plugin_id,
                "version": metadata.version,
                "priority": metadata.priority,
                "enabled": metadata.enabled,
                "dependencies": metadata.dependencies,
                "load_time": metadata.load_time,
                "module_path": metadata.module_path
            })
            
        return sorted(plugins_list, key=lambda x: x['priority'])
        
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get current dependency graph"""
        return self.dependency_graph.copy()
        
    def _load_plugin_module(self, plugin_path: str, config: dict) -> Any:
        """Load and instantiate plugin module"""
        if not Path(plugin_path).exists():
            raise PluginLoadError(f"Plugin file not found: {plugin_path}")
            
        # Dynamic import
        spec = importlib.util.spec_from_file_location(config['plugin_id'], plugin_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Failed to load spec from {plugin_path}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get plugin class
        if not hasattr(module, 'Plugin'):
            raise PluginLoadError(f"Plugin class not found in {plugin_path}")
            
        plugin_class = getattr(module, 'Plugin')
        
        # Instantiate plugin
        plugin_instance = plugin_class()
        
        return plugin_instance
        
    def _validate_plugin_config(self, config: dict) -> None:
        """Validate plugin configuration against schema"""
        required_fields = ['plugin_id', 'version', 'priority', 'enabled']
        
        for field in required_fields:
            if field not in config:
                raise PluginValidationError(f"Missing required field: {field}")
                
        # Validate plugin_id format
        plugin_id = config['plugin_id']
        if not isinstance(plugin_id, str) or len(plugin_id) < 3 or len(plugin_id) > 64:
            raise PluginValidationError("Invalid plugin_id format")
            
        # Validate version format
        version = config['version']
        if not isinstance(version, str) or not self._is_valid_semver(version):
            raise PluginValidationError("Invalid version format, expected semver (x.y.z)")
            
        # Validate priority range
        priority = config['priority']
        if not isinstance(priority, int) or priority < 1 or priority > 100:
            raise PluginValidationError("Priority must be integer between 1-100")
            
    def _is_valid_semver(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
        
    def _validate_plugin_interface(self, plugin_class: Type) -> None:
        """Validate plugin class implements required methods"""
        required_methods = self.interface_spec['required_methods']
        
        for method_name, method_spec in required_methods.items():
            if not hasattr(plugin_class, method_name):
                raise PluginValidationError(f"Missing required method: {method_name}")
                
            # Check method signature (basic validation)
            method = getattr(plugin_class, method_name)
            if not callable(method):
                raise PluginValidationError(f"Method {method_name} is not callable")
                
    def _validate_execution_context(self, context: dict) -> None:
        """Validate execution context"""
        required_fields = self.interface_spec['execution_context']['required_fields']
        
        for field in required_fields:
            if field not in context:
                raise PluginValidationError(f"Missing required context field: {field}")
                
    def _validate_execution_result(self, result: dict) -> None:
        """Validate plugin execution result"""
        if not isinstance(result, dict):
            raise PluginValidationError("Plugin result must be a dictionary")
            
        if 'status' not in result:
            raise PluginValidationError("Plugin result must include 'status' field")
            
        valid_statuses = ['SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'SKIPPED']
        if result['status'] not in valid_statuses:
            raise PluginValidationError(f"Invalid status: {result['status']}")
            
    def _update_dependency_graph(self, plugin_id: str, dependencies: List[str]) -> None:
        """Update dependency graph for loaded plugin"""
        self.dependency_graph[plugin_id] = dependencies
        
    def _remove_from_dependency_graph(self, plugin_id: str) -> None:
        """Remove plugin from dependency graph"""
        if plugin_id in self.dependency_graph:
            del self.dependency_graph[plugin_id]
            
        # Remove from other plugins' dependencies
        for deps in self.dependency_graph.values():
            if plugin_id in deps:
                deps.remove(plugin_id)
                
    def _find_dependent_plugins(self, plugin_id: str) -> List[str]:
        """Find plugins that depend on the given plugin"""
        dependents = []
        for pid, deps in self.dependency_graph.items():
            if plugin_id in deps:
                dependents.append(pid)
        return dependents
        
    def _resolve_execution_order(self, plugin_ids: List[str]) -> List[List[str]]:
        """
        Resolve plugin execution order using topological sort.
        Returns list of execution levels, where plugins in the same level can run in parallel.
        """
        # Build subgraph for requested plugins
        subgraph = {}
        for plugin_id in plugin_ids:
            if plugin_id in self.dependency_graph:
                subgraph[plugin_id] = [
                    dep for dep in self.dependency_graph[plugin_id] 
                    if dep in plugin_ids
                ]
            else:
                subgraph[plugin_id] = []
                
        # Topological sort with level detection
        in_degree = {pid: 0 for pid in subgraph}
        for pid, deps in subgraph.items():
            for dep in deps:
                in_degree[pid] += 1
                
        # Kahn's algorithm for topological sort
        queue = [pid for pid in in_degree if in_degree[pid] == 0]
        execution_levels = []
        
        while queue:
            current_level = queue.copy()
            queue = []
            
            for pid in current_level:
                # Remove processed node
                if pid in in_degree:
                    del in_degree[pid]
                    
                # Update neighbors
                for neighbor, deps in subgraph.items():
                    if pid in deps:
                        deps.remove(pid)
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
                            
            if current_level:
                execution_levels.append(current_level)
                
        # Check for circular dependencies
        if in_degree:
            raise PluginValidationError(f"Circular dependency detected: {list(in_degree.keys())}")
            
        return execution_levels
        
    def shutdown(self) -> None:
        """Shutdown plugin manager and cleanup all plugins"""
        logger.info("Shutting down plugin manager...")
        
        with self.lock:
            # Unload all plugins in reverse dependency order
            try:
                execution_order = self._resolve_execution_order(list(self.plugins.keys()))
                for level in reversed(execution_order):
                    for plugin_id in level:
                        self._unload_plugin_internal(plugin_id)
            except Exception as e:
                logger.warning(f"Error during shutdown: {e}")
                
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        logger.info("Plugin manager shutdown complete")


# Global plugin manager instance
plugin_manager = AxiomPluginManager()


# Context manager for plugin manager
class PluginManagerContext:
    """Context manager for plugin manager operations"""
    
    def __init__(self):
        self.manager = None
        
    def __enter__(self):
        self.manager = AxiomPluginManager()
        return self.manager
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            self.manager.shutdown()