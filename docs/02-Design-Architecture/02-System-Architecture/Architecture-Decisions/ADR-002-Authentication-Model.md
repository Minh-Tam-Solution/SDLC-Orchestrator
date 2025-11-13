# ADR-002: Authentication Model (JWT + OAuth 2.0 + MFA)

**Status**: ✅ ACCEPTED
**Date**: November 13, 2025
**Deciders**: CTO, Security Lead, Backend Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 4.9

---

## Context

SDLC Orchestrator requires authentication for:
- **Web Dashboard** (React SPA)
- **VS Code Extension** (OAuth device flow)
- **CLI** (`sdlcctl` - API key + OAuth)
- **API integrations** (CI/CD, third-party tools)

**Security Requirements**:
- C-Suite RBAC (13 roles: CEO, CTO, CPO, CIO, CFO + Engineering)
- Multi-Factor Authentication (MFA) mandatory for C-Suite
- SSO integration (GitHub, Google, Microsoft)
- API key authentication (CI/CD pipelines)
- Session management (refresh tokens, revocation)

**Alternatives Considered**:
1. **JWT (JSON Web Tokens)** - Stateless, self-contained
2. **Session cookies** - Stateful, server-side storage
3. **OAuth 2.0** - Delegated authorization (GitHub, Google, Microsoft)
4. **SAML 2.0** - Enterprise SSO (Okta, Azure AD)

---

## Decision

**We choose a hybrid authentication model:**
1. **JWT** for access tokens (short-lived, 1 hour)
2. **OAuth 2.0** for SSO (GitHub, Google, Microsoft)
3. **MFA** (TOTP) mandatory for C-Suite roles
4. **API keys** for CI/CD integrations

---

## Rationale

### Why JWT?

**1. Stateless Authentication (Scalability)**
```javascript
// JWT Access Token Payload
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // User ID
  "email": "john.doe@techcorp.com",
  "role": "em",  // Engineering Manager
  "team_id": "7f3e8400-e29b-41d4-a716-446655440001",
  "organization_id": "8a4f9500-e29b-41d4-a716-446655440002",
  "iat": 1673625600,  // Issued at
  "exp": 1673629200,  // Expires in 1 hour
  "type": "access"
}
```

**Benefits**:
- ✅ **No database lookups**: Verify signature, check expiry → auth in <1ms
- ✅ **Horizontal scaling**: No shared session storage (Redis not required for auth)
- ✅ **Microservices-ready**: Each service validates JWT independently

**Trade-offs**:
- ❌ **Cannot revoke**: Once issued, valid until expiry (mitigated by short TTL + refresh tokens)
- ❌ **Larger payload**: 300-500 bytes vs 32 bytes session ID

**2. Refresh Token Pattern (Session Management)**
```javascript
// JWT Refresh Token Payload
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "type": "refresh",
  "iat": 1673625600,
  "exp": 1676217600  // Expires in 30 days
}
```

**Flow**:
```
1. User logs in → Server issues access token (1h) + refresh token (30d)
2. Client stores refresh token (HttpOnly cookie, secure)
3. Access token expires → Client calls /auth/refresh with refresh token
4. Server validates refresh token → Issues new access token
5. Refresh token expires → User must re-login
```

**Benefits**:
- ✅ **Short-lived access tokens**: Limits damage if stolen (1 hour vs 30 days)
- ✅ **Revocation support**: Blacklist refresh tokens in Redis (rare operation)
- ✅ **Better UX**: User stays logged in for 30 days (no frequent re-login)

---

### Why OAuth 2.0?

**1. SSO Integration (GitHub, Google, Microsoft)**
```python
# OAuth 2.0 Authorization Code Flow (Backend)
@app.get("/auth/github")
async def github_login():
    # Redirect user to GitHub authorization page
    auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user:email"
    return RedirectResponse(auth_url)

@app.get("/auth/github/callback")
async def github_callback(code: str):
    # Exchange code for access token
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code
        }
    )
    access_token = token_response.json()["access_token"]

    # Fetch user profile from GitHub
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    github_user = user_response.json()

    # Create or update user in database
    user = await create_or_update_user(
        email=github_user["email"],
        name=github_user["name"],
        avatar_url=github_user["avatar_url"],
        provider="github"
    )

    # Issue JWT tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }
```

**Benefits**:
- ✅ **No password management**: Users authenticate via trusted providers
- ✅ **Faster onboarding**: No sign-up form (auto-populate from GitHub/Google)
- ✅ **Security**: Providers handle MFA, password resets, breach detection

