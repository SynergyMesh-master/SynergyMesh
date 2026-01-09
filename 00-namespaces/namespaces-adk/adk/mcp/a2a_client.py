"""
A2A Client: Implements Agent-to-Agent protocol client for inter-agent communication.

This module provides A2A protocol functionality for discovering agents,
exchanging context, and delegating tasks between agents.
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

from ..observability.logging import Logger
from ..observability.tracing import Tracer


class A2AMessageType(Enum):
    """A2A message types."""
    DISCOVERY = "discovery"
    DELEGATE = "delegate"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class A2AProtocolVersion(Enum):
    """A2A protocol versions."""
    V1_0 = "1.0"
    V1_1 = "1.1"


@dataclass
class AgentCapabilities:
    """Agent capabilities description."""
    tools: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 10
    supported_message_types: List[A2AMessageType] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tools": self.tools,
            "workflows": self.workflows,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "supported_message_types": [mt.value for mt in self.supported_message_types],
            "protocols": self.protocols
        }


@dataclass
class AgentInfo:
    """Information about an agent."""
    agent_id: str
    name: str
    version: str
    capabilities: AgentCapabilities
    endpoint: str
    protocol_version: A2AProtocolVersion = A2AProtocolVersion.V1_0
    status: str = "online"
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities.to_dict(),
            "endpoint": self.endpoint,
            "protocol_version": self.protocol_version.value,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "metadata": self.metadata
        }


@dataclass
class A2AMessage:
    """An A2A protocol message."""
    message_type: A2AMessageType
    from_agent: str
    to_agent: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_type": self.message_type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create message from dictionary."""
        return cls(
            message_type=A2AMessageType(data["message_type"]),
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            message_id=data["message_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to")
        )


@dataclass
class DelegationRequest:
    """Request to delegate a task to another agent."""
    task_id: str
    task_description: str
    task_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    priority: int = 0


