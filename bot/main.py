"""
Telegram Bot Service - Main Entry Point
Independent bot service that communicates with centralized_api via HTTP
Handles all Telegram updates and commands
"""

import asyncio
import logging
import os
from typing import Optional
import html

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, BotCommand
import httpx

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CENTRALIZED_API_URL = os.getenv("CENTRALIZED_API_URL", "http://localhost:8000")
CENTRALIZED_API_KEY = os.getenv("CENTRALIZED_API_KEY", "shared-api-key")

if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment variables")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")


# ============================================================================
# BOT CLIENT FOR CENTRALIZED API
# ============================================================================

class CentralizedAPIClient:
    """HTTP client for communicating with centralized_api"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 30
    
    async def health_check(self) -> bool:
        """Check if centralized_api is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/health",
                    timeout=self.timeout
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def execute_action(self, action_data: dict) -> dict:
        """Execute an action through centralized_api"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/actions/execute",
                    json=action_data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {"error": str(e)}
    
    async def get_user_permissions(self, user_id: int, group_id: int) -> dict:
        """Get user permissions from centralized_api"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/rbac/users/{user_id}/permissions",
                    params={"group_id": group_id},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Get permissions failed: {e}")
            return {"error": str(e)}


def escape_error_message(error_msg: str) -> str:
    """Escape HTML special characters in error messages for safe Telegram delivery"""
    return html.escape(error_msg)


# Global instances
bot: Optional[Bot] = None
dispatcher: Optional[Dispatcher] = None
api_client: Optional[CentralizedAPIClient] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_user_reference(text: str) -> tuple[Optional[int], str]:
    """
    Parse user reference from command argument.
    Supports: user_id (int), @username (str)
    Returns: (user_id, reference_str) where one may be None
    """
    if not text:
        return None, ""
    
    text = text.strip()
    
    # Check if it's a username (starts with @)
    if text.startswith("@"):
        return None, text  # Return username to be resolved later
    
    # Try to parse as user_id
    try:
        user_id = int(text)
        return user_id, str(user_id)
    except ValueError:
        # Not an int, treat as username
        if not text.startswith("@"):
            text = "@" + text
        return None, text


