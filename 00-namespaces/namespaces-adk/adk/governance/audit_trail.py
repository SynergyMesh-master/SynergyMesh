"""
Audit Trail: Maintains comprehensive, tamper-evident audit trails.

This module records all agent actions, tool invocations, and
governance events for compliance and forensic analysis.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib

from ..observability.logging import Logger


@dataclass
class AuditEntry:
    """An audit log entry."""
    entry_id: str
    timestamp: datetime
    event_type: str
    agent_id: str
    user_id: Optional[str]
    action: str
    resource: Optional[str]
    details: Dict[str, Any]
    hash: str
    previous_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "hash": self.hash,
            "previous_hash": self.previous_hash
        }


class AuditTrail:
    """
    Maintains tamper-evident audit trails.
    
    Features:
    - Immutable log entries with hashing
    - Chain of integrity verification
    - Search and export
    - Compliance reporting
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.logger = Logger(name="governance.audit")
        
        # In-memory storage
        self._entries: List[AuditEntry] = []
        
        # Hash chain
        self._last_hash = ""
    
    def log(
        self,
        event_type: str,
        agent_id: str,
        action: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        resource: Optional[str] = None
    ) -> AuditEntry:
        """Log an audit event."""
        entry_id = f"{datetime.now().timestamp()}_{action}_{agent_id}"
        
        # Create entry
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            event_type=event_type,
            agent_id=agent_id,
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            hash="",  # Will be calculated
            previous_hash=self._last_hash
        )
        
        # Calculate hash
        entry_data = json.dumps({
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "agent_id": entry.agent_id,
            "action": entry.action,
            "details": entry.details,
            "previous_hash": entry.previous_hash
        }, sort_keys=True)
        
        entry.hash = hashlib.sha256(entry_data.encode()).hexdigest()
        self._last_hash = entry.hash
        
        # Store entry
        self._entries.append(entry)
        
        # Persist if storage path provided
        if self.storage_path:
            self._persist_entry(entry)
        
        return entry
    
    def _persist_entry(self, entry: AuditEntry) -> None:
        """Persist entry to file."""
        if not self.storage_path:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        file_path = self.storage_path / f"{entry.entry_id}.json"
        with open(file_path, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
    
    def query(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Query audit entries."""
        entries = self._entries
        
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        
        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]
        
        return entries[-limit:]
    
    def verify_integrity(self) -> bool:
        """Verify hash chain integrity."""
        for i, entry in enumerate(self._entries):
            if i > 0:
                previous_entry = self._entries[i - 1]
                if entry.previous_hash != previous_entry.hash:
                    self.logger.error(
                        f"Hash chain broken at entry {entry.entry_id}"
                    )
                    return False
            
            # Recalculate hash
            entry_data = json.dumps({
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type,
                "agent_id": entry.agent_id,
                "action": entry.action,
                "details": entry.details,
                "previous_hash": entry.previous_hash
            }, sort_keys=True)
            
            calculated_hash = hashlib.sha256(entry_data.encode()).hexdigest()
            if calculated_hash != entry.hash:
                self.logger.error(f"Hash mismatch for entry {entry.entry_id}")
                return False
        
        return True
    
    def export(self, format: str = "json") -> str:
        """Export audit trail."""
        if format == "json":
            return json.dumps(
                [e.to_dict() for e in self._entries],
                indent=2
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")