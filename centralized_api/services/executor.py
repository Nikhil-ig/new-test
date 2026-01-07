"""
Action Executor Service
High-performance async executor for all action types
Uses existing Telegram API functions from src.services.telegram_api
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from centralized_api.models import (
    ActionRequest,
    ActionResponse,
    ActionStatus,
    ActionType,
    BanRequest,
    KickRequest,
    MuteRequest,
    UnmuteRequest,
    PromoteRequest,
    DemoteRequest,
    WarnRequest,
    PinRequest,
    UnpinRequest,
    DeleteMessageRequest,
)
from centralized_api.db.mongodb import ActionDatabase
from centralized_api.config import (
    BACKOFF_BASE,
    MAX_RETRIES,
    MAX_BACKOFF,
    BATCH_TIMEOUT,
)

# Import your existing Telegram API functions
try:
    from src.services.telegram_api import (
        ban_user_telegram,
        unban_user_telegram,
        kick_user_telegram,
        mute_user_telegram,
        unmute_user_telegram,
        promote_user_telegram,
        demote_user_telegram,
        pin_message_telegram,
        unpin_message_telegram,
        delete_message_telegram,
    )
    TELEGRAM_API_AVAILABLE = True
except ImportError:
    TELEGRAM_API_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Could not import telegram_api - will use direct bot calls")

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    High-performance async executor for Telegram actions.
    Handles retries, logging, validation, and database persistence.
    """

    def __init__(self, bot, db: Optional[ActionDatabase] = None):
        """
        Initialize executor
        
        Args:
            bot: Aiogram Bot instance
            db: Optional ActionDatabase instance (uses default if not provided)
        """
        self.bot = bot
        self.db = db or ActionDatabase()
        self._retry_config = {
            'base': BACKOFF_BASE,
            'max_retries': MAX_RETRIES,
            'max_backoff': MAX_BACKOFF,
        }
        self._pending_actions: Dict[str, Dict[str, Any]] = {}

    async def execute_action(self, request: ActionRequest) -> ActionResponse:
        """
        Execute a single action with automatic retries and logging
        
        Args:
            request: Action request model
            
        Returns:
            ActionResponse with execution details
        """
        action_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        retry_count = 0
        last_error = None

        # Store pending action
        self._pending_actions[action_id] = {
            'request': request,
            'status': ActionStatus.PENDING,
            'started_at': start_time,
        }

        try:
            # Attempt execution with retries
            while retry_count <= self._retry_config['max_retries']:
                try:
                    response = await self._execute_action_internal(
                        action_id=action_id,
                        request=request,
                        retry_count=retry_count,
                    )

                    # Log successful action
                    await self.db.log_action(
                        action_id=action_id,
                        action_type=request.action_type,
                        group_id=request.group_id,
                        user_id=request.user_id,
                        initiated_by=request.initiated_by,
                        status=ActionStatus.SUCCESS,
                        success=True,
                        message=response.message,
                        reason=request.reason,
                        execution_time_ms=response.execution_time_ms,
                        retry_count=retry_count,
                        api_response=response.api_response,
                        metadata=request.metadata,
                    )

                    # Remove from pending
                    del self._pending_actions[action_id]
                    return response

                except Exception as e:
                    last_error = e
                    retry_count += 1

                    if retry_count <= self._retry_config['max_retries']:
                        # Calculate backoff
                        backoff = min(
                            self._retry_config['base'] * (2 ** (retry_count - 1)),
                            self._retry_config['max_backoff'],
                        )
                        logger.warning(
                            f"Action {action_id} failed, retrying in {backoff}s: {str(e)}"
                        )
                        await asyncio.sleep(backoff)

            # All retries exhausted
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response = ActionResponse(
                action_id=action_id,
                action_type=request.action_type,
                group_id=request.group_id,
                user_id=request.user_id,
                status=ActionStatus.FAILED,
                success=False,
                message=f"Action failed after {retry_count} retries",
                error=str(last_error),
                timestamp=start_time,
                execution_time_ms=execution_time,
                retry_count=retry_count,
            )

            # Log failed action
            await self.db.log_action(
                action_id=action_id,
                action_type=request.action_type,
                group_id=request.group_id,
                user_id=request.user_id,
                initiated_by=request.initiated_by,
                status=ActionStatus.FAILED,
                success=False,
                message=response.message,
                error=response.error,
                reason=request.reason,
                execution_time_ms=execution_time,
                retry_count=retry_count,
                metadata=request.metadata,
            )

            # Store in dead letter queue
            await self.db.log_dead_letter(
                action_id=action_id,
                request=request,
                error=str(last_error),
                retry_count=retry_count,
            )

            del self._pending_actions[action_id]
            return response

        except Exception as e:
            logger.error(f"Unexpected error in action {action_id}: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response = ActionResponse(
                action_id=action_id,
                action_type=request.action_type,
                group_id=request.group_id,
                user_id=request.user_id,
                status=ActionStatus.FAILED,
                success=False,
                message="Unexpected error during execution",
                error=str(e),
                timestamp=start_time,
                execution_time_ms=execution_time,
            )
            self._pending_actions.pop(action_id, None)
            return response

    async def _execute_action_internal(
        self,
        action_id: str,
        request: ActionRequest,
        retry_count: int,
    ) -> ActionResponse:
        """Internal execution method that dispatches to specific action handlers"""
        start_time = datetime.utcnow()

        # Dispatch to appropriate handler
        if isinstance(request, BanRequest):
            result = await self._execute_ban(request)
        elif isinstance(request, KickRequest):
            result = await self._execute_kick(request)
        elif isinstance(request, MuteRequest):
            result = await self._execute_mute(request)
        elif isinstance(request, UnmuteRequest):
            result = await self._execute_unmute(request)
        elif isinstance(request, PromoteRequest):
            result = await self._execute_promote(request)
        elif isinstance(request, DemoteRequest):
            result = await self._execute_demote(request)
        elif isinstance(request, WarnRequest):
            result = await self._execute_warn(request)
        elif isinstance(request, PinRequest):
            result = await self._execute_pin(request)
        elif isinstance(request, UnpinRequest):
            result = await self._execute_unpin(request)
        elif isinstance(request, DeleteMessageRequest):
            result = await self._execute_delete_message(request)
        else:
            raise ValueError(f"Unknown action type: {type(request)}")

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ActionResponse(
            action_id=action_id,
            action_type=request.action_type,
            group_id=request.group_id,
            user_id=request.user_id,
            status=ActionStatus.SUCCESS if result['success'] else ActionStatus.FAILED,
            success=result['success'],
            message=result['message'],
            error=result.get('error'),
            timestamp=start_time,
            execution_time_ms=execution_time,
            retry_count=0,
            api_response=result.get('api_response'),
        )

    # =========================================================================
    # SPECIFIC ACTION HANDLERS
    # =========================================================================

    async def _execute_ban(self, request: BanRequest) -> Dict[str, Any]:
        """Ban user from group using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await ban_user_telegram(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    until_date=request.until_date,
                    revoke_messages=request.revoke_messages,
                )
            else:
                # Fallback to direct bot call
                success = await self.bot.ban_chat_member(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    until_date=request.until_date,
                    revoke_messages=request.revoke_messages,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ User {request.user_id} banned successfully",
                    'api_response': {'action': 'ban', 'user_id': request.user_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to ban user {request.user_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to ban user",
                'error': str(e),
            }

    async def _execute_kick(self, request: KickRequest) -> Dict[str, Any]:
        """Kick user from group using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await kick_user_telegram(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                )
            else:
                # Fallback
                from datetime import timedelta
                from aiogram.types import ChatPermissions
                
                restrict_until = datetime.utcnow() + timedelta(seconds=30)
                success = await self.bot.restrict_chat_member(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    permissions=ChatPermissions(),
                    until_date=int(restrict_until.timestamp()),
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ User {request.user_id} kicked successfully",
                    'api_response': {'action': 'kick', 'user_id': request.user_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to kick user {request.user_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to kick user",
                'error': str(e),
            }

    async def _execute_mute(self, request: MuteRequest) -> Dict[str, Any]:
        """Mute user in group using Telegram API"""
        try:
            # Use your existing telegram_api function
            # Note: your function takes duration_minutes, but our model uses duration_seconds
            duration_minutes = request.duration // 60
            
            if TELEGRAM_API_AVAILABLE:
                success = await mute_user_telegram(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    duration_minutes=duration_minutes,
                )
            else:
                # Fallback
                from aiogram.types import ChatPermissions
                from datetime import timedelta
                
                mute_until = datetime.utcnow() + timedelta(seconds=request.duration)
                success = await self.bot.restrict_chat_member(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=int(mute_until.timestamp()),
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ User {request.user_id} muted for {request.duration}s",
                    'api_response': {'action': 'mute', 'user_id': request.user_id, 'duration': request.duration},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to mute user {request.user_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to mute user",
                'error': str(e),
            }

    async def _execute_unmute(self, request: UnmuteRequest) -> Dict[str, Any]:
        """Unmute user in group using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await unmute_user_telegram(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                )
            else:
                # Fallback
                from aiogram.types import ChatPermissions
                
                permissions = ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                )
                await self.bot.restrict_chat_member(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    permissions=permissions,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ User {request.user_id} unmuted successfully",
                    'api_response': {'action': 'unmute', 'user_id': request.user_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to unmute user {request.user_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to unmute user",
                'error': str(e),
            }

    async def _execute_promote(self, request: PromoteRequest) -> Dict[str, Any]:
        """Promote user to admin using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await promote_user_telegram(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                )
            else:
                # Fallback
                from aiogram.types import ChatAdministratorRights
                
                admin_rights = ChatAdministratorRights(
                    is_anonymous=False,
                    can_manage_chat=True,
                    can_delete_messages=True,
                    can_manage_video_chats=False,
                    can_restrict_members=True,
                    can_promote_members=False,
                    can_change_info=False,
                    can_invite_users=True,
                    can_post_stories=False,
                    can_edit_stories=False,
                    can_delete_stories=False,
                )
                await self.bot.promote_chat_member(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    administrator_rights=admin_rights,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ User {request.user_id} promoted to admin",
                    'api_response': {'action': 'promote', 'user_id': request.user_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to promote user {request.user_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to promote user",
                'error': str(e),
            }

    async def _execute_demote(self, request: DemoteRequest) -> Dict[str, Any]:
        """Demote admin to regular user using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await demote_user_telegram(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                )
            else:
                # Fallback
                from aiogram.types import ChatAdministratorRights
                
                admin_rights = ChatAdministratorRights()
                await self.bot.promote_chat_member(
                    chat_id=request.group_id,
                    user_id=request.user_id,
                    administrator_rights=admin_rights,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ User {request.user_id} demoted to regular user",
                    'api_response': {'action': 'demote', 'user_id': request.user_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to demote user {request.user_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to demote user",
                'error': str(e),
            }

    async def _execute_warn(self, request: WarnRequest) -> Dict[str, Any]:
        """Warn user (placeholder - implement according to your warning system)"""
        try:
            # Placeholder: Update user warning count in database
            await self.db.increment_warning(
                group_id=request.group_id,
                user_id=request.user_id,
                increment=request.warn_count,
            )
            return {
                'success': True,
                'message': f"User {request.user_id} warned ({request.warn_count} warning(s))",
                'api_response': {'action': 'warn', 'user_id': request.user_id, 'count': request.warn_count},
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to warn user",
                'error': str(e),
            }

    async def _execute_pin(self, request: PinRequest) -> Dict[str, Any]:
        """Pin message in group using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await pin_message_telegram(
                    chat_id=request.group_id,
                    message_id=request.message_id,
                    disable_notification=not request.notify,
                )
            else:
                # Fallback
                await self.bot.pin_chat_message(
                    chat_id=request.group_id,
                    message_id=request.message_id,
                    disable_notification=not request.notify,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ Message {request.message_id} pinned",
                    'api_response': {'action': 'pin', 'message_id': request.message_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to pin message {request.message_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to pin message",
                'error': str(e),
            }

    async def _execute_unpin(self, request: UnpinRequest) -> Dict[str, Any]:
        """Unpin message from group using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await unpin_message_telegram(
                    chat_id=request.group_id,
                    message_id=request.message_id,
                )
            else:
                # Fallback
                await self.bot.unpin_chat_message(
                    chat_id=request.group_id,
                    message_id=request.message_id,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ Message unpinned",
                    'api_response': {'action': 'unpin', 'message_id': request.message_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to unpin message",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to unpin message",
                'error': str(e),
            }

    async def _execute_delete_message(self, request: DeleteMessageRequest) -> Dict[str, Any]:
        """Delete message from group using Telegram API"""
        try:
            # Use your existing telegram_api function
            if TELEGRAM_API_AVAILABLE:
                success = await delete_message_telegram(
                    chat_id=request.group_id,
                    message_id=request.message_id,
                )
            else:
                # Fallback
                await self.bot.delete_message(
                    chat_id=request.group_id,
                    message_id=request.message_id,
                )
                success = True
            
            if success:
                return {
                    'success': True,
                    'message': f"✅ Message {request.message_id} deleted",
                    'api_response': {'action': 'delete', 'message_id': request.message_id},
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to delete message {request.message_id}",
                    'error': "Telegram API returned False",
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to delete message",
                'error': str(e),
            }

    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================

    async def execute_batch(
        self,
        requests: List[ActionRequest],
        atomic: bool = True,
    ) -> List[ActionResponse]:
        """
        Execute multiple actions
        
        Args:
            requests: List of action requests
            atomic: If True, all actions must succeed or all fail (not fully implemented)
            
        Returns:
            List of ActionResponses
        """
        tasks = [self.execute_action(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=False)
        return responses

    # =========================================================================
    # ACTION MANAGEMENT
    # =========================================================================

    async def get_action_status(self, action_id: str) -> Optional[ActionResponse]:
        """Get current status of an action"""
        # Check if pending
        if action_id in self._pending_actions:
            pending = self._pending_actions[action_id]
            return ActionResponse(
                action_id=action_id,
                action_type=pending['request'].action_type,
                group_id=pending['request'].group_id,
                user_id=pending['request'].user_id,
                status=pending['status'],
                success=False,
                message="Action is still processing",
                timestamp=pending['started_at'],
            )

        # Check database
        log = await self.db.get_action_log(action_id)
        if log:
            return ActionResponse(
                action_id=action_id,
                action_type=log['action_type'],
                group_id=log['group_id'],
                user_id=log['user_id'],
                status=ActionStatus(log['status']),
                success=log['success'],
                message=log['message'],
                error=log.get('error'),
                timestamp=log['created_at'],
                execution_time_ms=log.get('execution_time_ms'),
                retry_count=log.get('retry_count', 0),
            )

        return None

    async def cancel_action(self, action_id: str) -> bool:
        """Cancel a pending action"""
        if action_id in self._pending_actions:
            del self._pending_actions[action_id]
            await self.db.update_action_status(
                action_id=action_id,
                status=ActionStatus.CANCELLED,
            )
            return True
        return False

    # =========================================================================
    # STATISTICS & MONITORING
    # =========================================================================

    def get_pending_actions_count(self) -> int:
        """Get number of pending actions"""
        return len(self._pending_actions)

    async def get_action_history(
        self,
        group_id: int,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Get action history for a group"""
        return await self.db.get_action_history(
            group_id=group_id,
            limit=limit,
            skip=skip,
        )
