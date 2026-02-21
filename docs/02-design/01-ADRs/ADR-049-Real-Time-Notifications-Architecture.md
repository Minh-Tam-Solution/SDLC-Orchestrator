# ADR-049: Real-Time Notifications Architecture

**Status**: APPROVED
**Date**: February 4, 2026
**Sprint**: Sprint 153 (Real-time Notifications)
**Author**: CTO + AI Assistant
**Framework**: SDLC 6.1.0

---

## Context

SDLC Orchestrator needs a real-time notification system to:
1. Push gate approval/rejection events instantly to team members
2. Notify users of evidence uploads and policy violations
3. Support browser push notifications for offline users
4. Provide configurable user preferences for notification channels

### Current State (Pre-Sprint 153)

- Email notifications only (async, delayed)
- No WebSocket infrastructure
- No browser push capability
- Manual page refresh for status updates

### Requirements

| Requirement | Priority | Source |
|-------------|----------|--------|
| Real-time gate status updates | P0 | User feedback |
| In-app notification center | P0 | UX research |
| Browser push notifications | P1 | Mobile users |
| User notification preferences | P1 | Enterprise customers |
| Quiet hours support | P2 | Enterprise customers |

---

## Decision

Implement a **3-Channel Notification Architecture**:

1. **WebSocket Channel** - Real-time in-app updates
2. **Push Notification Channel** - Browser push (Web Push API)
3. **Email Channel** - Async delivery (existing)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION TRIGGERS                         │
│  Gate Events │ Evidence Events │ Policy Events │ Team Events    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  NOTIFICATION SERVICE                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              _send_to_all_channels()                        ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           ││
│  │  │  WebSocket  │ │    Push     │ │    Email    │           ││
│  │  │   Channel   │ │   Channel   │ │   Channel   │           ││
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           ││
│  └─────────┼───────────────┼───────────────┼───────────────────┘│
└────────────┼───────────────┼───────────────┼────────────────────┘
             │               │               │
             ▼               ▼               ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ WebSocket Mgr  │ │ Web Push API   │ │ SMTP Service   │
│ (In-Memory)    │ │ (VAPID Keys)   │ │ (SendGrid)     │
└────────────────┘ └────────────────┘ └────────────────┘
             │               │               │
             ▼               ▼               ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Browser WS     │ │ Service Worker │ │ Email Inbox    │
│ Connection     │ │ sw-push.js     │ │                │
└────────────────┘ └────────────────┘ └────────────────┘
```

### WebSocket Architecture

**Connection Management**:
```python
class WebSocketManager:
    connections: Dict[str, WebSocketConnection]  # user_id -> connection
    project_subscriptions: Dict[str, Set[str]]   # project_id -> user_ids

    async def connect(user_id, websocket)
    async def disconnect(user_id)
    async def subscribe_to_project(user_id, project_id)
    async def broadcast_to_project(project_id, event)
    async def send_to_user(user_id, event)
```

**Event Types** (20 total):
```yaml
connection:
  - connected
  - disconnected
  - ping
  - pong

gates:
  - gate_approved
  - gate_rejected
  - gate_approval_required

evidence:
  - evidence_uploaded

violations:
  - policy_violation

comments:
  - comment_added

notifications:
  - notification_read
  - notification_created

project:
  - project_updated
  - member_added
  - member_removed

sase:
  - vcr_created
  - vcr_updated
  - mrp_validated

context_authority:
  - context_snapshot_created
  - template_updated
```

### Push Notification Architecture

**Service Worker** (`sw-push.js`):
```javascript
self.addEventListener('push', (event) => {
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      data: { url: data.url },
      actions: getNotificationActions(data.type)
    })
  );
});
```

**VAPID Authentication**:
- Public key exposed via `/push/vapid-key`
- Private key stored in environment variables
- Subscription saved to database per user

### User Preferences Schema

```typescript
interface NotificationPreferences {
  // Channel preferences
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;

