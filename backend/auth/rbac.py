"""
Role-Based Access Control (RBAC) for CEP Machine
Production-ready permission system with roles and access control
"""

from enum import Enum
from typing import List, Set, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field
from functools import wraps
from fastapi import HTTPException, status, Depends
import logging

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    """Available permissions in the system"""
    # Prospect permissions
    READ_PROSPECTS = "read_prospects"
    WRITE_PROSPECTS = "write_prospects"
    DELETE_PROSPECTS = "delete_prospects"
    
    # Tool permissions
    EXECUTE_TOOLS = "execute_tools"
    MANAGE_TOOLS = "manage_tools"
    
    # Agent permissions
    VIEW_AGENTS = "view_agents"
    MANAGE_AGENTS = "manage_agents"
    EXECUTE_AGENTS = "execute_agents"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_ANALYTICS = "export_analytics"
    
    # User management permissions
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    
    # System permissions
    VIEW_SYSTEM = "view_system"
    MANAGE_SYSTEM = "manage_system"
    ADMIN_ACCESS = "admin_access"
    
    # File permissions
    UPLOAD_FILES = "upload_files"
    DELETE_FILES = "delete_files"
    
    # Integration permissions
    MANAGE_INTEGRATIONS = "manage_integrations"
    VIEW_INTEGRATIONS = "view_integrations"

