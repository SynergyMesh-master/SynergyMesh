"""
Metrics: Collects and exposes runtime metrics for monitoring.

This module provides metrics collection for performance monitoring
and operational visibility.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """A metric."""
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    help_text: str = ""


class MetricsCollector:
    """
    Collects and exposes runtime metrics.
    
    Features:
    - Counter, gauge, histogram, summary metrics
    - Label-based filtering
    - Prometheus-compatible export
    - Real-time monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Metric storage
        self._counters: Dict[str, Dict[tuple, float]] = defaultdict(lambda: 0.0)
        self._gauges: Dict[str, Dict[tuple, float]] = {}
        self._histograms: Dict[str, Dict[tuple, List[float]]] = defaultdict(list)
        self._summaries: Dict[str, Dict[tuple, List[float]]] = defaultdict(list)
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Metric help text
        self._help_text: Dict[str, str] = {}
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """Increment a counter metric."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        
        with self._lock:
            self._counters[name][label_tuple] += value
        
        if help_text:
            self._help_text[name] = help_text
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """Set a gauge metric."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        
        with self._lock:
            self._gauges[name][label_tuple] = value
        
        if help_text:
            self._help_text[name] = help_text
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """Observe a histogram metric."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        
        with self._lock:
            self._histograms[name][label_tuple].append(value)
        
        if help_text:
            self._help_text[name] = help_text
    
    def observe_summary(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """Observe a summary metric."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        
        with self._lock:
            self._summaries[name][label_tuple].append(value)
        
        if help_text:
            self._help_text[name] = help_text
    
    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get counter value."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        return self._counters.get(name, {}).get(label_tuple)
    
    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get gauge value."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        return self._gauges.get(name, {}).get(label_tuple)
    
    def get_histogram(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[List[float]]:
        """Get histogram values."""
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        return self._histograms.get(name, {}).get(label_tuple, []).copy()
    
    def get_summary(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        quantiles: Optional[List[float]] = None
    ) -> Optional[Dict[str, float]]:
        """Get summary statistics."""
        quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        label_tuple = tuple(sorted(labels.items())) if labels else ()
        values = self._summaries.get(name, {}).get(label_tuple, [])
        
        if not values:
            return None
        
        sorted_values = sorted(values)
        stats = {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }
        
        for q in quantiles:
            index = int(q * len(values))
            stats[f"p{int(q*100)}"] = sorted_values[index]
        
        return stats
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Export counters
        for name, label_values in self._counters.items():
            help_text = self._help_text.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} counter")
            for label_tuple, value in label_values.items():
                labels = ",".join(f'{k}="{v}"' for k, v in label_tuple)
                if labels:
                    lines.append(f'{name}{{{labels}}} {value}')
                else:
                    lines.append(f'{name} {value}')
        
        # Export gauges
        for name, label_values in self._gauges.items():
            help_text = self._help_text.get(name, "")
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")
            for label_tuple, value in label_values.items():
                labels = ",".join(f'{k}="{v}"' for k, v in label_tuple)
                if labels:
                    lines.append(f'{name}{{{labels}}} {value}')
                else:
                    lines.append(f'{name} {value}')
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()


# Context manager for timing
class Timer:
    """Context manager for timing operations."""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.HISTOGRAM
    ):
        self.metrics_collector = metrics_collector
        self.name = name
        self.labels = labels
        self.metric_type = metric_type
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            if self.metric_type == MetricType.HISTOGRAM:
                self.metrics_collector.observe_histogram(
                    self.name,
                    duration,
                    self.labels
                )
            elif self.metric_type == MetricType.SUMMARY:
                self.metrics_collector.observe_summary(
                    self.name,
                    duration,
                    self.labels
                )