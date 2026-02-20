# API Authentication & Authorization
## JWT + OAuth 2.0 + C-Suite RBAC

**Version**: 2.0.0
**Date**: December 21, 2025
**Status**: ACTIVE - EP-04/05/06 EXTENDED
**Authority**: Backend Lead + Security Lead + CTO Review (✅ APPROVED)
**Foundation**: NFR v3.0.0, Data Model ERD v3.0.0, ADR-021 Analytics
**Stage**: Stage 01 (WHAT - Planning & Analysis)
**Framework**: SDLC 6.1.0 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)

**Changelog**:
- v2.0.0 (Dec 21, 2025): SDLC 5.1.3 update, FR-21 BYOK API key integration
- v1.0.0 (Nov 13, 2025): Initial auth specification

---

## Document Purpose

This document defines **WHAT authentication and authorization mechanisms to implement** for API security.

**Key Sections**:
- JWT token-based authentication (access + refresh tokens)
- OAuth 2.0 integration (GitHub, Google, Microsoft)
- Role-Based Access Control (RBAC) with C-Suite roles
- Multi-Factor Authentication (MFA)
- Session management & token revocation
- API key authentication (for integrations)

**Out of Scope** (Stage 02 - Architecture):
- Implementation details (passport.js, JWT libraries)
- Database schema for sessions
- Infrastructure (Redis for token blacklist)

---

## Authentication Overview

### Authentication Methods

| Method | Use Case | Token Type | Expiry |
|--------|----------|------------|--------|
| **JWT (Primary)** | User login (email/password) | Bearer token | 1 hour (access), 30 days (refresh) |
| **OAuth 2.0** | Social login (GitHub, Google, Microsoft) | Bearer token | 1 hour (access), 30 days (refresh) |
| **API Key** | Integration (GitHub Actions, CI/CD) | Static key | Never (until revoked) |
| **MFA** | High-security accounts (C-Suite, Admin) | TOTP (Time-based OTP) | 30 seconds |

### Authentication Flow (JWT)

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database
    participant Redis

    Client->>API: POST /auth/login (email, password)
    API->>Database: Validate credentials (bcrypt)
    Database-->>API: User found + role
    API->>Redis: Store session metadata
    API-->>Client: 200 OK (access_token, refresh_token, user)

    Note over Client: Use access_token for API calls

    Client->>API: GET /projects (Authorization: Bearer <access_token>)
    API->>Redis: Validate token (not blacklisted)
    API->>API: Verify JWT signature + expiry
    API->>Database: Fetch user permissions (RBAC)
    API-->>Client: 200 OK (projects data)

    Note over Client: Access token expires (1 hour)

    Client->>API: POST /auth/refresh (refresh_token)
    API->>Database: Validate refresh token (not revoked)
    API->>Redis: Store new session metadata
    API-->>Client: 200 OK (new access_token, new refresh_token)
```

---

## JWT Token Structure

### Access Token (Short-lived: 1 hour)

**Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@techcorp.com",
  "role": "em",
  "team_id": "7f3e8400-e29b-41d4-a716-446655440001",
  "organization_id": "8a4f9500-e29b-41d4-a716-446655440002",
  "iat": 1673625600,
  "exp": 1673629200,
  "type": "access"
}
```

**Fields**:
- `sub`: User ID (UUID)
- `email`: User email (for audit logs)
- `role`: User role (for RBAC, see NFR8)
- `team_id`: Team membership (for project filtering)
- `organization_id`: Organization (for multi-tenancy)
- `iat`: Issued at (Unix timestamp)
- `exp`: Expiry (Unix timestamp, 1 hour from `iat`)
- `type`: Token type (`access` or `refresh`)

### Refresh Token (Long-lived: 30 days)

