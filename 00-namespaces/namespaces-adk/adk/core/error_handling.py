"""
Error Handling: Centralized error handling, retry, and compensation.

This module provides robust error handling, retry strategies, and
compensation logic for agent workflows and tool invocations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import functools
import traceback

from .event_bus import EventBus
from ..observability.logging import Logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorType(Enum):
    """Error types."""
    TRANSIENT = "transient"  # Temporary, retryable
    PERMANENT = "permanent"  # Permanent, not retryable
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    component: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "traceback": self.traceback,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "correlation_id": self.correlation_id
        }


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.TRANSIENT,
        ErrorType.TIMEOUT,
        ErrorType.RATE_LIMIT
    ])


class ErrorHandler:
    """
    Centralized error handling with retry strategies and compensation.
    
    Features:
    - Error classification and routing
    - Configurable retry policies
    - Circuit breaker pattern
    - Compensation and rollback
    - Error event publishing
    - Error statistics and monitoring
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self.logger = Logger(name="error.handler")
        
        # Retry policies by operation name
        self._retry_policies: Dict[str, RetryPolicy] = {}
        
        # Circuit breaker state
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Error statistics
        self._stats = {
            "total_errors": 0,
            "by_type": {},
            "by_severity": {},
            "by_component": {}
        }
        
        # Error handlers
        self._error_handlers: Dict[ErrorType, List[Callable]] = {}
    
    def register_retry_policy(
        self,
        operation_name: str,
        policy: RetryPolicy
    ) -> None:
        """
        Register a retry policy for an operation.
        
        Args:
            operation_name: Name of the operation
            policy: Retry policy configuration
        """
        self._retry_policies[operation_name] = policy
        self.logger.debug(f"Registered retry policy for {operation_name}")
    
    def get_retry_policy(self, operation_name: str) -> RetryPolicy:
        """Get retry policy for an operation."""
        return self._retry_policies.get(
            operation_name,
            RetryPolicy()  # Default policy
        )
    
    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """
        Classify an error into ErrorType and ErrorSeverity.
        
        Args:
            error: The exception
            context: Additional context
            
        Returns:
            ErrorInfo object
        """
        error_type = ErrorType.UNKNOWN
        severity = ErrorSeverity.ERROR
        
        error_str = str(error).lower()
        
        # Classify error type
        if "timeout" in error_str or "timed out" in error_str:
            error_type = ErrorType.TIMEOUT
        elif "rate limit" in error_str or "429" in error_str:
            error_type = ErrorType.RATE_LIMIT
        elif "authentication" in error_str or "unauthorized" in error_str:
            error_type = ErrorType.AUTHENTICATION
        elif "permission" in error_str or "forbidden" in error_str:
            error_type = ErrorType.AUTHORIZATION
        elif "validation" in error_str or "invalid" in error_str:
            error_type = ErrorType.VALIDATION
        elif isinstance(error, (ConnectionError, TimeoutError)):
            error_type = ErrorType.TRANSIENT
        
        # Determine severity
        if error_type in [ErrorType.AUTHENTICATION, ErrorType.AUTHORIZATION]:
            severity = ErrorSeverity.WARNING
        elif error_type == ErrorType.RESOURCE_EXHAUSTED:
            severity = ErrorSeverity.CRITICAL
        
        return ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(error),
            context=context or {},
            traceback=traceback.format_exc(),
            component=context.get("component") if context else None,
            correlation_id=context.get("correlation_id") if context else None
        )
    
    async def handle_error(self, error_info: ErrorInfo) -> None:
        """
        Handle an error by publishing events and invoking handlers.
        
        Args:
            error_info: Error information
        """
        # Update statistics
        self._update_stats(error_info)
        
        # Publish error event
        if self.event_bus:
            await self.event_bus.publish(
                "error.occurred",
                error_info.to_dict()
            )
        
        # Invoke error handlers
        handlers = self._error_handlers.get(error_info.error_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_info)
                else:
                    handler(error_info)
            except Exception as e:
                self.logger.error(f"Error handler failed: {e}", exc_info=True)
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Function to execute
            operation_name: Name of the operation
            context: Execution context
            **kwargs: Arguments to pass to operation
            
        Returns:
            Operation result
            
        Raises:
            Exception: If operation fails after all retries
        """
        policy = self.get_retry_policy(operation_name)
        last_error = None
        
        for attempt in range(policy.max_attempts):
            try:
                # Check circuit breaker
                if self._is_circuit_open(operation_name):
                    raise Exception(f"Circuit breaker open for {operation_name}")
                
                # Execute operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(**kwargs)
                else:
                    result = operation(**kwargs)
                
                # Success - reset circuit breaker
                self._reset_circuit_breaker(operation_name)
                
                return result
                
            except Exception as e:
                last_error = e
                error_info = self.classify_error(e, context)
                
                # Check if error is retryable
                if error_info.error_type not in policy.retryable_errors:
                    await self.handle_error(error_info)
                    raise
                
                # Check if we have more attempts
                if attempt == policy.max_attempts - 1:
                    await self.handle_error(error_info)
                    raise
                
                # Calculate delay
                delay = self._calculate_delay(policy, attempt)
                
                self.logger.warning(
                    f"Attempt {attempt + 1}/{policy.max_attempts} failed for {operation_name}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                await asyncio.sleep(delay)
        
        # This should not be reached
        raise last_error
    
    def _calculate_delay(self, policy: RetryPolicy, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        delay = policy.initial_delay * (policy.exponential_base ** attempt)
        
        # Apply max delay
        delay = min(delay, policy.max_delay)
        
        # Apply jitter
        if policy.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def _is_circuit_open(self, operation_name: str) -> bool:
        """Check if circuit breaker is open for an operation."""
        breaker = self._circuit_breakers.get(operation_name)
        if not breaker:
            return False
        
        if breaker["state"] == "open":
            # Check if cooldown period has passed
            if datetime.now() >= breaker["next_attempt_time"]:
                breaker["state"] = "half_open"
                return False
            return True
        
        return False
    
    def _record_failure(self, operation_name: str) -> None:
        """Record a failure for circuit breaker."""
        if operation_name not in self._circuit_breakers:
            self._circuit_breakers[operation_name] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "next_attempt_time": None
            }
        
        breaker = self._circuit_breakers[operation_name]
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = datetime.now()
        
        # Open circuit after 3 consecutive failures
        if breaker["failure_count"] >= 3:
            breaker["state"] = "open"
            breaker["next_attempt_time"] = datetime.now() + timedelta(seconds=60)
            self.logger.warning(f"Circuit breaker opened for {operation_name}")
    
    def _reset_circuit_breaker(self, operation_name: str) -> None:
        """Reset circuit breaker after success."""
        if operation_name in self._circuit_breakers:
            self._circuit_breakers[operation_name] = {
                "state": "closed",
                "failure_count": 0,
                "last_failure_time": None,
                "next_attempt_time": None
            }
    
    def _update_stats(self, error_info: ErrorInfo) -> None:
        """Update error statistics."""
        self._stats["total_errors"] += 1
        
        # By type
        error_type = error_info.error_type.value
        self._stats["by_type"][error_type] = self._stats["by_type"].get(error_type, 0) + 1
        
        # By severity
        severity = error_info.severity.value
        self._stats["by_severity"][severity] = self._stats["by_severity"].get(severity, 0) + 1
        
        # By component
        if error_info.component:
            component = error_info.component
            self._stats["by_component"][component] = self._stats["by_component"].get(component, 0) + 1
    
    def register_error_handler(
        self,
        error_type: ErrorType,
        handler: Callable
    ) -> None:
        """
        Register an error handler.
        
        Args:
            error_type: Error type to handle
            handler: Handler function
        """
        if error_type not in self._error_handlers:
            self._error_handlers[error_type] = []
        self._error_handlers[error_type].append(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            **self._stats,
            "circuit_breakers": {
                name: {
                    "state": breaker["state"],
                    "failure_count": breaker["failure_count"]
                }
                for name, breaker in self._circuit_breakers.items()
            }
        }


def retry(
    operation_name: str,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Decorator for retrying operations.
    
    Args:
        operation_name: Name of the operation
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # This is a simplified version - in production,
            # would use the ErrorHandler instance
            policy = RetryPolicy(
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base
            )
            
            last_error = None
            for attempt in range(policy.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == policy.max_attempts - 1:
                        raise
                    
                    delay = policy.initial_delay * (policy.exponential_base ** attempt)
                    delay = min(delay, policy.max_delay)
                    await asyncio.sleep(delay)
            
            raise last_error
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Simplified sync version
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_attempts - 1:
                        raise
                    import time
                    time.sleep(initial_delay * (exponential_base ** attempt))
            raise last_error
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator