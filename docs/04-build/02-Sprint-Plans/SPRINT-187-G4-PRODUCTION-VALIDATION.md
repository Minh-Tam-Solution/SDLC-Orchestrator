---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "187"
spec_id: "SPRINT-187"
tier: "ENTERPRISE"
stage: "04 - Build"
---

# SPRINT-187 — G4 Production Validation + Enterprise Beta

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 10 working days
**Sprint Goal**: Gate G4 "Production Ready" declaration + enroll 2-3 enterprise beta customers
**Epic**: ADR-059 Enterprise-First
**ADR**: ADR-059 (G4 gate criteria from SDLC 6.1.0)
**Dependencies**: Sprint 186 complete (multi-region + GDPR live)
**Budget**: ~$6,400 (80 hrs at $80/hr)

---

## 1. Sprint Goal

Sprint 187 is a **validation sprint** — no new features. All effort goes into:
1. **G4 Gate validation** — Verify all 8 G4 criteria meet threshold
2. **Performance validation** — Locust load test at 50K concurrent users
3. **Security validation** — External pen test (P0/P1 must be zero)
4. **Enterprise beta program** — Enroll 2-3 international enterprise customers

| Track | Priority | Days |
|-------|----------|------|
| G4 criteria verification (8 checks) | P0 | 3 |
| Locust load test (50K concurrent) | P0 | 2 |
| External pen test validation | P0 | 2 |
| Bug fixing (P0/P1 from pen test/load test) | P0 | 2 |
| Enterprise beta enrollment | P1 | 1 |
| **Total** | | **10** |

---

## 2. G4 Gate Criteria (Non-Negotiable)

All 8 criteria must pass before G4 is declared:

| # | Criterion | Target | Measurement |
|---|-----------|--------|-------------|
| G4-01 | Enterprise SSO | SAML + Azure AD tested with real IdP | Manual test with IT admin |
| G4-02 | Compliance | SOC2 evidence pack generated, legal reviewed | Legal sign-off document |
| G4-03 | Audit trail | 90-day immutable log tested | AT-02, AT-03 pass + manual trigger test |
| G4-04 | Multi-region | EU region live (MinIO EU bucket) | SR-04, SR-05 pass in production |
| G4-05 | Performance | p95 <100ms with 50K concurrent users | Locust report |
| G4-06 | Security | External pen test: P0/P1 = 0 | Pen test report |
| G4-07 | OTT channels | Telegram + Teams + Slack all operational | Manual end-to-end test |
| G4-08 | Tier enforcement | All 78 routes tier-gated correctly | TG-01..40 pass in production |

**G4 Declaration**: CTO + CPO both must sign G4 declaration document.

---

## 3. Daily Schedule

### Day 1-3: G4 Criteria Verification

**Day 1: SSO + OTT validation**:

1. SSO end-to-end test with real IdP:
   - Configure Okta SAML SP in test organization
   - Log in via SAML ACS endpoint
   - Verify JIT provisioning creates user
   - Verify role mapping works
   - Log out via SSO logout endpoint
   - Verify sso_sessions row deleted

2. Azure AD end-to-end test:
   - Create Azure App Registration in test tenant
   - Initiate PKCE flow from browser
   - Verify callback processes id_token
   - Verify user JIT provisioned
   - Verify state parameter CSRF protection

3. OTT channel end-to-end:
   - Send test message via Telegram bot → verify OrchestratorMessage created
   - Send test message via Teams bot → verify TeamsNormalizer processes
   - Send test message via Slack bot → verify HMAC verification works

**Day 2-3: Compliance + Audit validation**:

1. SOC2 evidence pack generation:
   - Create test project with 6 months of evidence
   - Run `soc2_pack_service.generate_evidence_pack()`
   - Verify PDF is valid (opens in PDF reader)
   - Send to legal for review (CC6.1, CC8.1 mapping accuracy)

2. Audit trail validation:
   - Verify gate approval writes to audit_logs
   - Verify SSO login writes to audit_logs
   - Attempt manual DELETE on audit_logs → verify PostgreSQL trigger blocks
   - Export 30-day audit log as CSV → verify completeness

3. Tier enforcement validation in production:
   - Test each tier (LITE/STANDARD/PROFESSIONAL/ENTERPRISE) against 5 key routes
   - Verify 402 response body format on all blocked routes

---

### Day 4-5: Locust Load Test

**Goal**: Verify p95 <100ms under 50K concurrent users

**Locust scenario** (`backend/tests/load/locustfile_g4.py`):
```python
from locust import HttpUser, task, between

class OrchestratorUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(40)
    def list_projects(self):
        self.client.get("/api/v1/projects", headers=self.auth_headers)

    @task(20)
    def list_gates(self):
        self.client.get("/api/v1/gates?project_id=1", headers=self.auth_headers)

    @task(20)
    def list_evidence(self):
        self.client.get("/api/v1/evidence?gate_id=1", headers=self.auth_headers)

    @task(10)
    def evaluate_gate(self):
        self.client.post(
            "/api/v1/gates/1/evaluate",
            json={"force_reevaluate": False},
            headers=self.auth_headers,
        )

    @task(10)
    def audit_log_query(self):
        self.client.get("/api/v1/enterprise/audit", headers=self.enterprise_headers)
```

**Load test parameters**:
```bash
# Ramp up to 50K users over 10 minutes
locust -f backend/tests/load/locustfile_g4.py \
  --host https://staging.sdlcorchestrator.com \
  --users 50000 \
  --spawn-rate 100 \
  --run-time 30m \
  --html reports/load_test_g4.html
```

