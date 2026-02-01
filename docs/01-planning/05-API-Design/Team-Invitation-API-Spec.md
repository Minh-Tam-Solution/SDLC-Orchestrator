# Team Invitation API Specification

**Version**: 1.0.0
**Date**: January 30, 2026
**Sprint**: Sprint 128 (Feb 3-14, 2026)
**Reference**: ADR-043-Team-Invitation-System-Architecture.md
**Parent Spec**: API-Specification.md v3.3.0

---

## Overview

Team Invitation System provides a secure, GDPR-compliant invitation flow for adding members to teams. This replaces the insecure direct-add pattern (POST /teams/{id}/members with email) which is now deprecated.

**Security Features**:
- SHA256 token hashing (no raw tokens stored)
- Cryptographically secure token generation (`secrets.token_urlsafe(32)`)
- One-time use enforcement (status change prevents replay)
- 7-day expiry (configurable)
- Rate limiting (50 invitations/hour per team)
- Audit trail (who invited whom, when, from where)

**User Flow**:
```
1. Admin sends invitation → POST /teams/{id}/invitations
2. User receives email with magic link
3. User clicks link → GET /invitations/{token} (view details)
4. User accepts → POST /invitations/{token}/accept
5. Backend creates team membership
6. User can now access team resources
```

---

## Endpoints

### 1. Send Team Invitation

**Endpoint**: `POST /api/v1/teams/{team_id}/invitations`

**Description**: Send invitation to join team via email with magic link

**Authentication**: Required (JWT Bearer token)

**Authorization**:
- User must be team admin or owner
- Rate limit: 50 invitations/hour per team

**Request**:
```http
POST /api/v1/teams/550e8400-e29b-41d4-a716-446655440000/invitations
Authorization: Bearer <jwt_token>
Idempotency-Key: <uuid>  (optional, prevents duplicate sends)
Content-Type: application/json

{
  "email": "user@example.com",
  "role": "member",
  "message": "Join our SDLC project!" (optional)
}
```

**Request Body**:
```typescript
{
  email: string;          // Valid email format
  role: "owner" | "admin" | "member";  // Team role
  message?: string;       // Optional custom message (max 500 chars)
}
```

**Response (201 Created)**:
```json
{
  "invitation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "team_id": "550e8400-e29b-41d4-a716-446655440000",
  "invited_email": "user@example.com",
  "role": "member",
  "status": "pending",
  "expires_at": "2026-02-06T14:00:00Z",
  "invited_by": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "display_name": "John Doe"
  },
  "created_at": "2026-01-30T14:00:00Z"
}
```

**Error Responses**:

**400 Bad Request** (Invalid input):
```json
{
  "error": "validation_error",
  "message": "Invalid email format",
  "details": {
    "field": "email",
    "constraint": "email_format"
  }
}
```

**403 Forbidden** (Not authorized):
```json
{
  "error": "forbidden",
  "message": "Only team admins can send invitations"
}
```

**409 Conflict** (Invitation already exists):
```json
{
  "error": "invitation_exists",
  "message": "Pending invitation already sent to this email",
  "invitation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

**429 Too Many Requests** (Rate limit exceeded):
```json
{
  "error": "rate_limit_exceeded",
  "message": "Maximum 50 invitations per hour per team",
  "retry_after": 1800
}
```

---

### 2. Get Invitation Details

**Endpoint**: `GET /api/v1/invitations/{token}`

**Description**: Get invitation details (public endpoint, no auth required)

**Authentication**: None (public endpoint with secure token)

**Request**:
```http
GET /api/v1/invitations/abc123def456...
```

**Response (200 OK)**:
```json
{
  "team": {
    "team_id": "550e8400-e29b-41d4-a716-446655440000",
    "team_name": "SDLC Orchestrator Team",
    "organization": "NQH Holding"
  },
  "invited_email": "user@example.com",
  "role": "member",
  "status": "pending",
  "expires_at": "2026-02-06T14:00:00Z",
  "invited_by": {
    "display_name": "John Doe"
  },
  "message": "Join our SDLC project!",
  "created_at": "2026-01-30T14:00:00Z"
}
```

**Error Responses**:

**404 Not Found** (Invalid/expired token):
```json
{
  "error": "invitation_not_found",
  "message": "Invitation not found or has expired"
}
```

**410 Gone** (Already used):
```json
{
  "error": "invitation_already_used",
  "message": "This invitation has already been accepted or declined"
}
```

---

### 3. Accept Invitation

**Endpoint**: `POST /api/v1/invitations/{token}/accept`

**Description**: Accept invitation and join team

**Authentication**: Required (JWT Bearer token)

**Authorization**:
- User's email must match `invited_email`
- Invitation must be pending and not expired

**Request**:
```http
POST /api/v1/invitations/abc123def456.../accept
Authorization: Bearer <jwt_token>
Content-Type: application/json

