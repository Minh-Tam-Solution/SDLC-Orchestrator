# Governance System Incident Response Runbook

**Document Type:** Incident Response Runbook  
**Sprint:** 116 - Full Enforcement (February 17-21, 2026)  
**Status:** PRODUCTION-READY  
**Owner:** CTO + On-Call Engineer  
**Last Updated:** January 28, 2026  
**Framework:** SDLC 6.0 Governance System  

---

## 1. Overview

This runbook provides step-by-step incident response procedures for Governance System issues. Follow these procedures when governance system causes production impact or blocks critical PRs.

**Incident Severity Levels:**
- **P0 (Critical):** Production outage, complete governance system down
- **P1 (High):** Degraded service, high false positive rate blocking work
- **P2 (Medium):** Performance issues, latency exceeding thresholds
- **P3 (Low):** Minor issues, cosmetic bugs, non-blocking problems

---

## 2. Incident Response Flow

```
┌─────────────────┐
│ Incident Detected│
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Assess Severity │──> P0: Immediate break glass
│  (P0/P1/P2/P3)  │──> P1: Mode rollback to SOFT
└────────┬────────┘──> P2: Investigate + tune
         │         └──> P3: Create ticket for later
         v
┌─────────────────┐
│ Engage Team     │──> P0/P1: Page on-call + CTO
│                 │──> P2: Notify Slack #governance-incidents
└────────┬────────┘──> P3: Email to governance team
         │
         v
┌─────────────────┐
│ Mitigate Impact │──> Break glass, mode rollback, or hotfix
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Root Cause      │──> Investigate logs, metrics, database
│ Analysis        │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Permanent Fix   │──> Code fix, config change, threshold tuning
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Post-Mortem     │──> Document learnings, action items
└─────────────────┘
```

---

## 3. P0 Incident Response (Critical - Production Outage)

**SLA:** Acknowledge within 5 minutes, mitigate within 15 minutes

### 3.1 Symptoms
- All PRs failing governance checks
- Governance API returning 500 errors
- Database connection failures
- Redis cluster down
- Complete CEO dashboard unavailable

### 3.2 Immediate Actions (First 5 Minutes)

#### Step 1: Acknowledge Incident
```bash
# Create incident in PagerDuty
pd incident create \
  --title "P0: Governance System Down" \
  --service governance-system \
  --urgency high

# Post to Slack
slack send --channel "#governance-incidents" \
  --text "🚨 P0 INCIDENT: Governance system down. On-call responding."

# Update status page
curl -X POST https://api.statuspage.io/v1/pages/PAGE_ID/incidents \
  -H "Authorization: OAuth YOUR_TOKEN" \
  -d '{
    "incident": {
      "name": "Governance System Outage",
      "status": "investigating",
      "impact": "major"
    }
  }'
```

#### Step 2: Activate Break Glass (Bypass Governance)
```bash
# EMERGENCY: Set mode to OFF immediately
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $EMERGENCY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "OFF",
    "reason": "P0 INCIDENT: Governance system outage - bypassing all checks",
    "actor": "OnCall-Engineer",
    "incident_id": "INC-12345"
  }'

# Verify governance bypassed
curl https://api.sdlc-orchestrator.dev/v1/governance/mode
# Expected: {"mode": "OFF", "reason": "P0 INCIDENT..."}

# Notify all developers
slack send --channel "#engineering" \
  --text "⚠️ Governance system temporarily disabled due to P0 incident. All PRs will pass without checks until resolved. Please exercise extra caution with PR reviews."
```

#### Step 3: Check System Health
```bash
# Check all services
kubectl get pods -n sdlc-orchestrator
# Look for: CrashLoopBackOff, Error, ImagePullBackOff

# Check service logs
kubectl logs -f deployment/governance-service -n sdlc-orchestrator --tail=100
# Look for: "ERROR", "CRITICAL", stack traces

# Check database connectivity
psql -h prod-db.sdlc-orchestrator.dev -U postgres -c "SELECT 1;"
# Expected: "1" (if connection works)

# Check Redis cluster
redis-cli -h prod-redis.sdlc-orchestrator.dev ping
# Expected: "PONG" (if Redis works)
```

