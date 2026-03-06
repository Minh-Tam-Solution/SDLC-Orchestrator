"""
=========================================================================
FastAPI Main Application - SDLC Orchestrator Backend
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.2.0
Date: December 23, 2025
Status: ACTIVE - Phase 2-Pilot Week 1 (SE 3.0 Track 1)
Authority: Backend Lead + CTO Approved
Foundation: ADR-003 (API Strategy), ADR-004 (Microservices Architecture)
Framework: SDLC 5.1.0 Complete Lifecycle

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
from fastapi import Depends, FastAPI
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
from app.middleware.tier_gate import TierGateMiddleware  # Sprint 184 — Tier enforcement (ADR-059 INV-03)
from app.middleware.usage_limits import UsageLimitsMiddleware  # Sprint 188 — per-resource usage limits (INV-04)
from app.middleware.conversation_first_guard import ConversationFirstGuard  # Sprint 190 — admin-only write paths

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
    # Sprint 190: SOP Generator banner removed (route deleted)

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

    # Start WorkflowResumer if LangGraph is enabled (Sprint 208, ADR-066)
    workflow_resumer = None
    try:
        from app.services.agent_team.config import LANGGRAPH_ENABLED
        if LANGGRAPH_ENABLED:
            from app.services.agent_team.workflow_resumer import WorkflowResumer
            workflow_resumer = WorkflowResumer(
                db_url=str(settings.DATABASE_URL),
                redis_url=settings.REDIS_URL or "redis://localhost:6379/0",
            )
            await workflow_resumer.start()
            print("✅ WorkflowResumer started (LANGGRAPH_ENABLED=true)")
    except Exception as e:
        print(f"⚠️  WorkflowResumer startup skipped: {e}")
        workflow_resumer = None

    # Start HeartbeatMonitor (Sprint 219 — P6 Agent Liveness, ADR-072)
    heartbeat_monitor = None
    try:
        from app.services.agent_team.heartbeat_monitor import HeartbeatMonitor
        from app.utils.redis import get_redis_client
        _hb_redis = await get_redis_client()
        heartbeat_monitor = HeartbeatMonitor(
            db_url=str(settings.DATABASE_URL),
            redis=_hb_redis,
        )
        await heartbeat_monitor.start()
        print("✅ HeartbeatMonitor started (30s scan interval)")
    except Exception as e:
        print(f"⚠️  HeartbeatMonitor startup skipped: {e}")
        heartbeat_monitor = None

    # Yield control to the application
    yield

    # Shutdown
    print("👋 SDLC Orchestrator API shutting down...")

    # Stop WorkflowResumer (Sprint 208)
    if workflow_resumer is not None:
        try:
            workflow_resumer.stop()
            print("✅ WorkflowResumer stopped")
        except Exception as e:
            print(f"⚠️  WorkflowResumer shutdown error: {e}")

    # Stop HeartbeatMonitor (Sprint 219)
    if heartbeat_monitor is not None:
        try:
            heartbeat_monitor.stop()
            print("✅ HeartbeatMonitor stopped")
        except Exception as e:
            print(f"⚠️  HeartbeatMonitor shutdown error: {e}")

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
from app.api.routes import auth, evidence, gates, policies, dashboard, projects, github, compliance, notifications, triage, analytics_v2, sdlc_structure, admin, docs, ai_detection, policy_packs, sast, evidence_timeline, override, codegen, preview, contract_lock, api_keys, payments, ai_providers, teams, organizations, organization_invitations, planning, agents, evidence_manifest, check_runs, planning_subagent, risk_analysis, consultations, mrp, framework_version, context_validation, maturity, auto_generation, governance_mode, vibecoding_index, stage_gating, context_authority_v2, ceo_dashboard, governance_metrics, grafana_dashboards, governance_specs, governance_vibecoding, tier_management, gates_engine, compliance_validation, telemetry, mcp_analytics, deprecation_monitoring, vcr, websocket, push, cross_reference_validation  # Sprint 42-155 (Sprint 190: removed feedback, analytics v1, council, sop, pilot, learnings, context_authority v1, dogfooding, spec_converter)
from app.api.routes import agent_team  # Sprint 176 - Multi-Agent Team Engine (ADR-056/EP-07)
from app.api.routes import ott_gateway  # Sprint 181 - OTT Gateway (Telegram + Zalo, ADR-059)
from app.api.routes import templates  # Sprint 181 - SDLC Templates (CORE public endpoint)
from app.api.routes import compliance_framework  # Sprint 181 - Compliance Framework (ENTERPRISE)
# Sprint 190: NIST imports removed (nist_govern, nist_manage, nist_map, nist_measure) — frozen, unused
from app.api.routes import invitations  # Sprint 181 - Team Invitations (ENTERPRISE, async-fixed)
from app.api.routes import enterprise_sso  # Sprint 183 - Enterprise SSO (SAML 2.0 + Azure AD, ADR-061)
from app.api.routes import jira_integration  # Sprint 184 - Jira Integration (PROFESSIONAL+, ADR-059)
from app.api.routes import admin_ott  # Sprint 198 - OTT Gateway Admin Dashboard (ENTERPRISE)
from app.api.routes import workflows  # Sprint 206 - LangGraph Durable Workflows (ADR-066 Phase 2)
from app.api.v1.endpoints import cross_reference  # Sprint 139 - RFC-SDLC-602 E2E Cross-Reference Validation
from app.api.v1.endpoints import e2e_testing  # Sprint 140 - RFC-SDLC-602 E2E Test Execution API

# Create FastAPI app with lifespan
app = FastAPI(
    title="SDLC Orchestrator API",
    description="AI-Native SDLC Governance Platform with Quality Gates",
    version="1.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ============================================================================
# Exception Handlers (Debug)
# ============================================================================

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Custom handler for Pydantic validation errors (422).
    Logs detailed error information for debugging.

    Sprint 213: Sanitize Pydantic v2 error dicts — ctx.error contains raw
    ValueError/TypeError objects that are not JSON-serializable. Convert to
    string to prevent TypeError crash in JSONResponse serialization.
    """
    logger.error(f"Validation error on {request.method} {request.url}")
    logger.error(f"Errors: {exc.errors()}")
    logger.error(f"Body: {exc.body}")

    # Sanitize errors: Pydantic v2 ctx.error can contain non-serializable objects
    sanitized_errors = []
    for err in exc.errors():
        clean = dict(err)
        if "ctx" in clean and isinstance(clean["ctx"], dict):
            clean["ctx"] = {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in clean["ctx"].items()
            }
        sanitized_errors.append(clean)

    return JSONResponse(
        status_code=422,
        content={
            "detail": sanitized_errors,
            "body": str(exc.body) if exc.body else None,
        }
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
# P2 FIX (Sprint 33 Day 1): Explicit methods instead of wildcard
# Sprint 63: allow_credentials=True required for httpOnly cookie authentication
# IMPORTANT: Cannot use allow_origins=["*"] with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,  # Required for cookie-based auth (Sprint 63)
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit whitelist
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Cache Headers (Sprint 23 Day 4 - Response Optimization)
# Adds Cache-Control, Vary headers for client-side caching
app.add_middleware(CacheHeadersMiddleware)

# Tier Gate (Sprint 184 — ADR-059 INV-03 Tier Invariant Enforcement)
# Pure ASGI — returns 402 Payment Required when subscription tier insufficient.
# IMPORTANT: Added last so it runs first (LIFO stack order in Starlette).
# Reads user_tier from scope["state"]["user_tier"] if available (falls back to JWT + DB).
# X-Admin-Override header bypass controlled by TIER_GATE_ADMIN_SECRET env var.
app.add_middleware(TierGateMiddleware)  # Sprint 184 — pure ASGI, NOT BaseHTTPMiddleware

# Usage Limits (Sprint 188 — INV-04 Per-Resource Usage Enforcement)
# Pure ASGI — returns 402 with upgrade CTA when per-resource quota exceeded.
# Intercepts 4 mutation endpoints: POST /projects, /evidence/upload, /gates, /teams/members/invite
# IMPORTANT: Added AFTER TierGateMiddleware so it runs BEFORE it (LIFO order).
# This ensures usage check fires before the tier-route gate check.
app.add_middleware(UsageLimitsMiddleware)  # Sprint 188 — pure ASGI, NOT BaseHTTPMiddleware

# Conversation-First Guard (Sprint 190 — CEO directive)
# Pure ASGI — returns 403 for non-admin write ops on admin-gated paths.
# IMPORTANT: Added AFTER UsageLimitsMiddleware so it runs BEFORE (LIFO).
app.add_middleware(ConversationFirstGuard)  # Sprint 190 — admin-only write paths

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
from app.api.routes import compliance_export  # noqa: E402  # Sprint 192
app.include_router(compliance_export.router, prefix="/api/v1", tags=["Compliance Export"])  # Sprint 192 — Compliance PDF Export
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
# Sprint 190: feedback.router removed — frozen, unused (Day 2)
app.include_router(triage.router, prefix="/api/v1", tags=["Triage"])
# Sprint 190: analytics.router (v1) removed — superseded by analytics_v2 (Day 3)
app.include_router(analytics_v2.router, prefix="/api/v1", tags=["Analytics v2"])  # Sprint 41 (Mixpanel + PostgreSQL)
# Sprint 190: council.router removed — frozen, unused (Day 2)
app.include_router(sdlc_structure.router, prefix="/api/v1", tags=["SDLC Structure"])  # Sprint 30 Day 3
# Sprint 190: sop.router removed — frozen, unused (Day 3)
app.include_router(admin.router, prefix="/api/v1", tags=["Admin Panel"])  # Sprint 37 - ADR-017
app.include_router(docs.router, prefix="/api/v1", tags=["Documentation"])  # User Support Documentation
app.include_router(ai_detection.router, prefix="/api/v1", tags=["AI Detection"])  # Sprint 42 - AI Detection Service
app.include_router(policy_packs.router, prefix="/api/v1", tags=["Policy Packs"])  # Sprint 43 - Policy Guards
app.include_router(sast.router, prefix="/api/v1", tags=["SAST"])  # Sprint 43 - SAST Validator
app.include_router(evidence_timeline.router, prefix="/api/v1", tags=["Evidence Timeline"])  # Sprint 43 - Evidence UI
app.include_router(override.router, prefix="/api/v1", tags=["Override / VCR"])  # Sprint 43 - VCR Override Flow
app.include_router(codegen.router, prefix="/api/v1", tags=["Codegen"])  # Sprint 45 - EP-06 Codegen Engine
# Sprint 190: pilot.router removed — frozen, unused (Day 3)
app.include_router(preview.router, prefix="/api/v1", tags=["Preview"])  # Sprint 51B - QR Mobile Preview
app.include_router(contract_lock.router, prefix="/api/v1", tags=["Contract Lock"])  # Sprint 53 - Spec Immutability
app.include_router(api_keys.router, prefix="/api/v1", tags=["API Keys"])  # Sprint 52B - VS Code Extension Auth
app.include_router(payments.router, prefix="/api/v1", tags=["Payments"])  # Sprint 58 - VNPay + Subscriptions
app.include_router(ai_providers.router, prefix="/api/v1", tags=["AI Providers"])  # Sprint 70 - AI Provider Admin UI
app.include_router(teams.router, prefix="/api/v1", tags=["Teams"])  # Sprint 71 - Teams Foundation
app.include_router(organizations.router, prefix="/api/v1", tags=["Organizations"])  # Sprint 71 - Organizations
app.include_router(organization_invitations.router, prefix="/api/v1", tags=["Organization Invitations"])  # Sprint 146 - Organization Invitations (ADR-047)
app.include_router(planning.router, prefix="/api/v1", tags=["Planning Hierarchy"])  # Sprint 74 - Planning Hierarchy (ADR-013)
app.include_router(agents.router, prefix="/api/v1", tags=["AGENTS.md"])  # Sprint 80 - AGENTS.md Integration (ADR-029)
app.include_router(evidence_manifest.router, prefix="/api/v1", tags=["Evidence Manifest"])  # Sprint 82 - Tamper-Evident Hash Chain
app.include_router(check_runs.router, prefix="/api/v1", tags=["Check Runs"])  # Sprint 86 - GitHub Check Run UI (P0 Blocker)
app.include_router(planning_subagent.router, prefix="/api/v1", tags=["Planning Sub-agent"])  # Sprint 99 - Planning Sub-agent Orchestration (ADR-034)
# Sprint 190: learnings.router removed — frozen, unused (Day 2)
app.include_router(risk_analysis.router, prefix="/api/v1", tags=["Risk Analysis"])  # Sprint 101 - Risk-Based Planning Trigger (GAP-001)
app.include_router(consultations.router, prefix="/api/v1", tags=["CRP - Consultations"])  # Sprint 101 - Consultation Request Protocol (GAP-002)
app.include_router(mrp.router, prefix="/api/v1", tags=["MRP - Merge Readiness Protocol"])  # Sprint 102 - MRP/VCR 5-Point + 4-Tier Enforcement
app.include_router(framework_version.router, prefix="/api/v1", tags=["Framework Version"])  # Sprint 103 - Framework Version Tracking
app.include_router(context_validation.router, prefix="/api/v1", tags=["Context Validation"])  # Sprint 103 - AGENTS.md Context <60 Lines
app.include_router(maturity.router, prefix="/api/v1", tags=["Agentic Maturity"])  # Sprint 104 - Agentic Maturity L0-L3
app.include_router(auto_generation.router, prefix="/api/v1", tags=["Auto-Generation"])  # Sprint 108 - Governance Auto-Generation Layer
app.include_router(governance_mode.router, prefix="/api/v1", tags=["Governance Mode"])  # Sprint 108 - Governance Mode Management & Kill Switch
app.include_router(vibecoding_index.router, prefix="/api/v1", tags=["Vibecoding Index"])  # Sprint 109 - Vibecoding Index Signals Engine
app.include_router(stage_gating.router, prefix="/api/v1", tags=["Stage Gating"])  # Sprint 109 - Stage-Aware PR Gating (11 SDLC Stages)
# Sprint 190: context_authority.router (v1) removed — superseded by context_authority_v2 (Day 3)
app.include_router(ceo_dashboard.router, prefix="/api/v1", tags=["CEO Dashboard"])  # Sprint 110 - CEO Dashboard & Observability (Executive Governance Intelligence)
app.include_router(governance_metrics.router, prefix="/api/v1", tags=["Governance Metrics"])  # Sprint 110 - Prometheus Metrics Collector (45 Governance Observability Metrics)
app.include_router(grafana_dashboards.router, prefix="/api/v1", tags=["Grafana Dashboards"])  # Sprint 110 - Grafana Dashboard Configurations (CEO, Tech, Ops Dashboards)
# Sprint 190: dogfooding.router removed — frozen, unused (Day 3)
app.include_router(governance_specs.router, prefix="/api/v1", tags=["Governance Specs"])  # Sprint 118 - SPEC-0002 Specification Management
app.include_router(governance_vibecoding.router, prefix="/api/v1", tags=["Governance Vibecoding"])  # Sprint 118 - SPEC-0001 Vibecoding Index Engine
app.include_router(tier_management.router, prefix="/api/v1", tags=["Tier Management"])  # Sprint 118 - 4-Tier Classification System
app.include_router(context_authority_v2.router, prefix="/api/v1", tags=["Context Authority V2"])  # Sprint 120 - Context Authority V2 Gate-Aware Dynamic Context (SPEC-0011)
app.include_router(gates_engine.router, prefix="/api/v1", tags=["Gates Engine"])  # Sprint 120 - Gates Engine OPA Integration + Gate Evaluation (Track B)
app.include_router(compliance_validation.router, prefix="/api/v1", tags=["Compliance Validation"])  # Sprint 123 - SDLC 6.0.5 Compliance Validation (SPEC-0013)
app.include_router(cross_reference.router, prefix="/api/v1", tags=["Cross-Reference"])  # Sprint 139 - RFC-SDLC-602 E2E Cross-Reference Validation (Stage 03 ↔ Stage 05)
app.include_router(e2e_testing.router, prefix="/api/v1", tags=["E2E Testing"])  # Sprint 140 - RFC-SDLC-602 E2E Test Execution API (Phase 2 & 3)
app.include_router(telemetry.router, prefix="/api/v1", tags=["Telemetry"])  # Sprint 147 - Product Truth Layer (Replace "82-85% realization" with measured metrics)
app.include_router(mcp_analytics.router, prefix="/api/v1", tags=["MCP Analytics"])  # Sprint 150 - MCP Analytics Dashboard (Provider health, cost tracking, latency)
app.include_router(deprecation_monitoring.router, prefix="/api/v1", tags=["Deprecation Monitoring"])  # Sprint 150 - V1 Deprecation Monitoring (sunset tracking, migration progress)
app.include_router(vcr.router, prefix="/api/v1", tags=["VCR (Version Controlled Resolution)"])  # Sprint 151 - SASE Artifacts VCR Workflow (ADR-048, SPEC-0024)
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])  # Sprint 153 - Real-time Notifications (WebSocket)
app.include_router(push.router, prefix="/api/v1", tags=["Push Notifications"])  # Sprint 153 - Browser Push Notifications
# Sprint 190: spec_converter.router removed — frozen, unused (Day 3)
app.include_router(cross_reference_validation.router, prefix="/api/v1", tags=["Cross-Reference Validation"])  # Sprint 155 - Document Cross-Reference Validation (ADR-050)
app.include_router(agent_team.router, prefix="/api/v1", tags=["Multi-Agent Team Engine"])  # Sprint 176 - Multi-Agent Team Engine (ADR-056/EP-07)

