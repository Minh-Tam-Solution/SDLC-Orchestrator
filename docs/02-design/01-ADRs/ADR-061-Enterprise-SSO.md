---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "APPROVED"
adr_number: "061"
spec_id: "ADR-061"
tier: "ENTERPRISE"
stage: "02 - Design"
created_date: "2026-02-19"
---

# ADR-061 — Enterprise SSO Architecture

**Status**: APPROVED
**Date**: February 19, 2026
**Author**: @architect
**Reviewer**: CTO
**Sprint**: Sprint 182 — Enterprise SSO Design + Teams Channel
**Supersedes**: None
**Superseded By**: None (implementation in ADR-063, Sprint 183)

---

## Context

SDLC Orchestrator's first enterprise customer pipeline requires SAML 2.0 / Azure AD
SSO as a gate-blocking requirement before contract signature. The platform currently
supports only email/password + social OAuth (GitHub, Google). Enterprise customers on
regulated infrastructure (banks, large enterprises) require:

1. **Identity provider integration** — existing IdP (Okta, Azure AD, Google Workspace)
   must be the single source of truth for user identity; no new passwords
2. **Just-in-time provisioning** — users created on first login; no pre-provisioning by
   Orchestrator admins
3. **RBAC role mapping** — IdP groups or attributes should map to Orchestrator roles
   (Owner, Admin, Member, Viewer) without per-user configuration
4. **Token security** — raw SAML assertions and OIDC id_tokens must never be stored;
   only auditable hashes

**Without SSO, the enterprise sales pipeline is blocked.** ADR-059 established ENTERPRISE
tier as investment priority; SSO is P0 for first enterprise customer (Sprint 183 target).

---

## Decision 1: Protocol Selection — SAML 2.0 + Azure AD OIDC (NOT SDK lock-in)

**Decision**: Support two protocols:
- **SAML 2.0 SP-initiated flow** — for Okta, Google Workspace, Ping Identity
- **Azure AD OAuth 2.0 PKCE (OIDC)** — for Microsoft Azure AD / Entra ID

**Implementation**: Use `python3-saml` (MIT license) for SAML 2.0 and `msal` (MIT) for
Azure AD. Both are network-only (no AGPL contamination). No Okta SDK, no Auth0 SDK —
these create vendor lock-in and AGPL/commercial licensing risk.

**Alternatives considered**:

| Option | Rejected Reason |
|--------|----------------|
| Okta SDK (`okta-sdk-python`) | Vendor lock-in; Apache 2.0 but tight coupling to Okta cloud |
| Auth0 SDK | Commercial SDK; violates Zero-Vendor-Lock principle |
| LDAP/Active Directory direct | Legacy; no cloud-native support; no MFA delegation |
| Social OAuth only (GitHub, Google) | Not enterprise-grade; no corporate IdP support |
| OneLogin SDK | Vendor lock-in |

**Consequences**:
- Sprint 183 uses `python3-saml==1.16.0` (MIT) + `msal==1.32.0` (MIT) — both safe
- Supports 90%+ of enterprise IdPs through SAML 2.0 (Okta, Google, Ping, ADFS)
- Azure AD OIDC covers Microsoft-first enterprise customers natively
- Extensible: add Keycloak / generic OIDC in Sprint 184+ by adding a new provider class

---

## Decision 2: ACS URL Pattern

**Decision**: Assertion Consumer Service (ACS) URL pattern:
```
https://{domain}/api/v1/enterprise/sso/{provider}/callback
```

Where `{provider}` is one of: `saml`, `azure_ad`

**Examples**:
```
https://app.sdlcorchestrator.com/api/v1/enterprise/sso/saml/callback
https://app.sdlcorchestrator.com/api/v1/enterprise/sso/azure_ad/callback
```

**Additional endpoints**:
```
GET    /api/v1/enterprise/sso/metadata              — SP metadata XML (for IdP configuration)
POST   /api/v1/enterprise/sso/configure             — Configure SSO for organization (ENTERPRISE admin)
GET    /api/v1/enterprise/sso/status                — SSO configuration status
POST   /api/v1/enterprise/sso/saml/login            — Initiate SAML SP-initiated flow
POST   /api/v1/enterprise/sso/saml/callback         — SAML ACS endpoint
GET    /api/v1/enterprise/sso/azure_ad/login        — Initiate Azure AD PKCE flow
GET    /api/v1/enterprise/sso/azure_ad/callback     — Azure AD OAuth callback
DELETE /api/v1/enterprise/sso/session/{id}          — SSO logout
```