  // Notification type preferences
  gate_notifications: boolean;
  evidence_notifications: boolean;
  policy_notifications: boolean;
  team_notifications: boolean;
  system_notifications: boolean;

  // Quiet hours
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;  // "22:00"
  quiet_hours_end: string;    // "08:00"

  // Email digest
  email_digest_enabled: boolean;
  email_digest_frequency: 'daily' | 'weekly' | 'never';
}
```

---

## Alternatives Considered

### Alternative 1: Server-Sent Events (SSE)

**Pros**:
- Simpler server implementation
- Works over HTTP/2
- Auto-reconnection built-in

**Cons**:
- Unidirectional (server → client only)
- No binary data support
- Limited browser support for older browsers

**Decision**: Rejected - WebSocket bidirectional needed for subscriptions

### Alternative 2: Firebase Cloud Messaging (FCM)

**Pros**:
- Google infrastructure
- Mobile app support
- High deliverability

**Cons**:
- Vendor lock-in (Google)
- Additional cost at scale
- Privacy concerns (data goes through Google)
- AGPL compatibility concerns

**Decision**: Rejected - Web Push API is standard-based and vendor-neutral

### Alternative 3: Socket.IO

**Pros**:
- Fallback to long-polling
- Room/namespace support
- Large ecosystem

**Cons**:
- Additional dependency
- FastAPI native WebSocket sufficient
- Overhead for our use case

**Decision**: Rejected - FastAPI native WebSocket is lighter and sufficient

---

## Consequences

### Positive

1. **Instant Updates**: Users see gate status changes in <100ms
2. **Reduced Polling**: Eliminates need for frontend polling
3. **Offline Notifications**: Push notifications work when browser closed
4. **User Control**: Configurable preferences per user
5. **Scalability**: Project-based subscriptions reduce message volume

### Negative

1. **Connection Management**: Need to handle reconnection gracefully
2. **Server Memory**: WebSocket connections consume memory
3. **VAPID Key Management**: Additional secret to manage
4. **Service Worker Complexity**: Browser compatibility considerations

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Connection drops | Auto-reconnect with exponential backoff |
| Memory pressure | Connection limits per user (max 5) |
| Push permission denied | Graceful fallback to email |
| Service worker update | Version check and auto-update |

---

## Implementation

### Sprint 153 Deliverables

| Day | Deliverable | LOC |
|-----|-------------|-----|
| Day 1 | WebSocket Infrastructure | ~1,800 |
| Day 2 | Gate Status Push | ~365 |
| Day 3 | Notification Center UI | ~515 |
| Day 4 | Browser Push Notifications | ~1,090 |
| Day 5 | User Preferences | ~470 |
| **Total** | | **~4,240** |

### API Endpoints

**WebSocket**:
- `GET /api/v2/ws` - WebSocket connection (JWT auth)
- `GET /ws/stats` - Connection statistics
- `POST /ws/broadcast/project/{id}` - Admin broadcast

**Push**:
- `GET /push/vapid-key` - Public VAPID key
- `POST /push/subscribe` - Save subscription
- `POST /push/unsubscribe` - Remove subscription
- `GET /push/status` - Check subscription status
- `GET /push/subscriptions` - List subscriptions

**Preferences**:
- `GET /notifications/preferences` - Get user preferences
- `PUT /notifications/preferences` - Update preferences

### Test Coverage

- 19 unit tests (WebSocket manager)
- 13 integration tests (gate WebSocket events)
- Manual testing for push notifications

---

## References

- [Web Push API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [VAPID Specification](https://datatracker.ietf.org/doc/html/draft-ietf-webpush-vapid-01)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Service Worker Specification](https://w3c.github.io/ServiceWorker/)

---

## Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| CTO | - | Feb 4, 2026 | ✅ APPROVED |
| Frontend Lead | - | Feb 4, 2026 | ✅ APPROVED |
| Backend Lead | - | Feb 4, 2026 | ✅ APPROVED |

---

**Document Status**: APPROVED
**Implementation Status**: ✅ COMPLETE (Sprint 153)
**Exit Criteria**: 9/9 (100%)
