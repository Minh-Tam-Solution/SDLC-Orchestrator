# Docker Deployment Guide
## SDLC Orchestrator - Container-Based Deployment

**Version**: 1.0.0
**Date**: November 18, 2025
**Status**: ACTIVE - Week 4 Day 1 (Architecture Documentation)
**Authority**: Backend Lead + DevOps Lead + CTO Approved
**Foundation**: Week 3 Infrastructure (docker-compose.yml, .env.example)
**Framework**: SDLC 6.1.0

---

## Document Purpose

This guide provides **step-by-step instructions for deploying SDLC Orchestrator using Docker**.

**Key Sections**:
- **Prerequisites** - System requirements, Docker installation
- **Local Development Setup** - Docker Compose for local development
- **Production Deployment** - Multi-stage builds, optimization
- **Environment Configuration** - .env management, secrets
- **Volume Management** - Data persistence, backups
- **Health Checks** - Service health monitoring
- **Troubleshooting** - Common issues, debugging

**Audience**:
- Backend developers (local development)
- DevOps engineers (production deployment)
- QA engineers (test environments)
- System administrators (maintenance)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Volume Management](#volume-management)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [Scaling & Performance](#scaling--performance)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum Requirements** (Local Development):
- **CPU**: 4 cores (Intel i5/AMD Ryzen 5 or better)
- **RAM**: 8 GB (16 GB recommended)
- **Disk**: 20 GB free space (SSD recommended)
- **OS**: macOS 10.15+, Ubuntu 20.04+, Windows 10+ (WSL2)

**Recommended Requirements** (Production):
- **CPU**: 8 cores (Intel Xeon/AMD EPYC or better)
- **RAM**: 32 GB (64 GB for high traffic)
- **Disk**: 100 GB free space (SSD required)
- **OS**: Ubuntu 22.04 LTS, RHEL 8+, Amazon Linux 2

### Software Dependencies

**Required**:
- **Docker**: 24.0+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.20+ (bundled with Docker Desktop)
- **Git**: 2.30+ ([Install Git](https://git-scm.com/downloads))

**Optional**:
- **Make**: For using Makefile commands
- **curl**: For health checks and API testing

### Installation Verification

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.0.0 or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version v2.20.0 or higher

# Check Git version
git --version
# Expected: git version 2.30.0 or higher

# Verify Docker daemon is running
docker ps
# Expected: Empty list or running containers (no errors)
```

---

## Local Development Setup

### Step 1: Clone Repository

```bash
# Clone SDLC Orchestrator repository
git clone https://github.com/your-org/SDLC-Orchestrator.git
cd SDLC-Orchestrator

# Verify project structure
ls -la
# Expected: backend/, frontend/, docker-compose.yml, .env.example, Makefile
```

### Step 2: Configure Environment Variables

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

**Minimal Configuration** (.env):
```bash
# Database
POSTGRES_PASSWORD=changeme_secure_password_min_16_chars

# Redis
REDIS_PASSWORD=changeme_redis_password

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_changeme_16_chars

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production-minimum-32-characters-long

# Application
ENVIRONMENT=development
DEBUG=true
```

**⚠️ Security Warning**: Change default passwords in production!

### Step 3: Start Docker Services

```bash
# Start all services (PostgreSQL, Redis, MinIO, OPA, Prometheus, Grafana, Backend)
docker-compose up -d

# Expected output:
# Creating network "sdlc-network" ... done
# Creating volume "sdlc_postgres_data" ... done
# Creating volume "sdlc_redis_data" ... done
# Creating volume "sdlc_minio_data" ... done
# Creating sdlc-postgres ... done
# Creating sdlc-redis ... done
# Creating sdlc-minio ... done
# Creating sdlc-opa ... done
# Creating sdlc-prometheus ... done
# Creating sdlc-grafana ... done
# Creating sdlc-backend ... done
```

### Step 4: Verify Services are Running

```bash
# Check service status
docker-compose ps

# Expected output:
# NAME               STATUS              PORTS
# sdlc-postgres      Up (healthy)        0.0.0.0:5432->5432/tcp
# sdlc-redis         Up (healthy)        0.0.0.0:6379->6379/tcp
# sdlc-minio         Up (healthy)        0.0.0.0:9000-9001->9000-9001/tcp
# sdlc-opa           Up (healthy)        0.0.0.0:8181->8181/tcp
# sdlc-prometheus    Up (healthy)        0.0.0.0:9090->9090/tcp
# sdlc-grafana       Up (healthy)        0.0.0.0:3000->3000/tcp
# sdlc-backend       Up                  0.0.0.0:8000->8000/tcp
```

### Step 5: Run Database Migrations

```bash
# Run Alembic migrations to create database schema
docker-compose exec backend alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, create users table
# INFO  [alembic.runtime.migration] Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6g7, create gates table
# ...
```

**Alternative** (using Makefile):
```bash
make migrate
```

### Step 6: Verify API is Working

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy"}

# Test authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Expected output:
# {"access_token":"eyJhbGci...","token_type":"Bearer","expires_in":3600}
```

### Step 7: Access Web Interfaces

**Available Services**:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | N/A (JWT tokens) |
| **API Docs (Swagger)** | http://localhost:8000/docs | N/A |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | N/A |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin_changeme_16_chars |
| **Grafana** | http://localhost:3000 | admin / admin_changeme |
| **Prometheus** | http://localhost:9090 | N/A |
| **OPA** | http://localhost:8181 | N/A |

### Step 8: Stop Services

```bash
# Stop all services (preserves volumes)
docker-compose stop

# Stop and remove containers (preserves volumes)
docker-compose down

# Stop and remove everything (including volumes - DESTRUCTIVE!)
docker-compose down -v
```

**⚠️ Warning**: `docker-compose down -v` deletes all data (PostgreSQL, Redis, MinIO)!

---

## Production Deployment

### Overview

**Production Deployment Strategy**:
- ✅ Multi-stage Docker builds (smaller image sizes)
- ✅ Non-root user (security best practice)
- ✅ Health checks (container orchestration readiness)
- ✅ Environment-specific configuration (.env files)
- ✅ Volume mounts for data persistence
- ✅ Reverse proxy (NGINX/Traefik) for TLS termination

### Multi-Stage Dockerfile (Backend)

**File**: `backend/Dockerfile`

```dockerfile
# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Copy dependencies and application code
# ============================================================================
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r sdlc && useradd -r -g sdlc sdlc

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/sdlc/.local

# Copy application code
COPY --chown=sdlc:sdlc . .

# Set environment variables
ENV PATH=/home/sdlc/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER sdlc

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build Optimization**:
- ✅ Multi-stage build reduces image size by ~60% (300MB → 120MB)
- ✅ Non-root user improves security
- ✅ Health check enables Docker health monitoring
- ✅ `--no-cache-dir` reduces layer size

### Build Production Image

```bash
# Build backend image
docker build -t sdlc-orchestrator-backend:latest -f backend/Dockerfile backend/

# Expected output:
# [+] Building 45.3s (15/15) FINISHED
#  => [builder 1/5] FROM docker.io/library/python:3.11-slim
#  => [builder 2/5] WORKDIR /app
#  => [builder 3/5] RUN apt-get update && apt-get install -y gcc postgresql-client
#  => [builder 4/5] COPY requirements.txt .
#  => [builder 5/5] RUN pip install --no-cache-dir --user -r requirements.txt
#  => [runtime 1/5] FROM docker.io/library/python:3.11-slim
#  => [runtime 2/5] RUN groupadd -r sdlc && useradd -r -g sdlc sdlc
#  => [runtime 3/5] WORKDIR /app
#  => [runtime 4/5] COPY --from=builder /root/.local /home/sdlc/.local
#  => [runtime 5/5] COPY --chown=sdlc:sdlc . .
#  => exporting to image
#  => => naming to docker.io/library/sdlc-orchestrator-backend:latest

# Verify image size
docker images | grep sdlc-orchestrator-backend
# Expected: ~120MB (multi-stage build)
```

### Production docker-compose.yml

**File**: `docker-compose.prod.yml`

```yaml
version: '3.9'

services:
  # ============================================================================
  # PostgreSQL - Primary Database
  # ============================================================================
  postgres:
    image: postgres:15.5-alpine
    container_name: sdlc-postgres
    restart: always
    environment:
      POSTGRES_DB: sdlc_orchestrator
      POSTGRES_USER: sdlc_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups  # Database backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sdlc_user -d sdlc_orchestrator"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sdlc-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # ============================================================================
  # Redis - Caching + Sessions
  # ============================================================================
  redis:
    image: redis:7.2-alpine
    container_name: sdlc-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sdlc-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  # ============================================================================
  # MinIO - S3-Compatible Object Storage
  # ============================================================================
  minio:
    image: minio/minio:RELEASE.2024-01-01T16-36-33Z
    container_name: sdlc-minio
    restart: always
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
      MINIO_BROWSER_REDIRECT_URL: https://minio.your-domain.com
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sdlc-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # ============================================================================
  # OPA - Policy Engine
  # ============================================================================
  opa:
    image: openpolicyagent/opa:0.58.0
    container_name: sdlc-opa
    restart: always
    command:
      - "run"
      - "--server"
      - "--addr=0.0.0.0:8181"
      - "--log-level=info"
      - "/policies"
    ports:
      - "8181:8181"
    volumes:
      - ./policy-packs/rego:/policies:ro
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - sdlc-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # ============================================================================
  # FastAPI Backend - SDLC Orchestrator API
  # ============================================================================
  backend:
    image: sdlc-orchestrator-backend:latest
    container_name: sdlc-backend
    restart: always
    environment:
      # Database
      DATABASE_URL: postgresql+asyncpg://sdlc_user:${POSTGRES_PASSWORD}@postgres:5432/sdlc_orchestrator

      # JWT
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 60
      REFRESH_TOKEN_EXPIRE_DAYS: 30

      # MinIO
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      MINIO_BUCKET: evidence-vault
      MINIO_SECURE: "false"

      # OPA
      OPA_URL: http://opa:8181

      # Redis
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0

      # App
      ENVIRONMENT: production
      DEBUG: "false"
      ALLOWED_ORIGINS: https://app.your-domain.com,https://www.your-domain.com

    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
      opa:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - sdlc-network
    deploy:
      replicas: 3  # High availability
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s

  # ============================================================================
  # NGINX - Reverse Proxy + TLS Termination
  # ============================================================================
  nginx:
    image: nginx:1.25-alpine
    container_name: sdlc-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro  # TLS certificates
    depends_on:
      - backend
    networks:
      - sdlc-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local

networks:
  sdlc-network:
    driver: bridge
```

### Start Production Services

```bash
# Set production environment variables
export POSTGRES_PASSWORD="$(openssl rand -base64 32)"
export REDIS_PASSWORD="$(openssl rand -base64 32)"
export MINIO_ROOT_PASSWORD="$(openssl rand -base64 32)"
export JWT_SECRET_KEY="$(openssl rand -base64 48)"

# Save to .env.prod
cat > .env.prod <<EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENVIRONMENT=production
DEBUG=false
EOF

# Start production services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Verify services are healthy
docker-compose -f docker-compose.prod.yml ps
```

---

## Environment Configuration

### Environment Variables Reference

**Database (PostgreSQL)**:
```bash
POSTGRES_PASSWORD=<secure-password-min-16-chars>
DATABASE_URL=postgresql+asyncpg://sdlc_user:${POSTGRES_PASSWORD}@postgres:5432/sdlc_orchestrator
```

**Redis**:
```bash
REDIS_PASSWORD=<secure-password>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

**MinIO (S3-Compatible Storage)**:
```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<secure-password-min-16-chars>
MINIO_ENDPOINT=minio:9000
MINIO_USE_SSL=false  # true for HTTPS
MINIO_BUCKET_EVIDENCE=evidence-vault
MINIO_BUCKET_ORCHDOCS=orchdocs
MINIO_BUCKET_REPORTS=reports
```

**OPA (Open Policy Agent)**:
```bash
OPA_URL=http://opa:8181
```

**JWT Authentication**:
```bash
JWT_SECRET_KEY=<random-string-min-32-chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

**Application**:
```bash
ENVIRONMENT=development  # or production
DEBUG=true  # false for production
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Monitoring**:
```bash
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<secure-password>
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

### Secrets Management

**⚠️ NEVER commit .env files to Git!**

**Development** (.gitignore):
```bash
# Ignore environment files
.env
.env.local
.env.*.local
.env.prod
```

**Production** (Recommended Strategies):

**1. Docker Secrets** (Docker Swarm):
```bash
# Create secret
echo "my-secure-password" | docker secret create postgres_password -

# Use secret in docker-compose.yml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password

secrets:
  postgres_password:
    external: true
```

**2. AWS Secrets Manager** (AWS ECS/EKS):
```bash
# Store secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name sdlc/postgres/password \
  --secret-string "my-secure-password"

# Reference in ECS task definition
{
  "secrets": [
    {
      "name": "POSTGRES_PASSWORD",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:sdlc/postgres/password"
    }
  ]
}
```

**3. HashiCorp Vault** (Kubernetes):
```yaml
# Vault Kubernetes integration
apiVersion: v1
kind: Secret
metadata:
  name: sdlc-secrets
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "sdlc-app"
    vault.hashicorp.com/agent-inject-secret-postgres: "secret/data/sdlc/postgres"
```

---

## Volume Management

### Data Persistence Strategy

**Docker Volumes** (Recommended):
- ✅ Managed by Docker (automatic lifecycle)
- ✅ Platform-independent (works on Linux, macOS, Windows)
- ✅ Better performance than bind mounts
- ✅ Easier to backup and restore

**Volumes in docker-compose.yml**:
```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

### Backup Strategy

**PostgreSQL Backup**:
```bash
# Manual backup (pg_dump)
docker-compose exec postgres pg_dump -U sdlc_user sdlc_orchestrator > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backups (cron)
# Add to crontab: 0 2 * * * /path/to/backup_script.sh
cat > backup_script.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

docker-compose exec -T postgres pg_dump -U sdlc_user sdlc_orchestrator | gzip > "$BACKUP_DIR/sdlc_orchestrator_$TIMESTAMP.sql.gz"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup_script.sh
```

**Restore from Backup**:
```bash
# Restore from backup file
gunzip -c backup_20251118_020000.sql.gz | docker-compose exec -T postgres psql -U sdlc_user sdlc_orchestrator
```

**MinIO Backup** (S3 files):
```bash
# Sync MinIO data to AWS S3 (disaster recovery)
docker run --rm -it \
  -v sdlc_minio_data:/data \
  -e AWS_ACCESS_KEY_ID=<aws-key> \
  -e AWS_SECRET_ACCESS_KEY=<aws-secret> \
  amazon/aws-cli s3 sync /data s3://sdlc-backups/minio/ --storage-class GLACIER

# Schedule daily backups (cron)
0 3 * * * docker run --rm -v sdlc_minio_data:/data -e AWS_ACCESS_KEY_ID=<key> -e AWS_SECRET_ACCESS_KEY=<secret> amazon/aws-cli s3 sync /data s3://sdlc-backups/minio/
```

### Volume Inspection

```bash
# List all volumes
docker volume ls

# Inspect volume
docker volume inspect sdlc_postgres_data

# Output:
# [
#     {
#         "CreatedAt": "2025-11-18T10:00:00Z",
#         "Driver": "local",
#         "Labels": {
#             "com.docker.compose.project": "sdlc-orchestrator",
#             "com.docker.compose.volume": "postgres_data"
#         },
#         "Mountpoint": "/var/lib/docker/volumes/sdlc_postgres_data/_data",
#         "Name": "sdlc_postgres_data",
#         "Options": null,
#         "Scope": "local"
#     }
# ]

# Access volume data (requires root on Linux)
sudo ls -la /var/lib/docker/volumes/sdlc_postgres_data/_data
```

---

## Health Checks & Monitoring

### Container Health Checks

**PostgreSQL Health Check**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U sdlc_user -d sdlc_orchestrator"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Redis Health Check**:
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Backend Health Check**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 40s
  retries: 3
```

### Monitoring Service Health

```bash
# Check health status of all services
docker-compose ps

# Check specific service health
docker inspect --format='{{json .State.Health}}' sdlc-postgres | jq

# Output:
# {
#   "Status": "healthy",
#   "FailingStreak": 0,
#   "Log": [
#     {
#       "Start": "2025-11-18T10:00:00Z",
#       "End": "2025-11-18T10:00:01Z",
#       "ExitCode": 0,
#       "Output": "postgres is ready"
#     }
#   ]
# }
```

### Application Metrics (Prometheus)

**Prometheus Metrics Endpoint**:
```bash
# Backend exposes metrics at /metrics
curl http://localhost:8000/metrics

# Output (Prometheus format):
# # HELP http_requests_total Total HTTP requests
# # TYPE http_requests_total counter
# http_requests_total{method="GET",path="/api/v1/auth/me",status="200"} 1234
# http_requests_total{method="POST",path="/api/v1/auth/login",status="200"} 567
#
# # HELP http_request_duration_seconds HTTP request duration
# # TYPE http_request_duration_seconds histogram
# http_request_duration_seconds_bucket{le="0.1"} 1000
# http_request_duration_seconds_bucket{le="0.5"} 1500
# http_request_duration_seconds_sum 125.5
# http_request_duration_seconds_count 1567
```

**Grafana Dashboards**:
- **System Overview**: http://localhost:3000 (admin / admin_changeme)
- **Pre-configured Dashboards**:
  - API Request Rate (requests/second)
  - API Latency (p50, p95, p99)
  - Error Rate (4xx, 5xx errors)
  - Database Connections (active, idle)
  - Cache Hit Rate (Redis)

---

## Scaling & Performance

### Horizontal Scaling (Multiple Backend Replicas)

**docker-compose.yml** (Deploy section):
```yaml
services:
  backend:
    deploy:
      replicas: 3  # Run 3 backend instances
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

**Load Balancing** (NGINX):
```nginx
# nginx/nginx.conf
upstream backend {
    least_conn;  # Load balancing algorithm
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Resource Limits

**CPU & Memory Limits**:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'       # Max 2 CPU cores
          memory: 4G      # Max 4GB RAM
        reservations:
          cpus: '1'       # Guaranteed 1 CPU core
          memory: 2G      # Guaranteed 2GB RAM
```

**Verify Resource Usage**:
```bash
# Monitor real-time resource usage
docker stats

# Output:
# CONTAINER      CPU %   MEM USAGE / LIMIT   MEM %   NET I/O         BLOCK I/O
# sdlc-backend   45.2%   1.5GiB / 4GiB       37.5%   125MB / 89MB    12MB / 5MB
# sdlc-postgres  12.3%   800MB / 4GiB        20.0%   45MB / 32MB     890MB / 120MB
```

### Performance Optimization

**PostgreSQL Connection Pooling** (SQLAlchemy):
```python
# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_size=20,          # Min connections
    max_overflow=30,       # Max additional connections
    pool_pre_ping=True,    # Check connection health before use
    echo=False,            # Disable SQL logging in production
)
```

**Redis Connection Pooling** (aioredis):
```python
# backend/app/core/cache.py
import redis.asyncio as redis

redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    max_connections=50,  # Connection pool size
)
```

---

## Security Best Practices

### 1. Use Non-Root User in Containers

```dockerfile
# Create non-root user
RUN groupadd -r sdlc && useradd -r -g sdlc sdlc
USER sdlc
```

### 2. Use Secrets for Sensitive Data

```bash
# ❌ DON'T hardcode secrets
POSTGRES_PASSWORD=password123  # BAD!

# ✅ DO use environment variables
POSTGRES_PASSWORD=$(openssl rand -base64 32)  # GOOD!
```

### 3. Enable TLS/SSL

**NGINX TLS Configuration**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://backend:8000;
    }
}
```

### 4. Restrict Network Access

**docker-compose.yml** (Internal networks):
```yaml
services:
  postgres:
    # DON'T expose port publicly in production
    # ports:
    #   - "5432:5432"  # ❌ Publicly accessible!
    networks:
      - sdlc-network  # ✅ Internal network only

  backend:
    ports:
      - "8000:8000"  # Only backend exposed via NGINX
```

### 5. Regular Security Updates

```bash
# Update base images regularly
docker pull postgres:15.5-alpine
docker pull redis:7.2-alpine
docker pull python:3.11-slim

# Rebuild images with updated dependencies
docker-compose build --no-cache
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Port Already in Use

**Error**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use
```

**Solution**:
```bash
# Find process using port 5432
lsof -i :5432

# Kill process (or use different port)
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5433:5432"  # Use host port 5433 instead
```

#### Issue 2: Container Unhealthy

**Error**:
```
sdlc-postgres is unhealthy
```

**Solution**:
```bash
# Check container logs
docker-compose logs postgres

# Check health check status
docker inspect --format='{{json .State.Health}}' sdlc-postgres | jq

# Restart container
docker-compose restart postgres
```

#### Issue 3: Database Migration Failed

**Error**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'a1b2c3d4e5f6'
```

**Solution**:
```bash
# Check current migration version
docker-compose exec backend alembic current

# Reset migrations (DESTRUCTIVE - only for development!)
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head

# Or reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

#### Issue 4: Out of Memory

**Error**:
```
docker: Error response from daemon: OCI runtime create failed: container_linux.go:349: starting container process caused "process_linux.go:449: container init caused \"process_linux.go:432: running prestart hook 0 caused \\\"error running hook: exit status 1, stdout: , stderr: time=\\\"2025-11-18T10:00:00Z\\\" level=error msg=\\\"container_linux.go:348: starting container process caused \\\\\\\"process_linux.go:279: applying cgroup configuration for process caused \\\\\\\\\\\\\\\"open /sys/fs/cgroup/memory/docker/... : no space left on device\\\\\\\\\\\\\\\"\\\\\\\"\\\"\"": unknown.
```

**Solution**:
```bash
# Check Docker disk usage
docker system df

# Clean up unused containers, images, volumes
docker system prune -a --volumes

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 8 GB (minimum)
```

#### Issue 5: Cannot Connect to Database

**Error**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: Connection refused
```

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify DATABASE_URL is correct
docker-compose exec backend env | grep DATABASE_URL

# Test connection manually
docker-compose exec postgres psql -U sdlc_user -d sdlc_orchestrator -c "SELECT 1;"
```

### Debug Mode

**Enable Verbose Logging**:
```bash
# docker-compose.yml
services:
  backend:
    environment:
      DEBUG: "true"
      LOG_LEVEL: "DEBUG"

# Restart services
docker-compose restart backend

# Tail logs
docker-compose logs -f backend
```

### Performance Profiling

**Slow API Requests**:
```bash
# Check API request duration
curl -w "\nTime Total: %{time_total}s\n" http://localhost:8000/api/v1/auth/me

# Check database slow queries (PostgreSQL)
docker-compose exec postgres psql -U sdlc_user -d sdlc_orchestrator -c "
  SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"
```

---

## Makefile Commands

**Available Commands**:
```bash
# Setup
make install          # Install dependencies
make quickstart       # First-time setup (copy .env, install, start services)

# Development
make up               # Start all services
make down             # Stop all services
make restart          # Restart all services
make logs             # Show logs from all services
make clean            # Remove containers and volumes (DESTRUCTIVE!)

# Database
make migrate          # Run database migrations
make migrate-create   # Create new migration
make seed             # Seed database with test data
make db-reset         # Reset database (drop + migrate + seed)
make backup           # Backup database to ./backups/

# Testing
make test             # Run all tests
make test-backend     # Run backend tests only
make lint             # Run linters
make format           # Format code

# Health Checks
make health           # Check health of all services
make shell-db         # Open PostgreSQL shell
make shell-redis      # Open Redis shell
```

---

## Additional Resources

### Documentation
- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose Documentation**: https://docs.docker.com/compose/
- **PostgreSQL Docker Image**: https://hub.docker.com/_/postgres
- **Redis Docker Image**: https://hub.docker.com/_/redis
- **MinIO Docker Image**: https://hub.docker.com/r/minio/minio

### Internal Documentation
- **C4 Architecture Diagrams**: [C4-ARCHITECTURE-DIAGRAMS.md](../../02-Design-Architecture/02-System-Architecture/C4-ARCHITECTURE-DIAGRAMS.md)
- **API Developer Guide**: [API-DEVELOPER-GUIDE.md](../../02-Design-Architecture/04-API-Design/API-DEVELOPER-GUIDE.md)
- **Database Migration Strategy**: [DATABASE-MIGRATION-STRATEGY.md](./DATABASE-MIGRATION-STRATEGY.md)
- **Monitoring & Observability Guide**: [MONITORING-OBSERVABILITY-GUIDE.md](../02-Environment-Management/MONITORING-OBSERVABILITY-GUIDE.md)
- **Kubernetes Deployment Guide**: [KUBERNETES-DEPLOYMENT-GUIDE.md](./KUBERNETES-DEPLOYMENT-GUIDE.md) *(Coming Next)*
- **Cloud Deployment Guide**: [CLOUD-DEPLOYMENT-GUIDE.md](./CLOUD-DEPLOYMENT-GUIDE.md) *(Coming Next)*

---

**Last Updated**: November 18, 2025
**Owner**: Backend Lead + DevOps Lead + CTO
**Status**: ✅ ACTIVE (Week 4 Day 1)

---

**End of Docker Deployment Guide v1.0.0**
