"""
Tool Router: Routes tool invocation requests to appropriate endpoints.

This module manages tool routing, fallback, and policy enforcement
for tool invocations across multiple MCP servers and local tools.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .mcp_client import MCPClient, MCPTool, MCPToolCall, MCPToolResult
from .mcp_security import MCPSecurity
from ..observability.logging import Logger
from ..observability.tracing import Tracer


class RoutingStrategy(Enum):
    """Tool routing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PRIORITY = "priority"
    AFFINITY = "affinity"


@dataclass
class ToolEndpoint:
    """A tool endpoint."""
    tool_name: str
    server_id: str
    priority: int = 0
    enabled: bool = True
    tags: Set[str] = field(default_factory=set)
    load: int = 0
    last_used: Optional[datetime] = None
    
    def __hash__(self):
        return hash((self.tool_name, self.server_id))


@dataclass
class RoutingPolicy:
    """Routing policy configuration."""
    strategy: RoutingStrategy = RoutingStrategy.PRIORITY
    fallback_enabled: bool = True
    max_retries: int = 3
    timeout: int = 30
    require_permission: bool = True
    allowed_tags: Set[str] = field(default_factory=set)


class ToolRouter:
    """
    Routes tool invocation requests to appropriate endpoints.
    
    Features:
    - Dynamic tool registration and deregistration
    - Multiple routing strategies
    - Fallback and retry logic
    - Permission enforcement
    - Load balancing
    - Health checking
    """
    
    def __init__(
        self,
        mcp_client: MCPClient,
        security: Optional[MCPSecurity] = None,
        tracer: Optional[Tracer] = None
    ):
        self.mcp_client = mcp_client
        self.security = security
        self.tracer = tracer or Tracer()
        
        self.logger = Logger(name="tool.router")
        
        # Tool registry
        self._tool_endpoints: Dict[str, List[ToolEndpoint]] = {}
        
        # Routing policies
        self._policies: Dict[str, RoutingPolicy] = {}
        
        # Local tool handlers
        self._local_tools: Dict[str, Callable] = {}
        
        # Round-robin index
        self._round_robin_index: Dict[str, int] = {}
    
    def register_endpoint(
        self,
        tool_name: str,
        server_id: str,
        priority: int = 0,
        tags: Optional[Set[str]] = None,
        enabled: bool = True
    ) -> None:
        """
        Register a tool endpoint.
        
        Args:
            tool_name: Name of the tool
            server_id: Server ID
            priority: Priority level
            tags: Tags for filtering
            enabled: Whether endpoint is enabled
        """
        endpoint = ToolEndpoint(
            tool_name=tool_name,
            server_id=server_id,
            priority=priority,
            enabled=enabled,
            tags=tags or set()
        )
        
        if tool_name not in self._tool_endpoints:
            self._tool_endpoints[tool_name] = []
        
        self._tool_endpoints[tool_name].append(endpoint)
        
        # Sort by priority
        self._tool_endpoints[tool_name].sort(
            key=lambda e: e.priority,
            reverse=True
        )
        
        self.logger.debug(f"Registered endpoint: {tool_name}@{server_id}")
    
    def register_local_tool(
        self,
        tool_name: str,
        handler: Callable
    ) -> None:
        """
        Register a local tool handler.
        
        Args:
            tool_name: Name of the tool
            handler: Handler function
        """
        self._local_tools[tool_name] = handler
        self.logger.debug(f"Registered local tool: {tool_name}")
    
    def unregister_endpoint(
        self,
        tool_name: str,
        server_id: str
    ) -> bool:
        """
        Unregister a tool endpoint.
        
        Args:
            tool_name: Name of the tool
            server_id: Server ID
            
        Returns:
            True if unregistered, False if not found
        """
        if tool_name not in self._tool_endpoints:
            return False
        
        self._tool_endpoints[tool_name] = [
            e for e in self._tool_endpoints[tool_name]
            if not (e.tool_name == tool_name and e.server_id == server_id)
        ]
        
        self.logger.debug(f"Unregistered endpoint: {tool_name}@{server_id}")
        return True
    
    def set_policy(
        self,
        tool_name: str,
        policy: RoutingPolicy
    ) -> None:
        """
        Set routing policy for a tool.
        
        Args:
            tool_name: Name of the tool
            policy: Routing policy
        """
        self._policies[tool_name] = policy
        self.logger.debug(f"Set policy for {tool_name}: {policy.strategy.value}")
    
    def get_policy(self, tool_name: str) -> RoutingPolicy:
        """Get routing policy for a tool."""
        return self._policies.get(tool_name, RoutingPolicy())
    
    async def route_and_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        server_id: Optional[str] = None
    ) -> MCPToolResult:
        """
        Route and call a tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            context: Execution context
            server_id: Specific server ID (optional)
            
        Returns:
            Tool call result
        """
        span = self.tracer.start_span(f"router.{tool_name}")
        
        try:
            # Check for local tool
            if tool_name in self._local_tools:
                return await self._call_local_tool(
                    tool_name,
                    arguments,
                    context
                )
            
            # Get policy
            policy = self.get_policy(tool_name)
            
            # Check permission if required
            if policy.require_permission and self.security:
                if not await self.security.check_tool_permission(
                    tool_name,
                    context
                ):
                    return MCPToolResult(
                        call_id=str(uuid.uuid4()),
                        success=False,
                        error=f"Permission denied for tool: {tool_name}"
                    )
            
            # Select endpoint
            endpoint = self._select_endpoint(tool_name, server_id, policy)
            
            if not endpoint:
                return MCPToolResult(
                    call_id=str(uuid.uuid4()),
                    success=False,
                    error=f"No available endpoint for tool: {tool_name}"
                )
            
            # Call tool with retry
            return await self._call_tool_with_retry(
                endpoint,
                arguments,
                policy,
                context
            )
            
        finally:
            self.tracer.end_span(span)
    
    def _select_endpoint(
        self,
        tool_name: str,
        preferred_server_id: Optional[str],
        policy: RoutingPolicy
    ) -> Optional[ToolEndpoint]:
        """Select an endpoint based on routing strategy."""
        endpoints = self._tool_endpoints.get(tool_name, [])
        
        # Filter by enabled status
        endpoints = [e for e in endpoints if e.enabled]
        
        if not endpoints:
            return None
        
        # If specific server requested, use it
        if preferred_server_id:
            for endpoint in endpoints:
                if endpoint.server_id == preferred_server_id:
                    return endpoint
        
        # Apply routing strategy
        if policy.strategy == RoutingStrategy.PRIORITY:
            return endpoints[0]
        
        elif policy.strategy == RoutingStrategy.ROUND_ROBIN:
            if tool_name not in self._round_robin_index:
                self._round_robin_index[tool_name] = 0
            
            index = self._round_robin_index[tool_name] % len(endpoints)
            self._round_robin_index[tool_name] += 1
            return endpoints[index]
        
        elif policy.strategy == RoutingStrategy.LEAST_LOADED:
            return min(endpoints, key=lambda e: e.load)
        
        elif policy.strategy == RoutingStrategy.AFFINITY:
            # Would implement affinity logic
            return endpoints[0]
        
        return endpoints[0]
    
    async def _call_tool_with_retry(
        self,
        endpoint: ToolEndpoint,
        arguments: Dict[str, Any],
        policy: RoutingPolicy,
        context: Optional[Dict[str, Any]]
    ) -> MCPToolResult:
        """Call tool with retry logic."""
        last_error = None
        
        for attempt in range(policy.max_retries):
            try:
                # Update load
                endpoint.load += 1
                
                # Call tool
                tool_call = MCPToolCall(
                    tool_name=endpoint.tool_name,
                    arguments=arguments,
                    server_id=endpoint.server_id,
                    timeout=policy.timeout
                )
                
                result = await self.mcp_client.call_tool(tool_call)
                
                # Update endpoint stats
                endpoint.last_used = datetime.now()
                endpoint.load -= 1
                
                if result.success or not policy.fallback_enabled:
                    return result
                
                last_error = result.error
                
                # Try next endpoint
                endpoint.enabled = False
                next_endpoint = self._select_endpoint(
                    endpoint.tool_name,
                    None,
                    policy
                )
                
                if not next_endpoint:
                    break
                
                endpoint = next_endpoint
                
            except Exception as e:
                last_error = str(e)
                endpoint.load -= 1
        
        return MCPToolResult(
            call_id=str(uuid.uuid4()),
            success=False,
            error=last_error or "Tool call failed after all retries"
        )
    
    async def _call_local_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> MCPToolResult:
        """Call a local tool handler."""
        handler = self._local_tools.get(tool_name)
        if not handler:
            return MCPToolResult(
                call_id=str(uuid.uuid4()),
                success=False,
                error=f"Local tool not found: {tool_name}"
            )
        
        try:
            if asyncio.iscoroutinefunction(handler):
                output = await handler(arguments, context)
            else:
                output = handler(arguments, context)
            
            return MCPToolResult(
                call_id=str(uuid.uuid4()),
                success=True,
                output={"result": output}
            )
            
        except Exception as e:
            return MCPToolResult(
                call_id=str(uuid.uuid4()),
                success=False,
                error=str(e)
            )
    
    def list_endpoints(self, tool_name: Optional[str] = None) -> List[ToolEndpoint]:
        """List tool endpoints."""
        if tool_name:
            return self._tool_endpoints.get(tool_name, []).copy()
        
        endpoints = []
        for endpoint_list in self._tool_endpoints.values():
            endpoints.extend(endpoint_list)
        return endpoints
    
    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a tool."""
        endpoints = self._tool_endpoints.get(tool_name, [])
        
        return {
            "tool_name": tool_name,
            "endpoint_count": len(endpoints),
            "enabled_endpoints": sum(1 for e in endpoints if e.enabled),
            "total_load": sum(e.load for e in endpoints),
            "endpoints": [
                {
                    "server_id": e.server_id,
                    "enabled": e.enabled,
                    "load": e.load,
                    "priority": e.priority,
                    "last_used": e.last_used.isoformat() if e.last_used else None
                }
                for e in endpoints
            ]
        }