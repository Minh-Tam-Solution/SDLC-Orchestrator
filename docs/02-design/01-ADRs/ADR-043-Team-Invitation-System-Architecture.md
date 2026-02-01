# ADR-043: Team Invitation System Architecture

**Status**: ✅ APPROVED (CTO Sign-off: Jan 30, 2026)
**Date**: January 30, 2026
**Decision Maker**: CTO + Security Lead
**Context**: Sprint 128 preparation (Feb 3-14, 2026)
**Related ADRs**: ADR-008 (Authentication), ADR-015 (RBAC)
**Sprint**: Sprint 128 (Team Invitation System)

---

## Context and Problem Statement

The current team management system allows administrators to directly add members by email without user consent. This approach creates **three critical issues**:

1. **Security Risk**: No verification that the email owner actually wants to join
2. **Compliance Risk**: Violates GDPR consent requirements (auto-enrollment without consent)
3. **UX Risk**: Users receive unexpected access to systems they didn't request

**Business Impact**:
- **Blocks March 1 launch** (P0 compliance gap)
- **Security audit failure** (OWASP ASVS Level 2 violation)
- **Legal liability** (GDPR Article 7 violation)

**Requirements**:
- Replace direct-add pattern with consent-based invitation flow
- Implement cryptographically secure invitation tokens
- Email delivery within 10 seconds (p95)
- GDPR compliance (explicit consent)
- Audit trail for all invitation events

---

## Decision Drivers

### Must Have (P0)
- **Token Security**: Cryptographically secure tokens (SHA256 hashing)
- **Idempotency**: Prevent duplicate invitation sends
- **Rate Limiting**: Prevent invitation spam (50/hour per team)
- **Email Delivery**: <10s p95 via SendGrid
- **Audit Trail**: Who invited whom, when, from which IP

### Should Have (P1)
- **Transactional Email**: Email sent AFTER database commit
- **One-time Use**: Token expires after first use
- **Expiry**: Invitation expires after 7 days
- **Resend**: Allow admin to resend expired invitations

### Nice to Have (P2)
- **Email Templates**: Branded invitation emails
- **Multi-language**: Support Vietnamese + English
- **Analytics**: Track acceptance rate, time-to-accept

---

## Considered Options

### Option 1: Direct Member Addition (Current - REJECTED)

**Implementation**:
```python
# Current approach (INSECURE)
@router.post("/teams/{team_id}/members")
async def add_team_member(team_id: UUID, email: str, role: str):
    user = get_user_by_email(email)
    if not user:
        # Auto-create user account (NO CONSENT!)
        user = create_user(email=email, password=random_password())

    add_to_team(team_id, user.id, role)
    send_welcome_email(user.email)  # After the fact
    return {"status": "added"}
```

**Pros**:
- ✅ Simple implementation (1 API call)
- ✅ Instant team access (no waiting)

**Cons**:
- ❌ **Security risk**: No email verification
- ❌ **GDPR violation**: No explicit consent
- ❌ **UX issue**: Unexpected account creation
- ❌ **Audit risk**: No approval trail

**Verdict**: ❌ REJECTED (blocks launch, legal liability)

---

### Option 2: JWT-based Invitation Tokens (REJECTED)

**Implementation**:
```python
import jwt

@router.post("/teams/{team_id}/invitations")
async def send_invitation(team_id: UUID, email: str):
    # Generate JWT token
    token = jwt.encode({
        "team_id": str(team_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }, secret_key, algorithm="HS256")

    # Store token in database (RAW TOKEN!)
    invitation = Invitation(token=token, ...)  # ❌ Security risk
    db.add(invitation)

    send_email(email, invitation_link=f"/accept?token={token}")
```

**Pros**:
- ✅ Stateless (no DB lookup needed)
- ✅ Expiry built-in (JWT `exp` claim)

