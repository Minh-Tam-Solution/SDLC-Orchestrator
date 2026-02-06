"""
Tier Approval Service - Sprint 161

Tier-based gate approval routing service.

Sprint 161 Scope (Backend Foundation):
- Compute required roles based on tier + gate_code
- Create approval request (decision records)
- Record approval/rejection decision

Sprint 162+ (Out of Scope):
- OPA policy integration
- Delegation logic
- Escalation workflow
- Gate finalization

CTO v2.5 Adjustments Applied:
- ✅ Adjustment #1: ESCALATE enum in decision_action
- ✅ Adjustment #2: expires_at column with timeout support
- ✅ Adjustment #3: ApprovalChainMetadata return type

Reference: docs/04-build/02-Sprint-Plans/SPRINT-161-164-TIER-BASED-GATE-APPROVAL.md
"""

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.gate import Gate
from app.models.project import Project
from app.models.gate_decision import GateDecision
from app.schemas.tier_approval import ApprovalChainMetadata


class TierApprovalService:
    """Tier-based gate approval routing service (Sprint 161 - Foundation only)."""

    # Hardcoded approval rules (OPA integration in Sprint 162)
    DEFAULT_APPROVAL_CHAINS = {
        "FREE": {},  # Self-approval for all gates
        "STANDARD": {
            "G0.1": [],  # Self-approval (discovery)
            "G0.2": [],  # Self-approval (discovery)
            "G1": ["PM"],
            "G2": ["CTO"],
            "G3": ["CTO"],
            "G4": ["QA_LEAD"],
            "G5": ["CTO"],
            "G6": ["CEO"],
        },
        "PROFESSIONAL": {
            "G0.1": [],  # Self-approval
            "G0.2": [],  # Self-approval
            "G1": ["PM", "CTO"],
            "G2": ["CTO"],
            "G3": ["CTO", "CEO"],
            "G4": ["QA_LEAD"],
            "G5": ["CTO", "CEO"],
            "G6": ["CEO"],
        },
        "ENTERPRISE": {
            "G0.1": [],  # Self-approval
            "G0.2": [],  # Self-approval
            "G1": ["PM", "CTO"],
            "G2": ["CTO"],
            "G3": ["CTO", "CEO"],
            "G4": ["QA_LEAD", "COMPLIANCE_OFFICER"],
            "G5": ["CTO", "CEO", "COMPLIANCE_OFFICER"],  # Council review
            "G6": ["CEO", "COMPLIANCE_OFFICER"],
        },
    }

    async def compute_required_roles(
        self,
        project_tier: str,
        gate_code: str,
        db: AsyncSession
    ) -> List[str]:
        """
        Compute required functional roles for gate approval.

        Args:
            project_tier: Project tier (FREE/STANDARD/PROFESSIONAL/ENTERPRISE)
            gate_code: Gate code (G1, G2, etc.) - NOT gate_type
            db: Database session

        Returns:
            List of required functional roles (empty = self-approval)

        Raises:
            ValueError: If unknown project tier

        Note:
            - Uses hardcoded DEFAULT_APPROVAL_CHAINS
            - OPA integration in Sprint 162

        Examples:
            >>> service = TierApprovalService()
            >>> roles = await service.compute_required_roles("STANDARD", "G1", db)
            >>> roles
            ['PM']

            >>> roles = await service.compute_required_roles("FREE", "G1", db)
            >>> roles
            []  # Self-approval

            >>> roles = await service.compute_required_roles("ENTERPRISE", "G5", db)
            >>> roles
            ['CTO', 'CEO', 'COMPLIANCE_OFFICER']  # Council review
        """
        if project_tier not in self.DEFAULT_APPROVAL_CHAINS:
            raise ValueError(f"Unknown project tier: {project_tier}")

        approval_chain = self.DEFAULT_APPROVAL_CHAINS[project_tier]

        # FREE tier = self-approval for all gates
        if project_tier == "FREE":
            return []

        # Get required roles for this gate
        required_roles = approval_chain.get(gate_code, [])

        return required_roles

    async def create_approval_request(
        self,
        gate_id: UUID,
        requester_id: UUID,
        db: AsyncSession
    ) -> ApprovalChainMetadata:
        """
        Create approval request decision records.

        Args:
            gate_id: Gate requiring approval
            requester_id: User requesting approval
            db: Database session

        Returns:
            ApprovalChainMetadata with chain_id, decision_ids, metadata

        Raises:
            ValueError: If gate or project not found

        Behavior:
            - FREE tier: Create auto-approved decision (audit trail)
            - Other tiers: Create PENDING decision records (1 per required role)
            - Council review (ENTERPRISE): Create N decisions with same chain_id

        Note:
            - Does NOT finalize gate (defer to Sprint 164)
            - Does NOT assign approvers (defer to Sprint 162)

        Examples:
            >>> # FREE tier (self-approval)
            >>> metadata = await service.create_approval_request(gate_id, user_id, db)
            >>> metadata.is_self_approval
            True
            >>> metadata.decision_ids
            [UUID('...')]  # 1 auto-approved decision

            >>> # STANDARD tier (PM approval)
            >>> metadata = await service.create_approval_request(gate_id, user_id, db)
            >>> metadata.is_self_approval
            False
            >>> metadata.required_roles
            ['PM']
            >>> metadata.decision_ids
            [UUID('...')]  # 1 PENDING decision

            >>> # ENTERPRISE tier (council review)
            >>> metadata = await service.create_approval_request(gate_id, user_id, db)
            >>> metadata.required_roles
            ['CTO', 'CEO', 'COMPLIANCE_OFFICER']
            >>> metadata.decision_ids
            [UUID('...'), UUID('...'), UUID('...')]  # 3 PENDING decisions
        """
        # Get gate and project
        gate = await db.get(Gate, gate_id)
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")

        project = await db.get(Project, gate.project_id)
        if not project:
            raise ValueError(f"Project {gate.project_id} not found")

        # Get project tier (from projects.tier column added by migration)
        project_tier = getattr(project, 'tier', 'FREE')

        # Compute required roles
        required_roles = await self.compute_required_roles(
            project_tier=project_tier,
            gate_code=gate.gate_code,
            db=db
        )

        # Generate chain_id
        chain_id = uuid4()

        # Calculate expiration (48h default) - CTO v2.5 adjustment #2
        expires_at = datetime.utcnow() + timedelta(hours=48)

        decision_ids = []

        # Case 1: Self-approval (FREE tier or discovery gates)
        if not required_roles:
            # Create auto-approved decision (audit trail)
            decision = GateDecision(
                gate_id=gate_id,
                project_id=project.id,
                action="APPROVE",
                actor_id=requester_id,
                chain_id=chain_id,
                step_index=0,
                required_roles=[],
                status="COMPLETED",
                comments="Auto-approved (self-approval allowed)",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                expires_at=None,  # No expiration for completed
            )
            db.add(decision)
            await db.commit()
            await db.refresh(decision)
            decision_ids.append(decision.id)

            # CTO v2.5 adjustment #3: Return ApprovalChainMetadata
            return ApprovalChainMetadata(
                chain_id=chain_id,
                decision_ids=decision_ids,
                required_roles=[],
                expires_at=None,
                is_self_approval=True,
            )

        # Case 2: Approval required (STANDARD/PROFESSIONAL/ENTERPRISE)
        # Create N decision records (1 per required role)
        for step_index, role in enumerate(required_roles):
            decision = GateDecision(
                gate_id=gate_id,
                project_id=project.id,
                action="REQUEST",
                actor_id=requester_id,
                chain_id=chain_id,
                step_index=step_index,
                required_roles=[role],  # Each decision has 1 role
                status="PENDING",
                created_at=datetime.utcnow(),
                expires_at=expires_at,
            )
            db.add(decision)
            decision_ids.append(decision.id)

        await db.commit()

        # Refresh to get IDs
        for decision in db.new:
            if isinstance(decision, GateDecision):
                await db.refresh(decision)

        # CTO v2.5 adjustment #3: Return ApprovalChainMetadata
        return ApprovalChainMetadata(
            chain_id=chain_id,
            decision_ids=decision_ids,
            required_roles=required_roles,
            expires_at=expires_at,
            is_self_approval=False,
        )

    async def record_decision(
        self,
        decision_id: UUID,
        actor_id: UUID,
        action: str,  # 'APPROVE' or 'REJECT'
        comments: Optional[str],
        evidence_ids: Optional[List[UUID]],
        db: AsyncSession
    ) -> GateDecision:
        """
        Record approval or rejection decision.

        Args:
            decision_id: Decision record ID
            actor_id: User making the decision
            action: 'APPROVE' or 'REJECT'
            comments: Decision comments
            evidence_ids: List of evidence IDs
            db: Database session

        Returns:
            Updated GateDecision

        Raises:
            ValueError: If decision not found or not pending

        Note:
            - Does NOT finalize gate status (defer to Sprint 164)
            - Only updates decision record

        Examples:
            >>> # Approve decision
            >>> decision = await service.record_decision(
            ...     decision_id=decision_id,
            ...     actor_id=cto_id,
            ...     action='APPROVE',
            ...     comments='LGTM - code quality excellent',
            ...     evidence_ids=[ev1_id, ev2_id],
            ...     db=db
            ... )
            >>> decision.status
            'COMPLETED'
            >>> decision.action
            'APPROVE'

            >>> # Reject decision
            >>> decision = await service.record_decision(
            ...     decision_id=decision_id,
            ...     actor_id=cto_id,
            ...     action='REJECT',
            ...     comments='Missing security tests',
            ...     evidence_ids=None,
            ...     db=db
            ... )
            >>> decision.status
            'COMPLETED'
            >>> decision.action
            'REJECT'
        """
        # Get decision
        decision = await db.get(GateDecision, decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        if decision.status != "PENDING":
            raise ValueError(
                f"Decision {decision_id} is not pending (status: {decision.status})"
            )

        # Update decision
        decision.action = action
        decision.actor_id = actor_id
        decision.status = "COMPLETED"
        decision.completed_at = datetime.utcnow()
        decision.comments = comments
        decision.evidence_ids = evidence_ids or []

        await db.commit()
        await db.refresh(decision)

        # NOTE: Gate finalization deferred to Sprint 164
        # Sprint 161 only records decision, does not update gate.status

        return decision
