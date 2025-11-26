"""
=========================================================================
FastAPI Main Application - SDLC Orchestrator Backend
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + CTO Approved
Foundation: ADR-003 (API Strategy), ADR-004 (Microservices Architecture)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- FastAPI application entry point
- API route configuration (authentication, gates, evidence)
- Middleware setup (CORS, GZIP, logging)
- Health checks and metrics (Prometheus)

API Features:
- RESTful API (OpenAPI 3.1 documentation)
- JWT authentication (Bearer tokens)
- OAuth 2.0 social login (GitHub, Google, Microsoft)
- Rate limiting (100 req/min per user)
- API versioning (/api/v1)

Middleware Stack:
- CORS (Cross-Origin Resource Sharing)
- GZIP compression (responses >1KB)
- Request ID tracking (X-Request-ID header)
- Structured logging (structlog + JSON)

=========================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.middleware.prometheus_metrics import (
    PrometheusMetricsMiddleware,
    metrics_endpoint,
)
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

# Import API routers
from app.api.routes import auth, evidence, gates, policies

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

# Security Headers (Week 5 Day 1 - P1 Feature)
# Must be first to add headers to all responses
app.add_middleware(SecurityHeadersMiddleware)

# Rate Limiting (Week 5 Day 1 - P1 Feature)
# Redis-based: 100 req/min per user, 1000 req/hour per IP
app.add_middleware(RateLimiterMiddleware)

# Prometheus Metrics (Week 5 Day 2 - Performance Monitoring)
# Collect API latency, request rate, error rate
app.add_middleware(PrometheusMetricsMiddleware)

# CORS - Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================================
# API Routes Registration
# ============================================================================

# Register API v1 routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(gates.router, prefix="/api/v1", tags=["Gates"])
app.include_router(evidence.router, prefix="/api/v1", tags=["Evidence"])
app.include_router(policies.router, prefix="/api/v1", tags=["Policies"])

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


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint

    Returns:
        Prometheus metrics in text format (for Prometheus scraping)
    """
    return metrics_endpoint()


# ============================================================================
# Week 3 Day 3: Authentication + Gates APIs Implemented ✅
# Week 4 Day 4-5 TODO: Evidence + Policies + AI APIs
# ============================================================================

# TODO Week 4:
# from app.api.routes import evidence, policies, ai
# app.include_router(evidence.router, prefix="/api/v1", tags=["Evidence"])
# app.include_router(policies.router, prefix="/api/v1", tags=["Policies"])
# app.include_router(ai.router, prefix="/api/v1", tags=["AI"])

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
    print("🚀 SDLC Orchestrator API started successfully!")
    print(f"📊 OpenAPI docs: http://localhost:8000/api/docs")
    print(f"🔐 Authentication endpoints: http://localhost:8000/api/v1/auth")
    print(f"🚪 Gates endpoints: http://localhost:8000/api/v1/gates")
    
    # Initialize Redis connection (Week 5 Day 1 - P1 Features)
    try:
        from app.utils.redis import get_redis_client
        redis = await get_redis_client()
        await redis.ping()
        print("✅ Redis connected (rate limiting enabled)")
    except Exception as e:
        print(f"⚠️  Redis connection failed (rate limiting disabled): {e}")
    
    # TODO: Verify OPA availability
    # TODO: Initialize MinIO buckets


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown
    - Close database connections
    - Close Redis connection
    """
    print("👋 SDLC Orchestrator API shutdown complete")
    
    # Close Redis connection (Week 5 Day 1)
    from app.utils.redis import close_redis_client
    await close_redis_client()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