{}
```

**Response (200 OK)**:
```json
{
  "status": "accepted",
  "team_id": "550e8400-e29b-41d4-a716-446655440000",
  "team_name": "SDLC Orchestrator Team",
  "role": "member",
  "accepted_at": "2026-01-31T10:00:00Z",
  "redirect_url": "/teams/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:

**400 Bad Request** (Cannot accept):
```json
{
  "error": "cannot_accept_invitation",
  "message": "Invitation has expired",
  "expires_at": "2026-02-06T14:00:00Z"
}
```

**403 Forbidden** (Email mismatch):
```json
{
  "error": "email_mismatch",
  "message": "This invitation was sent to a different email address"
}
```

**409 Conflict** (Already member):
```json
{
  "error": "already_member",
  "message": "You are already a member of this team"
}
```

---

### 4. Decline Invitation

**Endpoint**: `POST /api/v1/invitations/{token}/decline`

**Description**: Decline invitation (polite rejection)

**Authentication**: None (public endpoint with secure token)

**Request**:
```http
POST /api/v1/invitations/abc123def456.../decline
Content-Type: application/json

{
  "reason": "Not interested" (optional)
}
```

**Response (200 OK)**:
```json
{
  "status": "declined",
  "declined_at": "2026-01-31T10:00:00Z",
  "message": "Invitation declined successfully"
}
```

**Error Responses**:

**400 Bad Request** (Cannot decline):
```json
{
  "error": "cannot_decline_invitation",
  "message": "Invitation has already been accepted"
}
```

---

### 5. Resend Invitation

**Endpoint**: `POST /api/v1/invitations/{invitation_id}/resend`

**Description**: Resend invitation email (max 3 times, 5min cooldown)

**Authentication**: Required (JWT Bearer token)

**Authorization**:
- User must be team admin or owner
- Invitation must be pending or expired
- Not exceeded resend limit (3 times)
- Cooldown period elapsed (5 minutes)

**Request**:
```http
POST /api/v1/invitations/7c9e6679-7425-40de-944b-e07fc1f90ae7/resend
Authorization: Bearer <jwt_token>
Content-Type: application/json

{}
```

**Response (200 OK)**:
```json
{
  "invitation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "pending",
  "resend_count": 1,
  "last_resent_at": "2026-01-31T10:00:00Z",
  "expires_at": "2026-02-06T14:00:00Z",
  "message": "Invitation email resent successfully"
}
```

**Error Responses**:

**400 Bad Request** (Cannot resend):
```json
{
  "error": "cannot_resend_invitation",
  "message": "Invitation has already been accepted",
  "status": "accepted"
}
```

**429 Too Many Requests** (Resend limit exceeded):
```json
{
  "error": "resend_limit_exceeded",
  "message": "Maximum 3 resends per invitation",
  "resend_count": 3
}
```

**429 Too Many Requests** (Cooldown active):
```json
{
  "error": "resend_cooldown_active",
  "message": "Please wait 5 minutes before resending",
  "retry_after": 180
}
```

---

## Deprecated Endpoint

### POST /teams/{team_id}/members (Email-based)

**Status**: ❌ **DEPRECATED** (as of v2.0, Feb 2026)

**Removal Date**: v3.0 (Aug 2026)

**Reason**: Security risk (no email verification, no user consent, GDPR violation)

**Response (410 Gone)**:
```json
{
  "error": "endpoint_deprecated",
  "message": "Email-based member addition is deprecated. Use invitation system instead.",
  "deprecation_date": "2026-02-01",
  "removal_date": "2026-08-01",
  "migration_guide": "https://docs.sdlc-orchestrator.com/api/migration/invitations",
  "replacement_endpoint": "POST /teams/{team_id}/invitations"
}
```

**Migration Example**:
```javascript
// ❌ OLD (deprecated)
POST /teams/123/members
{
  "email": "user@example.com",
  "role": "member"
}

// ✅ NEW (invitation flow)
POST /teams/123/invitations
{
  "email": "user@example.com",
  "role": "member"
}

// User receives email, clicks link, accepts invitation
POST /invitations/{token}/accept
```

---

## Rate Limiting

**Per Team**:
- 50 invitations/hour (sliding window)
- 3 resends per invitation
- 5 minute cooldown between resends

**Per Email**:
- 3 invitations/day to same email across all teams

**Implementation**:
- Redis-based rate limiting
- Sliding window algorithm
- Returns 429 Too Many Requests with `Retry-After` header

---

## Security Considerations

### Token Security

**Generation**:
```python
import secrets
token = secrets.token_urlsafe(32)  # 43-char base64url string (256-bit entropy)
```

**Storage**:
```python
import hashlib
token_hash = hashlib.sha256(token.encode()).hexdigest()  # Store hash, not raw token
```

**Verification**:
```python
import hmac
def verify_token(provided_token: str, stored_hash: str) -> bool:
    provided_hash = hashlib.sha256(provided_token.encode()).hexdigest()
    return hmac.compare_digest(provided_hash, stored_hash)  # Constant-time comparison
```

### Audit Trail

All invitation events are logged:
```json
{
  "event": "invitation_sent",
  "invitation_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "team_id": "550e8400-e29b-41d4-a716-446655440000",
  "invited_email": "user@example.com",
  "invited_by": "123e4567-e89b-12d3-a456-426614174000",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2026-01-30T14:00:00Z"
}
```

### GDPR Compliance

**Consent**: User must explicitly accept invitation (email click + button click)

**Right to Decline**: User can decline invitation without consequences

**Data Minimization**: Only email + role stored, no personal data

**Audit Trail**: Full history of who invited whom, when

---

## OpenAPI 3.0 Schema

```yaml
/teams/{team_id}/invitations:
  post:
    summary: Send team invitation
    operationId: sendTeamInvitation
    tags:
      - Team Invitations
    security:
      - bearerAuth: []
    parameters:
      - name: team_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
      - name: Idempotency-Key
        in: header
        required: false
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/InvitationCreate'
    responses:
      '201':
        description: Invitation sent successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvitationResponse'
      '400':
        $ref: '#/components/responses/BadRequest'
      '403':
        $ref: '#/components/responses/Forbidden'
      '409':
        $ref: '#/components/responses/Conflict'
      '429':
        $ref: '#/components/responses/TooManyRequests'

/invitations/{token}:
  get:
    summary: Get invitation details
    operationId: getInvitation
    tags:
      - Team Invitations
    parameters:
      - name: token
        in: path
        required: true
        schema:
          type: string
          minLength: 43
          maxLength: 43
    responses:
      '200':
        description: Invitation details
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvitationDetails'
      '404':
        $ref: '#/components/responses/NotFound'
      '410':
        $ref: '#/components/responses/Gone'

/invitations/{token}/accept:
  post:
    summary: Accept invitation
    operationId: acceptInvitation
    tags:
      - Team Invitations
    security:
      - bearerAuth: []
    parameters:
      - name: token
        in: path
        required: true
        schema:
          type: string
    responses:
      '200':
        description: Invitation accepted
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvitationAccepted'
      '400':
        $ref: '#/components/responses/BadRequest'
      '403':
        $ref: '#/components/responses/Forbidden'
      '409':
        $ref: '#/components/responses/Conflict'

/invitations/{token}/decline:
  post:
    summary: Decline invitation
    operationId: declineInvitation
    tags:
      - Team Invitations
    parameters:
      - name: token
        in: path
        required: true
        schema:
          type: string
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              reason:
                type: string
                maxLength: 500
    responses:
      '200':
        description: Invitation declined
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvitationDeclined'
      '400':
        $ref: '#/components/responses/BadRequest'

/invitations/{invitation_id}/resend:
  post:
    summary: Resend invitation email
    operationId: resendInvitation
    tags:
      - Team Invitations
    security:
      - bearerAuth: []
    parameters:
      - name: invitation_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    responses:
      '200':
        description: Invitation resent
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvitationResent'
      '400':
        $ref: '#/components/responses/BadRequest'
      '429':
        $ref: '#/components/responses/TooManyRequests'
```

---

## Components/Schemas

```yaml
components:
  schemas:
    InvitationCreate:
      type: object
      required:
        - email
        - role
      properties:
        email:
          type: string
          format: email
          example: user@example.com
        role:
          type: string
          enum: [owner, admin, member]
          example: member
        message:
          type: string
          maxLength: 500
          example: Join our SDLC project!

    InvitationResponse:
      type: object
      properties:
        invitation_id:
          type: string
          format: uuid
        team_id:
          type: string
          format: uuid
        invited_email:
          type: string
          format: email
        role:
          type: string
          enum: [owner, admin, member]
        status:
          type: string
          enum: [pending, accepted, declined, expired, cancelled]
        expires_at:
          type: string
          format: date-time
        invited_by:
          type: object
          properties:
            user_id:
              type: string
              format: uuid
            display_name:
              type: string
        created_at:
          type: string
          format: date-time

    InvitationDetails:
      type: object
      properties:
        team:
          type: object
          properties:
            team_id:
              type: string
              format: uuid
            team_name:
              type: string
            organization:
              type: string
        invited_email:
          type: string
          format: email
        role:
          type: string
        status:
          type: string
        expires_at:
          type: string
          format: date-time
        invited_by:
          type: object
          properties:
            display_name:
              type: string
        message:
          type: string
        created_at:
          type: string
          format: date-time

    InvitationAccepted:
      type: object
      properties:
        status:
          type: string
          enum: [accepted]
        team_id:
          type: string
          format: uuid
        team_name:
          type: string
        role:
          type: string
        accepted_at:
          type: string
          format: date-time
        redirect_url:
          type: string
          example: /teams/550e8400-e29b-41d4-a716-446655440000

    InvitationDeclined:
      type: object
      properties:
        status:
          type: string
          enum: [declined]
        declined_at:
          type: string
          format: date-time
        message:
          type: string
          example: Invitation declined successfully

    InvitationResent:
      type: object
      properties:
        invitation_id:
          type: string
          format: uuid
        status:
          type: string
        resend_count:
          type: integer
        last_resent_at:
          type: string
          format: date-time
        expires_at:
          type: string
          format: date-time
        message:
          type: string
```

---

**Status**: ✅ **APPROVED FOR IMPLEMENTATION** (Sprint 128, Feb 3-14, 2026)
**Reference**: ADR-043, SPRINT-128-TEAM-INVITATION-SYSTEM.md
**Last Updated**: January 30, 2026
