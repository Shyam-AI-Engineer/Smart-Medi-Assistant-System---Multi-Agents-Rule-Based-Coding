"""API v1 router aggregation.

Combines all v1 endpoints and includes them in FastAPI app.
"""
from fastapi import APIRouter

# Import routers from individual modules
from .chat import router as chat_router

# Aggregate all v1 routers
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(chat_router)

# Future routers to add:
# from .auth import router as auth_router
# from .patients import router as patients_router
# from .vitals import router as vitals_router
# from .medications import router as medications_router
# from .reports import router as reports_router
# from .admin import router as admin_router
#
# api_router.include_router(auth_router)
# api_router.include_router(patients_router)
# etc.

__all__ = ["api_router"]
