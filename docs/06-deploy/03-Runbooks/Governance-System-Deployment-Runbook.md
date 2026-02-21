# Governance System Deployment Runbook

**Document Type:** Operational Runbook  
**Sprint:** 116 - Full Enforcement (February 17-21, 2026)  
**Status:** PRODUCTION-READY  
**Owner:** CTO  
**Last Updated:** January 28, 2026  
**Framework:** SDLC 6.1.0 Governance System  

---

## 1. Executive Summary

This runbook provides step-by-step procedures for deploying the Framework 6.0 Governance System to production (FULL enforcement mode). Follow these steps carefully to ensure zero-downtime deployment.

**Deployment Timeline:**
- **Pre-Deployment:** 1 day (checklist verification)
- **Deployment:** 2-4 hours (phased rollout)
- **Post-Deployment:** 24 hours (monitoring period)

**Rollback Time:** <5 minutes (emergency mode toggle)

---

## 2. Pre-Deployment Checklist

### 2.1 Sprint 114 (WARNING Mode) Success Criteria ✅

- [ ] **100+ PRs evaluated** during dogfooding
- [ ] **PR latency impact <15%** (average over 5 days)
- [ ] **False positive rate <15%**
- [ ] **Complaint rate <10%**
- [ ] **Vibecoding Index accuracy r > 0.6**
- [ ] **Zero production incidents** caused by governance
- [ ] **CEO time baseline** established (current: 40h/week)
- [ ] **No auto-rollbacks** for >48 hours (stable thresholds)

### 2.2 Sprint 115 (SOFT Mode) Success Criteria ✅

- [ ] **CEO time reduced** from 40h → 25h (-37.5%)
- [ ] **False positive rate <10%**
- [ ] **Complaint rate <5%**
- [ ] **Medium/high violations blocked** successfully
- [ ] **Developer feedback positive** (>70% satisfaction)
- [ ] **Thresholds tuned** based on metrics
- [ ] **Zero critical incidents** from blocking

### 2.3 Technical Prerequisites ✅

#### Backend Services
- [ ] `governance-mode-service` healthy (3/3 replicas)
- [ ] `kill-switch-service` healthy (3/3 replicas)
- [ ] `vibecoding-index-service` healthy (3/3 replicas)
- [ ] `metrics-collector-service` healthy (2/2 replicas)
- [ ] `auto-generation-service` healthy (3/3 replicas)
- [ ] `stage-gating-service` healthy (2/2 replicas)

#### Databases
- [ ] PostgreSQL primary healthy (CPU <70%, disk <80%)
- [ ] PostgreSQL replica lag <5 seconds
- [ ] Redis cluster healthy (3/3 nodes)
- [ ] Database backups completed within 24 hours

#### External Dependencies
- [ ] GitHub API rate limit >1000 requests/hour
- [ ] OPA service healthy (policy evaluation <10ms)
- [ ] MinIO service healthy (object storage accessible)
- [ ] Slack webhook operational (test message sent)

#### Frontend Deployment
- [ ] Governance dashboard deployed (`/app/governance`)
- [ ] Kill switch admin deployed (`/app/governance/kill-switch`)
- [ ] CEO dashboard deployed (`/app/ceo-dashboard`)
- [ ] E2E tests passing (110/110 tests green)
- [ ] Build size <150 KB per page

#### Monitoring & Alerting
- [ ] Grafana dashboards configured (4 panels)
- [ ] Prometheus metrics scraping (5-second interval)
- [ ] PagerDuty integration tested
- [ ] Slack #governance-alerts channel active
- [ ] Email alerts to CTO/CEO configured

---

## 3. Deployment Steps

### Phase 1: Pre-Production Validation (30 minutes)

#### Step 1.1: Verify Staging Environment
```bash
# SSH to staging server
ssh staging.sdlc-orchestrator.dev

# Check governance mode
curl http://localhost:8000/api/v1/governance/mode
# Expected: {"mode": "SOFT", "health": "GREEN"}

# Run health checks
make health-check
# Expected: All services GREEN

# Check database migrations
alembic current
# Expected: Latest migration applied

# Verify Redis connection
redis-cli -h localhost -p 6379 ping
# Expected: PONG
```

