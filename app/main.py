"""Main FastAPI application entry point."""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.routes import health, conversion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated Web Article to PDF Conversion System for reMarkable Tablets",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(conversion.router, prefix="/api/v1", tags=["conversion"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PaperFlow API - Automated Article to PDF Conversion",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "convert": "/api/v1/convert",
            "status": "/api/v1/status/{job_id}",
            "health": "/api/v1/health",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logging.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logging.info(f"Debug mode: {settings.DEBUG}")

    # Create temp directory if it doesn't exist
    import os

    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    logging.info(f"Temp directory: {settings.TEMP_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logging.info("Shutting down PaperFlow API")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
