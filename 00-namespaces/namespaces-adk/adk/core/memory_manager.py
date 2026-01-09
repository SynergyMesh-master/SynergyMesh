"""
Memory Manager: Unified management of short-term and long-term memory.

This module provides unified memory operations for agents, supporting
both context window (short-term) and persistent (long-term) memory backends.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from abc import ABC, abstractmethod

from .event_bus import EventBus
from ..observability.logging import Logger


class MemoryType(Enum):
    """Types of memory storage."""
    SHORT_TERM = "short_term"  # Context window
    LONG_TERM = "long_term"    # Persistent storage
    VECTOR = "vector"          # Vector database for semantic search


@dataclass
class MemoryEntry:
    """A memory entry."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    memory_type: MemoryType = MemoryType.LONG_TERM
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    importance: float = 1.0  # 0.0 to 1.0
    access_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())


@dataclass
class MemoryQuery:
    """A memory query."""
    query_text: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    limit: int = 10
    threshold: float = 0.7
    metadata_filter: Optional[Dict[str, Any]] = None


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry."""
        pass
    
    @abstractmethod
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID."""
        pass
    
    @abstractmethod
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        pass
    
    @abstractmethod
    async def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memory entries."""
        pass
    
    @abstractmethod
    async def summarize(
        self,
        session_id: str,
        max_tokens: int = 1000
    ) -> str:
        """Summarize memory for a session."""
        pass


class InMemoryBackend(MemoryBackend):
    """In-memory backend for testing and development."""
    
    def __init__(self):
        self._storage: Dict[str, MemoryEntry] = {}
        self._logger = logging.getLogger(__name__)
    
    async def add(self, entry: MemoryEntry) -> str:
        self._storage[entry.id] = entry
        return entry.id
    
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        return self._storage.get(entry_id)
    
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        entry = self._storage.get(entry_id)
        if not entry:
            return False
        for key, value in updates.items():
            setattr(entry, key, value)
        entry.updated_at = datetime.now()
        return True
    
    async def delete(self, entry_id: str) -> bool:
        if entry_id in self._storage:
            del self._storage[entry_id]
            return True
        return False
    
    async def query(self, query: MemoryQuery) -> List[MemoryEntry]:
        # Simple text-based query (in production, use vector similarity)
        results = []
        query_lower = query.query_text.lower()
        
        for entry in self._storage.values():
            # Apply filters
            if query.session_id and entry.session_id != query.session_id:
                continue
            if query.user_id and entry.user_id != query.user_id:
                continue
            if query.memory_type and entry.memory_type != query.memory_type:
                continue
            
            # Simple text match
            if query_lower in entry.content.lower():
                results.append(entry)
                if len(results) >= query.limit:
                    break
        
        return results
    
    async def summarize(
        self,
        session_id: str,
        max_tokens: int = 1000
    ) -> str:
        # Simple summarization (in production, use LLM)
        entries = [e for e in self._storage.values() if e.session_id == session_id]
        if not entries:
            return ""
        
        # Sort by importance and recency
        entries.sort(key=lambda e: (e.importance, e.created_at), reverse=True)
        
        # Build summary
        summary_parts = []
        total_tokens = 0
        
        for entry in entries:
            entry_tokens = len(entry.content.split())
            if total_tokens + entry_tokens > max_tokens:
                break
            summary_parts.append(entry.content)
            total_tokens += entry_tokens
        
        return " ".join(summary_parts)


class MemoryManager:
    """
    Unified memory manager for agents.
    
    Provides:
    - Unified API for short-term and long-term memory
    - Context window management
    - Memory compaction and summarization
    - Plugin support for different backends
    - PII filtering integration
    """
    
    def __init__(
        self,
        backend: str = "in_memory",
        event_bus: Optional[EventBus] = None,
        **backend_config
    ):
        self.backend_type = backend
        self.event_bus = event_bus
        self.backend_config = backend_config
        
        self.logger = Logger(name="memory.manager")
        
        # Initialize backend
        self.backend: Optional[MemoryBackend] = None
        
        # Context window cache
        self._context_cache: Dict[str, List[MemoryEntry]] = {}
        self._context_max_size: int = backend_config.get("context_max_size", 50)
        
        # Statistics
        self._stats = {
            "total_entries": 0,
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the memory manager and backend."""
        self.logger.info(f"Initializing memory manager with backend: {self.backend_type}")
        
        if self.backend_type == "in_memory":
            self.backend = InMemoryBackend()
        elif self.backend_type == "redis":
            # Would initialize Redis backend
            pass
        elif self.backend_type == "vector":
            # Would initialize vector DB backend
            pass
        else:
            raise ValueError(f"Unknown backend type: {self.backend_type}")
        
        self.logger.info("Memory manager initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the memory manager."""
        self.logger.info("Memory manager shutdown")
    
    async def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0
    ) -> str:
        """
        Add a memory entry.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            session_id: Session ID
            user_id: User ID
            metadata: Additional metadata
            importance: Importance score (0.0 to 1.0)
            
        Returns:
            Entry ID
        """
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
            importance=importance
        )
        
        entry_id = await self.backend.add(entry)
        self._stats["total_entries"] += 1
        
        # Update context cache
        if session_id and memory_type == MemoryType.SHORT_TERM:
            self._update_context_cache(session_id, entry)
        
        # Emit event
        if self.event_bus:
            await self.event_bus.publish(
                "memory.added",
                {
                    "entry_id": entry_id,
                    "memory_type": memory_type.value,
                    "session_id": session_id,
                    "user_id": user_id
                }
            )
        
        self.logger.debug(f"Added memory entry: {entry_id}")
        return entry_id
    
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID."""
        entry = await self.backend.get(entry_id)
        if entry:
            entry.access_count += 1
        return entry
    
    async def update(
        self,
        entry_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a memory entry."""
        updates = {}
        if content:
            updates["content"] = content
        if metadata:
            updates["metadata"] = metadata
        
        success = await self.backend.update(entry_id, updates)
        
        if success and self.event_bus:
            await self.event_bus.publish(
                "memory.updated",
                {"entry_id": entry_id}
            )
        
        return success
    
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        success = await self.backend.delete(entry_id)
        
        if success and self.event_bus:
            await self.event_bus.publish(
                "memory.deleted",
                {"entry_id": entry_id}
            )
        
        return success
    
    async def query(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """
        Query memory entries.
        
        Args:
            query_text: Query text
            session_id: Session ID filter
            user_id: User ID filter
            memory_type: Memory type filter
            limit: Maximum number of results
            threshold: Similarity threshold (for vector search)
            metadata_filter: Metadata filter
            
        Returns:
            List of matching memory entries
        """
        self._stats["total_queries"] += 1
        
        query = MemoryQuery(
            query_text=query_text,
            session_id=session_id,
            user_id=user_id,
            memory_type=memory_type,
            limit=limit,
            threshold=threshold,
            metadata_filter=metadata_filter
        )
        
        results = await self.backend.query(query)
        
        # Update access counts
        for entry in results:
            entry.access_count += 1
        
        self.logger.debug(f"Query returned {len(results)} results")
        return results
    
    async def get_context(
        self,
        session_id: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Get context window for a session.
        
        Args:
            session_id: Session ID
            max_tokens: Maximum tokens
            
        Returns:
            Context string
        """
        # Check cache
        if session_id in self._context_cache:
            self._stats["cache_hits"] += 1
            entries = self._context_cache[session_id]
        else:
            self._stats["cache_misses"] += 1
            # Query for short-term memory
            entries = await self.query(
                query_text="",
                session_id=session_id,
                memory_type=MemoryType.SHORT_TERM,
                limit=100
            )
            self._context_cache[session_id] = entries
        
        # Build context string
        context_parts = []
        total_tokens = 0
        
        for entry in entries:
            entry_tokens = len(entry.content.split())
            if total_tokens + entry_tokens > max_tokens:
                break
            context_parts.append(entry.content)
            total_tokens += entry_tokens
        
        return "\n\n".join(context_parts)
    
    async def compact_context(
        self,
        session_id: str,
        max_tokens: int = 1000
    ) -> str:
        """
        Compact context window by summarizing older entries.
        
        Args:
            session_id: Session ID
            max_tokens: Maximum tokens for summary
            
        Returns:
            Compacted context string
        """
        if self.backend:
            return await self.backend.summarize(session_id, max_tokens)
        return ""
    
    def _update_context_cache(self, session_id: str, entry: MemoryEntry) -> None:
        """Update context cache with new entry."""
        if session_id not in self._context_cache:
            self._context_cache[session_id] = []
        
        cache = self._context_cache[session_id]
        cache.append(entry)
        
        # Maintain max size
        if len(cache) > self._context_max_size:
            # Remove oldest entries
            cache.sort(key=lambda e: e.created_at)
            self._context_cache[session_id] = cache[-self._context_max_size:]
    
    async def clear_session(self, session_id: str) -> int:
        """
        Clear all memory for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Number of entries deleted
        """
        # Query all entries for session
        entries = await self.query(query_text="", session_id=session_id, limit=1000)
        
        # Delete all entries
        count = 0
        for entry in entries:
            if await self.delete(entry.id):
                count += 1
        
        # Clear context cache
        if session_id in self._context_cache:
            del self._context_cache[session_id]
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            **self._stats,
            "backend_type": self.backend_type,
            "context_cache_size": len(self._context_cache)
        }