**Payload**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@techcorp.com",
  "iat": 1673625600,
  "exp": 1676217600,
  "type": "refresh",
  "jti": "a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d"
}
```

**Fields**:
- `jti`: JWT ID (for revocation tracking)
- `exp`: Expiry (30 days from `iat`)
- `type`: Token type (`refresh`)

### JWT Signature (HS256)

**Algorithm**: HMAC-SHA256
**Secret**: 256-bit random key (stored in environment variable `JWT_SECRET`)
**Rotation**: Every 90 days (per NFR7)

**Example**:
```
header.payload.signature
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6ImpvaG4uZG9lQHRlY2hjb3JwLmNvbSIsInJvbGUiOiJlbSIsInRlYW1faWQiOiI3ZjNlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDEiLCJvcmdhbml6YXRpb25faWQiOiI4YTRmOTUwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDIiLCJpYXQiOjE2NzM2MjU2MDAsImV4cCI6MTY3MzYyOTIwMCwidHlwZSI6ImFjY2VzcyJ9.ABC123xyz...
```

---

## OAuth 2.0 Integration

### Supported Providers

| Provider | Use Case | User Base | Implementation |
|----------|----------|-----------|----------------|
| **GitHub** | Developer login (primary) | 100M+ developers | OAuth 2.0 Authorization Code Flow |
| **Google** | Enterprise login | 2B+ users | OAuth 2.0 + OpenID Connect |
| **Microsoft** | Enterprise login (Azure AD) | 300M+ enterprise users | OAuth 2.0 + SAML 2.0 |

### OAuth 2.0 Flow (Authorization Code)

```mermaid
sequenceDiagram
    participant User
    participant Client (Browser)
    participant API
    participant GitHub
    participant Database

    User->>Client: Click "Login with GitHub"
    Client->>API: GET /auth/github
    API-->>Client: Redirect to GitHub OAuth
    Client->>GitHub: Authorize SDLC Orchestrator
    GitHub-->>Client: Redirect to /auth/github/callback?code=abc123
    Client->>API: GET /auth/github/callback?code=abc123
    API->>GitHub: POST /access_token (code, client_secret)
    GitHub-->>API: access_token
    API->>GitHub: GET /user (access_token)
    GitHub-->>API: User profile (email, name, avatar)
    API->>Database: Upsert user (email, OAuth provider)
    API->>API: Generate JWT tokens
    API-->>Client: Redirect to /dashboard?token=<jwt>
    Client->>User: Logged in successfully
```

### OAuth 2.0 Configuration

**GitHub OAuth App**:
```yaml
Client ID: ghp_1234567890abcdefghijklmnopqrst
Client Secret: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop (stored in env)
Callback URL: https://api.sdlc-orchestrator.com/v1/auth/github/callback
Scopes:
  - user:email (required, to get user email)
  - read:user (required, to get user profile)
  - read:org (optional, to detect team membership)
```

**Google OAuth 2.0 Client**:
```yaml
Client ID: 123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
Client Secret: GOCSPX-ABCDefghIJKlmnOPQrstUVWxyz123 (stored in env)
Callback URL: https://api.sdlc-orchestrator.com/v1/auth/google/callback
Scopes:
  - openid (required, OpenID Connect)
  - profile (required, user profile)
  - email (required, user email)
```

**Microsoft Azure AD**:
```yaml
Application (client) ID: a1b2c3d4-e5f6-4a5b-8c7d-1e2f3a4b5c6d
Client Secret: ABC~123.xyz~DEF-456 (stored in env)
Redirect URI: https://api.sdlc-orchestrator.com/v1/auth/microsoft/callback
Scopes:
  - openid (required)
  - profile (required)
  - email (required)
  - User.Read (Microsoft Graph API)
```

---

## Role-Based Access Control (RBAC)

### C-Suite + Engineering Roles (13 Roles)

**Role Hierarchy** (from highest to lowest privilege):

```yaml
Executive Leadership (C-Suite):
  - CEO (Chief Executive Officer)
    Permissions: ALL (view all, override all, approve all)
  - CTO (Chief Technology Officer)
    Permissions: View all, override gates, approve G2/G3/G5/G7
  - CPO (Chief Product Officer)
    Permissions: View all, approve G0.1/G0.2/G1/G4/G8
  - CIO (Chief Information Officer)
    Permissions: View all, approve G5/G6, manage integrations
  - CFO (Chief Financial Officer)
    Permissions: View all budgets, approve G9

Engineering Team:
  - EM (Engineering Manager)
    Permissions: View own projects, create projects, request approvals
  - PM (Product Manager)
    Permissions: View assigned projects, manage requirements
  - Dev Lead (Tech Lead)
    Permissions: View assigned projects, approve G3, code review
  - QA Lead
    Permissions: View assigned projects, approve G4, manage test plans
  - Security Lead
    Permissions: View all projects, approve G2, security audits
  - DevOps Lead
    Permissions: View all projects, approve G5/G6, manage deployments
  - Data Lead
    Permissions: View all projects, approve G7, data governance

System Admin:
  - Admin
    Permissions: ALL (system configuration, user management, policy management)
