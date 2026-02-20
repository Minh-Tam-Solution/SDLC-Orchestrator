"""
==========================================================================
AuditLog Model — Sprint 185 (Advanced Audit Trail, SOC2 Type II)
SDLC Orchestrator — ENTERPRISE Tier

Purpose:
- Immutable, append-only audit event store
- Covers: gate actions, evidence access, user admin, tier changes, SSO events
- 90-day retention window (configurable via AUDIT_LOG_RETENTION_DAYS)
- SOC2 Type II: provides tamper-evidence for security controls

Immutability Guarantee:
- PostgreSQL trigger (applied in s185_001 migration) raises EXCEPTION on
  any UPDATE or DELETE — enforced at the DB engine level, bypasses ORM
- AuditLog.create_event() is the ONLY write path (no .update(), no .delete())

Architecture:
- id           : UUID — primary key, indexed
- event_type   : string — gate_action / evidence_access / user_admin /
                           tier_change / sso_event / api_key_event / export_event
- actor_id     : UUID string — user who performed the action (null = system)
- actor_email  : string — captured at event time (stable even if email changes)
- organization_id: UUID string — tenant for row-level reporting
- resource_type: string — gate / evidence / user / tier / sso_config / api_key
- resource_id  : UUID string — ID of affected resource
- action       : string — verb: create / approve / reject / download /
                           update / delete / login / logout / export
- detail       : JSONB — event-specific payload (e.g., gate_type, tier_before/after)
- ip_address   : string — IPv4 or IPv6 of request origin
- user_agent   : string — truncated to 512 chars
- tier_at_event: string — LITE/STANDARD/PROFESSIONAL/ENTERPRISE at event time
- created_at   : timestamptz — indexed (retention queries, timeline export)

SOC2 Type II Controls Covered:
  CC6.1  — logical access controls (user_admin events)
  CC6.2  — credential management (sso_event, api_key_event)
  CC6.6  — logical access revocation (user_admin.action=deactivate)
  CC7.2  — monitoring of system components (gate_action, tier_change)
  CC8.1  — change management (gate_action.action=approve)
  A1.2   — system availability (uptime/health log events)

SDLC 6.1.0 — Sprint 185 P0 Deliverable
Authority: CTO + CPO Approved (ADR-059, Sprint 185)
==========================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base_class import Base


class AuditLog(Base):
    """
    Append-only audit event record.

    IMPORTANT — Immutability contract:
        This table has a PostgreSQL trigger (prevent_audit_log_modifications)
        that raises EXCEPTION on any UPDATE or DELETE attempt.
        Use AuditLog.create_event() factory method to write events.
        Do NOT call db.delete() or UPDATE SQL on this model.

    Attributes:
        id              : UUID primary key (auto-generated)
        event_type      : Broad event category (see EVENT_TYPES)
        actor_id        : UUID of the acting user (None for system events)
        actor_email     : Email captured at event time
        organization_id : Organization UUID for tenant isolation
        resource_type   : Type of affected resource (see RESOURCE_TYPES)
        resource_id     : UUID of affected resource
        action          : Specific action verb (see ACTION_VERBS)
        detail          : JSONB payload with event-specific data
        ip_address      : IPv4 or IPv6 of request (≤45 chars)
        user_agent      : HTTP User-Agent header (truncated to 512)
        tier_at_event   : Subscription tier at time of event
        created_at      : UTC timestamp (indexed, immutable)
    """

    __tablename__ = "audit_logs"

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Event classification
    event_type = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)

    # Actor (who)
    actor_id = Column(String(36), nullable=True, index=True)   # null = system/automated
    actor_email = Column(String(254), nullable=True)

    # Tenant scope
    organization_id = Column(String(36), nullable=True, index=True)

    # Affected resource (what)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(36), nullable=True, index=True)

    # Context
    detail = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)             # max IPv6 length
    user_agent = Column(String(512), nullable=True)

    # Tier snapshot
    tier_at_event = Column(String(32), nullable=True)

    # Timestamp — NEVER UPDATE this column (trigger enforces it)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_org_created", "organization_id", "created_at"),
        Index("ix_audit_actor_created", "actor_id", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
        # extend_existing=True: this model is imported early (before the legacy
        # AuditLog in support.py) via tests/conftest.py pre-import ordering.
        # The dict entry at the end of the tuple is the SQLAlchemy way to pass
        # keyword arguments alongside Index objects in __table_args__.
        {"extend_existing": True},
    )

    # -------------------------------------------------------------------------
    # Allowed enumeration values (documentation — not enforced at ORM level;
    # the DB trigger enforces immutability, not field constraints)
    # -------------------------------------------------------------------------

    EVENT_TYPES = frozenset({
        "gate_action",       # Gate lifecycle: create, evaluate, submit, approve, reject
        "evidence_access",   # Evidence upload, download, verify
        "user_admin",        # User create, deactivate, role change
        "tier_change",       # Subscription tier upgrade / downgrade
        "sso_event",         # SSO login, logout, JIT provisioning
        "api_key_event",     # API key create, revoke
        "export_event",      # Audit log export, SOC2 pack generation
        "system_event",      # Health, maintenance, migration
    })

    ACTION_VERBS = frozenset({
        "create", "read", "update", "delete",
        "approve", "reject", "submit", "evaluate",
        "upload", "download", "verify",
        "login", "logout", "provision",
        "export", "generate",
        "activate", "deactivate",
        "grant", "revoke",
    })

    RESOURCE_TYPES = frozenset({
        "gate", "evidence", "user", "organization",
        "tier", "sso_config", "api_key", "audit_log",
        "jira_connection", "compliance_pack",
    })

    # -------------------------------------------------------------------------
    # Factory method — ONLY write path for AuditLog rows
    # -------------------------------------------------------------------------

    @classmethod
    def create_event(
        cls,
        event_type: str,
        action: str,
        actor_id: str | None = None,
        actor_email: str | None = None,
        organization_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        detail: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        tier_at_event: str | None = None,
    ) -> "AuditLog":
        """
        Create an AuditLog instance ready to be added to a DB session.

        This is the canonical factory method — all audit events MUST be
        created through this method to ensure correct field population.

        Args:
            event_type      : One of AuditLog.EVENT_TYPES
            action          : One of AuditLog.ACTION_VERBS
            actor_id        : UUID string of acting user (None for system)
            actor_email     : Email captured at event time
            organization_id : Organization UUID
            resource_type   : One of AuditLog.RESOURCE_TYPES
            resource_id     : UUID string of affected resource
            detail          : Arbitrary JSONB payload
            ip_address      : Request IP address
            user_agent      : HTTP User-Agent (truncated to 512)
            tier_at_event   : Subscription tier at event time

        Returns:
            AuditLog instance (not yet flushed to DB)

        Example:
            event = AuditLog.create_event(
                event_type="gate_action",
                action="approve",
                actor_id=str(user.id),
                actor_email=user.email,
                organization_id=str(user.organization_id),
                resource_type="gate",
                resource_id=str(gate.id),
                detail={"gate_type": "G3", "project_id": str(gate.project_id)},
                ip_address=request.client.host,
                tier_at_event=user.effective_tier,
            )
            db.add(event)
            await db.commit()
        """
        return cls(
            event_type=event_type,
            action=action,
            actor_id=str(actor_id) if actor_id else None,
            actor_email=actor_email,
            organization_id=str(organization_id) if organization_id else None,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            detail=detail,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:512] or None,
            tier_at_event=tier_at_event,
        )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, event_type={self.event_type!r}, "
            f"action={self.action!r}, actor={self.actor_email!r}, "
            f"created_at={self.created_at})>"
        )
