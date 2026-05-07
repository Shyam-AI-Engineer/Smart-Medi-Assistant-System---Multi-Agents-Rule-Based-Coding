"""FastAPI app factory."""
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env FIRST, before anything else
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
import sys
import io

from app.api.v1 import api_router
from app.middleware.rate_limit import limiter
from app.middleware.request_id import RequestIDMiddleware, get_request_id
from app.exceptions import (
    NotFoundError,
    ConflictError,
    AuthenticationError,
    ForbiddenError,
    DomainValidationError,
)


class _RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


# Fix Windows encoding issue: configure logging with UTF-8
handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(name)s] %(levelname)s [rid=%(request_id)s]: %(message)s"
))
handler.addFilter(_RequestIDFilter())

# Configure logging for the application
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler],
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Includes:
    - CORS middleware (for frontend)
    - API v1 routes
    - Database initialization
    - Error handlers
    """
    app = FastAPI(
        title="Smart Medi Assistant API",
        version="0.1.0",
        description="Multi-agent AI medical assistant with RAG",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        redirect_slashes=False,
    )

    # ========================================
    # EXCEPTION HANDLERS
    # ========================================

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(_request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.detail})

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(_request: Request, exc: ForbiddenError):
        return JSONResponse(status_code=403, content={"detail": exc.detail})

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(_request: Request, exc: DomainValidationError):
        return JSONResponse(status_code=400, content={"detail": exc.detail})

    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        """Return validation errors for debugging."""
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={"debug_errors": errors, "error_count": len(errors)},
        )

    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    async def global_exception_handler(_request: Request, exc: Exception):
        """Handle unexpected exceptions with generic message (no internal details)."""
        logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

    app.add_exception_handler(Exception, global_exception_handler)

    # Rate limit exception handler
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, _exc: RateLimitExceeded):
        """Return 429 Too Many Requests on rate limit exceeded."""
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Maximum 10 requests per minute."},
        )

    # ========================================
    # MIDDLEWARE
    # ========================================

    # Request ID — must be outermost so the ID is set before any other middleware logs
    app.add_middleware(RequestIDMiddleware)

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # CORS - Allow frontend to call backend.
    # Supports both JSON array and comma-separated string in CORS_ORIGINS.
    _cors_raw = os.getenv("CORS_ORIGINS", "")
    if _cors_raw.strip().startswith("["):
        import json as _json
        try:
            cors_origins = _json.loads(_cors_raw)
        except Exception:
            cors_origins = []
    elif _cors_raw:
        cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
    else:
        cors_origins = []

    # Always allow local dev and the production Vercel frontend.
    _always_allowed = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://smart-medi-frontend.vercel.app",
    ]
    for _origin in _always_allowed:
        if _origin not in cors_origins:
            cors_origins.append(_origin)

    logger.info(f"CORS allowed origins: {cors_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================
    # STARTUP & SHUTDOWN
    # ========================================

    @app.on_event("startup")
    def startup_event():
        """Apply Alembic migrations on startup (skipped in test environment)."""
        logger.info("Starting Smart Medi Assistant API")
        if os.getenv("ENVIRONMENT") == "test":
            # Tests create their own in-memory SQLite DB via conftest.py fixtures.
            logger.info("Test environment: skipping database migration")
            return
        try:
            from alembic.config import Config
            from alembic import command as alembic_command
            # Use absolute path so this works regardless of cwd (Docker, Railway, etc.)
            alembic_ini = Path(__file__).parent.parent / "alembic.ini"
            alembic_cfg = Config(str(alembic_ini))
            alembic_command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations applied")
        except Exception as e:
            logger.error(f"Database migration failed: {e}")

    @app.on_event("shutdown")
    def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down Smart Medi Assistant API")

    # ========================================
    # ROUTES
    # ========================================

    # Include v1 API routes
    app.include_router(api_router)

    # ========================================
    # ROOT HEALTH CHECK
    # ========================================

    @app.get(
        "/",
        summary="Root endpoint",
        description="API is running"
    )
    def root():
        """API is running."""
        return {
            "message": "Smart Medi Assistant API",
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.get(
        "/health",
        summary="Health check",
        description="Check API and dependent services",
    )
    def health():
        """Return liveness + dependency status for load-balancer and monitoring."""
        from app.extensions import engine, redis_client

        checks: dict = {}

        # Database
        try:
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = True
        except Exception:
            checks["database"] = False

        # Redis
        try:
            checks["redis"] = bool(redis_client and redis_client.ping())
        except Exception:
            checks["redis"] = False

        # Euri AI API
        try:
            from app.services.euri_service import get_euri_service
            euri_result = get_euri_service().health_check()
            checks["euri"] = euri_result.get("status") == "healthy"
        except Exception:
            checks["euri"] = False

        # FAISS vector index
        try:
            from app.services.faiss_service import get_faiss_service
            checks["faiss"] = get_faiss_service().health_check()
        except Exception:
            checks["faiss"] = False

        all_ok = all(checks.values())
        return {
            "status": "ok" if all_ok else "degraded",
            "version": "0.1.0",
            "services": checks,
        }

    return app


# Create the app instance
app = create_app()