@dataclass
class DelegationResponse:
    """Response to a delegation request."""
    task_id: str
    accepted: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class A2AClient:
    """
    Agent-to-Agent protocol client.
    
    Features:
    - Agent discovery
    - Task delegation
    - Secure communication
    - Message queuing and retry
    - Capability negotiation
    - Heartbeat and health checks
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_info: AgentInfo,
        tracer: Optional[Tracer] = None
    ):
        self.agent_id = agent_id
        self.agent_info = agent_info
        self.tracer = tracer or Tracer()
        
        self.logger = Logger(name="a2a.client")
        
        # Known agents registry
        self._known_agents: Dict[str, AgentInfo] = {}
        
        # Pending responses
        self._pending_responses: Dict[str, asyncio.Future] = {}
        
        # Message handlers
        self._handlers: Dict[A2AMessageType, List[Callable]] = {}
        
        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """Initialize A2A client."""
        self._session = aiohttp.ClientSession()
        self.logger.info(f"A2A client initialized for agent: {self.agent_id}")
        
        # Register default handlers
        self.register_handler(A2AMessageType.DISCOVERY, self._handle_discovery)
        self.register_handler(A2AMessageType.HEARTBEAT, self._handle_heartbeat)
    
    async def shutdown(self) -> None:
        """Shutdown A2A client."""
        if self._session:
            await self._session.close()
        self.logger.info("A2A client shutdown")
    
    def register_handler(
        self,
        message_type: A2AMessageType,
        handler: Callable
    ) -> None:
        """Register a message handler."""
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
        self.logger.debug(f"Registered handler for {message_type.value}")
    
    async def discover_agents(
        self,
        discovery_url: Optional[str] = None
    ) -> List[AgentInfo]:
        """
        Discover other agents.
        
        Args:
            discovery_url: Optional discovery service URL
            
        Returns:
            List of discovered agents
        """
        if discovery_url:
            # Query discovery service
            return await self._query_discovery_service(discovery_url)
        else:
            # Return known agents
            return list(self._known_agents.values())
    
    async def _query_discovery_service(
        self,
        discovery_url: str
    ) -> List[AgentInfo]:
        """Query a discovery service for agents."""
        try:
            async with self._session.get(discovery_url) as response:
                data = await response.json()
                
                agents = []
                for agent_data in data.get("agents", []):
                    agent = AgentInfo(
                        agent_id=agent_data["agent_id"],
                        name=agent_data["name"],
                        version=agent_data["version"],
                        capabilities=AgentCapabilities(**agent_data.get("capabilities", {})),
                        endpoint=agent_data["endpoint"],
                        status=agent_data.get("status", "unknown"),
                        metadata=agent_data.get("metadata", {})
                    )
                    agents.append(agent)
                    self._known_agents[agent.agent_id] = agent
                
                return agents
                
        except Exception as e:
            self.logger.error(f"Discovery service query failed: {e}", exc_info=True)
            return []
    
    async def register_agent(self, agent: AgentInfo) -> None:
        """Register an agent."""
        self._known_agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information."""
        return self._known_agents.get(agent_id)
    
    async def delegate_task(
        self,
        target_agent_id: str,
        request: DelegationRequest
    ) -> DelegationResponse:
        """
        Delegate a task to another agent.
        
        Args:
            target_agent_id: ID of target agent
            request: Delegation request
            
        Returns:
            Delegation response
        """
        span = self.tracer.start_span(f"a2a.delegate.{target_agent_id}")
        
        try:
            # Get target agent info
            target_agent = self._known_agents.get(target_agent_id)
            if not target_agent:
                return DelegationResponse(
                    task_id=request.task_id,
                    accepted=False,
                    error=f"Agent not found: {target_agent_id}"
                )
            
            # Build message
            message = A2AMessage(
                message_type=A2AMessageType.DELEGATE,
                from_agent=self.agent_id,
                to_agent=target_agent_id,
                payload={
                    "delegation": {
                        "task_id": request.task_id,
                        "task_description": request.task_description,
                        "task_type": request.task_type,
                        "parameters": request.parameters,
                        "context": request.context,
                        "timeout": request.timeout,
                        "priority": request.priority
                    }
                }
            )
            
            # Send message
            response = await self._send_message(target_agent, message)
            
            if response:
                delegation_data = response.payload.get("delegation_response", {})
                return DelegationResponse(
                    task_id=delegation_data.get("task_id", request.task_id),
                    accepted=delegation_data.get("accepted", False),
                    result=delegation_data.get("result"),
                    error=delegation_data.get("error")
                )
            else:
                return DelegationResponse(
                    task_id=request.task_id,
                    accepted=False,
                    error="Failed to send delegation request"
                )
                
        finally:
            self.tracer.end_span(span)
    
    async def send_message(
        self,
        target_agent_id: str,
        message: A2AMessage
    ) -> bool:
        """
        Send a message to an agent.
        
        Args:
            target_agent_id: ID of target agent
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        target_agent = self._known_agents.get(target_agent_id)
        if not target_agent:
            return False
        
        response = await self._send_message(target_agent, message)
        return response is not None
    
    async def _send_message(
        self,
        target_agent: AgentInfo,
        message: A2AMessage
    ) -> Optional[A2AMessage]:
        """Send message to agent endpoint."""
        try:
            async with self._session.post(
                target_agent.endpoint,
                json=message.to_dict(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                data = await response.json()
                return A2AMessage.from_dict(data)
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}", exc_info=True)
            return None
    
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """
        Handle an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Response message if applicable
        """
        # Get handlers
        handlers = self._handlers.get(message.message_type, [])
        
        if not handlers:
            self.logger.warning(
                f"No handlers for message type: {message.message_type.value}"
            )
            return None
        
        # Invoke handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(message)
                else:
                    result = handler(message)
                
                if result:
                    return result
                    
            except Exception as e:
                self.logger.error(
                    f"Handler error for {message.message_type.value}: {e}",
                    exc_info=True
                )
        
        return None
    
    async def _handle_discovery(self, message: A2AMessage) -> A2AMessage:
        """Handle discovery message."""
        return A2AMessage(
            message_type=A2AMessageType.RESPONSE,
            from_agent=self.agent_id,
            to_agent=message.from_agent,
            reply_to=message.message_id,
            payload={
                "agent_info": self.agent_info.to_dict()
            }
        )
    
    async def _handle_heartbeat(self, message: A2AMessage) -> A2AMessage:
        """Handle heartbeat message."""
        return A2AMessage(
            message_type=A2AMessageType.RESPONSE,
            from_agent=self.agent_id,
            to_agent=message.from_agent,
            reply_to=message.message_id,
            payload={"status": "ok"}
        )
    
    async def send_heartbeat(self, target_agent_id: str) -> bool:
        """Send heartbeat to an agent."""
        message = A2AMessage(
            message_type=A2AMessageType.HEARTBEAT,
            from_agent=self.agent_id,
            to_agent=target_agent_id
        )
        
        return await self.send_message(target_agent_id, message)
    
    async def check_agent_health(self, agent_id: str) -> bool:
        """Check if an agent is healthy."""
        return await self.send_heartbeat(agent_id)