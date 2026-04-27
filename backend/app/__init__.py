"""FastAPI app factory."""
from pathlib import Path
from dotenv import load_dotenv

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

from app.extensions import init_db
from app.api.v1 import api_router
from app.middleware.rate_limit import limiter

# Fix Windows encoding issue: configure logging with UTF-8
handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))

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

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # CORS - Allow frontend to call backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Local frontend
            "http://localhost:8000",  # Swagger docs
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========================================
    # STARTUP & SHUTDOWN
    # ========================================

    @app.on_event("startup")
    def startup_event():
        """Initialize database and services on startup."""
        logger.info("Starting Smart Medi Assistant API")
        try:
            init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

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
        description="Check API and services"
    )
    def health():
        """Overall system health."""
        return {
            "status": "ok",
            "version": "0.1.0",
        }

    return app


# Create the app instance
app = create_app()
