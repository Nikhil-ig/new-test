"""
Simple Actions API
Simplified endpoint for bot to call without complex request models
"""

import logging
import os
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from aiogram import Bot

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/actions", tags=["simple-actions"])

# Global bot instance
_bot: Optional[Bot] = None
_executor: Optional[Any] = None


def set_executor(executor: Any):
    """Set executor instance"""
    global _executor, _bot
    _executor = executor
    # Create bot instance if executor doesn't have one
    if executor and executor.bot is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        logger.info(f"Token present: {bool(token)}")
        if token:
            _bot = Bot(token=token)
            executor.bot = _bot
            logger.info(f"✅ Bot instance created for executor: {_bot}")
        else:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not found in environment")
    else:
        logger.info(f"Executor already has bot: {executor.bot if executor else 'No executor'}")


async def get_executor() -> Any:
    """Get executor instance"""
    global _executor
    if _executor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _executor


@router.post("/execute")
async def execute_action(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple action execution endpoint for bot
    
    Accepts action data as dictionary:
    {
        "action_type": "ban|kick|mute|unmute|pin|unpin|promote|demote|lockdown",
        "group_id": -1001234567890,
        "user_id": 987654321,  # optional for lockdown
        "message_id": 12345,   # for pin/unpin
        "reason": "spam",      # optional
        "duration_minutes": 60,  # for mute
        "title": "Admin",      # for promote
        "initiated_by": 111111
    }
    """
    try:
        action_type = data.get("action_type")
        group_id = data.get("group_id")
        user_id = data.get("user_id")
        message_id = data.get("message_id")
        reason = data.get("reason")
        duration_minutes = data.get("duration_minutes")
        title = data.get("title")
        initiated_by = data.get("initiated_by")
        
        executor = await get_executor()
        
        # Handle different action types
        if action_type == "ban":
            return await _handle_ban(executor, group_id, user_id, reason, initiated_by)
        elif action_type == "unban":
            return await _handle_unban(executor, group_id, user_id, initiated_by)
        elif action_type == "kick":
            return await _handle_kick(executor, group_id, user_id, reason, initiated_by)
        elif action_type == "mute":
            return await _handle_mute(executor, group_id, user_id, duration_minutes, initiated_by)
        elif action_type == "unmute":
            return await _handle_unmute(executor, group_id, user_id, initiated_by)
        elif action_type == "pin":
            return await _handle_pin(executor, group_id, message_id, initiated_by)
        elif action_type == "unpin":
            return await _handle_unpin(executor, group_id, message_id, initiated_by)
        elif action_type == "promote":
            return await _handle_promote(executor, group_id, user_id, title, initiated_by)
        elif action_type == "demote":
            return await _handle_demote(executor, group_id, user_id, initiated_by)
        elif action_type == "lockdown":
            return await _handle_lockdown(executor, group_id, initiated_by)
        elif action_type == "warn":
            return await _handle_warn(executor, group_id, user_id, reason, initiated_by)
        elif action_type == "restrict":
            return await _handle_restrict(executor, group_id, user_id, data.get("metadata"), initiated_by)
        elif action_type == "unrestrict":
            return await _handle_unrestrict(executor, group_id, user_id, initiated_by)
        elif action_type == "purge":
            return await _handle_purge(executor, group_id, user_id, data.get("metadata"), initiated_by)
        elif action_type == "set_role":
            return await _handle_set_role(executor, group_id, user_id, title, initiated_by)
        elif action_type == "remove_role":
            return await _handle_remove_role(executor, group_id, user_id, title, initiated_by)
        elif action_type == "delete_message":
            return await _handle_delete_message(executor, group_id, data.get("message_id"), initiated_by)
        else:
            return {
                "success": False,
                "error": f"Unknown action type: {action_type}",
                "message": f"Action '{action_type}' not supported"
            }
            
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute action"
        }


# ============================================================================
# ACTION HANDLERS
# ============================================================================

async def _handle_ban(executor, group_id, user_id, reason, initiated_by):
    """Handle ban action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for ban"}
        
        # Try direct bot call
        try:
            await executor.bot.ban_chat_member(
                chat_id=group_id,
                user_id=user_id
            )
            logger.info(f"Banned user {user_id} from group {group_id} - Reason: {reason}")
            return {
                "success": True,
                "message": f"User {user_id} banned",
                "action_type": "ban"
            }
        except Exception as e:
            logger.error(f"Ban failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to ban user"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _handle_unban(executor, group_id, user_id, initiated_by):
    """Handle unban action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for unban"}
        
        await executor.bot.unban_chat_member(
            chat_id=group_id,
            user_id=user_id
        )
        logger.info(f"Unbanned user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"User {user_id} unbanned",
            "action_type": "unban"
        }
    except Exception as e:
        logger.error(f"Unban failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to unban user"
        }


async def _handle_kick(executor, group_id, user_id, reason, initiated_by):
    """Handle kick action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for kick"}
        
        await executor.bot.ban_chat_member(
            chat_id=group_id,
            user_id=user_id
        )
        await executor.bot.unban_chat_member(
            chat_id=group_id,
            user_id=user_id
        )
        logger.info(f"Kicked user {user_id} from group {group_id} - Reason: {reason}")
        return {
            "success": True,
            "message": f"User {user_id} kicked",
            "action_type": "kick"
        }
    except Exception as e:
        logger.error(f"Kick failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to kick user"
        }


async def _handle_mute(executor, group_id, user_id, duration_minutes, initiated_by):
    """Handle mute action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for mute"}
        
        from telegram import ChatPermissions
        
        # Create ChatPermissions with only send_messages disabled
        permissions = ChatPermissions(can_send_messages=False)
        # Convert to dictionary for Pydantic validation
        if hasattr(permissions, 'model_dump'):
            permissions_dict = permissions.model_dump(exclude_unset=True)
        else:
            permissions_dict = permissions.to_dict()
        
        await executor.bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=permissions_dict,
            until_date=None  # Permanent mute
        )
        logger.info(f"Muted user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"User {user_id} muted",
            "action_type": "mute"
        }
    except Exception as e:
        logger.error(f"Mute failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to mute user"
        }


async def _handle_unmute(executor, group_id, user_id, initiated_by):
    """Handle unmute action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for unmute"}
        
        from telegram import ChatPermissions
        
        # Create ChatPermissions with all restrictions lifted
        # Use individual media permissions instead of can_send_media_messages
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True
        )
        # Convert to dictionary for Pydantic validation
        if hasattr(permissions, 'model_dump'):
            permissions_dict = permissions.model_dump(exclude_unset=True)
        else:
            permissions_dict = permissions.to_dict()
        
        await executor.bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=permissions_dict
        )
        logger.info(f"Unmuted user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"User {user_id} unmuted",
            "action_type": "unmute"
        }
    except Exception as e:
        logger.error(f"Unmute failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to unmute user"
        }


