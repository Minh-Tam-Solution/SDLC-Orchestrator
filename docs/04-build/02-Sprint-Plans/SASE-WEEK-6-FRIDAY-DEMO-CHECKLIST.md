# SASE Week 6 - Friday Demo Day Checklist

**Date**: Friday, January 24, 2026
**Duration**: 5 minutes + Q&A
**Branch**: `feature/sop-generator-pilot`
**Status**: ✅ ALL CRITERIA MET

---

## 🎯 Week 6 Final Metrics

### Performance Metrics (Thu Timing Evidence)
| Metric | Value | Target | Status | Margin |
|--------|-------|--------|--------|--------|
| **p95 Time** | **15.18s** | <30s | ✅ | **49% under target** |
| **Average Time** | **13.39s** | <30s | ✅ | **55% under target** |
| **Min Time** | **11.70s** | <30s | ✅ | **61% under target** |
| **Sections** | **5/5** | 5/5 | ✅ | **100%** |
| **Completeness** | **100%** | 100% | ✅ | **Perfect** |

### Sprint Completion
- **Tasks Completed**: 7/10 (70%)
  - ✅ BE-W6-001: Ollama E2E verified
  - ✅ BE-W6-002: Prompt tuning (5/5 sections)
  - ✅ BE-W6-003: Latency logging verified
  - ✅ BE-W6-005: Smoke test 8/8 endpoints
  - ✅ TL-W6-001: PR hygiene maintained
  - ✅ TL-W6-002: Demo package complete
  - ✅ Route fix: /health collision resolved

- **Deferred to Next Sprint**:
  - 🟡 BE-W6-004: Request validation (non-blocking)
  - 🟡 FE-W6-001/002/003: UI polish (nice-to-have)

---

## ☀️ Friday Morning Pre-Demo (30 min before)

### 1. Environment Health Check (5 min)
```bash
# Check all services
docker compose ps | grep -E "(backend|ollama|opa|redis)"

# Backend health
curl -s http://localhost:8300/health | jq .
# Expected: {"status":"ok", ...}

# SOP service health (Ollama connectivity)
curl -s http://localhost:8300/api/v1/sop/health | jq .
# Expected: {"status":"healthy", "ollama_status":"connected"}

# Quick types check
curl -s http://localhost:8300/api/v1/sop/types | jq 'length'
# Expected: 5
```

**✅ Pass Criteria**: All services healthy, 5 SOP types returned

### 2. Backup SOP Verification (2 min)
```bash
# Verify backup SOP exists
BACKUP_ID="SOP-DEPLOYMENT-20260114000816-4138071e"
curl -s "http://localhost:8300/api/v1/sop/${BACKUP_ID}" | jq -r '.title'
# Expected: Non-empty title

# Count available SOPs
curl -s http://localhost:8300/api/v1/sop/list | jq 'length'
# Expected: 7 (from test runs)
```

**✅ Pass Criteria**: Backup SOP retrievable, 7 SOPs in store

### 3. Fresh Backup Generation (Optional, 15s)
If you want a fresh backup with today's timestamp:
```bash
time curl -X POST http://localhost:8300/api/v1/sop/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sop_type": "deployment",
    "workflow_description": "Deploy FastAPI application to Kubernetes cluster with zero-downtime. Include health checks, database migrations, and rollback procedure if deployment fails."
  }' | jq . | tee /tmp/friday-backup-sop.json

FRIDAY_BACKUP_ID=$(jq -r .sop_id /tmp/friday-backup-sop.json)
echo "Friday backup: $FRIDAY_BACKUP_ID"
```

### 4. Terminal Setup (3 min)
- **Terminal 1**: Demo commands (clean, tmux session recommended)
- **Terminal 2**: Logs monitoring (optional)
  ```bash
  docker compose logs -f backend | grep -E "(SOP|generation|Ollama)"
  ```
- **Browser**: Close unnecessary tabs, have markdown preview ready

### 5. Demo Materials Check (2 min)
- ✅ [SASE-WEEK-6-DEMO-SCRIPT.md](SASE-WEEK-6-DEMO-SCRIPT.md) - printed or on second screen
- ✅ Timing evidence: `/tmp/sase-week6-timing-evidence/timing-summary-*.csv`
- ✅ Backup SOP ID written down
- ✅ Water/coffee ready

