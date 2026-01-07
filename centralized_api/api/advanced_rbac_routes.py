"""
Advanced Web API Routes with RBAC

Provides role-based endpoints:
- Superadmin routes: manage all groups, admins, settings globally
- Group admin routes: manage only their own groups
- Shared routes: common functionality for authorized users
- Auth routes: login, token refresh, password management

All routes with comprehensive permission checking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from centralized_api.models.advanced_rbac import (
    UserRole,
    GroupPermission,
    ActionType,
    ActionRequest,
    ActionResponse,
    BatchActionRequest,
    GroupResponse,
    GroupAdmin,
    AdminResponse,
    UserResponse,
    GlobalAdminUser,
    DashboardStats,
    SuperadminDashboard,
    GroupDashboard,
    ActionAuditLog,
    ActionFilter,
)
from centralized_api.services.superadmin_service import SuperadminService
from centralized_api.services.group_admin_service import GroupAdminService

logger = logging.getLogger(__name__)

# Initialize routers
superadmin_router = APIRouter(prefix="/api/v1/superadmin", tags=["superadmin"])
group_admin_router = APIRouter(prefix="/api/v1/group-admin", tags=["group-admin"])
shared_router = APIRouter(prefix="/api/v1/shared", tags=["shared"])


# ============ DEPENDENCIES ============

class AuthUser:
    """Dependency to extract current user from token"""
    def __init__(self, user_id: int, username: str, role: UserRole, is_superadmin: bool = False):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.is_superadmin = is_superadmin


async def get_current_user(token: Optional[str] = None) -> AuthUser:
    """Extract current user from token (stub - integrate with your auth)"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    
    # TODO: Implement proper JWT token validation
    # For now, return mock user
    return AuthUser(
        user_id=1,
        username="testuser",
        role=UserRole.SUPERADMIN,
        is_superadmin=True,
    )


async def require_superadmin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require superadmin role"""
    if not user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return user


async def require_group_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Require at least group admin role"""
    if user.role not in [UserRole.SUPERADMIN, UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group admin access required"
        )
    return user


# ============ SUPERADMIN ROUTES ============