# Sprint 181 — OTT Gateway + Orphaned Route Activation (ADR-059)
# OTT Gateway: POST /channels/{channel}/webhook (Telegram + Zalo normalizers)
app.include_router(ott_gateway.router, prefix="/api/v1", tags=["OTT Gateway"])  # Sprint 181 - OTT Gateway (Telegram + Zalo)
# Sprint 199 — Magic Link OOB Auth callback (gate approvals via chat)
from app.api.routes import magic_link  # noqa: E402
app.include_router(magic_link.router, prefix="/api/v1", tags=["Magic Link"])  # Sprint 199 - Magic Link Verification (ADR-064 FR-047)
# Sprint 198 — OTT Gateway Admin Dashboard (ENTERPRISE, admin-only)
# Routes: /api/v1/admin/ott-channels/{stats,config,{channel}/health,{channel}/conversations}
# Tier gate: /api/v1/admin → ENTERPRISE (tier=4) already in ROUTE_TIER_TABLE
app.include_router(admin_ott.router, prefix="/api/v1", tags=["OTT Gateway Admin"])  # Sprint 198 - OTT Gateway Dashboard
app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])  # Sprint 206 - LangGraph Durable Workflows (ADR-066 Phase 2)
# Templates: CORE public endpoint (no auth, rate-limited by RateLimiterMiddleware)
app.include_router(templates.router, prefix="/api/v1", tags=["Templates"])  # Sprint 181 - SDLC Templates (public CORE)
# ENTERPRISE routes — HTTP 402 raised by require_enterprise_tier if tier < enterprise
from app.api.dependencies import require_enterprise_tier  # noqa: E402
app.include_router(compliance_framework.router, prefix="/api/v1", tags=["Compliance Framework"], dependencies=[Depends(require_enterprise_tier)])  # Sprint 181 - Compliance Framework (ENTERPRISE)
# Sprint 190: NIST router registrations removed (nist_govern, nist_manage, nist_map, nist_measure) — frozen, unused
app.include_router(invitations.router, prefix="/api/v1", tags=["Invitations"], dependencies=[Depends(require_enterprise_tier)])  # Sprint 181 - Team Invitations (ENTERPRISE, async-fixed)

