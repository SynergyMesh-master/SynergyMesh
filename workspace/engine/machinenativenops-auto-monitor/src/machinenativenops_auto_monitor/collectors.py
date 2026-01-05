"""
MachineNativeOps Auto-Monitor - Metrics Collectors
指標收集器

Collects metrics from various sources (system, services, custom).
"""

import logging
import os
import platform
import psutil
import requests
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Metric:
    """Represents a collected metric."""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat()
        }


class BaseCollector(ABC):
    """Base class for all metric collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize collector.
        
        Args:
            config: Collector configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def collect(self) -> Dict[str, float]:
        """
        Collect metrics.
        
        Returns:
            Dictionary of metric name to value
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if collector is enabled."""
        return self.enabled


class SystemCollector(BaseCollector):
    """Collects system-level metrics (CPU, memory, disk, network)."""
    
    def collect(self) -> Dict[str, float]:
        """Collect system metrics."""
        if not self.enabled:
            return {}
        
        metrics = {}
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['system_cpu_percent'] = cpu_percent
            
            cpu_count = psutil.cpu_count()
            metrics['system_cpu_count'] = cpu_count
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['system_memory_total'] = memory.total
            metrics['system_memory_available'] = memory.available
            metrics['system_memory_percent'] = memory.percent
            metrics['system_memory_used'] = memory.used
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics['system_disk_total'] = disk.total
            metrics['system_disk_used'] = disk.used
            metrics['system_disk_free'] = disk.free
            metrics['system_disk_percent'] = disk.percent
            
            # Network metrics
            net_io = psutil.net_io_counters()
            metrics['system_network_bytes_sent'] = net_io.bytes_sent
            metrics['system_network_bytes_recv'] = net_io.bytes_recv
            metrics['system_network_packets_sent'] = net_io.packets_sent
            metrics['system_network_packets_recv'] = net_io.packets_recv
            
            # Load average (Unix only)
            try:
                load1, load5, load15 = psutil.getloadavg()
                metrics['system_load_1'] = load1
                metrics['system_load_5'] = load5
                metrics['system_load_15'] = load15
            except (AttributeError, OSError):
                # Not available on Windows
                pass
            
            self.logger.debug(f"Collected {len(metrics)} system metrics")
        
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
        
        return metrics


class ServiceCollector(BaseCollector):
    """Collects metrics from services via health endpoints."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize service collector."""
        super().__init__(config)
        self.services = config.get('services', [])
        self.timeout = config.get('timeout', 5)
    
    def collect(self) -> Dict[str, float]:
        """Collect service metrics."""
        if not self.enabled:
            return {}
        
        metrics = {}
        
        for service in self.services:
            service_name = service.get('name')
            health_url = service.get('health_url')
            metrics_url = service.get('metrics_url')
            
            if not service_name or not health_url:
                continue
            
            try:
                # Check service health
                health_response = requests.get(
                    health_url,
                    timeout=self.timeout
                )
                
                is_healthy = health_response.status_code == 200
                metrics[f'service_{service_name}_healthy'] = 1.0 if is_healthy else 0.0
                metrics[f'service_{service_name}_response_time'] = health_response.elapsed.total_seconds()
                
                # Collect custom metrics if available
                if metrics_url:
                    metrics_response = requests.get(
                        metrics_url,
                        timeout=self.timeout
                    )
                    
                    if metrics_response.status_code == 200:
                        service_metrics = metrics_response.json()
                        
                        # Add service metrics with prefix
                        for key, value in service_metrics.items():
                            if isinstance(value, (int, float)):
                                metrics[f'service_{service_name}_{key}'] = float(value)
            
            except requests.RequestException as e:
                self.logger.error(f"Error collecting metrics for {service_name}: {e}")
                metrics[f'service_{service_name}_healthy'] = 0.0
            
            except Exception as e:
                self.logger.error(f"Unexpected error for {service_name}: {e}")
        
        self.logger.debug(f"Collected {len(metrics)} service metrics")
        
        return metrics