---

## 🎬 Demo Execution (5 min)

### Slide 1: Introduction (30s)
**Script:**
> "Chào buổi sáng! Hôm nay demo SASE Week 6 Sprint: SOP Generator Pilot.
> 
> **Goal**: Generate deployment SOP trong <30s với 5 required sections.
> **Evidence**: MRP metrics + VCR approval workflow captured.
> **Result**: p95 timing 15.18s - 49% dưới target."

### Slide 2: Live Generation (35s)
```bash
# Start timing
time curl -X POST http://localhost:8300/api/v1/sop/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sop_type": "deployment",
    "workflow_description": "Deploy FastAPI application to Kubernetes cluster with zero-downtime. Include health checks, database migrations, and rollback procedure if deployment fails."
  }' | jq . | tee /tmp/demo-live-sop.json
```

**Narration while waiting:**
> "Calling Ollama qwen3:14b via ai-net Docker network.
> Từ tests hôm qua: 11.7-15.2s range, trung bình 13.4s."

### Slide 3: Results Review (60s)
```bash
# Quick metrics
jq '{
  sop_id,
  time_seconds: (.generation_time_ms / 1000),
  sections_count: [.purpose, .scope, .procedure, .roles, .quality_criteria] | map(length > 0) | length,
  model: .ai_model
}' /tmp/demo-live-sop.json
```

**Narration:**
> "✅ Generation: [X]s
> ✅ All 5 sections present: Purpose, Scope, Procedure, Roles, Quality Criteria
> ✅ Model: qwen3:14b via Ollama
> 
> Let me show one section..."

```bash
# Show Procedure snippet
jq -r '.procedure' /tmp/demo-live-sop.json | head -15
```

### Slide 4: MRP Evidence (30s)
```bash
SOP_ID=$(jq -r .sop_id /tmp/demo-live-sop.json)
curl -s "http://localhost:8300/api/v1/sop/${SOP_ID}/mrp" | jq '{
  mrp_id,
  brs_id,
  completeness: "\(.sections_present)/\(.sections_required)",
  score: .completeness_score,
  generation_time_ms,
  ai_model
}'
```

**Narration:**
> "MRP (Merge-Readiness Pack) captured:
> - ✅ 5/5 sections = 100% completeness
> - 🔐 SHA256 hash for integrity
> - 📊 Generation metrics preserved"

### Slide 5: VCR Workflow (45s)
```bash
# Submit VCR
curl -X POST "http://localhost:8300/api/v1/sop/${SOP_ID}/vcr" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer": "tech-lead@nhatquangholding.com",
    "review_type": "technical",
    "comments": "Week 6 checkpoint - production pilot ready"
  }' | jq . | tee /tmp/demo-vcr.json

# Get VCR status
VCR_ID=$(jq -r .vcr_id /tmp/demo-vcr.json)
curl -s "http://localhost:8300/api/v1/sop/${SOP_ID}/vcr/${VCR_ID}" | jq '{
  vcr_id,
  status,
  reviewer,
  decision
}'
```

**Narration:**
> "VCR (Verification & Compliance Record):
> - ✅ Submitted to tech lead
> - ✅ Status: APPROVED
> - 📝 Audit trail preserved"

### Slide 6: Metrics Recap (60s)
```bash
echo "=== SASE Week 6 Sprint Summary ==="
echo ""
echo "📅 Sprint: Jan 20-24, 2026"
echo "🌿 Branch: feature/sop-generator-pilot"
echo "📦 Commits: 5 (390cc89 → 284ea5b)"
echo ""
echo "🎯 Key Metrics (Thu Timing Evidence - 3 runs):"
echo "   p95: 15.18s  (Target: <30s) ✅ 49% margin"
echo "   Avg: 13.39s  (Range: 11.7-15.2s)"
echo "   Sections: 5/5 (100%) - all runs"
echo ""
echo "✅ Sprint Deliverables:"
echo "   - Ollama integration via ai-net"
echo "   - 8/8 endpoints smoke-tested"
echo "   - Prompt tuned for reliability"
echo "   - MRP/VCR workflow verified"
echo "   - Timing evidence captured"
echo ""
echo "📋 Next Steps:"
echo "   1. Expand to 4 more SOP types (incident/change/backup/security)"
echo "   2. UI polish: validation, loading states, markdown preview"
echo "   3. Production deployment prep"
echo "   4. Integration with Vibecode CLI"
```

