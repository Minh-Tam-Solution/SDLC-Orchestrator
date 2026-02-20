---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "182"
spec_id: "SPRINT-182"
tier: "ENTERPRISE"
stage: "04 - Build"
---

# SPRINT-182 — Enterprise SSO Design + Teams Channel

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 6 working days
**Sprint Goal**: Unblock first enterprise sales — design SSO architecture (ADR-061) + implement Microsoft Teams OTT channel
**Epic**: EP-07 Multi-Agent Team Engine + ADR-059 Enterprise-First
**ADR**: ADR-061 (Enterprise SSO Design — 5 locked decisions)
**Dependencies**: Sprint 181 complete (agent_bridge/ operational, protocol_adapter.py live)
**Budget**: ~$3,840 (48 hrs at $80/hr)

---

## 1. Sprint Goal

Two parallel tracks:
1. **ADR-061 SSO Architecture** — Lock 5 decisions that unblock Sprint 183 implementation (SAML 2.0, Azure AD PKCE, JIT, SCIM, ACS URL pattern)
2. **Teams Normalizer** — First enterprise OTT channel; enterprise pilots communicate via Microsoft Teams

| Deliverable | Priority | New LOC | Days |
|-------------|----------|---------|------|
| ADR-061 Enterprise SSO Architecture | P0 | ~300 doc | 1 |
| DB Schema: enterprise_sso_configs + sso_sessions (Alembic s182_001) | P0 | ~80 | 0.5 |
| teams_normalizer.py + tests (15 tests PA-21..35) | P0 | ~200 | 2 |
| ADR-062 Draft: Compliance Evidence Types | P1 | ~150 doc | 0.5 |
| Integration: ott_gateway.py recognizes "teams" channel | P1 | ~20 | 0.5 |
| Coverage + regression tests | -- | ~50 | 1.5 |
| **Total** | | **~800** | **6** |

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | ADR-061 | 5 locked SSO decisions (SAML, Azure AD PKCE, JIT, SCIM deferred, ACS URL) | New | Day 1 |
| 2 | s182_001 migration | `enterprise_sso_configs` + `sso_sessions` tables (ERD v3.5.0 aligned) | New | Day 2 |
| 3 | `teams_normalizer.py` | Teams Activity → OrchestratorMessage, Bot Framework HMAC JWT verification | New | Day 2-3 |
| 4 | `test_teams_normalizer.py` | PA-21 to PA-35 (15 tests: activity parse, HMAC verify, Adaptive Cards) | New | Day 3 |
| 5 | `ott_gateway.py` update | Register "teams" channel in route dispatcher | Modified | Day 3 |
| 6 | ADR-062 Draft | Compliance Evidence Types: SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF, ISO27001 | New | Day 4 |
| 7 | Regression: Sprint 181 tests | All PA-01..20 Telegram/Zalo tests still pass | -- | Day 5 |
| 8 | Coverage report | 95%+ for agent_bridge/ package | -- | Day 6 |

---

## 3. Daily Schedule

### Day 1: ADR-061 — Enterprise SSO Architecture Design

**Goal**: Lock 5 SSO decisions to unblock Sprint 183 implementation

