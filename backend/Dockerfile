# File: backend/Dockerfile
# Version: 2.1.0
# Status: ACTIVE - Sprint 194 (Security + Agent Enrichment)
# Date: 2026-02-24
# Authority: DevOps Lead + CTO Approved
# Foundation: SDLC 6.1.0, Multi-Stage Build, Zero Mock Policy
#
# Description:
# Multi-stage Dockerfile for SDLC Orchestrator FastAPI backend.
# Stage 1 (builder): Installs build tools + compiles C extensions.
# Stage 2 (runtime): Copies only compiled packages. Target: <600MB.

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Build tools needed for C extensions (psycopg2, bcrypt, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements/core.txt requirements/core.txt

# Install Python deps into /install prefix (isolated from system Python)
RUN pip install --no-cache-dir --prefix=/install -r requirements/core.txt

# NOTE: Semgrep removed from runtime image (Sprint 194 F-192-07).
# SAST scans run in CI pipeline only (GitHub Actions).
# Keeps runtime image <600MB.

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime-only system deps (no build-essential, no pkg-config)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user for security (CWE-250)
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8300

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8300/health || exit 1

# Run the application (overridden by docker-compose.yml command)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8300"]
