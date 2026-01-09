"""
Workflow Orchestrator: Manages multi-step, hierarchical, and parallel workflows.

This module implements orchestration logic for complex agent workflows,
supporting sequential, parallel, conditional, and human-in-the-loop patterns.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
import networkx as nx
from abc import ABC, abstractmethod

from .memory_manager import MemoryManager
from .context_manager import ContextManager
from .sandbox import Sandbox
from .event_bus import EventBus
from ..observability.logging import Logger
from ..observability.tracing import Tracer


class WorkflowState(Enum):
    """Workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class StepType(Enum):
    """Types of workflow steps."""
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    SUBWORKFLOW = "subworkflow"
    TOOL_CALL = "tool_call"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str
    name: str
    type: StepType
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    retry_policy: Optional[Dict[str, Any]] = None
    condition: Optional[str] = None  # For conditional steps
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class WorkflowDefinition:
    """Definition of a workflow."""
    id: str
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    start_step: str = ""
    version: str = "1.0.0"
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class WorkflowExecution:
    """Execution instance of a workflow."""
    workflow_id: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: WorkflowState = WorkflowState.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    current_step: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "state": self.state.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "context": self.context,
            "results": self.results,
            "errors": self.errors,
            "current_step": self.current_step
        }


class WorkflowOrchestrator:
    """
    Orchestrates workflow execution with support for:
    - Sequential and parallel steps
    - Conditional branching
    - Human-in-the-loop approvals
    - Error handling and retry
    - Subworkflow execution
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        memory_manager: MemoryManager,
        context_manager: ContextManager,
        sandbox: Optional[Sandbox] = None
    ):
        self.event_bus = event_bus
        self.memory_manager = memory_manager
        self.context_manager = context_manager
        self.sandbox = sandbox
        
        self.logger = Logger(name="workflow.orchestrator")
        self.tracer = Tracer()
        
        # Workflow registry
        self.workflows: Dict[str, WorkflowDefinition] = {}
        
        # Active executions
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # Step handlers
        self.step_handlers: Dict[StepType, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default step handlers."""
        self.step_handlers[StepType.TASK] = self._handle_task_step
        self.step_handlers[StepType.CONDITION] = self._handle_condition_step
        self.step_handlers[StepType.PARALLEL] = self._handle_parallel_step
        self.step_handlers[StepType.HUMAN_IN_THE_LOOP] = self._handle_human_step
        self.step_handlers[StepType.SUBWORKFLOW] = self._handle_subworkflow_step
        self.step_handlers[StepType.TOOL_CALL] = self._handle_tool_call_step
    
    async def initialize(self) -> None:
        """Initialize the workflow orchestrator."""
        self.logger.info("Workflow orchestrator initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the workflow orchestrator."""
        # Cancel all running executions
        for execution in self.executions.values():
            if execution.state == WorkflowState.RUNNING:
                execution.state = WorkflowState.CANCELLED
        
        self.logger.info("Workflow orchestrator shutdown")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow definition."""
        self.workflows[workflow.id] = workflow
        self.logger.info(f"Registered workflow: {workflow.id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all registered workflows."""
        return list(self.workflows.values())
    
    def get_active_workflow_count(self) -> int:
        """Get the number of active workflow executions."""
        return sum(
            1 for e in self.executions.values()
            if e.state == WorkflowState.RUNNING
        )
    
    async def execute_workflow(
        self,
        workflow_id: Optional[str] = None,
        workflow_definition: Optional[WorkflowDefinition] = None,
        inputs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of registered workflow
            workflow_definition: Direct workflow definition
            inputs: Input parameters for the workflow
            context: Execution context
            
        Returns:
            Workflow execution result
        """
        # Get workflow definition
        if workflow_definition:
            workflow = workflow_definition
        elif workflow_id:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
        else:
            raise ValueError("Either workflow_id or workflow_definition required")
        
        # Create execution instance
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            context={**(context or {}), **(inputs or {})}
        )
        
        # Store execution
        self.executions[execution.execution_id] = execution
        
        # Start tracing span
        span = self.tracer.start_span(f"workflow.{workflow.id}")
        
        try:
            # Update state
            execution.state = WorkflowState.RUNNING
            execution.started_at = datetime.now()
            
            # Emit workflow started event
            await self.event_bus.publish(
                "workflow.started",
                {
                    "workflow_id": workflow.id,
                    "execution_id": execution.execution_id,
                    "context": execution.context
                }
            )
            
            # Build execution graph
            graph = self._build_execution_graph(workflow)
            
            # Execute workflow steps
            await self._execute_workflow_graph(
                workflow,
                graph,
                execution
            )
            
            # Update state
            execution.state = WorkflowState.COMPLETED
            execution.completed_at = datetime.now()
            
            # Emit workflow completed event
            await self.event_bus.publish(
                "workflow.completed",
                {
                    "workflow_id": workflow.id,
                    "execution_id": execution.execution_id,
                    "results": execution.results,
                    "duration": (execution.completed_at - execution.started_at).total_seconds()
                }
            )
            
            return {
                "success": True,
                "execution_id": execution.execution_id,
                "results": execution.results
            }
            
        except Exception as e:
            execution.state = WorkflowState.FAILED
            execution.completed_at = datetime.now()
            execution.errors.append(str(e))
            
            self.logger.error(
                f"Workflow execution failed: {e}",
                exc_info=True,
                extra={"execution_id": execution.execution_id}
            )
            
            # Emit workflow failed event
            await self.event_bus.publish(
                "workflow.failed",
                {
                    "workflow_id": workflow.id,
                    "execution_id": execution.execution_id,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "execution_id": execution.execution_id,
                "error": str(e),
                "results": execution.results
            }
            
        finally:
            self.tracer.end_span(span)
    
    def _build_execution_graph(self, workflow: WorkflowDefinition) -> nx.DiGraph:
        """Build a directed acyclic graph from workflow steps."""
        graph = nx.DiGraph()
        
        # Add all steps as nodes
        for step in workflow.steps:
            graph.add_node(step.id, step=step)
        
        # Add edges for dependencies
        for step in workflow.steps:
            for dep in step.dependencies:
                graph.add_edge(dep, step.id)
        
        return graph
    
    async def _execute_workflow_graph(
        self,
        workflow: WorkflowDefinition,
        graph: nx.DiGraph,
        execution: WorkflowExecution
    ) -> None:
        """Execute workflow using topological sort."""
        # Get start step
        start_step_id = workflow.start_step or workflow.steps[0].id if workflow.steps else None
        
        if not start_step_id:
            raise ValueError("No start step defined")
        
        # Execute steps in topological order
        for step_id in nx.topological_sort(graph):
            step_data = graph.nodes[step_id]
            step = step_data["step"]
            
            execution.current_step = step_id
            
            # Check if step has a condition
            if step.condition and not self._evaluate_condition(
                step.condition,
                execution.context
            ):
                self.logger.info(f"Skipping step {step_id}: condition not met")
                continue
            
            # Get step handler
            handler = self.step_handlers.get(step.type)
            if not handler:
                raise ValueError(f"No handler for step type: {step.type}")
            
            # Execute step
            result = await handler(step, execution)
            
            # Store result
            execution.results[step_id] = result
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context."""
        # Simple evaluation - can be extended with proper expression parser
        try:
            # For now, support simple comparisons
            # In production, use a safe expression evaluator
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {e}")
            return False
    
    async def _handle_task_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Any:
        """Handle a task step."""
        self.logger.info(f"Executing task step: {step.id}")
        
        # Get task handler from parameters
        task_name = step.parameters.get("task")
        if not task_name:
            raise ValueError("Task name required")
        
        # Execute task (would be delegated to appropriate handler)
        # For now, simulate task execution
        await asyncio.sleep(0.1)
        
        return {"status": "completed", "result": f"Task {task_name} executed"}
    
    async def _handle_condition_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Handle a condition step."""
        self.logger.info(f"Evaluating condition step: {step.id}")
        
        condition = step.parameters.get("condition")
        true_branch = step.parameters.get("true_branch")
        false_branch = step.parameters.get("false_branch")
        
        result = self._evaluate_condition(condition, execution.context)
        
        return {
            "condition_result": result,
            "next_step": true_branch if result else false_branch
        }
    
    async def _handle_parallel_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> List[Any]:
        """Handle a parallel step."""
        self.logger.info(f"Executing parallel step: {step.id}")
        
        tasks = step.parameters.get("tasks", [])
        
        # Execute tasks in parallel
        results = await asyncio.gather(
            *[self._execute_subtask(task, execution) for task in tasks],
            return_exceptions=True
        )
        
        return results
    
    async def _execute_subtask(
        self,
        task: Dict[str, Any],
        execution: WorkflowExecution
    ) -> Any:
        """Execute a subtask within a parallel step."""
        # Simulate subtask execution
        await asyncio.sleep(0.1)
        return {"status": "completed"}
    
    async def _handle_human_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Handle a human-in-the-loop step."""
        self.logger.info(f"Executing human-in-the-loop step: {step.id}")
        
        # Update execution state
        execution.state = WorkflowState.WAITING_FOR_APPROVAL
        
        # Emit approval request event
        await self.event_bus.publish(
            "workflow.approval_required",
            {
                "workflow_id": execution.workflow_id,
                "execution_id": execution.execution_id,
                "step_id": step.id,
                "parameters": step.parameters
            }
        )
        
        # Wait for approval (would be implemented via event listener)
        # For now, simulate approval
        await asyncio.sleep(0.5)
        
        # Update execution state
        execution.state = WorkflowState.RUNNING
        
        return {"status": "approved", "approval": "simulated"}
    
    async def _handle_subworkflow_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Handle a subworkflow step."""
        self.logger.info(f"Executing subworkflow step: {step.id}")
        
        subworkflow_id = step.parameters.get("subworkflow_id")
        
        if not subworkflow_id:
            raise ValueError("Subworkflow ID required")
        
        # Execute subworkflow
        result = await self.execute_workflow(
            workflow_id=subworkflow_id,
            inputs=step.parameters.get("inputs", {}),
            context=execution.context
        )
        
        return result
    
    async def _handle_tool_call_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Handle a tool call step."""
        self.logger.info(f"Executing tool call step: {step.id}")
        
        tool_name = step.parameters.get("tool")
        tool_args = step.parameters.get("arguments", {})
        
        # Tool invocation would be delegated to MCP client
        # For now, simulate tool call
        await asyncio.sleep(0.1)
        
        return {
            "status": "success",
            "result": f"Tool {tool_name} executed with args {tool_args}"
        }
    
    async def approve_step(
        self,
        execution_id: str,
        step_id: str,
        approved: bool
    ) -> Dict[str, Any]:
        """
        Approve or reject a human-in-the-loop step.
        
        Args:
            execution_id: Workflow execution ID
            step_id: Step ID to approve
            approved: Whether to approve the step
            
        Returns:
            Approval result
        """
        execution = self.executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        # Update execution state
        execution.state = WorkflowState.RUNNING
        
        # Store approval result
        execution.results[step_id] = {
            "status": "approved" if approved else "rejected",
            "approved": approved
        }
        
        return {"success": True, "execution_id": execution_id}
    
    async def cancel_workflow(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a running workflow.
        
        Args:
            execution_id: Workflow execution ID
            
        Returns:
            Cancellation result
        """
        execution = self.executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")
        
        if execution.state != WorkflowState.RUNNING:
            return {
                "success": False,
                "error": f"Cannot cancel workflow in state: {execution.state.value}"
            }
        
        execution.state = WorkflowState.CANCELLED
        
        # Emit cancellation event
        await self.event_bus.publish(
            "workflow.cancelled",
            {
                "workflow_id": execution.workflow_id,
                "execution_id": execution_id
            }
        )
        
        return {"success": True, "execution_id": execution_id}
    
    def get_execution(
        self,
        execution_id: str
    ) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        return self.executions.get(execution_id)
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        state: Optional[WorkflowState] = None
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters."""
        executions = list(self.executions.values())
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        if state:
            executions = [e for e in executions if e.state == state]
        
        return executions