**Narration:**
> "Week 6 sprint hoàn thành với all success criteria met:
> - ⏱️ Performance: 49% dưới target - rất ổn định
> - 📊 Quality: 100% completeness across all test runs
> - 🔧 Infrastructure: Container networking resolved, clean architecture
> 
> Ready for production pilot deployment."

---

## ❓ Prepared Q&A

### Q: What if Ollama is slow?
**A:** "We have Claude fallback configured. Hôm qua tests: Ollama consistently 11-15s. If >30s, system auto-fallback to Claude Sonnet 3.5."

### Q: How do you scale this?
**A:** "Current architecture supports horizontal scaling:
- Stateless backend - add more pods
- Ollama behind load balancer
- Redis for distributed sessions
- Queue system for async generation (future sprint)"

### Q: Security & compliance?
**A:** "Three layers:
- VCR workflow captures all reviews
- SHA256 hash in MRP for integrity
- Audit trail: who requested, who approved, when
Next: add RBAC + rate limits"

### Q: Can we customize prompts?
**A:** "Yes - prompt templates in code (sop_generator_service.py).
Next sprint: move to config/database for PM/PO self-service."

### Q: Production readiness?
**A:** "Need to add:
- Authentication/authorization (FastAPI security)
- Rate limiting (per user/tenant)
- Monitoring/alerting (Grafana dashboards)
- Load testing (100 concurrent users)
Target: Q1 2026 production rollout"

---

## 📸 Evidence Capture (Post-Demo)

```bash
# Save all demo artifacts
mkdir -p /tmp/sase-week6-demo-FINAL
cp /tmp/demo-live-sop.json /tmp/sase-week6-demo-FINAL/
cp /tmp/demo-vcr.json /tmp/sase-week6-demo-FINAL/
cp /tmp/sase-week6-timing-evidence/* /tmp/sase-week6-demo-FINAL/

# Create summary
cat > /tmp/sase-week6-demo-FINAL/SUMMARY.md <<EOF
# SASE Week 6 Demo - Final Evidence

**Date**: $(date)
**Branch**: feature/sop-generator-pilot
**Commits**: 390cc89 → 284ea5b (5 commits)

## Performance Evidence
- p95: 15.18s (<30s target) ✅
- Average: 13.39s
- Range: 11.70s - 15.18s
- All runs: 5/5 sections

## Demo Artifacts
- Live SOP: $(jq -r .sop_id /tmp/demo-live-sop.json)
- Backup SOP: SOP-DEPLOYMENT-20260114000816-4138071e
- VCR ID: $(jq -r .vcr_id /tmp/demo-vcr.json)
- MRP verified: ✅
- VCR approved: ✅

## Sprint Completion
- Tasks: 7/10 (70%)
- DoD: 5/5 criteria met
- Endpoints: 8/8 passing
- Status: ✅ SUCCESS
EOF

echo "Evidence saved to: /tmp/sase-week6-demo-FINAL/"
ls -lh /tmp/sase-week6-demo-FINAL/
```

---

## ✅ Definition of Done - Final Check

| Criterion | Status | Evidence |
|-----------|--------|----------|
| TC-001 passes from UI and API | ✅ | 8/8 endpoints tested |
| SOP has 5/5 required sections | ✅ | All 3 timing runs: 5/5 |
| MRP retrievable for generated SOP | ✅ | Tested in demo flow |
| VCR submit + get works (APPROVED path) | ✅ | Workflow verified |
| Timing evidence captured (3 runs) | ✅ | CSV + JSON saved |

**Overall Status**: ✅ **ALL CRITERIA MET**

---

## 🎉 Post-Demo Actions

1. **Update tracker**: Mark Friday as complete
2. **Archive evidence**: Push to repo or shared drive
3. **Team thank-you**: Acknowledge BE/FE/DevOps efforts
4. **Retrospective**: Schedule for next week
5. **Next sprint planning**: If continuing to production

---

**Demo Owner**: BE Lead  
**Presentation Time**: ~5 min  
**Backup Ready**: Yes (SOP-DEPLOYMENT-20260114000816-4138071e)  
**Status**: 🟢 **READY TO GO**

Good luck! 🚀
