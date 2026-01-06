#!/usr/bin/env python3
"""
L11: Metacognition - Meta Strategist
AXIOM Layer 11: 元認知 - 元策略師

Responsibilities:
- High-level strategic decision making
- Cross-layer optimization
- Emergent behavior coordination
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone


class StrategyType(Enum):
    """Strategy types."""
    OPTIMIZATION = "optimization"
    ADAPTATION = "adaptation"
    EVOLUTION = "evolution"
    COORDINATION = "coordination"


class StrategyPriority(Enum):
    """Strategy priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class SystemState:
    """Current system state snapshot."""
    timestamp: datetime
    layers: Dict[str, Dict[str, Any]]
    metrics: Dict[str, float]
    health: float  # 0.0 to 1.0


@dataclass
class Strategy:
    """Strategic decision."""
    id: str
    type: StrategyType
    priority: StrategyPriority
    description: str
    actions: List[Dict[str, Any]]
    affected_layers: List[str]
    expected_outcome: Dict[str, Any]
    confidence: float  # 0.0 to 1.0


@dataclass
class StrategicGoal:
    """High-level strategic goal."""
    id: str
    name: str
    target_metrics: Dict[str, float]
    deadline: Optional[datetime] = None
    weight: float = 1.0


class MetaStrategist:
    """
    Meta strategist for L11 Metacognition layer.

    Makes high-level strategic decisions across all AXIOM layers.
    """

    VERSION = "2.0.0"
    LAYER = "L11_metacognition"

    # All AXIOM layers for cross-layer optimization
    AXIOM_LAYERS = [
        "L0_immutable_foundation",
        "L1_neural_compute",
        "L2_knowledge_synthesis",
        "L3_protocol_mesh",
        "L4_multi_agent",
        "L5_autonomous_healing",
        "L6_federated_learning",
        "L7_infrastructure_automation",
        "L8_supply_chain_security",
        "L9_quantum_optimization",
        "L10_system_optimization",
        "L11_metacognition",
        "L12_edge_computing",
        "L13_digital_twin",
        "L14_strategic_governance",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._goals: List[StrategicGoal] = []
        self._strategies: List[Strategy] = []
        self._state_history: List[SystemState] = []
        self._learning_rate = config.get("learning_rate", 0.1) if config else 0.1

    def set_goal(self, goal: StrategicGoal) -> None:
        """Set a strategic goal."""
        self._goals.append(goal)

    def remove_goal(self, goal_id: str) -> bool:
        """Remove a strategic goal."""
        original_len = len(self._goals)
        self._goals = [g for g in self._goals if g.id != goal_id]
        return len(self._goals) < original_len

    async def analyze_state(self, state: SystemState) -> List[Strategy]:
        """Analyze system state and generate strategies."""
        self._state_history.append(state)

        # Keep only recent history
        max_history = self.config.get("max_history", 100)
        if len(self._state_history) > max_history:
            self._state_history = self._state_history[-max_history:]

        strategies = []

        # Analyze each goal
        for goal in self._goals:
            strategy = await self._strategize_for_goal(state, goal)
            if strategy:
                strategies.append(strategy)

        # Cross-layer optimization
        cross_layer = await self._cross_layer_optimization(state)
        strategies.extend(cross_layer)

        # Rank by priority and confidence
        strategies.sort(key=lambda s: (s.priority.value, -s.confidence))

        self._strategies = strategies
        return strategies

    async def _strategize_for_goal(self, state: SystemState,
                                   goal: StrategicGoal) -> Optional[Strategy]:
        """Generate strategy for a specific goal."""
        # Calculate gap between current and target metrics
        gaps = {}
        for metric, target in goal.target_metrics.items():
            current = state.metrics.get(metric, 0)
            gaps[metric] = target - current

        if all(g <= 0 for g in gaps.values()):
            return None  # Goal already achieved

        # Determine actions based on gaps
        actions = []
        affected_layers = []

        for metric, gap in gaps.items():
            if gap > 0:
                layer, action = self._map_metric_to_action(metric, gap)
                actions.append(action)
                if layer not in affected_layers:
                    affected_layers.append(layer)

        return Strategy(
            id=f"strategy_{goal.id}_{datetime.now(timezone.utc).timestamp()}",
            type=StrategyType.OPTIMIZATION,
            priority=StrategyPriority.MEDIUM,
            description=f"Strategy to achieve goal: {goal.name}",
            actions=actions,
            affected_layers=affected_layers,
            expected_outcome=goal.target_metrics,
            confidence=self._calculate_confidence(gaps),
        )

    def _map_metric_to_action(self, metric: str, gap: float) -> Tuple[str, Dict[str, Any]]:
        """Map a metric gap to an action and layer."""
        # Mapping of metrics to responsible layers
        metric_layer_map = {
            "latency": ("L10_system_optimization", "optimize_latency"),
            "throughput": ("L10_system_optimization", "increase_throughput"),
            "availability": ("L5_autonomous_healing", "improve_availability"),
            "security_score": ("L8_supply_chain_security", "enhance_security"),
            "accuracy": ("L1_neural_compute", "improve_accuracy"),
        }

        layer, action_type = metric_layer_map.get(
            metric, ("L10_system_optimization", "generic_optimize")
        )

        action = {
            "type": action_type,
            "metric": metric,
            "target_improvement": gap,
            "layer": layer,
        }

        return layer, action

    def _calculate_confidence(self, gaps: Dict[str, float]) -> float:
        """Calculate confidence based on historical success."""
        base_confidence = 0.7

        # Adjust based on gap magnitude
        avg_gap = sum(abs(g) for g in gaps.values()) / max(len(gaps), 1)
        if avg_gap > 0.5:
            base_confidence -= 0.2
        elif avg_gap < 0.1:
            base_confidence += 0.1

        return min(max(base_confidence, 0.1), 0.95)

    async def _cross_layer_optimization(self, state: SystemState) -> List[Strategy]:
        """Generate cross-layer optimization strategies."""
        strategies = []

        # Check for layer health imbalances
        layer_health = {}
        for layer, data in state.layers.items():
            layer_health[layer] = data.get("health", 1.0)

        # Find underperforming layers
        avg_health = sum(layer_health.values()) / max(len(layer_health), 1)
        for layer, health in layer_health.items():
            if health < avg_health * 0.8:  # 20% below average
                strategy = Strategy(
                    id=f"cross_layer_{layer}_{datetime.now(timezone.utc).timestamp()}",
                    type=StrategyType.COORDINATION,
                    priority=StrategyPriority.HIGH,
                    description=f"Cross-layer optimization for underperforming {layer}",
                    actions=[{
                        "type": "redistribute_load",
                        "from_layer": layer,
                        "to_layers": [l for l in self.AXIOM_LAYERS if l != layer],
                    }],
                    affected_layers=[layer],
                    expected_outcome={"layer_health": avg_health},
                    confidence=0.6,
                )
                strategies.append(strategy)

        return strategies

    def get_active_strategies(self) -> List[Strategy]:
        """Get currently active strategies."""
        return self._strategies

    def get_goals(self) -> List[StrategicGoal]:
        """Get all strategic goals."""
        return self._goals

    def get_state(self) -> Dict[str, Any]:
        """Get current strategist state."""
        return {
            "goals": len(self._goals),
            "active_strategies": len(self._strategies),
            "state_history_size": len(self._state_history),
            "learning_rate": self._learning_rate,
        }


# Module exports
__all__ = [
    "MetaStrategist",
    "Strategy",
    "StrategyType",
    "StrategyPriority",
    "SystemState",
    "StrategicGoal",
]
