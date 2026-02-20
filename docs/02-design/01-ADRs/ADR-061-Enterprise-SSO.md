---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "PROPOSED"
adr_id: "ADR-061"
spec_id: "ADR-061"
tier: "ENTERPRISE"
stage: "02 - Design"
sprint: "182"
---

# ADR-061: Enterprise SSO Architecture

**Status**: PROPOSED (pending CTO approval — Sprint 182)
**Date**: February 19, 2026
**Author**: Architect (@architect)
**Reviewers**: CTO, Security Lead
**Supersedes**: None
**Superseded By**: N/A
**Follow-up ADRs**: ADR-063 (Multi-Region, Sprint 186)
**Implementation Sprint**: Sprint 183

---

## Context

The first enterprise sales pipeline requires SSO (Single Sign-On). Enterprise engineering teams (50+ developers) cannot onboard SDLC Orchestrator without:
1. Their IT admin being able to configure company-wide SSO (no per-developer login)
2. Audit trail of who authenticated from which IdP session
3. Automatic account provisioning (JIT) without requiring a separate invitation flow

**Driving business event**: First enterprise customer evaluation (Q2 2026 target per ADR-059).

**What changed**: ADR-059 confirmed that ENTERPRISE is the revenue tier. SSO is listed as a P0 unblock for enterprise sales (BM-03: $80/seat minimum 25 seats = $2,000/month floor).

---

## Decision Table

| # | Decision | Owner | Status |
|---|----------|-------|--------|
| D-1 | Protocol selection: SAML 2.0 + Azure AD OAuth 2.0 PKCE | Tech Lead | LOCKED |
| D-2 | ACS URL pattern: `https://{domain}/api/v1/enterprise/sso/{provider}/callback` | Architect | LOCKED |
| D-3 | JIT provisioning: auto-create user on first SSO login with role mapping | Tech Lead | LOCKED |
| D-4 | SCIM 2.0 deferred to Sprint 185+, not Sprint 183 | Architect | LOCKED |
| D-5 | Token storage: SHA256 hash of id_token only; raw token never persisted | Security Lead | LOCKED |

---

## Alternatives Considered

### Option A (SELECTED): SAML 2.0 SP-initiated + Azure AD OAuth 2.0 PKCE

**Libraries**:
- `python3-saml` (MIT license) — SAML 2.0 service provider implementation
- `msal` (MIT license) — Microsoft Authentication Library for Azure AD

**Rationale**:
- SAML 2.0 covers Okta, Google Workspace, PingFederate (enterprise standard, 15+ years)
- Azure AD PKCE covers Microsoft 365 customers (majority of enterprise Vietnam/SEA market)
- Both libraries are MIT licensed — safe under Apache-2.0 Orchestrator license
- SP-initiated flow gives us control over redirect logic; IdP-initiated also supported as fallback

**Pros**: Enterprise standard; broad IdP compatibility; MIT libraries; clear audit trail
**Cons**: SAML XML parsing adds ~200ms overhead; PKCE S256 requires state management

---

### Option B (REJECTED): Okta SDK Direct Integration

**Why rejected**:
- Okta SDK is proprietary (not MIT/Apache); creates vendor dependency
- Price: Okta charges per monthly active user — cost scales with customer size
- Lock-in: If customer uses PingFederate or ADFS, we can't support them without SAML anyway
- Decision: Support SAML → automatically supports Okta's IdP without their SDK

---

### Option C (REJECTED): Social OAuth Only (GitHub, Google)

**Why rejected**:
- Enterprise IT admins cannot configure "GitHub OAuth" as corporate authentication
- No SAML metadata exchange possible
- No group/role mapping from corporate IdP
- ADR-059 explicitly states: ENTERPRISE tier requires SAML/Azure AD (BM-03 prerequisite)

---

### Option D (REJECTED): LDAP/Active Directory Direct

