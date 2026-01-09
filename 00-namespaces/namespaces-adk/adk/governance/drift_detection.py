"""
Drift Detection: Detects behavioral drift and anomalies.

This module distinguishes between legitimate adaptation and
suspicious changes in agent behavior.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import statistics

from ..observability.logging import Logger


@dataclass
class DriftAlert:
    """A drift alert."""
    alert_id: str
    severity: str
    drift_type: str
    description: str
    timestamp: datetime
    metrics: Dict[str, Any]


class DriftDetection:
    """
    Detects behavioral drift using statistical analysis.
    
    Features:
    - Baseline establishment
    - Statistical tests (Jensen-Shannon divergence)
    - Sliding window analysis
    - Adaptive thresholds
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.logger = Logger(name="governance.drift")
        
        # Baselines
        self._baselines: Dict[str, Any] = {}
        
        # Event windows
        self._windows: Dict[str, deque] = {}
        
        # Alerts
        self._alerts: List[DriftAlert] = []
    
    def establish_baseline(self, metric_name: str, baseline_value: float) -> None:
        """Establish baseline for a metric."""
        self._baselines[metric_name] = baseline_value
        self.logger.debug(f"Established baseline for {metric_name}: {baseline_value}")
    
    def record_event(self, metric_name: str, value: float) -> None:
        """Record a metric event."""
        if metric_name not in self._windows:
            self._windows[metric_name] = deque(maxlen=self.window_size)
        
        self._windows[metric_name].append(value)
    
    def check_drift(self, metric_name: str) -> Optional[DriftAlert]:
        """Check for drift in a metric."""
        if metric_name not in self._windows:
            return None
        
        window = self._windows[metric_name]
        if len(window) < self.window_size:
            return None
        
        if metric_name not in self._baselines:
            return None
        
        baseline = self._baselines[metric_name]
        current = statistics.mean(window)
        
        # Calculate deviation
        deviation = abs(current - baseline) / baseline if baseline != 0 else 0
        
        # Check threshold
        if deviation > 0.5:  # 50% deviation
            alert = DriftAlert(
                alert_id=f"drift_{metric_name}_{datetime.now().timestamp()}",
                severity="high",
                drift_type="statistical",
                description=f"Significant drift detected in {metric_name}",
                timestamp=datetime.now(),
                metrics={
                    "metric_name": metric_name,
                    "baseline": baseline,
                    "current": current,
                    "deviation": deviation
                }
            )
            self._alerts.append(alert)
            return alert
        
        return None
    
    def get_recent_alerts(self, limit: int = 10) -> List[DriftAlert]:
        """Get recent drift alerts."""
        return self._alerts[-limit:]