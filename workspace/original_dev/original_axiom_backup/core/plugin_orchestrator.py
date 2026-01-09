"""
AXIOM Plugin Execution Orchestrator
Intelligent plugin coordination with dependency resolution and error handling.
"""

import networkx as nx
import time
import logging
import threading
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from enum import Enum
import json
from pathlib import Path

from .plugin_manager import plugin_manager, PluginExecutionResult, PluginValidationError

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Plugin execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    SMART = "smart"


class ErrorHandlingStrategy(Enum):
    """Error handling strategies"""
    STOP_ON_FAILURE = "stop_on_failure"
    CONTINUE_ON_FAILURE = "continue_on_failure"
    RETRY_ON_FAILURE = "retry_on_failure"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class ExecutionContext:
    """Context for plugin execution"""
    workflow_id: str
    execution_mode: ExecutionMode
    error_handling: ErrorHandlingStrategy
    retry_policy: Dict[str, Any]
    timeout: Optional[float] = None
    global_context: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class WorkflowDefinition:
    """Definition of a plugin workflow"""
    name: str
    description: str
    plugins: List[str]
    parallel_execution: bool = False
    error_handling: str = "STOP_ON_FAILURE"
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginOrchestrator:
    """
    Advanced plugin orchestrator with intelligent dependency resolution,
    parallel execution, and sophisticated error handling.
    """
    
    def __init__(self, max_workers: int = 16):
        self.execution_graph = nx.DiGraph()
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.execution_history: List[Dict[str, Any]] = []
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
    def load_workflow(self, workflow_config: Dict[str, Any]) -> bool:
        """
        Load a workflow definition.
        
        Args:
            workflow_config: Workflow configuration
            
        Returns:
            bool: True if workflow loaded successfully
        """
        try:
            workflow = WorkflowDefinition(
                name=workflow_config['name'],
                description=workflow_config['description'],
                plugins=workflow_config['plugins'],
                parallel_execution=workflow_config.get('parallel_execution', False),
                error_handling=workflow_config.get('error_handling', 'STOP_ON_FAILURE'),
                retry_policy=workflow_config.get('retry_policy', {}),
                metadata=workflow_config.get('metadata', {})
            )
            
            self.workflows[workflow.name] = workflow
            
            # Build execution graph for this workflow
            self._build_workflow_graph(workflow)
            
            logger.info(f"Loaded workflow: {workflow.name} with {len(workflow.plugins)} plugins")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            return False
            
    def execute_workflow(self, workflow_name: str, 
                        context: Dict[str, Any],
                        execution_mode: Optional[ExecutionMode] = None) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow_name: Name of workflow to execute
            context: Execution context
            execution_mode: Override execution mode
            
        Returns:
            dict: Workflow execution result
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_name}")
            
        workflow = self.workflows[workflow_name]
        start_time = time.time()
        
        logger.info(f"Executing workflow: {workflow_name}")
        
        try:
            # Create execution context
            exec_context = ExecutionContext(
                workflow_id=workflow_name,
                execution_mode=execution_mode or (ExecutionMode.PARALLEL if workflow.parallel_execution else ExecutionMode.SEQUENTIAL),
                error_handling=ErrorHandlingStrategy(workflow.error_handling.lower()),
                retry_policy=workflow.retry_policy,
                global_context=context.copy()
            )
            
            # Build execution plan
            execution_plan = self._build_execution_plan(workflow.plugins)
            
            # Execute plugins according to plan
            results = self._execute_execution_plan(execution_plan, exec_context)
            
            execution_time = time.time() - start_time
            
            # Prepare workflow result
            workflow_result = {
                "workflow_id": workflow_name,
                "status": self._determine_workflow_status(results),
                "execution_time": execution_time,
                "plugins_executed": len(results),
                "plugins_successful": sum(1 for r in results if r.status == "SUCCESS"),
                "plugins_failed": sum(1 for r in results if r.status == "FAILED"),
                "results": [self._serialize_result(r) for r in results],
                "metadata": {
                    "workflow_description": workflow.description,
                    "execution_mode": exec_context.execution_mode.value,
                    "error_handling": exec_context.error_handling.value
                }
            }
            
            # Store execution history
            self._store_execution_history(workflow_result)
            
            # Update performance metrics
            self._update_performance_metrics(workflow_name, workflow_result)
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow_id": workflow_name,
                "status": "FAILED",
                "error": str(e),
                "execution_time": time.time() - start_time
            }
            
    def execute_plugins(self, plugin_ids: List[str],
                       context: Dict[str, Any],
                       execution_mode: ExecutionMode = ExecutionMode.SMART) -> List[PluginExecutionResult]:
        """
        Execute a list of plugins with intelligent scheduling.
        
        Args:
            plugin_ids: List of plugin IDs to execute
            context: Execution context
            execution_mode: Execution mode
            
        Returns:
            List[PluginExecutionResult]: Execution results
        """
        logger.info(f"Executing {len(plugin_ids)} plugins in {execution_mode.value} mode")
        
        # Build execution plan
        execution_plan = self._build_execution_plan(plugin_ids)
        
        # Create execution context
        exec_context = ExecutionContext(
            workflow_id="ad_hoc",
            execution_mode=execution_mode,
            error_handling=ErrorHandlingStrategy.STOP_ON_FAILURE,
            retry_policy={},
            global_context=context.copy()
        )
        
        # Execute plan
        return self._execute_execution_plan(execution_plan, exec_context)
        
    def get_execution_plan(self, plugin_ids: List[str]) -> List[List[str]]:
        """
        Get execution plan for plugins (for inspection/preview).
        
        Args:
            plugin_ids: List of plugin IDs
            
        Returns:
            List of execution levels
        """
        return self._build_execution_plan(plugin_ids)
        
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get current dependency graph"""
        return dict(self.execution_graph.adjacency())
        
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics and provide insights"""
        if not self.execution_history:
            return {"status": "NO_DATA"}
            
        # Calculate statistics
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for e in self.execution_history if e["status"] == "SUCCESS")
        
        avg_execution_time = sum(e["execution_time"] for e in self.execution_history) / total_executions
        
        # Plugin performance analysis
        plugin_stats = {}
        for execution in self.execution_history:
            for result in execution.get("results", []):
                plugin_id = result["plugin_id"]
                if plugin_id not in plugin_stats:
                    plugin_stats[plugin_id] = {
                        "executions": 0,
                        "successes": 0,
                        "total_time": 0,
                        "avg_time": 0
                    }
                    
                stats = plugin_stats[plugin_id]
                stats["executions"] += 1
                if result["status"] == "SUCCESS":
                    stats["successes"] += 1
                stats["total_time"] += result["execution_time"]
                stats["avg_time"] = stats["total_time"] / stats["executions"]
                
        return {
            "total_executions": total_executions,
            "success_rate": (successful_executions / total_executions) * 100,
            "avg_execution_time": avg_execution_time,
            "plugin_performance": plugin_stats,
            "recommendations": self._generate_performance_recommendations(plugin_stats)
        }
        
    def _build_execution_plan(self, plugin_ids: List[str]) -> List[List[str]]:
        """Build optimized execution plan respecting dependencies"""
        # Get loaded plugins
        loaded_plugins = set(plugin_manager.list_plugins(enabled_only=True))
        requested_plugins = set(plugin_ids)
        
        # Validate all requested plugins are available
        missing_plugins = requested_plugins - loaded_plugins
        if missing_plugins:
            raise PluginValidationError(f"Plugins not available: {missing_plugins}")
            
        # Resolve dependencies
        all_dependencies = set()
        for plugin_id in plugin_ids:
            deps = self._get_plugin_dependencies(plugin_id)
            all_dependencies.update(deps)
            
        # Create complete plugin set
        all_plugins = requested_plugins.union(all_dependencies)
        
        # Build dependency graph
        graph = nx.DiGraph()
        for plugin_id in all_plugins:
            deps = self._get_plugin_dependencies(plugin_id)
            for dep in deps:
                if dep in all_plugins:
                    graph.add_edge(dep, plugin_id)
                    
        # Topological sort to get execution order
        try:
            execution_order = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise PluginValidationError("Circular dependency detected in plugins")
            
        # Group into execution levels (plugins at same level can run in parallel)
        execution_levels = self._group_by_execution_level(execution_order, graph)
        
        return execution_levels
        
    def _execute_execution_plan(self, execution_plan: List[List[str]], 
                               context: ExecutionContext) -> List[PluginExecutionResult]:
        """Execute plugins according to execution plan"""
        all_results = []
        
        for level_plugins in execution_plan:
            level_results = []
            
            if context.execution_mode == ExecutionMode.PARALLEL and len(level_plugins) > 1:
                # Execute level in parallel
                level_results = self._execute_level_parallel(level_plugins, context)
            elif context.execution_mode == ExecutionMode.SEQUENTIAL:
                # Execute sequentially
                level_results = self._execute_level_sequential(level_plugins, context)
            elif context.execution_mode == ExecutionMode.SMART:
                # Smart execution based on performance metrics
                level_results = self._execute_level_smart(level_plugins, context)
            else:
                # Default to sequential for safety
                level_results = self._execute_level_sequential(level_plugins, context)
                
            all_results.extend(level_results)
            
            # Check error handling strategy
            if context.error_handling == ErrorHandlingStrategy.STOP_ON_FAILURE:
                failed_results = [r for r in level_results if r.status == "FAILED"]
                if failed_results:
                    logger.error(f"Stopping execution due to failures in plugins: {[r.plugin_id for r in failed_results]}")
                    break
                    
        return all_results
        
    def _execute_level_parallel(self, plugins: List[str], 
                               context: ExecutionContext) -> List[PluginExecutionResult]:
        """Execute plugins in parallel"""
        futures = {}
        
        for plugin_id in plugins:
            if self._should_execute_plugin(plugin_id, context):
                future = self.executor.submit(
                    self._execute_plugin_with_retry, plugin_id, context
                )
                futures[future] = plugin_id
                
        results = []
        for future in as_completed(futures):
            plugin_id = futures[future]
            try:
                result = future.result(timeout=context.timeout)
                results.append(result)
            except Exception as e:
                logger.error(f"Plugin {plugin_id} execution failed: {e}")
                results.append(PluginExecutionResult(
                    plugin_id=plugin_id,
                    status="FAILED",
                    result={},
                    execution_time=0.0,
                    error=str(e)
                ))
                
        return results
        
    def _execute_level_sequential(self, plugins: List[str], 
                                 context: ExecutionContext) -> List[PluginExecutionResult]:
        """Execute plugins sequentially"""
        results = []
        
        for plugin_id in plugins:
            if self._should_execute_plugin(plugin_id, context):
                result = self._execute_plugin_with_retry(plugin_id, context)
                results.append(result)
                
                # Check if we should continue
                if (context.error_handling == ErrorHandlingStrategy.STOP_ON_FAILURE and 
                    result.status == "FAILED"):
                    break
                    
        return results
        
    def _execute_level_smart(self, plugins: List[str], 
                            context: ExecutionContext) -> List[PluginExecutionResult]:
        """Execute plugins with intelligent scheduling"""
        # Analyze plugin performance to decide execution strategy
        fast_plugins = []
        slow_plugins = []
        
        for plugin_id in plugins:
            avg_time = self._get_plugin_average_time(plugin_id)
            if avg_time and avg_time > 5.0:  # 5 seconds threshold
                slow_plugins.append(plugin_id)
            else:
                fast_plugins.append(plugin_id)
                
        results = []
        
        # Execute fast plugins in parallel
        if fast_plugins:
            fast_results = self._execute_level_parallel(fast_plugins, context)
            results.extend(fast_results)
            
        # Execute slow plugins sequentially
        if slow_plugins:
            slow_results = self._execute_level_sequential(slow_plugins, context)
            results.extend(slow_results)
            
        return results
        
    def _execute_plugin_with_retry(self, plugin_id: str, 
                                  context: ExecutionContext) -> PluginExecutionResult:
        """Execute plugin with retry logic"""
        max_retries = context.retry_policy.get('max_retries', 0)
        backoff_strategy = context.retry_policy.get('backoff_strategy', 'LINEAR')
        
        last_result = None
        
        for attempt in range(max_retries + 1):
            try:
                # Check circuit breaker
                if self._is_circuit_breaker_open(plugin_id):
                    return PluginExecutionResult(
                        plugin_id=plugin_id,
                        status="FAILED",
                        result={},
                        execution_time=0.0,
                        error="Circuit breaker is open"
                    )
                    
                # Execute plugin
                plugin_context = context.global_context.copy()
                result = plugin_manager.execute_plugin(plugin_id, plugin_context, context.timeout)
                
                # Update circuit breaker
                self._update_circuit_breaker(plugin_id, result)
                
                if result.status == "SUCCESS":
                    return result
                else:
                    last_result = result
                    
                    # Check if we should retry
                    if attempt < max_retries:
                        wait_time = self._calculate_backoff_time(attempt, backoff_strategy)
                        logger.warning(f"Plugin {plugin_id} failed (attempt {attempt + 1}), retrying in {wait_time}s")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Plugin {plugin_id} failed after {max_retries + 1} attempts")
                        
            except Exception as e:
                last_result = PluginExecutionResult(
                    plugin_id=plugin_id,
                    status="FAILED",
                    result={},
                    execution_time=0.0,
                    error=str(e)
                )
                
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt, backoff_strategy)
                    logger.warning(f"Plugin {plugin_id} error (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    
        return last_result
        
    def _should_execute_plugin(self, plugin_id: str, context: ExecutionContext) -> bool:
        """Check if plugin should be executed based on conditions"""
        # Check if plugin is enabled
        plugins_list = plugin_manager.list_plugins(enabled_only=True)
        if plugin_id not in [p['plugin_id'] for p in plugins_list]:
            return False
            
        # Add more sophisticated conditions here
        return True
        
    def _get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """Get dependencies for a plugin"""
        plugins_list = plugin_manager.list_plugins()
        for plugin in plugins_list:
            if plugin['plugin_id'] == plugin_id:
                return plugin.get('dependencies', [])
        return []
        
    def _build_workflow_graph(self, workflow: WorkflowDefinition) -> None:
        """Build execution graph for a workflow"""
        with self._lock:
            # Clear existing graph for this workflow
            self.execution_graph.clear()
            
            # Add plugins and dependencies
            for plugin_id in workflow.plugins:
                self.execution_graph.add_node(plugin_id)
                deps = self._get_plugin_dependencies(plugin_id)
                for dep in deps:
                    if dep in workflow.plugins:
                        self.execution_graph.add_edge(dep, plugin_id)
                        
    def _group_by_execution_level(self, execution_order: List[str], 
                                  graph: nx.DiGraph) -> List[List[str]]:
        """Group plugins into execution levels"""
        levels = []
        remaining = execution_order.copy()
        
        while remaining:
            current_level = []
            
            for plugin_id in remaining[:]:
                # Check if all dependencies are already assigned to levels
                deps = set(graph.predecessors(plugin_id))
                assigned_deps = set()
                
                for level in levels:
                    assigned_deps.update(level)
                    
                if not deps - assigned_deps:
                    current_level.append(plugin_id)
                    remaining.remove(plugin_id)
                    
            if current_level:
                levels.append(current_level)
            else:
                # Circular dependency or unresolved dependencies
                raise PluginValidationError(f"Cannot resolve execution order for: {remaining}")
                
        return levels
        
    def _determine_workflow_status(self, results: List[PluginExecutionResult]) -> str:
        """Determine overall workflow status from plugin results"""
        if not results:
            return "FAILED"
            
        successful = sum(1 for r in results if r.status == "SUCCESS")
        total = len(results)
        
        if successful == total:
            return "SUCCESS"
        elif successful == 0:
            return "FAILED"
        else:
            return "PARTIAL_SUCCESS"
            
    def _serialize_result(self, result: PluginExecutionResult) -> Dict[str, Any]:
        """Serialize plugin execution result"""
        return {
            "plugin_id": result.plugin_id,
            "status": result.status,
            "execution_time": result.execution_time,
            "error": result.error,
            "warnings": result.warnings,
            "metrics": result.result.get('metrics', {}),
            "artifacts": result.result.get('artifacts', [])
        }
        
    def _calculate_backoff_time(self, attempt: int, strategy: str) -> float:
        """Calculate backoff time for retries"""
        if strategy == "LINEAR":
            return 1.0 + attempt * 0.5
        elif strategy == "EXPONENTIAL":
            return min(30.0, 2.0 ** attempt)
        else:
            return 1.0
            
    def _is_circuit_breaker_open(self, plugin_id: str) -> bool:
        """Check if circuit breaker is open for a plugin"""
        if plugin_id not in self.circuit_breakers:
            return False
            
        breaker = self.circuit_breakers[plugin_id]
        
        # Reset circuit breaker if timeout has passed
        if time.time() - breaker['last_failure_time'] > breaker['timeout']:
            breaker['state'] = 'CLOSED'
            breaker['failure_count'] = 0
            
        return breaker['state'] == 'OPEN'
        
    def _update_circuit_breaker(self, plugin_id: str, result: PluginExecutionResult) -> None:
        """Update circuit breaker state based on execution result"""
        if plugin_id not in self.circuit_breakers:
            self.circuit_breakers[plugin_id] = {
                'state': 'CLOSED',
                'failure_count': 0,
                'last_failure_time': 0,
                'timeout': 60.0,  # 1 minute
                'failure_threshold': 5
            }
            
        breaker = self.circuit_breakers[plugin_id]
        
        if result.status == "FAILED":
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = time.time()
            
            if breaker['failure_count'] >= breaker['failure_threshold']:
                breaker['state'] = 'OPEN'
                logger.warning(f"Circuit breaker opened for plugin {plugin_id}")
        else:
            # Reset on success
            breaker['failure_count'] = 0
            if breaker['state'] == 'HALF_OPEN':
                breaker['state'] = 'CLOSED'
                
    def _get_plugin_average_time(self, plugin_id: str) -> Optional[float]:
        """Get average execution time for a plugin"""
        if plugin_id not in self.performance_metrics:
            return None
            
        metrics = self.performance_metrics[plugin_id]
        if metrics['execution_count'] == 0:
            return None
            
        return metrics['total_execution_time'] / metrics['execution_count']
        
    def _store_execution_history(self, result: Dict[str, Any]) -> None:
        """Store execution result in history"""
        with self._lock:
            result['timestamp'] = time.time()
            self.execution_history.append(result)
            
            # Keep only last 1000 executions
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
                
    def _update_performance_metrics(self, workflow_name: str, result: Dict[str, Any]) -> None:
        """Update performance metrics"""
        with self._lock:
            for plugin_result in result.get('results', []):
                plugin_id = plugin_result['plugin_id']
                
                if plugin_id not in self.performance_metrics:
                    self.performance_metrics[plugin_id] = {
                        'execution_count': 0,
                        'total_execution_time': 0,
                        'success_count': 0,
                        'failure_count': 0,
                        'last_execution': 0
                    }
                    
                metrics = self.performance_metrics[plugin_id]
                metrics['execution_count'] += 1
                metrics['total_execution_time'] += plugin_result['execution_time']
                metrics['last_execution'] = time.time()
                
                if plugin_result['status'] == 'SUCCESS':
                    metrics['success_count'] += 1
                else:
                    metrics['failure_count'] += 1
                    
    def _generate_performance_recommendations(self, plugin_stats: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        for plugin_id, stats in plugin_stats.items():
            success_rate = (stats['successes'] / stats['executions']) * 100
            
            if success_rate < 90:
                recommendations.append(
                    f"Plugin {plugin_id} has low success rate ({success_rate:.1f}%). "
                    "Consider reviewing configuration or increasing retry attempts."
                )
                
            if stats['avg_time'] > 30:
                recommendations.append(
                    f"Plugin {plugin_id} has high average execution time ({stats['avg_time']:.1f}s). "
                    "Consider optimization or running in parallel."
                )
                
        if not recommendations:
            recommendations.append("All plugins are performing well.")
            
        return recommendations
        
    def load_workflows_from_config(self, config_path: str) -> int:
        """Load workflows from configuration file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.error(f"Workflow config file not found: {config_path}")
            return 0
            
        try:
            with open(config_file, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
                
            workflows = config.get('workflows', {})
            loaded_count = 0
            
            for workflow_name, workflow_config in workflows.items():
                workflow_config['name'] = workflow_name
                if self.load_workflow(workflow_config):
                    loaded_count += 1
                    
            logger.info(f"Loaded {loaded_count} workflows from configuration")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load workflows from config: {e}")
            return 0
            
    def shutdown(self) -> None:
        """Shutdown orchestrator and cleanup resources"""
        logger.info("Shutting down plugin orchestrator...")
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Plugin orchestrator shutdown complete")


# Global orchestrator instance
orchestrator = PluginOrchestrator()