#### Step 1.2: Run Smoke Tests
```bash
# Run E2E test suite on staging
cd frontend && npm run test:e2e:staging

# Expected output:
# ✓ 110 tests passing
# ✓ 0 tests failing
# Duration: ~5 minutes

# Test mode transition
curl -X POST http://localhost:8000/api/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -d '{"mode": "WARNING", "reason": "Smoke test"}'

# Verify rollback works
# Expected: Mode changes to WARNING, audit log entry created
```

#### Step 1.3: Backup Production Database
```bash
# Create production backup
pg_dump -h prod-db.sdlc-orchestrator.dev \
        -U postgres \
        -d sdlc_orchestrator \
        -F c \
        -f ~/backups/pre_sprint116_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
ls -lh ~/backups/
# Expected: File size >100 MB, timestamp today

# Upload to S3
aws s3 cp ~/backups/pre_sprint116_*.dump \
          s3://sdlc-orchestrator-backups/governance/
```

---

### Phase 2: Production Deployment (90 minutes)

#### Step 2.1: Deploy Backend Services (30 minutes)

```bash
# Set deployment context
export ENVIRONMENT=production
export NAMESPACE=sdlc-orchestrator

# Pull latest Docker images
docker pull ghcr.io/minh-tam-solution/sdlc-orchestrator:v6.0.5

# Update Kubernetes deployments
kubectl set image deployment/governance-service \
  governance-service=ghcr.io/minh-tam-solution/sdlc-orchestrator:v6.0.5 \
  -n $NAMESPACE

# Watch rollout status
kubectl rollout status deployment/governance-service -n $NAMESPACE
# Expected: "deployment successfully rolled out"

# Verify pods healthy
kubectl get pods -n $NAMESPACE | grep governance
# Expected: 3/3 Running, Ready 3/3

# Check logs for errors
kubectl logs -f deployment/governance-service -n $NAMESPACE --tail=50
# Expected: No ERROR or CRITICAL logs
```

#### Step 2.2: Run Database Migrations (10 minutes)

```bash
# SSH to production app server
ssh prod-app.sdlc-orchestrator.dev

# Run migrations (dry-run first)
cd /opt/sdlc-orchestrator/backend
alembic upgrade head --sql > migration.sql

# Review SQL
cat migration.sql
# Expected: CREATE TABLE, CREATE INDEX, ALTER TABLE statements

# Apply migrations
alembic upgrade head
# Expected: "Running upgrade ... OK"

# Verify schema version
alembic current
# Expected: v6.0.5 (head)
```

#### Step 2.3: Deploy Frontend (20 minutes)

```bash
# Build production frontend
cd frontend
npm run build

# Expected output:
# ✓ Build completed
# ✓ Static pages generated
# ✓ Bundle size: ~130 KB

# Deploy to CDN
aws s3 sync out/ s3://sdlc-orchestrator-frontend-prod/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"

# Verify deployment
curl https://sdlc-orchestrator.dev/app/governance
# Expected: HTTP 200, page loads
```

#### Step 2.4: Update Configuration (15 minutes)

```bash
# Update governance_rules.yaml
kubectl create configmap governance-rules \
  --from-file=backend/config/governance_rules.yaml \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify configmap
kubectl get configmap governance-rules -n $NAMESPACE -o yaml
# Expected: mode: "SOFT" (will change to FULL in Phase 3)

# Restart services to pick up new config
kubectl rollout restart deployment/governance-service -n $NAMESPACE

# Wait for rollout
kubectl rollout status deployment/governance-service -n $NAMESPACE
```

#### Step 2.5: Warm Up Caches (15 minutes)

```bash
# Pre-warm Redis cache with common queries
redis-cli -h prod-redis.sdlc-orchestrator.dev <<EOF
# Load CODEOWNERS
SET codeowners:cache "$(cat .github/CODEOWNERS)"

# Load ADR index
SET adr:index:cache "$(find docs/02-design/03-ADRs -name '*.md')"

# Load recent PRs
SET recent_prs:cache "$(gh pr list --limit 100 --json number,title)"
EOF

# Warm up Vibecoding Index calculator
for i in {1..50}; do
  curl http://localhost:8000/api/v1/vibecoding-index/calculate \
    -H "Authorization: Bearer $SYSTEM_TOKEN" \
    -d "{\"pr_number\": $i}"
  sleep 0.1
done

# Expected: <50ms response time after warmup
```

