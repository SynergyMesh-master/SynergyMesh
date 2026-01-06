#!/usr/bin/env python3
"""
L13: Digital Twin - Simulation Engine
AXIOM Layer 13: 數字孿生 - 模擬引擎

Responsibilities:
- System state simulation
- What-if scenario analysis
- Predictive modeling support
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
import random
import copy


class SimulationMode(Enum):
    """Simulation modes."""
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    HYBRID = "hybrid"


class ScenarioType(Enum):
    """Scenario types for what-if analysis."""
    LOAD_SPIKE = "load_spike"
    COMPONENT_FAILURE = "component_failure"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SECURITY_INCIDENT = "security_incident"


@dataclass
class SimulationState:
    """Simulation state at a point in time."""
    timestamp: datetime
    components: Dict[str, Dict[str, Any]]
    metrics: Dict[str, float]
    events: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SimulationScenario:
    """Simulation scenario definition."""
    id: str
    name: str
    type: ScenarioType
    parameters: Dict[str, Any]
    duration: timedelta
    initial_state: Optional[SimulationState] = None


@dataclass
class SimulationResult:
    """Result of a simulation run."""
    scenario_id: str
    start_time: datetime
    end_time: datetime
    states: List[SimulationState]
    metrics_summary: Dict[str, Dict[str, float]]  # metric -> {min, max, avg}
    events: List[Dict[str, Any]]
    recommendations: List[str]


class SimulationEngine:
    """
    Simulation engine for L13 Digital Twin layer.

    Provides system simulation and what-if analysis capabilities.
    """

    VERSION = "2.0.0"
    LAYER = "L13_digital_twin"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mode = SimulationMode.DISCRETE
        self._time_step = timedelta(seconds=config.get("time_step", 1)) if config else timedelta(seconds=1)
        self._models: Dict[str, Callable] = {}
        self._current_state: Optional[SimulationState] = None
        self._setup_default_models()

    def _setup_default_models(self) -> None:
        """Setup default simulation models."""
        self._models["load"] = self._model_load
        self._models["latency"] = self._model_latency
        self._models["resource"] = self._model_resource
        self._models["failure"] = self._model_failure

    async def run_scenario(self, scenario: SimulationScenario) -> SimulationResult:
        """Run a simulation scenario."""
        # Initialize state
        if scenario.initial_state:
            self._current_state = copy.deepcopy(scenario.initial_state)
        else:
            self._current_state = self._create_default_state()

        states = [copy.deepcopy(self._current_state)]
        events = []
        current_time = self._current_state.timestamp

        # Apply scenario parameters
        await self._apply_scenario(scenario)

        # Run simulation
        while current_time < self._current_state.timestamp + scenario.duration:
            # Advance time
            current_time += self._time_step

            # Run models
            await self._step(current_time, scenario)

            # Record state
            states.append(copy.deepcopy(self._current_state))

            # Check for events
            new_events = self._check_events()
            events.extend(new_events)

        # Calculate summary
        metrics_summary = self._calculate_metrics_summary(states)
        recommendations = self._generate_recommendations(metrics_summary, events)

        return SimulationResult(
            scenario_id=scenario.id,
            start_time=states[0].timestamp,
            end_time=states[-1].timestamp,
            states=states,
            metrics_summary=metrics_summary,
            events=events,
            recommendations=recommendations,
        )

    def _create_default_state(self) -> SimulationState:
        """Create default simulation state."""
        return SimulationState(
            timestamp=datetime.now(timezone.utc),
            components={
                "api_gateway": {"healthy": True, "load": 0.3},
                "backend_service": {"healthy": True, "load": 0.4},
                "database": {"healthy": True, "load": 0.2},
                "cache": {"healthy": True, "load": 0.1},
            },
            metrics={
                "latency_p50": 50.0,
                "latency_p99": 200.0,
                "throughput": 1000.0,
                "error_rate": 0.01,
                "cpu_usage": 0.4,
                "memory_usage": 0.5,
            },
        )

    async def _apply_scenario(self, scenario: SimulationScenario) -> None:
        """Apply scenario parameters to state."""
        if scenario.type == ScenarioType.LOAD_SPIKE:
            multiplier = scenario.parameters.get("multiplier", 2.0)
            for component in self._current_state.components.values():
                component["load"] = min(component.get("load", 0) * multiplier, 1.0)

        elif scenario.type == ScenarioType.COMPONENT_FAILURE:
            target = scenario.parameters.get("target")
            if target and target in self._current_state.components:
                self._current_state.components[target]["healthy"] = False

        elif scenario.type == ScenarioType.RESOURCE_EXHAUSTION:
            resource = scenario.parameters.get("resource", "cpu")
            self._current_state.metrics[f"{resource}_usage"] = 0.95

    async def _step(self, current_time: datetime, scenario: SimulationScenario) -> None:
        """Execute one simulation step."""
        self._current_state.timestamp = current_time

        # Run each model
        for name, model in self._models.items():
            await model(self._current_state, scenario)

    async def _model_load(self, state: SimulationState,
                         scenario: SimulationScenario) -> None:
        """Model load changes over time."""
        noise = random.gauss(0, 0.02)
        for component in state.components.values():
            load = component.get("load", 0.5)
            # Mean reversion with noise
            component["load"] = max(0, min(1, load + noise))

    async def _model_latency(self, state: SimulationState,
                            scenario: SimulationScenario) -> None:
        """Model latency based on load."""
        avg_load = sum(c.get("load", 0) for c in state.components.values()) / len(state.components)

        # Latency increases with load
        base_latency = 50
        state.metrics["latency_p50"] = base_latency * (1 + avg_load)
        state.metrics["latency_p99"] = state.metrics["latency_p50"] * 4

    async def _model_resource(self, state: SimulationState,
                             scenario: SimulationScenario) -> None:
        """Model resource usage."""
        avg_load = sum(c.get("load", 0) for c in state.components.values()) / len(state.components)
        state.metrics["cpu_usage"] = 0.2 + avg_load * 0.6
        state.metrics["memory_usage"] = 0.3 + avg_load * 0.4

    async def _model_failure(self, state: SimulationState,
                            scenario: SimulationScenario) -> None:
        """Model failure probability."""
        # Higher load = higher failure probability
        for name, component in state.components.items():
            if component.get("healthy", True):
                load = component.get("load", 0)
                failure_prob = load * 0.001  # 0.1% at full load
                if random.random() < failure_prob:
                    component["healthy"] = False
                    state.events.append({
                        "type": "component_failure",
                        "component": name,
                        "timestamp": state.timestamp.isoformat(),
                    })

    def _check_events(self) -> List[Dict[str, Any]]:
        """Check for and return new events."""
        events = self._current_state.events.copy()
        self._current_state.events.clear()
        return events

    def _calculate_metrics_summary(self,
                                   states: List[SimulationState]) -> Dict[str, Dict[str, float]]:
        """Calculate metrics summary from states."""
        summary = {}

        for metric in states[0].metrics.keys():
            values = [s.metrics.get(metric, 0) for s in states]
            summary[metric] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        return summary

    def _generate_recommendations(self, metrics: Dict[str, Dict[str, float]],
                                 events: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on simulation results."""
        recommendations = []

        # Check latency
        if metrics.get("latency_p99", {}).get("max", 0) > 500:
            recommendations.append("Consider adding caching layer to reduce latency")

        # Check resource usage
        if metrics.get("cpu_usage", {}).get("max", 0) > 0.8:
            recommendations.append("CPU usage peaked high - consider horizontal scaling")

        # Check failures
        if len(events) > 0:
            recommendations.append(f"Detected {len(events)} failure events - review resilience")

        return recommendations

    def register_model(self, name: str, model: Callable) -> None:
        """Register a custom simulation model."""
        self._models[name] = model


# Module exports
__all__ = [
    "SimulationEngine",
    "SimulationMode",
    "SimulationState",
    "SimulationScenario",
    "SimulationResult",
    "ScenarioType",
]
