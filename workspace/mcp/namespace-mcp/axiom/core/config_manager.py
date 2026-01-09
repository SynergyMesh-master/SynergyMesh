"""
AXIOM Configuration Manager
Provides YAML-based configuration with hot-reload and environment overrides.
"""

import yaml
import json
import os
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import copy

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationSection:
    """Configuration section with metadata"""
    name: str
    data: Dict[str, Any]
    source_file: str
    last_modified: float
    environment_overrides: Dict[str, Any] = field(default_factory=dict)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigurationFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes"""
    
    def __init__(self, config_manager: 'ConfigurationManager'):
        self.config_manager = config_manager
        
    def on_modified(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix in ['.yaml', '.yml', '.json']:
                logger.info(f"Configuration file modified: {file_path}")
                self.config_manager._reload_file(file_path)


class ConfigurationManager:
    """
    Advanced configuration manager with hot-reload, validation, and environment support.
    """
    
    def __init__(self, config_dir: str = "config", watch_interval: float = 1.0):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.configurations: Dict[str, ConfigurationSection] = {}
        self.watchers: Dict[str, Observer] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.lock = threading.RLock()
        
        # Environment-specific configuration
        self.environment = os.getenv('AXIOM_ENV', 'development')
        self.environment_prefix = 'AXIOM_CONFIG_'
        
        # Validation schemas
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
        # Setup file watching
        self.observer = Observer()
        self.observer.schedule(
            ConfigurationFileHandler(self),
            str(self.config_dir),
            recursive=True
        )
        self.observer.start()
        
        logger.info(f"Configuration manager initialized for environment: {self.environment}")
        
    def load_configuration(self, config_name: str, config_file: Optional[str] = None,
                          schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from file with environment overrides and validation.
        
        Args:
            config_name: Name/identifier for this configuration
            config_file: Path to configuration file (optional, defaults to config_name.yaml)
            schema: Validation schema (optional)
            
        Returns:
            dict: Loaded and validated configuration
        """
        with self.lock:
            # Determine configuration file path
            if config_file is None:
                config_file = self.config_dir / f"{config_name}.yaml"
            else:
                config_file = Path(config_file)
                
            if not config_file.exists():
                raise ConfigValidationError(f"Configuration file not found: {config_file}")
                
            # Load base configuration
            try:
                with open(config_file, 'r') as f:
                    if config_file.suffix == '.json':
                        base_config = json.load(f)
                    else:
                        base_config = yaml.safe_load(f)
            except Exception as e:
                raise ConfigValidationError(f"Failed to load configuration: {e}")
                
            # Apply environment-specific overrides
            environment_config = self._load_environment_overrides(config_name, config_file)
            merged_config = self._merge_configurations(base_config, environment_config)
            
            # Apply environment variable overrides
            env_var_config = self._load_environment_variable_overrides(config_name)
            final_config = self._merge_configurations(merged_config, env_var_config)
            
            # Validate configuration
            if schema:
                self._validate_configuration(final_config, schema)
            elif config_name in self.schemas:
                self._validate_configuration(final_config, self.schemas[config_name])
                
            # Store configuration
            config_section = ConfigurationSection(
                name=config_name,
                data=final_config,
                source_file=str(config_file),
                last_modified=config_file.stat().st_mtime,
                environment_overrides=environment_config
            )
            
            self.configurations[config_name] = config_section
            self.schemas[config_name] = schema or {}
            
            # Trigger callbacks
            self._trigger_callbacks(config_name, final_config)
            
            logger.info(f"Configuration '{config_name}' loaded successfully")
            return final_config
            
    def get_configuration(self, config_name: str, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration or specific section.
        
        Args:
            config_name: Name of configuration
            section: Specific section to retrieve (optional)
            
        Returns:
            dict: Configuration data
        """
        with self.lock:
            if config_name not in self.configurations:
                raise ConfigValidationError(f"Configuration '{config_name}' not loaded")
                
            config = self.configurations[config_name].data
            
            if section:
                if section not in config:
                    raise ConfigValidationError(f"Section '{section}' not found in '{config_name}'")
                return config[section]
                
            return copy.deepcopy(config)
            
    def update_configuration(self, config_name: str, updates: Dict[str, Any],
                           persist: bool = False) -> Dict[str, Any]:
        """
        Update configuration in memory and optionally persist to file.
        
        Args:
            config_name: Name of configuration to update
            updates: Configuration updates to apply
            persist: Whether to persist changes to file
            
        Returns:
            dict: Updated configuration
        """
        with self.lock:
            if config_name not in self.configurations:
                raise ConfigValidationError(f"Configuration '{config_name}' not loaded")
                
            # Apply updates
            current_config = self.configurations[config_name].data
            updated_config = self._merge_configurations(current_config, updates)
            
            # Validate updated configuration
            if config_name in self.schemas and self.schemas[config_name]:
                self._validate_configuration(updated_config, self.schemas[config_name])
                
            # Update stored configuration
            self.configurations[config_name].data = updated_config
            
            # Persist if requested
            if persist:
                self._persist_configuration(config_name)
                
            # Trigger callbacks
            self._trigger_callbacks(config_name, updated_config)
            
            logger.info(f"Configuration '{config_name}' updated successfully")
            return updated_config
            
    def register_callback(self, config_name: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback for configuration changes.
        
        Args:
            config_name: Configuration name to watch
            callback: Callback function to invoke on changes
        """
        with self.lock:
            if config_name not in self.callbacks:
                self.callbacks[config_name] = []
            self.callbacks[config_name].append(callback)
            logger.debug(f"Callback registered for configuration '{config_name}'")
            
    def unregister_callback(self, config_name: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister configuration change callback"""
        with self.lock:
            if config_name in self.callbacks:
                try:
                    self.callbacks[config_name].remove(callback)
                    logger.debug(f"Callback unregistered for configuration '{config_name}'")
                except ValueError:
                    pass
                    
    def _load_environment_overrides(self, config_name: str, config_file: Path) -> Dict[str, Any]:
        """Load environment-specific configuration overrides"""
        env_config_file = config_file.parent / f"{config_name}.{self.environment}.yaml"
        env_alternative = config_file.parent / self.environment / f"{config_name}.yaml"
        
        env_config = {}
        
        # Try environment-specific file
        for env_file in [env_config_file, env_alternative]:
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        env_config = yaml.safe_load(f) or {}
                    logger.info(f"Loaded environment overrides from: {env_file}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load environment overrides: {e}")
                    
        return env_config
        
    def _load_environment_variable_overrides(self, config_name: str) -> Dict[str, Any]:
        """Load configuration overrides from environment variables"""
        overrides = {}
        prefix = f"{self.environment_prefix}{config_name.upper()}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested dict structure
                config_key = key[len(prefix):].lower()
                
                # Parse value (attempt JSON, fallback to string)
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                    
                # Set nested key
                self._set_nested_value(overrides, config_key.split('_'), parsed_value)
                
        if overrides:
            logger.info(f"Applied {len(overrides)} environment variable overrides")
            
        return overrides
        
    def _merge_configurations(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        result = copy.deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configurations(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def _set_nested_value(self, config: Dict[str, Any], keys: List[str], value: Any) -> None:
        """Set nested value in configuration dictionary"""
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        
    def _validate_configuration(self, config: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate configuration against schema"""
        try:
            # Simple validation - in production, use jsonschema or similar
            if 'required' in schema:
                for field in schema['required']:
                    if field not in config:
                        raise ConfigValidationError(f"Required field missing: {field}")
                        
            # Type validation
            if 'properties' in schema:
                for field, field_schema in schema['properties'].items():
                    if field in config:
                        expected_type = field_schema.get('type')
                        if expected_type and not self._check_type(config[field], expected_type):
                            raise ConfigValidationError(f"Invalid type for {field}: expected {expected_type}")
                            
        except Exception as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")
            
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        return expected_python_type and isinstance(value, expected_python_type)
        
    def _persist_configuration(self, config_name: str) -> None:
        """Persist configuration to file"""
        if config_name not in self.configurations:
            return
            
        config_section = self.configurations[config_name]
        config_file = Path(config_section.source_file)
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config_section.data, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration '{config_name}' persisted to: {config_file}")
        except Exception as e:
            logger.error(f"Failed to persist configuration '{config_name}': {e}")
            
    def _reload_file(self, file_path: Path) -> None:
        """Reload configuration from modified file"""
        # Find which configuration this file belongs to
        for config_name, config_section in self.configurations.items():
            if Path(config_section.source_file) == file_path:
                try:
                    # Reload configuration
                    schema = self.schemas.get(config_name)
                    self.load_configuration(config_name, str(file_path), schema)
                    logger.info(f"Reloaded configuration '{config_name}' from file change")
                except Exception as e:
                    logger.error(f"Failed to reload configuration '{config_name}': {e}")
                break
                
    def _trigger_callbacks(self, config_name: str, config: Dict[str, Any]) -> None:
        """Trigger registered callbacks for configuration changes"""
        if config_name in self.callbacks:
            for callback in self.callbacks[config_name]:
                try:
                    callback(config.copy())
                except Exception as e:
                    logger.error(f"Configuration callback failed: {e}")
                    
    def list_configurations(self) -> List[str]:
        """List all loaded configuration names"""
        return list(self.configurations.keys())
        
    def get_configuration_info(self, config_name: str) -> Dict[str, Any]:
        """Get information about a loaded configuration"""
        if config_name not in self.configurations:
            raise ConfigValidationError(f"Configuration '{config_name}' not found")
            
        config_section = self.configurations[config_name]
        return {
            "name": config_section.name,
            "source_file": config_section.source_file,
            "last_modified": config_section.last_modified,
            "environment": self.environment,
            "has_overrides": bool(config_section.environment_overrides),
            "callbacks_registered": len(self.callbacks.get(config_name, []))
        }
        
    def export_configuration(self, config_name: str, output_file: str, 
                           include_overrides: bool = False) -> None:
        """Export configuration to file"""
        config = self.get_configuration(config_name)
        
        if not include_overrides:
            # Remove environment overrides
            base_config = self.configurations[config_name].data
            env_overrides = self.configurations[config_name].environment_overrides
            config = self._remove_overrides(base_config, env_overrides)
            
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w') as f:
                if output_path.suffix == '.json':
                    json.dump(config, f, indent=2)
                else:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration '{config_name}' exported to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            
    def _remove_overrides(self, base_config: Dict[str, Any], 
                         overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Remove environment overrides from base configuration"""
        # This is a simplified implementation
        # In practice, you'd need to track original vs overridden values
        return copy.deepcopy(base_config)
        
    def shutdown(self) -> None:
        """Shutdown configuration manager"""
        logger.info("Shutting down configuration manager...")
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info("Configuration manager shutdown complete")


# Global configuration manager instance
config_manager = ConfigurationManager()