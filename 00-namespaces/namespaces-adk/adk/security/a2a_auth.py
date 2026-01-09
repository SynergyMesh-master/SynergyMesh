"""
A2A Authentication: Implements agent-to-agent authentication.

This module provides authentication and trust establishment
for inter-agent communication.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from ..observability.logging import Logger


class A2AAuthMethod(Enum):
    """Agent-to-agent authentication methods."""
    SHARED_SECRET = "shared_secret"
    PUBLIC_KEY = "public_key"
    MUTUAL_TLS = "mutual_tls"
    CHALLENGE_RESPONSE = "challenge_response"


@dataclass
class AgentIdentity:
    """Agent identity."""
    agent_id: str
    name: str
    public_key: Optional[str] = None
    shared_secret: Optional[str] = None
    trust_level: str = "medium"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "trust_level": self.trust_level,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class A2ACredential:
    """Agent-to-agent credential."""
    credential_id: str
    from_agent: str
    to_agent: str
    method: A2AAuthMethod
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if credential is expired."""
        return self.expires_at and datetime.now() >= self.expires_at


class A2AAuthenticator:
    """
    Authenticates agent-to-agent communication.
    
    Features:
    - Multiple authentication methods
    - Trust establishment
    - Credential management
    - Challenge-response authentication
    """
    
    def __init__(self):
        self.logger = Logger(name="security.a2a_auth")
        
        # Agent identities
        self._identities: Dict[str, AgentIdentity] = {}
        
        # Credentials
        self._credentials: Dict[str, A2ACredential] = {}
        
        # Shared secrets
        self._shared_secrets: Dict[tuple[str, str], str] = {}
        
        # Pending challenges
        self._challenges: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        public_key: Optional[str] = None,
        trust_level: str = "medium"
    ) -> AgentIdentity:
        """Register an agent identity."""
        identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            public_key=public_key,
            trust_level=trust_level
        )
        
        self._identities[agent_id] = identity
        return identity
    
    def establish_shared_secret(
        self,
        agent_a: str,
        agent_b: str,
        secret: str
    ) -> None:
        """Establish a shared secret between two agents."""
        self._shared_secrets[(agent_a, agent_b)] = secret
        self._shared_secrets[(agent_b, agent_a)] = secret
    
    def create_credential(
        self,
        from_agent: str,
        to_agent: str,
        method: A2AAuthMethod,
        expires_in_hours: int = 24
    ) -> A2ACredential:
        """Create an A2A credential."""
        credential_id = f"cred_{secrets.token_hex(16)}"
        
        credential = A2ACredential(
            credential_id=credential_id,
            from_agent=from_agent,
            to_agent=to_agent,
            method=method,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        )
        
        self._credentials[credential_id] = credential
        return credential
    
    def generate_challenge(self, for_agent: str) -> str:
        """Generate a challenge for authentication."""
        challenge = secrets.token_hex(32)
        
        self._challenges[challenge] = {
            "for_agent": for_agent,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=5)
        }
        
        return challenge
    
    def verify_challenge_response(
        self,
        challenge: str,
        response: str,
        agent_id: str
    ) -> bool:
        """Verify a challenge response."""
        challenge_data = self._challenges.get(challenge)
        
        if not challenge_data:
            return False
        
        if challenge_data["for_agent"] != agent_id:
            return False
        
        if datetime.now() >= challenge_data["expires_at"]:
            return False
        
        # Verify response using shared secret
        secret = self._shared_secrets.get((agent_id, "system"))
        if not secret:
            return False
        
        expected_response = hashlib.sha256(
            f"{challenge}{secret}".encode()
        ).hexdigest()
        
        return response == expected_response
    
    def authenticate_agent(
        self,
        agent_id: str,
        credential: Optional[A2ACredential] = None,
        challenge: Optional[str] = None,
        response: Optional[str] = None
    ) -> bool:
        """Authenticate an agent."""
        identity = self._identities.get(agent_id)
        if not identity:
            return False
        
        if credential:
            if credential.is_expired:
                return False
            
            if credential.to_agent != "system":
                return False
        
        if challenge and response:
            if not self.verify_challenge_response(challenge, response, agent_id):
                return False
        
        return True
    
    def get_agent_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent identity."""
        return self._identities.get(agent_id)