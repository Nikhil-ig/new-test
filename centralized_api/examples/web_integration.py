"""
Example 2: Integrate Centralized API with Web Dashboard
Shows how to create FastAPI endpoints that use the action executor
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from centralized_api.api import router as actions_router
from centralized_api.api import set_executor
from centralized_api.services import ActionExecutor
from centralized_api.db import ActionDatabase

logger = logging.getLogger(__name__)


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

def create_app(bot) -> FastAPI:
    """
    Create FastAPI application with centralized API
    """
    app = FastAPI(
        title="Telegram Bot Dashboard",
        description="Web dashboard for telegram bot management",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store bot instance
    app.bot = bot
    
    # Startup event
    @app.on_event("startup")
    async def startup():
        """Initialize executor on startup"""
        try:
            # Initialize database
            db = ActionDatabase()
            await db.connect()
            
            # Initialize executor
            executor = ActionExecutor(bot=bot, db=db)
            
            # Set executor in router
            set_executor(executor)
            
            logger.info("Web API executor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize executor: {str(e)}")
            raise
    
    # Include centralized API routes
    app.include_router(actions_router)
    
    # Additional custom endpoints
    app.include_router(create_dashboard_router())
    
    return app


# ============================================================================
# CUSTOM DASHBOARD ENDPOINTS
# ============================================================================

def create_dashboard_router():
    """Create custom dashboard-specific endpoints"""
    from fastapi import APIRouter
    from pydantic import BaseModel
    from typing import Optional
    
    router = APIRouter(prefix="/api/v1", tags=["dashboard"])
    
    # =========================================================================
    # GROUP MANAGEMENT
    # =========================================================================
    
    @router.get("/groups/{group_id}/info")
    async def get_group_info(group_id: int):
        """Get group information and statistics"""
        try:
            from centralized_api.api import get_executor
            executor = await get_executor()
            
            stats = await executor.db.get_group_statistics(group_id)
            return stats
        except Exception as e:
            logger.error(f"Error getting group info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # =========================================================================
    # BULK ACTIONS
    # =========================================================================
    
    class BulkBanRequest(BaseModel):
        """Request to ban multiple users"""
        group_id: int
        user_ids: list[int]
        reason: Optional[str] = None
        initiated_by: Optional[int] = None
    
    
    @router.post("/groups/{group_id}/bulk-ban")
    async def bulk_ban(group_id: int, request: BulkBanRequest):
        """Ban multiple users at once"""
        try:
            from centralized_api.models import BanRequest
            from centralized_api.api import get_executor
            
            executor = await get_executor()
            
            # Create ban requests for each user
            ban_requests = [
                BanRequest(
                    group_id=group_id,
                    user_id=user_id,
                    reason=request.reason,
                    initiated_by=request.initiated_by,
                )
                for user_id in request.user_ids
            ]
            
            # Execute batch
            responses = await executor.execute_batch(ban_requests)
            
            success_count = sum(1 for r in responses if r.success)
            
            return {
                "total": len(responses),
                "successful": success_count,
                "failed": len(responses) - success_count,
                "responses": responses,
            }
        
        except Exception as e:
            logger.error(f"Error in bulk ban: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================
    
    @router.get("/groups/{group_id}/users/{user_id}/warnings")
    async def get_user_warnings(group_id: int, user_id: int):
        """Get user warning count"""
        try:
            from centralized_api.api import get_executor
            executor = await get_executor()
            
            warnings = await executor.db.get_warnings(
                group_id=group_id,
                user_id=user_id,
            )
            
            return {
                "group_id": group_id,
                "user_id": user_id,
                "warning_count": warnings,
            }
        
        except Exception as e:
            logger.error(f"Error getting warnings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.post("/groups/{group_id}/users/{user_id}/reset-warnings")
    async def reset_user_warnings(group_id: int, user_id: int):
        """Reset user warnings"""
        try:
            from centralized_api.api import get_executor
            executor = await get_executor()
            
            success = await executor.db.reset_warnings(
                group_id=group_id,
                user_id=user_id,
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "success": True,
                "message": "Warnings reset successfully",
                "group_id": group_id,
                "user_id": user_id,
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting warnings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # =========================================================================
    # MODERATION LOGS
    # =========================================================================
    
    @router.get("/groups/{group_id}/audit-log")
    async def get_audit_log(
        group_id: int,
        limit: int = 100,
        skip: int = 0,
        status: Optional[str] = None,
    ):
        """Get moderation audit log"""
        try:
            from centralized_api.api import get_executor
            from centralized_api.models import ActionStatus
            
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
            
            return history
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting audit log: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # =========================================================================
    # DASHBOARD STATUS
    # =========================================================================
    
    @router.get("/dashboard/status")
    async def get_dashboard_status():
        """Get overall dashboard status"""
        try:
            from centralized_api.api import get_executor
            executor = await get_executor()
            
            return {
                "status": "operational",
                "pending_actions": executor.get_pending_actions_count(),
                "database": "connected" if executor.db._connected else "disconnected",
                "executor": "ready",
            }
        
        except Exception as e:
            logger.error(f"Error getting dashboard status: {str(e)}")
            raise HTTPException(status_code=503, detail="Service unavailable")
    
    return router


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
To use this in your FastAPI application:

from src.bot import bot
from centralized_api.examples.web_integration import create_app

# Create app with bot instance
app = create_app(bot)

# Run with: uvicorn centralized_api.examples.web_integration:app --reload

# Available endpoints:
# POST /api/v1/actions/execute - Execute single action
# POST /api/v1/actions/batch - Execute batch actions
# GET /api/v1/actions/history - Get action history
# GET /api/v1/actions/status/{action_id} - Check action status
# DELETE /api/v1/actions/cancel/{action_id} - Cancel action
# 
# Dashboard endpoints:
# GET /api/v1/groups/{group_id}/info - Group statistics
# POST /api/v1/groups/{group_id}/bulk-ban - Bulk ban users
# GET /api/v1/groups/{group_id}/users/{user_id}/warnings - Get warnings
# GET /api/v1/dashboard/status - Dashboard status
"""
