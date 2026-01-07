"""
MongoDB Database Layer
Handles action logging and persistence
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from centralized_api.models import ActionStatus
from centralized_api.config import (
    MONGODB_URI,
    MONGODB_DATABASE,
    COLLECTION_ACTIONS,
    COLLECTION_DEAD_LETTERS,
    COLLECTION_WARNINGS,
)

logger = logging.getLogger(__name__)


class ActionDatabase:
    """
    MongoDB wrapper for action persistence and history
    """

    def __init__(self, uri: str = MONGODB_URI, database: str = MONGODB_DATABASE):
        """
        Initialize database connection
        
        Args:
            uri: MongoDB connection URI
            database: Database name
        """
        self.uri = uri
        self.database_name = database
        self.client: Optional[MongoClient] = None
        self.db = None
        self._connected = False

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
            )
            self.db = self.client[self.database_name]
            
            # Test connection
            self.db.command("ping")
            self._connected = True
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
            # Create indexes
            await self._create_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self._connected = False
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            actions_col = self.db[COLLECTION_ACTIONS]
            
            # Indexes for action logs
            actions_col.create_index([("action_id", ASCENDING)], unique=True)
            actions_col.create_index([("group_id", ASCENDING)])
            actions_col.create_index([("user_id", ASCENDING)])
            actions_col.create_index([("created_at", DESCENDING)])
            actions_col.create_index([("status", ASCENDING)])
            
            # Compound index for common queries
            actions_col.create_index([
                ("group_id", ASCENDING),
                ("created_at", DESCENDING),
            ])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create indexes: {str(e)}")

    async def log_action(
        self,
        action_id: str,
        action_type: str,
        group_id: int,
        user_id: int,
        initiated_by: Optional[int],
        status: ActionStatus,
        success: bool,
        message: str,
        reason: Optional[str] = None,
        error: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        retry_count: int = 0,
        api_response: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an action to database
        
        Args:
            action_id: Unique action identifier
            action_type: Type of action (from ActionType enum)
            group_id: Telegram group ID
            user_id: Target user ID
            initiated_by: Admin/bot that initiated action
            status: Action status
            success: Whether action succeeded
            message: Action message/result
            reason: Reason for action
            error: Error message if failed
            execution_time_ms: Execution time in milliseconds
            retry_count: Number of retries
            api_response: Response from Telegram API
            metadata: Additional metadata
            
        Returns:
            action_id
        """
        if not self._connected:
            logger.warning("Database not connected, skipping log")
            return action_id

        try:
            doc = {
                "action_id": action_id,
                "action_type": action_type,
                "group_id": group_id,
                "user_id": user_id,
                "initiated_by": initiated_by,
                "status": status.value if isinstance(status, ActionStatus) else status,
                "success": success,
                "message": message,
                "reason": reason,
                "error": error,
                "created_at": datetime.utcnow(),
                "executed_at": datetime.utcnow() if success else None,
                "execution_time_ms": execution_time_ms,
                "retry_count": retry_count,
                "api_response": api_response,
                "metadata": metadata,
            }

            self.db[COLLECTION_ACTIONS].insert_one(doc)
            logger.info(f"Action logged: {action_id} - {action_type}")
            return action_id

        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")
            return action_id

    async def log_dead_letter(
        self,
        action_id: str,
        request: Dict[str, Any],
        error: str,
        retry_count: int,
    ):
        """
        Log failed action to dead letter queue
        
        Args:
            action_id: Action identifier
            request: Original request data
            error: Error message
            retry_count: Number of retries attempted
        """
        if not self._connected:
            return

        try:
            doc = {
                "action_id": action_id,
                "request": request.dict() if hasattr(request, 'dict') else request,
                "error": error,
                "retry_count": retry_count,
                "created_at": datetime.utcnow(),
                "resolved": False,
            }

            self.db[COLLECTION_DEAD_LETTERS].insert_one(doc)
            logger.warning(f"Dead letter logged: {action_id}")

        except Exception as e:
            logger.error(f"Failed to log dead letter: {str(e)}")

    async def get_action_log(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve action log by ID
        
        Args:
            action_id: Action identifier
            
        Returns:
            Action log document or None
        """
        if not self._connected:
            return None

        try:
            doc = self.db[COLLECTION_ACTIONS].find_one({"action_id": action_id})
            return doc
        except Exception as e:
            logger.error(f"Failed to retrieve action log: {str(e)}")
            return None

    async def get_action_history(
        self,
        group_id: int,
        limit: int = 50,
        skip: int = 0,
        status: Optional[ActionStatus] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve action history for a group
        
        Args:
            group_id: Telegram group ID
            limit: Maximum number of results
            skip: Number of results to skip (pagination)
            status: Filter by status (optional)
            
        Returns:
            Dictionary with total count and action list
        """
        if not self._connected:
            return {"total": 0, "actions": []}

        try:
            query = {"group_id": group_id}
            if status:
                query["status"] = status.value if isinstance(status, ActionStatus) else status

            total = self.db[COLLECTION_ACTIONS].count_documents(query)
            actions = list(
                self.db[COLLECTION_ACTIONS]
                .find(query)
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )

            # Remove MongoDB _id field for cleaner response
            for action in actions:
                action.pop("_id", None)

            return {
                "total": total,
                "actions": actions,
            }

        except Exception as e:
            logger.error(f"Failed to retrieve action history: {str(e)}")
            return {"total": 0, "actions": []}

    async def update_action_status(
        self,
        action_id: str,
        status: ActionStatus,
    ) -> bool:
        """
        Update action status
        
        Args:
            action_id: Action identifier
            status: New status
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False

        try:
            result = self.db[COLLECTION_ACTIONS].update_one(
                {"action_id": action_id},
                {
                    "$set": {
                        "status": status.value if isinstance(status, ActionStatus) else status,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update action status: {str(e)}")
            return False

    async def increment_warning(
        self,
        group_id: int,
        user_id: int,
        increment: int = 1,
    ) -> int:
        """
        Increment user warning count
        
        Args:
            group_id: Telegram group ID
            user_id: User ID
            increment: Amount to increment
            
        Returns:
            New warning count
        """
        if not self._connected:
            return 0

        try:
            doc = self.db[COLLECTION_WARNINGS].find_one_and_update(
                {"group_id": group_id, "user_id": user_id},
                {
                    "$inc": {"warning_count": increment},
                    "$set": {"updated_at": datetime.utcnow()},
                },
                upsert=True,
                return_document=True,
            )
            return doc.get("warning_count", 0)

        except Exception as e:
            logger.error(f"Failed to increment warning: {str(e)}")
            return 0

    async def get_warnings(
        self,
        group_id: int,
        user_id: int,
    ) -> int:
        """
        Get user warning count
        
        Args:
            group_id: Telegram group ID
            user_id: User ID
            
        Returns:
            Warning count
        """
        if not self._connected:
            return 0

        try:
            doc = self.db[COLLECTION_WARNINGS].find_one({
                "group_id": group_id,
                "user_id": user_id,
            })
            return doc.get("warning_count", 0) if doc else 0

        except Exception as e:
            logger.error(f"Failed to get warnings: {str(e)}")
            return 0

    async def reset_warnings(
        self,
        group_id: int,
        user_id: int,
    ) -> bool:
        """
        Reset user warnings
        
        Args:
            group_id: Telegram group ID
            user_id: User ID
            
        Returns:
            True if successful
        """
        if not self._connected:
            return False

        try:
            result = self.db[COLLECTION_WARNINGS].update_one(
                {"group_id": group_id, "user_id": user_id},
                {
                    "$set": {
                        "warning_count": 0,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to reset warnings: {str(e)}")
            return False

    async def get_group_statistics(self, group_id: int) -> Dict[str, Any]:
        """
        Get action statistics for a group
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Statistics dictionary
        """
        if not self._connected:
            return {}

        try:
            total_actions = self.db[COLLECTION_ACTIONS].count_documents({
                "group_id": group_id
            })
            successful = self.db[COLLECTION_ACTIONS].count_documents({
                "group_id": group_id,
                "success": True,
            })
            failed = self.db[COLLECTION_ACTIONS].count_documents({
                "group_id": group_id,
                "success": False,
            })

            return {
                "group_id": group_id,
                "total_actions": total_actions,
                "successful": successful,
                "failed": failed,
                "success_rate": (successful / total_actions * 100) if total_actions > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {}
