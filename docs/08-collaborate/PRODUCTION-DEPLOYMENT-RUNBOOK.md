# Production Deployment Runbook

**Version**: 1.0.0
**Date**: November 27, 2025
**Status**: ACTIVE - Week 13 Production Launch
**Authority**: DevOps Lead + CTO
**Framework**: SDLC 5.1.3 Complete Lifecycle
**Type**: Blue-Green Deployment

---

## Pre-Deployment Checklist

### 1. Gate G3 Approval

- [ ] CTO signed off
- [ ] CPO signed off
- [ ] Security Lead signed off
- [ ] All blocking issues resolved

### 2. Infrastructure Ready

- [ ] Kubernetes cluster provisioned
- [ ] DNS records configured
- [ ] SSL certificates valid
- [ ] Load balancer configured
- [ ] Database provisioned (PostgreSQL 15.5)
- [ ] Redis cluster provisioned
- [ ] MinIO storage provisioned
- [ ] OPA policies deployed

### 3. Docker Images

- [ ] Backend image built and pushed
- [ ] Frontend image built and pushed
- [ ] Images scanned for vulnerabilities
- [ ] Image tags match release version

### 4. Configuration

- [ ] Production secrets created
- [ ] ConfigMaps deployed
- [ ] Environment variables verified
- [ ] CORS origins configured

---

## Deployment Procedure

### Step 1: Build Docker Images

```bash
# Backend
cd backend
docker build -t sdlc-orchestrator-backend:v1.0.0 .
docker push registry.sdlc-orchestrator.com/backend:v1.0.0

# Frontend
cd frontend/web
docker build -t sdlc-orchestrator-frontend:v1.0.0 .
docker push registry.sdlc-orchestrator.com/frontend:v1.0.0
```

### Step 2: Update Kubernetes Manifests

```bash
# Update image tags in kustomization.yaml
cd k8s/overlays/prod
vim kustomization.yaml

# Verify changes
kubectl kustomize . | less
```

### Step 3: Database Migration

```bash
# Run Alembic migrations
kubectl apply -f k8s/jobs/alembic-migrate.yaml

# Verify migration completed
kubectl logs -f job/alembic-migrate -n sdlc-orchestrator
```

### Step 4: Deploy Green Environment

```bash
# Deploy to green environment
kubectl apply -k k8s/overlays/prod-green

# Wait for pods to be ready
kubectl rollout status deployment/backend-green -n sdlc-orchestrator

# Verify health checks
kubectl exec -it deployment/backend-green -n sdlc-orchestrator -- curl localhost:8000/health
```

### Step 5: Run Smoke Tests

```bash
# Run smoke test suite
kubectl apply -f k8s/jobs/smoke-test.yaml

# Check results
kubectl logs -f job/smoke-test -n sdlc-orchestrator

# Expected output:
# ✅ Health check passed
# ✅ Auth endpoint responding
# ✅ Database connection OK
# ✅ Redis connection OK
# ✅ MinIO connection OK
# ✅ OPA connection OK
```

### Step 6: Switch Traffic (Blue → Green)

```bash
# Update ingress to point to green
kubectl patch ingress sdlc-orchestrator-ingress -n sdlc-orchestrator \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "backend-green"}]'

# Verify traffic switch
curl -s https://api.sdlc-orchestrator.com/health
```

### Step 7: Monitor

```bash
# Watch logs
kubectl logs -f deployment/backend-green -n sdlc-orchestrator

# Check metrics
open https://grafana.sdlc-orchestrator.com/d/sdlc-overview

# Monitor error rate
# Target: <0.1% error rate for 10 minutes
```

### Step 8: Cleanup Blue Environment

```bash
# After 24 hours of stable operation
kubectl delete -k k8s/overlays/prod-blue
```

---

## Rollback Procedure

### Immediate Rollback (< 5 minutes)

If issues detected immediately after traffic switch:

```bash
# Switch traffic back to blue
kubectl patch ingress sdlc-orchestrator-ingress -n sdlc-orchestrator \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "backend-blue"}]'

# Verify rollback
curl -s https://api.sdlc-orchestrator.com/health
```

### Database Rollback

If database migration caused issues:

```bash
# Run Alembic downgrade
kubectl apply -f k8s/jobs/alembic-downgrade.yaml

# Verify
kubectl logs -f job/alembic-downgrade -n sdlc-orchestrator
```

### Full Rollback

