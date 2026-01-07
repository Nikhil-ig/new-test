"""
Web Service - FastAPI Application
REST API service for web dashboards and clients
Communicates with centralized_api for business logic
Provides authentication, user management, and dashboard APIs
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
CENTRALIZED_API_URL = os.getenv("CENTRALIZED_API_URL", "http://localhost:8000")
CENTRALIZED_API_KEY = os.getenv("CENTRALIZED_API_KEY", "shared-api-key")
SECRET_KEY = os.getenv("SECRET_KEY", "web-secret-key-change-in-production")


# ============================================================================
# DATA MODELS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


class User(BaseModel):
    """User model"""
    id: int
    username: str
    email: str
    role: str


class Group(BaseModel):
    """Group model"""
    id: int
    name: str
    description: str
    members_count: int


class ActionRequest(BaseModel):
    """Action request model"""
    action_type: str
    group_id: int
    user_id: int
    reason: Optional[str] = None


# ============================================================================
# CENTRALIZED API CLIENT
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
    
    async def get_users(self) -> dict:
        """Get all users from centralized_api"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/rbac/users",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Get users failed: {e}")
            return {"error": str(e)}
    
    async def get_groups(self) -> dict:
        """Get all groups from centralized_api"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/rbac/groups",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Get groups failed: {e}")
            return {"error": str(e)}


# Global instances
_api_client: Optional[CentralizedAPIClient] = None


async def init_services():
    """Initialize services on startup"""
    global _api_client
    
    try:
        logger.info("🚀 Initializing Web Service...")
        
        # Initialize API client
        _api_client = CentralizedAPIClient(CENTRALIZED_API_URL, CENTRALIZED_API_KEY)
        
        # Check if centralized_api is healthy
        is_healthy = await _api_client.health_check()
        if is_healthy:
            logger.info("✅ Centralized API is healthy")
        else:
            logger.warning("⚠️ Centralized API is not responding, service will run in degraded mode")
        
        logger.info("✅ Web Service initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


async def close_services():
    """Close services on shutdown"""
    try:
        logger.info("🛑 Shutting down Web Service...")
        logger.info("✅ Web Service closed successfully")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    await init_services()
    yield
    # Shutdown
    await close_services()


# Create FastAPI app
app = FastAPI(
    title="Web Service",
    description="Web API for bot management and dashboards",
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
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    try:
        if _api_client is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "reason": "Service not initialized"}
            )
        
        is_centralized_healthy = await _api_client.health_check()
        
        return {
            "status": "healthy",
            "service": "web_service",
            "version": "1.0.0",
            "centralized_api": "connected" if is_centralized_healthy else "disconnected"
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
        "service": "Web Service",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }


# ============================================================================
# USERS ENDPOINTS
# ============================================================================

@app.get("/api/users")
async def get_users():
    """Get all users"""
    try:
        if _api_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        result = await _api_client.get_users()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/users")
async def create_user(user_data: dict):
    """Create a new user"""
    try:
        if _api_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # This would be implemented in centralized_api
        raise HTTPException(status_code=501, detail="Not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GROUPS ENDPOINTS
# ============================================================================

@app.get("/api/groups")
async def get_groups():
    """Get all groups"""
    try:
        if _api_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        result = await _api_client.get_groups()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get groups failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/groups")
async def create_group(group_data: dict):
    """Create a new group"""
    try:
        if _api_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # This would be implemented in centralized_api
        raise HTTPException(status_code=501, detail="Not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create group failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ACTIONS ENDPOINTS
# ============================================================================

@app.post("/api/actions/execute")
async def execute_action(action: ActionRequest):
    """Execute an action"""
    try:
        if _api_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        action_data = action.dict()
        result = await _api_client.execute_action(action_data)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute action failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        if _api_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Get stats from centralized_api
        users = await _api_client.get_users()
        groups = await _api_client.get_groups()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "users_count": len(users) if isinstance(users, list) else 0,
            "groups_count": len(groups) if isinstance(groups, list) else 0,
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"Get dashboard stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
