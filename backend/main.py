"""Entry point for FastAPI application.

Run with:
    python -m uvicorn main:app --reload

Or with:
    python main.py
"""
import os
import uvicorn
from app import app


if __name__ == "__main__":
    # Get config from environment
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    reload = os.getenv("DEBUG", "False").lower() == "true"

    print(f"Starting Smart Medi Assistant API on {host}:{port}")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
