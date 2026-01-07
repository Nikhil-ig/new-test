"""
Centralized API - FastAPI Application
Core business logic service for RBAC, permissions, and audit logging
All bot and web services communicate through this API
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from centralized_api.config import API_PREFIX
from centralized_api.db.mongodb import ActionDatabase
from centralized_api.api.routes import router as action_router
from centralized_api.api.simple_actions import router as simple_actions_router, set_executor
from centralized_api.api.advanced_rbac_routes import register_advanced_rbac_routes
from centralized_api.services.executor import ActionExecutor
from centralized_api.services.superadmin_service import SuperadminService
from centralized_api.services.group_admin_service import GroupAdminService

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
_db: Optional[ActionDatabase] = None
_executor: Optional[ActionExecutor] = None
_superadmin_service: Optional[SuperadminService] = None
_group_admin_service: Optional[GroupAdminService] = None


async def init_services():
    """Initialize all services on startup"""
    global _db, _executor, _superadmin_service, _group_admin_service
    
    try:
        logger.info("🚀 Initializing Centralized API services...")
        
        # Initialize database
        _db = ActionDatabase()
        await _db.connect()
        logger.info("✅ MongoDB connected")
        
        # Initialize services (bot is optional for centralized API)
        _executor = ActionExecutor(bot=None, db=_db)
        _superadmin_service = SuperadminService(db=_db)
        _group_admin_service = GroupAdminService(db=_db)
        
        # Initialize simple actions executor (for bot compatibility)
        set_executor(_executor)
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


async def close_services():
    """Close all services on shutdown"""
    global _db
    
    try:
        logger.info("🛑 Shutting down services...")
        
        if _db:
            await _db.disconnect()
            logger.info("✅ MongoDB disconnected")
            
        logger.info("✅ All services closed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    await init_services()
    yield
    # Shutdown
    await close_services()


# Create FastAPI app
app = FastAPI(
    title="Centralized API",
    description="Core API service for bot and web services",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker and orchestration"""
    try:
        if _db is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Database not initialized"}
            )
        
        # Check database connection using the _connected flag
        if not _db._connected:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Database connection failed"}
            )
        
        return {
            "status": "healthy",
            "service": "centralized_api",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": str(e)}
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Centralized API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Action execution routes (Port 8000/api/actions/...)
app.include_router(action_router)

# Simple actions routes (Port 8000/api/actions/execute)
app.include_router(simple_actions_router)

# RBAC routes (Port 8000/api/rbac/...)
register_advanced_rbac_routes(app)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ============================================================================
# STARTUP/SHUTDOWN EVENTS (Alternative to lifespan)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Called on startup (for compatibility)"""
    logger.info("FastAPI startup event")


@app.on_event("shutdown")
async def shutdown():
    """Called on shutdown (for compatibility)"""
    logger.info("FastAPI shutdown event")


if __name__ == "__main__":
    import uvicorn
    
    # Run with: python -m uvicorn app:app --reload
    # Or: python app.py
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
