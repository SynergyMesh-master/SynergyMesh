"""
Security Module: Authentication, authorization, and data privacy.

This package provides security capabilities including authentication,
A2A authentication, permissioning, and PII filtering.
"""

from .auth import (
    Authenticator,
    User,
    Session,
    AuthMethod
)
from .a2a_auth import (
    A2AAuthenticator,
    AgentIdentity,
    A2ACredential,
    A2AAuthMethod
)
from .permissioning import (
    PermissionManager,
    Role,
    Policy,
    Permission
)
from .pii_filter import (
    PIIFilter,
    PIIMatch,
    PIIType
)

__all__ = [
    # Authentication
    "Authenticator",
    "User",
    "Session",
    "AuthMethod",
    
    # A2A Authentication
    "A2AAuthenticator",
    "AgentIdentity",
    "A2ACredential",
    "A2AAuthMethod",
    
    # Permissioning
    "PermissionManager",
    "Role",
    "Policy",
    "Permission",
    
    # PII Filter
    "PIIFilter",
    "PIIMatch",
    "PIIType",
]