### 3.3 Mitigation Actions (Minutes 5-15)

#### Scenario A: Service Crash Loop
```bash
# Symptom: Pods restarting continuously
kubectl describe pod governance-service-xyz -n sdlc-orchestrator
# Look for: "Liveness probe failed", "OOMKilled"

# Quick fix: Rollback to previous version
kubectl rollout undo deployment/governance-service -n sdlc-orchestrator

# Wait for rollout
kubectl rollout status deployment/governance-service -n sdlc-orchestrator

# Test health
curl https://api.sdlc-orchestrator.dev/healthz
# Expected: HTTP 200
```

#### Scenario B: Database Outage
```bash
# Symptom: "connection refused" or "too many connections"
psql -h prod-db.sdlc-orchestrator.dev -U postgres -c "
SELECT count(*) FROM pg_stat_activity;
SELECT max_connections FROM pg_settings WHERE name='max_connections';
"
# If count > max_connections, database overwhelmed

# Emergency fix: Kill idle connections
psql -h prod-db.sdlc-orchestrator.dev -U postgres -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
  AND state_change < NOW() - INTERVAL '5 minutes';
"

# Or restart PostgreSQL (if corrupted)
ssh db-server.sdlc-orchestrator.dev
sudo systemctl restart postgresql
```

#### Scenario C: Redis Cluster Down
```bash
# Symptom: "Could not connect to Redis"
redis-cli -h prod-redis.sdlc-orchestrator.dev ping
# Expected: No response or "LOADING"

# Check Redis cluster status
redis-cli -c -h prod-redis.sdlc-orchestrator.dev cluster info
# Look for: "cluster_state:fail"

# Emergency fix: Failover to backup Redis
kubectl patch deployment governance-service -n sdlc-orchestrator \
  --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/env/0/value", "value":"backup-redis.sdlc-orchestrator.dev"}]'

# Or disable Redis caching temporarily
kubectl set env deployment/governance-service \
  REDIS_ENABLED=false \
  -n sdlc-orchestrator
```

### 3.4 Communication Template

**Slack #engineering:**
```
🚨 P0 INCIDENT UPDATE (15 minutes)

Status: MITIGATED
Root Cause: [Database connection pool exhausted]
Impact: Governance system down for 15 minutes, all PRs bypassed
Current State: Governance mode set to OFF, system recovering
ETA to Resolution: 30 minutes (mode will return to FULL after testing)

Action Required:
- All PRs are auto-passing right now (governance OFF)
- Please have extra caution during PR reviews
- Do NOT merge high-risk PRs until governance restored

Next Update: 15 minutes

Incident Lead: @oncall-engineer
PagerDuty: INC-12345
```

---

## 4. P1 Incident Response (High - Service Degradation)

**SLA:** Acknowledge within 15 minutes, mitigate within 60 minutes

### 4.1 Symptoms
- High false positive rate (>20%) blocking legitimate PRs
- Latency P95 >200ms (twice threshold)
- Auto-rollback loop (mode changing every 5 minutes)
- Break glass used >5 times in 1 hour

### 4.2 Immediate Actions (First 15 Minutes)

#### Step 1: Assess Impact
```bash
# Check metrics dashboard
open https://grafana.sdlc-orchestrator.dev/d/governance

# Key metrics to check:
# - Rollback risk score: If >80, immediate rollback needed
# - False positive rate: If >20%, thresholds too strict
# - Latency P95: If >200ms, performance issue
# - Complaint rate: If >10%, developer friction high

# Check recent PRs blocked
curl https://api.sdlc-orchestrator.dev/v1/governance/audit-log?event_type=pr_blocked&limit=20

# Check break glass usage
curl https://api.sdlc-orchestrator.dev/v1/governance/break-glass?since=1h
```

