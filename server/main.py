"""
Main FastAPI app for ML model training and prediction.
"""
import logging
import sys

from fastapi import FastAPI

# -----------------------------
# Logging setup (early for error handling)
# -----------------------------
from server.core_models.server_logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Handle configuration errors gracefully
try:
    from server.users.routes import router as user_router
    from server.models.routes import router as models_router
    from server.init_db import init_db
except RuntimeError as e:
    if "JWT_SECRET" in str(e):
        logger.error("\n" + "="*70)
        logger.error("ERROR: Missing JWT_SECRET environment variable")
        logger.error("="*70)
        logger.error("\nThe server requires JWT_SECRET to be set in your .env file.")
        logger.error("\nTo fix this:")
        logger.error("1. Create a .env file in the project root if it doesn't exist")
        logger.error("2. Add the following line to your .env file:")
        logger.error("   JWT_SECRET=your-secret-key-here")
        logger.error("\nExample .env file:")
        logger.error("   DB_HOST=localhost")
        logger.error("   DB_PORT=5432")
        logger.error("   DB_NAME=your_database_name")
        logger.error("   DB_USER=your_database_user")
        logger.error("   DB_PASSWORD=your_database_password")
        logger.error("   JWT_SECRET=your-secret-key-here")
        logger.error("="*70 + "\n")
        sys.exit(1)
    raise

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Trainer API", version="1.0.0")

# Include routers
app.include_router(user_router)
app.include_router(models_router)


# -----------------------------
# Startup event: Initialize database
# -----------------------------
@app.on_event("startup")
async def startup_event():
    """
    Initialize database tables on server startup.
    """
    try:
        init_db()
        logger.info("Server startup: Database tables verified/created")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")
        logger.error("Server will continue, but database operations may fail")
        # Don't raise - allow server to start even if DB init fails
        # This allows the server to start and show better error messages