**2. OAuth Device Flow (VS Code Extension)**
```python
# OAuth 2.0 Device Authorization Grant (for CLI/VS Code)
@app.post("/auth/device/code")
async def device_code():
    # Generate device code + user code
    device_code = generate_random_string(32)
    user_code = generate_random_string(8).upper()  # e.g., "ABCD-1234"

    # Store in Redis (expires in 10 minutes)
    await redis.setex(f"device:{device_code}", 600, json.dumps({
        "user_code": user_code,
        "status": "pending"
    }))

    return {
        "device_code": device_code,
        "user_code": user_code,
        "verification_uri": "https://sdlc-orchestrator.com/activate",
        "expires_in": 600
    }

@app.post("/auth/device/token")
async def device_token(device_code: str):
    # Check if user approved
    device_data = await redis.get(f"device:{device_code}")
    if device_data["status"] != "approved":
        return {"error": "authorization_pending"}

    # Issue tokens
    user_id = device_data["user_id"]
    user = await get_user(user_id)
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user)
    }
```

**VS Code Extension Flow**:
```
1. Extension calls /auth/device/code → Gets user_code "ABCD-1234"
2. Extension displays: "Go to https://sdlc-orchestrator.com/activate and enter: ABCD-1234"
3. User enters code in browser → Logs in → Approves extension
4. Extension polls /auth/device/token → Receives access token
```

**Benefits**:
- ✅ **Secure**: No browser redirect in VS Code (avoids phishing)
- ✅ **User-friendly**: Simple 8-character code (not 64-char URL)
- ✅ **Standard**: Used by GitHub CLI, Azure CLI, Google Cloud SDK

---

### Why MFA (TOTP)?

**1. C-Suite Mandate (SOC 2 Requirement)**
```python
# MFA Enrollment (TOTP - Time-based One-Time Password)
@app.post("/auth/mfa/enroll")
async def mfa_enroll(user: User = Depends(get_current_user)):
    # Generate TOTP secret (32-byte base32)
    secret = pyotp.random_base32()

    # Generate QR code (user scans with Google Authenticator)
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="SDLC Orchestrator"
    )
    qr_code = qrcode.make(totp_uri)

    # Store secret (encrypted) in database
    await store_mfa_secret(user.id, secret)

    return {
        "secret": secret,
        "qr_code": qr_code.to_base64(),
        "backup_codes": generate_backup_codes(10)  # 10 one-time codes
    }

# MFA Verification (Login)
@app.post("/auth/mfa/verify")
async def mfa_verify(user_id: str, code: str):
    # Retrieve secret from database
    secret = await get_mfa_secret(user_id)

    # Verify TOTP code (6-digit, 30-second window)
    totp = pyotp.TOTP(secret)
    if totp.verify(code, valid_window=1):  # Allow 1 step tolerance (±30s)
        return {"status": "verified"}
    else:
        return {"status": "invalid_code"}
```

**Benefits**:
- ✅ **Phishing-resistant**: TOTP codes change every 30 seconds (not reusable)
- ✅ **Offline**: Works without internet (Google Authenticator, Authy)
- ✅ **Compliance**: SOC 2 Type 2, ISO 27001 require MFA for privileged accounts

**2. MFA Enforcement (C-Suite Only)**
```python
# Role-based MFA enforcement
MFA_REQUIRED_ROLES = ["ceo", "cto", "cpo", "cio", "cfo"]

@app.post("/auth/login")
async def login(email: str, password: str):
    user = await authenticate_user(email, password)

    # Check if MFA required
    if user.role in MFA_REQUIRED_ROLES and not user.mfa_enabled:
        return {"error": "mfa_required", "message": "C-Suite must enable MFA"}

    # If MFA enabled, require TOTP code
    if user.mfa_enabled:
        return {"status": "mfa_required", "user_id": user.id}

    # No MFA → Issue tokens
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user)
    }
```

**Why NOT SMS MFA?**
- ❌ **SIM swapping attacks**: Attacker port phone number → intercept SMS
- ❌ **Cost**: $0.01-0.05 per SMS (vs $0 for TOTP)
- ❌ **Reliability**: SMS delivery delays, carrier issues
- ✅ **TOTP is better**: More secure, cheaper, faster

---

### Why API Keys (CI/CD)?

**1. Long-Lived Tokens (No User Interaction)**
```python
# API Key Generation
@app.post("/auth/api-keys")
async def create_api_key(user: User = Depends(get_current_user), name: str = "My API Key"):
    # Generate key (32-byte random, base64-encoded)
    api_key = f"sdlc_live_{base64.b64encode(os.urandom(32)).decode()}"

    # Hash key (store hash, not plaintext)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Store in database
    await store_api_key(
        user_id=user.id,
        name=name,
        key_hash=key_hash,
        created_at=datetime.utcnow()
    )

    # Return key ONCE (user must save it)
    return {"api_key": api_key, "warning": "Save this key. You won't see it again."}

# API Key Authentication
@app.get("/api/v1/projects")
async def list_projects(api_key: str = Header(None, alias="X-API-Key")):
    # Hash incoming key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Lookup in database
    api_key_record = await get_api_key_by_hash(key_hash)
    if not api_key_record:
        raise HTTPException(401, "Invalid API key")

    # Get user
    user = await get_user(api_key_record.user_id)
    return await get_projects(user)
```