---

### Phase 3: Mode Transition to FULL (30 minutes)

#### Step 3.1: Enable WARNING Mode (5 minutes)

```bash
# Set mode to WARNING first (gradual rollout)
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "WARNING",
    "reason": "Sprint 116 deployment - gradual rollout to FULL",
    "actor": "CTO"
  }'

# Verify mode change
curl https://api.sdlc-orchestrator.dev/v1/governance/mode
# Expected: {"mode": "WARNING", "health": "GREEN"}

# Monitor for 10 minutes
watch -n 5 'curl -s https://api.sdlc-orchestrator.dev/v1/metrics/snapshot'
# Expected: No auto-rollbacks, health GREEN
```

#### Step 3.2: Enable SOFT Mode (10 minutes)

```bash
# Transition to SOFT mode
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "SOFT",
    "reason": "Sprint 116 - intermediate step to FULL",
    "actor": "CTO"
  }'

# Monitor metrics dashboard
open https://sdlc-orchestrator.dev/governance/metrics

# Watch for:
# - Rejection rate: Should be <5%
# - Latency P95: Should be <100ms
# - False positive rate: Should be <10%
# - Complaint rate: Should be <3%

# If any metric breaches threshold, auto-rollback will trigger
```

#### Step 3.3: Enable FULL Mode (15 minutes)

```bash
# Final transition to FULL enforcement
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "FULL",
    "reason": "Sprint 116 complete - full enforcement enabled",
    "actor": "CTO",
    "confirm": true
  }'

# Verify FULL mode active
curl https://api.sdlc-orchestrator.dev/v1/governance/mode
# Expected: {
#   "mode": "FULL",
#   "health": "GREEN",
#   "auto_approve_threshold": 30,
#   "active_since": "2026-02-21T10:00:00Z"
# }

# Send announcement to Slack
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "#engineering",
    "text": "🎉 Governance System FULL mode is now active! PRs with Vibecoding Index <30 (Green) will auto-approve. Medium/high complexity PRs route to CEO for review.",
    "attachments": [{
      "color": "good",
      "text": "Documentation: https://docs.sdlc-orchestrator.dev/governance/full-mode"
    }]
  }'
```

---

## 4. Post-Deployment Validation

### 4.1 Functional Tests (30 minutes)

#### Test 1: Green PR Auto-Approve
```bash
# Create test PR with index <30
gh pr create \
  --title "test: Update README.md documentation" \
  --body "WHY: Clarify installation steps\nWHAT: Add prerequisites section" \
  --head test-green-pr

# Expected:
# - Vibecoding Index calculated: ~15 (Green)
# - PR auto-approved within 30 seconds
# - CEO dashboard shows "Auto-approved (Green)"
```

#### Test 2: Yellow PR Standard Review
```bash
# Create test PR with index 31-60
gh pr create \
  --title "feat: Add user profile page" \
  --body "WHY: Users need profile management\nWHAT: New profile page with 8 components" \
  --head test-yellow-pr

# Expected:
# - Vibecoding Index calculated: ~45 (Yellow)
# - PR routed to CEO dashboard for review
# - Notification sent to CEO
```

#### Test 3: Red PR Blocked
```bash
# Create test PR with index >80
gh pr create \
  --title "refactor: Complete backend restructure" \
  --body "Refactored entire backend" \
  --head test-red-pr

# Expected:
# - Vibecoding Index calculated: ~85 (Red)
# - PR blocked with error message
# - Suggested fixes displayed in PR comment
# - Developer notified via GitHub + Slack
```

#### Test 4: Break Glass Activation
```bash
# Simulate P0 incident
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/break-glass \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "P0",
    "reason": "Production outage - need immediate hotfix",
    "pr_number": 999
  }'

# Expected:
# - Mode changes to OFF immediately
# - 4-hour countdown timer starts
# - Slack alert to #governance-alerts
# - PagerDuty alert to on-call engineer
# - Audit log entry created
```

### 4.2 Performance Validation (30 minutes)

