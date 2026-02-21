"""
=========================================================================
GDPRService — Data Subject Rights + Consent Management (ADR-063)
SDLC Orchestrator — Sprint 186 (Multi-Region Data Residency)

Version: 1.0.0
Date: 2026-02-20
Status: ACTIVE — Sprint 186 P0
Authority: CTO Approved (ADR-063, GDPR Art. 7, 15, 17)

Purpose:
- Handle Data Subject Access Requests (DSAR) — GDPR Art. 15
- Handle Right to Erasure requests — GDPR Art. 17
- Manage processing consent audit trail — GDPR Art. 7
- 30-day GDPR response deadline enforcement

Scope (Sprint 186):
  ✅ DSAR creation + status tracking
  ✅ Consent log record/withdraw
  ✅ User data export (metadata only — file content excluded from MVP)
  ⏳ Automated PII purge (Sprint 187 — legal review required first)

Zero Mock Policy: Real SQLAlchemy models + async session.
=========================================================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# GDPR 30-day response deadline (Art. 12.3)
_GDPR_RESPONSE_DAYS = 30


# ---------------------------------------------------------------------------
# Inline SQLAlchemy models (avoid circular imports)
# We declare the table references here rather than importing full models.
# The actual ORM models are in app/models/gdpr.py (future sprint);
# for Sprint 186 we use core SQL for DSAR + consent operations.
# ---------------------------------------------------------------------------

class GDPRService:
    """
    Handles GDPR Data Subject Rights operations.

    Usage:
        svc = GDPRService(db)
        req = await svc.create_dsar(user_id, "access", "user@example.com")
        export = await svc.get_user_data_export(user_id)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # DSAR — Data Subject Access Requests
    # -------------------------------------------------------------------------

    async def create_dsar(
        self,
        requester_email: str,
        request_type: str,
        user_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> dict:
        """
        Create a new Data Subject request (GDPR Art. 15 / Art. 17).

        Args:
            requester_email: Email of the person making the request.
            request_type: 'access' | 'erasure' | 'portability' | 'rectification'
            user_id: Optional UUID of the requesting user (if authenticated).
            description: Optional free-text description of the request.

        Returns:
            Dict with the created DSAR record (id, status, due_at, ...).
        """
        from sqlalchemy import text

        valid_types = ("access", "erasure", "portability", "rectification")
        if request_type not in valid_types:
            raise ValueError(
                f"Invalid request_type '{request_type}'. Valid: {valid_types}"
            )

        now = datetime.now(timezone.utc)
        due_at = now + timedelta(days=_GDPR_RESPONSE_DAYS)
        dsar_id = uuid4()

        await self.db.execute(
            text("""
                INSERT INTO gdpr_dsar_requests
                    (id, user_id, request_type, status, requester_email,
                     description, created_at, updated_at, due_at)
                VALUES
                    (:id, :user_id, :request_type, 'pending', :requester_email,
                     :description, :created_at, :updated_at, :due_at)
            """),
            {
                "id": dsar_id,
                "user_id": user_id,
                "request_type": request_type,
                "requester_email": requester_email,
                "description": description,
                "created_at": now,
                "updated_at": now,
                "due_at": due_at,
            },
        )
        await self.db.commit()

        logger.info(
            "GDPR DSAR created: id=%s type=%s email=%s due=%s",
            dsar_id,
            request_type,
            requester_email,
            due_at.date(),
        )

        return {
            "id": str(dsar_id),
            "request_type": request_type,
            "status": "pending",
            "requester_email": requester_email,
            "description": description,
            "created_at": now.isoformat(),
            "due_at": due_at.isoformat(),
        }

    async def get_dsar_status(self, dsar_id: UUID) -> Optional[dict]:
        """
        Retrieve the status of a DSAR request.

        Returns None if the request does not exist.
        Returns user_id in the dict so the caller can enforce ownership.
        """
        from sqlalchemy import text

        row = (
            await self.db.execute(
                text("""
                    SELECT id, user_id, request_type, status, requester_email,
                           dpo_notes, created_at, updated_at, due_at, completed_at
                    FROM gdpr_dsar_requests
                    WHERE id = :id
                """),
                {"id": dsar_id},
            )
        ).fetchone()

        if row is None:
            return None

        return {
            "id": str(row.id),
            # user_id is returned so the route layer can enforce ownership (F-01)
            "user_id": str(row.user_id) if row.user_id else None,
            "request_type": row.request_type,
            "status": row.status,
            "requester_email": row.requester_email,
            "dpo_notes": row.dpo_notes,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "due_at": row.due_at.isoformat() if row.due_at else None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        }

    async def list_dsar_requests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        organization_id: Optional[UUID] = None,
    ) -> list[dict]:
        """
        List DSAR requests (DPO dashboard).

        F-01: Scoped to organization_id via JOIN through users table when provided.
        F-05: Uses fully-parameterized SQL — no f-string interpolation.

        Args:
            status: Optional status filter ('pending', 'processing', 'completed', etc.)
            limit: Max records to return.
            offset: Pagination offset.
            organization_id: When provided, restricts to requests from users in this org.
        """
        from sqlalchemy import text

        # Fully parameterized query — no f-string interpolation (F-05 fix).
        # org-scope: JOIN users table; when organization_id is NULL the condition is a no-op.
        query = text("""
            SELECT d.id, d.request_type, d.status, d.requester_email,
                   d.created_at, d.due_at, d.completed_at
            FROM gdpr_dsar_requests d
            JOIN users u ON d.user_id = u.id
            WHERE (:status_filter IS NULL OR d.status = :status_filter)
              AND (:org_id IS NULL OR u.organization_id = :org_id)
            ORDER BY d.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        rows = (
            await self.db.execute(
                query,
                {
                    "status_filter": status,
                    "org_id": organization_id,
                    "limit": limit,
                    "offset": offset,
                },
            )
        ).fetchall()

        return [
            {
                "id": str(r.id),
                "request_type": r.request_type,
                "status": r.status,
                "requester_email": r.requester_email,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "due_at": r.due_at.isoformat() if r.due_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in rows
        ]

    async def get_user_data_export(self, user_id: UUID) -> dict:
        """
        Collect all data held about a user for a DSAR access request.

        Returns a summary of data categories + record counts.
        For full data export, an S3 presigned URL is generated (future sprint).

        Args:
            user_id: UUID of the user.

        Returns:
            Dict with data categories and record counts (GDPR Art. 15 response).
        """
        from sqlalchemy import text

        now = datetime.now(timezone.utc)

        # Count records per category (no PII exposure — counts only)
        counts = {}

        for table, col in [
            ("agent_messages", "created_by"),
            ("gate_evidence", "uploaded_by"),
            ("audit_logs", "actor_id"),
            ("gdpr_consent_logs", "user_id"),
            ("gdpr_dsar_requests", "user_id"),
        ]:
            try:
                result = await self.db.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE {col} = :uid"),
                    {"uid": user_id},
                )
                counts[table] = result.scalar_one()
            except Exception:
                counts[table] = "unavailable"

        logger.info("GDPR data export summary generated for user %s", user_id)

        return {
            "user_id": str(user_id),
            "generated_at": now.isoformat(),
            "data_categories": {
                "agent_messages": counts.get("agent_messages", 0),
                "evidence_uploads": counts.get("gate_evidence", 0),
                "audit_events": counts.get("audit_logs", 0),
                "consent_records": counts.get("gdpr_consent_logs", 0),
                "dsar_requests": counts.get("gdpr_dsar_requests", 0),
            },
            "note": (
                "Full data export (with PII) requires DPO review. "
                "Submit a DSAR access request via POST /gdpr/dsar."
            ),
        }

    async def get_full_data_export(self, user_id: UUID) -> dict:
        """
        Full machine-readable PII export for the authenticated user (GDPR Art. 20).

        Returns all personal data held across 5 data categories:
          - user_profile: account info (email, full_name, role, created_at, last_login)
          - consent_records: all consent decisions with purpose + granted flag
          - dsar_requests: history of data subject requests submitted
          - agent_messages: messages sent by this user in multi-agent conversations
          - evidence_metadata: files uploaded by this user (metadata only, no content)

        Rate limit: 1 request per user per 24 hours (enforced in the route layer).

        Args:
            user_id: UUID of the authenticated user.

        Returns:
            Dict conforming to FR-045 Art.20 JSON schema.
        """
        from sqlalchemy import text

        now = datetime.now(timezone.utc)
        uid_str = str(user_id)

        # 1 — User profile (no password_hash / mfa_secret)
        user_row = (
            await self.db.execute(
                text("""
                    SELECT email, full_name, role, created_at, last_login, organization_id
                    FROM users
                    WHERE id = :uid AND deleted_at IS NULL
                """),
                {"uid": user_id},
            )
        ).fetchone()

        if user_row is None:
            raise ValueError(f"User {user_id} not found")

        user_profile = {
            "email": user_row.email,
            "full_name": user_row.full_name,
            "role": str(user_row.role) if user_row.role else None,
            "organization_id": str(user_row.organization_id) if user_row.organization_id else None,
            "account_created_at": user_row.created_at.isoformat() if user_row.created_at else None,
            "last_login": user_row.last_login.isoformat() if user_row.last_login else None,
        }

        # 2 — Consent records (full history, newest first)
        consent_rows = (
            await self.db.execute(
                text("""
                    SELECT id, purpose, granted, version, created_at, withdrawn_at
                    FROM gdpr_consent_logs
                    WHERE user_id = :uid
                    ORDER BY created_at DESC
                """),
                {"uid": user_id},
            )
        ).fetchall()

        consent_records = [
            {
                "id": str(r.id),
                "purpose": r.purpose,
                "granted": r.granted,
                "policy_version": r.version,
                "consented_at": r.created_at.isoformat() if r.created_at else None,
                "withdrawn_at": r.withdrawn_at.isoformat() if r.withdrawn_at else None,
            }
            for r in consent_rows
        ]

        # 3 — DSAR history
        dsar_rows = (
            await self.db.execute(
                text("""
                    SELECT id, request_type, status, requester_email,
                           created_at, due_at, completed_at
                    FROM gdpr_dsar_requests
                    WHERE user_id = :uid
                    ORDER BY created_at DESC
                """),
                {"uid": user_id},
            )
        ).fetchall()

        dsar_requests = [
            {
                "id": str(r.id),
                "request_type": r.request_type,
                "status": r.status,
                "requester_email": r.requester_email,
                "submitted_at": r.created_at.isoformat() if r.created_at else None,
                "due_at": r.due_at.isoformat() if r.due_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in dsar_rows
        ]

        # 4 — Agent messages sent by this user (limit 1000 most recent)
        #     sender_id stores the UUID as a plain string in the messages table.
        msg_rows = (
            await self.db.execute(
                text("""
                    SELECT id, conversation_id, content, message_type, created_at,
                           provider_used
                    FROM agent_messages
                    WHERE sender_id = :uid_str AND sender_type = 'human'
                    ORDER BY created_at DESC
                    LIMIT 1000
                """),
                {"uid_str": uid_str},
            )
        ).fetchall()

        agent_messages = [
            {
                "id": str(r.id),
                "conversation_id": str(r.conversation_id),
                "content": r.content,
                "message_type": r.message_type,
                "sent_at": r.created_at.isoformat() if r.created_at else None,
                "provider_used": r.provider_used,
            }
            for r in msg_rows
        ]

        # 5 — Evidence uploaded by this user (metadata only — no file contents)
        ev_rows = (
            await self.db.execute(
                text("""
                    SELECT id, gate_id, file_name, file_size, evidence_type,
                           source, description, uploaded_at, created_at
                    FROM gate_evidence
                    WHERE uploaded_by = :uid AND deleted_at IS NULL
                    ORDER BY created_at DESC
                """),
                {"uid": user_id},
            )
        ).fetchall()

        evidence_metadata = [
            {
                "id": str(r.id),
                "gate_id": str(r.gate_id),
                "file_name": r.file_name,
                "file_size_bytes": r.file_size,
                "evidence_type": r.evidence_type,
                "source": r.source,
                "description": r.description,
                "uploaded_at": (
                    r.uploaded_at.isoformat() if r.uploaded_at
                    else (r.created_at.isoformat() if r.created_at else None)
                ),
            }
            for r in ev_rows
        ]

        logger.info(
            "GDPR Art.20 full export generated: user=%s consents=%d dsars=%d msgs=%d evidence=%d",
            user_id,
            len(consent_records),
            len(dsar_requests),
            len(agent_messages),
            len(evidence_metadata),
        )

        return {
            "exported_at": now.isoformat(),
            "user_id": uid_str,
            "data_format": "GDPR Art.20 machine-readable export",
            "user_profile": user_profile,
            "consent_records": consent_records,
            "dsar_requests": dsar_requests,
            "agent_messages": agent_messages,
            "evidence_metadata": evidence_metadata,
        }

    # -------------------------------------------------------------------------
    # Consent Management
    # -------------------------------------------------------------------------

    async def record_consent(
        self,
        user_id: UUID,
        purpose: str,
        granted: bool,
        version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Record a consent decision for a processing purpose.

        Args:
            user_id: User UUID.
            purpose: Processing purpose ('essential'|'analytics'|'marketing'|'ai_training'|'third_party').
            granted: True if consent given, False if withdrawn/denied.
            version: Privacy policy version at consent time.
            ip_address: Optional IP address.
            user_agent: Optional browser user agent.

        Returns:
            Dict with the created consent record.
        """
        from sqlalchemy import text

        valid_purposes = ("essential", "analytics", "marketing", "ai_training", "third_party")
        if purpose not in valid_purposes:
            raise ValueError(
                f"Invalid purpose '{purpose}'. Valid: {valid_purposes}"
            )

        now = datetime.now(timezone.utc)
        log_id = uuid4()

        await self.db.execute(
            text("""
                INSERT INTO gdpr_consent_logs
                    (id, user_id, purpose, granted, version,
                     ip_address, user_agent, created_at)
                VALUES
                    (:id, :user_id, :purpose, :granted, :version,
                     :ip_address, :user_agent, :created_at)
            """),
            {
                "id": log_id,
                "user_id": user_id,
                "purpose": purpose,
                "granted": granted,
                "version": version,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": now,
            },
        )
        await self.db.commit()

        logger.info(
            "GDPR consent recorded: user=%s purpose=%s granted=%s version=%s",
            user_id,
            purpose,
            granted,
            version,
        )

        return {
            "id": str(log_id),
            "user_id": str(user_id),
            "purpose": purpose,
            "granted": granted,
            "version": version,
            "created_at": now.isoformat(),
        }

    async def get_active_consents(self, user_id: UUID) -> list[dict]:
        """
        Return all active (not withdrawn) consents for a user.

        Args:
            user_id: User UUID.

        Returns:
            List of active consent records.
        """
        from sqlalchemy import text

        rows = (
            await self.db.execute(
                text("""
                    SELECT id, purpose, granted, version, created_at
                    FROM gdpr_consent_logs
                    WHERE user_id = :uid AND withdrawn_at IS NULL
                    ORDER BY created_at DESC
                """),
                {"uid": user_id},
            )
        ).fetchall()

        return [
            {
                "id": str(r.id),
                "purpose": r.purpose,
                "granted": r.granted,
                "version": r.version,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
