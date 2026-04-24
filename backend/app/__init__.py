"""FastAPI app factory."""
from pathlib import Path
from dotenv import load_dotenv

# Load .env FIRST, before anything else
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.extensions import init_db
from app.api.v1 import api_router

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
    )

    # ========================================
    # MIDDLEWARE
    # ========================================

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
        logger.info("🚀 Starting Smart Medi Assistant API")
        try:
            init_db()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

    @app.on_event("shutdown")
    def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("🛑 Shutting down Smart Medi Assistant API")

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