class CustomMetricCollector(BaseCollector):
    """Collects custom application-specific metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize custom metric collector."""
        super().__init__(config)
        self.metric_sources = config.get('sources', [])
    
    def collect(self) -> Dict[str, float]:
        """Collect custom metrics."""
        if not self.enabled:
            return {}
        
        metrics = {}
        
        # Placeholder for custom metric collection
        # In production, this would integrate with application-specific
        # metric sources, databases, APIs, etc.
        
        for source in self.metric_sources:
            source_name = source.get('name')
            source_type = source.get('type')
            
            # Example: could support different source types
            # - database queries
            # - file-based metrics
            # - external APIs
            # - message queues
            
            self.logger.debug(f"Collecting from custom source: {source_name}")
        
        return metrics


class MetricsCollector:
    """
    Aggregates metrics from multiple collectors.
    """
    
    def __init__(self, collectors: List[BaseCollector]):
        """
        Initialize metrics collector.
        
        Args:
            collectors: List of metric collectors
        """
        self.collectors = collectors
        self.logger = logging.getLogger(__name__)
    
    def collect_all(self) -> Dict[str, float]:
        """
        Collect metrics from all enabled collectors.
        
        Returns:
            Dictionary of all collected metrics
        """
        all_metrics = {}
        
        for collector in self.collectors:
            if not collector.is_enabled():
                continue
            
            try:
                collector_metrics = collector.collect()
                all_metrics.update(collector_metrics)
            
            except Exception as e:
                self.logger.error(
                    f"Error collecting from {collector.__class__.__name__}: {e}"
                )
        
        return all_metrics
    
    def add_collector(self, collector: BaseCollector):
        """
        Add a new collector.
        
        Args:
            collector: Collector to add
        """
        self.collectors.append(collector)
    
    def remove_collector(self, collector_class):
        """
        Remove a collector by class.
        
        Args:
            collector_class: Class of collector to remove
        """
        self.collectors = [
            c for c in self.collectors
            if not isinstance(c, collector_class)
        ]

logger = logging.getLogger(__name__)


