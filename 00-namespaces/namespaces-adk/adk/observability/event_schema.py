"""
Event Schema: Defines event schema definitions for observability.

This module provides schemas for structured events and
standardized event definitions.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    """Event types."""
    AGENT_START = "agent.start"
    AGENT_STOP = "agent.stop"
    WORKFLOW_START = "workflow.start"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_FAIL = "workflow.fail"
    TOOL_CALL_START = "tool_call.start"
    TOOL_CALL_COMPLETE = "tool_call.complete"
    TOOL_CALL_FAIL = "tool_call.fail"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    CONTEXT_UPDATE = "context.update"
    ERROR_OCCURRED = "error.occurred"
    POLICY_VIOLATION = "policy.violation"
    DRIFT_DETECTED = "drift.detected"
    CONTAINMENT_CHANGED = "containment.changed"
    AUTH_REQUEST = "auth.request"
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    PERMISSION_DENIED = "permission.denied"


@dataclass
class EventSchemaDef:
    """Event schema definition."""
    event_type: EventType
    version: str = "1.0"
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema."""
        return {
            "type": "object",
            "properties": {
                "event_type": {"const": self.event_type.value},
                "timestamp": {"type": "string", "format": "date-time"},
                "version": {"const": self.version},
                **self.fields
            },
            "required": ["event_type", "timestamp", "version"] + self.required_fields
        }


class EventSchemaRegistry:
    """
    Event schema definitions and validation.
    
    Features:
    - Standardized event schemas
    - Event validation
    - Schema versioning
    - Event serialization
    """
    
    # Standard event schemas
    SCHEMAS: Dict[str, EventSchemaDef] = {}
    
    @classmethod
    def define_schema(cls, schema: EventSchemaDef) -> None:
        """Define an event schema."""
        cls.SCHEMAS[schema.event_type.value] = schema
    
    @classmethod
    def get_schema(cls, event_type: EventType) -> Optional[EventSchemaDef]:
        """Get schema for an event type."""
        key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        return cls.SCHEMAS.get(key)
    
    @classmethod
    def validate_event(cls, event: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate an event against its schema."""
        event_type = event.get("event_type")
        schema = cls.SCHEMAS.get(event_type)
        
        if not schema:
            return False, f"Unknown event type: {event_type}"
        
        # Check required fields
        for field in schema.required_fields:
            if field not in event:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    @classmethod
    def serialize_event(cls, event: Dict[str, Any]) -> str:
        """Serialize event to JSON."""
        return json.dumps(event)
    
    @classmethod
    def deserialize_event(cls, data: str) -> Dict[str, Any]:
        """Deserialize event from JSON."""
        return json.loads(data)


# Initialize standard schemas
EventSchemaRegistry.define_schema(EventSchemaDef(
    event_type=EventType.AGENT_START,
    fields={
        "agent_id": {"type": "string"},
        "config": {"type": "object"}
    },
    required_fields=["agent_id"]
))

EventSchemaRegistry.define_schema(EventSchemaDef(
    event_type=EventType.AGENT_STOP,
    fields={
        "agent_id": {"type": "string"},
        "reason": {"type": "string"}
    },
    required_fields=["agent_id"]
))

EventSchemaRegistry.define_schema(EventSchemaDef(
    event_type=EventType.WORKFLOW_START,
    fields={
        "workflow_id": {"type": "string"},
        "execution_id": {"type": "string"},
        "context": {"type": "object"}
    },
    required_fields=["workflow_id", "execution_id"]
))

EventSchemaRegistry.define_schema(EventSchemaDef(
    event_type=EventType.TOOL_CALL_START,
    fields={
        "tool_name": {"type": "string"},
        "call_id": {"type": "string"},
        "arguments": {"type": "object"},
        "server_id": {"type": "string"}
    },
    required_fields=["tool_name", "call_id"]
))

EventSchemaRegistry.define_schema(EventSchemaDef(
    event_type=EventType.TOOL_CALL_COMPLETE,
    fields={
        "call_id": {"type": "string"},
        "output": {"type": "object"},
        "duration_seconds": {"type": "number"}
    },
    required_fields=["call_id"]
))

EventSchemaRegistry.define_schema(EventSchemaDef(
    event_type=EventType.ERROR_OCCURRED,
    fields={
        "error_type": {"type": "string"},
        "severity": {"type": "string"},
        "message": {"type": "string"},
        "context": {"type": "object"}
    },
    required_fields=["error_type", "message"]
))
