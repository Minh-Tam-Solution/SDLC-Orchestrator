# Team Invitations Table Schema

**Version**: 1.0.0
**Date**: January 30, 2026
**Sprint**: Sprint 128 (Feb 3-14, 2026)
**Reference**: ADR-043-Team-Invitation-System-Architecture.md
**Migration**: s128_001_team_invitations.py

---

## Table: team_invitations

**Purpose**: Store team invitation tokens with hash-based security for GDPR-compliant member onboarding.

**Key Features**:
- SHA256 token hashing (no raw tokens stored)
- One-time use enforcement (status change)
- 7-day expiry (configurable)
- Rate limiting support (resend_count)
- Full audit trail (IP, user agent, timestamps)

---

## Schema Definition

```sql
CREATE TABLE team_invitations (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Invitation details
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  invited_email VARCHAR(255) NOT NULL,
  invitation_token_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 hash (64 hex chars)
  role VARCHAR(20) NOT NULL DEFAULT 'member',
  status invitation_status NOT NULL DEFAULT 'pending',
  invited_by UUID NOT NULL REFERENCES users(id),

  -- Timestamps
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  accepted_at TIMESTAMP WITH TIME ZONE,
  declined_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Rate limiting (enforced in application, no DB CHECK constraint)
  resend_count INT DEFAULT 0,
  last_resent_at TIMESTAMP WITH TIME ZONE,

  -- Audit trail
  ip_address INET,
  user_agent TEXT,

  -- Constraints
  CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Enum type
CREATE TYPE invitation_status AS ENUM (
  'pending',
  'accepted',
  'declined',
  'expired',
  'cancelled'
);
```

---

## Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| **id** | UUID | NOT NULL | `gen_random_uuid()` | Primary key |
| **team_id** | UUID | NOT NULL | - | Foreign key to teams.id (CASCADE delete) |
| **invited_email** | VARCHAR(255) | NOT NULL | - | Email address of invitee |
| **invitation_token_hash** | VARCHAR(64) | NOT NULL | - | SHA256 hash of token (never store raw) |
| **role** | VARCHAR(20) | NOT NULL | `'member'` | Team role (owner, admin, member) |
| **status** | invitation_status | NOT NULL | `'pending'` | Invitation status (enum) |
| **invited_by** | UUID | NOT NULL | - | Foreign key to users.id (who sent invite) |
| **expires_at** | TIMESTAMP TZ | NOT NULL | - | Expiration timestamp (7 days from creation) |
| **accepted_at** | TIMESTAMP TZ | NULL | - | Timestamp when invitation was accepted |
| **declined_at** | TIMESTAMP TZ | NULL | - | Timestamp when invitation was declined |
| **created_at** | TIMESTAMP TZ | NOT NULL | `NOW()` | Creation timestamp |
| **resend_count** | INT | NOT NULL | `0` | Number of times invitation was resent |
| **last_resent_at** | TIMESTAMP TZ | NULL | - | Last resend timestamp |
| **ip_address** | INET | NULL | - | IP address of inviter (audit) |
| **user_agent** | TEXT | NULL | - | User agent of inviter (audit) |

---

## Indexes

```sql
-- Partial unique index: Only one pending invitation per team+email
CREATE UNIQUE INDEX idx_unique_pending_invitation
  ON team_invitations(team_id, invited_email)
  WHERE status = 'pending';

-- Token hash lookup (most common query, partial index for performance)
CREATE INDEX idx_invitation_hash
  ON team_invitations(invitation_token_hash)
  WHERE status = 'pending';

-- Email lookup (admin searches invitations)
CREATE INDEX idx_invitation_email
  ON team_invitations(team_id, invited_email);

-- Expiry cleanup (background job)
CREATE INDEX idx_invitation_expiry
  ON team_invitations(expires_at)
  WHERE status = 'pending';

-- Audit queries (who invited)
CREATE INDEX idx_invitation_invited_by
  ON team_invitations(invited_by);
```

---

## Relationships

```
team_invitations
├─ team_id → teams.id (FOREIGN KEY, ON DELETE CASCADE)
└─ invited_by → users.id (FOREIGN KEY)
```

**Cardinality**:
- `teams` 1:N `team_invitations` (one team has many invitations)
- `users` 1:N `team_invitations` (one user can send many invitations)

---

## Enum Values

### invitation_status

| Value | Description |
|-------|-------------|
| `pending` | Invitation sent, awaiting response (default) |
| `accepted` | User accepted and joined team |
| `declined` | User declined invitation |
| `expired` | Invitation expired (7 days elapsed) |
| `cancelled` | Admin cancelled invitation |

**State Transitions**:
```
pending → accepted (user accepts)
pending → declined (user declines)
pending → expired (7 days elapsed, background job)
pending → cancelled (admin cancels)
```

---

## Constraints

### Check Constraints

```sql
CONSTRAINT valid_expiry CHECK (expires_at > created_at)
```

Ensures expiry date is always after creation date.

### Unique Constraints

```sql
-- Partial unique: Only one pending invitation per team+email
UNIQUE (team_id, invited_email) WHERE status = 'pending'
```

**Rationale**:
- Prevents duplicate pending invitations
- Allows re-invitation after previous one is accepted/declined/expired
- Uses partial index for performance (only checks pending invitations)

### Foreign Key Constraints

```sql
FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
FOREIGN KEY (invited_by) REFERENCES users(id)
```

**Cascade Behavior**:
- If team deleted → all invitations deleted (CASCADE)
- If inviter deleted → invitation record preserved (no CASCADE, for audit)

---

## Application-Layer Constraints