class MetricCollector(ABC):
    """Base class for metric collectors"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize collector"""
        self.config = config or {}
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect metrics"""
        pass


class SystemCollector(MetricCollector):
    """Collects system-level metrics"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            metrics = {
                "timestamp": psutil.time.time(),
                "hostname": platform.node(),
                "platform": platform.system(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": self._collect_memory(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk": self._collect_disk(),
                "disk_percent": psutil.disk_usage('/').percent,
                "network": self._collect_network(),
                "load_average": self._collect_load_average(),
            }
            return metrics
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _collect_memory(self) -> Dict[str, Any]:
        """Collect memory metrics"""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
        }
    
    def _collect_disk(self) -> Dict[str, Any]:
        """Collect disk metrics"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }
    
    def _collect_network(self) -> Dict[str, Any]:
        """Collect network metrics"""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "errin": net.errin,
            "errout": net.errout,
            "dropin": net.dropin,
            "dropout": net.dropout,
        }
    
    def _collect_load_average(self) -> List[float]:
        """Collect system load average"""
        try:
            return list(psutil.getloadavg())
        except (AttributeError, OSError):
            # getloadavg() may not be available on all platforms
            return [0.0, 0.0, 0.0]


class ServiceCollector(MetricCollector):
    """Collects service health metrics"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect service metrics"""
        services = self.config.get("monitored_services", [])
        
        service_metrics = {
            "timestamp": psutil.time.time(),
            "services": {}
        }
        
        for service in services:
            if isinstance(service, str):
                service_name = service
                service_config = {}
            else:
                service_name = service.get("name", "unknown")
                service_config = service
            
            service_metrics["services"][service_name] = self._check_service(
                service_name,
                service_config
            )
        
        return service_metrics
    
    def _check_service(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check individual service health"""
        check_type = config.get("type", "process")
        
        if check_type == "process":
            return self._check_process(service_name, config)
        elif check_type == "http":
            return self._check_http_endpoint(service_name, config)
        elif check_type == "port":
            return self._check_port(service_name, config)
        else:
            logger.warning(f"Unknown service check type: {check_type}")
            return {"healthy": False, "error": "unknown check type"}
    
    def _check_process(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a process is running"""
        process_name = config.get("process_name", service_name)
        
        try:
            for proc in psutil.process_iter(['name', 'status']):
                if proc.info['name'] == process_name:
                    return {
                        "healthy": True,
                        "status": "running",
                        "pid": proc.pid,
                        "memory_percent": proc.memory_percent(),
                        "cpu_percent": proc.cpu_percent(interval=0.1),
                    }
            
            return {
                "healthy": False,
                "status": "not_found",
                "error": f"Process {process_name} not found"
            }
        
        except Exception as e:
            logger.error(f"Error checking process {process_name}: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }
    
    def _check_http_endpoint(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check HTTP endpoint health"""
        # TODO: Implement HTTP health check
        logger.warning(f"HTTP health check not implemented for {service_name}")
        return {"healthy": True, "status": "unknown"}
    
    def _check_port(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a port is listening"""
        port = config.get("port")
        if not port:
            return {"healthy": False, "error": "No port specified"}
        
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return {
                        "healthy": True,
                        "status": "listening",
                        "port": port
                    }
            
            return {
                "healthy": False,
                "status": "not_listening",
                "port": port
            }
        
        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            }


class ApplicationMetricCollector(MetricCollector):
    """Collects application-specific metrics"""
    
    def collect(self) -> Dict[str, Any]:
        """Collect application metrics"""
        metrics = {
            "timestamp": psutil.time.time(),
            "applications": {}
        }
        
        # Collect metrics for each configured application
        apps = self.config.get("applications", [])
        for app in apps:
            app_name = app.get("name", "unknown")
            metrics["applications"][app_name] = self._collect_app_metrics(app)
        
        return metrics
    
    def _collect_app_metrics(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics for a specific application"""
        # TODO: Implement application-specific metric collection
        # This could query application APIs, parse log files, etc.
        return {
            "status": "unknown",
            "message": "Application metrics not implemented"
        }
@dataclass
class MetricData:
    """Represents a metric data point."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class LogEntry:
    """Represents a log entry."""
    level: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class Event:
    """Represents a system event."""
    type: str
    description: str
    timestamp: datetime
    severity: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
        }


class MetricsCollector:
    """Collects system and application metrics."""
    
    def __init__(self, interval: int = 10):
        self.interval = interval
        self.last_collection = None
    
    def collect(self) -> Dict:
        """Collect current metrics."""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count': psutil.cpu_count(),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_percent': psutil.disk_usage('/').percent,
                'disk_free_gb': psutil.disk_usage('/').free / (1024**3),
                'disk_total_gb': psutil.disk_usage('/').total / (1024**3),
                'network_sent_mb': psutil.net_io_counters().bytes_sent / (1024**2),
                'network_recv_mb': psutil.net_io_counters().bytes_recv / (1024**2),
                'process_count': len(psutil.pids()),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
            
            self.last_collection = datetime.now()
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def collect_process_metrics(self, pid: Optional[int] = None) -> Dict:
        """Collect metrics for a specific process."""
        try:
            process = psutil.Process(pid) if pid else psutil.Process()
            
            return {
                'pid': process.pid,
                'name': process.name(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_percent': process.memory_percent(),
                'memory_mb': process.memory_info().rss / (1024**2),
                'num_threads': process.num_threads(),
                'status': process.status(),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            return {}


class LogCollector:
    """Collects logs from various sources."""
    
    def __init__(self):
        self.log_buffer: List[LogEntry] = []
    
    def collect(self) -> List[LogEntry]:
        """Collect recent logs."""
        # In a real implementation, this would collect from log files,
        # syslog, or other log sources
        logs = self.log_buffer.copy()
        self.log_buffer.clear()
        return logs
    
    def add_log(self, level: str, message: str, source: str, metadata: Dict = None):
        """Add a log entry to the buffer."""
        entry = LogEntry(
            level=level,
            message=message,
            timestamp=datetime.now(),
            source=source,
            metadata=metadata or {},
        )
        self.log_buffer.append(entry)


class EventCollector:
    """Collects system events."""
    
    def __init__(self):
        self.event_buffer: List[Event] = []
        self._last_check = datetime.now()
    
    def collect(self) -> List[Event]:
        """Collect recent events."""
        events = self.event_buffer.copy()
        self.event_buffer.clear()
        
        # Auto-detect system events
        self._detect_system_events()
        
        return events
    
    def _detect_system_events(self):
        """Detect and record system events."""
        # Check for high resource usage
        cpu_usage = psutil.cpu_percent(interval=0.1)
        if cpu_usage > 90:
            self.add_event(
                type='high_cpu',
                description=f'High CPU usage detected: {cpu_usage}%',
                severity='warning'
            )
        
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 90:
            self.add_event(
                type='high_memory',
                description=f'High memory usage detected: {memory_usage}%',
                severity='warning'
            )
    
    def add_event(self, type: str, description: str, severity: str, metadata: Dict = None):
        """Add an event to the buffer."""
        event = Event(
            type=type,
            description=description,
            timestamp=datetime.now(),
            severity=severity,
            metadata=metadata or {},
        )
        self.event_buffer.append(event)


class KubernetesCollector:
    """Collects metrics from Kubernetes clusters."""
    
    def __init__(self):
        self.enabled = False
        # In a real implementation, initialize k8s client here
    
    def collect_pod_metrics(self) -> List[Dict]:
        """Collect metrics from all pods."""
        # Placeholder for Kubernetes integration
        return []
    
    def collect_node_metrics(self) -> List[Dict]:
        """Collect metrics from all nodes."""
        # Placeholder for Kubernetes integration
        return []

try:
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False


@dataclass
class SystemMetrics:
    """System metrics data structure"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    load_average: Optional[tuple]
    uptime: float
    process_count: int
    timestamp: str

@dataclass
class QuantumMetrics:
    """Quantum metrics data structure"""
    fidelity: float
    coherence_time: float
    error_rate: float
    qubits_active: int
    state_vector: str
    timestamp: str

class SystemCollector:
    """System metrics collector"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def collect(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = os.getloadavg()
            except (AttributeError, OSError):
                # Windows doesn't have load average
                pass
            
            # System info
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = {
                'timestamp': timestamp,
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_current': cpu_freq.current if cpu_freq else None,
                    'frequency_min': cpu_freq.min if cpu_freq else None,
                    'frequency_max': cpu_freq.max if cpu_freq else None,
                },
                'memory': {
                    'total_bytes': memory.total,
                    'available_bytes': memory.available,
                    'used_bytes': memory.used,
                    'usage_percent': memory.percent,
                    'buffers_bytes': getattr(memory, 'buffers', 0),
                    'cached_bytes': getattr(memory, 'cached', 0),
                },
                'disk': {
                    'total_bytes': disk.total,
                    'used_bytes': disk.used,
                    'free_bytes': disk.free,
                    'usage_percent': (disk.used / disk.total) * 100,
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv,
                    'errors_in': network.errin,
                    'errors_out': network.errout,
                    'drop_in': network.dropin,
                    'drop_out': network.dropout,
                },
                'system': {
                    'uptime_seconds': uptime,
                    'boot_time': boot_time,
                    'process_count': process_count,
                    'load_average': load_avg,
                    'os_info': {
                        'system': os.name,
                        'platform': os.uname().sysname if hasattr(os, 'uname') else None,
                        'release': os.uname().release if hasattr(os, 'uname') else None,
                        'version': os.uname().version if hasattr(os, 'uname') else None,
                    }
                }
            }
            
            # Flatten for easier database storage
            flat_metrics = self._flatten_metrics(metrics)
            
            self.logger.debug(f"Collected system metrics: {len(flat_metrics)} fields")
            return flat_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            raise
    
    def _flatten_metrics(self, metrics: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested metrics dictionary"""
        flat = {}
        
        for key, value in metrics.items():
            if key == 'timestamp':
                flat['timestamp'] = value
            elif isinstance(value, dict):
                nested_flat = self._flatten_metrics(value, f"{prefix}{key}_")
                flat.update(nested_flat)
            elif isinstance(value, tuple):
                for i, item in enumerate(value):
                    flat[f"{prefix}{key}_{i}"] = item
            else:
                flat[f"{prefix}{key}"] = value
        
        return flat

class QuantumCollector:
    """Quantum metrics collector"""
    
    def __init__(self, config: QuantumConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def collect(self) -> Dict[str, Any]:
        """Collect quantum metrics"""
        if not self.config.enabled:
            return {'quantum_enabled': False}
        
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Simulate quantum metrics (in real implementation, this would connect to actual quantum hardware)
            metrics = {
                'timestamp': timestamp,
                'quantum_enabled': True,
                'quantum_fidelity': self._get_quantum_fidelity(),
                'quantum_coherence_time': self._get_quantum_coherence_time(),
                'quantum_error_rate': self._get_quantum_error_rate(),
                'quantum_qubits_active': self._get_active_qubits(),
                'quantum_state_vector': '|ψ⟩',  # Simplified state representation
            }
            
            self.logger.debug(f"Collected quantum metrics")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect quantum metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'quantum_enabled': True,
                'quantum_error': str(e)
            }
    
    def _get_quantum_fidelity(self) -> float:
        """Get quantum fidelity (simulated)"""
        # In real implementation, this would query quantum hardware
        return max(0.0, min(1.0, self.config.fidelity_threshold + (hash(time.time()) % 100 - 50) / 1000))
    
    def _get_quantum_coherence_time(self) -> float:
        """Get quantum coherence time (simulated)"""
        # In real implementation, this would measure actual coherence
        return self.config.coherence_time_threshold + (hash(time.time()) % 100) / 10
    
    def _get_quantum_error_rate(self) -> float:
        """Get quantum error rate (simulated)"""
        # In real implementation, this would measure actual error rates
        return max(0.0, self.config.error_rate_threshold - (hash(time.time()) % 100) / 10000)
    
    def _get_active_qubits(self) -> int:
        """Get number of active qubits (simulated)"""
        # In real implementation, this would count active qubits
        return (hash(time.time()) % 50) + 1

class KubernetesCollector:
    """Kubernetes services collector"""
    
    def __init__(self, config: ServicesConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Kubernetes client
        self.k8s_client = None
        if KUBERNETES_AVAILABLE:
            try:
                config.load_incluster_config()  # For running in-cluster
                self.k8s_client = client.CoreV1Api()
                self.logger.info("Kubernetes client initialized (in-cluster)")
            except config.ConfigException:
                try:
                    config.load_kube_config()  # For local development
                    self.k8s_client = client.CoreV1Api()
                    self.logger.info("Kubernetes client initialized (kubeconfig)")
                except Exception:
                    self.logger.warning("Kubernetes client initialization failed")
    
    def collect(self) -> Dict[str, Any]:
        """Collect Kubernetes metrics"""
        if not self.k8s_client:
            return {
                'kubernetes_enabled': False,
                'kubernetes_error': 'Kubernetes client not available'
            }
        
        try:
            timestamp = datetime.utcnow().isoformat()
            metrics = {
                'timestamp': timestamp,
                'kubernetes_enabled': True,
            }
            
            # Collect service metrics
            if self.config.auto_discover:
                services_metrics = self._collect_services()
                metrics.update(services_metrics)
            
            # Collect deployment metrics
            deployments_metrics = self._collect_deployments()
            metrics.update(deployments_metrics)
            
            # Collect pod metrics
            pods_metrics = self._collect_pods()
            metrics.update(pods_metrics)
            
            self.logger.debug(f"Collected Kubernetes metrics: {len(metrics)} fields")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect Kubernetes metrics: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'kubernetes_enabled': True,
                'kubernetes_error': str(e)
            }
    
    def _collect_services(self) -> Dict[str, Any]:
        """Collect Kubernetes services metrics"""
        try:
            services = []
            total_services = 0
            healthy_services = 0
            
            for namespace in self.config.discovery_namespaces:
                svc_list = self.k8s_client.list_namespaced_service(namespace)
                
                for svc in svc_list.items:
                    total_services += 1
                    
                    service_info = {
                        'name': svc.metadata.name,
                        'namespace': svc.metadata.namespace,
                        'cluster_ip': svc.spec.cluster_ip,
                        'ports': len(svc.spec.ports) if svc.spec.ports else 0,
                        'selector': svc.spec.selector,
                        'labels': svc.metadata.labels or {},
                    }
                    
                    # Check if service has endpoints (health indicator)
                    try:
                        endpoints = self.k8s_client.read_namespaced_endpoints(
                            svc.metadata.name, namespace
                        )
                        service_info['has_endpoints'] = bool(endpoints.subsets)
                        if endpoints.subsets:
                            healthy_services += 1
                    except Exception:
                        service_info['has_endpoints'] = False
                    
                    services.append(service_info)
            
            return {
                'kubernetes_services_total': total_services,
                'kubernetes_services_healthy': healthy_services,
                'kubernetes_services_details': services,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect services: {e}")
            return {'kubernetes_services_error': str(e)}
    
    def _collect_deployments(self) -> Dict[str, Any]:
        """Collect Kubernetes deployments metrics"""
        try:
            from kubernetes import client as k8s_client
            apps_client = k8s_client.AppsV1Api()
            
            deployments = []
            total_deployments = 0
            ready_deployments = 0
            
            for namespace in self.config.discovery_namespaces:
                deploy_list = apps_client.list_namespaced_deployment(namespace)
                
                for deploy in deploy_list.items:
                    total_deployments += 1
                    
                    deployment_info = {
                        'name': deploy.metadata.name,
                        'namespace': deploy.metadata.namespace,
                        'replicas': deploy.spec.replicas or 0,
                        'ready_replicas': deploy.status.ready_replicas or 0,
                        'available_replicas': deploy.status.available_replicas or 0,
                        'conditions': [],
                    }
                    
                    # Parse conditions
                    for condition in deploy.status.conditions or []:
                        deployment_info['conditions'].append({
                            'type': condition.type,
                            'status': condition.status,
                            'reason': condition.reason,
                            'message': condition.message,
                        })
                    
                    # Check if deployment is ready
                    if (deploy.status.ready_replicas or 0) == (deploy.spec.replicas or 0):
                        ready_deployments += 1
                    
                    deployments.append(deployment_info)
            
            return {
                'kubernetes_deployments_total': total_deployments,
                'kubernetes_deployments_ready': ready_deployments,
                'kubernetes_deployments_details': deployments,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect deployments: {e}")
            return {'kubernetes_deployments_error': str(e)}
    
    def _collect_pods(self) -> Dict[str, Any]:
        """Collect Kubernetes pods metrics"""
        try:
            pods = []
            total_pods = 0
            running_pods = 0
            
            for namespace in self.config.discovery_namespaces:
                pod_list = self.k8s_client.list_namespaced_pod(namespace)
                
                for pod in pod_list.items:
                    total_pods += 1
                    
                    pod_info = {
                        'name': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'phase': pod.status.phase,
                        'node_name': pod.spec.node_name,
                        'ip': pod.status.pod_ip,
                        'container_count': len(pod.spec.containers),
                        'container_statuses': [],
                    }
                    
                    # Container status
                    for container_status in pod.status.container_statuses or []:
                        pod_info['container_statuses'].append({
                            'name': container_status.name,
                            'ready': container_status.ready,
                            'restart_count': container_status.restart_count,
                            'state': container_status.state,
                        })
                    
                    if pod.status.phase == 'Running':
                        running_pods += 1
                    
                    pods.append(pod_info)
            
            return {
                'kubernetes_pods_total': total_pods,
                'kubernetes_pods_running': running_pods,
                'kubernetes_pods_details': pods,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect pods: {e}")
            return {'kubernetes_pods_error': str(e)}
