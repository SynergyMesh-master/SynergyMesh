"""
Permissioning: Implements fine-grained permissioning for tools and resources.

This module provides role-based and attribute-based access control.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

from ..observability.logging import Logger


class Permission(Enum):
    """Standard permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DELETE = "delete"
    TOOL_INVOKE = "tool_invoke"
    WORKFLOW_START = "workflow_start"
    MEMORY_ACCESS = "memory_access"
    CONTEXT_MODIFY = "context_modify"


@dataclass
class Role:
    """A role."""
    role_id: str
    name: str
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "permissions": [p.value for p in self.permissions],
            "metadata": self.metadata
        }


@dataclass
class Policy:
    """An access policy."""
    policy_id: str
    resource: str
    allowed_roles: Set[str] = field(default_factory=set)
    allowed_permissions: Set[Permission] = field(default_factory=set)
    denied_roles: Set[str] = field(default_factory=set)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "resource": self.resource,
            "allowed_roles": list(self.allowed_roles),
            "allowed_permissions": [p.value for p in self.allowed_permissions],
            "denied_roles": list(self.denied_roles),
            "enabled": self.enabled
        }


class PermissionManager:
    """
    Manages permissions and access control.
    
    Features:
    - Role-based access control (RBAC)
    - Attribute-based access control (ABAC)
    - Policy evaluation
    - Permission caching
    - Audit logging
    """
    
    def __init__(self):
        self.logger = Logger(name="security.permissioning")
        
        # Roles
        self._roles: Dict[str, Role] = {}
        
        # User roles
        self._user_roles: Dict[str, Set[str]] = {}
        
        # Policies
        self._policies: Dict[str, Policy] = {}
        
        # Permission cache
        self._cache: Dict[tuple[str, str, Permission], bool] = {}
        
        # Initialize default roles
        self._initialize_default_roles()
    
    def _initialize_default_roles(self) -> None:
        """Initialize default roles."""
        # Admin role
        admin_role = Role(
            role_id="admin",
            name="Administrator",
            permissions=set(Permission)
        )
        self._roles[admin_role.role_id] = admin_role
        
        # User role
        user_role = Role(
            role_id="user",
            name="User",
            permissions={
                Permission.READ,
                Permission.TOOL_INVOKE,
                Permission.WORKFLOW_START
            }
        )
        self._roles[user_role.role_id] = user_role
        
        # Read-only role
        readonly_role = Role(
            role_id="readonly",
            name="Read Only",
            permissions={Permission.READ}
        )
        self._roles[readonly_role.role_id] = readonly_role
    
    def create_role(
        self,
        role_id: str,
        name: str,
        permissions: List[Permission]
    ) -> Role:
        """Create a role."""
        role = Role(
            role_id=role_id,
            name=name,
            permissions=set(permissions)
        )
        
        self._roles[role_id] = role
        return role
    
    def assign_role_to_user(self, user_id: str, role_id: str) -> None:
        """Assign a role to a user."""
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        
        self._user_roles[user_id].add(role_id)
    
    def revoke_role_from_user(self, user_id: str, role_id: str) -> None:
        """Revoke a role from a user."""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_id)
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get roles for a user."""
        role_ids = self._user_roles.get(user_id, set())
        return [self._roles[rid] for rid in role_ids if rid in self._roles]
    
    def create_policy(
        self,
        policy_id: str,
        resource: str,
        allowed_roles: Optional[List[str]] = None,
        allowed_permissions: Optional[List[Permission]] = None,
        denied_roles: Optional[List[str]] = None
    ) -> Policy:
        """Create an access policy."""
        policy = Policy(
            policy_id=policy_id,
            resource=resource,
            allowed_roles=set(allowed_roles or []),
            allowed_permissions=set(allowed_permissions or []),
            denied_roles=set(denied_roles or [])
        )
        
        self._policies[policy_id] = policy
        return policy
    
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if a user has a permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            resource: Resource (optional)
            
        Returns:
            True if permitted
        """
        cache_key = (user_id, resource or "*", permission)
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get user roles
        roles = self.get_user_roles(user_id)
        
        # Check each role
        for role in roles:
            # Check role permissions
            if permission in role.permissions:
                self._cache[cache_key] = True
                return True
        
        # Check resource policies
        if resource:
            for policy in self._policies.values():
                if not policy.enabled:
                    continue
                
                if policy.resource == resource:
                    # Check denied roles
                    user_role_ids = {r.role_id for r in roles}
                    if user_role_ids & policy.denied_roles:
                        self._cache[cache_key] = False
                        return False
                    
                    # Check allowed roles and permissions
                    if policy.allowed_roles and (user_role_ids & policy.allowed_roles):
                        if permission in policy.allowed_permissions or not policy.allowed_permissions:
                            self._cache[cache_key] = True
                            return True
        
        self._cache[cache_key] = False
        return False
    
    def require_permission(self, permission: Permission, resource: Optional[str] = None):
        """Decorator to require a permission."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                user_id = kwargs.get("user_id")
                if not user_id:
                    raise PermissionError("User ID required")
                
                pm = kwargs.get("permission_manager")
                if not pm:
                    raise PermissionError("Permission manager required")
                
                if not pm.check_permission(user_id, permission, resource):
                    raise PermissionError(f"Permission denied: {permission.value}")
                
                return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                user_id = kwargs.get("user_id")
                if not user_id:
                    raise PermissionError("User ID required")
                
                pm = kwargs.get("permission_manager")
                if not pm:
                    raise PermissionError("Permission manager required")
                
                if not pm.check_permission(user_id, permission, resource):
                    raise PermissionError(f"Permission denied: {permission.value}")
                
                return func(*args, **kwargs)
            
            return async_wrapper if kwargs.get("async") else sync_wrapper
        return decorator
    
    def clear_cache(self) -> None:
        """Clear permission cache."""
        self._cache.clear()