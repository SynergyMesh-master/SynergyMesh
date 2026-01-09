"""
Conformance Engine: Enforces temporal and sequence-based policies.

This module uses finite-state machines for workflow conformance checking.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..observability.logging import Logger


@dataclass
class PolicyRule:
    """A policy rule."""
    rule_id: str
    description: str
    sequence: List[str]
    forbidden_transitions: List[tuple[str, str]]


class ConformanceEngine:
    """Enforces workflow conformance using FSMs."""
    
    def __init__(self):
        self.logger = Logger(name="governance.conformance")
        self._policies: Dict[str, PolicyRule] = {}
        self._state_machines: Dict[str, str] = {}  # workflow_id -> current_state
    
    def add_policy(self, policy: PolicyRule) -> None:
        """Add a policy rule."""
        self._policies[policy.rule_id] = policy
    
    def check_conformance(
        self,
        workflow_id: str,
        current_step: str,
        next_step: str
    ) -> tuple[bool, Optional[str]]:
        """Check if transition conforms to policies."""
        current_state = self._state_machines.get(workflow_id, "")
        
        for policy in self._policies.values():
            # Check forbidden transitions
            if (current_step, next_step) in policy.forbidden_transitions:
                return False, f"Forbidden transition: {current_step} -> {next_step}"
        
        # Update state
        self._state_machines[workflow_id] = next_step
        return True, None
    
    def reset_workflow(self, workflow_id: str) -> None:
        """Reset workflow state."""
        if workflow_id in self._state_machines:
            del self._state_machines[workflow_id]