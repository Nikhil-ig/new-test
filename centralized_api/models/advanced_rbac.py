"""
Advanced RBAC Models for Superadmin and Group Admin Management

Defines:
- Role hierarchy (Superadmin > Owner > Admin > Member)
- Permission models for different roles
- Action tracking with full audit trail
- Group and User management models
- RBAC enforcement models
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field, validator


# ============ ENUMS ============

class UserRole(str, Enum):
    """Role hierarchy in the system"""
    SUPERADMIN = "superadmin"      # Can manage everything globally
    OWNER = "owner"                # Can manage only their group
    ADMIN = "admin"                # Can execute actions in their group
    MODERATOR = "moderator"        # Can execute limited actions
    MEMBER = "member"              # No special permissions


class GlobalPermission(str, Enum):
    """Global permissions for superadmins"""
    MANAGE_SUPERADMINS = "manage_superadmins"
    VIEW_ALL_GROUPS = "view_all_groups"
    MANAGE_ALL_GROUPS = "manage_all_groups"
    MANAGE_GROUP_OWNERS = "manage_group_owners"
    VIEW_SYSTEM_STATS = "view_system_stats"
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    VIEW_ALL_AUDIT_LOGS = "view_all_audit_logs"
    MANAGE_BOT_SETTINGS = "manage_bot_settings"


class GroupPermission(str, Enum):
    """Group-level permissions"""
    VIEW_GROUP = "view_group"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_ADMINS = "manage_admins"
    MANAGE_BLACKLIST = "manage_blacklist"
    MANAGE_RULES = "manage_rules"
    MANAGE_WELCOME = "manage_welcome"
    MANAGE_AUTO_MOD = "manage_auto_mod"
    VIEW_LOGS = "view_logs"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_WARNS = "manage_warns"
    MANAGE_BANS = "manage_bans"
    EXECUTE_BAN = "execute_ban"
    EXECUTE_KICK = "execute_kick"
    EXECUTE_MUTE = "execute_mute"
    EXECUTE_PROMOTE = "execute_promote"
    EXECUTE_DEMOTE = "execute_demote"
    EXECUTE_PIN = "execute_pin"
    EXECUTE_DELETE = "execute_delete"


class ActionType(str, Enum):
    """Types of moderation actions"""
    BAN = "ban"
    UNBAN = "unban"
    KICK = "kick"
    MUTE = "mute"
    UNMUTE = "unmute"
    PROMOTE = "promote"
    DEMOTE = "demote"
    PIN = "pin"
    UNPIN = "unpin"
    DELETE = "delete"
    WARN = "warn"


class ActionStatus(str, Enum):
    """Status of action execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============ PERMISSION DEFINITIONS ============

# Map roles to their default permissions
ROLE_PERMISSIONS: Dict[UserRole, Set[GroupPermission]] = {
    UserRole.SUPERADMIN: set(GroupPermission),  # All permissions
    UserRole.OWNER: {
        GroupPermission.VIEW_GROUP,
        GroupPermission.MANAGE_MEMBERS,
        GroupPermission.MANAGE_ADMINS,
        GroupPermission.MANAGE_BLACKLIST,
        GroupPermission.MANAGE_RULES,
        GroupPermission.MANAGE_WELCOME,
        GroupPermission.MANAGE_AUTO_MOD,
        GroupPermission.MANAGE_SETTINGS,
        GroupPermission.MANAGE_WARNS,
        GroupPermission.MANAGE_BANS,
        GroupPermission.VIEW_LOGS,
        GroupPermission.EXECUTE_BAN,
        GroupPermission.EXECUTE_KICK,
        GroupPermission.EXECUTE_MUTE,
        GroupPermission.EXECUTE_PROMOTE,
        GroupPermission.EXECUTE_DEMOTE,
        GroupPermission.EXECUTE_PIN,
        GroupPermission.EXECUTE_DELETE,
    },
    UserRole.ADMIN: {
        GroupPermission.VIEW_GROUP,
        GroupPermission.MANAGE_MEMBERS,
        GroupPermission.VIEW_LOGS,
        GroupPermission.EXECUTE_BAN,
        GroupPermission.EXECUTE_KICK,
        GroupPermission.EXECUTE_MUTE,
        GroupPermission.EXECUTE_PROMOTE,
        GroupPermission.EXECUTE_PIN,
        GroupPermission.EXECUTE_DELETE,
    },
    UserRole.MODERATOR: {
        GroupPermission.VIEW_GROUP,
        GroupPermission.EXECUTE_KICK,
        GroupPermission.EXECUTE_MUTE,
    },
    UserRole.MEMBER: {
        GroupPermission.VIEW_GROUP,
    },
}

