# SDLC Orchestrator - Deployment Runbook

**Version**: 1.0.0
**Last Updated**: January 29, 2026
**Owner**: DevOps Team
**Framework**: SDLC 6.1.0

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Standard Deployment](#standard-deployment)
3. [Canary Deployment](#canary-deployment)
4. [Rollback Procedures](#rollback-procedures)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Required Prerequisites

Before deploying to any environment, ensure:

```bash
# 1. Run pre-production checks
cd backend/scripts/production
python pre_production_check.py --all

# 2. Verify all checks pass (minimum thresholds)
# Security: 100% pass
# Performance: API p95 < 100ms
# Infrastructure: K8s manifests valid
# Documentation: All runbooks exist
```

### Environment Variables

Ensure these are set in your environment or CI/CD:

```bash
# Required
export KUBECONFIG=/path/to/kubeconfig
export DOCKER_REGISTRY=registry.sdlc-orchestrator.io
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Optional
export CANARY_PERCENTAGE=10
export ROLLOUT_TIMEOUT=600
```

### Access Requirements

| Resource | Access Level | Contact |
|----------|-------------|---------|
| Kubernetes Cluster | `cluster-admin` | DevOps Lead |
| Docker Registry | Push access | DevOps Lead |
| Slack Webhooks | Post permission | DevOps Lead |
| Vault Secrets | Read access | Security Lead |

---

## Standard Deployment

### Step 1: Prepare Release

```bash
# 1. Ensure on main branch with latest code
git checkout main
git pull origin main

# 2. Run tests
pytest --cov=app --cov-report=term-missing

# 3. Verify version bump in pyproject.toml
grep "version" pyproject.toml
```

### Step 2: Execute Deployment

```bash
# Navigate to deployment scripts
cd backend/scripts/production

# Deploy to staging first
python deploy.py --version 1.2.0 --env staging

# After staging validation, deploy to production
python deploy.py --version 1.2.0 --env production --auto-rollback
```

### Step 3: Monitor Deployment

```bash
# Watch rollout status
kubectl rollout status deployment/sdlc-api -n sdlc-production

# Check pod health
kubectl get pods -n sdlc-production -l app=sdlc-api

# View recent logs
kubectl logs -n sdlc-production -l app=sdlc-api --tail=100
```

### Step 4: Verify Success

```bash
# Run smoke tests
curl -s https://api.sdlc-orchestrator.io/health | jq

# Expected response:
{
  "status": "healthy",
  "version": "1.2.0",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "opa": "healthy",
    "minio": "healthy"
  }
}
```

---

## Canary Deployment

For high-risk changes, use canary deployment:

### Step 1: Deploy Canary (10% Traffic)

```bash
python deploy.py --version 1.2.0 --env canary --canary-percentage 10
```

### Step 2: Monitor Canary Metrics

Watch for 30 minutes:
- Error rate comparison (canary vs stable)
- Latency comparison (p50, p95, p99)
- Resource usage (CPU, memory)

```bash
# Prometheus query for error rate comparison
rate(http_requests_total{version="1.2.0",status=~"5.."}[5m])
/
rate(http_requests_total{version="1.2.0"}[5m])
```

### Step 3: Promote or Rollback

```bash
# If canary looks good, promote to 100%
python deploy.py --version 1.2.0 --env production --promote-canary

# If canary shows issues, rollback
python deploy.py --rollback --previous-version 1.1.0
```

---

## Rollback Procedures

### Automatic Rollback

If deployment fails any health check, automatic rollback triggers:

```bash
# Automatic rollback is enabled by default with --auto-rollback
python deploy.py --version 1.2.0 --env production --auto-rollback
```

### Manual Rollback

For manual rollback:

```bash
# Option 1: Using deploy script
python deploy.py --rollback --previous-version 1.1.0

# Option 2: Direct kubectl (emergency)
kubectl rollout undo deployment/sdlc-api -n sdlc-production

# Option 3: Rollback to specific revision
kubectl rollout undo deployment/sdlc-api -n sdlc-production --to-revision=3
```

### Database Rollback

If database migration needs rollback:

```bash
# Check current revision
alembic current

# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123def456
```

**WARNING**: Database rollbacks may cause data loss. Always backup first.

---

## Post-Deployment Verification

### Health Check Endpoints

| Endpoint | Expected Status | Response Time |
|----------|----------------|---------------|
| `/health` | 200 OK | < 100ms |
| `/api/v1/gates/health` | 200 OK | < 200ms |
| `/api/v1/evidence/health` | 200 OK | < 200ms |

### Monitoring Dashboard

After deployment, verify in Grafana:

1. **API Metrics**: Request rate, error rate, latency
2. **Gate Evaluations**: Success rate, duration
3. **Pod Health**: CPU, memory, restart count
4. **Database**: Connection pool, query latency

### Alerting Verification

Ensure alerts are firing correctly:

```bash
# Check Alertmanager
curl -s http://alertmanager:9093/api/v1/alerts | jq '.data[] | .labels.alertname'

# Should NOT see any critical alerts
```

---

## Troubleshooting

### Deployment Stuck in Pending

```bash
# Check events
kubectl describe deployment sdlc-api -n sdlc-production

# Common causes:
# - Insufficient resources (scale up node pool)
# - Image pull errors (check registry credentials)
# - ConfigMap/Secret missing (check mounted volumes)
```

### Pods CrashLooping

```bash
# Get pod logs
kubectl logs -n sdlc-production <pod-name> --previous

# Check resource limits
kubectl describe pod <pod-name> -n sdlc-production | grep -A5 "Limits"

# Common causes:
# - OOM killed (increase memory limit)
# - Health check failing (check /health endpoint)
# - Database connection refused (check connection string)
```

### High Latency After Deploy

```bash
# Check if HPA is scaling
kubectl get hpa -n sdlc-production

# Check pod resource usage
kubectl top pods -n sdlc-production

# Check database connections
kubectl exec -it <api-pod> -- python -c "from app.db import engine; print(engine.pool.status())"
```

### Database Migration Failed

```bash
# Check migration status
kubectl exec -it <api-pod> -- alembic current

# View migration history
kubectl exec -it <api-pod> -- alembic history

# Manually fix and re-run
kubectl exec -it <api-pod> -- alembic upgrade head
```

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| DevOps On-Call | Rotation | #devops-oncall Slack |
| Backend Lead | [Name] | @backend-lead Slack |
| CTO | [Name] | Direct escalation |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Jan 29, 2026 | DevOps Team | Initial runbook |

---

**Document Status**: ✅ Production Ready