#### Step 2: Rollback Governance Mode
```bash
# If false positive rate >20%, step down mode
curl -X POST https://api.sdlc-orchestrator.dev/v1/governance/mode \
  -H "Authorization: Bearer $CTO_TOKEN" \
  -d '{
    "mode": "SOFT",
    "reason": "P1: High false positive rate - stepping down to SOFT mode for investigation",
    "incident_id": "INC-12346"
  }'

# Monitor for 15 minutes
watch -n 30 'curl -s https://api.sdlc-orchestrator.dev/v1/metrics/snapshot | jq .'

# If metrics improve, stay in SOFT
# If metrics still bad, step down to WARNING
```

### 4.3 Root Cause Investigation

#### Common Cause 1: Vibecoding Index Miscalibrated
```bash
# Check index distribution
psql -h prod-db.sdlc-orchestrator.dev -U postgres -d sdlc_orchestrator -c "
SELECT 
  CASE 
    WHEN vibecoding_index < 30 THEN 'Green'
    WHEN vibecoding_index < 60 THEN 'Yellow'
    WHEN vibecoding_index < 80 THEN 'Orange'
    ELSE 'Red'
  END as zone,
  COUNT(*) as pr_count
FROM pr_reviews
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY zone;
"

# Expected distribution:
# Green: 30-40%
# Yellow: 40-50%
# Orange: 15-20%
# Red: 5-10%

# If Red >20%, index too strict, adjust weights
vi backend/config/governance_rules.yaml
# signals.ownership_signal.weight: 0.25 → 0.20
# signals.intent_signal.weight: 0.20 → 0.15
```

#### Common Cause 2: Security Scanner Timing Out
```bash
# Check security scan latency
kubectl logs deployment/security-scanner -n sdlc-orchestrator | grep "scan_duration"

# If >10 seconds, scanner overloaded
# Quick fix: Increase timeout
kubectl set env deployment/governance-service \
  SECURITY_SCAN_TIMEOUT_SECONDS=30 \
  -n sdlc-orchestrator

# Or disable security checks temporarily (P1 only)
vi backend/config/governance_rules.yaml
# blocking_rules.security_scan_failures.enabled: false
```

#### Common Cause 3: External API Rate Limited
```bash
# Check GitHub API rate limit
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/rate_limit

# If remaining <100, need to wait or use different token
# Mitigation: Increase cache TTL
kubectl set env deployment/governance-service \
  GITHUB_CACHE_TTL_SECONDS=600 \
  -n sdlc-orchestrator
```

### 4.4 Hotfix Deployment

```bash
# If code fix needed
git checkout -b hotfix/governance-false-positives
# Make fix
git commit -m "fix: Adjust Vibecoding Index weights to reduce false positives"
git push origin hotfix/governance-false-positives

# Deploy hotfix (bypass normal PR process)
docker build -t ghcr.io/minh-tam-solution/sdlc-orchestrator:hotfix-123 .
docker push ghcr.io/minh-tam-solution/sdlc-orchestrator:hotfix-123

kubectl set image deployment/governance-service \
  governance-service=ghcr.io/minh-tam-solution/sdlc-orchestrator:hotfix-123 \
  -n sdlc-orchestrator

# Monitor rollout
kubectl rollout status deployment/governance-service -n sdlc-orchestrator
```

---

## 5. P2 Incident Response (Medium - Performance Degradation)

**SLA:** Acknowledge within 30 minutes, mitigate within 4 hours

### 5.1 Symptoms
- Latency P95 100-200ms (above target but not critical)
- False positive rate 10-15% (elevated but manageable)
- Complaint rate 5-10% (some developer friction)
- Rollback risk score 50-70 (yellow zone)

### 5.2 Actions

#### Step 1: Gather Data
```bash
# Export metrics for last 24h
curl https://api.sdlc-orchestrator.dev/v1/metrics/hourly?hours=24 > metrics_24h.json

# Analyze trends
cat metrics_24h.json | jq '.[] | {hour: .metric_hour, latency: .avg_pr_latency_impact_percent, fp_rate: .false_positive_rate}'

# Identify spike time
cat metrics_24h.json | jq 'max_by(.false_positive_rate)'
```

