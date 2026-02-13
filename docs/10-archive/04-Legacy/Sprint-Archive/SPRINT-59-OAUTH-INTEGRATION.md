# SPRINT-59: OAuth Integration (GitHub + Google)
## Marketing & Growth | Social Authentication

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-59 |
| **Epic** | Marketing & Growth |
| **Duration** | 2 days (Dec 27-28, 2025) |
| **Status** | COMPLETE ✅ |
| **Priority** | P1 Should Have |
| **Dependencies** | Sprint 58 complete |
| **Framework** | SDLC 5.1.2 Universal Framework |

---

## Sprint Goal

Implement OAuth 2.0 social login with GitHub and Google providers to reduce registration friction.

---

## Sprint Objectives

| Day | Focus | Deliverables | Effort |
|-----|-------|--------------|--------|
| Day 1 | Backend OAuth | OAuth service, endpoints, user linking | 8h |
| Day 2 | Frontend Integration | OAuth buttons, callback page, token storage | 6h |

---

## Feature 1: Backend OAuth Service

### OAuth Flow (Authorization Code)

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│  User   │────>│  Frontend   │────>│   Backend   │────>│ Provider│
│         │     │             │     │             │     │(GitHub/ │
│         │     │ /login      │     │ /authorize  │     │ Google) │
└─────────┘     └─────────────┘     └─────────────┘     └─────────┘
     │                                     │                  │
     │<──────────────────────────────────────────────────────│
     │              Redirect to provider login               │
     │                                     │                  │
     │──────────────────────────────────────────────────────>│
     │                   User authorizes                     │
     │                                     │                  │
     │<──────────────────────────────────────────────────────│
     │         Redirect with code to /callback               │
     │                                     │                  │
     │─────────────────────────────────────>                  │
     │                                     │                  │
     │                                     │<─────────────────│
     │                                     │  Exchange code   │
     │                                     │  for tokens      │
     │<────────────────────────────────────│                  │
     │         JWT tokens returned                           │
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `services/oauth_service.py` | CREATE | OAuth provider integration |
| `api/routes/auth.py` | MODIFY | Add OAuth endpoints |
| `schemas/auth.py` | MODIFY | Add OAuth schemas |
| `core/config.py` | MODIFY | Add OAuth settings |

### OAuth Service (`oauth_service.py`)

```python
class OAuthService:
    """
    OAuth 2.0 service for GitHub and Google integration.

    Methods:
    - get_github_auth_url(state, redirect_uri) -> str
    - exchange_github_code(code, redirect_uri) -> OAuthTokens
    - get_github_user_info(access_token) -> OAuthUserInfo

    - get_google_auth_url(state, redirect_uri, code_verifier) -> str
    - exchange_google_code(code, redirect_uri, code_verifier) -> OAuthTokens
    - get_google_user_info(access_token) -> OAuthUserInfo
    """
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/oauth/{provider}/authorize` | Get OAuth authorization URL |
| POST | `/auth/oauth/{provider}/callback` | Handle OAuth callback |
| POST | `/auth/oauth/{provider}/link` | Link OAuth to existing account |
| DELETE | `/auth/oauth/{provider}/unlink` | Unlink OAuth from account |

### OAuth State Management

```python
# Store state in Redis with 10-minute expiration
redis_key = f"oauth_state:{state}"
redis_data = {
    "provider": provider,
    "redirect_uri": redirect_uri,
    "code_verifier": code_verifier,  # For Google PKCE
    "created_at": datetime.utcnow().isoformat()
}
await redis.setex(redis_key, 600, json.dumps(redis_data))
```

---

## Feature 2: Frontend OAuth Integration

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `app/login/page.tsx` | MODIFY | Enable OAuth buttons |
| `app/register/page.tsx` | MODIFY | Add OAuth signup |
| `app/auth/callback/page.tsx` | CREATE | Handle OAuth callback |
| `lib/api.ts` | MODIFY | Add OAuth API functions |

### OAuth Buttons Component

```tsx
// Enable GitHub and Google buttons in login/register pages
<Button onClick={() => handleOAuthLogin("github")}>
  <GitHubIcon /> Continue with GitHub
</Button>

<Button onClick={() => handleOAuthLogin("google")}>
  <GoogleIcon /> Continue with Google
</Button>
```

### OAuth Callback Page (`app/auth/callback/page.tsx`)

```tsx
export default function OAuthCallbackPage() {
  // 1. Extract code and state from URL
  // 2. Call backend /auth/oauth/{provider}/callback
  // 3. Store tokens in localStorage
  // 4. Redirect to dashboard or original page
}
```

---

## Feature 3: User Account Linking

### Use Cases

1. **New User via OAuth**: Create new user, link OAuth account
2. **Existing User via OAuth**: Match by email, link OAuth account
3. **Manual Link**: Logged-in user links additional OAuth provider
4. **Unlink**: Remove OAuth provider from account

### Database Impact

Uses existing `oauth_accounts` table:

```sql
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- 'github', 'google'
    provider_account_id VARCHAR(255) NOT NULL,
    access_token VARCHAR(512),
    refresh_token VARCHAR(512),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider, provider_account_id)
);
```

---

## Configuration

### Environment Variables

```env
# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### OAuth Redirect URIs

| Provider | Development | Production |
|----------|-------------|------------|
| GitHub | `http://localhost:3000/auth/callback` | `https://sdlc.nhatquangholding.com/auth/callback` |
| Google | `http://localhost:3000/auth/callback` | `https://sdlc.nhatquangholding.com/auth/callback` |

---

## Security Considerations

### GitHub OAuth

- Scopes: `read:user user:email`
- State parameter for CSRF protection
- Verify primary email is verified

### Google OAuth

- Scopes: `openid email profile`
- PKCE flow (S256 code challenge)
- Verify email is verified
- State parameter for CSRF protection

### Token Storage

- OAuth tokens encrypted in database (AES-256)
- Never log or expose OAuth tokens
- Refresh tokens rotated on use

---

## Success Metrics

| Metric | Target |
|--------|--------|
| OAuth login success rate | 95%+ |
| OAuth flow completion time | <10s |
| Account linking accuracy | 100% |
| Security compliance | OWASP ASVS L2 |

---

## Files Summary

| Category | Files | Lines (Est.) |
|----------|-------|--------------|
| Backend Service | 1 | ~400 |
| Backend Endpoints | 1 (modify) | ~200 |
| Backend Schemas | 1 (modify) | ~50 |
| Frontend Pages | 2 | ~300 |
| Frontend API | 1 (modify) | ~80 |
| Tests | 2 | ~300 |
| **Total** | **8** | **~1,330** |

---

## Deliverables Checklist

### Backend

- [x] OAuth service with GitHub provider
- [x] OAuth service with Google provider (PKCE)
- [x] GET `/auth/oauth/{provider}/authorize` endpoint
- [x] POST `/auth/oauth/{provider}/callback` endpoint
- [x] State validation (base64-encoded JSON state)
- [x] User creation/linking logic
- [x] Unit tests for OAuth service

### Frontend

- [x] Enable OAuth buttons in login page
- [x] Enable OAuth buttons in register page
- [x] OAuth callback page
- [x] API client OAuth functions
- [x] Error handling and user feedback

### Configuration

- [x] Add OAuth environment variables
- [x] Update config.py with OAuth settings
- [x] Document OAuth setup in README

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Last Updated** | December 27, 2025 |
| **Owner** | Backend Lead |
| **Approved By** | CTO (Pending) |
