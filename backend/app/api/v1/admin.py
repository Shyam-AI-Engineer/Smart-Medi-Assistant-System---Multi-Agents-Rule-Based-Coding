"""Admin router — aggregates analytics, audit, user, and assignment sub-routers."""
from fastapi import APIRouter

from .admin_analytics import router as analytics_router
from .admin_audit import router as audit_router
from .admin_users import router as users_router
from .admin_assignments import router as assignments_router

router = APIRouter(prefix="/admin")
router.include_router(analytics_router)
router.include_router(audit_router)
router.include_router(users_router)
router.include_router(assignments_router)
