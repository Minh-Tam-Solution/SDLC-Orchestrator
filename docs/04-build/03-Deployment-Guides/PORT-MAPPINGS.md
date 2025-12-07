# SDLC Orchestrator - Port Mappings
**Created**: 2025-12-16 (Sprint 33 Day 3)
**Purpose**: Document all port allocations for Production and Beta environments

---

## 📍 **Port Allocation Strategy**

Due to shared infrastructure with other NQH projects (BFlow, NQHBot, Kafka, Sentry, etc.), SDLC Orchestrator uses non-standard ports to avoid conflicts.

### **Occupied Ports (Other Projects)**
| Port | Service | Project |
|------|---------|---------|
| 3000 | Open WebUI | Infrastructure |
| 5432 | PostgreSQL (production) | SDLC Orchestrator Production |
| 6379 | Redis Master | Infrastructure |
| 6380 | Redis | n8n |
| 6381 | Redis | BFlow |
| 8181 | OPA | SDLC Orchestrator Production |
| 9000 | Clickhouse / Sentry | Infrastructure |
| 9090 | Kafka UI | Infrastructure |
| 9092-9093 | Kafka | Infrastructure |
| 9094 | Prometheus | NQH |
| 9099 | Sentry Web | Infrastructure |

---

## 🔵 **PRODUCTION Environment Ports**

**Container Prefix**: `sdlc-*`
**Network**: `sdlc-orchestrator_sdlc-network`
**Compose File**: `docker-compose.yml`

| Service | Container Name | Internal Port | Host Port | Access URL |
|---------|----------------|---------------|-----------|------------|
| **Backend** | sdlc-backend | 8000 | 8000 | http://localhost:8000 |
| **Frontend** | sdlc-frontend | 80 | 8310 | http://localhost:8310 |
| **PostgreSQL** | sdlc-postgres | 5432 | 5432 | postgresql://localhost:5432 |
| **Redis** | sdlc-redis | 6379 | 6382 | redis://localhost:6382 |
| **MinIO S3 API** | sdlc-minio | 9000 | 9097 | http://localhost:9097 |
| **MinIO Console** | sdlc-minio | 9001 | 9098 | http://localhost:9098 |
| **OPA** | sdlc-opa | 8181 | 8181 | http://localhost:8181 |
| **Prometheus** | sdlc-prometheus | 9090 | 9096 | http://localhost:9096 |
| **Grafana** | sdlc-grafana | 3000 | 3001 | http://localhost:3001 |
| **Alertmanager** | sdlc-alertmanager | 9093 | 9095 | http://localhost:9095 |

### **Production Health Checks**
```bash
# Backend API
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"1.1.0","service":"sdlc-orchestrator-backend"}

# Frontend
curl http://localhost:8310/health
# Expected: "healthy"

# PostgreSQL
docker exec sdlc-postgres pg_isready -U sdlc_user
# Expected: "sdlc_user ready to accept connections"

# Redis
docker exec sdlc-redis redis-cli --raw incr ping
# Expected: (integer) 1

# MinIO
curl http://localhost:9097/minio/health/live
# Expected: 200 OK

# Prometheus
curl http://localhost:9096/-/healthy
# Expected: 200 OK

# Grafana
curl http://localhost:3001/api/health
# Expected: {"commit":"...","database":"ok","version":"10.2.0"}
```

---

## 🟢 **BETA Environment Ports**

**Container Prefix**: `sdlc-beta-*`
**Network**: `sdlc-beta-network`
**Compose File**: `docker-compose.beta.yml`
**Env File**: `.env.beta`
**External URL**: `https://sdlc.nqh.vn` (via Cloudflare Tunnel)

| Service | Container Name | Internal Port | Host Port | Access URL |
|---------|----------------|---------------|-----------|------------|
| **Backend** | sdlc-beta-backend | 8000 | 8001 | http://localhost:8001 |
| **Frontend** | sdlc-beta-frontend | 80 | 8311 | http://localhost:8311 |
| **PostgreSQL** | sdlc-beta-postgres | 5432 | 5435 | postgresql://localhost:5435 |
| **Redis** | sdlc-beta-redis | 6379 | 6383 | redis://localhost:6383 |
| **MinIO S3 API** | sdlc-beta-minio | 9000 | 9002 | http://localhost:9002 |
| **MinIO Console** | sdlc-beta-minio | 9001 | 9003 | http://localhost:9003 |
| **OPA** | sdlc-beta-opa | 8181 | 8182 | http://localhost:8182 |
| **Prometheus** | sdlc-beta-prometheus | 9090 | 9091 | http://localhost:9091 |
| **Grafana** | sdlc-beta-grafana | 3000 | 3002 | http://localhost:3002 |
| **Alertmanager** | sdlc-beta-alertmanager | 9093 | 9100 | http://localhost:9100 |

