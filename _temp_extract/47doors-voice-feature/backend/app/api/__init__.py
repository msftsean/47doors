"""
API routes for the Front Door Support Agent.
"""

from fastapi import APIRouter

from app.api.routes import router
from app.api.realtime import realtime_router

# Combine all routers into one
api_router = APIRouter()
api_router.include_router(router)
api_router.include_router(realtime_router)

__all__ = ["router", "realtime_router", "api_router"]
