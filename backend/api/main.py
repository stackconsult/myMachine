"""
Main API router for CEP Machine Backend
"""

from fastapi import APIRouter
from .tools import router as tools_router
from .file_upload import router as file_upload_router
from .analytics import router as analytics_router
from .auth import router as auth_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(tools_router)
api_router.include_router(file_upload_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)

# API health check
@api_router.get("/health")
async def api_health():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "service": "cep-machine-api",
        "version": "1.0.0"
    }