```

### RBAC Matrix (Per NFR8)

**Resource Permissions**:

| Resource | View | Create | Update | Delete | Approve | Override |
|----------|------|--------|--------|--------|---------|----------|
| **Projects** |
| CEO | All | ✅ | ✅ | ✅ | ✅ All gates | ✅ |
| CTO | All | ✅ | ✅ | ✅ | ✅ G2/G3/G5/G7 | ✅ |
| CPO | All | ✅ | ✅ | ❌ | ✅ G0.1/G0.2/G1/G4/G8 | ❌ |
| CIO | All | ❌ | ❌ | ❌ | ✅ G5/G6 | ❌ |
| CFO | All | ❌ | ❌ | ❌ | ✅ G9 (budget) | ❌ |
| EM | Own only | ✅ | ✅ | ✅ | ❌ | ❌ |
| PM | Assigned | ❌ | ✅ | ❌ | ❌ | ❌ |
| Dev Lead | Assigned | ❌ | ❌ | ❌ | ✅ G3 | ❌ |
| QA Lead | Assigned | ❌ | ❌ | ❌ | ✅ G4 | ❌ |
| Security Lead | All | ❌ | ❌ | ❌ | ✅ G2 | ❌ |
| DevOps Lead | All | ❌ | ❌ | ❌ | ✅ G5/G6 | ❌ |
| Data Lead | All | ❌ | ❌ | ❌ | ✅ G7 | ❌ |
| Admin | All | ✅ | ✅ | ✅ | ✅ All gates | ✅ |

| **Evidence** |
| CEO | All | ✅ | ✅ | ✅ | - | - |
| CTO | All | ✅ | ✅ | ✅ | - | - |
| CPO | All | ✅ | ✅ | ❌ | - | - |
| EM | Own projects | ✅ | ✅ | ✅ | - | - |
| PM | Assigned | ✅ | ❌ | ❌ | - | - |
| Dev/QA/etc | Assigned | ✅ | ❌ | ❌ | - | - |
| Admin | All | ✅ | ✅ | ✅ | - | - |

| **Policies** |
| CEO | All | ✅ | ✅ | ✅ (custom only) | - | - |
| CTO | All | ✅ | ✅ | ✅ (custom only) | - | - |
| Admin | All | ✅ | ✅ | ✅ (custom only) | - | - |
| Others | All | ❌ | ❌ | ❌ | - | - |

| **Users** |
| CEO | All | ✅ | ✅ | ✅ | - | - |
| CIO | All | ✅ | ✅ | ❌ | - | - |
| Admin | All | ✅ | ✅ | ✅ | - | - |
| Others | Self only | ❌ | ✅ (self) | ❌ | - | - |

| **Audit Logs** |
| CEO | All | - | - | ❌ | - | - |
| CTO | All | - | - | ❌ | - | - |
| CIO | All | - | - | ❌ | - | - |
| Admin | All | - | - | ❌ | - | - |
| Others | ❌ | - | - | ❌ | - | - |

**Note**: Audit logs are **immutable** (NFR17) - no one can delete, only view.

---

## Multi-Factor Authentication (MFA)

### MFA Requirements

**Mandatory MFA** (per NFR7):
- ✅ CEO, CTO, CPO, CIO, CFO (C-Suite)
- ✅ Admin
- ⚠️ Optional for other roles (EM, PM, Dev, QA, etc.)

### MFA Methods

| Method | Type | Security Level | User Experience |
|--------|------|----------------|-----------------|
| **TOTP (Primary)** | Time-based OTP (Google Authenticator, Authy) | HIGH | Good (scan QR code once) |
| **SMS (Backup)** | SMS code | MEDIUM | Fair (carrier dependency) |
| **Email (Backup)** | Email code | LOW | Fair (email compromise risk) |
| **WebAuthn (Future)** | Hardware key (YubiKey, Face ID) | VERY HIGH | Excellent (biometric) |

### MFA Flow (TOTP)

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API
    participant Database
    participant TOTP Service

    Note over User: First-time MFA setup
    User->>Client: Login (email/password)
    Client->>API: POST /auth/login
    API->>Database: Validate credentials
    API-->>Client: 200 OK (mfa_required: true, mfa_setup: true)
    Client->>User: Show QR code (TOTP secret)
    User->>TOTP Service: Scan QR code (Google Authenticator)
    TOTP Service-->>User: Generate 6-digit code
    User->>Client: Enter code: 123456
    Client->>API: POST /auth/mfa/setup (code: 123456)
    API->>API: Verify TOTP code
    API->>Database: Save TOTP secret (encrypted)
    API-->>Client: 200 OK (access_token, refresh_token)

    Note over User: Subsequent logins
    User->>Client: Login (email/password)
    Client->>API: POST /auth/login
    API->>Database: Validate credentials
    API-->>Client: 200 OK (mfa_required: true, mfa_setup: false)
    Client->>User: Prompt for MFA code
    User->>TOTP Service: Open app → Get code: 789012
    User->>Client: Enter code: 789012
    Client->>API: POST /auth/mfa/verify (code: 789012)
    API->>API: Verify TOTP code (30-second window)
    API-->>Client: 200 OK (access_token, refresh_token)
```

