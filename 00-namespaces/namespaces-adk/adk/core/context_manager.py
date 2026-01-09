"""
Context Manager: Manages per-session and per-invocation context.

This module provides hierarchical context management for agent sessions,
including user, session, and invocation-scoped variables.
"""

import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import copy

from .event_bus import EventBus
from ..observability.logging import Logger


class ContextScope(Enum):
    """Context scope levels."""
    GLOBAL = "global"       # Application-wide
    USER = "user"           # User-specific
    SESSION = "session"     # Session-specific
    INVOCATION = "invocation"  # Single invocation
    WORKFLOW = "workflow"   # Workflow-specific


@dataclass
class ContextSnapshot:
    """A snapshot of context at a point in time."""
    context_id: str
    timestamp: datetime
    data: Dict[str, Any]
    scope: ContextScope
    parent_id: Optional[str] = None


@dataclass
class ContextEntry:
    """A context entry."""
    key: str
    value: Any
    scope: ContextScope
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ContextManager:
    """
    Manages hierarchical context for agent sessions and invocations.
    
    Features:
    - Hierarchical context (global, user, session, invocation, workflow)
    - Context inheritance and override
    - Thread-safe operations
    - Context snapshots and rollback
    - Context export and import
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self.logger = Logger(name="context.manager")
        
        # Context storage by scope and ID
        self._contexts: Dict[ContextScope, Dict[str, Dict[str, Any]]] = {
            ContextScope.GLOBAL: {},
            ContextScope.USER: {},
            ContextScope.SESSION: {},
            ContextScope.INVOCATION: {},
            ContextScope.WORKFLOW: {}
        }
        
        # Snapshots for rollback
        self._snapshots: Dict[str, ContextSnapshot] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Change listeners
        self._listeners: List[Callable] = []
    
    def create_global_context(self, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create global context (application-wide).
        
        Args:
            initial_data: Initial context data
            
        Returns:
            Context ID
        """
        context_id = "global"
        with self._lock:
            self._contexts[ContextScope.GLOBAL][context_id] = initial_data or {}
        
        self.logger.info(f"Created global context: {context_id}")
        return context_id
    
    def create_user_context(
        self,
        user_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create user-specific context.
        
        Args:
            user_id: User identifier
            initial_data: Initial context data
            
        Returns:
            Context ID
        """
        with self._lock:
            self._contexts[ContextScope.USER][user_id] = initial_data or {}
        
        self.logger.debug(f"Created user context: {user_id}")
        return user_id
    
    def create_session_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create session-specific context.
        
        Args:
            session_id: Session identifier
            user_id: Parent user ID
            initial_data: Initial context data
            
        Returns:
            Context ID
        """
        with self._lock:
            self._contexts[ContextScope.SESSION][session_id] = initial_data or {}
        
        self.logger.debug(f"Created session context: {session_id}")
        return session_id
    
    def create_invocation_context(
        self,
        invocation_id: str,
        session_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create invocation-specific context.
        
        Args:
            invocation_id: Invocation identifier
            session_id: Parent session ID
            initial_data: Initial context data
            
        Returns:
            Context ID
        """
        with self._lock:
            self._contexts[ContextScope.INVOCATION][invocation_id] = initial_data or {}
        
        self.logger.debug(f"Created invocation context: {invocation_id}")
        return invocation_id
    
    def create_workflow_context(
        self,
        workflow_id: str,
        invocation_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create workflow-specific context.
        
        Args:
            workflow_id: Workflow identifier
            invocation_id: Parent invocation ID
            initial_data: Initial context data
            
        Returns:
            Context ID
        """
        with self._lock:
            self._contexts[ContextScope.WORKFLOW][workflow_id] = initial_data or {}
        
        self.logger.debug(f"Created workflow context: {workflow_id}")
        return workflow_id
    
    def get(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        context_id: str = "global",
        default: Any = None
    ) -> Any:
        """
        Get a context value.
        
        Args:
            key: Context key
            scope: Context scope
            context_id: Context ID within scope
            default: Default value if not found
            
        Returns:
            Context value
        """
        with self._lock:
            context = self._contexts.get(scope, {}).get(context_id, {})
            return context.get(key, default)
    
    def set(
        self,
        key: str,
        value: Any,
        scope: ContextScope = ContextScope.GLOBAL,
        context_id: str = "global"
    ) -> None:
        """
        Set a context value.
        
        Args:
            key: Context key
            value: Context value
            scope: Context scope
            context_id: Context ID within scope
        """
        with self._lock:
            if context_id not in self._contexts[scope]:
                self._contexts[scope][context_id] = {}
            
            old_value = self._contexts[scope][context_id].get(key)
            self._contexts[scope][context_id][key] = value
            
            # Emit change event
            self._notify_listeners(key, old_value, value, scope, context_id)
    
    def delete(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        context_id: str = "global"
    ) -> bool:
        """
        Delete a context value.
        
        Args:
            key: Context key
            scope: Context scope
            context_id: Context ID within scope
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            context = self._contexts.get(scope, {}).get(context_id, {})
            if key in context:
                del context[key]
                return True
            return False
    
    def get_all(
        self,
        scope: ContextScope = ContextScope.GLOBAL,
        context_id: str = "global"
    ) -> Dict[str, Any]:
        """
        Get all context values for a scope and context ID.
        
        Args:
            scope: Context scope
            context_id: Context ID within scope
            
        Returns:
            All context values
        """
        with self._lock:
            return copy.deepcopy(self._contexts.get(scope, {}).get(context_id, {}))
    
    def merge_context(
        self,
        data: Dict[str, Any],
        scope: ContextScope = ContextScope.GLOBAL,
        context_id: str = "global",
        overwrite: bool = False
    ) -> None:
        """
        Merge data into context.
        
        Args:
            data: Data to merge
            scope: Context scope
            context_id: Context ID within scope
            overwrite: Whether to overwrite existing values
        """
        with self._lock:
            if context_id not in self._contexts[scope]:
                self._contexts[scope][context_id] = {}
            
            context = self._contexts[scope][context_id]
            
            for key, value in data.items():
                if overwrite or key not in context:
                    context[key] = value
    
    def get_merged_context(
        self,
        session_id: Optional[str] = None,
        invocation_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get merged context from all applicable scopes.
        
        Args:
            session_id: Session ID
            invocation_id: Invocation ID
            workflow_id: Workflow ID
            
        Returns:
            Merged context data (lower scopes override higher scopes)
        """
        with self._lock:
            merged = {}
            
            # Start with global
            merged.update(self._contexts.get(ContextScope.GLOBAL, {}).get("global", {}))
            
            # Add user context if session provided
            if session_id:
                user_id = self.get("user_id", ContextScope.SESSION, session_id)
                if user_id:
                    merged.update(self._contexts.get(ContextScope.USER, {}).get(user_id, {}))
                
                # Add session context
                merged.update(self._contexts.get(ContextScope.SESSION, {}).get(session_id, {}))
            
            # Add invocation context
            if invocation_id:
                merged.update(self._contexts.get(ContextScope.INVOCATION, {}).get(invocation_id, {}))
            
            # Add workflow context
            if workflow_id:
                merged.update(self._contexts.get(ContextScope.WORKFLOW, {}).get(workflow_id, {}))
            
            return copy.deepcopy(merged)
    
    def create_snapshot(
        self,
        scope: ContextScope,
        context_id: str
    ) -> str:
        """
        Create a snapshot of context.
        
        Args:
            scope: Context scope
            context_id: Context ID within scope
            
        Returns:
            Snapshot ID
        """
        with self._lock:
            snapshot_id = f"{scope.value}_{context_id}_{datetime.now().timestamp()}"
            
            self._snapshots[snapshot_id] = ContextSnapshot(
                context_id=snapshot_id,
                timestamp=datetime.now(),
                data=copy.deepcopy(self._contexts.get(scope, {}).get(context_id, {})),
                scope=scope
            )
            
            self.logger.debug(f"Created snapshot: {snapshot_id}")
            return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore context from snapshot.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if restored, False if snapshot not found
        """
        with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
            if not snapshot:
                return False
            
            self._contexts[snapshot.scope][snapshot.context_id] = copy.deepcopy(snapshot.data)
            
            self.logger.debug(f"Restored snapshot: {snapshot_id}")
            return True
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if snapshot_id in self._snapshots:
                del self._snapshots[snapshot_id]
                return True
            return False
    
    def clear_context(
        self,
        scope: ContextScope,
        context_id: Optional[str] = None
    ) -> None:
        """
        Clear context data.
        
        Args:
            scope: Context scope
            context_id: Context ID (if None, clears all in scope)
        """
        with self._lock:
            if context_id:
                self._contexts[scope][context_id] = {}
            else:
                self._contexts[scope] = {}
    
    def export_context(
        self,
        scope: ContextScope,
        context_id: str
    ) -> Dict[str, Any]:
        """
        Export context as dictionary.
        
        Args:
            scope: Context scope
            context_id: Context ID
            
        Returns:
            Exported context data
        """
        return self.get_all(scope, context_id)
    
    def import_context(
        self,
        data: Dict[str, Any],
        scope: ContextScope,
        context_id: str,
        overwrite: bool = False
    ) -> None:
        """
        Import context data.
        
        Args:
            data: Context data to import
            scope: Context scope
            context_id: Context ID
            overwrite: Whether to overwrite existing values
        """
        self.merge_context(data, scope, context_id, overwrite)
    
    def add_change_listener(self, listener: Callable) -> None:
        """
        Add a change listener callback.
        
        Args:
            listener: Callback function
        """
        self._listeners.append(listener)
    
    def _notify_listeners(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        scope: ContextScope,
        context_id: str
    ) -> None:
        """Notify all change listeners."""
        for listener in self._listeners:
            try:
                listener(key, old_value, new_value, scope, context_id)
            except Exception as e:
                self.logger.error(f"Change listener error: {e}", exc_info=True)