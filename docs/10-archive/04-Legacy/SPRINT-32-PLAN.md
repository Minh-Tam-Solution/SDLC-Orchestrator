# Sprint 32: SDLC 6.1.0 Restructure & User API Key Management

**Sprint**: 32  
**Duration**: TBD (Post-Gate G3)  
**Status**: PLANNED  
**Framework**: SDLC 6.1.0
**Authority**: CTO + CPO Approved

---

## Executive Summary

Sprint 32 implements two major features:
1. **SDLC 6.1.0 Stage Restructuring** - Move INTEGRATE from Stage 07 → Stage 03
2. **User API Key Management (BYOK)** - Allow users to manage third-party AI provider keys

Both features approved by CTO/CPO with conditions. Implementation timeline: Post-Gate G3 (Sprint 32).

---

## Part 1: SDLC 6.1.0 Stage Restructuring

### Phase 0: Framework Documentation Update (2-3 hours)

**Deliverables**:
- Update SDLC-Enterprise-Framework documents
- Update docs/ stage references
- Batch update script

**Files to Update**:
- `SDLC-Enterprise-Framework/00-Overview/README.md`
- `SDLC-Enterprise-Framework/02-Core-Methodology/SDLC-Core-Methodology.md`
- `SDLC-Enterprise-Framework/02-Core-Methodology/SDLC-Tier-Classification.md`
- `docs/00-Project-Foundation/`
- `docs/01-Planning-Analysis/`
- `docs/02-Design-Architecture/`

---

### Phase 1: Migration Tool (1 day) ⚠️ MANDATORY

**Deliverable**: `sdlcctl migrate` command

**Functionality**:
- Detect old stage mapping
- Remap stages: 07-INTEGRATE → 03-integration
- Update `.sdlc-config.json`
- Generate migration report

**Success Criteria**:
- [ ] Migration tool functional
- [ ] Backward compatibility support (3 months)
- [ ] Migration guide created

---

### Phase 2: Onboarding Flow Updates (2-3 days)

**Web Dashboard**:
- Update stage selector
- Update TierSelection component
- Add visual diagram

**VS Code Extension**:
- Update `/init` command
- Generate restructured structure

---

## Part 2: User API Key Management (BYOK)

### Phase 1: Database & Backend (3-4 days)

**Deliverables**:
1. Database migration (`user_ai_providers` table)
2. Backend API endpoints (5 endpoints)
3. Encryption service (AES-256)
4. Validation service
5. Cost tracking integration

**Endpoints**:
- `GET /api/v1/users/me/ai-providers`
- `POST /api/v1/users/me/ai-providers`
- `POST /api/v1/users/me/ai-providers/{id}/validate`
- `PUT /api/v1/users/me/ai-providers/{id}`
- `DELETE /api/v1/users/me/ai-providers/{id}`

---

### Phase 2: Frontend Web (2-3 days)

**Deliverables**:
1. Settings page (`/settings/api-keys`)
2. ProviderCard component
3. ApiKeyInput component
4. ApiKeyValidator component
5. UsageStatistics component

---

### Phase 3: VS Code Extension (2 days)

**Deliverables**:
1. Command: `SDLC: Configure AI Provider`
2. Settings UI integration
3. Local + Server sync
4. Environment variable support

---

## Success Criteria

### SDLC Restructuring

- [ ] Migration tool functional
- [ ] All documentation updated
- [ ] Onboarding flows updated
- [ ] Backward compatibility working

### User API Key Management

- [ ] Database migration complete
- [ ] All API endpoints functional
- [ ] Encryption working (AES-256)
- [ ] Validation working
- [ ] Cost tracking implemented
- [ ] Web UI complete
- [ ] VS Code Extension complete

---

## Timeline

**Sprint 32** (Post-Gate G3):
- Week 1: SDLC Restructuring (Phase 0-1)
- Week 2: User API Key Management (Phase 1-2)
- Week 3: VS Code Extension + Testing

**Total Effort**: 10-12 days

---

## Risk Assessment

### High Risk: None ✅

### Medium Risk

| Risk | Mitigation | Owner |
|------|------------|-------|
| Breaking change | Migration tool + backward compatibility | Backend Lead |
| API key security | AES-256 encryption + audit trail | Security Lead |

---

## Approval

**CTO**: ✅ **APPROVED**  
**CPO**: ✅ **APPROVED**

**Status**: ✅ **APPROVED FOR SPRINT 32**

---

**Plan Created**: December 13, 2025  
**Next**: Sprint 32 kickoff (post-G3)