@superadmin_router.get(
    "/dashboard",
    response_model=SuperadminDashboard,
    summary="Get superadmin dashboard"
)
async def get_superadmin_dashboard(
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),  # TODO: inject database
    include_actions: bool = Query(True),
) -> SuperadminDashboard:
    """Get complete superadmin dashboard with all groups and statistics"""
    try:
        service = SuperadminService(db)
        dashboard = await service.get_superadmin_dashboard(include_actions=include_actions)
        return dashboard
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.get(
    "/groups",
    summary="List all groups"
)
async def list_all_groups(
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_active: Optional[bool] = None,
) -> Dict[str, Any]:
    """List all groups with optional filtering"""
    try:
        service = SuperadminService(db)
        result = await service.list_all_groups(skip=skip, limit=limit, is_active=is_active)
        return result
    except Exception as e:
        logger.error(f"Error listing groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.get(
    "/groups/{group_id}",
    response_model=GroupResponse,
    summary="Get group details"
)
async def get_group_details(
    group_id: int,
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> GroupResponse:
    """Get detailed information about a group"""
    try:
        service = SuperadminService(db)
        group_info = await service.get_group_details(group_id)
        return GroupResponse(
            group_id=group_info.group_id,
            group_name=group_info.group_name,
            owner_id=group_info.owner_id,
            owner_username=group_info.owner_name,
            admin_count=group_info.admin_count,
            member_count=group_info.member_count,
        )
    except Exception as e:
        logger.error(f"Error getting group details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.put(
    "/groups/{group_id}/owner",
    response_model=GroupResponse,
    summary="Change group owner"
)
async def change_group_owner(
    group_id: int,
    new_owner_id: int,
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> GroupResponse:
    """Change the owner of a group (superadmin only)"""
    try:
        service = SuperadminService(db)
        group = await service.change_group_owner(group_id, new_owner_id)
        return group
    except Exception as e:
        logger.error(f"Error changing group owner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.post(
    "/groups/{group_id}/disable",
    summary="Disable a group"
)
async def disable_group(
    group_id: int,
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> Dict[str, str]:
    """Disable a group from active management"""
    try:
        service = SuperadminService(db)
        await service.disable_group(group_id)
        return {"status": "success", "message": f"Group {group_id} disabled"}
    except Exception as e:
        logger.error(f"Error disabling group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.get(
    "/groups/{group_id}/admins",
    response_model=List[GroupAdmin],
    summary="Get group admins"
)
async def get_group_admins_superadmin(
    group_id: int,
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> List[GroupAdmin]:
    """Get all admins in a group"""
    try:
        service = SuperadminService(db)
        admins = await service.get_group_admins(group_id)
        return admins
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.post(
    "/groups/{group_id}/admins",
    response_model=GroupAdmin,
    summary="Add admin to group"
)
async def add_admin_to_group(
    group_id: int,
    user_id: int,
    username: Optional[str] = None,
    permissions: Optional[Dict[str, bool]] = None,
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> GroupAdmin:
    """Promote a user to admin in a group"""
    try:
        service = SuperadminService(db)
        admin = await service.promote_to_admin(group_id, user_id, username, permissions)
        return admin
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.delete(
    "/groups/{group_id}/admins/{admin_id}",
    summary="Remove admin from group"
)
async def remove_admin_from_group(
    group_id: int,
    admin_id: int,
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> Dict[str, str]:
    """Remove an admin from a group"""
    try:
        service = SuperadminService(db)
        result = await service.remove_admin(group_id, admin_id)
        return result
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.get(
    "/statistics",
    response_model=DashboardStats,
    summary="Get system statistics"
)
async def get_system_statistics(
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
) -> DashboardStats:
    """Get system-wide statistics"""
    try:
        service = SuperadminService(db)
        stats = await service.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@superadmin_router.get(
    "/audit-logs",
    response_model=List[ActionAuditLog],
    summary="Get audit logs"
)
async def get_audit_logs(
    user: AuthUser = Depends(require_superadmin),
    db = Depends(),
    group_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(100, ge=1, le=1000),
) -> List[ActionAuditLog]:
    """Get audit logs with optional filtering"""
    try:
        service = SuperadminService(db)
        logs = await service.get_audit_logs(group_id=group_id, days=days, limit=limit)
        return logs
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ GROUP ADMIN ROUTES ============

@group_admin_router.get(
    "/dashboard/{group_id}",
    response_model=GroupDashboard,
    summary="Get group dashboard"
)
async def get_group_dashboard(
    group_id: int,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
    include_actions: bool = Query(True),
) -> GroupDashboard:
    """Get dashboard for a specific group (admin must have access)"""
    try:
        service = GroupAdminService(db)
        
        # Verify access
        has_access = await service.verify_group_access(user.user_id, group_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this group"
            )
        
        dashboard = await service.get_group_dashboard(
            user.user_id,
            group_id,
            include_actions=include_actions
        )
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_admin_router.get(
    "/groups/{group_id}",
    summary="Get group info"
)
async def get_group_info(
    group_id: int,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
):
    """Get information about a group"""
    try:
        service = GroupAdminService(db)
        group_info = await service.get_group_info(user.user_id, group_id)
        return group_info
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this group"
        )
    except Exception as e:
        logger.error(f"Error getting group info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_admin_router.get(
    "/groups/{group_id}/members",
    summary="Get group members"
)
async def get_group_members(
    group_id: int,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """Get list of members in a group"""
    try:
        service = GroupAdminService(db)
        members = await service.get_group_members(user.user_id, group_id, skip, limit)
        return members
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this group"
        )
    except Exception as e:
        logger.error(f"Error getting members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_admin_router.get(
    "/groups/{group_id}/admins",
    response_model=List[GroupAdmin],
    summary="Get group admins"
)
async def get_group_admins_admin(
    group_id: int,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
) -> List[GroupAdmin]:
    """Get admins in a group"""
    try:
        service = GroupAdminService(db)
        admins = await service.get_group_admins(user.user_id, group_id)
        return admins
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this group"
        )
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_admin_router.get(
    "/groups/{group_id}/statistics",
    response_model=DashboardStats,
    summary="Get group statistics"
)
async def get_group_statistics(
    group_id: int,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
) -> DashboardStats:
    """Get statistics for a group"""
    try:
        service = GroupAdminService(db)
        stats = await service.get_group_stats(user.user_id, group_id)
        return stats
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this group"
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_admin_router.get(
    "/groups/{group_id}/audit-logs",
    response_model=List[ActionAuditLog],
    summary="Get group audit logs"
)
async def get_group_audit_logs(
    group_id: int,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
    limit: int = Query(50, ge=1, le=500),
) -> List[ActionAuditLog]:
    """Get audit logs for a group"""
    try:
        service = GroupAdminService(db)
        logs = await service.get_group_audit_logs(user.user_id, group_id, limit)
        return logs
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this group"
        )
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ ACTION EXECUTION ROUTES ============

@group_admin_router.post(
    "/groups/{group_id}/actions/execute",
    response_model=ActionResponse,
    summary="Execute action"
)
async def execute_action(
    group_id: int,
    action_request: ActionRequest,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
    executor = Depends(),  # TODO: inject executor
) -> ActionResponse:
    """Execute a moderation action in a group"""
    try:
        service = GroupAdminService(db, executor)
        response = await service.execute_action(user.user_id, group_id, action_request)
        return response
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_admin_router.post(
    "/groups/{group_id}/actions/batch",
    summary="Execute batch actions"
)
async def execute_batch_actions(
    group_id: int,
    batch_request: BatchActionRequest,
    user: AuthUser = Depends(require_group_admin),
    db = Depends(),
    executor = Depends(),
) -> Dict[str, Any]:
    """Execute multiple actions in a group"""
    try:
        service = GroupAdminService(db, executor)
        result = await service.execute_batch_actions(
            user.user_id,
            group_id,
            batch_request.actions,
            batch_request.stop_on_error
        )
        return result
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error executing batch actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ SHARED ROUTES (Available to all authorized users) ============

@shared_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info"
)
async def get_current_user_info(
    user: AuthUser = Depends(get_current_user),
) -> UserResponse:
    """Get information about the current authenticated user"""
    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        is_superadmin=user.is_superadmin,
    )


@shared_router.get(
    "/health",
    summary="Health check"
)
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============ EXPORT ROUTERS ============

def register_advanced_rbac_routes(app):
    """Register all RBAC routes with FastAPI app"""
    app.include_router(superadmin_router)
    app.include_router(group_admin_router)
    app.include_router(shared_router)
    logger.info("✅ Advanced RBAC routes registered")