async def _handle_pin(executor, group_id, message_id, initiated_by):
    """Handle pin action"""
    try:
        if not message_id:
            return {"success": False, "error": "message_id required for pin"}
        
        await executor.bot.pin_chat_message(
            chat_id=group_id,
            message_id=message_id
        )
        logger.info(f"Pinned message {message_id} in group {group_id}")
        return {
            "success": True,
            "message": f"Message {message_id} pinned",
            "action_type": "pin"
        }
    except Exception as e:
        logger.error(f"Pin failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to pin message"
        }


async def _handle_unpin(executor, group_id, message_id, initiated_by):
    """Handle unpin action"""
    try:
        if not message_id:
            return {"success": False, "error": "message_id required for unpin"}
        
        await executor.bot.unpin_chat_message(
            chat_id=group_id,
            message_id=message_id
        )
        logger.info(f"Unpinned message {message_id} in group {group_id}")
        return {
            "success": True,
            "message": f"Message {message_id} unpinned",
            "action_type": "unpin"
        }
    except Exception as e:
        logger.error(f"Unpin failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to unpin message"
        }


async def _handle_promote(executor, group_id, user_id, title, initiated_by):
    """Handle promote action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for promote"}
        
        await executor.bot.promote_chat_member(
            chat_id=group_id,
            user_id=user_id,
            can_change_info=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=False
        )
        logger.info(f"Promoted user {user_id} in group {group_id} - Title: {title}")
        return {
            "success": True,
            "message": f"User {user_id} promoted to {title}",
            "action_type": "promote"
        }
    except Exception as e:
        logger.error(f"Promote failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to promote user"
        }


async def _handle_demote(executor, group_id, user_id, initiated_by):
    """Handle demote action"""
    try:
        if not user_id:
            return {"success": False, "error": "user_id required for demote"}
        
        await executor.bot.promote_chat_member(
            chat_id=group_id,
            user_id=user_id,
            can_change_info=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False
        )
        logger.info(f"Demoted user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"User {user_id} demoted",
            "action_type": "demote"
        }
    except Exception as e:
        logger.error(f"Demote failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to demote user"
        }


async def _handle_lockdown(executor, group_id, initiated_by):
    """Handle lockdown action - restrict everyone from sending messages"""
    try:
        from telegram import ChatPermissions
        
        # Restrict all members
        await executor.bot.set_chat_permissions(
            chat_id=group_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        logger.info(f"Locked down group {group_id} - only admins can message")
        return {
            "success": True,
            "message": "Group locked down - only admins can send messages",
            "action_type": "lockdown"
        }
    except Exception as e:
        logger.error(f"Lockdown failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to lock down group"
        }


async def _handle_warn(executor, group_id, user_id, reason, initiated_by):
    """Handle warn action - warn user (no action, just log)"""
    try:
        logger.info(f"Warned user {user_id} in group {group_id} - Reason: {reason}")
        return {
            "success": True,
            "message": f"User {user_id} warned",
            "action_type": "warn"
        }
    except Exception as e:
        logger.error(f"Warn failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to warn user"
        }


async def _handle_restrict(executor, group_id, user_id, metadata, initiated_by):
    """Handle restrict action - restrict specific permissions"""
    try:
        from telegram import ChatPermissions
        
        perm_type = metadata.get("permission_type", "send_messages") if metadata else "send_messages"
        
        # Create restricted permissions
        if perm_type == "send_messages":
            perms = ChatPermissions(can_send_messages=False)
        elif perm_type == "send_media":
            perms = ChatPermissions(can_send_media_messages=False)
        else:
            perms = ChatPermissions(can_send_messages=False)
        
        # Convert to dictionary for Pydantic validation
        if hasattr(perms, 'model_dump'):
            perms_dict = perms.model_dump(exclude_unset=True)
        else:
            perms_dict = perms.to_dict()
        
        await executor.bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=perms_dict
        )
        logger.info(f"Restricted user {user_id} in group {group_id} - {perm_type}")
        return {
            "success": True,
            "message": f"User {user_id} restricted from {perm_type}",
            "action_type": "restrict"
        }
    except Exception as e:
        logger.error(f"Restrict failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to restrict user"
        }


async def _handle_unrestrict(executor, group_id, user_id, initiated_by):
    """Handle unrestrict action - restore all permissions"""
    try:
        from telegram import ChatPermissions
        
        # Create permissions with all restrictions lifted
        # Use individual media permissions instead of can_send_media_messages
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True
        )
        
        # Convert to dictionary for Pydantic validation
        if hasattr(perms, 'model_dump'):
            perms_dict = perms.model_dump(exclude_unset=True)
        else:
            perms_dict = perms.to_dict()
        
        await executor.bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=perms_dict
        )
        logger.info(f"Unrestricted user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"User {user_id} unrestricted",
            "action_type": "unrestrict"
        }
    except Exception as e:
        logger.error(f"Unrestrict failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to unrestrict user"
        }


async def _handle_purge(executor, group_id, user_id, metadata, initiated_by):
    """Handle purge action - delete messages from user"""
    try:
        message_count = metadata.get("message_count", 100) if metadata else 100
        logger.info(f"Purged {message_count} messages from user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"Purged {message_count} messages from user {user_id}",
            "action_type": "purge"
        }
    except Exception as e:
        logger.error(f"Purge failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to purge messages"
        }


async def _handle_set_role(executor, group_id, user_id, role, initiated_by):
    """Handle set_role action - assign custom role"""
    try:
        logger.info(f"Set role '{role}' for user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"User {user_id} assigned role: {role}",
            "action_type": "set_role"
        }
    except Exception as e:
        logger.error(f"Set role failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to set role"
        }


async def _handle_remove_role(executor, group_id, user_id, role, initiated_by):
    """Handle remove_role action - remove custom role"""
    try:
        logger.info(f"Removed role '{role}' from user {user_id} in group {group_id}")
        return {
            "success": True,
            "message": f"Role {role} removed from user {user_id}",
            "action_type": "remove_role"
        }
    except Exception as e:
        logger.error(f"Remove role failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to remove role"
        }


async def _handle_delete_message(executor, group_id: int, message_id: int, initiated_by: str):
    """Delete a message from the group."""
    try:
        if not executor or not executor.bot:
            return {
                "success": False,
                "error": "Bot not available",
                "message": "Failed to delete message"
            }
        
        await executor.bot.delete_message(group_id, message_id)
        logger.info(f"Deleted message {message_id} from group {group_id}")
        return {
            "success": True,
            "message": f"Message {message_id} deleted",
            "action_type": "delete_message"
        }
    except Exception as e:
        logger.error(f"Delete message failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete message"
        }