class Role(BaseModel):
    """Role definition with permissions"""
    name: str
    description: str
    permissions: Set[Permission]
    is_system_role: bool = False
    
    class Config:
        use_enum_values = True
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        return any(p in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if role has all of the specified permissions"""
        return all(p in self.permissions for p in permissions)

# Define system roles
ROLES: Dict[str, Role] = {
    "viewer": Role(
        name="viewer",
        description="Read-only access to prospects and analytics",
        permissions={
            Permission.READ_PROSPECTS,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_AGENTS,
            Permission.VIEW_INTEGRATIONS
        },
        is_system_role=True
    ),
    "operator": Role(
        name="operator",
        description="Can execute tools and manage prospects",
        permissions={
            Permission.READ_PROSPECTS,
            Permission.WRITE_PROSPECTS,
            Permission.EXECUTE_TOOLS,
            Permission.EXECUTE_AGENTS,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_AGENTS,
            Permission.UPLOAD_FILES,
            Permission.VIEW_INTEGRATIONS
        },
        is_system_role=True
    ),
    "manager": Role(
        name="manager",
        description="Can manage agents and export analytics",
        permissions={
            Permission.READ_PROSPECTS,
            Permission.WRITE_PROSPECTS,
            Permission.DELETE_PROSPECTS,
            Permission.EXECUTE_TOOLS,
            Permission.MANAGE_TOOLS,
            Permission.VIEW_AGENTS,
            Permission.MANAGE_AGENTS,
            Permission.EXECUTE_AGENTS,
            Permission.VIEW_ANALYTICS,
            Permission.EXPORT_ANALYTICS,
            Permission.VIEW_USERS,
            Permission.UPLOAD_FILES,
            Permission.DELETE_FILES,
            Permission.VIEW_INTEGRATIONS,
            Permission.MANAGE_INTEGRATIONS
        },
        is_system_role=True
    ),
    "admin": Role(
        name="admin",
        description="Full system access",
        permissions={perm for perm in Permission},
        is_system_role=True
    )
}

class RBACUser(BaseModel):
    """User model with RBAC support"""
    id: str
    email: str
    name: Optional[str] = None
    role_name: str = "viewer"
    mfa_enabled: bool = False
    is_active: bool = True
    custom_permissions: Set[Permission] = Field(default_factory=set)
    
    class Config:
        use_enum_values = True
    
    @property
    def role(self) -> Role:
        """Get the user's role"""
        return ROLES.get(self.role_name, ROLES["viewer"])
    
    @property
    def all_permissions(self) -> Set[Permission]:
        """Get all permissions (role + custom)"""
        return self.role.permissions | self.custom_permissions
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        if not self.is_active:
            return False
        return permission in self.all_permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        if not self.is_active:
            return False
        return any(p in self.all_permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        if not self.is_active:
            return False
        return all(p in self.all_permissions for p in permissions)
    
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role_name == "admin" or Permission.ADMIN_ACCESS in self.all_permissions

class RBACManager:
    """Manager for RBAC operations"""
    
    def __init__(self):
        self.roles = ROLES.copy()
        # In production, custom roles would be loaded from database
        self._custom_roles: Dict[str, Role] = {}
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """Get a role by name"""
        return self.roles.get(role_name) or self._custom_roles.get(role_name)
    
    def list_roles(self) -> List[Role]:
        """List all available roles"""
        all_roles = list(self.roles.values()) + list(self._custom_roles.values())
        return all_roles
    
    def create_custom_role(
        self, 
        name: str, 
        description: str, 
        permissions: Set[Permission]
    ) -> Role:
        """Create a custom role"""
        if name in self.roles or name in self._custom_roles:
            raise ValueError(f"Role '{name}' already exists")
        
        role = Role(
            name=name,
            description=description,
            permissions=permissions,
            is_system_role=False
        )
        self._custom_roles[name] = role
        logger.info(f"Custom role created: {name}")
        return role
    
    def delete_custom_role(self, name: str) -> bool:
        """Delete a custom role"""
        if name in self.roles:
            raise ValueError(f"Cannot delete system role '{name}'")
        
        if name in self._custom_roles:
            del self._custom_roles[name]
            logger.info(f"Custom role deleted: {name}")
            return True
        return False
    
    def update_custom_role(
        self, 
        name: str, 
        description: Optional[str] = None,
        permissions: Optional[Set[Permission]] = None
    ) -> Optional[Role]:
        """Update a custom role"""
        if name in self.roles:
            raise ValueError(f"Cannot modify system role '{name}'")
        
        if name not in self._custom_roles:
            return None
        
        role = self._custom_roles[name]
        if description:
            role.description = description
        if permissions is not None:
            role.permissions = permissions
        
        logger.info(f"Custom role updated: {name}")
        return role
    
    def check_permission(self, user: RBACUser, permission: Permission) -> bool:
        """Check if a user has a specific permission"""
        return user.has_permission(permission)
    
    def require_permission(self, permission: Permission):
        """Decorator to require a specific permission"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, current_user: RBACUser = None, **kwargs):
                if current_user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not current_user.has_permission(permission):
                    logger.warning(
                        f"Permission denied: {current_user.email} tried to access "
                        f"resource requiring {permission.value}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value} required"
                    )
                
                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator
    
    def require_any_permission(self, permissions: List[Permission]):
        """Decorator to require any of the specified permissions"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, current_user: RBACUser = None, **kwargs):
                if current_user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not current_user.has_any_permission(permissions):
                    perm_names = [p.value for p in permissions]
                    logger.warning(
                        f"Permission denied: {current_user.email} tried to access "
                        f"resource requiring any of {perm_names}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: one of {perm_names} required"
                    )
                
                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator
    
    def require_all_permissions(self, permissions: List[Permission]):
        """Decorator to require all of the specified permissions"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, current_user: RBACUser = None, **kwargs):
                if current_user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not current_user.has_all_permissions(permissions):
                    perm_names = [p.value for p in permissions]
                    logger.warning(
                        f"Permission denied: {current_user.email} tried to access "
                        f"resource requiring all of {perm_names}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: all of {perm_names} required"
                    )
                
                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator
    
    def require_admin(self):
        """Decorator to require admin access"""
        return self.require_permission(Permission.ADMIN_ACCESS)

# Global RBAC manager
rbac_manager = RBACManager()

# Dependency functions for FastAPI
def get_permission_checker(permission: Permission):
    """Create a dependency that checks for a specific permission"""
    async def check_permission(current_user: RBACUser = Depends()):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required"
            )
        return current_user
    return check_permission

def get_role_checker(role_name: str):
    """Create a dependency that checks for a specific role"""
    async def check_role(current_user: RBACUser = Depends()):
        if current_user.role_name != role_name and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        return current_user
    return check_role
