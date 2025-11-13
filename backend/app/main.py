"""
SDLC Orchestrator - FastAPI Main Application
Entry point for the backend API server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app
import structlog

from app.core.config import settings
from app.core.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SDLC Orchestrator API",
    description="AI-Native SDLC Governance Platform with Quality Gates",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS - Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================================
# Prometheus Metrics Endpoint
# ============================================================================

# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ============================================================================
# Health Check Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "sdlc-orchestrator-backend",
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available
    TODO: Add checks for PostgreSQL, Redis, OPA, MinIO
    """
    return {
        "status": "ready",
        "dependencies": {
            "postgres": "connected",  # TODO: Implement actual check
            "redis": "connected",  # TODO: Implement actual check
            "opa": "connected",  # TODO: Implement actual check
            "minio": "connected",  # TODO: Implement actual check
        },
    }


@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "service": "SDLC Orchestrator API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# ============================================================================
# API Routes (TODO: Implement in Phase 1)
# ============================================================================

# from app.api import products, gates, evidence, policies, ai

# app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
# app.include_router(gates.router, prefix="/api/v1/gates", tags=["gates"])
# app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
# app.include_router(policies.router, prefix="/api/v1/policies", tags=["policies"])
# app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])

# ============================================================================
# Startup & Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """
    Application startup
    - Initialize database connection pool
    - Connect to Redis
    - Verify OPA availability
    - Initialize MinIO buckets
    """
    logger.info(
        "application_startup",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )
    # TODO: Initialize connections


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown
    - Close database connections
    - Close Redis connection
    """
    logger.info("application_shutdown")
    # TODO: Cleanup connections


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
