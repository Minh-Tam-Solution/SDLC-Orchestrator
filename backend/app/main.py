"""
=========================================================================
FastAPI Main Application - SDLC Orchestrator Backend
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.1.0
Date: December 2, 2025
Status: ACTIVE - Sprint 21 Day 2 (P0 Fixes)
Authority: Backend Lead + CTO Approved
Foundation: ADR-003 (API Strategy), ADR-004 (Microservices Architecture)
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- FastAPI application entry point
- API route configuration (authentication, gates, evidence)
- Middleware setup (CORS, GZIP, logging)
- Health checks and metrics (Prometheus)
- APScheduler background jobs (compliance scans)

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

Background Jobs (Sprint 21):
- APScheduler for scheduled tasks
- Daily compliance scans (2:00 AM)
- Scan queue processor (every 5 minutes)

=========================================================================
"""

import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.jobs.compliance_scan import register_scheduled_jobs
from app.middleware.prometheus_metrics import (
    PrometheusMetricsMiddleware,
    metrics_endpoint,
)
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.cache_headers import CacheHeadersMiddleware

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


# ============================================================================
# Lifespan Context Manager
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.

    Startup:
    - Initialize database connection pool
    - Connect to Redis
    - Verify OPA availability
    - Initialize MinIO buckets
    - Start APScheduler for background jobs

    Shutdown:
    - Stop APScheduler
    - Close database connections
    - Close Redis connection
    """
    global scheduler
    api_host = os.getenv("API_HOST", "localhost")
    api_port = os.getenv("API_PORT", "8000")
    print("🚀 SDLC Orchestrator API starting...")
    print(f"📊 OpenAPI docs: http://{api_host}:{api_port}/api/docs")
    print(f"🔐 Authentication endpoints: http://{api_host}:{api_port}/api/v1/auth")
    print(f"🚪 Gates endpoints: http://{api_host}:{api_port}/api/v1/gates")

    startup_errors = []

    # Initialize Redis connection (Week 5 Day 1 - P1 Features)
    try:
        from app.utils.redis import get_redis_client
        redis = await get_redis_client()
        await redis.ping()
        print("✅ Redis connected (rate limiting enabled)")
    except Exception as e:
        print(f"⚠️  Redis connection failed (rate limiting disabled): {e}")
        # Redis is optional - don't add to startup_errors

    # Verify OPA availability (Sprint 14 - TD-02)
    try:
        from app.services.opa_service import opa_service
        health = opa_service.health_check()
        if health.get("healthy"):
            print(f"✅ OPA connected (version: {health.get('version', 'unknown')})")
        else:
            error_msg = f"OPA unhealthy: {health.get('error', 'unknown error')}"
            print(f"❌ {error_msg}")
            startup_errors.append(error_msg)
    except Exception as e:
        error_msg = f"OPA connection failed: {e}"
        print(f"❌ {error_msg}")
        startup_errors.append(error_msg)

    # Initialize MinIO buckets (Sprint 14 - TD-02)
    try:
        from app.services.minio_service import minio_service
        minio_service.ensure_bucket_exists()
        print(f"✅ MinIO connected (bucket: {minio_service.bucket_name})")
    except Exception as e:
        error_msg = f"MinIO initialization failed: {e}"
        print(f"❌ {error_msg}")
        startup_errors.append(error_msg)

    # Initialize APScheduler for background jobs (Sprint 21)
    try:
        scheduler = AsyncIOScheduler()
        register_scheduled_jobs(scheduler)
        scheduler.start()
        print("✅ APScheduler started (compliance scans scheduled)")
        print("   - Daily compliance scan: 2:00 AM")
        print("   - Queue processor: every 5 minutes")
    except Exception as e:
        error_msg = f"APScheduler initialization failed: {e}"
        print(f"❌ {error_msg}")
        startup_errors.append(error_msg)

    # Fail fast if critical dependencies unavailable
    if startup_errors:
        print("\n" + "=" * 60)
        print("❌ STARTUP FAILED - Critical dependencies unavailable:")
        for error in startup_errors:
            print(f"   - {error}")
        print("=" * 60 + "\n")
        # In production, we might want to exit here
        # For development, we continue with warnings
        if not settings.DEBUG:
            import sys
            sys.exit(1)
    else:
        print("\n✅ SDLC Orchestrator API started successfully!")

    # Yield control to the application
    yield

    # Shutdown
    print("👋 SDLC Orchestrator API shutting down...")

    # Stop APScheduler (Sprint 21)
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        print("✅ APScheduler stopped")

    # Close Redis connection (Week 5 Day 1)
    from app.utils.redis import close_redis_client
    await close_redis_client()

    print("✅ SDLC Orchestrator API shutdown complete")


# ============================================================================
# Create FastAPI App
# ============================================================================

# Import API routers (after lifespan is defined)
from app.api.routes import auth, evidence, gates, policies, dashboard, projects, github, compliance, notifications, feedback, triage, analytics, council, sdlc_structure

# Create FastAPI app with lifespan
app = FastAPI(
    title="SDLC Orchestrator API",
    description="AI-Native SDLC Governance Platform with Quality Gates",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
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

# Cache Headers (Sprint 23 Day 4 - Response Optimization)
# Adds Cache-Control, Vary headers for client-side caching
app.add_middleware(CacheHeadersMiddleware)

# ============================================================================
# API Routes Registration
# ============================================================================

# Register API v1 routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(gates.router, prefix="/api/v1", tags=["Gates"])
app.include_router(evidence.router, prefix="/api/v1", tags=["Evidence"])
app.include_router(policies.router, prefix="/api/v1", tags=["Policies"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(github.router, prefix="/api/v1", tags=["GitHub"])
app.include_router(compliance.router, prefix="/api/v1", tags=["Compliance"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(triage.router, prefix="/api/v1", tags=["Triage"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(council.router, prefix="/api/v1", tags=["AI Council"])  # Sprint 26 Day 3
app.include_router(sdlc_structure.router, prefix="/api/v1", tags=["SDLC Structure"])  # Sprint 30 Day 3

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
        "version": "1.1.0",
        "service": "sdlc-orchestrator-backend",
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.

    Checks:
    - PostgreSQL: SELECT 1 query
    - Redis: PING command
    - OPA: /health endpoint
    - MinIO: HEAD bucket
    - APScheduler: Running status

    Returns:
        200 OK if all dependencies are healthy
        503 Service Unavailable if any dependency is down
    """
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal
    from app.utils.redis import get_redis_client
    from app.services.opa_service import opa_service
    from app.services.minio_service import minio_service

    dependencies = {}
    all_healthy = True

    # Check PostgreSQL
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        dependencies["postgres"] = {"status": "connected", "healthy": True}
    except Exception as e:
        dependencies["postgres"] = {"status": "disconnected", "healthy": False, "error": str(e)}
        all_healthy = False

    # Check Redis
    try:
        redis = await get_redis_client()
        await redis.ping()
        dependencies["redis"] = {"status": "connected", "healthy": True}
    except Exception as e:
        dependencies["redis"] = {"status": "disconnected", "healthy": False, "error": str(e)}
        all_healthy = False

    # Check OPA
    try:
        health = opa_service.health_check()
        if health.get("healthy"):
            dependencies["opa"] = {"status": "connected", "healthy": True, "version": health.get("version")}
        else:
            dependencies["opa"] = {"status": "unhealthy", "healthy": False, "error": health.get("error")}
            all_healthy = False
    except Exception as e:
        dependencies["opa"] = {"status": "disconnected", "healthy": False, "error": str(e)}
        all_healthy = False

    # Check MinIO
    try:
        minio_service.client.head_bucket(Bucket=minio_service.bucket_name)
        dependencies["minio"] = {"status": "connected", "healthy": True, "bucket": minio_service.bucket_name}
    except Exception as e:
        error_msg = str(e)
        # Bucket not existing is OK - it will be created on startup
        if "404" in error_msg or "NoSuchBucket" in error_msg:
            dependencies["minio"] = {"status": "connected", "healthy": True, "bucket": f"{minio_service.bucket_name} (will be created)"}
        else:
            dependencies["minio"] = {"status": "disconnected", "healthy": False, "error": error_msg}
            all_healthy = False

    # Check APScheduler (Sprint 21)
    if scheduler and scheduler.running:
        jobs = scheduler.get_jobs()
        dependencies["scheduler"] = {
            "status": "running",
            "healthy": True,
            "jobs_count": len(jobs),
        }
    else:
        dependencies["scheduler"] = {"status": "stopped", "healthy": False}
        all_healthy = False

    from fastapi.responses import JSONResponse

    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "dependencies": dependencies,
    }

    if all_healthy:
        return response_data
    else:
        return JSONResponse(status_code=503, content=response_data)


@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "service": "SDLC Orchestrator API",
        "version": "1.1.0",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
