"""
Namespace-ADK: Machine-Native AI Agent Runtime Layer

A comprehensive agent runtime framework that orchestrates MCP tools,
manages agent memory and context, enforces runtime governance,
and supports multi-step, auditable workflows.

Version: 1.0.0
License: Apache 2.0
"""

__version__ = "1.0.0"
__author__ = "MachineNativeOps"

from .core.agent_runtime import AgentRuntime
from .core.workflow_orchestrator import WorkflowOrchestrator
from .core.memory_manager import MemoryManager
from .core.context_manager import ContextManager
from .core.event_bus import EventBus
from .core.error_handling import ErrorHandler
from .core.plugin_manager import PluginManager
from .core.sandbox import Sandbox

from .mcp.mcp_client import MCPClient
from .mcp.tool_router import ToolRouter
from .mcp.tool_schemas import ToolSchemas
from .mcp.a2a_client import A2AClient
from .mcp.mcp_security import MCPSecurity

from .governance.mi9_runtime import MI9Runtime
from .governance.ari_index import ARIIndex
from .governance.conformance_engine import ConformanceEngine
from .governance.drift_detection import DriftDetection
from .governance.containment import Containment
from .governance.audit_trail import AuditTrail

from .observability.logging import Logger
from .observability.tracing import Tracer
from .observability.metrics import MetricsCollector
from .observability.event_schema import EventSchema

from .security.auth import Authenticator
from .security.a2a_auth import A2AAuthenticator
from .security.permissioning import PermissionManager
from .security.pii_filter import PIIFilter

__all__ = [
    # Core
    "AgentRuntime",
    "WorkflowOrchestrator",
    "MemoryManager",
    "ContextManager",
    "EventBus",
    "ErrorHandler",
    "PluginManager",
    "Sandbox",
    
    # MCP
    "MCPClient",
    "ToolRouter",
    "ToolSchemas",
    "A2AClient",
    "MCPSecurity",
    
    # Governance
    "MI9Runtime",
    "ARIIndex",
    "ConformanceEngine",
    "DriftDetection",
    "Containment",
    "AuditTrail",
    
    # Observability
    "Logger",
    "Tracer",
    "MetricsCollector",
    "EventSchema",
    
    # Security
    "Authenticator",
    "A2AAuthenticator",
    "PermissionManager",
    "PIIFilter",
]