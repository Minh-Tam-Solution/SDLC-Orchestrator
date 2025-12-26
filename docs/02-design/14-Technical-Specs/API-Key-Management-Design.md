# API Key Management Design

**Version**: 1.0.0
**Date**: December 26, 2025
**Status**: DRAFT - Pending CTO Approval
**Sprint**: Sprint 52B - VS Code Extension Authentication
**Author**: Claude AI + CTO Review

---

## 1. Problem Statement

### Current State
- VS Code extension chạy trên Remote SSH server không thể kết nối đến `https://sdlc.nhatquangholding.com` do firewall/network restrictions
- Extension chỉ có thể kết nối qua `localhost:8300` khi chạy trên cùng server với backend
- Không có cách để user authenticate extension từ máy khác

### User Pain Points
1. **Remote Development**: User dùng VS Code Remote SSH không thể login vì server không có internet access ra ngoài
2. **No API Token UI**: Settings page không có nơi để generate/manage API tokens
3. **Manual Configuration**: User phải tự lấy JWT token từ browser và paste vào extension

### Reference: How Claude Code Does It
- Claude Code extension cho phép login qua:
  1. **Browser OAuth**: Mở browser trên máy local để authenticate
  2. **API Key**: Nhập API key trực tiếp (generated từ console.anthropic.com)
- API Key approach phù hợp cho Remote SSH scenarios

---

## 2. Solution Design

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Workflow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User logs in to Web Dashboard (https://sdlc.nhatquangholding.com)
│                          │                                       │
│                          ▼                                       │
│  2. Navigate to Settings → API Keys                             │
│                          │                                       │
│                          ▼                                       │
│  3. Click "Generate New API Key"                                │
│     - Enter name: "VS Code Extension"                           │
│     - Optional: Set expiry (90 days)                            │
│                          │                                       │
│                          ▼                                       │
│  4. Copy API Key (shown ONCE)                                   │
│     sdlc_live_abc123def456...                                   │
│                          │                                       │
│                          ▼                                       │
│  5. In VS Code Extension:                                       │
│     - Command: "SDLC: Login"                                    │
│     - Select: "API Token"                                       │
│     - Paste: sdlc_live_abc123def456...                          │
│                          │                                       │
│                          ▼                                       │
│  6. Extension authenticated! ✓                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Model

**Existing Table: `api_keys`** (already in database schema)

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,           -- "VS Code Extension"
    key_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash (64 chars)
    prefix VARCHAR(20) NOT NULL,          -- "sdlc_live_abc..." for display
    last_used_at TIMESTAMP,               -- Track usage
    expires_at TIMESTAMP,                 -- Optional expiry
    is_active BOOLEAN DEFAULT TRUE,       -- Revocation flag
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
```

### 2.3 API Key Format

```
sdlc_live_<43-character-base64-urlsafe>

Example: sdlc_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789_-AB
         ├────────┤├──────────────────────────────────────────┤
         Prefix    Random 32 bytes (base64-urlsafe encoded)

Total length: 10 + 43 = 53 characters
```

**Security Properties:**
- 256-bit entropy (32 random bytes)
- URL-safe characters only (A-Z, a-z, 0-9, -, _)
- Prefix identifies key type (`sdlc_live_` = production)
- SHA-256 hash stored in database (not plaintext)

---

## 3. API Endpoints

### 3.1 Create API Key

```http
POST /api/v1/api-keys
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "name": "VS Code Extension",
    "expires_in_days": 90  // Optional, null = never expires
}
```

**Response (201 Created):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "VS Code Extension",
    "api_key": "sdlc_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789_-AB",
    "prefix": "sdlc_live_aBcDeFgHi...",
    "expires_at": "2026-03-26T00:00:00Z",
    "created_at": "2025-12-26T10:00:00Z"
}
```

**Important:** `api_key` is shown ONCE. User must save it immediately.

### 3.2 List API Keys

```http
GET /api/v1/api-keys
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "VS Code Extension",
        "prefix": "sdlc_live_aBcDeFgHi...",
        "last_used_at": "2025-12-26T10:30:00Z",
        "expires_at": "2026-03-26T00:00:00Z",
        "is_active": true,
        "created_at": "2025-12-26T10:00:00Z"
    }
]
```

**Note:** Actual `api_key` is NOT returned (only shown on creation).

### 3.3 Revoke API Key

```http
DELETE /api/v1/api-keys/{key_id}
Authorization: Bearer <jwt_token>
```

**Response (204 No Content)**

---

## 4. Frontend UI Design

### 4.1 Settings Page - API Keys Section

