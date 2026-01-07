"""
Group Admin Service Layer

Provides operations for admins managing their own groups:
- View group details and members
- Execute actions within their group
- Manage admins in their group (limited)
- View group statistics and audit logs
- Manage group settings (if owner)
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from centralized_api.models.advanced_rbac import (
    UserRole,
    GroupPermission,
    ActionType,
    ActionRequest,
    ActionResponse,
    ActionAuditLog,
    GroupInfo,
    GroupAdmin,
    GroupResponse,
    DashboardStats,
    GroupDashboard,
    ActionMetadata,
    GroupMember,
)

logger = logging.getLogger(__name__)


class GroupAdminService:
    """Service for group admin operations"""
    
    def __init__(self, db, executor=None):
        """Initialize group admin service
        
        Args:
            db: Database connection
            executor: Action executor (optional)
        """
        self.db = db
        self.executor = executor
    
    # ============ PERMISSION CHECKING ============
    
    async def check_permission(
        self,
        admin_user_id: int,
        group_id: int,
        required_permission: GroupPermission,
    ) -> bool:
        """Check if admin has a specific permission in a group
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            required_permission: Permission to check
            
        Returns:
            True if admin has permission, False otherwise
        """
        try:
            group = await self.db.groups.find_one({"telegram_id": group_id})
            if not group:
                logger.warning(f"Group {group_id} not found")
                return False
            
            # Superadmin has all permissions
            admin_user = await self.db.superadmins.find_one({"user_id": admin_user_id})
            if admin_user:
                return True
            
            # Group owner has all permissions in their group
            if group.get("owner_id") == admin_user_id:
                return True
            
            # Check admin in group
            admins = group.get("admins", [])
            for admin in admins:
                if admin.get("user_id") == admin_user_id:
                    # Map permission to field name
                    permission_map = {
                        GroupPermission.EXECUTE_BAN: "can_ban",
                        GroupPermission.EXECUTE_KICK: "can_kick",
                        GroupPermission.EXECUTE_MUTE: "can_mute",
                        GroupPermission.EXECUTE_PROMOTE: "can_promote",
                        GroupPermission.EXECUTE_DEMOTE: "can_promote",
                        GroupPermission.EXECUTE_PIN: "can_pin_messages",
                        GroupPermission.EXECUTE_DELETE: "can_delete_messages",
                        GroupPermission.MANAGE_MEMBERS: "can_ban",
                        GroupPermission.MANAGE_ADMINS: "can_promote",
                        GroupPermission.VIEW_LOGS: True,
                    }
                    
                    field = permission_map.get(required_permission, None)
                    if field:
                        return admin.get(field, False)
            
            return False
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def verify_group_access(
        self,
        admin_user_id: int,
        group_id: int,
    ) -> bool:
        """Verify admin has access to group
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            
        Returns:
            True if admin can access group
        """
        try:
            # Superadmin can access all groups
            admin_user = await self.db.superadmins.find_one({"user_id": admin_user_id})
            if admin_user:
                return True
            
            # Owner can access their group
            group = await self.db.groups.find_one({"telegram_id": group_id})
            if not group:
                return False
            
            if group.get("owner_id") == admin_user_id:
                return True
            
            # Admin in group can access
            admins = group.get("admins", [])
            for admin in admins:
                if admin.get("user_id") == admin_user_id and admin.get("active", True):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error verifying group access: {e}")
            return False
    
    # ============ GROUP INFORMATION ============
    
    async def get_group_info(
        self,
        admin_user_id: int,
        group_id: int,
    ) -> GroupInfo:
        """Get group information (admin must have access)
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            
        Returns:
            GroupInfo object
        """
        try:
            # Verify access
            has_access = await self.verify_group_access(admin_user_id, group_id)
            if not has_access:
                raise PermissionError(f"User {admin_user_id} cannot access group {group_id}")
            
            group = await self.db.groups.find_one({"telegram_id": group_id})
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            admins = group.get("admins", [])
            members = group.get("members", [])
            
            return GroupInfo(
                group_id=group_id,
                group_name=group.get("group_name"),
                owner_id=group.get("owner_id"),
                owner_name=group.get("owner_name"),
                admin_count=len(admins),
                member_count=len(members),
                created_at=group.get("created_at", datetime.utcnow()),
                updated_at=group.get("updated_at", datetime.utcnow()),
            )
        except Exception as e:
            logger.error(f"Error getting group info: {e}")
            raise
    
    async def get_group_members(
        self,
        admin_user_id: int,
        group_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get group members list
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            Dictionary with members list
        """
        try:
            # Verify access
            has_access = await self.verify_group_access(admin_user_id, group_id)
            if not has_access:
                raise PermissionError(f"User {admin_user_id} cannot access group {group_id}")
            
            group = await self.db.groups.find_one({"telegram_id": group_id})
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            members = group.get("members", [])
            
            return {
                "total": len(members),
                "members": members[skip:skip+limit],
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error getting group members: {e}")
            raise
    
    async def get_group_admins(
        self,
        admin_user_id: int,
        group_id: int,
    ) -> List[GroupAdmin]:
        """Get list of admins in group
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            
        Returns:
            List of GroupAdmin objects
        """
        try:
            # Verify access
            has_access = await self.verify_group_access(admin_user_id, group_id)
            if not has_access:
                raise PermissionError(f"User {admin_user_id} cannot access group {group_id}")
            
            group = await self.db.groups.find_one({"telegram_id": group_id})
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            admins = []
            for admin_data in group.get("admins", []):
                admin = GroupAdmin(
                    user_id=admin_data.get("user_id"),
                    username=admin_data.get("username"),
                    first_name=admin_data.get("first_name"),
                    role=UserRole(admin_data.get("role", "admin").lower()),
                    can_ban=admin_data.get("can_ban", True),
                    can_kick=admin_data.get("can_kick", True),
                    can_mute=admin_data.get("can_mute", True),
                    can_warn=admin_data.get("can_warn", False),
                    can_promote=admin_data.get("can_promote", False),
                    active=admin_data.get("active", True),
                )
                admins.append(admin)
            
            return admins
        except Exception as e:
            logger.error(f"Error getting group admins: {e}")
            raise
    
    # ============ ACTION EXECUTION ============
    
    async def execute_action(
        self,
        admin_user_id: int,
        group_id: int,
        action_request: ActionRequest,
    ) -> ActionResponse:
        """Execute a moderation action in a group
        
        Args:
            admin_user_id: Admin executing action
            group_id: Group ID
            action_request: ActionRequest details
            
        Returns:
            ActionResponse with result
        """
        try:
            # Verify access
            has_access = await self.verify_group_access(admin_user_id, group_id)
            if not has_access:
                raise PermissionError(f"User {admin_user_id} cannot access group {group_id}")
            
            # Check permission for action type
            permission_map = {
                ActionType.BAN: GroupPermission.EXECUTE_BAN,
                ActionType.KICK: GroupPermission.EXECUTE_KICK,
                ActionType.MUTE: GroupPermission.EXECUTE_MUTE,
                ActionType.PROMOTE: GroupPermission.EXECUTE_PROMOTE,
                ActionType.DEMOTE: GroupPermission.EXECUTE_DEMOTE,
                ActionType.PIN: GroupPermission.EXECUTE_PIN,
                ActionType.DELETE: GroupPermission.EXECUTE_DELETE,
            }
            
            required_perm = permission_map.get(action_request.action_type)
            if required_perm:
                has_perm = await self.check_permission(admin_user_id, group_id, required_perm)
                if not has_perm:
                    return ActionResponse(
                        action_id="",
                        success=False,
                        message=f"You don't have permission to {action_request.action_type.value}",
                        error=f"Missing permission: {required_perm.value}",
                    )
            
            if not self.executor:
                raise ValueError("Executor not configured")
            
            # Set context
            action_request.group_id = group_id
            action_request.initiated_by = admin_user_id
            
            # Execute action
            response = await self.executor.execute_action(action_request)
            
            logger.info(f"✅ Admin {admin_user_id} executed {action_request.action_type.value} in group {group_id}")
            
            return response
        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            raise
    
    async def execute_batch_actions(
        self,
        admin_user_id: int,
        group_id: int,
        actions: List[ActionRequest],
        stop_on_error: bool = False,
    ) -> Dict[str, Any]:
        """Execute multiple actions in a group
        
        Args:
            admin_user_id: Admin executing actions
            group_id: Group ID
            actions: List of actions to execute
            stop_on_error: Stop if any action fails
            
        Returns:
            Dictionary with results
        """
        try:
            results = []
            failed = 0
            
            for action in actions:
                try:
                    response = await self.execute_action(admin_user_id, group_id, action)
                    results.append(response)
                    
                    if not response.success and stop_on_error:
                        break
                    elif not response.success:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error executing action: {e}")
                    failed += 1
                    if stop_on_error:
                        break
            
            return {
                "total": len(actions),
                "successful": len(actions) - failed,
                "failed": failed,
                "results": results,
            }
        except Exception as e:
            logger.error(f"Error executing batch actions: {e}")
            raise
    
    # ============ STATISTICS ============
    
    async def get_group_stats(
        self,
        admin_user_id: int,
        group_id: int,
    ) -> DashboardStats:
        """Get statistics for a group
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            
        Returns:
            DashboardStats object
        """
        try:
            # Verify access
            has_access = await self.verify_group_access(admin_user_id, group_id)
            if not has_access:
                raise PermissionError(f"User {admin_user_id} cannot access group {group_id}")
            
            group = await self.db.groups.find_one({"telegram_id": group_id})
            if not group:
                raise ValueError(f"Group {group_id} not found")
            
            members = group.get("members", [])
            admins = group.get("admins", [])
            
            # Count actions for this group today
            today = datetime.utcnow().date()
            actions = await self.db.actions.find({
                "group_id": group_id,
                "executed_at": {"$gte": datetime.combine(today, datetime.min.time())}
            }).to_list(length=None)
            
            total_bans = sum(1 for a in actions if a.get("action_type") == "ban")
            total_warnings = sum(1 for a in actions if a.get("action_type") == "warn")
            
            return DashboardStats(
                total_groups=1,
                total_members=len(members),
                total_actions_today=len(actions),
                total_warnings=total_warnings,
                total_bans=total_bans,
                total_admins=len(admins),
            )
        except Exception as e:
            logger.error(f"Error getting group stats: {e}")
            raise
    
    async def get_group_dashboard(
        self,
        admin_user_id: int,
        group_id: int,
        include_actions: bool = True,
    ) -> GroupDashboard:
        """Get complete group dashboard for admin
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            include_actions: Whether to include recent actions
            
        Returns:
            GroupDashboard with all data
        """
        try:
            # Get group info, stats, admins
            group_info = await self.get_group_info(admin_user_id, group_id)
            stats = await self.get_group_stats(admin_user_id, group_id)
            admins = await self.get_group_admins(admin_user_id, group_id)
            
            # Get recent actions if requested
            recent_actions = []
            if include_actions:
                actions = await self.db.actions.find({
                    "group_id": group_id
                }).sort("executed_at", -1).limit(20).to_list(length=20)
                
                for action in actions:
                    recent_actions.append(ActionAuditLog(
                        action_id=str(action.get("_id", "")),
                        action_type=ActionType(action.get("action_type", "ban")),
                        group_id=action.get("group_id"),
                        user_id=action.get("user_id"),
                        username=action.get("username"),
                        target_user_id=action.get("target_user_id"),
                        target_username=action.get("target_username"),
                        status=action.get("status", "success"),
                        reason=action.get("reason"),
                        executed_at=action.get("executed_at", datetime.utcnow()),
                    ))
            
            dashboard = GroupDashboard(
                group_id=group_id,
                group_name=group_info.group_name,
                stats=stats,
                recent_actions=recent_actions,
                admins=admins,
            )
            
            return dashboard
        except Exception as e:
            logger.error(f"Error getting group dashboard: {e}")
            raise
    
    # ============ AUDIT LOGS ============
    
    async def get_group_audit_logs(
        self,
        admin_user_id: int,
        group_id: int,
        limit: int = 50,
    ) -> List[ActionAuditLog]:
        """Get audit logs for a group
        
        Args:
            admin_user_id: Admin's user ID
            group_id: Group ID
            limit: Maximum logs to return
            
        Returns:
            List of ActionAuditLog entries
        """
        try:
            # Verify access
            has_access = await self.verify_group_access(admin_user_id, group_id)
            if not has_access:
                raise PermissionError(f"User {admin_user_id} cannot access group {group_id}")
            
            logs = await self.db.actions.find({
                "group_id": group_id
            }).sort("executed_at", -1).limit(limit).to_list(length=limit)
            
            result = []
            for log in logs:
                result.append(ActionAuditLog(
                    action_id=str(log.get("_id", "")),
                    action_type=ActionType(log.get("action_type", "ban")),
                    group_id=log.get("group_id"),
                    user_id=log.get("user_id"),
                    username=log.get("username"),
                    target_user_id=log.get("target_user_id"),
                    target_username=log.get("target_username"),
                    status=log.get("status", "success"),
                    reason=log.get("reason"),
                    executed_at=log.get("executed_at", datetime.utcnow()),
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            raise