**Pass criteria**:
- p95 API latency: <100ms for `list_projects`, `list_gates`, `list_evidence`
- p95 API latency: <500ms for `evaluate_gate` (OPA evaluation)
- p99 latency: <200ms for read endpoints
- Error rate: <0.1%
- Throughput: >5,000 req/s sustained

**Database tuning if p95 fails**:
- Add missing indexes (`EXPLAIN ANALYZE` on slow queries)
- PgBouncer pool size tuning
- Redis caching for frequently-accessed project/gate data

---

### Day 6-7: External Pen Test Validation

**Scope** (provided to external security firm):
- Authentication: JWT, OAuth, SSO flows
- Authorization: RBAC, tier gate middleware
- Evidence Vault: file upload/download integrity
- Multi-Agent API: message injection, shell guard
- OTT Gateway: input sanitization (12 injection patterns)
- Audit trail: immutability bypass attempts

**Pass criteria** (G4-06):
- P0 findings: 0 (critical vulnerabilities)
- P1 findings: 0 (high vulnerabilities)
- P2 findings: acceptable (documented, remediation plan)

**P0 definition** (must fix before G4):
- Authentication bypass
- Tier gate bypass (LITE accessing ENTERPRISE endpoints)
- SQL injection
- Credential leakage (OutputScrubber bypass)
- SSRF via Jira/OTT webhook endpoints

**If P0/P1 found**:
- Days 8-9 allocated for P0/P1 remediation
- Re-test specific findings after fix
- G4 declaration delayed if P0 found on Day 7

---

### Day 8-9: P0/P1 Bug Fixing Buffer

**Reserved for pen test findings**. If no P0/P1 bugs found (Day 7 clean), use this time for:
- Performance optimization from load test results
- Documentation updates
- Enterprise beta enrollment activities

---

### Day 9-10: Enterprise Beta Enrollment

**Goal**: Enroll 2-3 international enterprise customers in beta program

**Beta program terms**:
- 3-month ENTERPRISE tier free
- Weekly CSM calls (30 min)
- Priority P1 support (4h response)
- Feedback collected via Google Forms + monthly survey
- Customer agrees to anonymized case study

**Beta customer criteria**:
- 25+ developers
- Uses Jira or GitHub Projects
- Interest in SOC2 or NIST AI RMF compliance
- English-speaking (international, not Vietnam market)

**Enrollment activities**:
- Create ENTERPRISE tier accounts for 2-3 beta customers
- Configure SSO with their IdP (SAML or Azure AD)
- Configure Jira integration
- Deliver onboarding document (5-page quick start)
- Set up Teams or Slack bot in their workspace

---

## 4. G4 Declaration Document

To be signed by CTO + CPO after all criteria pass:

```markdown
# SDLC Orchestrator v2.0 — Gate G4 Production Ready Declaration

**Date**: [Sprint 187 completion date]
**Version**: 2.0.0

## Criteria Verification

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| G4-01 | Enterprise SSO | ✅ PASS | SAML tested with Okta; Azure AD PKCE tested |
| G4-02 | SOC2 compliance | ✅ PASS | PDF pack generated, legal reviewed |
| G4-03 | Audit trail | ✅ PASS | 90-day log exported, immutability confirmed |
| G4-04 | Multi-region | ✅ PASS | EU MinIO bucket live |
| G4-05 | Performance | ✅ PASS | p95 < 100ms at 50K concurrent |
| G4-06 | Security | ✅ PASS | External pen test: 0 P0, 0 P1 |
| G4-07 | OTT channels | ✅ PASS | Telegram, Teams, Slack all tested end-to-end |
| G4-08 | Tier enforcement | ✅ PASS | All 78 routes verified in production |

**CTO Sign-off**: _______________
**CPO Sign-off**: _______________
**Date**: _______________
```

---

## 5. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| All 8 G4 criteria pass | 8/8 | G4 declaration document signed |
| Load test p95 <100ms | Pass | Locust report |
| Pen test P0/P1 = 0 | 0 | External firm report |
| Beta customers enrolled | 2-3 | Confirmed accounts in ENTERPRISE tier |
| No new features shipped | 0 | Sprint is validation-only |

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| P0 security finding delays G4 | Medium | Critical | 2-day buffer (Day 8-9) for emergency fixes |
| p95 >100ms at 50K users | Medium | High | Day 4-5 diagnostic + index tuning; G4 delayed if not resolved |
| Legal review of SOC2 mapping takes >1 sprint | Medium | Medium | Engage legal firm at Sprint 185 start |
| No enterprise beta customers found | Low | Medium | CPO pipeline from Vietnam network + LinkedIn outbound |

---

## 7. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 186 complete | Prerequisite | Required |
| External security firm engaged | Vendor | Engage at Sprint 185 start |
| Legal firm for SOC2 review | Vendor | Engage at Sprint 185 start |
| Staging environment (production-equivalent) | Infrastructure | Must match production |
| 50K user load test infrastructure | Infrastructure | Locust distributed (5 workers) |

---

## 8. Definition of Done

- [ ] All 8 G4 criteria pass
- [ ] Locust load test report with p95 <100ms
- [ ] External pen test report: 0 P0/P1 findings
- [ ] G4 Declaration document signed by CTO + CPO
- [ ] 2-3 enterprise beta customers enrolled
- [ ] Any P0/P1 pen test findings remediated and re-tested
- [ ] SPRINT-187-CLOSE.md written
- [ ] Gate G4 officially APPROVED in platform (POST /api/v1/gates/{g4_gate_id}/approve)

---

**Approval Required**: CTO + CPO (for G4 declaration)
**Budget**: ~$6,400 (10 days × 8 hrs × $80/hr)
**Risk Level**: HIGH (G4 gate is strict; P0 pen test findings block launch)
