# PORT ALLOCATION MANAGEMENT
## SDLC Orchestrator - Service Port Configuration

**Version**: 1.0.0
**Date**: November 29, 2025
**Status**: ACTIVE - Staging Environment
**Authority**: DevOps Lead + Backend Lead
**Framework**: SDLC 4.9 Complete Lifecycle

---

## Overview

This document defines all port allocations for SDLC Orchestrator services across different environments (development, staging, production). All ports are now **configurable via environment variables** following the Twelve-Factor App methodology.

---

## Port Allocation Table

### Core Services

| Service | Default Port | Environment Variable | Container Port | Description |
|---------|-------------|---------------------|----------------|-------------|
| **Backend API** | 8000 | `API_PORT`, `BACKEND_PORT` | 8000 | FastAPI REST API |
| **Frontend Web** | 3000 (dev) / 4000 (prod) | `VITE_DEV_PORT`, `FRONTEND_PORT` | 4000 | React SPA (Nginx in production) |
| **PostgreSQL** | 5432 | `DATABASE_URL` | 5432 | Primary database |
| **Redis** | 6379 | `REDIS_URL` | 6379 | Session cache, token blacklist |
| **MinIO** | 9000 (API) / 9001 (Console) | `MINIO_ENDPOINT` | 9000/9001 | S3-compatible evidence storage |
| **OPA** | 8181 | `OPA_URL` | 8181 | Policy evaluation engine |

### Staging Environment Ports

| Service | Host Port | Container Port | Environment Variable |
|---------|-----------|----------------|---------------------|
| Backend | 8000 | 8000 | `API_PORT=8000` |
| Frontend | 4000 | 4000 | `FRONTEND_PORT=4000` |
| PostgreSQL | 5433 | 5432 | `DATABASE_URL=...@localhost:5433/...` |
| Redis | 6380 | 6379 | `REDIS_URL=redis://localhost:6380/0` |
| MinIO API | 9002 | 9000 | `MINIO_ENDPOINT=localhost:9002` |
| MinIO Console | 9003 | 9001 | N/A |
| OPA | 8182 | 8181 | `OPA_URL=http://localhost:8182` |

### Production Environment Ports

| Service | Port | Notes |
|---------|------|-------|
| Backend | 8000 | Behind load balancer (443 → 8000) |
| Frontend | 443 | Nginx serves static files, proxies /api |
| PostgreSQL | 5432 | Managed database (RDS/Cloud SQL) |
| Redis | 6379 | Managed Redis (ElastiCache/Memorystore) |
| MinIO | 9000 | Or AWS S3 in production |
| OPA | 8181 | Sidecar container |

---

## Environment Variable Configuration

### Backend (Python/FastAPI)

**File**: `backend/app/core/config.py`

```python
# Database - configurable via DATABASE_URL
DATABASE_URL: str = "postgresql+asyncpg://user:pass@postgres:5432/db"

# Redis - configurable via REDIS_URL
REDIS_URL: str = "redis://redis:6379/0"

# MinIO - configurable via MINIO_ENDPOINT
MINIO_ENDPOINT: str = "minio:9000"

# OPA - configurable via OPA_URL
OPA_URL: str = "http://opa:8181"

# CORS origins - configurable via ALLOWED_ORIGINS
ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:4000,..."
```

### Frontend (TypeScript/Vite)

**File**: `frontend/web/vite.config.ts`

```typescript
server: {
  // Dev server port - configurable via VITE_DEV_PORT (default: 3000)
  port: parseInt(process.env.VITE_DEV_PORT || '3000'),
  proxy: {
    '/api': {
      // Backend URL - configurable via VITE_API_URL (default: http://localhost:8000)
      target: process.env.VITE_API_URL || 'http://localhost:8000',
    },
  },
},
```

### E2E Tests (Playwright)

**File**: `frontend/web/playwright.config.ts`

```typescript
// Base URL - configurable via BASE_URL, FRONTEND_PORT, VITE_DEV_PORT
baseURL: process.env.BASE_URL ||
  (process.env.SKIP_WEB_SERVER
    ? `http://localhost:${process.env.FRONTEND_PORT || '4000'}`
    : `http://localhost:${process.env.VITE_DEV_PORT || '5173'}`)
```

### Integration Tests (Pytest)

**File**: `tests/conftest.py`

```python
# Test database - configurable via TEST_DATABASE_URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://user:pass@postgres:5432/test_db"
)
```

---

## Docker Compose Port Mappings

### Development (docker-compose.yml)

```yaml
services:
  backend:
    ports:
      - "8000:8000"

  frontend:
    ports:
      - "3000:3000"  # Dev server

  postgres:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"

  minio:
    ports:
      - "9000:9000"
      - "9001:9001"

  opa:
    ports:
      - "8181:8181"
```

### Staging (docker-compose.staging.yml)

```yaml
services:
  backend:
    ports:
      - "8000:8000"

  frontend:
    ports:
      - "4000:4000"  # Production build (Nginx)

  postgres:
    ports:
      - "5433:5432"  # Offset to avoid dev conflict

  redis:
    ports:
      - "6380:6379"

  minio:
    ports:
      - "9002:9000"
      - "9003:9001"

  opa:
    ports:
      - "8182:8181"
```

---

## Port Conflict Resolution

### Common Conflicts

| Conflict | Resolution |
|----------|------------|
| PostgreSQL (5432) already in use | Use staging port 5433 or stop local PostgreSQL |
| Redis (6379) already in use | Use staging port 6380 or stop local Redis |
| Port 3000 in use (other React apps) | Set `VITE_DEV_PORT=3001` |
| Port 8000 in use (other Python apps) | Set `API_PORT=8001` |

### Quick Fix Commands

```bash
# Check what's using a port
lsof -i :8000

# Kill process using port
kill -9 $(lsof -t -i :8000)

# Use staging environment (offset ports)
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

---

## Service Discovery

### Docker Network (Internal)

Services communicate using Docker service names (not localhost):

| Service | Internal URL |
|---------|-------------|
| Backend | `http://backend:8000` |
| PostgreSQL | `postgres:5432` |
| Redis | `redis:6379` |
| MinIO | `minio:9000` |
| OPA | `http://opa:8181` |

### External Access (Host Machine)

| Service | External URL |
|---------|-------------|
| Backend API | `http://localhost:8000` |
| Frontend | `http://localhost:4000` |
| MinIO Console | `http://localhost:9003` |
| API Docs | `http://localhost:8000/api/docs` |

---

## Health Check Endpoints

| Service | Health Check URL | Expected Response |
|---------|-----------------|-------------------|
| Backend | `GET /health` | `{"status": "healthy"}` |
| PostgreSQL | TCP 5432 | Connection accepted |
| Redis | `PING` | `PONG` |
| MinIO | `GET /minio/health/live` | `200 OK` |
| OPA | `GET /health` | `200 OK` |

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-29 | 1.0.0 | Initial port allocation document |
| 2025-11-29 | 1.0.0 | Hardcoded ports migrated to env vars |
| 2025-11-29 | 1.0.0 | Staging environment port offsets defined |

---

**Last Updated**: November 29, 2025
**Owner**: DevOps Lead
**Status**: ACTIVE
