#!/usr/bin/env python3
"""
L5: Autonomous Healing - MAPE-K Control Loop
AXIOM Layer 5: 自主治愈 - MAPE-K 控制迴路

Responsibilities:
- Monitor: Collect system metrics and events
- Analyze: Detect anomalies and issues
- Plan: Generate remediation plans
- Execute: Apply fixes automatically
- Knowledge: Learn from past incidents
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import asyncio


class LoopState(Enum):
    """MAPE-K loop state."""
    IDLE = "idle"
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    LEARNING = "learning"


class SeverityLevel(Enum):
    """Issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetric:
    """System metric data."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Detected anomaly."""
    id: str
    type: str
    severity: SeverityLevel
    description: str
    metrics: List[SystemMetric]
    detected_at: datetime


@dataclass
class RemediationPlan:
    """Remediation plan."""
    id: str
    anomaly_id: str
    actions: List[Dict[str, Any]]
    estimated_duration: int  # seconds
    risk_level: str
    requires_approval: bool = False


@dataclass
class ExecutionResult:
    """Execution result."""
    plan_id: str
    success: bool
    actions_completed: int
    actions_total: int
    duration: float
    error: Optional[str] = None


class MAPEKLoop:
    """
    MAPE-K autonomic control loop for L5 Autonomous Healing.

    Implements the Monitor-Analyze-Plan-Execute-Knowledge loop
    for self-healing system behavior.
    """

    VERSION = "2.0.0"
    LAYER = "L5_autonomous_healing"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.state = LoopState.IDLE
        self.knowledge_base: List[Dict[str, Any]] = []
        self._monitors: List[Callable] = []
        self._analyzers: List[Callable] = []
        self._planners: List[Callable] = []
        self._executors: List[Callable] = []
        self._running = False

    async def start(self) -> None:
        """Start the MAPE-K loop."""
        self._running = True
        while self._running:
            await self._run_cycle()
            await asyncio.sleep(self.config.get("cycle_interval", 10))

    async def stop(self) -> None:
        """Stop the MAPE-K loop."""
        self._running = False

    async def _run_cycle(self) -> None:
        """Run one complete MAPE-K cycle."""
        # Monitor
        self.state = LoopState.MONITORING
        metrics = await self._monitor()

        # Analyze
        self.state = LoopState.ANALYZING
        anomalies = await self._analyze(metrics)

        if not anomalies:
            self.state = LoopState.IDLE
            return

        # Plan
        self.state = LoopState.PLANNING
        plans = await self._plan(anomalies)

        # Execute
        self.state = LoopState.EXECUTING
        results = await self._execute(plans)

        # Learn
        self.state = LoopState.LEARNING
        await self._learn(anomalies, plans, results)

        self.state = LoopState.IDLE

    async def _monitor(self) -> List[SystemMetric]:
        """Monitor phase: Collect metrics."""
        metrics = []
        for monitor in self._monitors:
            try:
                result = await monitor()
                if isinstance(result, list):
                    metrics.extend(result)
                else:
                    metrics.append(result)
            except Exception as e:
                # Log error but continue monitoring
                pass
        return metrics

    async def _analyze(self, metrics: List[SystemMetric]) -> List[Anomaly]:
        """Analyze phase: Detect anomalies."""
        anomalies = []
        for analyzer in self._analyzers:
            try:
                result = await analyzer(metrics)
                if result:
                    anomalies.extend(result if isinstance(result, list) else [result])
            except Exception:
                # Silently ignore analyzer failures to allow other analyzers to run
                pass
        return anomalies

    async def _plan(self, anomalies: List[Anomaly]) -> List[RemediationPlan]:
        """Plan phase: Generate remediation plans."""
        plans = []
        for anomaly in anomalies:
            for planner in self._planners:
                try:
                    plan = await planner(anomaly, self.knowledge_base)
                    if plan:
                        plans.append(plan)
                        break  # One plan per anomaly
                except Exception:
                    # Silently ignore planner failures and try next planner
                    pass
        return plans

    async def _execute(self, plans: List[RemediationPlan]) -> List[ExecutionResult]:
        """Execute phase: Apply remediation."""
        results = []
        for plan in plans:
            if plan.requires_approval:
                # Skip plans requiring approval (handled separately)
                continue

            for executor in self._executors:
                try:
                    result = await executor(plan)
                    results.append(result)
                    break
                except Exception as e:
                    results.append(ExecutionResult(
                        plan_id=plan.id,
                        success=False,
                        actions_completed=0,
                        actions_total=len(plan.actions),
                        duration=0,
                        error=str(e),
                    ))
        return results

    async def _learn(self, anomalies: List[Anomaly],
                     plans: List[RemediationPlan],
                     results: List[ExecutionResult]) -> None:
        """Knowledge phase: Learn from execution."""
        for anomaly, plan, result in zip(anomalies, plans, results):
            knowledge_entry = {
                "anomaly_type": anomaly.type,
                "severity": anomaly.severity.value,
                "plan_actions": plan.actions,
                "success": result.success,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.knowledge_base.append(knowledge_entry)

            # Prune old knowledge
            max_entries = self.config.get("max_knowledge_entries", 1000)
            if len(self.knowledge_base) > max_entries:
                self.knowledge_base = self.knowledge_base[-max_entries:]

    def register_monitor(self, monitor: Callable) -> None:
        """Register a monitor function."""
        self._monitors.append(monitor)

    def register_analyzer(self, analyzer: Callable) -> None:
        """Register an analyzer function."""
        self._analyzers.append(analyzer)

    def register_planner(self, planner: Callable) -> None:
        """Register a planner function."""
        self._planners.append(planner)

    def register_executor(self, executor: Callable) -> None:
        """Register an executor function."""
        self._executors.append(executor)

    def get_state(self) -> Dict[str, Any]:
        """Get current loop state."""
        return {
            "state": self.state.value,
            "knowledge_entries": len(self.knowledge_base),
            "monitors": len(self._monitors),
            "analyzers": len(self._analyzers),
            "planners": len(self._planners),
            "executors": len(self._executors),
        }


# Module exports
__all__ = [
    "MAPEKLoop",
    "LoopState",
    "SeverityLevel",
    "SystemMetric",
    "Anomaly",
    "RemediationPlan",
    "ExecutionResult",
]