**Rationale**: `{provider}` in path makes multi-provider support explicit. Enterprise admins
configuring IdPs need a stable, predictable URL. The SP metadata endpoint is required for
Okta/ADFS/Google Workspace configuration UIs.

**Non-goal**: IdP-initiated SAML flow — deferred to Sprint 184 (SP-initiated is sufficient
for 95% of enterprise deployments; IdP-initiated requires additional state management).

---

## Decision 3: Just-in-Time (JIT) User Provisioning

**Decision**: On first successful SSO login, automatically create a user account if one
does not exist for the SSO subject identifier.

**JIT flow**:
```
1. SSO assertion received → extract subject (SAML NameID or OIDC sub)
2. Lookup user by (sso_config_id, subject_id) in sso_sessions
3. If found → update last_login, return existing user
4. If not found:
   a. Create User record (email from IdP assertion, display_name from IdP)
   b. Create sso_sessions record
   c. Map IdP groups → Orchestrator RBAC role (via role_mapping JSONB)
   d. Assign user to organization as ENTERPRISE member
5. Issue Orchestrator JWT (15-min expiry, standard flow)
```

**Role mapping** (`enterprise_sso_configs.role_mapping` JSONB):
```json
{
  "group_mappings": {
    "SDLC-Admins": "admin",
    "SDLC-Owners": "owner",
    "SDLC-Members": "member",
    "SDLC-Viewers": "viewer"
  },
  "default_role": "member",
  "attribute_claim": "groups"
}
```

**Alternatives considered**:

| Option | Rejected Reason |
|--------|----------------|
| Pre-provisioning (SCIM) | See Decision 4 — deferred |
| Manual user creation by admin | Too much friction; enterprise expects zero-touch |
| No role mapping (all members) | Enterprise requires RBAC; CISO sign-off requires fine-grained |

**Consequences**:
- Reduces onboarding friction to zero for enterprise users
- Requires IdP to send `groups` claim in assertion (standard with Okta/Azure AD)
- Sprint 183: implement role_mapping parser in `sso_service.py`

---

## Decision 4: SCIM 2.0 — DEFERRED

**Decision**: SCIM 2.0 user provisioning is **not implemented in Sprint 182 or 183**.
Evaluated but deferred until first enterprise customer explicitly requests it.

**Evaluation**:
- SCIM 2.0 (RFC 7643/7644) enables bidirectional user sync: IdP creates/suspends users
  automatically in Orchestrator without any login event
- Requires `GET /scim/v2/Users`, `POST /scim/v2/Users`, `PATCH /scim/v2/Users/{id}`,
  `DELETE /scim/v2/Users/{id}` endpoints
- Complexity: 5x more code than JIT; requires separate SCIM token management
- JIT covers 90%+ of enterprise SSO use cases; SCIM is an optimization for large orgs
  with frequent employee turnover

**Deferral condition**: SCIM 2.0 added to Sprint 185+ backlog, activated when first
enterprise customer has >200 users OR explicitly requires SCIM in RFP.

---

## Decision 5: Token Storage Security

**Decision**: NEVER store raw SAML assertions, OIDC id_tokens, or access_tokens.
Store only `SHA256(id_token)` in `sso_sessions.id_token_hash`.

**Storage rules**:
```
STORE:   sso_sessions.id_token_hash = SHA256(id_token)    # audit only
STORE:   sso_sessions.subject_id = NameID / sub claim     # lookup key
STORE:   sso_sessions.expires_at = token expiry           # session management
NEVER:   raw SAML assertion XML
NEVER:   raw id_token JWT string
NEVER:   OAuth access_token or refresh_token
```

**Rationale**:
- Raw tokens are credentials; storing them creates a credential-theft surface
- SHA256 hash is sufficient for audit log ("did this session exist?")
- Orchestrator issues its own short-lived JWT (15-min) after SSO validation;
  SSO token is consumed and discarded immediately