### TOTP Configuration

**Algorithm**: TOTP (RFC 6238)
**Hash**: SHA-1
**Digits**: 6
**Period**: 30 seconds
**Issuer**: SDLC Orchestrator

**QR Code Format** (otpauth URI):
```
otpauth://totp/SDLC%20Orchestrator:john.doe@techcorp.com?secret=JBSWY3DPEHPK3PXP&issuer=SDLC%20Orchestrator
```

---

## API Key Authentication

### Use Case: Integration Authentication

**When to Use API Keys**:
- ✅ GitHub Actions workflows (CI/CD)
- ✅ Terraform/IaC automation
- ✅ Third-party integrations (Slack bots, webhooks)
- ❌ **NOT for user authentication** (use JWT instead)

### API Key Format

**Format**: `sdlc_live_<32_random_chars>` (production) or `sdlc_test_<32_random_chars>` (test)

**Example**:
```
sdlc_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Storage**: SHA256 hash stored in database (never store plaintext)

**Scope**: API keys are scoped to a team (team_id) and have limited permissions:
- ✅ Can read projects, gates, evidence
- ✅ Can create evidence (upload from CI/CD)
- ❌ Cannot approve gates (requires user authentication)
- ❌ Cannot delete projects/evidence

### API Key Authentication Flow

```http
GET /projects HTTP/1.1
Host: api.sdlc-orchestrator.com
Authorization: Bearer sdlc_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Backend Validation**:
1. Extract API key from `Authorization` header
2. Hash API key (SHA256)
3. Lookup hashed key in `api_keys` table
4. Verify key is not revoked (`is_active = true`)
5. Load team permissions (`team_id`)
6. Grant limited access (read + create evidence only)

---

## Session Management

### Session Storage (Redis)

**Why Redis**:
- ✅ In-memory (fast lookup, <1ms)
- ✅ TTL support (auto-expire sessions)
- ✅ High availability (Redis Sentinel)
- ✅ Scalable (Redis Cluster)

**Session Data** (per access token):
```redis
Key: session:<jwt_jti>
Value: {
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "em",
  "team_id": "7f3e8400-e29b-41d4-a716-446655440001",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2025-01-13T10:00:00Z"
}
TTL: 3600 seconds (1 hour, matches access token expiry)
```

### Token Revocation (Blacklist)

**Use Cases**:
- ✅ User logs out (invalidate refresh token)
- ✅ Admin revokes user access (invalidate all tokens)
- ✅ Security breach (invalidate all tokens for team/org)

**Blacklist Storage** (Redis):
```redis
Key: blacklist:<jwt_jti>
Value: "revoked"
TTL: 2592000 seconds (30 days, matches refresh token expiry)
```

**Validation Flow**:
1. Extract JWT from `Authorization` header
2. Verify JWT signature + expiry
3. Check Redis blacklist: `EXISTS blacklist:<jwt_jti>`
4. If blacklisted → Return `401 Unauthorized`
5. If not blacklisted → Proceed to RBAC check

---

## Password Security

### Password Requirements (per NFR7)

**Minimum Requirements**:
- ✅ 8+ characters
- ✅ At least 1 uppercase letter (A-Z)
- ✅ At least 1 lowercase letter (a-z)
- ✅ At least 1 digit (0-9)
- ✅ At least 1 special character (!@#$%^&*)

**Forbidden**:
- ❌ Common passwords (password123, qwerty, etc.)
- ❌ User email as password
- ❌ Repeated characters (aaaaaa, 111111)
- ❌ Sequential characters (abcdef, 123456)

**Validation Regex**:
```regex
^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$
```

### Password Hashing (bcrypt)

**Algorithm**: bcrypt (NIST recommended)
**Cost Factor**: 12 rounds (per NFR7)
**Salt**: Automatically generated per password (random, 16 bytes)

**Example**:
```javascript
const bcrypt = require('bcrypt');

// Hashing
const password = 'SecurePassword123!';
const salt_rounds = 12;
const password_hash = await bcrypt.hash(password, salt_rounds);
// $2b$12$KIXxJ3Xy7z9.1eD0qQ5N8.abc123xyz...

// Verification
const is_match = await bcrypt.compare(password, password_hash);
// true
```

### Password Reset Flow

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API
    participant Database
    participant Email Service

    User->>Client: Click "Forgot Password"
    Client->>API: POST /auth/forgot-password (email)
    API->>Database: Find user by email
    API->>API: Generate reset token (JWT, 15 min expiry)
    API->>Database: Store reset token (hashed)
    API->>Email Service: Send reset email
    Email Service-->>User: Email with reset link
    User->>Client: Click reset link
    Client->>API: GET /auth/reset-password?token=<jwt>
    API->>Database: Validate reset token (not expired, not used)
    API-->>Client: 200 OK (show reset form)
    User->>Client: Enter new password
    Client->>API: POST /auth/reset-password (token, new_password)
    API->>API: Hash new password (bcrypt)
    API->>Database: Update password, invalidate reset token
    API->>Database: Revoke all existing refresh tokens (force re-login)
    API-->>Client: 200 OK (password reset successful)
```

---

## Rate Limiting (Authentication)

### Rate Limits (per IP address)

| Endpoint | Limit | Window | Reason |
|----------|-------|--------|--------|
| `/auth/login` | 5 requests | 15 minutes | Prevent brute-force attacks |
| `/auth/forgot-password` | 3 requests | 1 hour | Prevent email spam |
| `/auth/reset-password` | 3 requests | 1 hour | Prevent token guessing |
| `/auth/mfa/verify` | 5 requests | 5 minutes | Prevent TOTP brute-force |

**Rate Limit Exceeded Response** (HTTP 429):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many login attempts. Try again in 15 minutes.",
    "details": {
      "limit": 5,
      "window": "15 minutes",
      "retry_after": 900
    },
    "timestamp": "2025-01-13T10:30:00Z"
  }
}
```

---

## Security Best Practices

### 1. Never Log Sensitive Data

**NEVER log**:
- ❌ Passwords (plaintext or hashed)
- ❌ JWT tokens (access or refresh)
- ❌ API keys
- ❌ OAuth secrets (client_secret)
- ❌ TOTP secrets

**OK to log**:
- ✅ User ID (UUID)
- ✅ Email address (for audit)
- ✅ IP address (for security)
- ✅ User agent (for device tracking)
- ✅ Authentication events (login success/failure)

### 2. Use HTTPS Everywhere (TLS 1.3)

**Requirements**:
- ✅ All API endpoints use HTTPS (no HTTP)
- ✅ TLS 1.3 or TLS 1.2 (minimum)
- ✅ Certificate from trusted CA (Let's Encrypt, Cloudflare)
- ✅ HSTS header (Strict-Transport-Security: max-age=31536000)

### 3. Implement CORS Properly

**CORS Configuration**:
```javascript
{
  "origin": ["https://app.sdlc-orchestrator.com", "https://staging.sdlc-orchestrator.com"],
  "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
  "allowedHeaders": ["Authorization", "Content-Type"],
  "credentials": true,
  "maxAge": 86400
}
```

**Production**:
- ✅ Whitelist specific origins (NOT `*`)
- ✅ `credentials: true` (for cookies, if used)
- ❌ NEVER allow `Access-Control-Allow-Origin: *` with credentials

### 4. Validate JWT on Every Request

**JWT Validation Checklist**:
- ✅ Verify signature (HMAC-SHA256)
- ✅ Check expiry (`exp` claim)
- ✅ Check issued-at (`iat` claim, not in future)
- ✅ Check token type (`type: "access"` for API calls)
- ✅ Check blacklist (Redis lookup)
- ✅ Verify user still exists (database lookup)
- ✅ Verify user still active (`is_active = true`)

### 5. Rotate Secrets Regularly

**Rotation Schedule**:
- ✅ JWT secret: Every 90 days
- ✅ OAuth client secrets: Every 180 days
- ✅ API keys: Never expire (manual revocation only)
- ✅ TOTP secrets: Never rotate (user would lose access)

---

## References

- [JWT Best Practices (RFC 8725)](https://tools.ietf.org/html/rfc8725)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NFR8: Authentication & Authorization](../01-Requirements/Non-Functional-Requirements.md#nfr8-authentication--authorization)
- [Data Model ERD](../03-Data-Model/Data-Model-ERD.md)

---

**Last Updated**: 2025-01-13
**Owner**: Backend Lead + Security Lead
**Status**: 🟡 DRAFT (PENDING REVIEW)

---

**End of API Authentication & Authorization v1.0.0**
