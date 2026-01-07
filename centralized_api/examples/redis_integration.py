"""
Example 3: Integrate with Redis Listeners
Shows how to route Redis-based web actions through the centralized API
"""

import asyncio
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from centralized_api.services import ActionExecutor
from centralized_api.models import (
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
from centralized_api.config import REDIS_URI

logger = logging.getLogger(__name__)


class RedisActionListener:
    """
    Listen for action requests from web dashboard via Redis
    and execute them through centralized API
    """

    def __init__(self, executor: ActionExecutor, redis_uri: str = REDIS_URI):
        """
        Initialize Redis listener
        
        Args:
            executor: ActionExecutor instance
            redis_uri: Redis connection URI
        """
        self.executor = executor
        self.redis_uri = redis_uri
        self.redis = None
        self.pubsub = None
        self._running = False

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(self.redis_uri)
            logger.info(f"Connected to Redis: {self.redis_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def start(self):
        """Start listening for action requests"""
        if self._running:
            logger.warning("Listener already running")
            return

        try:
            await self.connect()
            self._running = True
            
            # Subscribe to web action channel
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("web:actions")
            
            logger.info("Started listening for web actions on Redis")
            
            # Listen for messages
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self._handle_action_message(message['data'])
        
        except Exception as e:
            logger.error(f"Error in Redis listener: {str(e)}")
            self._running = False
            raise
        finally:
            await self.disconnect()

    async def _handle_action_message(self, data: bytes):
        """
        Handle incoming action message from Redis
        
        Expected format:
        {
            "action_type": "ban",
            "group_id": -1001234567890,
            "user_id": 987654321,
            "reason": "Spam",
            "initiated_by": 111111,
            "metadata": {...}
        }
        """
        try:
            action_data = json.loads(data)
            
            # Validate required fields
            if not action_data.get('action_type'):
                logger.warning("Missing action_type in Redis message")
                return
            
            if not action_data.get('group_id') or not action_data.get('user_id'):
                logger.warning("Missing group_id or user_id in Redis message")
                return
            
            # Create appropriate request object
            action_type = action_data.get('action_type')
            request = self._create_request(action_data)
            
            if not request:
                logger.warning(f"Could not create request for action: {action_type}")
                return
            
            # Execute via centralized API
            logger.info(f"Executing action from web: {action_type}")
            response = await self.executor.execute_action(request)
            
            # Publish result back to web via result channel
            result_channel = f"web:results:{response.action_id}"
            result_data = {
                "action_id": response.action_id,
                "status": response.status.value,
                "success": response.success,
                "message": response.message,
                "error": response.error,
                "execution_time_ms": response.execution_time_ms,
            }
            
            await self.redis.publish(result_channel, json.dumps(result_data))
            logger.info(f"Action result published: {response.action_id}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Redis message: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling action message: {str(e)}")

    def _create_request(self, action_data: dict):
        """
        Create appropriate request object from action data
        
        Args:
            action_data: Raw action data from Redis
            
        Returns:
            Appropriate ActionRequest subclass or None
        """
        try:
            action_type = action_data.get('action_type')
            
            common_params = {
                'group_id': action_data.get('group_id'),
                'user_id': action_data.get('user_id'),
                'reason': action_data.get('reason'),
                'initiated_by': action_data.get('initiated_by'),
                'metadata': action_data.get('metadata'),
            }
            
            if action_type == ActionType.BAN:
                return BanRequest(
                    **common_params,
                    until_date=action_data.get('until_date'),
                    revoke_messages=action_data.get('revoke_messages', True),
                )
            
            elif action_type == ActionType.KICK:
                return KickRequest(
                    **common_params,
                    revoke_messages=action_data.get('revoke_messages', False),
                )
            
            elif action_type == ActionType.MUTE:
                return MuteRequest(
                    **common_params,
                    duration=action_data.get('duration', 3600),
                )
            
            elif action_type == ActionType.UNMUTE:
                return UnmuteRequest(**common_params)
            
            elif action_type == ActionType.PROMOTE:
                return PromoteRequest(
                    **common_params,
                    permissions=action_data.get('permissions'),
                )
            
            elif action_type == ActionType.DEMOTE:
                return DemoteRequest(**common_params)
            
            elif action_type == ActionType.WARN:
                return WarnRequest(
                    **common_params,
                    warn_count=action_data.get('warn_count', 1),
                    auto_ban_after=action_data.get('auto_ban_after'),
                )
            
            elif action_type == ActionType.PIN:
                return PinRequest(
                    **common_params,
                    message_id=action_data.get('message_id'),
                    notify=action_data.get('notify', True),
                )
            
            elif action_type == ActionType.UNPIN:
                return UnpinRequest(
                    **common_params,
                    message_id=action_data.get('message_id'),
                )
            
            elif action_type == ActionType.DELETE_MESSAGE:
                return DeleteMessageRequest(
                    **common_params,
                    message_id=action_data.get('message_id'),
                )
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating request: {str(e)}")
            return None


# ============================================================================
# HELPER FUNCTION FOR WEB TO TRIGGER ACTIONS
# ============================================================================

async def web_publish_action(
    redis_uri: str = REDIS_URI,
    action_type: str = None,
    group_id: int = None,
    user_id: int = None,
    reason: str = None,
    initiated_by: int = None,
    **kwargs,
) -> str:
    """
    Publish action request from web to Redis for bot to execute
    
    Args:
        redis_uri: Redis connection string
        action_type: Type of action
        group_id: Telegram group ID
        user_id: Target user ID
        reason: Reason for action
        initiated_by: Admin that initiated
        **kwargs: Additional action-specific parameters
        
    Returns:
        action_id for tracking
    """
    try:
        redis = await aioredis.from_url(redis_uri)
        
        import uuid
        action_id = str(uuid.uuid4())
        
        action_data = {
            "action_id": action_id,
            "action_type": action_type,
            "group_id": group_id,
            "user_id": user_id,
            "reason": reason,
            "initiated_by": initiated_by,
            **kwargs,
        }
        
        # Publish to Redis
        await redis.publish("web:actions", json.dumps(action_data))
        
        logger.info(f"Web action published: {action_id} - {action_type}")
        
        await redis.close()
        return action_id
    
    except Exception as e:
        logger.error(f"Error publishing web action: {str(e)}")
        raise


# ============================================================================
# USAGE IN BOT STARTUP
# ============================================================================

"""
In your bot startup:

from centralized_api.examples.redis_integration import RedisActionListener
from centralized_api.services import ActionExecutor
from centralized_api.db import ActionDatabase

async def start_redis_listener(bot):
    # Initialize executor
    db = ActionDatabase()
    await db.connect()
    executor = ActionExecutor(bot=bot, db=db)
    
    # Start Redis listener
    listener = RedisActionListener(executor)
    asyncio.create_task(listener.start())

# In your dispatcher setup:
dp.startup.register(start_redis_listener)
"""

# ============================================================================
# USAGE IN WEB DASHBOARD
# ============================================================================

"""
In your web dashboard to trigger actions:

from centralized_api.examples.redis_integration import web_publish_action

# Example: Ban user from web
action_id = await web_publish_action(
    action_type="ban",
    group_id=-1001234567890,
    user_id=987654321,
    reason="Spam",
    initiated_by=111111,
)

# Track result
result = await redis.get(f"web:results:{action_id}")
"""