### **Beta Health Checks**
```bash
# Backend API
curl http://localhost:8001/health
# Expected: {"status":"healthy","version":"1.1.0","service":"sdlc-orchestrator-backend"}

# Frontend
curl http://localhost:8311/health
# Expected: "healthy"

# PostgreSQL
docker exec sdlc-beta-postgres pg_isready -U sdlc_user
# Expected: "sdlc_user ready to accept connections"

# Redis
docker exec sdlc-beta-redis redis-cli --raw incr ping
# Expected: (integer) 1

# MinIO
curl http://localhost:9002/minio/health/live
# Expected: 200 OK

# Prometheus
curl http://localhost:9091/-/healthy
# Expected: 200 OK

# Grafana
curl http://localhost:3002/api/health
# Expected: {"commit":"...","database":"ok","version":"10.2.0"}
```

---

## 🔄 **Quick Commands**

### **Start Environments**
```bash
# Production
docker compose up -d

# Beta
docker compose -f docker-compose.beta.yml --env-file .env.beta up -d
```

### **Check Status**
```bash
# Production
docker compose ps

# Beta
docker compose -f docker-compose.beta.yml --env-file .env.beta ps
```

### **View Logs**
```bash
# Production Backend
docker compose logs -f backend

# Beta Backend
docker compose -f docker-compose.beta.yml --env-file .env.beta logs -f backend
```

### **Stop Environments**
```bash
# Production
docker compose down

# Beta
docker compose -f docker-compose.beta.yml --env-file .env.beta down
```

---

## 🌐 **Cloudflare Tunnel Configuration (Beta)**

**Public URL**: `https://sdlc.nqh.vn`
**Tunnel Name**: `sdlc-beta-tunnel`
**Target**: `http://localhost:8311` (Beta Frontend)

### **Tunnel Setup**
```bash
# Install cloudflared (if not already)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate (first time only)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create sdlc-beta-tunnel

# Configure tunnel
cloudflared tunnel route dns sdlc-beta-tunnel sdlc.nqh.vn

# Run tunnel
cloudflared tunnel run sdlc-beta-tunnel
```

### **Tunnel Config File** (`~/.cloudflared/config.yml`)
```yaml
tunnel: sdlc-beta-tunnel
credentials-file: /home/nqh/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: sdlc.nqh.vn
    service: http://localhost:8311
  - service: http_status:404
```

---

## 📊 **Port Range Summary**

| Range | Purpose |
|-------|---------|
| 3000-3099 | Web UIs (Grafana, monitoring dashboards) |
| 5432-5499 | PostgreSQL databases |
| 6379-6399 | Redis instances |
| 8000-8399 | Backend APIs |
| 8181-8199 | Policy engines (OPA) |
| 9000-9199 | Object storage (MinIO), monitoring (Prometheus), alerting |

### **Reserved for Future Environments**
| Environment | Port Range | Status |
|-------------|------------|--------|
| Staging | 8300-8399 (Backend), 5450-5499 (DB) | Used in Sprint 33 Day 2 |
| QA | 8400-8499 (Backend), 5500-5599 (DB) | Reserved |
| Demo | 8500-8599 (Backend), 5600-5699 (DB) | Reserved |

---

## 🚨 **Known Issues**

### **Issue 1: Port 5433 Persistent Binding**
**Symptom**: Beta PostgreSQL can't bind to 5433 despite `lsof` showing no process.
**Workaround**: Use port 5435 instead.
**Root Cause**: Suspected stale Docker network binding.

### **Issue 2: Multiple Infrastructure Port Conflicts**
**Impact**: Production required 6 port remaps to avoid conflicts with Kafka, Sentry, n8n, BFlow.
**Solution**: Documented port allocation strategy above.
**Prevention**: Future projects should consult this document before deployment.

---

## ✅ **Validation Checklist**

Before deploying a new environment, verify:

- [ ] All required ports are available (check with `lsof -i :<port>`)
- [ ] Docker network name is unique (production: `sdlc-orchestrator_sdlc-network`, beta: `sdlc-beta-network`)
- [ ] Container names are unique (production: `sdlc-*`, beta: `sdlc-beta-*`)
- [ ] `.env` file has production-grade secrets (SECRET_KEY ≥32 chars)
- [ ] ALLOWED_ORIGINS matches the Cloudflare Tunnel domain

---

**Last Updated**: 2025-12-16 (Sprint 33 Day 3)
**Owner**: DevOps Team
**Status**: ✅ PRODUCTION + BETA DEPLOYED (9/9 services each)
