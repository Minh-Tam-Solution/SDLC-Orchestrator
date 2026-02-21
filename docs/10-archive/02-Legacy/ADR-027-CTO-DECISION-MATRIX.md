# System Settings Mock Violation - CTO Decision Matrix

**Status**: 🔴 **CRITICAL - Awaiting Approval**  
**Discovered**: 2026-01-14  
**Issue**: All 8 system settings are mock (violates SDLC 6.1.0 Zero Mock Policy)

---

## Quick Decision Matrix

### The Problem
| What | Why Critical |
|------|--------------|
| **8/8 settings are mock** | Admin changes have zero effect - database only |
| **Framework violation** | SDLC Orchestrator violates its own Zero Mock Policy |
| **Security risk** | MFA/lockout/session settings don't work but appear to |
| **Credibility risk** | Cannot enforce SDLC 6.1.0 on teams while violating it |

---

## Proposed Solution: 3-Phase Implementation

| Phase | Settings | Priority | Timeline | Risk |
|-------|----------|----------|----------|------|
| **Phase 1** | 4 security settings | 🔴 P0 | 2 weeks | LOW |
| **Phase 2** | 3 resource limits | 🟡 P1 | 2 weeks | LOW |
| **Phase 3** | 1 lifecycle setting | 🟢 P2 | 2 weeks | MEDIUM |

### Phase 1: Critical Security (Week 1-2) 🔴
```
✅ session_timeout_minutes    → Replace env var with DB value
✅ max_login_attempts          → Add account lockout middleware  
✅ mfa_required                → Enforce MFA when flag = true
✅ password_min_length         → Add validation in user endpoints
```

**Impact**: Immediate security posture improvement

### Phase 2: Resource Limits (Week 3-4) 🟡
```
✅ max_projects_per_user       → Validate in project creation
✅ max_file_size_mb            → Add upload size check
✅ ai_council_enabled          → Gate AI Council calls
```

**Impact**: Platform resource control

### Phase 3: Lifecycle (Week 5-6) 🟢
```
✅ evidence_retention_days     → Background job + cold storage
```

**Impact**: Data governance compliance (complex, needs architecture)

---

## CTO Decision Points

### 1️⃣ Approve Phased Approach?
- ✅ **YES**: Implement in 3 phases (security first, low risk)
- ❌ **NO**: (Alternative: remove all settings, or implement all at once)

### 2️⃣ Approve Phase 1 Scope?
- ✅ **YES**: 4 security settings in Sprint N+1 (2 weeks)
- ✅ **MODIFY**: Different settings priority? (specify below)
- ❌ **NO**: Different approach needed

### 3️⃣ Approve Timeline?
- ✅ **YES**: 6 weeks total (2 weeks per phase)
- ✅ **MODIFY**: Faster? Slower? (specify)
- ❌ **NO**: Different schedule needed

### 4️⃣ API Key Management?
- ✅ **YES**: Defer to separate ADR-028 (keep scope clean)
- ❌ **NO**: Include in this effort

---

## Resource Requirements

**Phase 1 (Immediate)**:
- **Owner**: BE Lead (primary)
- **Support**: 1 BE developer (testing)
- **Timeline**: Sprint N+1 (Jan 27 - Feb 7, 2026)
- **Effort**: ~40 hours (2 weeks, 50% allocation)

**Total (All Phases)**:
- **Duration**: 6 weeks (3 sprints)
- **Effort**: ~100 hours
- **Team**: BE Lead + 1 BE developer

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing deployments | LOW | HIGH | Env var migration + 2-sprint deprecation |
| Security downgrade | LOW | HIGH | Hard limits + audit logs |
| Scope creep | MEDIUM | MEDIUM | Strict phase boundaries |
| Performance regression | LOW | LOW | Caching (5-min TTL) |

---

## Success Criteria

### Phase 1 Exit (Sprint N+1 End)
- [ ] Admin changes session timeout → new tokens use new duration ✅
- [ ] Admin sets max login attempts → accounts lock after N failures ✅
- [ ] Admin enables MFA required → all users must configure MFA ✅
- [ ] Admin sets password min → create user validates length ✅
- [ ] 100% test coverage for all Phase 1 settings
- [ ] Zero Mock Policy violations = 0 (for Phase 1 settings)

### Final Success (After Phase 3)
- [ ] 8/8 settings fully functional
- [ ] SDLC Orchestrator complies with SDLC 6.1.0
- [ ] Framework credibility restored
- [ ] Security posture demonstrably improved

---

## Recommended Action

**Approve Phase 1 immediately:**
- Critical security settings affecting all users
- Low implementation risk (well-scoped, tested)
- Restores framework credibility
- Unblocks future compliance work

**Decision needed by**: End of week (Fri Jan 17, 2026)  
**Start date**: Sprint N+1 kickoff (Mon Jan 27, 2026)

---

## Quick Comparison: Options

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Do Nothing** | Zero effort | Framework violation persists, security risk | ❌ Unacceptable |
| **Remove Settings** | Fast, honest | Breaks admin UI, loses extensibility | ❌ Band-aid |
| **All At Once** | Complete solution | High risk, 6-week block on other work | ❌ Too risky |
| **Phased (Proposed)** | Security-first, low risk, early value | Takes 6 weeks total | ✅ **Recommended** |

---

## CTO Signature

- [ ] ✅ **APPROVED** - Proceed with 3-phase plan as proposed
- [ ] ✅ **APPROVED WITH CHANGES** - (specify below)
- [ ] ❌ **REJECTED** - (reason below)

**Changes/Notes**:
```
[CTO feedback here]
```

**Signed**: ________________  
**Date**: ________________

---

**Next Steps After Approval**:
1. Create JIRA/Linear tickets for Phase 1 (4 settings × 2 stories each)
2. Schedule design review with BE team
3. Assign BE Lead as DRI (Directly Responsible Individual)
4. Add to Sprint N+1 planning

**Full Details**: See [ADR-027-System-Settings-Real-Implementation.md](ADR-027-System-Settings-Real-Implementation.md)