**Tasks**:
1. Write `docs/02-design/01-ADRs/ADR-061-Enterprise-SSO.md`:
   - Decision 1: **Protocol selection** — SAML 2.0 SP-initiated + Azure AD OAuth 2.0 PKCE (NOT Okta SDK, NOT social OAuth)
   - Decision 2: **ACS URL pattern** — `https://{domain}/api/v1/enterprise/sso/{provider}/callback`
   - Decision 3: **JIT provisioning** — Auto-create user on first SSO login; map IdP groups → RBAC roles via `role_mapping` JSONB
   - Decision 4: **SCIM 2.0 deferred** — Evaluated but deferred until first enterprise customer explicitly requests it (Sprint 185+)
   - Decision 5: **Token storage** — NEVER store raw id_token; store SHA256 hash only in `sso_sessions.id_token_hash`
   - Alternatives considered: Okta SDK (rejected: vendor lock-in), LDAP (rejected: legacy, no cloud-native), Social OAuth only (rejected: not enterprise-grade)
   - Non-goals: SSO for LITE/STANDARD tiers (ENTERPRISE only); MFA via SSO IdP (delegate to IdP, don't re-implement)
   - Consequences: Sprint 183 can proceed with `python3-saml` (MIT) + `msal` (MIT)

2. Research: JWKS endpoint for Teams Bot Framework JWT verification
3. Design: ACS URL flow diagram (SP-initiated vs IdP-initiated)

**Verification**:
```bash
# ADR file exists
ls docs/02-design/01-ADRs/ADR-061-Enterprise-SSO.md
```

**Exit Criteria**: ADR-061 has all 5 decisions locked, no TBDs, CTO sign-off required

---

### Day 2: Alembic Migration + Teams Normalizer Foundation

**Goal**: Create DB schema for SSO + begin Teams normalizer implementation

**Tasks**:
1. Create `backend/alembic/versions/s182_001_enterprise_sso.py`:
   - Upgrade: creates `enterprise_sso_configs` (13 cols) + `sso_sessions` (7 cols)
   - Indices: `idx_sso_config_org` (unique org+provider), `idx_sso_sessions_user`, `idx_sso_sessions_expiry`
   - Downgrade: drops both tables
   - Naming standard: `s182_001` prefix per SDLC 6.1.0 migration naming

2. Begin `backend/app/services/agent_bridge/teams_normalizer.py`:
   - `TeamsNormalizer` class inheriting `BaseNormalizer` protocol
   - `verify_hmac(request_body: bytes, signature: str, secret: str) -> bool`
   - `parse_activity(raw_payload: dict) -> OrchestratorMessage`
   - Support Bot Framework Activity types: `message`, `invoke`, `conversationUpdate`
   - Bot Framework JWKS: `https://login.botframework.com/v1/.well-known/openidconfiguration`
   - JWT audience: `appId` from bot registration
   - Map Teams `channelId="msteams"`, `from.aadObjectId` as `sender_id`

**Teams Activity → OrchestratorMessage mapping**:
```python
OrchestratorMessage(
    channel="teams",
    sender_id=activity.get("from", {}).get("aadObjectId", ""),
    content=activity.get("text", ""),
    timestamp=activity.get("timestamp", ""),
    correlation_id=activity.get("id", ""),  # Bot Framework activity ID
    metadata={
        "conversation_id": activity.get("conversation", {}).get("id"),
        "tenant_id": activity.get("channelData", {}).get("tenant", {}).get("id"),
        "activity_type": activity.get("type"),
    }
)
```

**Verification**:
```bash
python -m pytest backend/tests/unit/test_teams_normalizer.py -v --collect-only
```

**Exit Criteria**: Migration created, Teams normalizer skeleton with parse + HMAC verify

---

### Day 3: Teams Normalizer Tests (PA-21 to PA-35)

**Goal**: 15 tests covering all Teams normalizer functionality

**Test Cases**:
```
PA-21: parse_activity extracts text content from Teams message activity
PA-22: parse_activity maps from.aadObjectId → OrchestratorMessage.sender_id
PA-23: parse_activity maps activity.id → OrchestratorMessage.correlation_id
PA-24: parse_activity sets channel="teams"
PA-25: parse_activity handles empty text (voice/card activities)
PA-26: parse_activity extracts tenant_id from channelData.tenant.id
PA-27: parse_activity handles conversationUpdate (member added/removed)
PA-28: parse_activity rejects unknown activity type (raises ValueError)
PA-29: verify_hmac returns True for valid Bot Framework signature
PA-30: verify_hmac returns False for tampered body
PA-31: verify_hmac returns False for wrong secret
PA-32: verify_hmac constant-time comparison (no timing oracle)
PA-33: Adaptive Card response format: attachment type = application/vnd.microsoft.card.adaptive
PA-34: ott_gateway.py routes "teams" channel to TeamsNormalizer
PA-35: TeamsNormalizer rejects non-Teams channelId (e.g., "slack")
```

**Adaptive Cards response format**:
```python
def build_adaptive_card_response(content: str) -> dict:
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.5",
                "body": [{"type": "TextBlock", "text": content, "wrap": True}]
            }
        }]
    }
```

**Verification**:
```bash
python -m pytest backend/tests/unit/test_teams_normalizer.py -v
```

**Exit Criteria**: All 15 PA-21..35 tests pass

---

### Day 4: ADR-062 Draft + OTT Gateway Integration

**Goal**: Draft compliance evidence types ADR + wire Teams into gateway

**Tasks**:
1. Write `docs/02-design/01-ADRs/ADR-062-Compliance-Evidence-Types.md` (DRAFT — finalized Sprint 183):
   - Problem: EvidenceType enum only has general types (DESIGN_DOCUMENT, TEST_RESULTS, CODE_REVIEW, etc.) — no compliance-specific types
   - Decision (DRAFT): Extend enum with: `SOC2_CONTROL`, `HIPAA_AUDIT`, `NIST_AI_RMF`, `ISO27001`
   - Impact: `backend/app/models/evidence.py` EvidenceType enum + Alembic migration `s183_002`
   - Non-goal: Don't add compliance-specific validation logic in Sprint 182 (Sprint 183 task)

2. Update `backend/app/api/routes/ott_gateway.py`:
   - Add "teams" to `SUPPORTED_CHANNELS` set
   - Import `TeamsNormalizer` from `agent_bridge.teams_normalizer`
   - Register in `CHANNEL_NORMALIZER_MAP: dict[str, BaseNormalizer]`

3. Write `backend/app/services/agent_bridge/teams_normalizer.py` final version:
   - `normalize()` top-level function (consistent with `telegram_normalizer.normalize()`)
   - Full type annotations
   - Docstrings per Google style

**Verification**:
```bash
python -m pytest backend/tests/unit/test_teams_normalizer.py \
  backend/tests/unit/test_protocol_adapter.py -v
```

**Exit Criteria**: Teams channel registered in gateway, ADR-062 draft committed

---

### Day 5: Regression Testing + Sprint 181 Verification

**Goal**: All Sprint 181 + Sprint 182 tests pass together

**Tasks**:
1. Run full Sprint 181 regression (PA-01..20):
   ```bash
   python -m pytest backend/tests/unit/test_protocol_adapter.py -v  # PA-01..20
   ```
2. Run Sprint 182 new tests (PA-21..35):
   ```bash
   python -m pytest backend/tests/unit/test_teams_normalizer.py -v
   ```
3. Verify Alembic migration runs cleanly:
   ```bash
   cd backend && alembic upgrade head
   alembic downgrade -1
   alembic upgrade head  # round-trip test
   ```
4. Fix any regressions found

**Verification**:
```bash
python -m pytest backend/tests/unit/ -k "protocol_adapter or teams_normalizer" -v
```

**Exit Criteria**: 35/35 OTT tests pass (PA-01..35), migration round-trip clean

---

### Day 6: Coverage + Documentation + Sprint Close

**Goal**: 95%+ coverage for agent_bridge/ + sprint close documentation

**Tasks**:
1. Run coverage for `agent_bridge/`:
   ```bash
   python -m pytest backend/tests/unit/ -k "agent_bridge or protocol_adapter or teams_normalizer" \
     --cov=backend/app/services/agent_bridge \
     --cov-report=term-missing -v
   ```
2. Fix any coverage gaps (target: 95%+)
3. Write `docs/04-build/02-Sprint-Plans/SPRINT-182-CLOSE.md` (gate G-Sprint-Close)
4. Update CLAUDE.md to reference Sprint 182 completion

**Verification**:
```bash
python -m pytest backend/tests/unit/ --cov=backend/app/services/agent_bridge \
  --cov-report=term-missing | grep "TOTAL"
```

**Exit Criteria**: 95%+ coverage, SPRINT-182-CLOSE.md written

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| ADR-061 all 5 decisions locked | 5/5 | No TBDs, CTO sign-off |
| Teams normalizer tests pass | 15/15 | PA-21 to PA-35 |
| Sprint 181 regression clean | 20/20 | PA-01 to PA-20 |
| Migration round-trip clean | Pass | alembic upgrade + downgrade + upgrade |
| agent_bridge/ coverage | 95%+ | --cov-report=term-missing |
| ADR-062 draft committed | Draft | File exists in docs/02-design/01-ADRs/ |
| Zero P0 bugs | 0 | No test failures in CI |

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Teams Bot Framework JWKS fetch fails in test | Medium | Low | Mock JWKS HTTP call in tests, test HMAC verification logic separately |
| Adaptive Cards version compatibility | Low | Low | Pin to v1.5 (widely supported by Teams desktop + mobile) |
| SAML 2.0 complexity underestimated (ADR-061) | Medium | Medium | ADR-061 is design only; implementation complexity addressed in Sprint 183 |
| Migration naming conflict with existing s18x | Low | Medium | Use `s182_001` prefix (sprint-aligned, unique) |

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 181 complete | Prerequisite | Required |
| `agent_bridge/` package operational | Code | Available (Sprint 181) |
| `protocol_adapter.py` + `BaseNormalizer` | Code | Available (Sprint 181) |
| `ott_gateway.py` route registered | Code | Available (Sprint 181) |
| Teams Bot registration (Azure Portal) | Infrastructure | Teams registration needed for production; dev uses mock |
| ERD v3.5.0 enterprise_sso_configs + sso_sessions defined | Spec | Available (ERD v3.5.0) |

---

## 7. Definition of Done

- [ ] ADR-061 written with 5 locked decisions, no TBDs
- [ ] ADR-062 draft committed (to be finalized Sprint 183)
- [ ] `s182_001_enterprise_sso.py` migration created and tested (round-trip)
- [ ] `teams_normalizer.py` implemented with HMAC verification + Adaptive Cards
- [ ] 15 new tests (PA-21..35) written and passing
- [ ] 20 Sprint 181 tests (PA-01..20) still passing (regression clean)
- [ ] 95%+ coverage for `agent_bridge/` package
- [ ] Zero P0 bugs
- [ ] SPRINT-182-CLOSE.md written
- [ ] CTO sign-off on ADR-061 before Sprint 183 starts

---

**Approval Required**: CTO (ADR-061 sign-off before Sprint 183 starts)
**Budget**: ~$3,840 (6 days × 8 hrs × $80/hr)
**Risk Level**: HIGH (SSO architecture has downstream implementation impact)
