"""
MCP Integration Layer: Model Context Protocol integration.

This package provides MCP client functionality for tool discovery,
invocation, and security.
"""

from .mcp_client import (
    MCPClient,
    MCPServerConfig,
    MCPTransportType,
    MCPTool,
    MCPToolCall,
    MCPToolResult
)
from .tool_router import (
    ToolRouter,
    ToolEndpoint,
    RoutingPolicy,
    RoutingStrategy
)
from .tool_schemas import (
    ToolSchemas,
    ToolSchema,
    ParameterSchema,
    SchemaValidator,
    SchemaConverter,
    SchemaFormat
)
from .a2a_client import (
    A2AClient,
    AgentInfo,
    AgentCapabilities,
    A2AMessage,
    DelegationRequest,
    DelegationResponse,
    A2AMessageType,
    A2AProtocolVersion
)
from .mcp_security import (
    MCPSecurity,
    AccessPolicy,
    SecurityContext,
    AuthConfig,
    AuthMethod
)

__all__ = [
    # MCP Client
    "MCPClient",
    "MCPServerConfig",
    "MCPTransportType",
    "MCPTool",
    "MCPToolCall",
    "MCPToolResult",
    
    # Tool Router
    "ToolRouter",
    "ToolEndpoint",
    "RoutingPolicy",
    "RoutingStrategy",
    
    # Tool Schemas
    "ToolSchemas",
    "ToolSchema",
    "ParameterSchema",
    "SchemaValidator",
    "SchemaConverter",
    "SchemaFormat",
    
    # A2A Client
    "A2AClient",
    "AgentInfo",
    "AgentCapabilities",
    "A2AMessage",
    "DelegationRequest",
    "DelegationResponse",
    "A2AMessageType",
    "A2AProtocolVersion",
    
    # MCP Security
    "MCPSecurity",
    "AccessPolicy",
    "SecurityContext",
    "AuthConfig",
    "AuthMethod",
]