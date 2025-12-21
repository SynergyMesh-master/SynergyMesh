#!/usr/bin/env python3
"""
AAPS SuperAgent - Multi-Agent Orchestrator

SuperAgent is the central coordinator in the multi-agent MPC architecture.
It handles message routing, state machine management, and agent orchestration.

Key Responsibilities:
- Message routing and distribution
- Incident lifecycle state machine management
- Agent coordination and decision making
- Audit trail and provenance tracking
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("super-agent")

# Data Models
class MessageType(str, Enum):
    INCIDENT_SIGNAL = "IncidentSignal"
    RCA_REPORT = "RCAReport"
    FIX_PROPOSAL = "FixProposal"
    VERIFICATION_REPORT = "VerificationReport"
    APPROVAL_DECISION = "ApprovalDecision"
    EXECUTION_ORDER = "ExecutionOrder"
    EXECUTION_RESULT = "ExecutionResult"
    EVIDENCE_BUNDLE_REF = "EvidenceBundleRef"
    KNOWLEDGE_ARTIFACT_PUBLISHED = "KnowledgeArtifactPublished"

class IncidentState(str, Enum):
    OPEN = "OPEN"
    TRIAGE = "TRIAGE"
    RCA = "RCA"
    PROPOSE = "PROPOSE"
    VERIFY = "VERIFY"
    APPROVE = "APPROVE"
    EXECUTE = "EXECUTE"
    VALIDATE = "VALIDATE"
    ROLLBACK = "ROLLBACK"
    CLOSE = "CLOSE"
    LEARN = "LEARN"

class Urgency(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

@dataclass
class MessageMetadata:
    trace_id: str
    span_id: str
    timestamp: str
    source_agent: str
    target_agent: str
    message_type: MessageType
    schema_version: str = "v1.0.0"
    idempotency_key: Optional[str] = None
    signature: Optional[str] = None

@dataclass
class MessageContext:
    namespace: str
    cluster: str
    urgency: Optional[Urgency] = None
    constraints_ref: Optional[str] = None

class MessageEnvelope(BaseModel):
    meta: Dict[str, Any]
    context: Dict[str, Any]
    payload: Dict[str, Any]

@dataclass
class Incident:
    incident_id: str
    trace_id: str
    state: IncidentState
    incident_type: str
    severity: str
    affected_resources: List[str]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]

# SuperAgent Core
class SuperAgent:
    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self.message_handlers = {
            MessageType.INCIDENT_SIGNAL: self.handle_incident_signal,
            MessageType.RCA_REPORT: self.handle_rca_report,
            MessageType.FIX_PROPOSAL: self.handle_fix_proposal,
            MessageType.VERIFICATION_REPORT: self.handle_verification_report,
            MessageType.EXECUTION_RESULT: self.handle_execution_result,
        }
        
    def generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return f"axm-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4()}"
    
    def generate_span_id(self) -> str:
        """Generate unique span ID"""
        return str(uuid.uuid4())
    
    def validate_message_envelope(self, envelope: MessageEnvelope) -> bool:
        """Validate message envelope structure and required fields"""
        try:
            meta = envelope.meta
            context = envelope.context
            payload = envelope.payload
            
            # Required fields validation
            required_meta_fields = ["trace_id", "source_agent", "target_agent", "message_type"]
            for field in required_meta_fields:
                if field not in meta:
                    logger.error(f"Missing required meta field: {field}")
                    return False
            
            required_context_fields = ["namespace", "cluster"]
            for field in required_context_fields:
                if field not in context:
                    logger.error(f"Missing required context field: {field}")
                    return False
            
            # Validate message type
            try:
                MessageType(meta["message_type"])
            except ValueError:
                logger.error(f"Invalid message type: {meta['message_type']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Message validation failed: {e}")
            return False
    
    def route_message(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Route message to appropriate handler"""
        try:
            message_type = MessageType(envelope.meta["message_type"])
            
            if message_type in self.message_handlers:
                return self.message_handlers[message_type](envelope)
            else:
                logger.warning(f"No handler for message type: {message_type}")
                return {"status": "no_handler", "message_type": message_type.value}
                
        except Exception as e:
            # Log full exception details server-side but avoid exposing them to the caller
            logger.exception("Message routing failed")
            return {"status": "error", "error": "Message routing failed"}
    
    def handle_incident_signal(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handle incoming incident signal"""
        trace_id = envelope.meta["trace_id"]
        payload = envelope.payload
        
        # Create or update incident
        incident_id = payload.get("incident_id") or trace_id
        incident = Incident(
            incident_id=incident_id,
            trace_id=trace_id,
            state=IncidentState.OPEN,
            incident_type=payload.get("incident_type"),
            severity=payload.get("severity"),
            affected_resources=payload.get("affected_resources", []),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            metadata=payload.get("metadata", {})
        )
        
        self.incidents[incident_id] = incident
        
        # State transition: OPEN -> TRIAGE
        incident.state = IncidentState.TRIAGE
        incident.updated_at = datetime.now().isoformat()
        
        logger.info(f"Incident {incident_id} created and moved to TRIAGE")
        
        return {
            "status": "created",
            "incident_id": incident_id,
            "trace_id": trace_id,
            "state": incident.state.value,
            "next_action": "severity_assessment"
        }
    
    def handle_rca_report(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handle RCA report from ProblemSolverAgent"""
        trace_id = envelope.meta["trace_id"]
        payload = envelope.payload
        
        # Find incident by trace_id
        incident = None
        for inc in self.incidents.values():
            if inc.trace_id == trace_id:
                incident = inc
                break
        
        if not incident:
            return {"status": "error", "error": "Incident not found"}
        
        # State transition: RCA -> PROPOSE
        incident.state = IncidentState.PROPOSE
        incident.updated_at = datetime.now().isoformat()
        
        logger.info(f"Incident {incident.incident_id} RCA received, moving to PROPOSE")
        
        return {
            "status": "processed",
            "incident_id": incident.incident_id,
            "trace_id": trace_id,
            "state": incident.state.value,
            "next_action": "generate_fix_proposals"
        }
    
    def handle_fix_proposal(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handle fix proposal from ProblemSolverAgent"""
        trace_id = envelope.meta["trace_id"]
        payload = envelope.payload
        
        # Find incident by trace_id
        incident = None
        for inc in self.incidents.values():
            if inc.trace_id == trace_id:
                incident = inc
                break
        
        if not incident:
            return {"status": "error", "error": "Incident not found"}
        
        # State transition: PROPOSE -> VERIFY
        incident.state = IncidentState.VERIFY
        incident.updated_at = datetime.now().isoformat()
        
        logger.info(f"Incident {incident.incident_id} fix proposal received, moving to VERIFY")
        
        return {
            "status": "processed",
            "incident_id": incident.incident_id,
            "trace_id": trace_id,
            "state": incident.state.value,
            "next_action": "verification",
            "proposal_id": payload.get("proposal_id")
        }
    
    def handle_verification_report(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handle verification report from QualityAssuranceAgent"""
        trace_id = envelope.meta["trace_id"]
        payload = envelope.payload
        
        # Find incident by trace_id
        incident = None
        for inc in self.incidents.values():
            if inc.trace_id == trace_id:
                incident = inc
                break
        
        if not incident:
            return {"status": "error", "error": "Incident not found"}
        
        overall_status = payload.get("overall_status")
        
        if overall_status == "approved":
            # State transition: VERIFY -> APPROVE
            incident.state = IncidentState.APPROVE
            next_action = "prepare_execution"
        else:
            # State transition: VERIFY -> PROPOSE (for refinement)
            incident.state = IncidentState.PROPOSE
            next_action = "refine_proposals"
        
        incident.updated_at = datetime.now().isoformat()
        
        logger.info(f"Incident {incident.incident_id} verification {overall_status}, moving to {incident.state.value}")
        
        return {
            "status": "processed",
            "incident_id": incident.incident_id,
            "trace_id": trace_id,
            "state": incident.state.value,
            "verification_status": overall_status,
            "next_action": next_action
        }
    
    def handle_execution_result(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """Handle execution result from MaintenanceAgent"""
        trace_id = envelope.meta["trace_id"]
        payload = envelope.payload
        
        # Find incident by trace_id
        incident = None
        for inc in self.incidents.values():
            if inc.trace_id == trace_id:
                incident = inc
                break
        
        if not incident:
            return {"status": "error", "error": "Incident not found"}
        
        execution_status = payload.get("status")
        
        if execution_status == "success":
            # State transition: EXECUTE -> VALIDATE
            incident.state = IncidentState.VALIDATE
            next_action = "validation"
        else:
            # State transition: EXECUTE -> ROLLBACK
            incident.state = IncidentState.ROLLBACK
            next_action = "rollback"
        
        incident.updated_at = datetime.now().isoformat()
        
        logger.info(f"Incident {incident.incident_id} execution {execution_status}, moving to {incident.state.value}")
        
        return {
            "status": "processed",
            "incident_id": incident.incident_id,
            "trace_id": trace_id,
            "state": incident.state.value,
            "execution_status": execution_status,
            "next_action": next_action
        }
    
    def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an incident"""
        if incident_id in self.incidents:
            incident = self.incidents[incident_id]
            return {
                "incident_id": incident.incident_id,
                "trace_id": incident.trace_id,
                "state": incident.state.value,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "created_at": incident.created_at,
                "updated_at": incident.updated_at,
                "affected_resources": incident.affected_resources
            }
        return None
    
    def list_incidents(self) -> List[Dict[str, Any]]:
        """List all incidents"""
        return [self.get_incident_status(incident_id) for incident_id in self.incidents.keys()]

# FastAPI Application
app = FastAPI(
    title="AAPS SuperAgent",
    description="Multi-Agent Orchestrator for AAPS Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SuperAgent
super_agent = SuperAgent()

@app.post("/message")
async def receive_message(message: MessageEnvelope):
    """Receive and route messages from other agents"""
    try:
        # Validate message envelope
        if not super_agent.validate_message_envelope(message):
            raise HTTPException(status_code=400, detail="Invalid message envelope")
        
        # Route message to appropriate handler
        trace_id = message.meta["trace_id"]
        result = super_agent.route_message(message)
        
        logger.info(f"Message processed: trace_id={trace_id}, result={result}")
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "processing_result": result
        }
        
    except Exception as e:
        # Log the full exception details server-side, but return a generic error message
        logger.exception("Message processing failed")
        raise HTTPException(status_code=500, detail="Message processing failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "incidents_count": len(super_agent.incidents)
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "message_handlers": list(super_agent.message_handlers.keys())
    }

@app.get("/incidents")
async def list_incidents():
    """List all incidents"""
    incidents = super_agent.list_incidents()
    return {
        "incidents": incidents,
        "count": len(incidents),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get specific incident details"""
    incident = super_agent.get_incident_status(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@app.get("/metrics")
async def get_metrics():
    """Get basic metrics"""
    return {
        "total_incidents": len(super_agent.incidents),
        "incidents_by_state": {
            state.value: sum(1 for inc in super_agent.incidents.values() if inc.state == state)
            for state in IncidentState
        },
        "message_types_supported": [mt.value for mt in MessageType],
        "uptime": "TODO",  # Implement uptime tracking
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )