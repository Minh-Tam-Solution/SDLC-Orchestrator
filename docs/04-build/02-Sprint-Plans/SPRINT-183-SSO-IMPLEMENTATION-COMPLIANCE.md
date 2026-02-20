---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "183"
spec_id: "SPRINT-183"
tier: "ENTERPRISE"
stage: "04 - Build"
---

# SPRINT-183 — Enterprise SSO Implementation + Compliance Evidence

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 8 working days
**Sprint Goal**: Ship SAML 2.0 + Azure AD SSO and extend Evidence Vault with compliance evidence types
**Epic**: EP-07 Multi-Agent + ADR-059 Enterprise-First
**ADR**: ADR-061 (implementation), ADR-062 (finalized)
**Dependencies**: Sprint 182 complete (ADR-061 approved, enterprise_sso_configs migration applied)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Three parallel tracks:
1. **SAML 2.0 + Azure AD SSO** — Full implementation per ADR-061 (5 locked decisions from Sprint 182)
2. **Compliance Evidence Types** — Finalize ADR-062, extend EvidenceType enum (SOC2/HIPAA/NIST/ISO27001)
3. **Slack Normalizer** — Third OTT channel; enterprise teams use Slack

| Deliverable | Priority | New LOC | Days |
|-------------|----------|---------|------|
| `saml_service.py` (python3-saml MIT) | P0 | ~200 | 2 |
| `azure_ad_service.py` (msal MIT, PKCE S256) | P0 | ~150 | 1.5 |
| `enterprise_sso.py` routes (6 endpoints) | P0 | ~250 | 1.5 |
| SSO tests (30 tests: SS-01..15 + AD-01..15) | P0 | ~300 | 1 |
| `s182_001_enterprise_sso.py` (applied in Sprint 182) | -- | already applied | -- |
| ADR-062 finalized + EvidenceType enum extension | P0 | ~100 code + 200 doc | 1 |
| `s183_002_compliance_evidence_types.py` migration | P0 | ~40 | 0.5 |
| `slack_normalizer.py` + 15 tests (PA-36..50) | P1 | ~200 + 200 | 2 |
| Integration + regression | -- | ~50 | 1.5 |
| **Total** | | **~1,770** | **8** |

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | `saml_service.py` | SAML 2.0 SP: login, ACS callback, metadata, JIT provisioning | New | Day 1-2 |
| 2 | `azure_ad_service.py` | Azure AD PKCE: login, callback, JWKS token validation, JIT provisioning | New | Day 3 |
| 3 | `enterprise_sso.py` | 6 API routes: configure, metadata, SAML login/callback, Azure AD login/callback, logout | New | Day 3-4 |
| 4 | `test_saml_service.py` | SS-01 to SS-15 (15 SAML unit tests) | New | Day 4 |
| 5 | `test_azure_ad_service.py` | AD-01 to AD-15 (15 Azure AD unit tests) | New | Day 4 |
| 6 | ADR-062 final | Compliance Evidence Types — 4 new enum values + migration plan | Modified | Day 5 |
| 7 | `s183_002_compliance_evidence_types.py` | Add SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF, ISO27001 to EvidenceType enum | New | Day 5 |
| 8 | `slack_normalizer.py` | Slack Events API → OrchestratorMessage, HMAC-SHA256 verification, Block Kit | New | Day 6-7 |
| 9 | `test_slack_normalizer.py` | PA-36 to PA-50 (15 Slack unit tests) | New | Day 7 |
| 10 | Regression: Sprint 181-182 tests | PA-01..35 still passing | -- | Day 8 |

---

## 3. Daily Schedule

### Day 1-2: SAML 2.0 Service (`saml_service.py`)

**Goal**: Implement SAML 2.0 SP per ADR-061 D-1 and D-3

**Tasks**:
1. Create `backend/app/services/sso/saml_service.py`:
   ```python
   from onelogin.saml2.auth import OneLogin_Saml2_Auth
   from onelogin.saml2.utils import OneLogin_Saml2_Utils

   class SAMLService:
       def __init__(self, sso_config: EnterpriseSsoConfig):
           self.settings = self._build_settings(sso_config)

       def initiate_login(self, request_data: dict) -> str:
           """Return redirect URL for SP-initiated SAML flow."""

       def process_callback(
           self, request_data: dict, db: AsyncSession
       ) -> tuple[User, SsoSession]:
           """Process ACS callback: validate assertion, JIT provision, create session."""

       def get_metadata(self) -> str:
           """Return SP metadata XML for IdP registration."""

       def logout(self, request_data: dict, sso_session_id: int, db: AsyncSession) -> None:
           """Process logout: delete sso_sessions row, clear local session."""
   ```

2. Implement `_jit_provision()` shared logic (used by both SAML and Azure AD):
   - Extract email from SAML NameID or attributes
   - Map IdP groups → Orchestrator role via `sso_config.role_mapping` JSONB
   - Create User if not exists; return existing User if email matches
   - Create `SsoSession` row with SHA256 hash of id_token (D-5)

3. Security: enforce `wantAssertionsSigned=True`, `wantMessagesSigned=True`
4. Security: validate `InResponseTo`, `NotBefore`, `NotOnOrAfter` (±5min window)

**Verification**:
```bash
python -m pytest backend/tests/unit/test_saml_service.py -v --collect-only
```

---

### Day 3: Azure AD Service (`azure_ad_service.py`)

**Goal**: Implement Azure AD OAuth 2.0 PKCE per ADR-061 D-1

**Tasks**:
1. Create `backend/app/services/sso/azure_ad_service.py`:
   ```python
   import msal, hashlib, secrets, httpx

   class AzureADService:
       def __init__(self, sso_config: EnterpriseSsoConfig):
           self.tenant_id = sso_config.issuer_url   # Azure AD tenant ID
           self.client_id = sso_config.client_id

       def initiate_login(self) -> tuple[str, str, str]:
           """Return (auth_url, code_verifier, state). Store verifier+state in Redis (5-min TTL)."""
           code_verifier, code_challenge = generate_pkce_pair()
           state = secrets.token_urlsafe(32)
           auth_url = self._build_auth_url(code_challenge, state)
           return auth_url, code_verifier, state

       async def process_callback(
           self, code: str, state: str, code_verifier: str, db: AsyncSession
       ) -> tuple[User, SsoSession]:
           """Exchange code for id_token, validate JWT, JIT provision user."""

       async def _validate_id_token(self, id_token: str) -> dict:
           """Validate Azure AD JWT: fetch JWKS from login.microsoftonline.com."""
   ```

2. PKCE S256 enforcement:
   ```python
   def generate_pkce_pair() -> tuple[str, str]:
       code_verifier = secrets.token_urlsafe(64)
       code_challenge = base64.urlsafe_b64encode(
           hashlib.sha256(code_verifier.encode()).digest()
       ).rstrip(b"=").decode()
       return code_verifier, code_challenge
   ```

3. State parameter: 32-byte random token stored in Redis with 5-min TTL
4. JWKS caching: cache JWKS for 1 hour (Azure AD rotates keys ~weekly)

**Verification**:
```bash
python -m pytest backend/tests/unit/test_azure_ad_service.py -v --collect-only
```

---

### Day 3-4: Enterprise SSO Routes (`enterprise_sso.py`)

**Goal**: Implement 6 API endpoints per API Spec v3.7.0 Section 12

**Tasks**:
1. Create `backend/app/api/routes/enterprise_sso.py`:

```python
router = APIRouter(prefix="/api/v1/enterprise/sso", tags=["Enterprise SSO"])

# Configure SSO for organization (ENTERPRISE tier required)
@router.post("/configure")
async def configure_sso(config: SsoConfigCreate, db: AsyncSession = Depends(get_db)):
    # Tier gate: ENTERPRISE only (INV-03 from ADR-059)
    ...

# SP metadata XML (public — IT admin downloads this for IdP registration)
@router.get("/saml/metadata")
async def saml_metadata(organization_id: int, db: AsyncSession = Depends(get_db)):
    # No auth required — public metadata endpoint
    # Rate limit: 10 req/min per IP
    ...

# SAML SP-initiated login (returns redirect URL)
@router.post("/saml/login", response_model=SsoLoginResponse)
async def saml_login(org_id: int, current_user: User = Depends(get_current_user)):
    ...

# SAML ACS callback (IdP posts to this endpoint)
@router.post("/saml/callback")
async def saml_callback(request: Request, db: AsyncSession = Depends(get_db)):
    # No auth — IdP posts directly to this endpoint
    # Validate SAML response, JIT provision, create session, redirect to dashboard
    ...

# Azure AD login (returns auth URL with PKCE)
@router.get("/azure-ad/login", response_model=SsoLoginResponse)
async def azure_ad_login(org_id: int, current_user: User = Depends(get_current_user)):
    ...

# Azure AD OAuth2 callback
@router.get("/azure-ad/callback")
async def azure_ad_callback(code: str, state: str, request: Request):
    ...

# Logout: delete sso_sessions row + clear session
@router.post("/logout")
async def sso_logout(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ...
```

2. HTTP status codes:
   - `401 Unauthorized`: Missing/invalid JWT
   - `402 Payment Required`: ENTERPRISE tier required
   - `409 Conflict`: SSO config already exists for this org + provider
   - `422 Unprocessable Entity`: Invalid SAML response

---

### Day 4: SSO Tests (30 tests: SS-01..15 + AD-01..15)

**SAML Tests (SS-01 to SS-15)**:
```
SS-01: initiate_login returns valid SAML redirect URL
SS-02: process_callback validates AssertionConsumerServiceURL
SS-03: process_callback rejects expired assertion (NotOnOrAfter in past)
SS-04: process_callback rejects unsigned assertion (wantAssertionsSigned)
SS-05: process_callback creates new User on first login (JIT provisioning)
SS-06: process_callback returns existing User on second login (no duplicate)
SS-07: process_callback maps IdP group "Engineering" → role "developer" via role_mapping
SS-08: process_callback defaults to "developer" role when no group match
SS-09: process_callback stores id_token_hash (SHA256), NOT raw id_token
SS-10: process_callback creates SsoSession with expires_at ≤ 8h from now
SS-11: get_metadata returns valid XML with SP entityId
SS-12: get_metadata XML contains AssertionConsumerService URL
SS-13: logout deletes SsoSession row from DB
SS-14: process_callback raises SAMLError for InResponseTo mismatch
SS-15: process_callback raises SAMLError for XML injection in assertion
```

**Azure AD Tests (AD-01 to AD-15)**:
```
AD-01: initiate_login returns tuple (auth_url, code_verifier, state)
AD-02: initiate_login uses code_challenge_method=S256
AD-03: auth_url contains response_type=code
AD-04: auth_url contains scope including openid profile email
AD-05: process_callback exchanges code for id_token via HTTPS
AD-06: process_callback validates id_token JWT signature via JWKS
AD-07: process_callback rejects expired id_token
AD-08: process_callback rejects state mismatch (CSRF protection)
AD-09: process_callback JIT provisions user from JWT claims
AD-10: process_callback stores SHA256 hash of id_token
AD-11: process_callback creates SsoSession
AD-12: generate_pkce_pair returns verifier 64 bytes
AD-13: generate_pkce_pair S256 challenge matches sha256(verifier)
AD-14: Azure AD config endpoint GET /azure-ad/callback returns 400 on missing code
AD-15: JWKS cache: second call within TTL doesn't make HTTP request
```

**Verification**:
```bash
python -m pytest backend/tests/unit/test_saml_service.py \
  backend/tests/unit/test_azure_ad_service.py -v
```

---

### Day 5: ADR-062 Final + Compliance Evidence Types Migration

**Goal**: Extend EvidenceType enum with 4 compliance-specific values

**Tasks**:
1. Finalize `docs/02-design/01-ADRs/ADR-062-Compliance-Evidence-Types.md`:
   - 4 locked decisions
   - Implementation: `s183_002_compliance_evidence_types.py`

2. Extend `backend/app/models/evidence.py` EvidenceType enum:
   ```python
   class EvidenceType(str, Enum):
       # Existing types
       DESIGN_DOCUMENT = "DESIGN_DOCUMENT"
       TEST_RESULTS = "TEST_RESULTS"
       CODE_REVIEW = "CODE_REVIEW"
       DEPLOYMENT_PROOF = "DEPLOYMENT_PROOF"
       DOCUMENTATION = "DOCUMENTATION"
       COMPLIANCE = "COMPLIANCE"      # Generic compliance evidence
       # New compliance-specific types (Sprint 183, ADR-062)
       SOC2_CONTROL = "SOC2_CONTROL"    # Maps to SOC2 Trust Service Criteria
       HIPAA_AUDIT = "HIPAA_AUDIT"      # PHI access audit records
       NIST_AI_RMF = "NIST_AI_RMF"     # NIST AI Risk Management Framework controls
       ISO27001 = "ISO27001"            # ISO 27001 Annex A controls
   ```

3. Create `backend/alembic/versions/s183_002_compliance_evidence_types.py`:
   - Add 4 new values to PostgreSQL enum `evidencetype`
   - Alembic: `op.execute("ALTER TYPE evidencetype ADD VALUE IF NOT EXISTS 'SOC2_CONTROL'")`
   - Repeat for HIPAA_AUDIT, NIST_AI_RMF, ISO27001
   - Note: PostgreSQL enum ADD VALUE is irreversible — downgrade is no-op with WARNING

4. Update `backend/app/api/routes/evidence.py`:
   - Add `compliance_type` filter parameter to GET `/api/v1/evidence`
   - Filter: `WHERE evidence_type IN ('SOC2_CONTROL', 'HIPAA_AUDIT', 'NIST_AI_RMF', 'ISO27001')`

**Verification**:
```bash
python -m pytest backend/tests/unit/ -k "evidence" -v
```

---

### Day 6-7: Slack Normalizer (`slack_normalizer.py` + 15 tests PA-36..50)

**Goal**: Third enterprise OTT channel — Slack Events API

**Tasks**:
1. Create `backend/app/services/agent_bridge/slack_normalizer.py`:
   ```python
   import hmac, hashlib, time

   class SlackNormalizer:
       def verify_signature(
           self, body: bytes, timestamp: str, signature: str, signing_secret: str
       ) -> bool:
           """Verify Slack HMAC-SHA256 signature with replay protection."""
           # Replay protection: reject if timestamp > 5 minutes old
           if abs(time.time() - int(timestamp)) > 300:
               return False
           base_string = f"v0:{timestamp}:{body.decode()}"
           expected = "v0=" + hmac.new(
               signing_secret.encode(), base_string.encode(), hashlib.sha256
           ).hexdigest()
           return hmac.compare_digest(expected, signature)

       def parse_event(self, payload: dict) -> OrchestratorMessage:
           """Parse Slack event payload → OrchestratorMessage."""
   ```

2. Handle Slack event types:
   - `event_callback` with `event.type == "message"` (direct messages + mentions)
   - `url_verification` challenge (must return `{"challenge": payload["challenge"]}`)
   - `app_mention` (bot mentioned in channel)

3. OrchestratorMessage mapping:
   ```python
   OrchestratorMessage(
       channel="slack",
       sender_id=event.get("user", ""),
       content=event.get("text", ""),
       timestamp=event.get("ts", ""),
       correlation_id=event.get("event_id", ""),
       metadata={
           "team_id": payload.get("team_id"),
           "channel_id": event.get("channel"),
           "event_type": event.get("type"),
       }
   )
   ```

4. Block Kit response format:
   ```python
   def build_block_kit_response(content: str) -> dict:
       return {
           "blocks": [
               {"type": "section", "text": {"type": "mrkdwn", "text": content}}
           ]
       }
   ```

**Slack Tests (PA-36 to PA-50)**:
```
PA-36: parse_event extracts text from message event
PA-37: parse_event maps user → OrchestratorMessage.sender_id
PA-38: parse_event maps event_id → OrchestratorMessage.correlation_id
PA-39: parse_event sets channel="slack"
PA-40: parse_event handles app_mention event type
PA-41: parse_event handles url_verification challenge (returns challenge string)
PA-42: parse_event handles empty text (bot commands without text)
PA-43: verify_signature returns True for valid Slack signature
PA-44: verify_signature returns False for tampered body
PA-45: verify_signature returns False for wrong signing secret
PA-46: verify_signature constant-time comparison (hmac.compare_digest)
PA-47: verify_signature rejects stale timestamp (>5 min old)
PA-48: ott_gateway.py routes "slack" channel to SlackNormalizer
PA-49: build_block_kit_response returns valid Block Kit structure
PA-50: SlackNormalizer rejects non-Slack channels (raises ValueError)
```

