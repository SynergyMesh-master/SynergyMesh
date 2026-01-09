"""
Tracing: Implements distributed tracing for workflow execution.

This module provides tracing capabilities for workflow steps,
tool invocations, and agent interactions.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class SpanStatus(Enum):
    """Span status."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    """A trace span."""
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: SpanStatus
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000 if self.end_time else None,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events
        }


@dataclass
class Trace:
    """A distributed trace."""
    trace_id: str
    root_span_id: str
    spans: List[Span] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "spans": [s.to_dict() for s in self.spans]
        }


class Tracer:
    """
    Distributed tracer for workflow execution.
    
    Features:
    - Span creation and management
    - Parent-child relationships
    - Attribute recording
    - Event logging
    - Status tracking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Active traces
        self._traces: Dict[str, Trace] = {}
        
        # Current span stack
        self._span_stack: List[Span] = []
    
    def start_span(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span."""
        span_id = str(uuid.uuid4())
        
        # Get parent span if not provided
        if not parent_span_id and self._span_stack:
            parent_span_id = self._span_stack[-1].span_id
        
        span = Span(
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            start_time=datetime.now(),
            end_time=None,
            status=SpanStatus.UNSET,
            attributes=attributes or {}
        )
        
        # Add to stack
        self._span_stack.append(span)
        
        return span
    
    def end_span(
        self,
        span: Span,
        status: SpanStatus = SpanStatus.OK
    ) -> None:
        """End a span."""
        span.end_time = datetime.now()
        span.status = status
        
        # Remove from stack
        if span in self._span_stack:
            self._span_stack.remove(span)
        
        # Add to trace
        if span.parent_span_id is None:
            # Root span - create trace
            trace_id = str(uuid.uuid4())
            trace = Trace(
                trace_id=trace_id,
                root_span_id=span.span_id,
                spans=[span]
            )
            self._traces[trace_id] = trace
        else:
            # Find parent trace
            for trace in self._traces.values():
                if any(s.span_id == span.parent_span_id for s in trace.spans):
                    trace.spans.append(span)
                    break
    
    def add_attribute(self, span: Span, key: str, value: Any) -> None:
        """Add attribute to span."""
        span.attributes[key] = value
    
    def add_event(self, span: Span, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span."""
        span.events.append({
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {}
        })
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID."""
        return self._traces.get(trace_id)
    
    def get_current_span(self) -> Optional[Span]:
        """Get current span."""
        return self._span_stack[-1] if self._span_stack else None