# Sprint 183 — Enterprise SSO (SAML 2.0 + Azure AD, ADR-061)
# Routes: /api/v1/enterprise/sso/{configure,saml/*,azure-ad/*,logout}
# Tier gate applied per-endpoint (configure = ENTERPRISE; metadata = public; callbacks = no auth)
app.include_router(enterprise_sso.router, prefix="/api/v1", tags=["Enterprise SSO"])  # Sprint 183 - Enterprise SSO SAML 2.0 + Azure AD (ENTERPRISE, ADR-061)

# Sprint 184 — Jira Integration (PROFESSIONAL+, ADR-059)
# Routes: POST /jira/connect, GET /jira/projects, POST /jira/sync
# Tier gate: /api/v1/jira → PROFESSIONAL (tier=3) enforced by TierGateMiddleware
app.include_router(jira_integration.router, prefix="/api/v1", tags=["Jira Integration"])  # Sprint 184 - Jira Integration (PROFESSIONAL+)

# Sprint 185 — Audit Trail + SOC2 Evidence Pack (ENTERPRISE, ADR-059)
# Routes: GET /enterprise/audit, POST /enterprise/audit/export, POST /enterprise/soc2-pack
# Tier gate: /api/v1/enterprise → ENTERPRISE (tier=4) enforced by TierGateMiddleware
from app.api.routes import audit_trail  # noqa: E402
app.include_router(audit_trail.router, prefix="/api/v1", tags=["Audit Trail"])  # Sprint 185 - Immutable Audit Trail + SOC2 Pack (ENTERPRISE)

# Sprint 186 — Multi-Region Data Residency (ENTERPRISE, ADR-063)
# Routes: GET /data-residency/regions, GET|PUT /data-residency/projects/{id}/region
# Storage-level residency only (MinIO bucket per region; DB single-region VN)
from app.api.routes import data_residency  # noqa: E402
app.include_router(data_residency.router, prefix="/api/v1", tags=["Data Residency"], dependencies=[Depends(require_enterprise_tier)])  # Sprint 186 - Data Residency (ENTERPRISE)

# Sprint 186 — GDPR Data Subject Rights + Consent Management (ADR-063)
# Self-service endpoints: /gdpr/dsar (submit), /gdpr/me/data-export, /gdpr/me/consent
# DPO endpoints: /gdpr/dsar (list) — ENTERPRISE tier enforced below via dependency
from app.api.routes import gdpr  # noqa: E402
app.include_router(gdpr.router, prefix="/api/v1", tags=["GDPR"])  # Sprint 186 - GDPR (self-service: authenticated; DPO list: ENTERPRISE via service layer)

# Sprint 191: deprecated_routes.py removed (410 stub grace period expired)

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
        "version": "1.2.0",
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
        "version": "1.2.0",
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
