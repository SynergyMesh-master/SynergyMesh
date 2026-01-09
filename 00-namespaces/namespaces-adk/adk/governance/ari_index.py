"""
ARI Index: Calculates the Agency-Risk Index for agents.

This module quantifies autonomy, adaptability, and continuity
to determine governance intensity.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..observability.logging import Logger


class RiskTier(Enum):
    """Risk tier levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ARIScore:
    """Agency-Risk Index score."""
    autonomy: float  # 0.0 to 1.0
    adaptability: float  # 0.0 to 1.0
    continuity: float  # 0.0 to 1.0
    overall: float  # Weighted average
    tier: RiskTier
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "autonomy": self.autonomy,
            "adaptability": self.adaptability,
            "continuity": self.continuity,
            "overall": self.overall,
            "tier": self.tier.value,
            "timestamp": self.timestamp.isoformat()
        }


class ARIIndex:
    """
    Agency-Risk Index calculator.
    
    The ARI quantifies agent risk across three dimensions:
    - Autonomy: How independently the agent operates
    - Adaptability: How much the agent can change its behavior
    - Continuity: How long the agent operates without supervision
    """
    
    def __init__(
        self,
        autonomy_weight: float = 0.4,
        adaptability_weight: float = 0.3,
        continuity_weight: float = 0.3
    ):
        self.autonomy_weight = autonomy_weight
        self.adaptability_weight = adaptability_weight
        self.continuity_weight = continuity_weight
        
        self.logger = Logger(name="governance.ari")
        
        # Current scores
        self._current_score: ARIScore = ARIScore(
            autonomy=0.0,
            adaptability=0.0,
            continuity=0.0,
            overall=0.0,
            tier=RiskTier.LOW
        )
        
        # Score history
        self._history: list[ARIScore] = []
    
    def calculate_score(
        self,
        autonomy_metrics: Dict[str, Any],
        adaptability_metrics: Dict[str, Any],
        continuity_metrics: Dict[str, Any]
    ) -> ARIScore:
        """
        Calculate ARI score from metrics.
        
        Args:
            autonomy_metrics: Autonomy metrics
            adaptability_metrics: Adaptability metrics
            continuity_metrics: Continuity metrics
            
        Returns:
            ARI score
        """
        # Calculate individual scores
        autonomy = self._calculate_autonomy(autonomy_metrics)
        adaptability = self._calculate_adaptability(adaptability_metrics)
        continuity = self._calculate_continuity(continuity_metrics)
        
        # Calculate weighted average
        overall = (
            autonomy * self.autonomy_weight +
            adaptability * self.adaptability_weight +
            continuity * self.continuity_weight
        )
        
        # Determine risk tier
        tier = self._determine_tier(overall)
        
        score = ARIScore(
            autonomy=autonomy,
            adaptability=adaptability,
            continuity=continuity,
            overall=overall,
            tier=tier
        )
        
        self._current_score = score
        self._history.append(score)
        
        return score
    
    def _calculate_autonomy(self, metrics: Dict[str, Any]) -> float:
        """Calculate autonomy score."""
        score = 0.0
        
        # Decision-making autonomy
        if metrics.get("makes_decisions", False):
            score += 0.3
        
        # Tool selection autonomy
        if metrics.get("selects_tools", False):
            score += 0.3
        
        # Workflow planning autonomy
        if metrics.get("plans_workflows", False):
            score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_adaptability(self, metrics: Dict[str, Any]) -> float:
        """Calculate adaptability score."""
        score = 0.0
        
        # Learning capability
        if metrics.get("can_learn", False):
            score += 0.3
        
        # Self-modification
        if metrics.get("can_modify_self", False):
            score += 0.4
        
        # Context adaptation
        if metrics.get("adapts_to_context", False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_continuity(self, metrics: Dict[str, Any]) -> float:
        """Calculate continuity score."""
        score = 0.0
        
        # Long-running capability
        if metrics.get("long_running", False):
            score += 0.3
        
        # Persistent state
        if metrics.get("persistent_state", False):
            score += 0.3
        
        # Multi-session memory
        if metrics.get("cross_session_memory", False):
            score += 0.4
        
        return min(score, 1.0)
    
    def _determine_tier(self, overall: float) -> RiskTier:
        """Determine risk tier from overall score."""
        if overall < 0.25:
            return RiskTier.LOW
        elif overall < 0.5:
            return RiskTier.MEDIUM
        elif overall < 0.75:
            return RiskTier.HIGH
        else:
            return RiskTier.CRITICAL
    
    def get_current_score(self) -> ARIScore:
        """Get current ARI score."""
        return self._current_score
    
    def get_history(self, limit: int = 100) -> list[ARIScore]:
        """Get score history."""
        return self._history[-limit:]