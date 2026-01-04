"""
MachineNativeOps Auto-Monitor - Main Application

Main application class for the auto-monitor system.
Auto-Monitor Application
自動監控應用程式

Main application logic for the auto-monitor system.
"""

import logging
import time
import threading
from typing import Dict, Any
from datetime import datetime

from .config import AutoMonitorConfig
from .collectors import MetricsCollector, SystemCollector, ServiceCollector
from .alerts import AlertManager
from .儲存 import StorageManager


class AutoMonitorApp:
    """
    
    def __init__(self, config: AutoMonitorConfig):
        """
        Initialize auto-monitor application.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False
        self._stop_event = threading.Event()
        
        # Initialize components
        self.logger.info("Initializing auto-monitor components...")
        
        # Metrics collectors
        self.system_collector = SystemCollector(config.collectors.get('system', {}))
        self.service_collector = ServiceCollector(config.collectors.get('service', {}))
        self.metrics_collector = MetricsCollector([
            self.system_collector,
            self.service_collector
        ])
        
        # Alert manager
        self.alert_manager = AlertManager(config.alerts)
        
        # Storage manager
        self.storage_manager = StorageManager(config.storage)
        
        self.logger.info("Auto-monitor initialization complete")
    
    def run(self):
        """Run auto-monitor in foreground mode."""
        self.running = True
        self.logger.info("Starting auto-monitor collection loop...")
        
        try:
            while self.running:
                self._collect_and_process()
                time.sleep(self.config.collection_interval)
        
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        
        finally:
            self.shutdown()
    
    def run_daemon(self):
        """Run auto-monitor as daemon."""
        self.running = True
        self.logger.info("Starting auto-monitor daemon...")
        
        # Start collection thread
        collector_thread = threading.Thread(target=self._collection_loop, daemon=True)
        collector_thread.start()
        
        # Wait for stop event
        self._stop_event.wait()
        
        self.shutdown()
    
    def _collection_loop(self):
        """Main collection loop for daemon mode."""
        self.logger.info("Collection loop started")
        
        while self.running and not self._stop_event.is_set():
            try:
                self._collect_and_process()
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}", exc_info=True)
            
            self._stop_event.wait(timeout=self.config.collection_interval)
        
        self.logger.info("Collection loop stopped")
    
    def _collect_and_process(self):
        """Collect metrics, evaluate alerts, and store data."""
        collection_start = time.time()
        
        try:
            # Collect metrics
            self.logger.debug("Collecting metrics...")
            metrics = self.metrics_collector.collect_all()
            
            metrics_count = len(metrics)
            self.logger.debug(f"Collected {metrics_count} metrics")
            
            # Evaluate alerts
            if self.config.alerts.get('enabled', True):
                self.logger.debug("Evaluating alerts...")
                self.alert_manager.evaluate_metrics(metrics)
            
            # Store metrics
            if not self.config.dry_run and self.config.storage.get('enabled', True):
                self.logger.debug("Storing metrics...")
                self.storage_manager.store_metrics(metrics)
            
            # Log statistics
            collection_duration = time.time() - collection_start
            self.logger.info(
                f"Collection completed: {metrics_count} metrics in {collection_duration:.2f}s"
            )
            
            # Log active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            if active_alerts:
                self.logger.info(f"Active alerts: {len(active_alerts)}")
                for alert in active_alerts:
                    self.logger.info(f"  - {alert.name} [{alert.severity.value}]")
        
        except Exception as e:
            self.logger.error(f"Error in collect and process: {e}", exc_info=True)
    
    def shutdown(self):
        """Shutdown auto-monitor gracefully."""
        self.logger.info("Shutting down auto-monitor...")
        
        self.running = False
        self._stop_event.set()
        
        # Close storage
        if self.storage_manager:
            self.storage_manager.close()
        
        self.logger.info("Auto-monitor shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current application status."""
        return {
            'running': self.running,
            'version': self.config.version,
            'namespace': self.config.namespace,
            'collection_interval': self.config.collection_interval,
            'dry_run': self.config.dry_run,
            'metrics': {
                'collectors': len(self.metrics_collector.collectors),
                'last_collection': datetime.now().isoformat()
            },
            'alerts': self.alert_manager.get_stats(),
            'storage': self.storage_manager.get_stats()
        }
from typing import Any, Dict

from .alerts import AlertManager, AlertSeverity
from .collectors import SystemCollector, ServiceCollector, MetricCollector
from .config import MonitorConfig
Auto-Monitor Application Core
自動監控應用核心

Main application logic for the MachineNativeOps auto-monitoring system.
"""

import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime

from .config import MonitorConfig
from .collectors import MetricsCollector, LogCollector, EventCollector
from .alerts import AlertManager, create_default_rules
from .儲存 import StorageBackend, InMemoryStorage

logger = logging.getLogger(__name__)


class AutoMonitorApp:
    """Main auto-monitor application"""
    
    def __init__(self, config: MonitorConfig):
        """Initialize auto-monitor app"""
        self.config = config
        self.alert_manager = AlertManager(config.get("alerts", {}))
        
        # Initialize collectors
        self.system_collector = SystemCollector(config.get("system", {}))
        self.service_collector = ServiceCollector(config.get("services", {}))
        self.metric_collector = MetricCollector(config.get("metrics", {}))
        
        self.running = False
        logger.info("Auto-monitor initialized")
    
    def collect_once(self):
        """Perform one collection cycle"""
        logger.info("Starting collection cycle...")
        
        try:
            # Collect system metrics
            system_metrics = self.system_collector.collect()
            logger.debug(f"Collected system metrics: {system_metrics}")
            
            # Collect service status
            service_metrics = self.service_collector.collect()
            logger.debug(f"Collected service metrics: {service_metrics}")
            
            # Collect custom metrics
            custom_metrics = self.metric_collector.collect()
            logger.debug(f"Collected custom metrics: {custom_metrics}")
            
            # Store metrics
            self._store_metrics({
                "system": system_metrics,
                "services": service_metrics,
                "custom": custom_metrics
            })
            
            logger.info("Collection cycle complete")
            
        except Exception as e:
            logger.error(f"Error during collection: {e}", exc_info=True)
    
    def check_alerts_once(self):
        """Perform one alert checking cycle"""
        logger.info("Checking alerts...")
        
        try:
            # Collect current metrics
            system_metrics = self.system_collector.collect()
            service_metrics = self.service_collector.collect()
            
            # Check system metrics against thresholds
            self._check_system_alerts(system_metrics)
            
            # Check service health
            self._check_service_alerts(service_metrics)
            
            # Log alert summary
            summary = self.alert_manager.get_alert_summary()
            if summary["total"] > 0:
                logger.warning(f"Active alerts: {summary}")
            else:
                logger.info("No active alerts")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}", exc_info=True)
    
    def _check_system_alerts(self, metrics: Dict[str, Any]):
        """Check system metrics and create alerts if needed"""
        # Check CPU usage
        if "cpu_percent" in metrics:
            alert = self.alert_manager.check_metric(
                "cpu", 
                metrics["cpu_percent"]
            )
            if alert:
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert("cpu_high", "auto-monitor")
        
        # Check memory usage
        if "memory_percent" in metrics:
            alert = self.alert_manager.check_metric(
                "memory",
                metrics["memory_percent"]
            )
            if alert:
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert("memory_high", "auto-monitor")
        
        # Check disk usage
        if "disk_percent" in metrics:
            alert = self.alert_manager.check_metric(
                "disk",
                metrics["disk_percent"]
            )
            if alert:
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert("disk_high", "auto-monitor")
    
    def _check_service_alerts(self, metrics: Dict[str, Any]):
        """Check service health and create alerts if needed"""
        services = metrics.get("services", {})
        
        for service_name, service_data in services.items():
            if not service_data.get("healthy", True):
                from .alerts import Alert
                alert = Alert(
                    name=f"service_{service_name}_down",
                    severity=AlertSeverity.ERROR,
                    message=f"Service {service_name} is unhealthy",
                    source="auto-monitor",
                    metadata={
                        "service": service_name,
                        "status": service_data.get("status", "unknown")
                    }
                )
                self.alert_manager.add_alert(alert)
            else:
                self.alert_manager.resolve_alert(
                    f"service_{service_name}_down",
                    "auto-monitor"
                )
    
    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store collected metrics"""
        # TODO: Implement metric storage (e.g., to database, time-series DB, etc.)
        storage_config = self.config.get("storage", {})
        storage_type = storage_config.get("type", "memory")
        
        if storage_type == "memory":
            # Just log for now
            logger.debug(f"Storing metrics (memory): {len(metrics)} categories")
        else:
            logger.warning(f"Storage type {storage_type} not implemented")
    
    def run(self, interval: int = 60, daemon: bool = False):
        """
        Run auto-monitor continuously
        
        Args:
            interval: Collection interval in seconds
            daemon: Run as daemon (background process)
        """
        self.running = True
        logger.info(f"Starting auto-monitor (interval: {interval}s, daemon: {daemon})")
        
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"Starting iteration {iteration}")
                
                # Collect metrics
                self.collect_once()
                
                # Check alerts
                self.check_alerts_once()
                
                # Clean up resolved alerts
                self.alert_manager.clear_resolved_alerts()
                
                # Wait for next interval
                if self.running:
                    logger.debug(f"Sleeping for {interval}s...")
                    time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            self.stop()
            raise
    
    def stop(self):
        """Stop the auto-monitor"""
        logger.info("Stopping auto-monitor...")
        self.running = False
        
        # Final alert summary
        summary = self.alert_manager.get_alert_summary()
        if summary["total"] > 0:
            logger.warning(f"Shutting down with {summary['total']} active alerts")
            for alert in self.alert_manager.get_active_alerts():
                logger.warning(f"  - {alert.name}: {alert.message}")
    """Main auto-monitor application."""
    
    def __init__(self, config: MonitorConfig):
        self.config = config
        self.running = False
        
        # Initialize components
        self.metrics_collector = MetricsCollector(
            interval=config.collection_interval
        )
        self.log_collector = LogCollector()
        self.event_collector = EventCollector()
        
        self.alert_manager = AlertManager()
        self.storage: StorageBackend = InMemoryStorage()
        
        # Setup default alert rules
        for rule in create_default_rules():
            self.alert_manager.add_rule(rule)
        
        # Register alert handler
        self.alert_manager.add_handler(self._handle_alert)
        
        logger.info("✅ AutoMonitorApp initialized")
    
    def _handle_alert(self, alert):
        """Handle fired alerts."""
        # Store alert
        self.storage.store_alert(alert)
        
        # Log alert
        logger.warning(f"🚨 {alert.severity.value.upper()}: {alert.message}")
        
        # Additional handling (webhooks, notifications, etc.) can be added here
    
    async def collect_metrics(self):
        """Continuously collect metrics."""
        while self.running:
            try:
                metrics = self.metrics_collector.collect()
                
                # Store metrics
                self.storage.store_metrics(metrics)
                
                # Evaluate alert rules
                self.alert_manager.evaluate_rules(metrics)
                
                # Log metrics in development mode
                if self.config.mode == 'development':
                    logger.debug(f"📊 Metrics: {metrics}")
                
                await asyncio.sleep(self.config.collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def collect_logs(self):
        """Continuously collect logs."""
        while self.running:
            try:
                logs = self.log_collector.collect()
                
                if logs:
                    self.storage.store_logs(logs)
                
                await asyncio.sleep(self.config.log_collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting logs: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def collect_events(self):
        """Continuously collect events."""
        while self.running:
            try:
                events = self.event_collector.collect()
                
                if events:
                    self.storage.store_events(events)
                
                await asyncio.sleep(self.config.event_collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting events: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def run_async(self):
        """Run the application asynchronously."""
        self.running = True
        
        logger.info("🚀 Starting auto-monitor collectors...")
        
        # Create tasks for all collectors
        tasks = [
            asyncio.create_task(self.collect_metrics()),
            asyncio.create_task(self.collect_logs()),
            asyncio.create_task(self.collect_events()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("⏹️  Shutting down collectors...")
            self.running = False
    
    def run(self):
        """Run the application (blocking)."""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            logger.info("\n⏹️  Received shutdown signal")
            self.running = False
    
    def get_status(self) -> Dict:
        """Get application status."""
        return {
            'running': self.running,
            'mode': self.config.mode,
            'uptime': 'N/A',  # TODO: Track uptime
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'metrics_collected': self.storage.get_metrics_count(),
            'logs_collected': self.storage.get_logs_count(),
            'events_collected': self.storage.get_events_count(),
        }
Main application for MachineNativeOps Auto Monitor
Core monitoring logic without auto-installation
"""

import os
import sys
import time
import threading
import logging
import signal
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

import psutil
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import Config
from .collectors import SystemCollector, QuantumCollector, KubernetesCollector
from .storage import DatabaseManager
from .alerts import AlertManager

class MachineNativeOpsAutoMonitor:
    """Main monitoring application class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.db_manager = DatabaseManager(config.database.path)
        self.system_collector = SystemCollector()
        self.quantum_collector = QuantumCollector(config.quantum)
        self.k8s_collector = KubernetesCollector(config.services)
        self.alert_manager = AlertManager(config.monitoring, config.auto_repair)
        
        # Prometheus metrics
        self._init_prometheus_metrics()
        
        # FastAPI application
        self.app = FastAPI(
            title="MachineNativeOps Auto Monitor",
            description="System monitoring with quantum state tracking",
            version=config.version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        self._setup_fastapi_routes()
        
        # Control flags
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.logger.info("MachineNativeOps Auto Monitor initialized")
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        self.metrics = {
            'cpu_usage': Gauge('machinenativenops_cpu_usage_percent', 'CPU usage percentage'),
            'memory_usage': Gauge('machinenativenops_memory_usage_percent', 'Memory usage percentage'),
            'disk_usage': Gauge('machinenativenops_disk_usage_percent', 'Disk usage percentage'),
            'network_bytes_sent': Gauge('machinenativenops_network_bytes_sent_total', 'Total bytes sent'),
            'network_bytes_recv': Gauge('machinenativenops_network_bytes_recv_total', 'Total bytes received'),
            'quantum_fidelity': Gauge('machinenativenops_quantum_fidelity', 'Quantum state fidelity'),
            'quantum_coherence_time': Gauge('machinenativenops_quantum_coherence_time_microseconds', 'Quantum coherence time'),
            'quantum_error_rate': Gauge('machinenativenops_quantum_error_rate', 'Quantum error rate'),
            'active_services': Gauge('machinenativenops_active_services_count', 'Number of active services'),
            'collection_duration': Histogram('machinenativenops_collection_duration_seconds', 'Collection duration'),
            'alerts_total': Counter('machinenativenops_alerts_total', 'Total alerts triggered'),
        }
        
        self.logger.info("Prometheus metrics initialized")
    
    def _setup_fastapi_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                # Basic health checks
                db_status = self.db_manager.health_check()
                system_load = psutil.cpu_percent(interval=0.1)
                
                health_data = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": self.config.version,
                    "architecture_hash": self.config.architecture_hash,
                    "database_status": "ok" if db_status else "error",
                    "system_load": system_load,
                    "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
                }
                
                # Include service status if not healthy
                if system_load > 90:
                    health_data["status"] = "degraded"
                    health_data["warnings"] = ["High system load"]
                
                return JSONResponse(health_data)
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail="Service unavailable")
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint - handled by prometheus_client"""
            pass
        
        @self.app.get("/status")
        async def status():
            """Detailed status endpoint"""
            try:
                recent_metrics = self.db_manager.get_recent_metrics(limit=10)
                alerts = self.alert_manager.get_active_alerts()
                
                status_data = {
                    "status": "running" if self._running else "stopped",
                    "timestamp": datetime.utcnow().isoformat(),
                    "config": {
                        "monitoring_interval": self.config.monitoring.interval,
                        "prometheus_port": self.config.monitoring.prometheus_port,
                        "quantum_enabled": self.config.quantum.enabled,
                        "auto_repair_enabled": self.config.auto_repair.enabled,
                    },
                    "recent_metrics_count": len(recent_metrics),
                    "active_alerts_count": len(alerts),
                    "database_stats": self.db_manager.get_stats()
                }
                
                return JSONResponse(status_data)
                
            except Exception as e:
                self.logger.error(f"Status check failed: {e}")
                raise HTTPException(status_code=500, detail="Status check failed")
        
        @self.app.get("/api/v1/metrics")
        async def get_metrics(limit: int = 100):
            """Get recent metrics"""
            try:
                metrics = self.db_manager.get_recent_metrics(limit=limit)
                return JSONResponse({"metrics": metrics, "count": len(metrics)})
            except Exception as e:
                self.logger.error(f"Failed to get metrics: {e}")
                raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
        
        @self.app.get("/api/v1/alerts")
        async def get_alerts():
            """Get active alerts"""
            try:
                alerts = self.alert_manager.get_active_alerts()
                return JSONResponse({"alerts": alerts, "count": len(alerts)})
            except Exception as e:
                self.logger.error(f"Failed to get alerts: {e}")
                raise HTTPException(status_code=500, detail="Failed to retrieve alerts")
    
    def collect_once(self) -> Dict[str, Any]:
        """Perform one-time metrics collection"""
        self.logger.info("Starting one-time metrics collection")
        
        start_time = time.time()
        metrics = {}
        
        try:
            # System metrics collection
            system_metrics = self.system_collector.collect()
            metrics.update(system_metrics)
            
            # Quantum metrics (if enabled)
            if self.config.quantum.enabled:
                try:
                    quantum_metrics = self.quantum_collector.collect()
                    metrics.update(quantum_metrics)
                except Exception as e:
                    self.logger.warning(f"Quantum collection failed: {e}")
                    metrics["quantum_error"] = str(e)
            
            # Kubernetes services metrics
            try:
                k8s_metrics = self.k8s_collector.collect()
                metrics.update(k8s_metrics)
            except Exception as e:
                self.logger.warning(f"Kubernetes collection failed: {e}")
                metrics["kubernetes_error"] = str(e)
            
            # Update Prometheus metrics
            self._update_prometheus_metrics(metrics)
            
            # Store to database
            self.db_manager.store_metrics(metrics)
            
            # Check for alerts
            self.alert_manager.check_alerts(metrics)
            
            duration = time.time() - start_time
            metrics['collection_duration'] = duration
            
            self.logger.info(f"Collection completed in {duration:.2f}s")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            raise
    
    def _update_prometheus_metrics(self, metrics: Dict[str, Any]):
        """Update Prometheus gauge metrics"""
        gauge_mappings = {
            'cpu_usage': 'cpu_usage_percent',
            'memory_usage': 'memory_usage_percent', 
            'disk_usage': 'disk_usage_percent',
            'network_bytes_sent': 'network_bytes_sent_total',
            'network_bytes_recv': 'network_bytes_recv_total',
            'quantum_fidelity': 'quantum_fidelity',
            'quantum_coherence_time': 'quantum_coherence_time_microseconds',
            'quantum_error_rate': 'quantum_error_rate',
            'active_services': 'active_services_count',
        }
        
        for metric_key, gauge_name in gauge_mappings.items():
            if metric_key in metrics and isinstance(metrics[metric_key], (int, float)):
                self.metrics[gauge_name].set(metrics[metric_key])
        
        # Update collection duration histogram
        if 'collection_duration' in metrics:
            self.metrics['collection_duration'].observe(metrics['collection_duration'])
    
    def run_serve(self):
        """Run monitoring service in daemon mode"""
        self.logger.info("Starting MachineNativeOps Auto Monitor service")
        
        self._running = True
        self.start_time = time.time()
        
        # Start Prometheus HTTP server
        start_http_server(self.config.monitoring.prometheus_port)
        self.logger.info(f"Prometheus server started on port {self.config.monitoring.prometheus_port}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        
        try:
            self.logger.info("Service running. Press Ctrl+C to stop.")
            self._shutdown_event.wait()
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
        finally:
            self._shutdown()
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running and not self._shutdown_event.is_set():
            try:
                self.collect_once()
                
                # Wait for next collection interval
                self._shutdown_event.wait(self.config.monitoring.interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                # Continue running even if individual collection fails
                self._shutdown_event.wait(min(60, self.config.monitoring.interval))
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown_event.set()
    
    def _shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down MachineNativeOps Auto Monitor")
        
        self._running = False
        self._shutdown_event.set()
        
        # Close database connection
        self.db_manager.close()
        
        self.logger.info("Shutdown complete")