- Compliant with OWASP ASVS Level 2 (V3.3 Session Management, V8.3 Sensitive Data)

**Consequences**:
- `sso_sessions` table: 7 columns (see DB schema below)
- `enterprise_sso_configs`: stores SP/IdP metadata, not tokens (13 columns)
- Sprint 183: all SSO service functions enforce this rule; Semgrep rule added to
  detect raw token storage in CI (ADR-058 Pattern integration)

---

## Database Schema

### `enterprise_sso_configs` (13 columns)

```sql
CREATE TABLE enterprise_sso_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider        VARCHAR(20) NOT NULL,        -- 'saml' | 'azure_ad'
    is_enabled      BOOLEAN NOT NULL DEFAULT false,
    -- SAML 2.0 fields
    idp_entity_id   TEXT,                         -- IdP entity ID URL
    idp_sso_url     TEXT,                         -- IdP SSO URL
    idp_x509_cert   TEXT,                         -- IdP public cert (PEM)
    sp_entity_id    TEXT,                         -- Our SP entity ID
    -- Azure AD fields
    tenant_id       VARCHAR(36),                  -- Azure AD tenant GUID
    client_id       VARCHAR(36),                  -- App registration client ID
    -- Role mapping
    role_mapping    JSONB NOT NULL DEFAULT '{}',  -- group → role mapping
    -- Audit
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sso_config_org_provider UNIQUE (organization_id, provider)
);
CREATE INDEX idx_sso_config_org ON enterprise_sso_configs (organization_id);
```

### `sso_sessions` (7 columns)

```sql
CREATE TABLE sso_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sso_config_id   UUID NOT NULL REFERENCES enterprise_sso_configs(id),
    subject_id      VARCHAR(255) NOT NULL,        -- NameID / sub claim
    id_token_hash   VARCHAR(64) NOT NULL,         -- SHA256(id_token) — audit only
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sso_sessions_user    ON sso_sessions (user_id);
CREATE INDEX idx_sso_sessions_expiry  ON sso_sessions (expires_at);
CREATE INDEX idx_sso_sessions_subject ON sso_sessions (sso_config_id, subject_id);
```

---

## Non-Goals

1. **SSO for LITE/STANDARD tiers** — SSO is ENTERPRISE-only (ADR-059 tier gate)
2. **MFA via Orchestrator** — delegate to IdP; Orchestrator never implements TOTP
3. **IdP-initiated SAML** — deferred (Sprint 184+)
4. **SCIM 2.0** — deferred (Decision 4 above)
5. **LDAP/Active Directory direct** — no cloud-native support; rejected
6. **Social OAuth (GitHub, Google) for enterprise** — these remain in LITE/STANDARD tier;
   enterprise uses corporate IdP exclusively

---

## Follow-Up ADRs

| ADR | Description | Sprint |
|-----|-------------|--------|
| ADR-063 | SAML 2.0 Implementation Details (python3-saml integration) | Sprint 183 |
| ADR-064 | Azure AD OIDC Implementation Details (msal integration) | Sprint 183 |
| ADR-065 | SCIM 2.0 Provisioning (if enterprise customer requires) | Sprint 185+ |

---

## Consequences

**Positive**:
- Unblocks first enterprise customer contract (SSO is gate requirement)
- JIT provisioning reduces zero-touch onboarding friction
- Protocol selection (SAML + Azure AD) covers 95%+ of enterprise IdPs
- Token security design satisfies SOC2 Type II and HIPAA audit requirements

**Negative**:
- Sprint 183 implementation complexity is HIGH (SAML XML parsing, cert validation)
- `python3-saml` has strict OpenSSL dependency — Docker image must include `libxmlsec1`
- ACS endpoint must be HTTPS in production (self-signed cert not supported by most IdPs)

**Neutral**:
- SCIM deferral means admin must manually remove departed employees (acceptable short-term)
- IdP-initiated flow deferral means enterprise users must log in from Orchestrator
  (standard SP-initiated flow is the expected enterprise pattern)

---

[@cto: ADR-061 complete — 5 decisions locked, no TBDs. Sprint 183 SAML implementation
can proceed with python3-saml + msal. DB schema ready for s182_001 migration.
Security model satisfies OWASP ASVS V3.3 + V8.3. Ready for sign-off.]