If complete rollback required:

```bash
# 1. Switch traffic to blue
# 2. Scale down green
kubectl scale deployment backend-green --replicas=0 -n sdlc-orchestrator

# 3. Investigate logs
kubectl logs deployment/backend-green -n sdlc-orchestrator --previous

# 4. Fix issues and redeploy
```

---

## Post-Deployment Verification

### Health Checks

```bash
# Backend health
curl -s https://api.sdlc-orchestrator.com/health

# Expected response:
# {"status":"healthy","version":"1.0.0","service":"sdlc-orchestrator-backend"}
```

### API Verification

```bash
# Login
TOKEN=$(curl -s -X POST https://api.sdlc-orchestrator.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sdlc-orchestrator.io","password":"PROD_PASSWORD"}' \
  | jq -r '.access_token')

# Dashboard stats
curl -s https://api.sdlc-orchestrator.com/api/v1/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"
```

### Database Verification

```bash
# Check migrations
kubectl exec -it statefulset/postgres -n sdlc-orchestrator -- \
  psql -U postgres -d sdlc_orchestrator -c "SELECT * FROM alembic_version;"

# Check table count
kubectl exec -it statefulset/postgres -n sdlc-orchestrator -- \
  psql -U postgres -d sdlc_orchestrator -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
# Expected: 21 tables
```

---

## Monitoring Dashboards

### Grafana URLs

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Overview | /d/sdlc-overview | High-level metrics |
| Backend | /d/sdlc-backend | API performance |
| Database | /d/sdlc-postgres | PostgreSQL metrics |
| Redis | /d/sdlc-redis | Cache performance |

### Key Metrics to Watch

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Error Rate | <0.1% | >1% |
| API Latency (p95) | <100ms | >500ms |
| CPU Usage | <70% | >85% |
| Memory Usage | <80% | >90% |
| Database Connections | <80 | >100 |

### Alert Channels

| Severity | Channel | Response Time |
|----------|---------|---------------|
| P0 (Critical) | PagerDuty + Slack | <15 min |
| P1 (High) | Slack #alerts | <1 hour |
| P2 (Medium) | Slack #ops | <4 hours |
| P3 (Low) | Jira | <24 hours |

---

## On-Call Rotation

### Week 1 (Launch Week)

| Day | Primary | Secondary |
|-----|---------|-----------|
| Mon | DevOps Lead | Backend Lead |
| Tue | Backend Lead | Frontend Lead |
| Wed | DevOps Lead | Backend Lead |
| Thu | Backend Lead | DevOps Lead |
| Fri | DevOps Lead | All Hands |
| Sat | Backend Lead | DevOps Lead |
| Sun | DevOps Lead | Backend Lead |

### Escalation Matrix

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | First response |
| L2 | Team lead | Issue not resolved in 30 min |
| L3 | CTO | Production down > 1 hour |

---

## Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| DevOps Lead | TBD | TBD | @devops-lead |
| Backend Lead | TBD | TBD | @backend-lead |
| CTO | TBD | TBD | @cto |

---

## Appendix: Useful Commands

### Kubernetes

```bash
# Get all pods
kubectl get pods -n sdlc-orchestrator

# Describe pod
kubectl describe pod POD_NAME -n sdlc-orchestrator

# Get logs
kubectl logs -f POD_NAME -n sdlc-orchestrator

# Exec into pod
kubectl exec -it POD_NAME -n sdlc-orchestrator -- /bin/sh

# Scale deployment
kubectl scale deployment/backend --replicas=5 -n sdlc-orchestrator
```

### Database

```bash
# Connect to PostgreSQL
kubectl exec -it statefulset/postgres -n sdlc-orchestrator -- psql -U postgres -d sdlc_orchestrator

# Backup database
kubectl exec statefulset/postgres -n sdlc-orchestrator -- pg_dump -U postgres sdlc_orchestrator > backup.sql
```

### Redis

```bash
# Connect to Redis
kubectl exec -it deployment/redis -n sdlc-orchestrator -- redis-cli -a PASSWORD

# Flush cache (emergency only)
kubectl exec -it deployment/redis -n sdlc-orchestrator -- redis-cli -a PASSWORD FLUSHALL
```

---

*This document is part of the SDLC 5.1.3 Complete Lifecycle documentation.*

**Generated**: November 27, 2025
**Version**: 1.0.0
**Classification**: Internal - DevOps
