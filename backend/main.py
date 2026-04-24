"""Entry point for FastAPI application.

Run with:
    python -m uvicorn main:app --reload

Or with:
    python main.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file (explicit path)
env_file = Path(__file__).parent / ".env"
print(f"Loading .env from: {env_file}")
load_dotenv(dotenv_path=env_file)

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
