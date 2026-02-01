# Sprint 128: Team Invitation System

**Sprint Duration**: Jan 30 - Feb 7, 2026 (Pre-work + 2 weeks)
**Sprint Goal**: Implement secure team invitation system with email delivery
**Story Points**: 5 SP (Delivered: 11 SP)
**Team**: Backend (2 FTE), Frontend (1 FTE), DevOps (0.5 FTE)
**Priority**: P0 (BLOCKING for March 1 launch)

---

## 🎉 Sprint Status: BACKEND COMPLETE ✅

**Backend Completion**: January 31, 2026, 11:45 AM
**Tests**: 48/48 PASSED (100%)
**Coverage**: 97% (invitation_service.py)
**Security**: OWASP ASVS L2 compliant
**CTO Approval**: ✅ PRODUCTION READY

---

## Executive Summary

Sprint 128 implements the **Team Invitation System**, closing a critical P0 gap identified in the onboarding flow review. This replaces the insecure "direct member addition via email" pattern with a consent-based invitation flow using cryptographically secure tokens.

**Strategic Context**:
- **Problem**: Current team management allows admins to add members by email without consent (security + compliance issue)
- **Solution**: Invitation-only flow with magic links, token hashing, and audit trails
- **Impact**: Enables GDPR-compliant team onboarding, blocks launch-critical gap

**Success Criteria**:
- ✅ Invitation API responds <2s p95
- ✅ Email accepted by provider <10s p95
- ✅ Token hashing verified (no raw tokens in DB)
- ✅ 48 tests passing (exceeds 15 target)

---

## Sprint Backlog

### Week 1: Backend + Email (3 SP, 3 days) ✅ COMPLETE

#### Day 1-2: Database + Core APIs (2 SP) ✅ COMPLETE (Jan 30-31)

**Tasks**:
- [x] **DB-001**: Create Alembic migration `s128_001_team_invitations.py` ✅
  - Remove CHECK constraint on `resend_count` (application-layer enforcement)
  - Add token hashing support (`invitation_token_hash` VARCHAR(64))
  - Add audit fields (`ip_address`, `user_agent`)
  - Add unique constraint on `(team_id, invited_email)` WHERE status='pending'
- [x] **MODEL-001**: Create `TeamInvitation` SQLAlchemy model ✅
  - Implement `generate_token()` method (secrets.token_urlsafe(32))
  - Implement `hash_token()` method (SHA256)
  - Implement `verify_token()` method (constant-time comparison)
- [x] **SCHEMA-001**: Create Pydantic schemas ✅
  - `InvitationCreate`: email, role (validation: email format, role enum)
  - `InvitationResponse`: id, email, role, status, expires_at, created_at
  - `InvitationAccept`: token (validation: 43-char base64url)
- [x] **SERVICE-001**: Implement `invitation_service.py` ✅
  - `create_invitation()`: Generate token, hash, store, return unhashed token
  - `get_invitation_by_token()`: Hash input, lookup by hash
  - `accept_invitation()`: Verify token, create team member, update status
  - `decline_invitation()`: Update status to 'declined'
  - `resend_invitation()`: Check rate limit (config-based), regenerate token
- [x] **API-001**: Create invitation endpoints in `routes/invitations.py` ✅
  - `POST /teams/{team_id}/invitations`: Send invitation (with RBAC enforcement)
  - `GET /invitations/{token}`: Get invitation details (public endpoint)
  - `POST /invitations/{token}/accept`: Accept invitation (creates team member)
  - `POST /invitations/{token}/decline`: Decline invitation
  - `POST /invitations/{invitation_id}/resend`: Resend invitation (admin only)
- [x] **TEST-001**: Write 31 unit tests ✅ (exceeds 10 target)
  - Token generation uniqueness (100 iterations)
  - Token hashing correctness (SHA256 verification)
  - Constant-time comparison (timing attack protection)
  - Concurrent accept race condition (only one succeeds)
  - Rate limiting enforcement (50/hour per team)

**Acceptance Criteria**:
- All endpoints return correct HTTP status codes
- Token hashing verified (no raw tokens in DB)
- Idempotency key prevents duplicate sends
- Rate limiting enforced via config (no DB constraints)

---

#### Day 3: Email Service + Security (1 SP) ✅ COMPLETE (Jan 31)

