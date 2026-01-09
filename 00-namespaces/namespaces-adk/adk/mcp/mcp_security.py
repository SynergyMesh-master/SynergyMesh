"""
MCP Security: Implements security controls for MCP tool invocation.

This module provides authentication, authorization, and data privacy
controls for MCP tool invocations.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import secrets
import re

from ..security.auth import Authenticator
from ..security.permissioning import PermissionManager
from ..security.pii_filter import PIIFilter
from ..observability.logging import Logger


class AuthMethod(Enum):
    """Authentication methods."""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT = "jwt"
    MUTUAL_TLS = "mutual_tls"
    CUSTOM = "custom"


@dataclass
class AuthConfig:
    """Authentication configuration."""
    method: AuthMethod
    credentials: Dict[str, Any] = field(default_factory=dict)
    token_expiry: Optional[timedelta] = None
    refresh_enabled: bool = False


@dataclass
class AccessPolicy:
    """Access policy for tool invocation."""
    policy_id: str
    tool_name: str
    allowed_roles: Set[str] = field(default_factory=set)
    allowed_users: Set[str] = field(default_factory=set)
    denied_roles: Set[str] = field(default_factory=set)
    denied_users: Set[str] = field(default_factory=set)
    require_context: bool = False
    max_rate_per_minute: int = 100
    enabled: bool = True


@dataclass
class SecurityContext:
    """Security context for tool invocation."""
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPSecurity:
    """
    Security controls for MCP tool invocation.
    
    Features:
    - Authentication and authorization
    - Permission checking
    - Rate limiting
    - PII filtering
    - Audit logging
    - Token management
    """
    
    def __init__(
        self,
        authenticator: Optional[Authenticator] = None,
        permission_manager: Optional[PermissionManager] = None,
        pii_filter: Optional[PIIFilter] = None
    ):
        self.authenticator = authenticator
        self.permission_manager = permission_manager
        self.pii_filter = pii_filter
        
        self.logger = Logger(name="mcp.security")
        
        # Access policies
        self._policies: Dict[str, AccessPolicy] = {}
        
        # Rate limiting
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Token cache
        self._token_cache: Dict[str, Dict[str, Any]] = {}
    
    async def authenticate(
        self,
        credentials: Dict[str, Any],
        method: AuthMethod = AuthMethod.JWT
    ) -> Optional[SecurityContext]:
        """
        Authenticate a user or agent.
        
        Args:
            credentials: Authentication credentials
            method: Authentication method
            
        Returns:
            Security context if authenticated, None otherwise
        """
        if self.authenticator:
            return await self.authenticator.authenticate(credentials, method)
        
        # Simplified authentication
        token = credentials.get("token")
        if token:
            return SecurityContext(
                user_id=credentials.get("user_id"),
                roles=credentials.get("roles", []),
                session_id=credentials.get("session_id")
            )
        
        return None
    
    async def check_tool_permission(
        self,
        tool_name: str,
        context: Optional[SecurityContext] = None,
        invocation_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if tool invocation is permitted.
        
        Args:
            tool_name: Name of the tool
            context: Security context
            invocation_context: Additional invocation context
            
        Returns:
            True if permitted
        """
        # Get policy
        policy = self._policies.get(tool_name)
        
        if not policy:
            # Default deny
            self.logger.warning(f"No policy for tool: {tool_name}")
            return False
        
        if not policy.enabled:
            return False
        
        # Check deny lists first
        if context:
            if context.user_id in policy.denied_users:
                return False
            
            for role in context.roles:
                if role in policy.denied_roles:
                    return False
        
        # If no allow lists, permit by default
        if not policy.allowed_roles and not policy.allowed_users:
            return True
        
        # Check allow lists
        if context:
            if context.user_id in policy.allowed_users:
                return True
            
            for role in context.roles:
                if role in policy.allowed_roles:
                    return True
        
        return False
    
    async def check_rate_limit(
        self,
        tool_name: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if invocation rate limit is exceeded.
        
        Args:
            tool_name: Name of the tool
            user_id: User ID for per-user limits
            
        Returns:
            True if within limit
        """
        policy = self._policies.get(tool_name)
        
        if not policy:
            return True
        
        # Get or create rate limit tracker
        key = f"{tool_name}:{user_id or 'anonymous'}"
        
        if key not in self._rate_limits:
            self._rate_limits[key] = {
                "count": 0,
                "window_start": datetime.now(),
                "policy_max": policy.max_rate_per_minute
            }
        
        tracker = self._rate_limits[key]
        
        # Reset if window expired
        if datetime.now() - tracker["window_start"] > timedelta(minutes=1):
            tracker["count"] = 0
            tracker["window_start"] = datetime.now()
        
        # Check limit
        if tracker["count"] >= tracker["policy_max"]:
            self.logger.warning(
                f"Rate limit exceeded for {key}: "
                f"{tracker['count']}/{tracker['policy_max']}"
            )
            return False
        
        tracker["count"] += 1
        return True
    
    def add_policy(self, policy: AccessPolicy) -> None:
        """Add an access policy."""
        self._policies[policy.tool_name] = policy
        self.logger.info(f"Added policy for tool: {policy.tool_name}")
    
    def remove_policy(self, tool_name: str) -> bool:
        """Remove an access policy."""
        if tool_name in self._policies:
            del self._policies[tool_name]
            return True
        return False
    
    def get_policy(self, tool_name: str) -> Optional[AccessPolicy]:
        """Get an access policy."""
        return self._policies.get(tool_name)
    
    def list_policies(self) -> List[AccessPolicy]:
        """List all policies."""
        return list(self._policies.values())
    
    async def filter_pii(
        self,
        data: Dict[str, Any],
        context: Optional[SecurityContext] = None
    ) -> Dict[str, Any]:
        """
        Filter PII from data.
        
        Args:
            data: Data to filter
            context: Security context
            
        Returns:
            Filtered data
        """
        if self.pii_filter:
            return await self.pii_filter.filter(data, context)
        
        # Simplified PII filtering
        return data
    
    async def filter_tool_arguments(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[SecurityContext] = None
    ) -> Dict[str, Any]:
        """
        Filter PII from tool arguments.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            context: Security context
            
        Returns:
            Filtered arguments
        """
        return await self.filter_pii(arguments, context)
    
    async def filter_tool_result(
        self,
        tool_name: str,
        result: Dict[str, Any],
        context: Optional[SecurityContext] = None
    ) -> Dict[str, Any]:
        """
        Filter PII from tool result.
        
        Args:
            tool_name: Name of the tool
            result: Tool result
            context: Security context
            
        Returns:
            Filtered result
        """
        return await self.filter_pii(result, context)
    
    def generate_token(
        self,
        user_id: str,
        expiry: Optional[timedelta] = None
    ) -> str:
        """
        Generate an authentication token.
        
        Args:
            user_id: User ID
            expiry: Token expiry time
            
        Returns:
            Token string
        """
        token = secrets.token_urlsafe(32)
        
        self._token_cache[token] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + expiry if expiry else None
        }
        
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        """
        Validate an authentication token.
        
        Args:
            token: Token to validate
            
        Returns:
            User ID if valid, None otherwise
        """
        token_data = self._token_cache.get(token)
        
        if not token_data:
            return None
        
        # Check expiry
        if token_data["expires_at"] and datetime.now() > token_data["expires_at"]:
            del self._token_cache[token]
            return None
        
        return token_data["user_id"]
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke an authentication token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked
        """
        if token in self._token_cache:
            del self._token_cache[token]
            return True
        return False
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        return {
            "total_policies": len(self._policies),
            "enabled_policies": sum(1 for p in self._policies.values() if p.enabled),
            "active_tokens": len(self._token_cache),
            "rate_limit_trackers": len(self._rate_limits)
        }