**Why rejected**:
- LDAP is a legacy protocol; modern enterprise has migrated to SAML/OIDC
- LDAP requires firewall exposure (port 389/636) — security risk
- No federation support (multi-tenant SaaS cannot query customer's LDAP)
- Maintenance burden: LDAP edge cases (encoding, cert rotation) are disproportionate

---

## Decision Details

### D-1: Protocol Selection

**SAML 2.0 Service Provider (SP) Implementation**:
```python
# backend/app/services/sso/saml_service.py
# Library: python3-saml (MIT license, pip install python3-saml)

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings

SAML_SETTINGS_TEMPLATE = {
    "strict": True,                    # Enforce security checks
    "debug": False,
    "sp": {
        "entityId": "https://{domain}/api/v1/enterprise/sso/saml/metadata",
        "assertionConsumerService": {
            "url": "https://{domain}/api/v1/enterprise/sso/saml/callback",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        },
        "singleLogoutService": {
            "url": "https://{domain}/api/v1/enterprise/sso/saml/logout",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        "x509cert": "",               # SP signing cert (HashiCorp Vault managed)
        "privateKey": ""              # SP private key (HashiCorp Vault managed)
    },
    "idp": {
        "entityId": "{idp_issuer_url}",
        "singleSignOnService": {
            "url": "{idp_sso_url}",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "x509cert": "{idp_cert}"     # From IdP metadata XML
    },
    "security": {
        "authnRequestsSigned": True,
        "wantAssertionsSigned": True,
        "wantMessagesSigned": True,
        "wantNameIdEncrypted": False, # Most IdPs don't support NameID encryption
        "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
    }
}
```

**Azure AD OAuth 2.0 PKCE Implementation**:
```python
# backend/app/services/sso/azure_ad_service.py
# Library: msal (MIT license, pip install msal)

import msal
import secrets
import hashlib
import base64

def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256 method)."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return code_verifier, code_challenge

# Azure AD endpoints
AZURE_AD_AUTH_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
AZURE_AD_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
AZURE_AD_JWKS_URL = "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
```

---

### D-2: ACS URL Pattern

**Assertion Consumer Service URL** (where IdP POSTs SAML response):
```
https://{domain}/api/v1/enterprise/sso/saml/callback
```

**Azure AD Callback URL**:
```
https://{domain}/api/v1/enterprise/sso/azure-ad/callback
```

**Metadata URL** (for IdP registration):
```
https://{domain}/api/v1/enterprise/sso/saml/metadata
```

**Rationale**:
- Consistent `/api/v1/enterprise/sso/{provider}/` namespace
- Clear separation of SAML vs Azure AD flows
- Metadata URL allows IT admin to configure without manual cert exchange

---

### D-3: JIT (Just-In-Time) Provisioning

On first successful SSO login, auto-create Orchestrator user:

```python
async def jit_provision_user(
    saml_attributes: dict,
    sso_config: EnterpriseSsoConfig,
    db: AsyncSession,
) -> User:
    """
    Auto-create user on first SSO login.

    Args:
        saml_attributes: Parsed SAML assertion attributes
        sso_config: SSO config with role_mapping JSONB
        db: Database session

    Returns:
        Newly created or existing User
    """
    email = saml_attributes.get("email") or saml_attributes.get(
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    )
    idp_groups = saml_attributes.get("groups", [])

    # Map IdP groups to Orchestrator roles via role_mapping JSONB
    # role_mapping example: {"Engineering": "developer", "QA": "qa", "Admin": "admin"}
    orchestrator_role = _map_idp_groups_to_role(idp_groups, sso_config.role_mapping)

    user = await db.execute(select(User).where(User.email == email))
    if not user.scalar_one_or_none():
        user = User(
            email=email,
            username=email.split("@")[0],
            role=orchestrator_role,
            auth_provider="saml",
            is_active=True,
            password_hash=None,  # SSO users have no password
        )
        db.add(user)
        await db.commit()

    return user
```

**Role mapping rules**:
- If IdP group matches `role_mapping` key → use mapped Orchestrator role
- If no match → default to `developer` role (least privilege)
- IT admin configures `role_mapping` in `enterprise_sso_configs.role_mapping` JSONB

---

### D-4: SCIM 2.0 Deferred

**SCIM 2.0** (System for Cross-domain Identity Management) enables push-based user sync from IdP.

**Why deferred to Sprint 185+**:
- SCIM requires always-on webhook endpoint that IdP calls
- Adds ~400 LOC complexity for edge cases (partial updates, bulk operations, pagination)
- JIT provisioning covers 90% of enterprise onboarding needs
- First enterprise customer has not explicitly requested SCIM
- Sprint 183 already has SSO implementation + compliance types — adding SCIM risks scope creep

**SCIM evaluation criteria** (when to implement):
- Enterprise customer explicitly requires SCIM for IT compliance
- Automated deprovisioning needed (leaver process)
- >100 users need pre-provisioning before SSO login

---

### D-5: Token Storage Security

**NEVER store raw tokens in database**:

```python
# ❌ BANNED — raw token stored
sso_session = SsoSession(id_token=id_token_raw)

# ✅ REQUIRED — SHA256 hash only
import hashlib
id_token_hash = hashlib.sha256(id_token_raw.encode()).hexdigest()
sso_session = SsoSession(id_token_hash=id_token_hash)
```

**Rationale**:
- id_tokens can contain PII (email, name, groups)
- Raw token storage = database breach → token replay attacks
- SHA256 hash is sufficient for session validation (compare hash, not raw token)
- Consistent with `sso_sessions.id_token_hash VARCHAR(64)` column (ERD v3.5.0)

**Session expiry**:
- Max session lifetime: 8 hours (override by IdP token lifetime if shorter)
- Background task: `cleanup_expired_sso_sessions()` runs every hour
- Revocation: DELETE `sso_sessions` row on logout

---

## API Endpoints (Sprint 183 implementation)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/enterprise/sso/saml/metadata` | SP metadata XML for IdP registration | None (public) |
| POST | `/api/v1/enterprise/sso/saml/login` | Initiate SP-initiated SAML flow | JWT (admin) |
| POST | `/api/v1/enterprise/sso/saml/callback` | ACS endpoint for IdP SAML response | None (IdP POST) |
| GET | `/api/v1/enterprise/sso/azure-ad/login` | Initiate Azure AD PKCE flow | JWT (admin) |
| GET | `/api/v1/enterprise/sso/azure-ad/callback` | Azure AD OAuth2 callback | None (Azure redirect) |
| POST | `/api/v1/enterprise/sso/configure` | Configure SSO (save `enterprise_sso_configs` row) | JWT (enterprise admin) |
| POST | `/api/v1/enterprise/sso/logout` | SSO logout + delete sso_sessions row | JWT (user) |

---

## Database Schema (ERD v3.5.0 aligned)

### Table: enterprise_sso_configs

```sql
CREATE TABLE enterprise_sso_configs (
    id                      SERIAL PRIMARY KEY,
    organization_id         INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider                VARCHAR(20) NOT NULL
                               CHECK (provider IN ('SAML', 'AZURE_AD', 'GOOGLE_WS')),
    issuer_url              TEXT,                         -- IdP entity ID
    metadata_url            TEXT,                         -- URL to IdP metadata XML
    acs_url                 TEXT NOT NULL,                -- Our ACS URL
    client_id               VARCHAR(255),                 -- Azure AD: application ID
    client_secret_encrypted BYTEA,                        -- AES-256 encrypted via HashiCorp Vault
    jit_provisioning        BOOLEAN DEFAULT TRUE,
    scim_enabled            BOOLEAN DEFAULT FALSE,        -- Deferred to Sprint 185+
    role_mapping            JSONB DEFAULT '{}',           -- {"IdP-Group": "orchestrator-role"}
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_sso_config_org
    ON enterprise_sso_configs(organization_id, provider);
```

### Table: sso_sessions

```sql
CREATE TABLE sso_sessions (
    id                   SERIAL PRIMARY KEY,
    user_id              INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sso_config_id        INTEGER NOT NULL
                            REFERENCES enterprise_sso_configs(id),
    provider_session_id  TEXT UNIQUE,               -- IdP session ID
    id_token_hash        VARCHAR(64),               -- SHA256 of id_token
    provisioning_method  VARCHAR(20) DEFAULT 'jit', -- 'jit' | 'scim' | 'manual'
    expires_at           TIMESTAMP NOT NULL,        -- Max 8h from creation
    created_at           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sso_sessions_user   ON sso_sessions(user_id);
CREATE INDEX idx_sso_sessions_expiry ON sso_sessions(expires_at);
```

### Alembic Migration: s182_001_enterprise_sso.py

```python
# backend/alembic/versions/s182_001_enterprise_sso.py
# Revision: s182_001
# Revises: s181_001 (or latest Sprint 181 revision)

def upgrade():
    op.create_table("enterprise_sso_configs", ...)
    op.create_table("sso_sessions", ...)
    op.create_index("idx_sso_config_org", "enterprise_sso_configs", ["organization_id", "provider"], unique=True)
    op.create_index("idx_sso_sessions_user", "sso_sessions", ["user_id"])
    op.create_index("idx_sso_sessions_expiry", "sso_sessions", ["expires_at"])

def downgrade():
    op.drop_index("idx_sso_sessions_expiry")
    op.drop_index("idx_sso_sessions_user")
    op.drop_index("idx_sso_config_org")
    op.drop_table("sso_sessions")
    op.drop_table("enterprise_sso_configs")
```

---

## Security Considerations

| Threat | Mitigation |
|--------|-----------|
| SAML XML signature bypass | `authnRequestsSigned=True`, `wantAssertionsSigned=True` in python3-saml settings |
| XML External Entity (XXE) injection | python3-saml uses defusedxml — XXE safe by default |
| PKCE downgrade attack | Enforce `code_challenge_method=S256` only; reject plain method |
| CSRF on OAuth callback | Use `state` parameter (random 32-byte token, stored in server-side session) |
| Replay attack on SAML assertion | Check `InResponseTo` attribute; enforce 5-minute NotBefore/NotOnOrAfter window |
| Token theft from DB | SHA256 hash only (D-5) — raw token never stored |
| Session fixation | Create new `sso_sessions` row on each authentication event |
| Brute force on callback | Rate limit `/sso/callback` at 10 req/min per IP |

---

## Non-Goals

- **LITE/STANDARD SSO**: SSO is ENTERPRISE-only (ADR-059 D1 tier feature matrix)
- **MFA via Orchestrator**: Delegate MFA to IdP (enterprise already enforces it via SAML)
- **Social OAuth (GitHub/Google)**: Already implemented in existing auth flow; SSO is separate path
- **SCIM 2.0**: Deferred (D-4) — JIT covers Sprint 183-184 needs
- **iOS/Android SSO**: Web-based only in Sprint 183; OTT channel auth uses Magic Link (ADR-060)

---

## Consequences

**Positive**:
- Unblocks first enterprise customer ($2,000/month floor per BM-03)
- python3-saml (MIT) + msal (MIT) are safe under Apache-2.0 license — legal audit passes
- JIT provisioning eliminates manual onboarding for 100-seat enterprise deal
- SAML metadata URL allows IT admin self-service configuration

**Negative**:
- SAML XML parsing adds ~200ms to first authentication (subsequent logins use cached session)
- python3-saml requires OpenSSL system dependency (must be in Dockerfile)
- HashiCorp Vault dependency for `client_secret_encrypted` BYTEA (already required for ADR-058)
- SP metadata URL must use HTTPS (self-signed cert not accepted by enterprise IdPs)

**Neutral**:
- Azure AD PKCE flow requires Azure App Registration in customer's tenant (IT admin action)
- SAML IdP-initiated flow supported as fallback (IT admin preference varies)

---

## Follow-up ADRs

| ADR | Topic | Sprint |
|-----|-------|--------|
| ADR-062 | Compliance Evidence Types (SOC2/HIPAA/NIST) | Sprint 182-183 |
| ADR-063 | Multi-Region Deployment + Data Residency | Sprint 186 |

---

## References

- [ERD v3.5.0](../01-planning/04-Data-Model/Data-Model-ERD.md) — enterprise_sso_configs + sso_sessions tables
- [API Spec v3.7.0](../01-planning/05-API-Design/API-Specification.md) — Section 12: Enterprise SSO (6 endpoints)
- [ADR-059](ADR-059-Enterprise-First-Refocus.md) — Enterprise-First strategy, BM-03 pricing
- [python3-saml](https://github.com/SAML-Toolkits/python3-saml) — MIT license, SAML 2.0 SP
- [msal](https://github.com/AzureAD/microsoft-authentication-library-for-python) — MIT license, Azure AD

---

## Document Control

**Version History**:
- v1.0.0 (February 19, 2026): Initial ADR — 5 decisions locked (PROPOSED)

**Status**: PROPOSED — pending CTO sign-off before Sprint 183 implementation starts
**Implementation Sprint**: Sprint 183
**Gate**: G2 Design Ready (CTO approval required)