```bash
# Test 1: Latency P95 <100ms
ab -n 1000 -c 10 https://api.sdlc-orchestrator.dev/v1/vibecoding-index/calculate
# Expected: P95 <100ms, P99 <200ms

# Test 2: Database query performance
psql -h prod-db.sdlc-orchestrator.dev -U postgres -d sdlc_orchestrator -c "
EXPLAIN ANALYZE SELECT * FROM governance_metrics_hourly 
WHERE metric_hour > NOW() - INTERVAL '7 days' 
ORDER BY metric_hour DESC;
"
# Expected: Execution time <50ms

# Test 3: Redis cache hit rate
redis-cli -h prod-redis.sdlc-orchestrator.dev INFO stats | grep keyspace_hits
# Expected: Hit rate >95%

# Test 4: CPU/memory usage
kubectl top pods -n sdlc-orchestrator
# Expected: CPU <70%, Memory <80%
```

---

## 5. Monitoring & Alerting Setup

### 5.1 Grafana Dashboards

**Dashboard URL:** https://grafana.sdlc-orchestrator.dev/d/governance

**Panels to monitor:**
1. **Rollback Risk Gauge:** Should be <30 (Green zone)
2. **Metrics Trends (24h):** All 4 metrics within target
3. **Time Savings Tracker:** CEO time trending toward 10h/week
4. **Mode History Timeline:** No unexpected rollbacks

**Alert Rules:**
```yaml
# Grafana alert rules
alerts:
  - name: "High Rollback Risk"
    condition: "rollback_risk_score > 70"
    for: "5m"
    severity: "warning"
    notification: "slack"
    
  - name: "Health Status RED"
    condition: "health_status == 'RED'"
    for: "2m"
    severity: "critical"
    notification: "pagerduty"
    
  - name: "False Positive Rate High"
    condition: "false_positive_rate > 15"
    for: "10m"
    severity: "warning"
    notification: "email_cto"
```

### 5.2 Log Monitoring

```bash
# Tail production logs
kubectl logs -f deployment/governance-service -n sdlc-orchestrator | grep -E "ERROR|CRITICAL"

# Expected: No errors in first 1 hour

# Check for common issues
kubectl logs deployment/governance-service -n sdlc-orchestrator | grep "rollback triggered"
# Expected: 0 occurrences

# Monitor Slack notifications
# Channel: #governance-alerts
# Expected: Mode change announcement, no error alerts
```

---

## 6. Rollback Procedures

### 6.1 Emergency Rollback (< 5 minutes)

**Trigger:** Critical production incident caused by governance system

```bash
# IMMEDIATE: Change mode to OFF
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "OFF",
    "reason": "EMERGENCY ROLLBACK: Production incident #{incident_id}",
    "actor": "CTO"
  }'

# Verify mode OFF
curl https://api.sdlc-orchestrator.dev/v1/governance/mode
# Expected: {"mode": "OFF"}

# Notify team
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -d '{
    "channel": "#engineering",
    "text": "🚨 GOVERNANCE EMERGENCY ROLLBACK: Mode set to OFF. All PRs will pass without checks. Incident: #{incident_id}"
  }'

# Create incident ticket
gh issue create \
  --title "INCIDENT: Governance emergency rollback" \
  --body "Mode: FULL → OFF\nReason: {reason}\nTime: $(date)\nDuration: TBD" \
  --label "P0,governance"
```

### 6.2 Gradual Rollback (30 minutes)

**Trigger:** High rollback risk score (>70) or increasing false positives

```bash
# Step down mode: FULL → SOFT
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -d '{"mode": "SOFT", "reason": "High false positive rate, stepping down to SOFT"}'

# Monitor for 15 minutes
# If metrics improve, stay in SOFT
# If metrics worsen, continue to WARNING

# Step down to WARNING if needed
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -d '{"mode": "WARNING", "reason": "Continuing rollback to WARNING for investigation"}'
```

### 6.3 Code Rollback (60 minutes)

**Trigger:** Service instability, cannot fix forward

