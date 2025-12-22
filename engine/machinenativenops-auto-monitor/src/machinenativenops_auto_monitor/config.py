"""
MachineNativeOps Auto-Monitor - Configuration

Configuration management for auto-monitor system.
Configuration Module
配置模組

Handles configuration loading and management for the auto-monitor system.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AutoMonitorConfig:
    """
    Auto-monitor configuration.
    """
    
    # System identification
    namespace: str = "machinenativeops"
    version: str = "1.0.0"
    
    # Collection settings
    collection_interval: int = 30  # seconds
    dry_run: bool = False
    
    # Component configurations
    collectors: Dict[str, Any] = field(default_factory=dict)
    alerts: Dict[str, Any] = field(default_factory=dict)
    storage: Dict[str, Any] = field(default_factory=dict)
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'AutoMonitorConfig':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            AutoMonitorConfig instance
        """
        logger = logging.getLogger(__name__)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Extract configuration sections
            config = cls(
                namespace=config_data.get('namespace', 'machinenativeops'),
                version=config_data.get('version', '1.0.0'),
                collection_interval=config_data.get('collection_interval', 30),
                dry_run=config_data.get('dry_run', False),
                collectors=config_data.get('collectors', {}),
                alerts=config_data.get('alerts', {}),
                storage=config_data.get('storage', {}),
                log_level=config_data.get('log_level', 'INFO'),
                log_file=config_data.get('log_file')
            )
            
            logger.info(f"Configuration loaded from: {config_path}")
            return config
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    @classmethod
    def default(cls) -> 'AutoMonitorConfig':
        """
        Create default configuration.
        
        Returns:
            AutoMonitorConfig with default values
        """
        return cls(
            namespace="machinenativeops",
            version="1.0.0",
            collection_interval=30,
            collectors={
                'system': {
                    'enabled': True
                },
                'service': {
                    'enabled': True,
                    'services': [],
                    'timeout': 5
                }
            },
            alerts={
                'enabled': True,
                'rules': [
                    {
                        'name': 'high_cpu_usage',
                        'description': 'CPU usage is too high',
                        'severity': 'warning',
                        'condition': '>',
                        'threshold': 80.0,
                        'duration': 60
                    },
                    {
                        'name': 'high_memory_usage',
                        'description': 'Memory usage is too high',
                        'severity': 'warning',
                        'condition': '>',
                        'threshold': 85.0,
                        'duration': 60
                    },
                    {
                        'name': 'low_disk_space',
                        'description': 'Disk space is running low',
                        'severity': 'critical',
                        'condition': '>',
                        'threshold': 90.0,
                        'duration': 300
                    }
                ]
            },
            storage={
                'enabled': True,
                'backend': 'timeseries',
                'retention_days': 30,
                'path': '/var/lib/machinenativeops/metrics'
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'namespace': self.namespace,
            'version': self.version,
            'collection_interval': self.collection_interval,
            'dry_run': self.dry_run,
            'collectors': self.collectors,
            'alerts': self.alerts,
            'storage': self.storage,
            'log_level': self.log_level,
            'log_file': self.log_file
        }
    
    def save(self, output_path: Path):
        """
        Save configuration to YAML file.
        
        Args:
            output_path: Path to save configuration
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        # Validate namespace
        if not self.namespace:
            logger.error("Namespace cannot be empty")
            return False
        
        # Validate collection interval
        if self.collection_interval < 1:
            logger.error("Collection interval must be at least 1 second")
            return False
        
        # Validate collectors
        if not isinstance(self.collectors, dict):
            logger.error("Collectors must be a dictionary")
            return False
        
        # Validate alerts
        if not isinstance(self.alerts, dict):
            logger.error("Alerts must be a dictionary")
            return False
        
        # Validate storage
        if not isinstance(self.storage, dict):
            logger.error("Storage must be a dictionary")
            return False
        
        logger.info("Configuration validation passed")
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Configuration for the auto-monitor system."""
    
    # Application settings
    mode: str = 'development'  # 'development' or 'production'
    port: int = 8080
    host: str = '0.0.0.0'
    
    # Collection intervals (in seconds)
    collection_interval: int = 10
    log_collection_interval: int = 5
    event_collection_interval: int = 15
    
    # Storage settings
    storage_backend: str = 'memory'  # 'memory', 'file', 'database'
    storage_path: Optional[str] = None
    retention_days: int = 7
    
    # Alert settings
    enable_alerts: bool = True
    alert_channels: list = field(default_factory=list)
    
    # Namespace configuration
    namespace: str = 'machinenativeops'
    registry: str = 'registry.machinenativeops.io'
    certificate_path: str = 'etc/machinenativeops/pkl'
    cluster_token: str = 'super-agent-etcd-cluster'
    
    # Feature flags
    enable_kubernetes: bool = False
    enable_metrics_export: bool = True
    enable_log_aggregation: bool = True
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'MonitorConfig':
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from: {config_path}")
            return cls(**data)
            
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            logger.info("Using default configuration")
            return cls.default()
    
    @classmethod
    def default(cls) -> 'MonitorConfig':
        """Get default configuration."""
        return cls()
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def to_yaml(self, output_path: Path):
        """Save configuration to YAML file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False)
            logger.info(f"Configuration saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def validate(self) -> bool:
        """Validate configuration."""
        if self.mode not in ['development', 'production']:
            logger.error(f"Invalid mode: {self.mode}")
            return False
        
        if self.port < 1 or self.port > 65535:
            logger.error(f"Invalid port: {self.port}")
            return False
        
        if self.collection_interval < 1:
            logger.error(f"Invalid collection_interval: {self.collection_interval}")
            return False
        
        logger.info("✅ Configuration validated successfully")
        return True


def create_default_config_file(output_path: Path):
    """
    Create a default configuration file.
    
    Args:
        output_path: Path to create configuration file
    """
    config = AutoMonitorConfig.default()
    config.save(output_path)
    print(f"Default configuration created at: {output_path}")
    """Create a default configuration file."""
    config = MonitorConfig.default()
    config.to_yaml(output_path)
    print(f"✅ Created default configuration file: {output_path}")


if __name__ == "__main__":
    # Create a sample configuration file
    sample_path = Path("config.example.yaml")
    create_default_config_file(sample_path)
