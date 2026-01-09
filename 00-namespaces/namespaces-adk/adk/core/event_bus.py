"""
Event Bus: Internal event system for decoupled communication.

This module implements a publish-subscribe event bus for communication
between runtime components.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import inspect

from ..observability.logging import Logger


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """An event in the system."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class Subscription:
    """A subscription to events."""
    event_name: str
    handler: Callable
    priority: EventPriority = EventPriority.NORMAL
    filter_func: Optional[Callable[[Event], bool]] = None
    once: bool = False  # Unsubscribe after first event
    async_handler: bool = False
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
    
    def matches(self, event: Event) -> bool:
        """Check if subscription matches event."""
        if self.event_name != "*" and event.name != self.event_name:
            return False
        
        if self.filter_func and not self.filter_func(event):
            return False
        
        return True


class EventBus:
    """
    Internal event bus for decoupled component communication.
    
    Features:
    - Publish-subscribe pattern
    - Wildcard event matching
    - Event filtering
    - Async and sync event handlers
    - Event prioritization
    - One-time subscriptions
    - Event history and replay
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.logger = Logger(name="event.bus")
        
        # Subscriptions by event name
        self._subscriptions: Dict[str, List[Subscription]] = {}
        
        # Wildcard subscriptions
        self._wildcard_subscriptions: List[Subscription] = []
        
        # Event history
        self._history: List[Event] = []
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def publish(
        self,
        event_name: str,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Publish an event to all subscribers.
        
        Args:
            event_name: Name of the event
            data: Event data payload
            priority: Event priority
            correlation_id: Correlation ID for event chains
            source: Event source
            metadata: Additional metadata
            
        Returns:
            Number of subscribers notified
        """
        event = Event(
            name=event_name,
            data=data or {},
            priority=priority,
            correlation_id=correlation_id,
            source=source,
            metadata=metadata or {}
        )
        
        # Add to history
        self._add_to_history(event)
        
        # Get matching subscriptions
        subscriptions = await self._get_matching_subscriptions(event)
        
        # Sort by priority
        subscriptions.sort(key=lambda s: s.priority.value, reverse=True)
        
        # Execute handlers
        notified_count = 0
        once_subscriptions: List[str] = []
        
        for subscription in subscriptions:
            try:
                if subscription.async_handler:
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                
                notified_count += 1
                
                if subscription.once:
                    once_subscriptions.append(subscription.id)
                    
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event_name}: {e}",
                    exc_info=True,
                    extra={"subscription_id": subscription.id}
                )
        
        # Remove one-time subscriptions
        for sub_id in once_subscriptions:
            await self.unsubscribe(sub_id)
        
        self.logger.debug(
            f"Published event {event_name} to {notified_count} subscribers"
        )
        
        return notified_count
    
    async def subscribe(
        self,
        event_name: str,
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None,
        once: bool = False
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_name: Name of the event (use "*" for all events)
            handler: Event handler function
            priority: Subscription priority
            filter_func: Optional filter function
            once: Whether to unsubscribe after first event
            
        Returns:
            Subscription ID
        """
        # Check if handler is async
        async_handler = inspect.iscoroutinefunction(handler)
        
        subscription = Subscription(
            event_name=event_name,
            handler=handler,
            priority=priority,
            filter_func=filter_func,
            once=once,
            async_handler=async_handler
        )
        
        async with self._lock:
            if event_name == "*":
                self._wildcard_subscriptions.append(subscription)
            else:
                if event_name not in self._subscriptions:
                    self._subscriptions[event_name] = []
                self._subscriptions[event_name].append(subscription)
        
        self.logger.debug(f"Subscribed to {event_name}: {subscription.id}")
        return subscription.id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if unsubscribed, False if not found
        """
        async with self._lock:
            # Check wildcard subscriptions
            for sub in self._wildcard_subscriptions:
                if sub.id == subscription_id:
                    self._wildcard_subscriptions.remove(sub)
                    return True
            
            # Check regular subscriptions
            for event_name, subs in self._subscriptions.items():
                for sub in subs:
                    if sub.id == subscription_id:
                        subs.remove(sub)
                        return True
        
        return False
    
    async def _get_matching_subscriptions(
        self,
        event: Event
    ) -> List[Subscription]:
        """Get all subscriptions matching an event."""
        async with self._lock:
            matching = []
            
            # Add wildcard subscriptions
            for sub in self._wildcard_subscriptions:
                if sub.matches(event):
                    matching.append(sub)
            
            # Add specific event subscriptions
            for sub in self._subscriptions.get(event.name, []):
                if sub.matches(event):
                    matching.append(sub)
            
            return matching
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history."""
        self._history.append(event)
        
        # Maintain max history size
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
    
    def get_history(
        self,
        event_name: Optional[str] = None,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_name: Filter by event name
            limit: Maximum number of events
            since: Filter events since this timestamp
            
        Returns:
            List of events
        """
        history = self._history
        
        if event_name:
            history = [e for e in history if e.name == event_name]
        
        if since:
            history = [e for e in history if e.timestamp >= since]
        
        return history[-limit:]
    
    async def wait_for_event(
        self,
        event_name: str,
        timeout: Optional[float] = None,
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> Optional[Event]:
        """
        Wait for a specific event.
        
        Args:
            event_name: Name of event to wait for
            timeout: Timeout in seconds
            filter_func: Optional filter function
            
        Returns:
            Event if received, None if timeout
        """
        future = asyncio.Future()
        
        async def handler(event: Event):
            if not future.done():
                future.set_result(event)
        
        subscription_id = await self.subscribe(
            event_name,
            handler,
            once=True,
            filter_func=filter_func
        )
        
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            await self.unsubscribe(subscription_id)
    
    def get_subscriber_count(self, event_name: Optional[str] = None) -> int:
        """
        Get the number of subscribers.
        
        Args:
            event_name: Event name (if None, counts all)
            
        Returns:
            Number of subscribers
        """
        count = 0
        
        if event_name:
            count = len(self._subscriptions.get(event_name, []))
        else:
            for subs in self._subscriptions.values():
                count += len(subs)
            count += len(self._wildcard_subscriptions)
        
        return count
    
    async def clear_history(self) -> None:
        """Clear event history."""
        self._history = []
        self.logger.debug("Event history cleared")
    
    async def shutdown(self) -> None:
        """Shutdown the event bus."""
        async with self._lock:
            self._subscriptions = {}
            self._wildcard_subscriptions = []
            self._history = []
        
        self.logger.info("Event bus shutdown")