**Benefits**:
- ✅ **No expiry**: Ideal for CI/CD (GitHub Actions, Jenkins)
- ✅ **Revocable**: User can revoke from dashboard
- ✅ **Auditable**: Track which key accessed which resource

**Example (GitHub Actions)**:
```yaml
# .github/workflows/gate-check.yml
name: Gate G1 Check
on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Gate G1
        run: |
          curl -X POST https://api.sdlc-orchestrator.com/api/v1/gates/G1/validate \
            -H "X-API-Key: ${{ secrets.SDLC_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"project_id": "proj_123", "evidence": [...]}'
```

---

## Consequences

### Positive

**1. Security**
- ✅ **Short-lived access tokens** (1 hour) limit damage if stolen
- ✅ **MFA mandatory for C-Suite** prevents account takeover
- ✅ **OAuth 2.0** delegates auth to trusted providers (GitHub, Google)
- ✅ **API keys hashed** (SHA-256) prevent plaintext leaks

**2. User Experience**
- ✅ **SSO** = faster onboarding (no sign-up form)
- ✅ **Remember me** = refresh tokens (30 days, no re-login)
- ✅ **Device flow** = secure VS Code/CLI auth (no browser redirect)

**3. Compliance**
- ✅ **SOC 2 Type 2** ready (MFA for privileged accounts)
- ✅ **ISO 27001** ready (password policy, token expiry, audit logs)
- ✅ **GDPR** ready (consent, data portability, right to deletion)

### Negative

**1. Complexity**
- ❌ **Multiple auth methods** (JWT, OAuth, MFA, API keys) increase attack surface
- **Mitigation**: Thorough security testing (OWASP ASVS Level 2)

**2. Token Revocation**
- ❌ **JWT cannot be revoked** until expiry (1 hour window)
- **Mitigation**: Blacklist refresh tokens in Redis (rare operation)

**3. Clock Skew (TOTP)**
- ❌ **TOTP requires synchronized clocks** (server + user device)
- **Mitigation**: Allow ±30 second window (`valid_window=1`)

---

## Alternatives Considered

### Session Cookies (Rejected)

**Pros**:
- ✅ Instant revocation (delete session from Redis)
- ✅ Smaller payload (32-byte session ID vs 300-byte JWT)

**Cons**:
- ❌ **Stateful**: Requires Redis for every request (latency, cost)
- ❌ **Not microservices-friendly**: Shared session storage
- ❌ **CSRF vulnerability**: Requires CSRF tokens

**Decision**: JWT is better for distributed systems.

### SAML 2.0 (Deferred to Enterprise Tier)

**Pros**:
- ✅ Enterprise SSO (Okta, Azure AD, OneLogin)
- ✅ Attribute-based access control (ABAC)

**Cons**:
- ❌ **Complex setup**: XML signatures, IdP configuration
- ❌ **No developer adoption**: Developers use OAuth (GitHub, Google)

**Decision**: Defer SAML to Enterprise tier (not MVP).

---

## Implementation Plan

### Phase 1: MVP (Week 5-8)
```yaml
Features:
  - JWT access tokens (1 hour expiry)
  - Refresh tokens (30 days expiry)
  - OAuth 2.0 (GitHub, Google, Microsoft)
  - Password auth (bcrypt, 12 rounds)
  - API keys (SHA-256 hashed)

Deferred:
  - MFA (TOTP) - Week 9-10
  - Device flow - Week 11-12
```

### Phase 2: Security (Week 9-10)
```yaml
Features:
  - MFA enrollment (TOTP + QR code)
  - MFA enforcement (C-Suite mandatory)
  - Backup codes (10 one-time codes)
  - Account recovery (email-based)
```

### Phase 3: Enterprise (Year 2)
```yaml
Features:
  - SAML 2.0 integration (Okta, Azure AD)
  - SCIM provisioning (auto-add/remove users)
  - Session policies (IP whitelisting, device fingerprinting)
```

---

## References

- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [OAuth Device Flow RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628)
- [TOTP RFC 6238](https://datatracker.ietf.org/doc/html/rfc6238)
- [API Authentication Best Practices](../05-Legal-Compliance/API-Authentication.md)

---

## Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **CTO** | [CTO Name] | ✅ APPROVED | Nov 13, 2025 |
| **Security Lead** | [Security Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Backend Lead** | [Backend Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Last Updated**: November 13, 2025
**Status**: ✅ ACCEPTED - Binding decision
**Next Review**: Phase 2 (MFA implementation, Week 9)