**Tasks**:
- [x] **EMAIL-001**: Implement `email_service.py` ✅
  - Gmail SMTP integration (App Password from secrets)
  - Email template rendering (HTML templates with XSS escaping)
  - Transactional email pattern (send AFTER DB commit)
  - Error handling with logging (async failures don't block request)
- [x] **TEMPLATE-001**: Create invitation email template ✅
  - Subject: "You're invited to join {team_name} on SDLC Orchestrator"
  - Body: Magic link with token, team info, expiry warning
  - Footer: Company branding, XSS-safe HTML escaping
- [x] **TEMPLATE-002**: Create confirmation email template ✅
  - Subject: "Welcome to {team_name}!"
  - Body: Team details, next steps, support links
- [x] **JOB-001**: Email sending integrated into API ✅
  - Synchronous send after DB commit
  - Error handling (log failures, don't fail request)
  - Admin can resend if email fails
- [x] **SECURITY-001**: Implement rate limiting ✅
  - Redis-based rate limiter (sliding window)
  - Per-team limit: 50 invitations/hour
  - Per-email limit: 3 invitations/day (prevent spam)
  - Resend cooldown: 5 minutes
- [x] **SECURITY-002**: Implement token security ✅
  - Token hashing: SHA256 before storage
  - One-time use: Status check prevents replay
  - Constant-time comparison: hmac.compare_digest()
- [x] **TEST-002**: Write 17 security tests ✅ (exceeds 5 target)
  - Token enumeration protection (404 for invalid tokens)
  - Replay attack prevention (second use returns 409)
  - Rate limiting bypass attempts (returns 429)
  - XSS prevention in email templates (HTML escaping)
  - Timing attack prevention (constant-time comparison verified)
  - Token randomness verification (entropy + uniqueness tests)

**Acceptance Criteria**: ✅ ALL MET
- Email delivered within 10s (p95) ✅
- Token hashing verified (SHA256 in DB) ✅
- Rate limiting enforced (50/hour per team) ✅
- All 17 security tests passing ✅

---

### Week 2: Frontend + Testing (2 SP, 2 days)

#### Day 4: Frontend UI (1 SP)

**Tasks**:
- [ ] **UI-001**: Create `InviteMemberModal.tsx`
  - Form: Email input (validation), role selector (dropdown)
  - Submit button (disabled during send)
  - Error handling (display validation errors)
  - Success toast ("Invitation sent to {email}")
- [ ] **UI-002**: Create `AcceptInvitationPage.tsx`
  - Fetch invitation details by token (from URL query param)
  - Display team info, role, inviter name
  - Actions: Accept (green button), Decline (red button)
  - Loading state (skeleton loader)
  - Error states: Expired, invalid token, already accepted
- [ ] **HOOK-001**: Create `useInvitations.ts` (React Query)
  - `useSendInvitation`: POST /teams/{id}/invitations
  - `useGetInvitation`: GET /invitations/{token}
  - `useAcceptInvitation`: POST /invitations/{token}/accept
  - `useDeclineInvitation`: POST /invitations/{token}/decline
  - Optimistic updates (update cache before API response)
- [ ] **INTEGRATION-001**: Add "Invite Member" button to team settings
  - Location: TeamMembersCard.tsx (next to member list)
  - Icon: UserPlus
  - Opens InviteMemberModal on click
- [ ] **ROUTE-001**: Add invitation route
  - Path: `/invitations/accept?token={token}`
  - Component: AcceptInvitationPage
  - Public route (no auth required)
- [ ] **TEST-003**: Write 8 component tests
  - InviteMemberModal renders correctly
  - Form validation (email format, required fields)
  - Submit button disabled during send
  - Error messages displayed correctly
  - AcceptInvitationPage renders invitation details
  - Accept button calls API correctly
  - Decline button calls API correctly
  - Loading/error states render correctly

**Acceptance Criteria**:
- UI matches design mockups
- Form validation works correctly
- Error messages are user-friendly
- All component tests passing

---

#### Day 5: E2E Testing + Documentation (1 SP)

**Tasks**:
- [ ] **E2E-001**: Write end-to-end test: Happy path
  - Admin sends invitation → Email delivered → User clicks link → Accepts → Member created
  - Assertions: DB record created, user has team access, email sent
- [ ] **E2E-002**: Write end-to-end test: Decline path
  - Admin sends invitation → User clicks link → Declines → Member NOT created
  - Assertions: DB status='declined', user does NOT have team access
- [ ] **E2E-003**: Write end-to-end test: Expired invitation
  - Admin sends invitation → Wait 7 days → User clicks link → Error shown
  - Assertions: API returns 400, error message "Invitation expired"
- [ ] **E2E-004**: Write end-to-end test: Invalid token
  - User visits `/invitations/accept?token=invalid` → 404 error
  - Assertions: API returns 404, error message "Invitation not found"
- [ ] **E2E-005**: Write end-to-end test: Concurrent accept
  - Admin sends invitation → 2 users click link simultaneously → Only one succeeds
  - Assertions: DB has one member, second request returns 409
- [ ] **DOC-001**: Update OpenAPI spec
  - Add invitation endpoints with request/response examples
  - Add error codes documentation (400, 404, 409, 429)
- [ ] **DOC-002**: Write user guide
  - How to invite team members (admin perspective)
  - How to accept invitations (user perspective)
  - Troubleshooting: Expired links, email not received, etc.
- [ ] **DOC-003**: Update API changelog
  - Add breaking change notice (POST /teams/{id}/members deprecated)
  - Migration guide for API consumers

**Acceptance Criteria**:
- 15 integration tests passing (10 unit + 5 E2E)
- OpenAPI spec updated with invitation endpoints
- User guide published to docs site
- API changelog updated with deprecation notice

---

## Technical Architecture

### Database Schema

```sql
CREATE TABLE team_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  invited_email VARCHAR(255) NOT NULL,
  invitation_token_hash VARCHAR(64) UNIQUE NOT NULL,
  role team_role NOT NULL DEFAULT 'member',
  status invitation_status NOT NULL DEFAULT 'pending',
  invited_by UUID NOT NULL REFERENCES users(id),
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  accepted_at TIMESTAMP WITH TIME ZONE,
  declined_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Rate limiting (no CHECK constraint, enforced in app)
  resend_count INT DEFAULT 0,
  last_resent_at TIMESTAMP WITH TIME ZONE,

  -- Audit trail
  ip_address INET,
  user_agent TEXT,

  CONSTRAINT valid_expiry CHECK (expires_at > created_at),
  CONSTRAINT unique_pending_invitation UNIQUE (team_id, invited_email)
    WHERE status = 'pending'
);

CREATE INDEX idx_invitation_hash ON team_invitations(invitation_token_hash)
  WHERE status = 'pending';
CREATE INDEX idx_invitation_email ON team_invitations(invited_email, team_id);
CREATE INDEX idx_invitation_expiry ON team_invitations(expires_at)
  WHERE status = 'pending';
```

### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/teams/{id}/invitations` | POST | Admin | Send invitation |
| `/invitations/{token}` | GET | Public | Get invitation details |
| `/invitations/{token}/accept` | POST | Public | Accept invitation |
| `/invitations/{token}/decline` | POST | Public | Decline invitation |
| `/invitations/{id}/resend` | POST | Admin | Resend invitation |

### Sequence Diagram: Invitation Flow

```
┌──────┐     ┌─────────┐     ┌─────────┐     ┌──────────┐     ┌─────┐
│Admin │     │ Backend │     │ SendGrid│     │   User   │     │ DB  │
└──┬───┘     └────┬────┘     └────┬────┘     └────┬─────┘     └──┬──┘
   │              │                │               │               │
   │ POST /invitations              │               │               │
   │─────────────>│                │               │               │
   │              │                │               │               │
   │              │ Generate token │               │               │
   │              │ (secrets.token_urlsafe)        │               │
   │              │                │               │               │
   │              │ Hash token     │               │               │
   │              │ (SHA256)       │               │               │
   │              │                │               │               │
   │              │ INSERT invitation              │               │
   │              │────────────────────────────────────────────────>│
   │              │                │               │               │
   │              │ COMMIT         │               │               │
   │              │────────────────────────────────────────────────>│
   │              │                │               │               │
   │              │ Enqueue email job              │               │
   │              │───────────────>│               │               │
   │              │                │               │               │
   │              │                │ Send email    │               │
   │              │                │──────────────>│               │
   │              │                │               │               │
   │ 201 Created  │                │               │               │
   │<─────────────│                │               │               │
   │              │                │               │               │
   │              │                │     Email received            │
   │              │                │<──────────────│               │
   │              │                │               │               │
   │              │                │     Click link│               │
   │              │                │               │               │
   │              │     GET /invitations/{token}   │               │
   │              │<───────────────────────────────│               │
   │              │                │               │               │
   │              │ Hash token     │               │               │
   │              │                │               │               │
   │              │ SELECT BY hash │               │               │
   │              │────────────────────────────────────────────────>│
   │              │                │               │               │
   │              │ 200 OK (invitation details)    │               │
   │              │────────────────────────────────>│               │
   │              │                │               │               │
   │              │     POST /invitations/{token}/accept           │
   │              │<───────────────────────────────│               │
   │              │                │               │               │
   │              │ BEGIN TRANSACTION              │               │
   │              │                │               │               │
   │              │ UPDATE status='accepted'       │               │
   │              │────────────────────────────────────────────────>│
   │              │                │               │               │
   │              │ INSERT team_member             │               │
   │              │────────────────────────────────────────────────>│
   │              │                │               │               │
   │              │ COMMIT         │               │               │
   │              │────────────────────────────────────────────────>│
   │              │                │               │               │
   │              │ 200 OK (member created)        │               │
   │              │────────────────────────────────>│               │
   │              │                │               │               │
```

---

## Security Considerations

### Token Security

**Token Generation**:
```python
import secrets
invitation_token = secrets.token_urlsafe(32)  # 43-char base64url string
```

**Token Hashing**:
```python
import hashlib
token_hash = hashlib.sha256(invitation_token.encode()).hexdigest()
```

**Token Verification** (constant-time):
```python
import hmac
def verify_token(provided_token: str, stored_hash: str) -> bool:
    provided_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    return hmac.compare_digest(provided_hash, stored_hash)
```

### Rate Limiting

**Redis Implementation**:
```python
from redis import Redis
from datetime import datetime, timedelta

def check_rate_limit(redis: Redis, team_id: str, limit: int = 50) -> bool:
    """Check if team has exceeded rate limit (50/hour)"""
    key = f"invitation_rate:{team_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
    count = redis.incr(key)

    if count == 1:
        redis.expire(key, 3600)  # Expire after 1 hour

    return count <= limit
```

### Email Deliverability

**SPF Record** (add to DNS):
```
v=spf1 include:sendgrid.net ~all
```

**DKIM Record** (provided by SendGrid):
```
s1._domainkey.yourdomain.com CNAME s1.domainkey.u12345678.wl123.sendgrid.net
s2._domainkey.yourdomain.com CNAME s2.domainkey.u12345678.wl123.sendgrid.net
```

**DMARC Record**:
```
_dmarc.yourdomain.com TXT v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

---

## Performance Requirements

| Metric | Target | Measurement | Rationale |
|--------|--------|-------------|-----------|
| API Response Time | <2s (p95) | Prometheus histogram | User expects instant feedback |
| Email Acceptance | <10s (p95) | SendGrid webhook | Provider delivery time |
| Email Delivery | >95% | SendGrid reports | Industry standard |
| Token Generation | <50ms | pytest-benchmark | Cryptographic operation |
| Database Insert | <100ms | SQLAlchemy timing | Simple INSERT operation |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SendGrid rate limits | Low | High | AWS SES backup configured |
| Email deliverability | Medium | Medium | SPF/DKIM/DMARC setup, monitor bounces |
| Token enumeration | Low | High | SHA256 hashing, rate limiting |
| Double-click send | High | Medium | Idempotency key + frontend disable |
| Email before commit | Medium | High | Transactional email (after commit) |
| Concurrent accept | Low | Medium | DB unique constraint |

---

## Definition of Done

### Backend (Jan 31) ✅ COMPLETE
- [x] All backend tasks completed ✅
- [x] 48 tests passing (31 unit + 17 security) ✅
- [x] Code coverage 97% (exceeds 95% target) ✅
- [x] Security baseline met (OWASP ASVS L2) ✅
- [x] Performance requirements met (<2s p95) ✅
- [x] CTO approval received ✅

### Frontend (Feb 3-4) ⏳ PENDING
- [ ] InviteMemberModal.tsx
- [ ] AcceptInvitationPage.tsx
- [ ] React Query hooks
- [ ] Component tests

### E2E Testing (Feb 5-6) ⏳ PENDING
- [ ] 5 E2E tests (happy path, decline, expired, invalid, concurrent)
- [ ] OpenAPI spec updated
- [ ] User guide published

---

## Sprint Retrospective (Backend Phase)

**What went well**:
- [x] Token security implementation (SHA256 + constant-time comparison)
- [x] Email integration (Gmail SMTP working)
- [x] Rate limiting effectiveness (Redis-based 3-tier)
- [x] Test-driven development (48 tests caught 6 bugs before review)
- [x] CTO code review (prevented 3 production issues)

**What could be improved**:
- [x] Sustainable velocity (65.5 SP → 11 SP per day, now sustainable)
- [x] Earlier integration testing (do in parallel with unit tests)
- [x] P1/P2 estimation (separate from feature estimates)

**Action items**:
- [x] Apply learnings to Sprint 129 (GitHub integration)
- [x] Add 20% buffer for fixes/review in future sprints
- [x] Code review BEFORE claiming sprint complete

---

**Sprint Owner**: Backend Lead
**Product Owner**: CTO
**Stakeholders**: Security Team, Product Team, Frontend Team

**Status**:
- 🟢 **BACKEND COMPLETE** (Jan 31, 2026) - CTO APPROVED
- 🟡 **FRONTEND READY** (Kickoff: Feb 3, 2026)
- ⏳ **E2E TESTING PENDING** (Feb 5-6, 2026)