```
┌─────────────────────────────────────────────────────────────────┐
│ API Keys                                                         │
│ Generate personal access tokens for VS Code extension and CLI    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Your API Keys                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ VS Code Extension                                           │ │
│ │ sdlc_live_aBcDeFgHi...                                     │ │
│ │ Last used: 5 minutes ago • Expires: Mar 26, 2026           │ │
│ │                                              [Revoke]       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CI/CD Pipeline                                              │ │
│ │ sdlc_live_xYzAbCdEfG...                                    │ │
│ │ Last used: Never • Never expires                           │ │
│ │                                              [Revoke]       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                              [+ Generate New API Key]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Generate API Key Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│ Generate New API Key                                       [X]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Name                                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ VS Code Extension                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Expiration                                                       │
│ ○ 30 days                                                        │
│ ● 90 days (Recommended)                                          │
│ ○ 1 year                                                         │
│ ○ Never expires                                                  │
│                                                                  │
│              [Cancel]                    [Generate API Key]      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 API Key Created Success Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│ ✓ API Key Created Successfully                             [X]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ⚠️ Make sure to copy your API key now.                          │
│    You won't be able to see it again!                           │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ sdlc_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789_-AB        │ │
│ │                                                  [Copy]     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ How to use in VS Code:                                           │
│ 1. Open VS Code Command Palette (Ctrl+Shift+P)                  │
│ 2. Run "SDLC: Login to SDLC Orchestrator"                       │
│ 3. Select "API Token"                                           │
│ 4. Paste your API key                                           │
│                                                                  │
│                                        [Done, I've saved my key] │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Backend Authentication Flow

### 5.1 API Key Validation in Auth Dependency

```python
# app/api/dependencies.py

async def get_current_user_from_token_or_api_key(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Authenticate user via JWT token OR API key.

    Header formats:
        - JWT: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        - API Key: Authorization: Bearer sdlc_live_abc123...
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization[7:]  # Remove "Bearer " prefix

    # Check if it's an API key (starts with "sdlc_live_")
    if token.startswith("sdlc_live_"):
        return await validate_api_key(token, db)
    else:
        # It's a JWT token
        return await validate_jwt_token(token, db)


async def validate_api_key(api_key: str, db: AsyncSession) -> User:
    """Validate API key and return user."""
    key_hash = hash_api_key(api_key)

    result = await db.execute(
        select(APIKey)
        .where(APIKey.key_hash == key_hash, APIKey.is_active == True)
        .options(selectinload(APIKey.user))
    )
    db_key = result.scalar_one_or_none()

    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Check expiry
    if db_key.expires_at and db_key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")

    # Update last_used_at
    db_key.last_used_at = datetime.utcnow()
    await db.commit()

    return db_key.user
```

---

## 6. Security Considerations

### 6.1 API Key Storage
- **Database**: Store SHA-256 hash only (not plaintext)
- **Frontend**: Never log API key, clear from memory after display
- **Transport**: HTTPS only (TLS 1.3)

### 6.2 API Key Lifecycle
- **Creation**: Generate 256-bit random key, show ONCE
- **Usage**: Hash + compare on each request
- **Expiry**: Optional expiry date (default: 90 days recommended)
- **Revocation**: Immediate effect via `is_active = false`

### 6.3 Rate Limiting
- API key creation: 10 keys per user max
- API key usage: Same rate limits as JWT tokens

### 6.4 Audit Logging
- Log API key creation (user_id, key_prefix, expires_at)
- Log API key usage (user_id, key_prefix, endpoint, timestamp)
- Log API key revocation (user_id, key_prefix, revoked_by)

---

## 7. Implementation Plan

### Phase 1: Backend API (Day 1)
- [x] Create `api_keys.py` router
- [ ] Register router in `main.py`
- [ ] Update auth dependency to support API keys
- [ ] Add unit tests

### Phase 2: Frontend UI (Day 2)
- [ ] Add API Keys section to Settings page
- [ ] Create Generate API Key dialog
- [ ] Create API Key Created success dialog
- [ ] Add revoke confirmation dialog

### Phase 3: VS Code Extension (Day 2)
- [ ] Already supports "API Token" login option
- [ ] Test with real API key
- [ ] Update documentation

### Phase 4: Testing & Documentation (Day 3)
- [ ] E2E test: Generate key → Use in extension
- [ ] Update README with API key instructions
- [ ] Update VS Code extension README

---

## 8. Acceptance Criteria

1. **Backend**
   - [ ] POST /api-keys creates new key, returns full key ONCE
   - [ ] GET /api-keys lists keys (without actual key)
   - [ ] DELETE /api-keys/{id} revokes key
   - [ ] API key authentication works same as JWT

2. **Frontend**
   - [ ] Settings page shows API Keys section
   - [ ] Can generate new API key with name + expiry
   - [ ] Copy button works
   - [ ] Can revoke existing keys

3. **VS Code Extension**
   - [ ] Can login with API key (existing "API Token" option)
   - [ ] Works on Remote SSH server

4. **Security**
   - [ ] API key stored as SHA-256 hash only
   - [ ] Key shown only once on creation
   - [ ] Expired keys are rejected
   - [ ] Revoked keys are rejected immediately

---

## 9. References

- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Anthropic API Keys](https://console.anthropic.com/settings/keys)
- [OWASP API Security - Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/)

---

**Approval Required:**
- [ ] CTO Review
- [ ] Security Lead Review