```bash
# Rollback Kubernetes deployment
kubectl rollout undo deployment/governance-service -n sdlc-orchestrator

# Verify pods running previous version
kubectl get pods -n sdlc-orchestrator -o jsonpath='{.items[*].spec.containers[*].image}'
# Expected: v5.3.0 (previous version)

# Rollback database migrations
cd /opt/sdlc-orchestrator/backend
alembic downgrade -1

# Verify schema version
alembic current
# Expected: v5.3.0

# Rollback frontend
aws s3 sync s3://sdlc-orchestrator-frontend-backup/v5.3.0/ \
             s3://sdlc-orchestrator-frontend-prod/ \
             --delete

# Clear CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

---

## 7. Success Criteria

### 7.1 Deployment Success (24 hours post-deployment)

- [ ] **FULL mode stable:** No auto-rollbacks for 24 hours
- [ ] **Health status GREEN:** All 4 metrics within target
- [ ] **Green PRs auto-approving:** >20 auto-approved PRs in 24h
- [ ] **CEO time savings:** Trending toward 10h/week target
- [ ] **Zero critical incidents:** No P0/P1 issues from governance
- [ ] **False positive rate <10%:** Developer feedback positive
- [ ] **Latency P95 <100ms:** Performance within SLA
- [ ] **Complaint rate <3%:** Minimal developer friction

### 7.2 Long-Term Success (7 days post-deployment)

- [ ] **CEO time target achieved:** 40h → 10h (-75%)
- [ ] **Developer satisfaction >80%:** Survey results positive
- [ ] **Green auto-approve rate >30%:** 30%+ of PRs skip CEO review
- [ ] **No mode changes:** FULL mode stable for 7 days
- [ ] **Documentation complete:** All runbooks, guides published
- [ ] **Support tickets <5/week:** Minimal support burden

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Issue 1: High False Positive Rate
```bash
# Symptom: FP rate >15%, developers complaining
# Root Cause: Vibecoding Index thresholds too strict

# Solution: Tune index weights
vi backend/config/governance_rules.yaml
# Adjust signal weights (ownership: 0.25 → 0.20)

# Restart services
kubectl rollout restart deployment/governance-service -n sdlc-orchestrator

# Monitor FP rate
watch -n 60 'curl -s https://api.sdlc-orchestrator.dev/v1/metrics/snapshot | jq .false_positive_rate_current'
```

#### Issue 2: Latency P95 >100ms
```bash
# Symptom: Governance checks timing out
# Root Cause: Database slow queries or external API timeouts

# Check slow queries
psql -h prod-db.sdlc-orchestrator.dev -U postgres -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
WHERE mean_exec_time > 50 
ORDER BY mean_exec_time DESC 
LIMIT 10;"

# Add missing indexes
CREATE INDEX CONCURRENTLY idx_pr_reviews_created 
ON pr_reviews(created_at DESC);

# Check external API latency
curl -w "@curl-format.txt" https://api.github.com/rate_limit
# If >500ms, increase timeout or add caching
```

#### Issue 3: Auto-Rollback Loop
```bash
# Symptom: Mode keeps auto-rolling back (FULL → SOFT → WARNING → FULL)
# Root Cause: Thresholds too sensitive or metrics oscillating

# Increase cooldown period
vi backend/config/governance_rules.yaml
# auto_rollback.cooldown_period_minutes: 60 → 120

# Widen threshold bands
# rejection_rate.threshold_percent: 5.0 → 7.0

# Apply config
kubectl rollout restart deployment/governance-service -n sdlc-orchestrator
```

---

## 9. Contact Information

**Incident Response:**
- **PagerDuty:** https://mintamsolution.pagerduty.com/incidents
- **Slack:** #governance-incidents
- **On-Call:** `pagerduty schedule show governance-oncall`

**Escalation:**
- **CTO:** cto@sdlc-orchestrator.dev
- **CEO:** ceo@sdlc-orchestrator.dev
- **DevOps Lead:** devops@sdlc-orchestrator.dev

**Support:**
- **Slack:** #governance-support
- **Email:** support@sdlc-orchestrator.dev
- **Status Page:** https://status.sdlc-orchestrator.dev

---

**Runbook Version:** 1.0.0  
**Last Updated:** January 28, 2026  
**Next Review:** February 28, 2026  
**Owner:** CTO  
**Approved By:** CEO, CTO, DevOps Lead
