"""
Containment: Implements graduated containment strategies.

This module provides graduated containment levels for runtime
intervention, from monitoring to execution isolation.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..observability.logging import Logger


class ContainmentLevel(Enum):
    """Containment levels."""
    NONE = "none"
    MONITOR = "monitor"
    RESTRICT = "restrict"
    SANDBOX = "sandbox"
    ISOLATE = "isolate"
    TERMINATE = "terminate"


@dataclass
class ContainmentAction:
    """A containment action."""
    action_id: str
    level: ContainmentLevel
    agent_id: str
    timestamp: datetime
    reason: str
    metadata: Dict[str, Any]


class Containment:
    """
    Implements graduated containment strategies.
    
    Containment levels:
    - NONE: No restrictions
    - MONITOR: Log all actions
    - RESTRICT: Limit tool access
    - SANDBOX: Execute in sandbox
    - ISOLATE: Full network isolation
    - TERMINATE: Stop execution
    """
    
    def __init__(self):
        self.logger = Logger(name="governance.containment")
        
        # Current containment level per agent
        self._levels: Dict[str, ContainmentLevel] = {}
        
        # Action history
        self._actions: List[ContainmentAction] = []
    
    def set_level(
        self,
        agent_id: str,
        level: ContainmentLevel,
        reason: str
    ) -> ContainmentAction:
        """Set containment level for an agent."""
        old_level = self._levels.get(agent_id, ContainmentLevel.NONE)
        self._levels[agent_id] = level
        
        action = ContainmentAction(
            action_id=f"containment_{datetime.now().timestamp()}",
            level=level,
            agent_id=agent_id,
            timestamp=datetime.now(),
            reason=reason,
            metadata={
                "old_level": old_level.value,
                "new_level": level.value
            }
        )
        
        self._actions.append(action)
        self.logger.info(
            f"Set containment level for {agent_id}: {level.value} ({reason})"
        )
        
        return action
    
    def get_level(self, agent_id: str) -> ContainmentLevel:
        """Get containment level for an agent."""
        return self._levels.get(agent_id, ContainmentLevel.NONE)
    
    def should_allow_action(
        self,
        agent_id: str,
        action_type: str
    ) -> bool:
        """Check if action should be allowed based on containment level."""
        level = self.get_level(agent_id)
        
        if level in [ContainmentLevel.ISOLATE, ContainmentLevel.TERMINATE]:
            return False
        
        if level == ContainmentLevel.RESTRICT:
            # Only allow read-only actions
            return action_type in ["read", "query"]
        
        return True
    
    def escalate(self, agent_id: str, reason: str) -> None:
        """Escalate containment level."""
        current = self.get_level(agent_id)
        levels = list(ContainmentLevel)
        
        current_index = levels.index(current)
        if current_index < len(levels) - 1:
            new_level = levels[current_index + 1]
            self.set_level(agent_id, new_level, reason)
    
    def deescalate(self, agent_id: str, reason: str) -> None:
        """Deescalate containment level."""
        current = self.get_level(agent_id)
        levels = list(ContainmentLevel)
        
        current_index = levels.index(current)
        if current_index > 0:
            new_level = levels[current_index - 1]
            self.set_level(agent_id, new_level, reason)
    
    def get_action_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ContainmentAction]:
        """Get containment action history."""
        actions = self._actions
        
        if agent_id:
            actions = [a for a in actions if a.agent_id == agent_id]
        
        return actions[-limit:]