"""
Example 1: Integrate Centralized API with Bot Commands
Shows how to update existing bot command handlers to use the action executor
"""

# ============================================================================
# IN YOUR BOT STARTUP (e.g., src/bot/main.py)
# ============================================================================

# Add these imports at the top:
from centralized_api.services import ActionExecutor
from centralized_api.db import ActionDatabase


# In your bot startup function, initialize the executor:
async def bot_startup(bot):
    """
    Initialize bot and centralized API executor
    """
    # ... existing startup code ...
    
    # Initialize database
    db = ActionDatabase()
    await db.connect()
    
    # Initialize action executor with bot and database
    bot.executor = ActionExecutor(bot=bot, db=db)
    
    # Store for later use
    bot.action_db = db
    
    logger.info("Centralized API executor initialized")


# ============================================================================
# EXAMPLE: /ban COMMAND HANDLER
# ============================================================================

from aiogram import types, Router
from aiogram.filters import Command
from centralized_api.models import BanRequest

router = Router()


@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    """
    /ban @username [reason]
    Ban user from group using centralized API
    """
    try:
        # Parse command: /ban @username reason
        args = message.text.split(maxsplit=2)
        
        if len(args) < 2:
            await message.reply("Usage: /ban @username [reason]")
            return
        
        username_or_id = args[1]
        reason = args[2] if len(args) > 2 else "No reason provided"
        
        # Get user ID from mention or direct ID
        user_id = await get_user_id(message, username_or_id)
        if not user_id:
            await message.reply("User not found")
            return
        
        # Create ban request
        ban_request = BanRequest(
            group_id=message.chat.id,
            user_id=user_id,
            reason=reason,
            initiated_by=message.from_user.id,
        )
        
        # Execute via centralized API
        executor = message.bot.executor
        response = await executor.execute_action(ban_request)
        
        # Reply to user
        if response.success:
            await message.reply(f"✅ {response.message}")
        else:
            await message.reply(f"❌ {response.error or response.message}")
    
    except Exception as e:
        logger.error(f"Error in ban command: {str(e)}")
        await message.reply(f"Error: {str(e)}")


# ============================================================================
# EXAMPLE: /kick COMMAND HANDLER
# ============================================================================

from centralized_api.models import KickRequest


@router.message(Command("kick"))
async def cmd_kick(message: types.Message):
    """
    /kick @username [reason]
    Kick user from group using centralized API
    """
    try:
        args = message.text.split(maxsplit=2)
        
        if len(args) < 2:
            await message.reply("Usage: /kick @username [reason]")
            return
        
        username_or_id = args[1]
        reason = args[2] if len(args) > 2 else "No reason provided"
        
        user_id = await get_user_id(message, username_or_id)
        if not user_id:
            await message.reply("User not found")
            return
        
        # Create kick request
        kick_request = KickRequest(
            group_id=message.chat.id,
            user_id=user_id,
            reason=reason,
            initiated_by=message.from_user.id,
        )
        
        # Execute via centralized API
        executor = message.bot.executor
        response = await executor.execute_action(kick_request)
        
        if response.success:
            await message.reply(f"✅ {response.message}")
        else:
            await message.reply(f"❌ {response.error or response.message}")
    
    except Exception as e:
        logger.error(f"Error in kick command: {str(e)}")
        await message.reply(f"Error: {str(e)}")


# ============================================================================
# EXAMPLE: /mute COMMAND HANDLER
# ============================================================================

from centralized_api.models import MuteRequest


@router.message(Command("mute"))
async def cmd_mute(message: types.Message):
    """
    /mute @username [duration_in_seconds]
    Mute user for specified duration
    """
    try:
        args = message.text.split()
        
        if len(args) < 2:
            await message.reply("Usage: /mute @username [duration]")
            return
        
        username_or_id = args[1]
        duration = int(args[2]) if len(args) > 2 else 3600  # Default 1 hour
        
        if duration < 60:
            await message.reply("Minimum mute duration is 60 seconds")
            return
        
        user_id = await get_user_id(message, username_or_id)
        if not user_id:
            await message.reply("User not found")
            return
        
        # Create mute request
        mute_request = MuteRequest(
            group_id=message.chat.id,
            user_id=user_id,
            duration=duration,
            initiated_by=message.from_user.id,
        )
        
        # Execute via centralized API
        executor = message.bot.executor
        response = await executor.execute_action(mute_request)
        
        if response.success:
            await message.reply(f"✅ {response.message}")
        else:
            await message.reply(f"❌ {response.error or response.message}")
    
    except Exception as e:
        logger.error(f"Error in mute command: {str(e)}")
        await message.reply(f"Error: {str(e)}")


# ============================================================================
# EXAMPLE: /warn COMMAND HANDLER
# ============================================================================

from centralized_api.models import WarnRequest


@router.message(Command("warn"))
async def cmd_warn(message: types.Message):
    """
    /warn @username [reason]
    Warn user (increase warning count)
    """
    try:
        args = message.text.split(maxsplit=2)
        
        if len(args) < 2:
            await message.reply("Usage: /warn @username [reason]")
            return
        
        username_or_id = args[1]
        reason = args[2] if len(args) > 2 else "No reason"
        
        user_id = await get_user_id(message, username_or_id)
        if not user_id:
            await message.reply("User not found")
            return
        
        # Create warn request
        warn_request = WarnRequest(
            group_id=message.chat.id,
            user_id=user_id,
            reason=reason,
            initiated_by=message.from_user.id,
            warn_count=1,
        )
        
        # Execute via centralized API
        executor = message.bot.executor
        response = await executor.execute_action(warn_request)
        
        # Get current warning count
        warnings = await message.bot.action_db.get_warnings(
            group_id=message.chat.id,
            user_id=user_id,
        )
        
        if response.success:
            await message.reply(
                f"⚠️ User warned. Total warnings: {warnings}"
            )
        else:
            await message.reply(f"❌ {response.error or response.message}")
    
    except Exception as e:
        logger.error(f"Error in warn command: {str(e)}")
        await message.reply(f"Error: {str(e)}")


# ============================================================================
# HELPER FUNCTION
# ============================================================================

async def get_user_id(message: types.Message, username_or_id: str) -> int:
    """
    Get user ID from username mention or direct ID
    """
    try:
        # If it's a direct ID
        if username_or_id.isdigit():
            return int(username_or_id)
        
        # If it's a mention (@username)
        if username_or_id.startswith("@"):
            # Try to get from reply
            if message.reply_to_message and message.reply_to_message.from_user:
                return message.reply_to_message.from_user.id
            
            # Otherwise would need to lookup by username (requires member list)
            # For now, return None
            return None
        
        return None
    except Exception as e:
        logger.error(f"Error getting user ID: {str(e)}")
        return None


# ============================================================================
# SHUTDOWN HANDLER
# ============================================================================

async def bot_shutdown(bot):
    """
    Cleanup on bot shutdown
    """
    if hasattr(bot, 'action_db'):
        await bot.action_db.disconnect()
    logger.info("Centralized API executor shutdown complete")