# Role hierarchy (lower number = higher level)
ROLE_HIERARCHY = {
    UserRole.SUPERADMIN: 1,
    UserRole.OWNER: 2,
    UserRole.ADMIN: 3,
    UserRole.MODERATOR: 4,
    UserRole.MEMBER: 5,
}


# ============ BASE MODELS ============

class PermissionSet(BaseModel):
    """Set of permissions for a role"""
    permissions: List[GroupPermission] = Field(default_factory=list)
    
    def has_permission(self, permission: GroupPermission) -> bool:
        """Check if permission exists"""
        return permission in self.permissions
    
    def add_permission(self, permission: GroupPermission) -> None:
        """Add a permission"""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: GroupPermission) -> None:
        """Remove a permission"""
        if permission in self.permissions:
            self.permissions.remove(permission)


class UserPermissions(BaseModel):
    """User permissions in a specific group"""
    user_id: int
    group_id: int
    role: UserRole = UserRole.MEMBER
    permissions: List[GroupPermission] = Field(default_factory=list)
    custom_permissions: bool = False  # True if permissions were customized
    assigned_by: Optional[int] = None
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    
    def has_permission(self, permission: GroupPermission) -> bool:
        """Check if user has a specific permission"""
        if self.role == UserRole.SUPERADMIN:
            return True
        return permission in self.permissions or permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def can_manage(self, target_role: UserRole) -> bool:
        """Check if user can manage someone with target_role"""
        user_level = ROLE_HIERARCHY.get(self.role, 999)
        target_level = ROLE_HIERARCHY.get(target_role, 999)
        return user_level < target_level  # Lower number = higher rank


# ============ GROUP MODELS ============

class GroupMember(BaseModel):
    """Member in a group"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    permissions: List[GroupPermission] = Field(default_factory=list)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    warn_count: int = 0
    ban_expires_at: Optional[datetime] = None


class GroupSettings(BaseModel):
    """Settings for a group"""
    group_id: int
    group_name: Optional[str] = None
    group_description: Optional[str] = None
    auto_moderation_enabled: bool = True
    welcome_message_enabled: bool = False
    welcome_message: Optional[str] = None
    rules_enabled: bool = False
    rules_text: Optional[str] = None
    max_warns_before_ban: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GroupInfo(BaseModel):
    """Complete group information"""
    group_id: int
    group_name: Optional[str] = None
    owner_id: int
    owner_name: Optional[str] = None
    admin_count: int = 0
    member_count: int = 0
    settings: GroupSettings = Field(default_factory=lambda: GroupSettings(group_id=0))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GroupAdmin(BaseModel):
    """Admin in a group"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    role: UserRole = UserRole.ADMIN
    permissions: List[GroupPermission] = Field(default_factory=list)
    can_ban: bool = True
    can_kick: bool = True
    can_mute: bool = True
    can_warn: bool = False
    can_promote: bool = False
    can_delete_messages: bool = False
    can_pin_messages: bool = False
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[int] = None
    active: bool = True


# ============ ACTION MODELS ============

class ActionMetadata(BaseModel):
    """Additional metadata for an action"""
    duration_minutes: Optional[int] = None
    duration_seconds: Optional[int] = None
    until_date: Optional[int] = None
    message_text: Optional[str] = None
    target_message_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    custom_data: Optional[Dict[str, Any]] = None


