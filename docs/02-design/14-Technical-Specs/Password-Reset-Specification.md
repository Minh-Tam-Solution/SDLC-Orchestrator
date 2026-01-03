# Password Reset Feature Specification

## Overview

| Field | Value |
|-------|-------|
| **Feature** | Password Reset (Forgot Password) |
| **Sprint** | 60 - i18n Localization |
| **Status** | ✅ COMPLETE |
| **Author** | AI Assistant (Claude) |
| **Date** | December 29, 2025 |
| **Completion Date** | December 30, 2025 |
| **SDLC Stage** | 03-BUILD |
| **Production URL** | https://sdlc.nhatquangholding.com/forgot-password |

## 1. Business Requirements

### 1.1 User Story

> As a user who has forgotten my password, I want to reset it securely via email so that I can regain access to my account.

### 1.2 Acceptance Criteria

- [x] User can request password reset from login page
- [x] Reset email sent within 30 seconds (background thread)
- [x] Reset link expires after 1 hour
- [x] Reset link is one-time use only
- [x] User can set new password meeting security requirements
- [x] All reset attempts are audit logged

---

## 2. Technical Design

### 2.1 System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PASSWORD RESET FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User clicks "Forgot Password" on Login Page                │
│                 ↓                                               │
│  2. Frontend: POST /api/v1/auth/forgot-password                │
│     Body: { "email": "user@example.com" }                      │
│                 ↓                                               │
│  3. Backend:                                                    │
│     a. Check if email exists in database                       │
│     b. Generate secure reset token (UUID + timestamp)          │
│     c. Hash token and store in password_reset_tokens table     │
│     d. Send email with reset link                              │
│     e. Return 200 OK (always, for security)                    │
│                 ↓                                               │
│  4. User clicks reset link in email                            │
│     URL: /reset-password?token=xxx                             │
│                 ↓                                               │
│  5. Frontend: GET /api/v1/auth/verify-reset-token?token=xxx    │
│     (Optional: validate token before showing form)             │
│                 ↓                                               │
│  6. User enters new password                                   │
│                 ↓                                               │
│  7. Frontend: POST /api/v1/auth/reset-password                 │
│     Body: { "token": "xxx", "password": "NewSecure123!" }      │
│                 ↓                                               │
│  8. Backend:                                                    │
│     a. Validate token (exists, not expired, not used)          │
│     b. Hash new password with bcrypt                           │
│     c. Update user.password_hash                               │
│     d. Mark token as used                                      │
│     e. Revoke all refresh tokens (logout all sessions)         │
│     f. Audit log the password change                           │
│     g. Return 200 OK                                           │
│                 ↓                                               │
│  9. Redirect user to login page with success message           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Database Schema

```sql
-- New table for password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL,  -- SHA256 hash of token
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,  -- NULL if not used
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent VARCHAR(512)
);

-- Indexes
CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX ix_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);
CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);
```

### 2.3 API Endpoints

#### 2.3.1 POST /api/v1/auth/forgot-password

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK - Always):**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent.",
  "email_sent": true
}
```

**Security Notes:**
- Always returns 200 to prevent email enumeration attacks
- Rate limited: 3 requests per email per hour
- Rate limited: 10 requests per IP per hour

#### 2.3.2 GET /api/v1/auth/verify-reset-token

**Query Parameters:**
- `token`: Reset token from email

**Response (200 OK):**
```json
{
  "valid": true,
  "email": "u***@example.com",  // Masked email for confirmation
  "expires_in_minutes": 45
}
```

**Response (400 Bad Request):**
```json
{
  "valid": false,
  "error": "Token is invalid or has expired"
}
```

#### 2.3.3 POST /api/v1/auth/reset-password

**Request:**
```json
{
  "token": "reset-token-from-email",
  "password": "NewSecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully. Please login with your new password."
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Token is invalid or has expired"
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": "Password must be at least 12 characters"
}
```

### 2.4 Email Template

**Subject:** Reset your SDLC Orchestrator password

**Body:**
```html
<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
  <h1 style="color: #1a1a1a;">Reset Your Password</h1>

  <p>Hello,</p>

  <p>We received a request to reset your password for your SDLC Orchestrator account.</p>

  <p>Click the button below to reset your password:</p>

  <a href="{reset_url}" style="display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0;">
    Reset Password
  </a>

  <p style="color: #666; font-size: 14px;">
    This link will expire in 1 hour. If you didn't request this, you can safely ignore this email.
  </p>

  <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

  <p style="color: #999; font-size: 12px;">
    SDLC Orchestrator<br>
    This is an automated message.
  </p>
