"""
Superadmin Service Layer

Provides high-level superadmin operations:
- Manage all groups globally
- Manage group owners
- View system-wide statistics
- Execute actions across all groups
- Manage global settings
- Audit logging
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

from centralized_api.models.advanced_rbac import (
    UserRole,
    GlobalPermission,
    GroupPermission,
    ActionType,
    ActionStatus,
    ActionResponse,
    ActionAuditLog,
    ActionRequest,
    GroupInfo,
    GroupAdmin,
    GroupResponse,
    GroupSettings,
    DashboardStats,
    SuperadminDashboard,
    GlobalAdminUser,
    ActionMetadata,
)

logger = logging.getLogger(__name__)


class SuperadminService:
    """Service for superadmin operations"""
    
    def __init__(self, db, executor=None):
        """Initialize superadmin service
        
        Args:
            db: Database connection
            executor: Action executor (optional)
        """
        self.db = db
        self.executor = executor
    
    # ============ GROUP MANAGEMENT ============
    
    async def list_all_groups(
        self,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """List all groups in the system
        
        Args:
            skip: Number of groups to skip
            limit: Maximum number of groups to return
            is_active: Filter by active status
            
        Returns:
            Dictionary with groups list and total count
        """
        try:
            query = {}
            if is_active is not None:
                query["is_active"] = is_active
            
            total = await self.db.groups.count_documents(query)
            groups = await self.db.groups.find(query).skip(skip).limit(limit).to_list(length=limit)
            
            return {
                "total": total,
                "groups": [self._format_group(g) for g in groups],
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            raise
    
    async def get_group_details(self, group_id: int) -> GroupInfo:
        """Get detailed information about a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            GroupInfo with full details
        """
        try:
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
                settings=GroupSettings(
                    group_id=group_id,
                    group_name=group.get("group_name"),
                    auto_moderation_enabled=group.get("auto_mod_enabled", True),
                    welcome_message_enabled=group.get("welcome_enabled", False),
                    welcome_message=group.get("welcome_message"),
                ),
                created_at=group.get("created_at", datetime.utcnow()),
                updated_at=group.get("updated_at", datetime.utcnow()),
            )
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}")
            raise
    
    async def change_group_owner(
        self,
        group_id: int,
        new_owner_id: int,
        new_owner_name: Optional[str] = None,
    ) -> GroupResponse:
        """Change the owner of a group
        
        Args:
            group_id: Telegram group ID
            new_owner_id: New owner's Telegram ID
            new_owner_name: New owner's name
            
        Returns:
            Updated GroupResponse
        """
        try:
            result = await self.db.groups.update_one(
                {"telegram_id": group_id},
                {
                    "$set": {
                        "owner_id": new_owner_id,
                        "owner_name": new_owner_name or f"User{new_owner_id}",
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Group {group_id} not found")
            
            logger.info(f"✅ Changed owner of group {group_id} to {new_owner_id}")
            
            group = await self.db.groups.find_one({"telegram_id": group_id})
            return self._format_group(group)
        except Exception as e:
            logger.error(f"Error changing group owner: {e}")
            raise
    
    async def disable_group(self, group_id: int) -> GroupResponse:
        """Disable a group (remove from active management)
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Updated GroupResponse
        """
        try:
            result = await self.db.groups.update_one(
                {"telegram_id": group_id},
                {
                    "$set": {
                        "is_active": False,
                        "disabled_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Group {group_id} not found")
            
            logger.warning(f"⚠️  Disabled group {group_id}")
            
            group = await self.db.groups.find_one({"telegram_id": group_id})
            return self._format_group(group)
        except Exception as e:
            logger.error(f"Error disabling group: {e}")
            raise
    
    # ============ ADMIN MANAGEMENT ============
    
    async def list_all_admins(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List all admins across all groups
        
        Args:
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            Dictionary with admins list
        """
        try:
            admins = []
            groups = await self.db.groups.find({}).to_list(length=None)
            
            for group in groups:
                group_admins = group.get("admins", [])
                for admin in group_admins:
                    admins.append({
                        "group_id": group.get("telegram_id"),
                        "user_id": admin.get("user_id"),
                        "username": admin.get("username"),
                        "role": admin.get("role", "ADMIN"),
                        "active": admin.get("active", True),
                        "assigned_at": admin.get("assigned_at"),
                    })
            
            return {
                "total": len(admins),
                "admins": admins[skip:skip+limit],
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error listing admins: {e}")
            raise
    
    async def get_group_admins(self, group_id: int) -> List[GroupAdmin]:
        """Get all admins in a specific group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            List of GroupAdmin objects
        """
        try:
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
            logger.error(f"Error getting admins for group {group_id}: {e}")
            raise
    
    async def promote_to_admin(
        self,
        group_id: int,
        user_id: int,
        username: Optional[str] = None,
        permissions: Optional[Dict[str, bool]] = None,
    ) -> GroupAdmin:
        """Promote a user to admin in a group (superadmin only)
        
        Args:
            group_id: Telegram group ID
            user_id: User to promote
            username: User's name
            permissions: Custom permissions dict
            
        Returns:
            Created GroupAdmin
        """
        try:
            admin_data = {
                "user_id": user_id,
                "username": username or f"User{user_id}",
                "role": "ADMIN",
                "can_ban": permissions.get("can_ban", True) if permissions else True,
                "can_kick": permissions.get("can_kick", True) if permissions else True,
                "can_mute": permissions.get("can_mute", True) if permissions else True,
                "can_warn": permissions.get("can_warn", False) if permissions else False,
                "can_promote": permissions.get("can_promote", False) if permissions else False,
                "can_delete_messages": permissions.get("can_delete_messages", False) if permissions else False,
                "can_pin_messages": permissions.get("can_pin_messages", False) if permissions else False,
                "active": True,
                "assigned_at": datetime.utcnow(),
            }
            
            await self.db.groups.update_one(
                {"telegram_id": group_id},
                {
                    "$push": {"admins": admin_data},
                    "$set": {"updated_at": datetime.utcnow()},
                }
            )
            
            logger.info(f"✅ Promoted user {user_id} to admin in group {group_id}")
            
            return GroupAdmin(**admin_data)
        except Exception as e:
            logger.error(f"Error promoting user: {e}")
            raise
    
    async def remove_admin(self, group_id: int, user_id: int) -> Dict[str, str]:
        """Remove an admin from a group
        
        Args:
            group_id: Telegram group ID
            user_id: Admin to remove
            
        Returns:
            Status message
        """
        try:
            result = await self.db.groups.update_one(
                {"telegram_id": group_id},
                {
                    "$pull": {"admins": {"user_id": user_id}},
                    "$set": {"updated_at": datetime.utcnow()},
                }
            )
            
            if result.modified_count == 0:
                raise ValueError(f"Admin {user_id} not found in group {group_id}")
            
            logger.info(f"✅ Removed admin {user_id} from group {group_id}")
            
            return {"status": "success", "message": f"Removed admin {user_id} from group {group_id}"}
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            raise
    
    # ============ ACTION EXECUTION ============
    
    async def execute_group_action(
        self,
        action_request: ActionRequest,
    ) -> ActionResponse:
        """Execute a moderation action on behalf of group admin
        
        Args:
            action_request: ActionRequest with details
            
        Returns:
            ActionResponse with result
        """
        try:
            if not self.executor:
                raise ValueError("Executor not configured")
            
            # Execute action through executor
            response = await self.executor.execute_action(action_request)
            
            # Log action
            await self._log_action(action_request, response)
            
            logger.info(f"✅ Executed action {response.action_id}: {action_request.action_type}")
            
            return response
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            raise
    
    async def execute_batch_actions(
        self,
        group_id: int,
        actions: List[ActionRequest],
        stop_on_error: bool = False,
    ) -> Dict[str, Any]:
        """Execute multiple actions in a group
        
        Args:
            group_id: Telegram group ID
            actions: List of actions to execute
            stop_on_error: Stop if any action fails
            
        Returns:
            Dictionary with results
        """
        try:
            results = []
            failed = 0
            
            for action in actions:
                action.group_id = group_id
                
                try:
                    response = await self.execute_group_action(action)
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
    
    # ============ STATISTICS & ANALYTICS ============
    
    async def get_system_stats(self) -> DashboardStats:
        """Get system-wide statistics
        
        Returns:
            DashboardStats with current stats
        """
        try:
            groups = await self.db.groups.count_documents({"is_active": True})
            
            total_members = 0
            total_admins = 0
            total_actions_today = 0
            total_bans = 0
            total_warnings = 0
            active_mutes = 0
            
            # Calculate from groups
            groups_list = await self.db.groups.find({"is_active": True}).to_list(length=None)
            for group in groups_list:
                total_members += len(group.get("members", []))
                total_admins += len(group.get("admins", []))
            
            # Get today's actions
            today = datetime.utcnow().date()
            actions = await self.db.actions.find({
                "executed_at": {"$gte": datetime.combine(today, datetime.min.time())}
            }).to_list(length=None)
            
            total_actions_today = len(actions)
            
            for action in actions:
                if action.get("action_type") == "ban":
                    total_bans += 1
                elif action.get("action_type") == "warn":
                    total_warnings += 1
            
            return DashboardStats(
                total_groups=groups,
                total_members=total_members,
                total_actions_today=total_actions_today,
                total_warnings=total_warnings,
                total_bans=total_bans,
                active_mutes=active_mutes,
                total_admins=total_admins,
            )
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            raise
    
    async def get_superadmin_dashboard(
        self,
        include_actions: bool = True,
    ) -> SuperadminDashboard:
        """Get complete superadmin dashboard
        
        Args:
            include_actions: Whether to include recent actions
            
        Returns:
            SuperadminDashboard with all data
        """
        try:
            stats = await self.get_system_stats()
            groups_list = await self.list_all_groups(limit=100)
            
            # Get recent actions if requested
            recent_actions = []
            if include_actions:
                actions = await self.db.actions.find({}).sort("executed_at", -1).limit(50).to_list(length=50)
                recent_actions = [self._format_action_log(a) for a in actions]
            
            dashboard = SuperadminDashboard(
                total_stats=stats,
                groups_data=[],  # Could include individual group data
                system_health={
                    "db_status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                recent_global_actions=recent_actions,
            )
            
            return dashboard
        except Exception as e:
            logger.error(f"Error getting superadmin dashboard: {e}")
            raise
    
    # ============ AUDIT LOGGING ============
    
    async def get_audit_logs(
        self,
        group_id: Optional[int] = None,
        days: int = 7,
        limit: int = 100,
    ) -> List[ActionAuditLog]:
        """Get audit logs
        
        Args:
            group_id: Filter by group (None for all groups)
            days: Number of days back
            limit: Maximum logs to return
            
        Returns:
            List of ActionAuditLog entries
        """
        try:
            query = {
                "executed_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
            }
            
            if group_id:
                query["group_id"] = group_id
            
            logs = await self.db.actions.find(query).sort("executed_at", -1).limit(limit).to_list(length=limit)
            
            return [self._format_action_log(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            raise
    
    # ============ HELPER METHODS ============
    
    def _format_group(self, group: Dict) -> GroupResponse:
        """Format group document to GroupResponse"""
        return GroupResponse(
            group_id=group.get("telegram_id"),
            group_name=group.get("group_name"),
            owner_id=group.get("owner_id"),
            owner_username=group.get("owner_name"),
            admin_count=len(group.get("admins", [])),
            member_count=len(group.get("members", [])),
            is_active=group.get("is_active", True),
            created_at=group.get("created_at", datetime.utcnow()),
            updated_at=group.get("updated_at", datetime.utcnow()),
        )
    
    def _format_action_log(self, action: Dict) -> ActionAuditLog:
        """Format action document to ActionAuditLog"""
        return ActionAuditLog(
            action_id=str(action.get("_id", "")),
            action_type=ActionType(action.get("action_type", "ban")),
            group_id=action.get("group_id"),
            user_id=action.get("user_id"),
            username=action.get("username"),
            target_user_id=action.get("target_user_id"),
            target_username=action.get("target_username"),
            status=ActionStatus(action.get("status", "success")),
            reason=action.get("reason"),
            initiated_by=action.get("initiated_by"),
            executed_at=action.get("executed_at", datetime.utcnow()),
            success=action.get("success", True),
            error_message=action.get("error_message"),
        )
    
    async def _log_action(
        self,
        request: ActionRequest,
        response: ActionResponse,
    ) -> None:
        """Log an action to audit trail
        
        Args:
            request: Original request
            response: Response from action
        """
        try:
            log_entry = {
                "_id": response.action_id,
                "action_type": request.action_type.value,
                "group_id": request.group_id,
                "user_id": request.user_id,
                "target_user_id": request.user_id,
                "initiated_by": request.initiated_by,
                "reason": request.reason,
                "status": response.status.value,
                "success": response.success,
                "error_message": response.error,
                "execution_time_ms": response.execution_time_ms,
                "executed_at": response.timestamp,
            }
            
            await self.db.actions.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging action: {e}")
