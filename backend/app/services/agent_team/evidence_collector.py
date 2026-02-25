"""
=========================================================================
Evidence Collector — Agent Output → Evidence Vault Bridge (ADR-056/EP-07)
SDLC Orchestrator - Sprint 178 (Team Orchestrator + Evidence + Traces)
Updated: Sprint 179 — Output credential scrubbing before hash (ADR-058 Pattern A)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 178
Authority: CTO Approved (ADR-056, FR-041)
Reference: ADR-056-Multi-Agent-Team-Engine.md
Reference: Evidence Vault API (Module 2)

Purpose:
- Capture agent outputs as GateEvidence records
- SHA256 content hashing for integrity verification
- Correlation ID linking: agent_message → gate_evidence
- Identity masquerading audit (Non-Negotiable #12): on_behalf_of tracking
- Only captures agent messages (not user/system messages)

Evidence Lifecycle for Agent Outputs:
  Orchestrator enqueues response → EvidenceCollector.capture_message()
  → Compute SHA256 → Create GateEvidence (gate_id=None, source='agent')
  → Link via agent_message.evidence_id FK
  → Evidence available for downstream Gate evaluation

Design Decisions:
- gate_id=None: Agent evidence isn't gate-tied at capture time
  (s178_001 migration makes gate_id nullable)
- evidence_type="AGENT_OUTPUT": New evidence classification
- source="agent": Distinguishes from cli/extension/web
- SHA256 on content only (not file-based, content is text)
- No processing_status gate: per CTO note, captures directly from content
  (response messages are 'pending' when first enqueued)
- Batch capture for multi-message workflows

Zero Mock Policy: Production-ready implementation with real SHA256.
=========================================================================
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_message import AgentMessage
from app.models.gate_evidence import GateEvidence
from app.services.agent_team.output_scrubber import OutputScrubber

logger = logging.getLogger(__name__)


class EvidenceCollectorError(Exception):
    """Base error for evidence collection operations."""


class EvidenceCollector:
    """
    Captures agent outputs as GateEvidence records in the Evidence Vault.

    Satisfies ADR-056 Non-Negotiable #12 (Identity Masquerading Audit):
    - Every agent action is recorded with on_behalf_of tracking
    - correlation_id links related evidence across multi-agent chains
    - SHA256 content hash ensures evidence immutability

    Usage:
        collector = EvidenceCollector(db)
        evidence = await collector.capture_message(
            message=response_msg,
            agent_name="coder",
            on_behalf_of="user:alice",
        )
        # message.evidence_id now links to the new evidence record
    """

    # Evidence settings
    S3_BUCKET = "sdlc-evidence"
    EVIDENCE_TYPE = "AGENT_OUTPUT"
    SOURCE = "agent"
    FILE_TYPE = "text/plain"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def capture_message(
        self,
        message: AgentMessage,
        agent_name: str,
        on_behalf_of: str | None = None,
        gate_id: UUID | None = None,
    ) -> GateEvidence | None:
        """
        Capture an agent message as evidence.

        Captures directly from message content without requiring
        processing_status='completed' (per CTO implementation note:
        response messages are 'pending' when first enqueued).

        Only captures messages where sender_type == 'agent'.

        Args:
            message: The AgentMessage to capture.
            agent_name: Name of the agent that produced this output.
            on_behalf_of: Identity masquerading audit — who the agent acts for.
            gate_id: Optional gate binding. None for gate-independent agent evidence.

        Returns:
            GateEvidence record if captured, None if message not eligible.
        """
        if message.sender_type != "agent":
            logger.debug(
                "TRACE_EVIDENCE skip_non_agent: msg_id=%s, sender_type=%s",
                message.id,
                message.sender_type,
            )
            return None

        now = datetime.now(timezone.utc)

        # Sprint 179 — ADR-058 Pattern A: scrub credentials BEFORE
        # computing SHA256 hash.  Order: scrub → hash → store.
        # Covers non-invoker paths (OTT gateway, manual API injection).
        scrubber = OutputScrubber()
        scrubbed_content, scrub_violations = scrubber.scrub(message.content)
        if scrub_violations:
            logger.warning(
                "TRACE_SCRUB_EVIDENCE msg_id=%s, patterns=%s",
                message.id,
                scrub_violations,
            )

        content_hash = self._compute_content_hash(scrubbed_content)
        content_bytes = len(scrubbed_content.encode("utf-8"))
        evidence_description = self._build_description(
            agent_name=agent_name,
            correlation_id=message.correlation_id,
            on_behalf_of=on_behalf_of,
            message_id=message.id,
            message_type=message.message_type,
            captured_at=now,
        )
        s3_key = self._build_s3_key(message)

        evidence = GateEvidence(
            id=uuid4(),
            gate_id=gate_id,
            file_name=f"agent-output-{message.id}.txt",
            file_size=content_bytes,
            file_type=self.FILE_TYPE,
            evidence_type=self.EVIDENCE_TYPE,
            s3_key=s3_key,
            s3_bucket=self.S3_BUCKET,
            sha256_hash=content_hash,
            sha256_server=content_hash,
            source=self.SOURCE,
            description=evidence_description,
            uploaded_at=now,
            created_at=now,
        )

        self.db.add(evidence)

        # Link message → evidence
        message.evidence_id = evidence.id
        await self.db.flush()

        logger.info(
            "TRACE_EVIDENCE capture_complete: evidence_id=%s, msg_id=%s, "
            "agent=%s, on_behalf_of=%s, correlation_id=%s, hash=%.16s",
            evidence.id,
            message.id,
            agent_name,
            on_behalf_of or "unknown",
            message.correlation_id,
            content_hash,
        )

        return evidence

    async def capture_batch(
        self,
        messages: list[AgentMessage],
        agent_name: str,
        on_behalf_of: str | None = None,
    ) -> list[GateEvidence]:
        """
        Capture multiple messages as evidence in a single transaction scope.

        Args:
            messages: List of AgentMessages to capture.
            agent_name: Agent that produced these outputs.
            on_behalf_of: Identity masquerading audit field.

        Returns:
            List of created GateEvidence records (skipped messages excluded).
        """
        captured: list[GateEvidence] = []

        for msg in messages:
            evidence = await self.capture_message(
                msg,
                agent_name=agent_name,
                on_behalf_of=on_behalf_of,
            )
            if evidence is not None:
                captured.append(evidence)

        logger.info(
            "TRACE_EVIDENCE batch_complete: captured=%d/%d, agent=%s",
            len(captured),
            len(messages),
            agent_name,
        )

        return captured

    async def capture_eval_report(
        self,
        report_content: str,
        evaluator_model: str,
        on_behalf_of: str | None = None,
    ) -> GateEvidence:
        """Capture an eval suite result as evidence (Sprint 202 — Track C).

        Creates a GateEvidence record with evidence_type='EVAL_REPORT'
        for automated eval suite runs. Not linked to a specific gate
        (gate_id=None) — used for quality trend tracking.

        Args:
            report_content: JSON-serialized eval suite result.
            evaluator_model: Model used for evaluation.
            on_behalf_of: Identity audit field.

        Returns:
            GateEvidence record for the eval report.
        """
        now = datetime.now(timezone.utc)

        content_hash = self._compute_content_hash(report_content)
        content_bytes = len(report_content.encode("utf-8"))

        description = json.dumps({
            "evidence_type": "EVAL_REPORT",
            "evaluator_model": evaluator_model,
            "on_behalf_of": on_behalf_of or "system",
            "captured_at": now.isoformat(),
        })

        evidence = GateEvidence(
            id=uuid4(),
            gate_id=None,
            file_name=f"eval-report-{now.strftime('%Y%m%d-%H%M%S')}.json",
            file_size=content_bytes,
            file_type="application/json",
            evidence_type="EVAL_REPORT",
            s3_key=f"evidence/evals/{now.strftime('%Y/%m/%d')}/report-{uuid4()}.json",
            s3_bucket=self.S3_BUCKET,
            sha256_hash=content_hash,
            sha256_server=content_hash,
            source="agent",
            description=description,
            uploaded_at=now,
            created_at=now,
        )

        self.db.add(evidence)
        await self.db.flush()

        logger.info(
            "TRACE_EVIDENCE: eval_report captured: evidence_id=%s, "
            "model=%s, hash=%.16s",
            evidence.id,
            evaluator_model,
            content_hash,
        )

        return evidence

    async def get_evidence_by_correlation(
        self,
        correlation_id: UUID,
    ) -> list[GateEvidence]:
        """
        Retrieve all evidence linked to messages sharing a correlation ID.

        This enables tracing all evidence produced within a single
        request lifecycle (Non-Negotiable #12: correlation_id).

        Args:
            correlation_id: The correlation UUID to search for.

        Returns:
            List of GateEvidence records linked to matching messages.
        """
        result = await self.db.execute(
            select(GateEvidence)
            .join(
                AgentMessage,
                AgentMessage.evidence_id == GateEvidence.id,
            )
            .where(AgentMessage.correlation_id == correlation_id)
            .order_by(GateEvidence.created_at.asc())
        )
        evidence_list = list(result.scalars().all())

        logger.debug(
            "TRACE_EVIDENCE: Correlation lookup: correlation=%s, found=%d",
            correlation_id,
            len(evidence_list),
        )
        return evidence_list

    @staticmethod
    def _compute_content_hash(content: str) -> str:
        """
        Compute SHA256 hash of message content.

        Uses UTF-8 encoding for deterministic hashing across platforms.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_description(
        agent_name: str,
        correlation_id: UUID,
        on_behalf_of: str | None,
        message_id: UUID,
        message_type: str,
        captured_at: datetime | None = None,
    ) -> str:
        """
        Build JSON description with audit fields.

        Non-Negotiable #12: Every agent action must record who the agent
        acts on behalf of for security audit trail.
        """
        ts = captured_at or datetime.now(timezone.utc)
        return json.dumps({
            "agent_name": agent_name,
            "correlation_id": str(correlation_id),
            "on_behalf_of": on_behalf_of or "unknown",
            "message_id": str(message_id),
            "message_type": message_type,
            "captured_at": ts.isoformat(),
        })

    @staticmethod
    def _build_s3_key(message: AgentMessage) -> str:
        """
        Build a unique S3 key for the evidence file.

        Format: evidence/agent/{conversation_id}/{message_id}.txt
        """
        conv_id = message.conversation_id or "orphan"
        return f"evidence/agent/{conv_id}/{message.id}.txt"
