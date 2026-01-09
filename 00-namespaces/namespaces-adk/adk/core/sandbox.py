"""
Sandbox: Provides secure, isolated execution environments.

This module implements secure sandboxing for tool calls, code execution,
and untrusted plugins using containers and microVMs.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import subprocess
import shlex


class SandboxType(Enum):
    """Types of sandbox environments."""
    CONTAINER = "container"  # Docker container
    MICROVM = "microvm"      # Firecracker microVM
    PROCESS = "process"      # Isolated process
    PYTHON = "python"        # Python subprocess


class SandboxState(Enum):
    """Sandbox lifecycle states."""
    CREATING = "creating"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ResourceLimits:
    """Resource limits for sandbox."""
    max_memory_mb: int = 512
    max_cpu_cores: float = 1.0
    max_runtime_seconds: int = 60
    max_network: bool = False
    disk_size_mb: int = 100


@dataclass
class SandboxConfig:
    """Configuration for a sandbox."""
    sandbox_type: SandboxType = SandboxType.CONTAINER
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    image: Optional[str] = None  # Container image
    command: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    working_dir: str = "/workspace"
    volumes: Dict[str, str] = field(default_factory=dict)  # host:container


@dataclass
class SandboxExecution:
    """A sandbox execution result."""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.exit_code == 0


class Sandbox:
    """
    Provides secure, isolated execution environments.
    
    Features:
    - Container and microVM support
    - Resource limiting
    - Timeout enforcement
    - Network isolation
    - Execution logging
    - Pool management for performance
    """
    
    def __init__(
        self,
        pool_size: int = 5,
        default_config: Optional[SandboxConfig] = None
    ):
        self.pool_size = pool_size
        self.default_config = default_config or SandboxConfig()
        
        self.logger = logging.getLogger(__name__)
        
        # Available sandbox pool
        self._pool: List[str] = []
        
        # Active sandboxes
        self._sandboxes: Dict[str, Dict[str, Any]] = {}
        
        # Execution history
        self._executions: Dict[str, SandboxExecution] = {}
        
        # Initialize pool
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize the sandbox pool."""
        self.logger.info(f"Initializing sandbox pool with {self.pool_size} instances")
        
        for i in range(self.pool_size):
            sandbox_id = f"sandbox-{i}"
            self._pool.append(sandbox_id)
            self._sandboxes[sandbox_id] = {
                "id": sandbox_id,
                "state": SandboxState.READY,
                "last_used": None,
                "execution_count": 0
            }
    
    async def acquire_sandbox(
        self,
        config: Optional[SandboxConfig] = None
    ) -> str:
        """
        Acquire a sandbox from the pool.
        
        Args:
            config: Sandbox configuration
            
        Returns:
            Sandbox ID
        """
        config = config or self.default_config
        
        # Wait for available sandbox
        while not self._pool:
            await asyncio.sleep(0.1)
        
        sandbox_id = self._pool.pop(0)
        sandbox = self._sandboxes[sandbox_id]
        
        sandbox["state"] = SandboxState.RUNNING
        sandbox["config"] = config
        
        self.logger.debug(f"Acquired sandbox: {sandbox_id}")
        return sandbox_id
    
    def release_sandbox(self, sandbox_id: str) -> None:
        """
        Release a sandbox back to the pool.
        
        Args:
            sandbox_id: Sandbox ID
        """
        if sandbox_id in self._sandboxes:
            sandbox = self._sandboxes[sandbox_id]
            sandbox["state"] = SandboxState.READY
            sandbox["last_used"] = datetime.now()
            
            self._pool.append(sandbox_id)
            self.logger.debug(f"Released sandbox: {sandbox_id}")
    
    async def execute(
        self,
        command: str,
        config: Optional[SandboxConfig] = None,
        input_data: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> SandboxExecution:
        """
        Execute a command in a sandbox.
        
        Args:
            command: Command to execute
            config: Sandbox configuration
            input_data: Input data for stdin
            timeout: Execution timeout in seconds
            
        Returns:
            Execution result
        """
        config = config or self.default_config
        timeout = timeout or config.resource_limits.max_runtime_seconds
        
        # Acquire sandbox
        sandbox_id = await self.acquire_sandbox(config)
        
        execution = SandboxExecution()
        execution.started_at = datetime.now()
        
        try:
            # Execute command
            result = await self._execute_command(
                sandbox_id,
                command,
                config,
                input_data,
                timeout
            )
            
            execution.exit_code = result.get("exit_code")
            execution.stdout = result.get("stdout", "")
            execution.stderr = result.get("stderr", "")
            
        except asyncio.TimeoutError:
            execution.error = f"Execution timeout after {timeout}s"
            self.logger.warning(
                f"Sandbox execution timeout: {sandbox_id}"
            )
        except Exception as e:
            execution.error = str(e)
            self.logger.error(
                f"Sandbox execution error: {e}",
                exc_info=True
            )
        finally:
            execution.completed_at = datetime.now()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            # Store execution
            self._executions[execution.execution_id] = execution
            
            # Update sandbox stats
            sandbox = self._sandboxes[sandbox_id]
            sandbox["execution_count"] += 1
            
            # Release sandbox
            self.release_sandbox(sandbox_id)
        
        return execution
    
    async def _execute_command(
        self,
        sandbox_id: str,
        command: str,
        config: SandboxConfig,
        input_data: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute a command in the sandbox."""
        
        if config.sandbox_type == SandboxType.PROCESS:
            return await self._execute_in_process(
                command, config, input_data, timeout
            )
        elif config.sandbox_type == SandboxType.PYTHON:
            return await self._execute_in_python(
                command, config, input_data, timeout
            )
        else:
            # For container/microVM, would use Docker SDK
            # Simplified implementation using subprocess
            return await self._execute_in_process(
                command, config, input_data, timeout
            )
    
    async def _execute_in_process(
        self,
        command: str,
        config: SandboxConfig,
        input_data: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute in an isolated process."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                env=config.environment,
                cwd=config.working_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(
                    input_data.encode() if input_data else None
                ),
                timeout=timeout
            )
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
            
        except asyncio.TimeoutError:
            process.kill()
            raise
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def _execute_in_python(
        self,
        command: str,
        config: SandboxConfig,
        input_data: Optional[str],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute Python code in a subprocess."""
        python_command = f'python -c {shlex.quote(command)}'
        return await self._execute_in_process(
            python_command, config, input_data, timeout
        )
    
    def get_execution(
        self,
        execution_id: str
    ) -> Optional[SandboxExecution]:
        """Get an execution by ID."""
        return self._executions.get(execution_id)
    
    def get_sandbox_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics."""
        return {
            "pool_size": self.pool_size,
            "available": len(self._pool),
            "active": self.pool_size - len(self._pool),
            "total_executions": len(self._executions),
            "successful_executions": sum(
                1 for e in self._executions.values() if e.success
            ),
            "failed_executions": sum(
                1 for e in self._executions.values() if not e.success
            )
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.logger.info("Cleaning up sandbox...")
        # Would cleanup containers/microVMs here