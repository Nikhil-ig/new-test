"""
FastAPI Routes for Centralized API
Endpoints for action execution and management
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from centralized_api.models import (
    ActionRequest,
    ActionResponse,
    ActionStatus,
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
from centralized_api.services import ActionExecutor
from centralized_api.db import ActionDatabase
from centralized_api.config import API_PREFIX

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix=API_PREFIX, tags=["actions"])

# Global executor instance (will be initialized in app startup)
_executor: Optional[ActionExecutor] = None


async def get_executor() -> ActionExecutor:
    """Get executor instance"""
    global _executor
    if _executor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _executor


def set_executor(executor: ActionExecutor):
    """Set executor instance"""
    global _executor
    _executor = executor


# ============================================================================
# ACTION EXECUTION ENDPOINTS
# ============================================================================

@router.post("/actions/execute", response_model=ActionResponse)
async def execute_action(request: ActionRequest) -> ActionResponse:
    """
    Execute a single action
    
    Supports all action types:
    - ban, kick, mute, unmute, promote, demote, warn, pin, unpin, delete_message, etc.
    
    Example:
    ```json
    {
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_id": 987654321,
        "reason": "Spam",
        "initiated_by": 111111
    }
    ```
    """
    try:
        executor = await get_executor()
        response = await executor.execute_action(request)
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/actions/batch", response_model=List[ActionResponse])
async def execute_batch(requests: List[ActionRequest]) -> List[ActionResponse]:
    """
    Execute multiple actions in batch
    
    All actions are executed concurrently for speed.
    
    Example:
    ```json
    [
        {
            "action_type": "ban",
            "group_id": -1001234567890,
            "user_id": 111111,
            "reason": "Spam"
        },
        {
            "action_type": "mute",
            "group_id": -1001234567890,
            "user_id": 222222,
            "duration": 3600
        }
    ]
    ```
    """
    try:
        if not requests:
            raise ValueError("Batch must contain at least one action")

        if len(requests) > 100:
            raise ValueError("Batch size limited to 100 actions")

        executor = await get_executor()
        responses = await executor.execute_batch(requests)
        return responses

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing batch: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ACTION STATUS & HISTORY ENDPOINTS
# ============================================================================

@router.get("/actions/status/{action_id}", response_model=ActionResponse)
async def get_action_status(
    action_id: str = Path(..., description="Action ID")
) -> ActionResponse:
    """
    Get current status of an action
    
    Returns the action status, whether it's pending, in progress, succeeded, or failed.
    """
    try:
        executor = await get_executor()
        response = await executor.get_action_status(action_id)

        if response is None:
            raise HTTPException(status_code=404, detail="Action not found")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/actions/history")
async def get_action_history(
    group_id: int = Query(..., description="Telegram group ID"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    skip: int = Query(0, ge=0, description="Results to skip"),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> dict:
    """
    Get action history for a group with pagination
    
    Supports filtering by status: pending, in_progress, success, failed, cancelled, retrying
    
    Example: `/api/v1/actions/history?group_id=-1001234567890&limit=50&skip=0`
    """
    try:
        executor = await get_executor()
        
        status_enum = None
        if status:
            try:
                status_enum = ActionStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        history = await executor.get_action_history(
            group_id=group_id,
            limit=limit,
            skip=skip,
        )

        return {
            "group_id": group_id,
            "total": history.get("total", 0),
            "limit": limit,
            "skip": skip,
            "actions": history.get("actions", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ACTION MANAGEMENT ENDPOINTS
# ============================================================================

@router.delete("/actions/cancel/{action_id}")
async def cancel_action(
    action_id: str = Path(..., description="Action ID")
) -> dict:
    """
    Cancel a pending action
    
    Only works for actions that are still pending.
    Already executed actions cannot be cancelled.
    """
    try:
        executor = await get_executor()
        success = await executor.cancel_action(action_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Action not found or already completed"
            )

        return {
            "success": True,
            "message": f"Action {action_id} cancelled successfully",
            "action_id": action_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    try:
        executor = await get_executor()
        return {
            "status": "healthy",
            "pending_actions": executor.get_pending_actions_count(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/actions/stats/{group_id}")
async def get_group_statistics(
    group_id: int = Path(..., description="Telegram group ID")
) -> dict:
    """
    Get action statistics for a group
    
    Returns total actions, success rate, etc.
    """
    try:
        executor = await get_executor()
        db = executor.db
        stats = await db.get_group_statistics(group_id)

        if not stats:
            raise HTTPException(status_code=404, detail="No data for group")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@router.get("/actions/dead-letters")
async def get_dead_letters() -> dict:
    """
    Get dead letter queue (failed actions that couldn't be recovered)
    
    Useful for debugging and manual intervention.
    """
    try:
        executor = await get_executor()
        db = executor.db

        if not db._connected:
            raise HTTPException(status_code=503, detail="Database not connected")

        dead_letters = list(
            db.db["action_dead_letters"].find().sort("created_at", -1).limit(100)
        )

        for doc in dead_letters:
            doc.pop("_id", None)

        return {
            "count": len(dead_letters),
            "dead_letters": dead_letters,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dead letters: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# HELPER ENDPOINTS
# ============================================================================

@router.get("/actions/pending-count")
async def get_pending_count() -> dict:
    """Get number of currently pending actions"""
    try:
        executor = await get_executor()
        return {
            "pending_count": executor.get_pending_actions_count(),
        }
    except Exception as e:
        logger.error(f"Error getting pending count: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
