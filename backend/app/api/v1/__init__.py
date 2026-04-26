"""API v1 router aggregation."""
from fastapi import APIRouter

from .chat import router as chat_router
from .auth import router as auth_router
from .patients import router as patients_router
from .vitals import router as vitals_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(vitals_router)
api_router.include_router(chat_router)

# Future routers:
# from .vitals import router as vitals_router
# from .medications import router as medications_router
# from .reports import router as reports_router
# from .admin import router as admin_router

__all__ = ["api_router"]
