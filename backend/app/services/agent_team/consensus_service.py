"""Consensus Service — Sprint 221 (P2 Group Consensus).

Multi-agent voting with quorum detection and race condition protection.

INVARIANT: Consensus is advisory — CANNOT bypass EP-07 gates.
Quorum result = evidence returned to EP-07 gate. Gate still decides PASS/FAIL.

References: ADR-070, Sprint 221 Plan, CTO F3 (@vote syntax).
"""

import logging
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import escape as xml_escape
import uuid
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

from app.models.consensus_session import ConsensusSession, ConsensusVote
from app.models.agent_definition import AgentDefinition

@dataclass
class QuorumResult:
    reached: bool
    decision: Optional[str]
    votes_for: int
    votes_against: int
    votes_abstain: int

class ConsensusService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        conversation_id: uuid.UUID,
        topic: str,
        created_by: uuid.UUID,
        quorum_type: str = "majority",
        required_voters: List[str] = None,
        timeout_seconds: int = 300,
        threshold_pct: float = 0.67
    ) -> ConsensusSession:
        if quorum_type not in ["majority", "unanimous", "threshold"]:
            raise ValueError(f"Invalid quorum_type: {quorum_type}")

        if required_voters is None:
            required_voters = []

        session = ConsensusSession(
            conversation_id=conversation_id,
            topic=topic,
            created_by=created_by,
            quorum_type=quorum_type,
            required_voters=required_voters,
            timeout_seconds=timeout_seconds,
            threshold_pct=threshold_pct,
            status="open"
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def cast_vote(
        self,
        session_id: uuid.UUID,
        voter_agent_id: uuid.UUID,
        vote: str,
        reasoning: Optional[str] = None
    ) -> ConsensusVote:
        if vote not in ["approve", "reject", "abstain"]:
            raise ValueError("Vote must be approve, reject, or abstain")

        # 1. Check if session exists and voter is authorized
        session = await self.db.get(ConsensusSession, session_id)
        if not session:
            raise ValueError("Session not found")
            
        if session.status not in ["open", "voting"]:
            raise ValueError(f"Session is already {session.status}")

        # Check required voters (stored as list of UUID strings/strings)
        required_voters_str = [str(v) for v in session.required_voters]
        if str(voter_agent_id) not in required_voters_str:
            raise ValueError("Not authorized to vote in this session")

        new_vote = ConsensusVote(
            session_id=session_id,
            voter_agent_id=voter_agent_id,
            vote=vote,
            reasoning=reasoning
        )
        self.db.add(new_vote)
        
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Agent has already voted in this session")

        # Change status if it's open
        if session.status == "open":
            session.status = "voting"
            await self.db.flush()

        # Check quorum logic
        await self.db.refresh(new_vote)
        
        # 2. Race condition protection: SELECT FOR UPDATE
        query = select(ConsensusSession).where(ConsensusSession.id == session_id).with_for_update()
        result = await self.db.execute(query)
        locked_session = result.scalar_one_or_none()
        
        if not locked_session or locked_session.decided_by_vote_id is not None:
            return new_vote # Quorum already handled or session gone
            
        quorum_result = await self.check_quorum(session_id)
        if quorum_result.reached:
            # Update session to decided
            locked_session.status = "decided"
            locked_session.result = {
                "decision": quorum_result.decision,
                "votes_for": quorum_result.votes_for,
                "votes_against": quorum_result.votes_against,
                "votes_abstain": quorum_result.votes_abstain
            }
            locked_session.decided_by_vote_id = new_vote.id
            locked_session.closed_at = datetime.now(timezone.utc)
            await self.db.flush()

        return new_vote

    async def check_quorum(self, session_id: uuid.UUID) -> QuorumResult:
        # Get all votes for session
        votes_result = await self.db.execute(
            select(ConsensusVote).where(ConsensusVote.session_id == session_id)
        )
        votes = votes_result.scalars().all()
        
        session = await self.db.get(ConsensusSession, session_id)
        
        votes_for = sum(1 for v in votes if v.vote == "approve")
        votes_against = sum(1 for v in votes if v.vote == "reject")
        votes_abstain = sum(1 for v in votes if v.vote == "abstain")
        total_voters = len(session.required_voters)
        voted_count = len(votes)
        pending = total_voters - voted_count

        if session.quorum_type == "majority":
            required_to_approve = math.floor(total_voters / 2) + 1
            if votes_for >= required_to_approve:
                return QuorumResult(True, "approve", votes_for, votes_against, votes_abstain)
            if votes_against + votes_abstain + pending == 0 and votes_for < required_to_approve:
                return QuorumResult(True, "reject", votes_for, votes_against, votes_abstain)
            if votes_against >= required_to_approve:
                return QuorumResult(True, "reject", votes_for, votes_against, votes_abstain)
            if pending == 0:
                # all voted, no one reached majority ? Like tie? Treat as reject if tie.
                return QuorumResult(True, "reject", votes_for, votes_against, votes_abstain)

        elif session.quorum_type == "unanimous":
            if votes_against > 0:
                return QuorumResult(True, "reject", votes_for, votes_against, votes_abstain)
            if votes_for == total_voters:
                return QuorumResult(True, "approve", votes_for, votes_against, votes_abstain)

        elif session.quorum_type == "threshold":
            threshold = float(session.threshold_pct)
            required = math.ceil(total_voters * threshold)
            if votes_for >= required:
                return QuorumResult(True, "approve", votes_for, votes_against, votes_abstain)
            if votes_for + pending < required:
                return QuorumResult(True, "reject", votes_for, votes_against, votes_abstain)
            if pending == 0:
                return QuorumResult(True, "reject", votes_for, votes_against, votes_abstain)

        return QuorumResult(False, None, votes_for, votes_against, votes_abstain)

    async def close_session(self, session_id: uuid.UUID, agent_id: uuid.UUID, reason: str, is_lead: bool = False) -> ConsensusSession:
        session = await self.db.get(ConsensusSession, session_id)
        if not session:
            raise ValueError("Session not found")
        if session.status not in ["open", "voting"]:
            raise ValueError(f"Cannot cancel session in {session.status} status")
            
        if not is_lead and str(session.created_by) != str(agent_id):
            raise ValueError("Authorization error: Only creator or team lead can cancel the session")
            
        session.status = "cancelled"
        session.result = {"decision": "cancelled", "reason": reason}
        session.closed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return session
        
    async def timeout_expired_sessions(self) -> list:
        """Find and mark expired sessions as timed out.

        Scans for open/voting sessions past their timeout_seconds TTL.

        Returns:
            List of sessions that were timed out.
        """
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(ConsensusSession).where(
                ConsensusSession.status.in_(["open", "voting"])
            )
        )
        sessions = list(result.scalars().all())
        timed_out = []

        for session in sessions:
            created = session.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            deadline = created + timedelta(seconds=session.timeout_seconds)
            if now > deadline:
                session.status = "timeout"
                session.closed_at = now
                session.result = {"decision": "timeout", "reason": "TTL expired"}
                timed_out.append(session)

        if timed_out:
            await self.db.flush()
            logger.info(
                "TRACE_CONSENSUS: timed out %d sessions", len(timed_out)
            )

        return timed_out

    async def build_consensus_md(self, conversation_id: uuid.UUID | None) -> str:
        """Build <active_votes> context section for agent injection.

        Simplified version for context_injector — shows open/voting sessions
        with vote tallies. Called by context_injector.inject_context().

        Args:
            conversation_id: Conversation to scope sessions.

        Returns:
            XML string wrapped in <active_votes> tags, or empty string.
        """
        if conversation_id is None:
            return ""

        result = await self.db.execute(
            select(ConsensusSession).where(
                and_(
                    ConsensusSession.conversation_id == conversation_id,
                    ConsensusSession.status.in_(["open", "voting"]),
                )
            )
        )
        sessions = list(result.scalars().all())

        if not sessions:
            return ""

        lines = [
            "## Active Votes\n",
            "The following consensus sessions are awaiting your vote:\n",
        ]

        for session in sessions:
            topic = xml_escape(session.topic)
            qtype = xml_escape(session.quorum_type)
            required = len(session.required_voters) if session.required_voters else 0

            # Count votes from loaded relationship
            votes = session.votes if session.votes else []
            approve = sum(1 for v in votes if v.vote == "approve")
            reject = sum(1 for v in votes if v.vote == "reject")
            abstain = sum(1 for v in votes if v.vote == "abstain")
            total = len(votes)

            lines.append(
                f"- **{topic}** (quorum: {qtype}, "
                f"votes: {total}/{required} — "
                f"approve: {approve}, reject: {reject}, abstain: {abstain})"
            )

        lines.append(
            "\nCast your vote using: `@vote approve|reject|abstain \"reasoning\"`"
        )

        content = "\n".join(lines)
        return f"<active_votes>\n{content}\n</active_votes>"