**Rate Limiting** (NOT enforced in DB, for flexibility):

```python
# Config-driven, no DB CHECK constraint
MAX_INVITATION_RESENDS = 3  # Environment variable
INVITATION_RESEND_COOLDOWN_MINUTES = 5

# Application validates before insert/update
if invitation.resend_count >= settings.MAX_INVITATION_RESENDS:
    raise HTTPException(429, "Maximum resend limit reached")
```

**Why not DB constraint?**
- Flexibility: Can change limit via environment variable (no migration)
- Different limits per tier: LITE (3 resends), PROFESSIONAL (5 resends)
- Easier testing: Can override limit in test environment

---

## Example Data

```sql
-- Pending invitation
INSERT INTO team_invitations VALUES (
  '7c9e6679-7425-40de-944b-e07fc1f90ae7',  -- id
  '550e8400-e29b-41d4-a716-446655440000',  -- team_id
  'user@example.com',                      -- invited_email
  'a5e8f3d...hash...', --  invitation_token_hash (SHA256)
  'member',                                 -- role
  'pending',                                -- status
  '123e4567-e89b-12d3-a456-426614174000',  -- invited_by
  '2026-02-06 14:00:00+00',                -- expires_at (+7 days)
  NULL,                                     -- accepted_at
  NULL,                                     -- declined_at
  '2026-01-30 14:00:00+00',                -- created_at
  0,                                        -- resend_count
  NULL,                                     -- last_resent_at
  '192.168.1.100',                         -- ip_address
  'Mozilla/5.0...'                         -- user_agent
);
```

---

## Security Considerations

### Token Security

**NEVER store raw tokens**:
```python
# ❌ WRONG: Store raw token
invitation.token = "abc123def456..."  # Security violation!

# ✅ CORRECT: Store SHA256 hash
import hashlib
token = secrets.token_urlsafe(32)  # Generate
token_hash = hashlib.sha256(token.encode()).hexdigest()
invitation.invitation_token_hash = token_hash  # Store hash only
```

**Token verification** (constant-time comparison):
```python
import hmac

def verify_token(provided_token: str, stored_hash: str) -> bool:
    provided_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    return hmac.compare_digest(provided_hash, stored_hash)  # Timing-safe
```

### Audit Trail

All invitation events logged:
- Who invited whom (invited_by, invited_email)
- When (created_at, accepted_at, declined_at)
- From where (ip_address, user_agent)
- How many resends (resend_count, last_resent_at)

---

## Queries

### Common Queries

**1. Find invitation by token hash**:
```sql
SELECT * FROM team_invitations
WHERE invitation_token_hash = $1
  AND status = 'pending'
  AND expires_at > NOW()
LIMIT 1;
```

**2. List pending invitations for team**:
```sql
SELECT * FROM team_invitations
WHERE team_id = $1
  AND status = 'pending'
ORDER BY created_at DESC;
```

**3. Check if invitation already exists**:
```sql
SELECT id FROM team_invitations
WHERE team_id = $1
  AND invited_email = $2
  AND status = 'pending'
LIMIT 1;
```

**4. Find expired invitations (background job)**:
```sql
SELECT id FROM team_invitations
WHERE status = 'pending'
  AND expires_at < NOW()
LIMIT 1000;
```

**5. Audit: Who invited this email?**:
```sql
SELECT ti.*, u.display_name AS inviter_name
FROM team_invitations ti
JOIN users u ON ti.invited_by = u.id
WHERE ti.invited_email = $1
ORDER BY ti.created_at DESC;
```

---

## Performance

**Expected Load**:
- 50 invitations/hour per team (rate limit)
- Avg 100 teams active → 5,000 invitations/hour
- 7-day retention → ~840,000 pending invitations at peak

**Index Performance**:
- Token lookup: O(log n) with idx_invitation_hash (partial index)
- Expiry cleanup: O(log n) with idx_invitation_expiry (partial index)
- Team invitations list: O(log n) with idx_invitation_email

**Storage**:
- Avg row size: ~250 bytes (with audit trail)
- 1M invitations: ~250 MB
- 10M invitations: ~2.5 GB (manageable)

---

## Maintenance

### Cleanup Job (Background)

**Mark expired invitations** (every 1 hour):
```sql
UPDATE team_invitations
SET status = 'expired'
WHERE status = 'pending'
  AND expires_at < NOW();
```

**Archive old invitations** (every month):
```sql
-- Move to archive table (accepted/declined/expired > 90 days)
INSERT INTO team_invitations_archive
SELECT * FROM team_invitations
WHERE status IN ('accepted', 'declined', 'expired', 'cancelled')
  AND created_at < NOW() - INTERVAL '90 days';

DELETE FROM team_invitations
WHERE status IN ('accepted', 'declined', 'expired', 'cancelled')
  AND created_at < NOW() - INTERVAL '90 days';
```

---

## Migration Path

### Alembic Migration

**Forward**:
```bash
alembic upgrade head  # Creates team_invitations table
```

**Rollback**:
```bash
alembic downgrade -1  # Drops team_invitations table
```

**Backup Strategy** (before production migration):
```bash
# Backup entire database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --format=custom \
  --file=backup_pre_sprint128_$(date +%Y%m%d).dump

# Test restore on staging
pg_restore -h $STAGING_HOST -U $STAGING_USER \
  -d $STAGING_DB \
  backup_pre_sprint128_*.dump
```

---

**Status**: ✅ **APPROVED FOR IMPLEMENTATION** (Sprint 128, Feb 3-14, 2026)
**Reference**: ADR-043, s128_001_team_invitations.py
**Last Updated**: January 30, 2026