</div>
```

---

## 3. Security Considerations

### 3.1 Token Generation
- Use `secrets.token_urlsafe(32)` for cryptographically secure tokens
- Store only SHA256 hash of token in database
- Token includes timestamp to prevent replay

### 3.2 Token Expiration
- Tokens expire after 1 hour
- Tokens are single-use (marked as used after successful reset)
- Background job cleans up expired tokens daily

### 3.3 Rate Limiting
| Limit | Value |
|-------|-------|
| Per email | 3 requests/hour |
| Per IP | 10 requests/hour |
| Per user (reset attempts) | 5/day |

### 3.4 Audit Logging

All actions are logged:
- `PASSWORD_RESET_REQUESTED`: Email sent
- `PASSWORD_RESET_TOKEN_VERIFIED`: Token validated
- `PASSWORD_RESET_COMPLETED`: Password changed
- `PASSWORD_RESET_FAILED`: Invalid token or other error

---

## 4. Frontend Implementation

### 4.1 Pages

#### /forgot-password
- Email input form
- Submit button
- Link back to login
- Success message after submission

#### /reset-password?token=xxx
- Password input (new password)
- Confirm password input
- Password strength indicator
- Submit button
- Validation messages

### 4.2 Translations (i18n)

```json
{
  "auth": {
    "forgotPassword": {
      "title": "Forgot Password",
      "description": "Enter your email address and we'll send you a link to reset your password.",
      "emailLabel": "Email address",
      "emailPlaceholder": "Enter your email",
      "submitButton": "Send Reset Link",
      "backToLogin": "Back to Login",
      "successMessage": "If an account exists with this email, you will receive a password reset link shortly.",
      "errorTooManyAttempts": "Too many attempts. Please try again later."
    },
    "resetPassword": {
      "title": "Reset Password",
      "description": "Enter your new password below.",
      "passwordLabel": "New Password",
      "confirmPasswordLabel": "Confirm Password",
      "submitButton": "Reset Password",
      "successMessage": "Your password has been reset successfully.",
      "errorInvalidToken": "This reset link is invalid or has expired.",
      "errorPasswordMismatch": "Passwords do not match.",
      "passwordRequirements": "Password must be at least 12 characters."
    }
  }
}
```

---

## 5. Implementation Plan

### 5.1 Backend Tasks ✅ COMPLETE

1. ✅ Create Alembic migration for `password_reset_tokens` table (`s60_password_reset.py`)
2. ✅ Create Pydantic schemas for request/response (`app/schemas/auth.py`)
3. ✅ Implement `forgot-password` endpoint (`app/api/routes/auth.py`)
4. ✅ Implement `verify-reset-token` endpoint (`app/api/routes/auth.py`)
5. ✅ Implement `reset-password` endpoint (`app/api/routes/auth.py`)
6. ✅ Add HTML email template for password reset (inline in auth.py)
7. ✅ Add background thread email sending (non-blocking)
8. ✅ Timezone handling for PostgreSQL Asia/Ho_Chi_Minh

### 5.2 Frontend Tasks ✅ COMPLETE

1. ✅ Create `/forgot-password` page (`frontend/landing/src/app/forgot-password/page.tsx`)
2. ✅ Create `/reset-password` page (`frontend/landing/src/app/reset-password/page.tsx`)
3. ✅ Add i18n translations (EN + VI in `messages/en.json`, `messages/vi.json`)
4. ✅ Add form validation with Zod
5. ✅ Add success/error states with loading indicators
6. ✅ API client functions (`frontend/landing/src/lib/api.ts`)

### 5.3 Actual Effort

| Task | Estimate | Actual |
|------|----------|--------|
| Backend API | 2-3 hours | 4 hours |
| Frontend Pages | 2-3 hours | 3 hours |
| Testing & Debugging | 1-2 hours | 3 hours |
| **Total** | 5-8 hours | **10 hours** |

**Note**: Extra time spent on timezone handling (PostgreSQL Asia/Ho_Chi_Minh vs UTC) and background email threading.

---

## 6. Testing Plan

### 6.1 Unit Tests

- Token generation is cryptographically secure
- Token hashing is consistent
- Expired tokens are rejected
- Used tokens are rejected
- Rate limiting works correctly

### 6.2 Integration Tests

- Email is sent when user exists
- Email is NOT sent when user doesn't exist (but 200 returned)
- Password is updated on valid reset
- All sessions are logged out after reset

### 6.3 E2E Tests

- Complete flow: request → email → reset → login

---

## 7. Rollout Plan

1. **Phase 1**: Deploy to staging environment
2. **Phase 2**: Internal testing with team emails
3. **Phase 3**: Deploy to production
4. **Phase 4**: Monitor metrics (success rate, email delivery)

---

## 8. References

- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- [ADR-007: Authentication & Security](../01-ADRs/ADR-007-AI-Context-Engine-Ollama-Integration.md)
- [API Specification v3.1.0](../../01-planning/05-API-Design/API-Specification.md)

---

## 9. Implementation Details (Post-Completion)

### 9.1 Files Created/Modified

**Backend:**
| File | Lines | Purpose |
|------|-------|---------|
| `backend/alembic/versions/s60_password_reset.py` | ~80 | Database migration |
| `backend/app/models/user.py` | +50 | PasswordResetToken model |
| `backend/app/schemas/auth.py` | +40 | Request/response schemas |
| `backend/app/api/routes/auth.py` | +300 | 3 API endpoints |

**Frontend:**
| File | Lines | Purpose |
|------|-------|---------|
| `frontend/landing/src/app/forgot-password/page.tsx` | 194 | Forgot password page |
| `frontend/landing/src/app/reset-password/page.tsx` | ~250 | Reset password page |
| `frontend/landing/src/lib/api.ts` | +50 | API client functions |
| `frontend/landing/src/messages/en.json` | +30 | English translations |
| `frontend/landing/src/messages/vi.json` | +30 | Vietnamese translations |

### 9.2 Technical Decisions

**1. Token Storage:**
- SHA256 hash stored in database (not plain token)
- Raw token sent via email URL
- Prevents token theft from database

**2. Timezone Handling:**
- PostgreSQL timezone: `Asia/Ho_Chi_Minh` (UTC+7)
- Solution: Add 7-hour offset to `expires_at` when creating token
- `is_expired` property handles offset-aware comparison

**3. Email Sending:**
- Background thread (non-blocking API response)
- SMTP with TLS (Gmail compatible)
- HTML email template with CTA button

**4. Security Measures:**
- Always return 200 OK (prevent email enumeration)
- One-time use tokens (marked as used after reset)
- All sessions revoked after password change
- Audit logging for all actions

### 9.3 Known Issues & Workarounds

| Issue | Workaround | Status |
|-------|------------|--------|
| PostgreSQL timezone mismatch | Add 7h offset to expires_at | ✅ Fixed |
| Email blocking API response | Background thread sending | ✅ Fixed |
| Token expired immediately | Fixed timezone comparison in is_expired | ✅ Fixed |

### 9.4 Production URLs

| Environment | URL |
|-------------|-----|
| Forgot Password | https://sdlc.nhatquangholding.com/forgot-password |
| Reset Password | https://sdlc.nhatquangholding.com/reset-password?token=xxx |
| API Endpoint | https://sdlc.nhatquangholding.com/api/v1/auth/forgot-password |

---

**Document Status:** ✅ COMPLETE
**Reviewed By:** CTO
**Completion Date:** December 30, 2025
**Production Status:** DEPLOYED
