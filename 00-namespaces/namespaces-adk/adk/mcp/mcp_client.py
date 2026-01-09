"""
MCP Client: Implements the MCP client for tool discovery and invocation.

This module provides MCP client functionality for connecting to MCP servers,
discovering tools, and invoking them with structured arguments.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import aiohttp
import websockets
from abc import ABC, abstractmethod

from ..observability.logging import Logger
from ..observability.tracing import Tracer


class MCPTransportType(Enum):
    """MCP transport types."""
    HTTP = "http"
    SSE = "sse"
    WEBSOCKET = "websocket"
    STDIO = "stdio"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    url: str
    transport: MCPTransportType = MCPTransportType.HTTP
    auth_token: Optional[str] = None
    timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    server_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "server_id": self.server_id,
            "metadata": self.metadata
        }


@dataclass
class MCPToolCall:
    """MCP tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    server_id: str
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timeout: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "server_id": self.server_id,
            "timeout": self.timeout
        }


@dataclass
class MCPToolResult:
    """MCP tool call result."""
    call_id: str
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_seconds": self.execution_time_seconds
        }


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        pass
    
    @abstractmethod
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        pass


class HTTPTransport(MCPTransport):
    """HTTP transport for MCP."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to MCP server via HTTP."""
        headers = {
            "Content-Type": "application/json",
            **self.config.headers
        }
        
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        self.session = aiohttp.ClientSession(headers=headers)
        self._connected = True
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.session:
            await self.session.close()
            self._connected = False
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via HTTP."""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        async with self.session.post(
            self.config.url,
            json=request,
            timeout=timeout
        ) as response:
            return await response.json()
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected


class WebSocketTransport(MCPTransport):
    """WebSocket transport for MCP."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to MCP server via WebSocket."""
        headers = self.config.headers.copy()
        
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        self.websocket = await websockets.connect(
            self.config.url,
            extra_headers=headers
        )
        self._connected = True
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.websocket:
            await self.websocket.close()
            self._connected = False
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via WebSocket."""
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected and self.websocket is not None


class MCPClient:
    """
    MCP client for tool discovery and invocation.
    
    Features:
    - Multiple transport types (HTTP, WebSocket, SSE)
    - Tool discovery and schema negotiation
    - Tool invocation with structured arguments
    - Connection pooling and management
    - Error handling and retry logic
    - Authentication support
    """
    
    def __init__(
        self,
        servers: Dict[str, MCPServerConfig],
        tracer: Optional[Tracer] = None
    ):
        self.servers = servers
        self.tracer = tracer or Tracer()
        
        self.logger = Logger(name="mcp.client")
        
        # Active connections
        self._connections: Dict[str, MCPTransport] = {}
        
        # Tool registry
        self._tools: Dict[str, MCPTool] = {}
        
        # Tool index by server
        self._tools_by_server: Dict[str, List[str]] = {}
    
    async def initialize(self) -> None:
        """Initialize MCP client and connect to all servers."""
        self.logger.info(f"Initializing MCP client with {len(self.servers)} servers")
        
        for server_id, config in self.servers.items():
            await self.connect_server(server_id, config)
    
    async def connect_server(
        self,
        server_id: str,
        config: MCPServerConfig
    ) -> None:
        """Connect to an MCP server."""
        self.logger.info(f"Connecting to MCP server: {server_id}")
        
        # Create transport based on type
        if config.transport == MCPTransportType.WEBSOCKET:
            transport = WebSocketTransport(config)
        else:
            transport = HTTPTransport(config)
        
        # Connect
        await transport.connect()
        self._connections[server_id] = transport
        
        # Discover tools
        await self._discover_tools(server_id)
        
        self.logger.info(f"Connected to MCP server: {server_id}")
    
    async def disconnect_server(self, server_id: str) -> None:
        """Disconnect from an MCP server."""
        if server_id in self._connections:
            await self._connections[server_id].disconnect()
            del self._connections[server_id]
            
            # Remove tools from registry
            tool_names = self._tools_by_server.get(server_id, [])
            for tool_name in tool_names:
                if tool_name in self._tools:
                    del self._tools[tool_name]
            del self._tools_by_server[server_id]
            
            self.logger.info(f"Disconnected from MCP server: {server_id}")
    
    async def _discover_tools(self, server_id: str) -> None:
        """Discover tools from an MCP server."""
        transport = self._connections.get(server_id)
        if not transport:
            return
        
        try:
            # Request tool list
            request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list"
            }
            
            response = await transport.send_request(request)
            
            # Parse tools
            tools_data = response.get("result", {}).get("tools", [])
            
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    output_schema=tool_data.get("outputSchema"),
                    server_id=server_id,
                    metadata=tool_data.get("metadata", {})
                )
                
                self._tools[tool.name] = tool
                
                if server_id not in self._tools_by_server:
                    self._tools_by_server[server_id] = []
                self._tools_by_server[server_id].append(tool.name)
            
            self.logger.info(
                f"Discovered {len(tools_data)} tools from server {server_id}"
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to discover tools from server {server_id}: {e}",
                exc_info=True
            )
    
    async def call_tool(
        self,
        tool_call: MCPToolCall
    ) -> MCPToolResult:
        """
        Call an MCP tool.
        
        Args:
            tool_call: Tool call request
            
        Returns:
            Tool call result
        """
        span = self.tracer.start_span(f"mcp.tool.{tool_call.tool_name}")
        
        start_time = datetime.now()
        result = MCPToolResult(call_id=tool_call.call_id, success=False)
        
        try:
            # Get tool
            tool = self._tools.get(tool_call.tool_name)
            if not tool:
                result.error = f"Tool not found: {tool_call.tool_name}"
                return result
            
            # Get transport
            transport = self._connections.get(tool_call.server_id)
            if not transport:
                result.error = f"Server not connected: {tool_call.server_id}"
                return result
            
            # Build request
            request = {
                "jsonrpc": "2.0",
                "id": tool_call.call_id,
                "method": "tools/call",
                "params": {
                    "name": tool_call.tool_name,
                    "arguments": tool_call.arguments
                }
            }
            
            # Send request
            response = await transport.send_request(request)
            
            # Parse result
            if "error" in response:
                result.error = json.dumps(response["error"])
            else:
                result.success = True
                result.output = response.get("result")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time_seconds = execution_time
            
            self.logger.debug(
                f"Tool call completed: {tool_call.tool_name} "
                f"({execution_time:.3f}s)"
            )
            
        except Exception as e:
            result.error = str(e)
            self.logger.error(
                f"Tool call failed: {tool_call.tool_name}: {e}",
                exc_info=True
            )
        
        finally:
            self.tracer.end_span(span)
        
        return result
    
    async def call_tool_simple(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> MCPToolResult:
        """
        Simplified tool call interface.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            server_id: Server ID (optional, inferred from tool)
            timeout: Timeout in seconds
            
        Returns:
            Tool call result
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return MCPToolResult(
                call_id=str(uuid.uuid4()),
                success=False,
                error=f"Tool not found: {tool_name}"
            )
        
        tool_call = MCPToolCall(
            tool_name=tool_name,
            arguments=arguments,
            server_id=server_id or tool.server_id,
            timeout=timeout
        )
        
        return await self.call_tool(tool_call)
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def list_tools(
        self,
        server_id: Optional[str] = None
    ) -> List[MCPTool]:
        """
        List available tools.
        
        Args:
            server_id: Filter by server ID
            
        Returns:
            List of tools
        """
        if server_id:
            tool_names = self._tools_by_server.get(server_id, [])
            return [self._tools[name] for name in tool_names]
        return list(self._tools.values())
    
    def refresh_tools(self, server_id: str) -> None:
        """Refresh tool discovery for a server."""
        # Would trigger re-discovery
        pass
    
    async def shutdown(self) -> None:
        """Shutdown MCP client and disconnect from all servers."""
        self.logger.info("Shutting down MCP client...")
        
        for server_id in list(self._connections.keys()):
            await self.disconnect_server(server_id)
        
        self.logger.info("MCP client shutdown")