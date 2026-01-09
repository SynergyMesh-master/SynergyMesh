"""
Agent Runtime: Main lifecycle manager for agent execution.

This module provides the entry point and main lifecycle management for
agent execution, including initialization, request handling, and shutdown.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path

from ..observability.logging import Logger
from ..observability.tracing import Tracer
from ..observability.metrics import MetricsCollector
from .workflow_orchestrator import WorkflowOrchestrator
from .memory_manager import MemoryManager
from .context_manager import ContextManager
from .event_bus import EventBus
from .error_handling import ErrorHandler
from .plugin_manager import PluginManager
from .sandbox import Sandbox
from ..governance.audit_trail import AuditTrail
from ..security.auth import Authenticator


class AgentState(Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for the agent runtime."""
    name: str
    version: str = "1.0.0"
    environment: str = "development"
    config_path: Optional[str] = None
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_audit: bool = True
    max_concurrent_workflows: int = 10
    sandbox_enabled: bool = True
    plugin_directories: List[str] = field(default_factory=list)
    memory_backend: str = "redis"
    
    def __post_init__(self):
        if self.config_path:
            self._load_from_file()
    
    def _load_from_file(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception as e:
            logging.warning(f"Failed to load config from {self.config_path}: {e}")


class AgentRuntime:
    """
    Main agent runtime that orchestrates all components.
    
    The AgentRuntime is responsible for:
    - Bootstrapping the agent environment
    - Managing agent lifecycle (init, run, shutdown)
    - Handling incoming requests
    - Coordinating workflows, memory, and tool invocations
    - Integrating observability and governance hooks
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.INITIALIZING
        
        # Initialize core components
        self.logger = Logger(name=f"agent.{config.name}")
        self.tracer = Tracer() if config.enable_tracing else None
        self.metrics = MetricsCollector() if config.enable_metrics else None
        self.audit_trail = AuditTrail() if config.enable_audit else None
        
        # Initialize event bus
        self.event_bus = EventBus()
        
        # Initialize error handler
        self.error_handler = ErrorHandler(self.event_bus)
        
        # Initialize authentication
        self.authenticator = Authenticator(self.event_bus)
        
        # Initialize sandbox
        self.sandbox = Sandbox() if config.sandbox_enabled else None
        
        # Initialize context manager
        self.context_manager = ContextManager(self.event_bus)
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            backend=config.memory_backend,
            event_bus=self.event_bus
        )
        
        # Initialize workflow orchestrator
        self.workflow_orchestrator = WorkflowOrchestrator(
            event_bus=self.event_bus,
            memory_manager=self.memory_manager,
            context_manager=self.context_manager,
            sandbox=self.sandbox
        )
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(
            directories=config.plugin_directories,
            event_bus=self.event_bus
        )
        
        # Request handlers registry
        self.request_handlers: Dict[str, Callable] = {}
        
        # Initialize metrics
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize runtime metrics."""
        if self.metrics:
            self.metrics.register_counter(
                "agent_requests_total",
                "Total number of agent requests"
            )
            self.metrics.register_histogram(
                "agent_request_duration_seconds",
                "Duration of agent requests in seconds"
            )
            self.metrics.register_gauge(
                "agent_state",
                "Current agent state"
            )
            self.metrics.register_gauge(
                "active_workflows",
                "Number of active workflows"
            )
    
    async def initialize(self) -> None:
        """Initialize the agent runtime and all components."""
        with self.logger.context("initialization"):
            self.logger.info(f"Initializing AgentRuntime: {self.config.name}")
            
            try:
                # Initialize plugin manager first to load plugins
                await self.plugin_manager.initialize()
                self.logger.info("Plugin manager initialized")
                
                # Initialize memory manager
                await self.memory_manager.initialize()
                self.logger.info("Memory manager initialized")
                
                # Initialize workflow orchestrator
                await self.workflow_orchestrator.initialize()
                self.logger.info("Workflow orchestrator initialized")
                
                # Register default request handlers
                self._register_default_handlers()
                
                # Update state
                self.state = AgentState.READY
                self._update_state_metric()
                
                self.logger.info("AgentRuntime initialization complete")
                
            except Exception as e:
                self.state = AgentState.ERROR
                self.logger.error(f"Initialization failed: {e}", exc_info=True)
                raise
    
    def _register_default_handlers(self) -> None:
        """Register default request handlers."""
        self.register_handler("workflow.execute", self._handle_workflow_execute)
        self.register_handler("agent.status", self._handle_agent_status)
        self.register_handler("memory.query", self._handle_memory_query)
        self.register_handler("agent.shutdown", self._handle_shutdown)
    
    def register_handler(self, name: str, handler: Callable) -> None:
        """Register a request handler."""
        self.request_handlers[name] = handler
        self.logger.debug(f"Registered handler: {name}")
    
    def _update_state_metric(self) -> None:
        """Update the agent state metric."""
        if self.metrics:
            self.metrics.set_gauge("agent_state", self.state.value)
    
    async def handle_request(
        self,
        request_type: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an incoming request.
        
        Args:
            request_type: Type of request (e.g., "workflow.execute")
            payload: Request payload
            context: Request context (user, session, etc.)
            
        Returns:
            Response payload
        """
        if self.state not in [AgentState.READY, AgentState.RUNNING]:
            return {
                "success": False,
                "error": f"Agent not ready, current state: {self.state.value}"
            }
        
        with self.logger.context(f"request.{request_type}"):
            # Increment request counter
            if self.metrics:
                self.metrics.increment_counter("agent_requests_total")
            
            # Start tracing span
            span = None
            if self.tracer:
                span = self.tracer.start_span(f"request.{request_type}")
            
            try:
                # Get handler
                handler = self.request_handlers.get(request_type)
                if not handler:
                    raise ValueError(f"Unknown request type: {request_type}")
                
                # Execute handler
                result = await handler(payload, context or {})
                
                # Update active workflows metric
                if self.metrics and request_type == "workflow.execute":
                    active = self.workflow_orchestrator.get_active_workflow_count()
                    self.metrics.set_gauge("active_workflows", active)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Request failed: {e}", exc_info=True)
                
                # Emit error event
                await self.event_bus.publish(
                    "error.occurred",
                    {
                        "request_type": request_type,
                        "error": str(e),
                        "context": context
                    }
                )
                
                return {
                    "success": False,
                    "error": str(e)
                }
                
            finally:
                # End tracing span
                if span:
                    self.tracer.end_span(span)
    
    async def _handle_workflow_execute(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle workflow execution requests."""
        workflow_id = payload.get("workflow_id")
        workflow_def = payload.get("workflow_definition")
        inputs = payload.get("inputs", {})
        
        if not workflow_id and not workflow_def:
            return {"success": False, "error": "workflow_id or workflow_definition required"}
        
        try:
            result = await self.workflow_orchestrator.execute_workflow(
                workflow_id=workflow_id,
                workflow_definition=workflow_def,
                inputs=inputs,
                context=context
            )
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _handle_agent_status(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle agent status requests."""
        return {
            "success": True,
            "status": {
                "state": self.state.value,
                "name": self.config.name,
                "version": self.config.version,
                "active_workflows": self.workflow_orchestrator.get_active_workflow_count(),
                "plugins_loaded": len(self.plugin_manager.get_loaded_plugins()),
                "memory_backend": self.config.memory_backend
            }
        }
    
    async def _handle_memory_query(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle memory query requests."""
        query = payload.get("query")
        session_id = context.get("session_id")
        
        if not query:
            return {"success": False, "error": "query required"}
        
        try:
            results = await self.memory_manager.retrieve(
                query=query,
                session_id=session_id,
                limit=payload.get("limit", 10)
            )
            return {"success": True, "results": results}
        except Exception as e:
            self.logger.error(f"Memory query failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _handle_shutdown(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle shutdown requests."""
        await self.shutdown()
        return {"success": True, "message": "Agent shutdown complete"}
    
    async def run(self) -> None:
        """Run the agent runtime (main event loop)."""
        self.state = AgentState.RUNNING
        self._update_state_metric()
        self.logger.info("AgentRuntime started")
        
        try:
            # Main event loop
            while self.state == AgentState.RUNNING:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("AgentRuntime run cancelled")
        except Exception as e:
            self.logger.error(f"AgentRuntime error: {e}", exc_info=True)
            self.state = AgentState.ERROR
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Shutdown the agent runtime gracefully."""
        if self.state in [AgentState.SHUTTING_DOWN, AgentState.TERMINATED]:
            return
        
        self.state = AgentState.SHUTTING_DOWN
        self._update_state_metric()
        self.logger.info("Shutting down AgentRuntime...")
        
        try:
            # Shutdown workflow orchestrator
            await self.workflow_orchestrator.shutdown()
            self.logger.info("Workflow orchestrator shutdown")
            
            # Shutdown memory manager
            await self.memory_manager.shutdown()
            self.logger.info("Memory manager shutdown")
            
            # Shutdown plugin manager
            await self.plugin_manager.shutdown()
            self.logger.info("Plugin manager shutdown")
            
            # Close event bus
            await self.event_bus.shutdown()
            self.logger.info("Event bus shutdown")
            
            self.state = AgentState.TERMINATED
            self.logger.info("AgentRuntime shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}", exc_info=True)
            self.state = AgentState.ERROR
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state
    
    def get_config(self) -> AgentConfig:
        """Get agent configuration."""
        return self.config


def create_runtime(config_path: Optional[str] = None) -> AgentRuntime:
    """
    Factory function to create an AgentRuntime instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Initialized AgentRuntime instance
    """
    if config_path:
        config = AgentConfig(
            name="default_agent",
            config_path=config_path
        )
    else:
        config = AgentConfig(name="default_agent")
    
    return AgentRuntime(config)