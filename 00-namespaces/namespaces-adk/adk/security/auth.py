"""
Authentication: Implements authentication mechanisms for agents and users.

This module provides authentication, token management, and
session handling.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib

from ..observability.logging import Logger


class AuthMethod(Enum):
    """Authentication methods."""
    PASSWORD = "password"
    TOKEN = "token"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    CERTIFICATE = "certificate"


@dataclass
class User:
    """A user."""
    user_id: str
    username: str
    email: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


@dataclass
class Session:
    """A user session."""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "metadata": self.metadata
        }


class Authenticator:
    """
    Authenticates users and agents.
    
    Features:
    - Multiple authentication methods
    - Session management
    - Token generation
    - Password hashing
    """
    
    def __init__(self):
        self.logger = Logger(name="security.auth")
        
        # User storage
        self._users: Dict[str, Any] = {}
        
        # Session storage
        self._sessions: Dict[str, Session] = {}
        
        # Token storage
        self._tokens: Dict[str, Dict[str, Any]] = {}
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: Optional[List[str]] = None
    ) -> User:
        """Create a new user."""
        user_id = f"user_{username}_{secrets.token_hex(8)}"
        
        # Hash password
        password_hash = self._hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles or [],
            permissions=[]
        )
        
        # Store user with password hash
        self._users[user_id] = user
        self._users[f"{user_id}_pwd"] = password_hash
        
        return user
    
    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, user_id: str, password: str) -> bool:
        """Verify a password."""
        password_hash = self._users.get(f"{user_id}_pwd")
        if not password_hash:
            return False
        
        return self._hash_password(password) == password_hash
    
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        method: AuthMethod = AuthMethod.TOKEN
    ) -> Optional[Dict[str, Any]]:
        """Authenticate a user or agent."""
        if method == AuthMethod.PASSWORD:
            username = credentials.get("username")
            password = credentials.get("password")
            
            user = self._get_user_by_username(username)
            if not user:
                return None
            
            if not self.verify_password(user.user_id, password):
                return None
            
            # Update last login
            user.last_login = datetime.now()
            
            return {
                "user_id": user.user_id,
                "roles": user.roles,
                "session_id": None
            }
        
        elif method == AuthMethod.TOKEN:
            token = credentials.get("token")
            token_data = self._tokens.get(token)
            
            if not token_data:
                return None
            
            # Check expiration
            if token_data.get("expires_at") and datetime.now() >= token_data["expires_at"]:
                return None
            
            user = self._users.get(token_data["user_id"])
            if not user:
                return None
            
            return {
                "user_id": user.user_id,
                "roles": user.roles,
                "session_id": token_data.get("session_id")
            }
        
        return None
    
    def create_session(
        self,
        user_id: str,
        duration_hours: int = 24,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a session."""
        session_id = secrets.token_urlsafe(32)
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=duration_hours),
            metadata=metadata or {}
        )
        
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session."""
        session = self._sessions.get(session_id)
        if session and session.is_expired:
            del self._sessions[session_id]
            return None
        return session
    
    def revoke_session(self, session_id: str) -> None:
        """Revoke a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def generate_token(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> str:
        """Generate an authentication token."""
        token = secrets.token_urlsafe(64)
        
        self._tokens[token] = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=expires_in_hours)
        }
        
        return token
    
    def revoke_token(self, token: str) -> None:
        """Revoke a token."""
        if token in self._tokens:
            del self._tokens[token]
    
    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self._users.values():
            if isinstance(user, User) and user.username == username:
                return user
        return None