**Cons**:
- ❌ **Cannot revoke** (JWT is stateless, can't invalidate)
- ❌ **Token in database** (if stored for audit, defeats stateless purpose)
- ❌ **Larger tokens** (JWT is ~200 chars vs 43 chars for random token)
- ❌ **Replay attacks** (can't enforce one-time use)

**Verdict**: ❌ REJECTED (cannot revoke, replay risk)

---

### Option 3: Hash-based Invitation Tokens (APPROVED ✅)

**Implementation**:
```python
import secrets
import hashlib

@router.post("/teams/{team_id}/invitations")
async def send_invitation(team_id: UUID, email: str):
    # Generate cryptographically secure token
    token = secrets.token_urlsafe(32)  # 43-char base64url string

    # Hash token before storage (SHA256)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Store ONLY the hash
    invitation = Invitation(
        invitation_token_hash=token_hash,  # ✅ Hashed
        team_id=team_id,
        invited_email=email,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(invitation)
    db.commit()

    # Send email with raw token (only time it's visible)
    send_email(email, invitation_link=f"/accept?token={token}")

    return {"status": "sent"}

@router.post("/invitations/accept")
async def accept_invitation(token: str):
    # Hash incoming token
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Lookup by hash (constant-time comparison)
    invitation = db.query(Invitation).filter(
        Invitation.invitation_token_hash == token_hash,
        Invitation.status == "pending",
        Invitation.expires_at > datetime.utcnow()
    ).first()

    if not invitation:
        raise HTTPException(404, "Invitation not found or expired")

    # One-time use: Update status
    invitation.status = "accepted"
    invitation.accepted_at = datetime.utcnow()

    # Create team member
    add_to_team(invitation.team_id, user.id, invitation.role)

    db.commit()
    return {"status": "accepted"}
```

**Pros**:
- ✅ **Cryptographically secure**: `secrets.token_urlsafe(32)` uses OS random
- ✅ **Token not in database**: Only hash stored (rainbow table protection)
- ✅ **Revocable**: Can delete/expire invitation in database
- ✅ **One-time use**: Status change prevents replay
- ✅ **Audit trail**: Full history in database
- ✅ **Short tokens**: 43 chars vs 200+ for JWT

**Cons**:
- ⚠️ Requires database lookup (not stateless)
- ⚠️ Requires Redis for idempotency caching

**Verdict**: ✅ **APPROVED** (best security-usability trade-off)

---

## Decision Outcome

**Chosen Option**: **Option 3 - Hash-based Invitation Tokens**

### Implementation Details

#### 1. Database Schema

```sql
CREATE TABLE team_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  invited_email VARCHAR(255) NOT NULL,
  invitation_token_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 hash
  role team_role NOT NULL DEFAULT 'member',
  status invitation_status NOT NULL DEFAULT 'pending',
  invited_by UUID NOT NULL REFERENCES users(id),
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  accepted_at TIMESTAMP WITH TIME ZONE,
  declined_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Rate limiting (enforced in application, NOT DB constraint)
  resend_count INT DEFAULT 0,  -- No CHECK constraint (flexible)
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
```

**Why no CHECK constraint on `resend_count`?**
- Flexibility: Rate limit can change via config (no migration needed)
- Application layer enforcement: `MAX_INVITATION_RESENDS` env var

#### 2. Token Security

**Token Generation**:
```python
import secrets

def generate_invitation_token() -> str:
    """Generate cryptographically secure token (43 chars)"""
    return secrets.token_urlsafe(32)  # 32 bytes = 256 bits entropy
```

**Token Hashing**:
```python
import hashlib

def hash_token(token: str) -> str:
    """Hash token with SHA256 (one-way)"""
    return hashlib.sha256(token.encode()).hexdigest()
```

**Token Verification** (constant-time to prevent timing attacks):
```python
import hmac

def verify_token(provided_token: str, stored_hash: str) -> bool:
    """Verify token with constant-time comparison"""
    provided_hash = hash_token(provided_token)
    return hmac.compare_digest(provided_hash, stored_hash)
```

#### 3. Idempotency Protection

**Frontend** (immediate):
```typescript
const [isSending, setIsSending] = useState(false);

const handleSendInvite = async () => {
  if (isSending) return;  // Prevent double-click
  setIsSending(true);
  try {
    await sendInvitation(teamId, email, role);
  } finally {
    setIsSending(false);
  }
};
```

**Backend** (robust):
```python
from fastapi import Header

@router.post("/teams/{team_id}/invitations")
async def send_invitation(
    idempotency_key: str = Header(None, alias="Idempotency-Key")
):
    if idempotency_key:
        cached = redis.get(f"invite:{idempotency_key}")
        if cached:
            return {"status": "already_sent", "invitation_id": cached}

    invitation = create_invitation(...)

    if idempotency_key:
        redis.setex(f"invite:{idempotency_key}", 86400, str(invitation.id))

    return invitation
```

#### 4. Transactional Email

**Problem**: Email sent before DB commit → DB rollback → Ghost invite

**Solution**: Send email AFTER commit
```python
from sqlalchemy import event

async def send_invitation(...):
    invitation = TeamInvitation(...)
    db.add(invitation)

    # Register after-commit hook
    @event.listens_for(db, "after_commit", once=True)
    def send_email_after_commit(session):
        send_invitation_email_job.delay(invitation.id)

    db.commit()  # Email sent ONLY if commit succeeds
```

#### 5. Rate Limiting

**Redis-based** (50 invitations/hour per team):
```python
from redis import Redis

def check_rate_limit(redis: Redis, team_id: str) -> bool:
    key = f"invitation_rate:{team_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
    count = redis.incr(key)

    if count == 1:
        redis.expire(key, 3600)  # 1 hour

    if count > 50:
        raise HTTPException(429, "Rate limit exceeded (50/hour)")

    return True
```

---

## Consequences

### Positive

1. **Security**:
   - ✅ Tokens are cryptographically secure (256-bit entropy)
   - ✅ Tokens hashed in database (rainbow table protection)
   - ✅ Constant-time comparison (timing attack protection)
   - ✅ One-time use (replay attack protection)

2. **Compliance**:
   - ✅ GDPR compliant (explicit consent via email click)
   - ✅ Audit trail (who invited whom, when, from which IP)
   - ✅ Right to withdraw (user can decline invitation)

3. **UX**:
   - ✅ Magic link (no password needed for acceptance)
   - ✅ Clear invitation email (team name, inviter, role)
   - ✅ Expiry warning (7 days to accept)

4. **Operations**:
   - ✅ Rate limiting (prevent spam)
   - ✅ Idempotency (prevent duplicate sends)
   - ✅ Revocable (admin can cancel invitation)

### Negative

1. **Performance**:
   - ⚠️ Database lookup required (not stateless like JWT)
   - ⚠️ Redis required (for idempotency + rate limiting)
   - **Mitigation**: Index on `invitation_token_hash`, Redis caching

2. **Complexity**:
   - ⚠️ More complex than direct-add (3 steps vs 1)
   - ⚠️ Email delivery dependency (SendGrid)
   - **Mitigation**: Background job for email, AWS SES backup

3. **UX Trade-off**:
   - ⚠️ Delayed access (user must click email)
   - ⚠️ Email may be delayed/missed
   - **Mitigation**: Resend functionality, expiry warning

---

## Breaking Changes

### API Deprecation

**Deprecated Endpoint**:
```
POST /api/v1/teams/{team_id}/members (email-based direct add)
```

**New Endpoints**:
```
POST /api/v1/teams/{team_id}/invitations (send invitation)
GET  /api/v1/invitations/{token}         (get invitation details)
POST /api/v1/invitations/{token}/accept  (accept invitation)
POST /api/v1/invitations/{token}/decline (decline invitation)
```

**Migration Timeline**:
- **Feb 2026**: Deprecated endpoint returns 410 GONE
- **Aug 2026**: Endpoint removed entirely

**Migration Guide**:
```python
# OLD (deprecated)
POST /teams/123/members
{
  "email": "user@example.com",
  "role": "member"
}

# NEW (invitation flow)
POST /teams/123/invitations
{
  "email": "user@example.com",
  "role": "member"
}

# User receives email and clicks link
# Backend calls:
POST /invitations/{token}/accept
```

---

## Validation and Testing

### Security Tests

1. **Token Enumeration Protection**:
   - ❌ Invalid token → 404 Not Found (no info leak)
   - ❌ Expired token → 400 Bad Request
   - ❌ Used token → 409 Conflict

2. **Timing Attack Protection**:
   - ✅ Constant-time comparison (hmac.compare_digest)
   - ✅ No early exit on hash mismatch

3. **Replay Attack Protection**:
   - ✅ One-time use (status change)
   - ✅ Idempotency key (prevent duplicate sends)

### Performance Tests

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API Response | <2s (p95) | TBD | Sprint 128 |
| Email Acceptance | <10s (p95) | TBD | Sprint 128 |
| Email Delivery | >95% | TBD | Sprint 128 |
| Token Generation | <50ms | ~1ms | ✅ |
| Database Insert | <100ms | TBD | Sprint 128 |

---

## Alternatives Not Chosen

### Alternative A: OAuth-based Invitations

Use GitHub/Google OAuth for invitation acceptance.

**Pros**: No email dependency, instant verification
**Cons**: Requires OAuth for all users, complex flow
**Verdict**: Rejected (too complex, not all users have GitHub/Google)

### Alternative B: SMS-based Invitations

Send invitation via SMS instead of email.

**Pros**: Higher delivery rate than email
**Cons**: Cost ($0.01/SMS), requires phone numbers
**Verdict**: Rejected (cost prohibitive, privacy concerns)

### Alternative C: QR Code Invitations

Generate QR code for team invitation.

**Pros**: Works offline, easy to share in person
**Cons**: Still need email for remote invites
**Verdict**: Deferred to P2 (nice-to-have for events)

---

## References

- **OWASP ASVS Level 2**: V2.2 (Session Management), V3.2 (Token-based Authentication)
- **GDPR Article 7**: Conditions for consent
- **NIST SP 800-63B**: Digital Identity Guidelines (Token Entropy)
- **RFC 7519**: JSON Web Token (JWT) - considered but not chosen
- **secrets module**: Python cryptographic random generation

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Jan 25, 2026 | Explored JWT tokens | Stateless, but cannot revoke |
| Jan 27, 2026 | Explored hash-based tokens | Revocable, secure, audit trail |
| Jan 30, 2026 | **APPROVED hash-based** | Best security-usability trade-off |
| Jan 30, 2026 | Remove CHECK constraint | Flexibility (config-based rate limit) |
| Jan 30, 2026 | Add idempotency protection | Prevent double-click sends |
| Jan 30, 2026 | Add transactional email | Prevent ghost invites |

---

## Implementation Checklist

- [ ] Database migration: `s128_001_team_invitations.py`
- [ ] Backend API: 5 invitation endpoints
- [ ] Email service: SendGrid integration
- [ ] Frontend UI: `InviteMemberModal` + `AcceptInvitationPage`
- [ ] Security tests: 5 scenarios (enumeration, replay, timing)
- [ ] Performance tests: <2s API, <10s email
- [ ] Documentation: API deprecation notice
- [ ] Migration guide: Email to API consumers

---

**Status**: ✅ **APPROVED FOR SPRINT 128**
**Approval**: CTO + Security Lead (Jan 30, 2026)
**Implementation**: Sprint 128 (Feb 3-14, 2026)
**Review Date**: Feb 14, 2026 (Sprint 128 demo)

---

**Document Version**: v1.0
**Author**: Backend Lead + Security Lead
**Reviewers**: CTO, Product Owner, Security Team
**Last Updated**: January 30, 2026