**Verification**:
```bash
python -m pytest backend/tests/unit/test_slack_normalizer.py -v
```

---

### Day 8: Integration + Regression + Sprint Close

**Goal**: All 50 OTT tests pass + SSO tests pass + Sprint close

**Tasks**:
1. Run full OTT regression (PA-01..50):
   ```bash
   python -m pytest backend/tests/unit/ \
     -k "protocol_adapter or teams_normalizer or slack_normalizer" -v
   ```
2. Run SSO tests (SS-01..15 + AD-01..15):
   ```bash
   python -m pytest backend/tests/unit/ -k "saml or azure_ad" -v
   ```
3. Run Alembic round-trip:
   ```bash
   cd backend && alembic upgrade head && alembic downgrade -2 && alembic upgrade head
   ```
4. Register SSO routes in `backend/app/main.py`:
   ```python
   from app.api.routes.enterprise_sso import router as enterprise_sso_router
   app.include_router(enterprise_sso_router)
   ```
5. Coverage check:
   ```bash
   python -m pytest backend/tests/unit/ \
     --cov=backend/app/services/sso \
     --cov=backend/app/services/agent_bridge \
     --cov-report=term-missing -v
   ```

**Exit Criteria**: All 50 OTT tests (PA-01..50) + 30 SSO tests (SS-01..15 + AD-01..15) pass

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| SAML tests pass | 15/15 | SS-01 to SS-15 |
| Azure AD tests pass | 15/15 | AD-01 to AD-15 |
| Slack tests pass | 15/15 | PA-36 to PA-50 |
| Sprint 181-182 OTT regression | 35/35 | PA-01 to PA-35 |
| Compliance evidence types migration | Clean | s183_002 runs without error |
| ADR-062 finalized | 4/4 decisions | No TBDs |
| SSO service coverage | 90%+ | services/sso/ package |
| agent_bridge/ coverage | 95%+ | Full package |
| Zero P0 bugs | 0 | CI clean |

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| SAML assertion validation edge cases | HIGH | HIGH | python3-saml is battle-tested; rely on library; add extensive test cases |
| Azure AD JWKS fetch fails in CI | Medium | Medium | Mock JWKS HTTP in tests; real JWKS only in integration tests |
| PostgreSQL enum irreversibility | Low | Low | s183_002 downgrade is no-op with logged WARNING — acceptable |
| Slack URL verification timing | Low | Low | url_verification challenge returns in <200ms; no async needed |
| python3-saml OpenSSL dependency | Medium | Medium | Add to Dockerfile: `RUN apt-get install -y libxml2-dev libxmlsec1-dev` |

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 182 complete | Prerequisite | Required |
| ADR-061 approved | Design | Required (Sprint 182) |
| `s182_001` migration applied | Database | Sprint 182 |
| python3-saml (MIT) | Package | `pip install python3-saml` |
| msal (MIT) | Package | `pip install msal` |
| OpenSSL + libxml2 | System | Dockerfile update needed |
| Slack app registration | Infrastructure | Dev: use Slack workspace test app; prod: company Slack workspace |

---

## 7. Definition of Done

- [ ] `saml_service.py` implemented with login, callback, metadata, logout
- [ ] `azure_ad_service.py` implemented with PKCE S256 flow
- [ ] `enterprise_sso.py` — 6 routes registered in main.py
- [ ] 30 SSO unit tests (SS-01..15 + AD-01..15) written and passing
- [ ] `slack_normalizer.py` implemented with HMAC verification + Block Kit
- [ ] 15 Slack tests (PA-36..50) written and passing
- [ ] `s183_002` migration clean (4 new enum values)
- [ ] ADR-062 finalized (status: APPROVED)
- [ ] All 35 Sprint 181-182 OTT tests still passing (regression)
- [ ] SSO routes registered in main.py
- [ ] 90%+ coverage for services/sso/, 95%+ for agent_bridge/
- [ ] Zero P0 bugs
- [ ] SPRINT-183-CLOSE.md written

---

**Approval Required**: CTO
**Budget**: ~$5,120 (8 days × 8 hrs × $80/hr)
**Risk Level**: HIGH (SAML XML parsing; python3-saml OpenSSL system dependency)