#### Step 2: Tune Thresholds
```bash
# Adjust rollback thresholds to prevent unnecessary rollbacks
vi backend/config/governance_rules.yaml

# Before:
# auto_rollback.thresholds.false_positive_rate.threshold_percent: 10.0

# After:
# auto_rollback.thresholds.false_positive_rate.threshold_percent: 15.0

# Apply config
kubectl rollout restart deployment/governance-service -n sdlc-orchestrator
```

#### Step 3: Optimize Queries
```bash
# Check slow queries
psql -h prod-db.sdlc-orchestrator.dev -U postgres -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Add indexes if needed
psql -h prod-db.sdlc-orchestrator.dev -U postgres -d sdlc_orchestrator -c "
CREATE INDEX CONCURRENTLY idx_pr_reviews_vibecoding_index 
ON pr_reviews(vibecoding_index, created_at DESC);
"
```

---

## 6. Escalation Procedures

### 6.1 Escalation Path

**Level 1: On-Call Engineer** (First responder)
- Acknowledge incident
- Follow runbook procedures
- Escalate to Level 2 if unable to mitigate within SLA

**Level 2: CTO** (Technical leadership)
- Approve break glass / mode rollback
- Make architectural decisions
- Engage additional engineers if needed

**Level 3: CEO** (Executive decision)
- Approve emergency bypass of governance
- Make business continuity decisions
- Communicate with customers if needed

### 6.2 Escalation Triggers

**Escalate to CTO if:**
- Incident not mitigated within SLA
- Requires code changes beyond config tuning
- Break glass approval needed
- Customer impact (external users affected)

**Escalate to CEO if:**
- Governance system must be disabled for >4 hours
- Revenue impact or SLA breach
- Customer complaints about governance blocking critical work
- Media/public relations concern

---

## 7. Post-Incident Review

### 7.1 Post-Mortem Template

```markdown
# Post-Mortem: Governance System Incident INC-XXXXX

## Incident Summary
- **Date:** YYYY-MM-DD
- **Duration:** X hours Y minutes
- **Severity:** P0/P1/P2
- **Impact:** [Describe business/customer impact]
- **Root Cause:** [1-2 sentence summary]

## Timeline
- **HH:MM** - Incident detected (how?)
- **HH:MM** - On-call acknowledged
- **HH:MM** - Mitigation action taken (what?)
- **HH:MM** - Service restored
- **HH:MM** - Root cause identified
- **HH:MM** - Permanent fix deployed
- **HH:MM** - Incident closed

## Root Cause Analysis
[Detailed technical explanation]

## What Went Well
- [List things that worked well during response]

## What Went Wrong
- [List things that could have gone better]

## Action Items
- [ ] **[OWNER]** - [Action item with deadline]
- [ ] **[OWNER]** - [Action item with deadline]

## Lessons Learned
- [Key takeaways for future incidents]
```

### 7.2 Action Item Tracking

Create follow-up issues:
```bash
# Create GitHub issue for each action item
gh issue create \
  --title "Post-mortem action: Improve Vibecoding Index calibration" \
  --body "From incident INC-12345: Need to recalibrate index weights based on 1 week of production data" \
  --label "post-mortem,governance,p1" \
  --assignee @cto
```

---

## 8. Contact Information

**Incident Response Team:**
- **On-Call Engineer:** PagerDuty rotation
- **CTO:** cto@sdlc-orchestrator.dev (PagerDuty escalation)
- **CEO:** ceo@sdlc-orchestrator.dev (Level 3 escalation)

**Communication Channels:**
- **Slack:** #governance-incidents (incident updates)
- **PagerDuty:** https://mintamsolution.pagerduty.com
- **Status Page:** https://status.sdlc-orchestrator.dev

**External Dependencies:**
- **GitHub Support:** https://support.github.com (API issues)
- **AWS Support:** 1-800-xxx-xxxx (infrastructure issues)
- **Redis Labs:** support@redis.com (Redis cluster issues)

---

**Runbook Version:** 1.0.0  
**Last Updated:** January 28, 2026  
**Next Drill:** February 15, 2026 (Pre-Sprint 116)  
**Owner:** On-Call Rotation  
**Approved By:** CTO
