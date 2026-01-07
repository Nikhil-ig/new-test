"""
Action Types and Models
Define all action types and their request/response models
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ActionType(str, Enum):
    """All supported action types"""
    BAN = "ban"
    KICK = "kick"
    MUTE = "mute"
    UNMUTE = "unmute"
    PROMOTE = "promote"
    DEMOTE = "demote"
    WARN = "warn"
    PIN = "pin"
    UNPIN = "unpin"
    DELETE_MESSAGE = "delete_message"
    RESTRICT = "restrict"
    UNRESTRICT = "unrestrict"
    PURGE = "purge"
    SET_ROLE = "set_role"
    REMOVE_ROLE = "remove_role"
    LOCKDOWN = "lockdown"


class ActionStatus(str, Enum):
    """Action execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ActionRequest(BaseModel):
    """Base action request model"""
    action_type: ActionType
    group_id: int
    user_id: Optional[int] = None  # Optional for lockdown which doesn't need user_id
    message_id: Optional[int] = None  # For pin/unpin actions
    reason: Optional[str] = None
    duration_minutes: Optional[int] = None  # For mute/restrict
    title: Optional[str] = None  # For promote (admin title)
    initiated_by: Optional[int] = None  # Admin/bot that initiated
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = False


class ActionResponse(BaseModel):
    """Standardized action response"""
    action_id: str
    action_type: ActionType
    group_id: int
    user_id: int
    status: ActionStatus
    success: bool
    message: str
    error: Optional[str] = None
    timestamp: datetime
    execution_time_ms: Optional[float] = None
    retry_count: int = 0
    api_response: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = False


class ActionLog(BaseModel):
    """Log entry for database persistence"""
    action_id: str
    action_type: ActionType
    group_id: int
    user_id: int
    initiated_by: Optional[int] = None
    status: ActionStatus
    success: bool
    message: str
    error: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    retry_count: int = 0
    api_response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = False


# ============================================================================
# SPECIFIC ACTION REQUEST MODELS
# ============================================================================

class BanRequest(ActionRequest):
    """Ban user from group"""
    action_type: ActionType = ActionType.BAN
    until_date: Optional[int] = None  # Unix timestamp for temporary ban
    revoke_messages: bool = True

    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError('user_id must be positive')
        return v


class KickRequest(ActionRequest):
    """Kick user from group"""
    action_type: ActionType = ActionType.KICK
    revoke_messages: bool = False


class MuteRequest(ActionRequest):
    """Mute user in group"""
    action_type: ActionType = ActionType.MUTE
    duration: int = 3600  # Duration in seconds
    
    @validator('duration')
    def validate_duration(cls, v):
        if v < 60:
            raise ValueError('duration must be at least 60 seconds')
        return v


class UnmuteRequest(ActionRequest):
    """Unmute user in group"""
    action_type: ActionType = ActionType.UNMUTE


class PromoteRequest(ActionRequest):
    """Promote user to admin"""
    action_type: ActionType = ActionType.PROMOTE
    permissions: Optional[Dict[str, bool]] = None


class DemoteRequest(ActionRequest):
    """Demote admin to regular user"""
    action_type: ActionType = ActionType.DEMOTE


class WarnRequest(ActionRequest):
    """Warn user (increase warning count)"""
    action_type: ActionType = ActionType.WARN
    warn_count: int = 1
    auto_ban_after: Optional[int] = None  # Ban after N warnings

    @validator('warn_count')
    def validate_warn_count(cls, v):
        if v < 1:
            raise ValueError('warn_count must be at least 1')
        return v


class PinRequest(ActionRequest):
    """Pin message in group"""
    action_type: ActionType = ActionType.PIN
    message_id: int
    notify: bool = True

    @validator('message_id')
    def validate_message_id(cls, v):
        if v <= 0:
            raise ValueError('message_id must be positive')
        return v


class UnpinRequest(ActionRequest):
    """Unpin message from group"""
    action_type: ActionType = ActionType.UNPIN
    message_id: Optional[int] = None


class DeleteMessageRequest(ActionRequest):
    """Delete message from group"""
    action_type: ActionType = ActionType.DELETE_MESSAGE
    message_id: int

    @validator('message_id')
    def validate_message_id(cls, v):
        if v <= 0:
            raise ValueError('message_id must be positive')
        return v


class RestrictRequest(ActionRequest):
    """Restrict user permissions"""
    action_type: ActionType = ActionType.RESTRICT
    permissions: Dict[str, bool]
    until_date: Optional[int] = None


class UnrestrictRequest(ActionRequest):
    """Unrestrict user (restore full permissions)"""
    action_type: ActionType = ActionType.UNRESTRICT


class PurgeRequest(ActionRequest):
    """Purge messages from user"""
    action_type: ActionType = ActionType.PURGE
    message_count: int = 100
    hours_back: Optional[int] = None

    @validator('message_count')
    def validate_message_count(cls, v):
        if v < 1 or v > 10000:
            raise ValueError('message_count must be between 1 and 10000')
        return v


class SetRoleRequest(ActionRequest):
    """Set user role (custom roles)"""
    action_type: ActionType = ActionType.SET_ROLE
    role: str

    @validator('role')
    def validate_role(cls, v):
        if not v or len(v) > 50:
            raise ValueError('role must be 1-50 characters')
        return v


class RemoveRoleRequest(ActionRequest):
    """Remove user role"""
    action_type: ActionType = ActionType.REMOVE_ROLE
    role: str

    @validator('role')
    def validate_role(cls, v):
        if not v or len(v) > 50:
            raise ValueError('role must be 1-50 characters')
        return v