class ActionAuditLog(BaseModel):
    """Audit log entry for an action"""
    action_id: str
    action_type: ActionType
    group_id: int
    user_id: int
    username: Optional[str] = None
    target_user_id: int
    target_username: Optional[str] = None
    status: ActionStatus = ActionStatus.SUCCESS
    reason: Optional[str] = None
    initiated_by: Optional[int] = None
    executed_by: Optional[str] = None
    execution_time_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[ActionMetadata] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ActionRequest(BaseModel):
    """Request to execute an action"""
    action_type: ActionType
    group_id: int
    user_id: int
    reason: Optional[str] = None
    initiated_by: int
    metadata: Optional[ActionMetadata] = None
    
    @validator('group_id', 'user_id', 'initiated_by')
    def validate_ids(cls, v):
        if v <= 0:
            raise ValueError("IDs must be positive integers")
        return v


class ActionResponse(BaseModel):
    """Response from executing an action"""
    action_id: str
    status: ActionStatus = ActionStatus.SUCCESS
    success: bool = True
    message: str
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class BatchActionRequest(BaseModel):
    """Request to execute multiple actions"""
    actions: List[ActionRequest]
    execute_sequentially: bool = False
    stop_on_error: bool = True


# ============ USER MODELS ============

class GlobalAdminUser(BaseModel):
    """A global superadmin user"""
    user_id: int
    username: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    is_superadmin: bool = True
    is_active: bool = True
    global_permissions: List[GlobalPermission] = Field(default_factory=lambda: list(GlobalPermission))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    login_count: int = 0


class LocalAdminUser(BaseModel):
    """A group admin user"""
    user_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.ADMIN
    managed_groups: List[int] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


# ============ DASHBOARD MODELS ============

class DashboardStats(BaseModel):
    """Statistics for dashboard"""
    total_groups: int = 0
    total_members: int = 0
    total_actions_today: int = 0
    total_warnings: int = 0
    total_bans: int = 0
    active_mutes: int = 0
    total_admins: int = 0


class GroupDashboard(BaseModel):
    """Group dashboard data"""
    group_id: int
    group_name: Optional[str] = None
    stats: DashboardStats = Field(default_factory=DashboardStats)
    recent_actions: List[ActionAuditLog] = Field(default_factory=list)
    admins: List[GroupAdmin] = Field(default_factory=list)
    settings: GroupSettings = Field(default_factory=lambda: GroupSettings(group_id=0))


class SuperadminDashboard(BaseModel):
    """Superadmin dashboard with all groups"""
    total_stats: DashboardStats = Field(default_factory=DashboardStats)
    groups_data: List[GroupDashboard] = Field(default_factory=list)
    system_health: Dict[str, Any] = Field(default_factory=dict)
    recent_global_actions: List[ActionAuditLog] = Field(default_factory=list)


# ============ RESPONSE MODELS ============

class UserResponse(BaseModel):
    """Response containing user info"""
    user_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    is_superadmin: bool = False
    is_active: bool = True
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class GroupResponse(BaseModel):
    """Response containing group info"""
    group_id: int
    group_name: Optional[str] = None
    owner_id: int
    owner_username: Optional[str] = None
    admin_count: int = 0
    member_count: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdminResponse(BaseModel):
    """Response containing admin info"""
    user_id: int
    username: str
    first_name: Optional[str] = None
    role: UserRole = UserRole.ADMIN
    group_id: int
    permissions: List[GroupPermission] = Field(default_factory=list)
    is_active: bool = True
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


# ============ FILTER MODELS ============

class ActionFilter(BaseModel):
    """Filters for searching actions"""
    group_id: Optional[int] = None
    user_id: Optional[int] = None
    action_type: Optional[ActionType] = None
    status: Optional[ActionStatus] = None
    initiated_by: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class AdminFilter(BaseModel):
    """Filters for searching admins"""
    group_id: Optional[int] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    limit: int = 50
    offset: int = 0