async def get_user_id_from_reply(message: Message) -> Optional[int]:
    """
    Get user_id from replied message if available.
    Returns user_id of message author or None.
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    return None


# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "🤖 Welcome to the Telegram Bot!\n\n"
        "Available commands:\n"
        "/help - Show help\n"
        "/status - Bot status\n"
        "/ban - Ban user\n"
        "/kick - Kick user\n"
        "/mute - Mute user\n"
        "/unmute - Unmute user\n"
        "/pin - Pin message\n"
        "/unpin - Unpin message\n"
        "/promote - Promote user to admin\n"
        "/demote - Demote admin to user\n"
        "/lockdown - Lock group (only admins can message)"
    )


async def cmd_help(message: Message):
    """Handle /help command"""
    await message.answer(
        "📖 **Bot Commands**\n\n"
        "/start - Welcome message\n"
        "/status - Check bot and API status\n"
        "/ban - Ban a user (admin only)\n"
        "/unban - Unban a user (admin only)\n"
        "/kick - Kick a user (admin only)\n"
        "/mute - Mute a user (admin only)\n"
        "/unmute - Unmute a user (admin only)\n"
        "/pin - Pin a message (admin only)\n"
        "/unpin - Unpin a message (admin only)\n"
        "/promote - Promote user to admin (admin only)\n"
        "/demote - Demote admin to user (admin only)\n"
        "/lockdown - Lock group (only admins can message, admin only)",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_status(message: Message):
    """Handle /status command"""
    try:
        is_healthy = await api_client.health_check()
        status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
        
        await message.answer(
            f"🤖 **Bot Status**\n\n"
            f"Bot: ✅ Running\n"
            f"Centralized API: {status}\n"
            f"Version: 1.0.0",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_ban(message: Message):
    """Handle /ban command - Ban user
    Usage: /ban (reply to message) or /ban <user_id|@username> [reason]
    """
    try:
        user_id = None
        reason = "No reason"
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse reason from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                reason = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/ban (reply to message)\n/ban <user_id|@username> [reason]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            reason = args[2] if len(args) > 2 else "No reason"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /ban <user_id|@username>")
            return
        
        action_data = {
            "action_type": "ban",
            "group_id": message.chat.id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been banned")
            
    except Exception as e:
        logger.error(f"Ban command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unban(message: Message):
    """Handle /unban command - Unban user
    Usage: /unban (reply to message) or /unban <user_id|@username>
    """
    try:
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/unban (reply to message)\n/unban <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /unban <user_id|@username>")
            return
        
        action_data = {
            "action_type": "unban",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been unbanned")
            
    except Exception as e:
        logger.error(f"Unban command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_kick(message: Message):
    """Handle /kick command - Kick user
    Usage: /kick (reply to message) or /kick <user_id|@username> [reason]
    """
    try:
        user_id = None
        reason = "No reason"
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse reason from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                reason = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/kick (reply to message)\n/kick <user_id|@username> [reason]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            reason = args[2] if len(args) > 2 else "No reason"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /kick <user_id|@username>")
            return
        
        action_data = {
            "action_type": "kick",
            "group_id": message.chat.id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been kicked")
            
    except Exception as e:
        logger.error(f"Kick command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_mute(message: Message):
    """Handle /mute command - Mute user (forever by default)
    Usage: /mute (reply to message) or /mute <user_id|@username> [duration_minutes]
    """
    try:
        user_id = None
        duration = 0  # 0 = forever
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse duration from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                try:
                    duration = int(args[1])
                except ValueError:
                    pass
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/mute (reply to message)\n/mute <user_id|@username> [duration_minutes]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            
            # Parse duration if provided
            if len(args) > 2:
                try:
                    duration = int(args[2])
                except ValueError:
                    pass
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /mute <user_id|@username>")
            return
        
        action_data = {
            "action_type": "mute",
            "group_id": message.chat.id,
            "user_id": user_id,
            "duration_minutes": duration,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            error_msg = html.escape(result['error'])
            await message.answer(f"❌ Error: {error_msg}", parse_mode=None)
        else:
            duration_text = "forever" if duration == 0 else f"for {duration} minutes"
            await message.answer(f"✅ User {user_id} has been muted {duration_text}")
            
    except Exception as e:
        logger.error(f"Mute command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unmute(message: Message):
    """Handle /unmute command - Unmute user
    Usage: /unmute (reply to message) or /unmute <user_id|@username>
    """
    try:
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/unmute (reply to message)\n/unmute <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /unmute <user_id|@username>")
            return
        
        action_data = {
            "action_type": "unmute",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been unmuted")
            
    except Exception as e:
        logger.error(f"Unmute command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_pin(message: Message):
    """Handle /pin command - Pin a message
    Usage: /pin (reply to message) or /pin <message_id>
    """
    try:
        # /pin [message_id] (if no message_id, pins the replied message)
        args = message.text.split(maxsplit=1)
        
        message_id = None
        if message.reply_to_message:
            message_id = message.reply_to_message.message_id
        elif len(args) > 1:
            try:
                message_id = int(args[1])
            except ValueError:
                await message.answer("❌ Invalid message ID")
                return
        
        if not message_id:
            await message.answer("Usage:\n/pin (reply to message)\n/pin <message_id>")
            return
        
        action_data = {
            "action_type": "pin",
            "group_id": message.chat.id,
            "message_id": message_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ Message {message_id} has been pinned")
            
    except Exception as e:
        logger.error(f"Pin command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unpin(message: Message):
    """Handle /unpin command - Unpin a message
    Usage: /unpin (reply to message) or /unpin <message_id>
    """
    try:
        args = message.text.split(maxsplit=1)
        
        message_id = None
        if message.reply_to_message:
            message_id = message.reply_to_message.message_id
        elif len(args) > 1:
            try:
                message_id = int(args[1])
            except ValueError:
                await message.answer("❌ Invalid message ID")
                return
        
        if not message_id:
            await message.answer("Usage:\n/unpin (reply to message)\n/unpin <message_id>")
            return
        
        action_data = {
            "action_type": "unpin",
            "group_id": message.chat.id,
            "message_id": message_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ Message {message_id} has been unpinned")
            
    except Exception as e:
        logger.error(f"Unpin command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_promote(message: Message):
    """Handle /promote command - Promote user to admin
    Usage: /promote (reply to message) or /promote <user_id|@username> [title]
    """
    try:
        user_id = None
        title = "Admin"  # default
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse title from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                title = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/promote (reply to message)\n/promote <user_id|@username> [title]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            title = args[2] if len(args) > 2 else "Admin"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /promote <user_id|@username>")
            return
        
        action_data = {
            "action_type": "promote",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": title,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been promoted to {title}")
            
    except Exception as e:
        logger.error(f"Promote command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_demote(message: Message):
    """Handle /demote command - Demote admin to user
    Usage: /demote (reply to message) or /demote <user_id|@username>
    """
    try:
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/demote (reply to message)\n/demote <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /demote <user_id|@username>")
            return
        
        action_data = {
            "action_type": "demote",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} has been demoted")
            
    except Exception as e:
        logger.error(f"Demote command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_lockdown(message: Message):
    """Handle /lockdown command - Lock group (only admins can message)"""
    try:
        action_data = {
            "action_type": "lockdown",
            "group_id": message.chat.id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"🔒 Group has been locked. Only admins can send messages.")
            
    except Exception as e:
        logger.error(f"Lockdown command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def cmd_warn(message: Message):
    """Handle /warn command - Warn user
    Usage: /warn (reply to message) or /warn <user_id|@username> [reason]
    """
    try:
        user_id = None
        reason = "No reason"
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse reason from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                reason = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/warn (reply to message)\n/warn <user_id|@username> [reason]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            reason = args[2] if len(args) > 2 else "No reason"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /warn <user_id|@username>")
            return
        
        action_data = {
            "action_type": "warn",
            "group_id": message.chat.id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"⚠️ User {user_id} warned - Reason: {reason}")
            
    except Exception as e:
        logger.error(f"Warn command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_restrict(message: Message):
    """Handle /restrict command - Restrict user permissions
    Usage: /restrict (reply to message) or /restrict <user_id|@username> [permission_type]
    """
    try:
        user_id = None
        perm_type = "send_messages"  # default
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse permission type from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                perm_type = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/restrict (reply to message)\n/restrict <user_id|@username> [permission_type]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            perm_type = args[2] if len(args) > 2 else "send_messages"
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /restrict <user_id|@username>")
            return
        
        action_data = {
            "action_type": "restrict",
            "group_id": message.chat.id,
            "user_id": user_id,
            "metadata": {"permission_type": perm_type},
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"🔒 User {user_id} restricted from {perm_type}")
            
    except Exception as e:
        logger.error(f"Restrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_unrestrict(message: Message):
    """Handle /unrestrict command - Unrestrict user (restore permissions)
    Usage: /unrestrict (reply to message) or /unrestrict <user_id|@username>
    """
    try:
        user_id = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=1)
            
            if len(args) < 2:
                await message.answer("Usage:\n/unrestrict (reply to message)\n/unrestrict <user_id|@username>")
                return
            
            user_id, _ = parse_user_reference(args[1])
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /unrestrict <user_id|@username>")
            return
        
        action_data = {
            "action_type": "unrestrict",
            "group_id": message.chat.id,
            "user_id": user_id,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"✅ User {user_id} unrestricted - permissions restored")
            
    except Exception as e:
        logger.error(f"Unrestrict command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_purge(message: Message):
    """Handle /purge command - Delete multiple messages from user
    Usage: /purge (reply to message) or /purge <user_id|@username> [message_count]
    """
    try:
        user_id = None
        count = 100  # default
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse message count from command args if provided
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                try:
                    count = int(args[1])
                except ValueError:
                    pass
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 2:
                await message.answer("Usage:\n/purge (reply to message)\n/purge <user_id|@username> [message_count]")
                return
            
            user_id, _ = parse_user_reference(args[1])
            if len(args) > 2:
                try:
                    count = int(args[2])
                except ValueError:
                    pass
        
        if not user_id:
            await message.answer("❌ Could not identify user. Reply to a message or use /purge <user_id|@username>")
            return
        
        action_data = {
            "action_type": "purge",
            "group_id": message.chat.id,
            "user_id": user_id,
            "metadata": {"message_count": count},
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"🗑️ Purged {count} messages from user {user_id}")
            
    except Exception as e:
        logger.error(f"Purge command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_setrole(message: Message):
    """Handle /setrole command - Set custom role for user
    Usage: /setrole (reply to message with role) or /setrole <user_id|@username> <role_name>
    """
    try:
        user_id = None
        role = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse role from command args (required)
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                role = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 3:
                await message.answer("Usage:\n/setrole (reply to message with role)\n/setrole <user_id|@username> <role_name>")
                return
            
            user_id, _ = parse_user_reference(args[1])
            role = args[2]
        
        if not user_id or not role:
            await message.answer("❌ Could not identify user or role. Reply to a message or use /setrole <user_id|@username> <role>")
            return
        
        action_data = {
            "action_type": "set_role",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": role,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 User {user_id} assigned role: {role}")
            
    except Exception as e:
        logger.error(f"Set role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)


async def cmd_removerole(message: Message):
    """Handle /removerole command - Remove custom role from user
    Usage: /removerole (reply to message with role) or /removerole <user_id|@username> <role_name>
    """
    try:
        user_id = None
        role = None
        
        # Check if replying to a message
        if message.reply_to_message:
            user_id = await get_user_id_from_reply(message)
            # Parse role from command args (required)
            args = message.text.split(maxsplit=1)
            if len(args) > 1:
                role = args[1]
        else:
            # Direct command with user_id or username
            args = message.text.split(maxsplit=2)
            
            if len(args) < 3:
                await message.answer("Usage:\n/removerole (reply to message with role)\n/removerole <user_id|@username> <role_name>")
                return
            
            user_id, _ = parse_user_reference(args[1])
            role = args[2]
        
        if not user_id or not role:
            await message.answer("❌ Could not identify user or role. Reply to a message or use /removerole <user_id|@username> <role>")
            return
        
        action_data = {
            "action_type": "remove_role",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": role,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 Role {role} removed from user {user_id}")
            
    except Exception as e:
        logger.error(f"Remove role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}", parse_mode=None)
        
        action_data = {
            "action_type": "remove_role",
            "group_id": message.chat.id,
            "user_id": user_id,
            "title": role,
            "initiated_by": message.from_user.id
        }
        
        result = await api_client.execute_action(action_data)
        
        if "error" in result:
            await message.answer(f"❌ Error: {escape_error_message(result['error'])}", parse_mode=None)
        else:
            await message.answer(f"👤 Role {role} removed from user {user_id}")
            
    except ValueError:
        await message.answer("❌ Invalid user ID")
    except Exception as e:
        logger.error(f"Remove role command failed: {e}")
        await message.answer(f"❌ Error: {escape_error_message(str(e))}")


async def handle_message(message: Message):
    """Handle regular text messages"""
    try:
        logger.info(f"📨 Message from {message.from_user.username} ({message.from_user.id}): {message.text}")
        
        # Echo the message back
        await message.answer(
            f"🤖 Message received!\n\n"
            f"You said: {message.text}\n\n"
            f"Type /help to see available commands."
        )
    except Exception as e:
        logger.error(f"Message handler failed: {e}")
        await message.answer(f"❌ Error processing message: {str(e)}")


# ============================================================================
# BOT SETUP
# ============================================================================

async def setup_bot():
    """Initialize bot and dispatcher"""
    global bot, dispatcher, api_client
    
    try:
        logger.info("🚀 Starting Telegram Bot...")
        
        # Initialize API client
        api_client = CentralizedAPIClient(CENTRALIZED_API_URL, CENTRALIZED_API_KEY)
        
        # Check if centralized_api is healthy
        is_healthy = await api_client.health_check()
        if not is_healthy:
            logger.warning("⚠️ Centralized API is not healthy, continuing anyway...")
        else:
            logger.info("✅ Centralized API is healthy")
        
        # Initialize bot (without default parse_mode to avoid HTML parsing issues)
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Initialize dispatcher with memory storage
        storage = MemoryStorage()
        dispatcher = Dispatcher(storage=storage)
        
        # Register command handlers
        dispatcher.message.register(cmd_start, Command("start"))
        dispatcher.message.register(cmd_help, Command("help"))
        dispatcher.message.register(cmd_status, Command("status"))
        dispatcher.message.register(cmd_ban, Command("ban"))
        dispatcher.message.register(cmd_unban, Command("unban"))
        dispatcher.message.register(cmd_kick, Command("kick"))
        dispatcher.message.register(cmd_mute, Command("mute"))
        dispatcher.message.register(cmd_unmute, Command("unmute"))
        dispatcher.message.register(cmd_pin, Command("pin"))
        dispatcher.message.register(cmd_unpin, Command("unpin"))
        dispatcher.message.register(cmd_promote, Command("promote"))
        dispatcher.message.register(cmd_demote, Command("demote"))
        dispatcher.message.register(cmd_lockdown, Command("lockdown"))
        dispatcher.message.register(cmd_warn, Command("warn"))
        dispatcher.message.register(cmd_restrict, Command("restrict"))
        dispatcher.message.register(cmd_unrestrict, Command("unrestrict"))
        dispatcher.message.register(cmd_purge, Command("purge"))
        dispatcher.message.register(cmd_setrole, Command("setrole"))
        dispatcher.message.register(cmd_removerole, Command("removerole"))
        
        # Register general message handler (for non-command messages)
        dispatcher.message.register(handle_message)
        
        # Set bot commands
        await bot.set_my_commands([
            BotCommand(command="start", description="Welcome message"),
            BotCommand(command="help", description="Show help"),
            BotCommand(command="status", description="Bot status"),
            BotCommand(command="ban", description="Ban user (admin)"),
            BotCommand(command="kick", description="Kick user (admin)"),
            BotCommand(command="mute", description="Mute user (admin)"),
            BotCommand(command="unmute", description="Unmute user (admin)"),
            BotCommand(command="pin", description="Pin message (admin)"),
            BotCommand(command="unpin", description="Unpin message (admin)"),
            BotCommand(command="promote", description="Promote to admin (admin)"),
            BotCommand(command="demote", description="Demote admin (admin)"),
            BotCommand(command="lockdown", description="Lock group (admin)"),
            BotCommand(command="warn", description="Warn user (admin)"),
            BotCommand(command="restrict", description="Restrict user (admin)"),
            BotCommand(command="unrestrict", description="Unrestrict user (admin)"),
            BotCommand(command="purge", description="Delete user messages (admin)"),
            BotCommand(command="setrole", description="Set user role (admin)"),
            BotCommand(command="removerole", description="Remove user role (admin)"),
        ])
        
        logger.info("✅ Bot initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        raise


async def run_bot():
    """Run the bot"""
    try:
        logger.info("🤖 Bot is polling for updates...")
        await dispatcher.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot polling failed: {e}")
        raise


async def main():
    """Main entry point"""
    try:
        await setup_bot()
        await run_bot()
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        if bot:
            await bot.session.close()
            logger.info("✅ Bot session closed")


if __name__ == "__main__":
    asyncio.run(main())
