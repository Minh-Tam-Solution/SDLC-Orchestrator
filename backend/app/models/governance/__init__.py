"""
=========================================================================
Governance Models Package - Anti-Vibecoding Governance System
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- 14-table database schema for governance validation
- Vibecoding Index storage and tracking
- Evidence vault metadata
- Audit logging (7-year retention)
- CEO escalation workflow

Tables:
1. governance_submissions - Central submission tracking
2. governance_rejections - Rejection reasons and feedback
3. evidence_vault_entries - Evidence metadata (MinIO S3)
4. governance_audit_log - Immutable audit trail
5. ownership_registry - File ownership annotations
6. quality_contracts - Policy-as-code rules
7. context_authorities - Context validation results
8. context_snapshots - Historical context state
9. contract_versions - Policy versioning
10. contract_violations - Policy violation details
11. ai_attestations - AI-generated code attestations
12. human_reviews - Human review tracking
13. governance_exceptions - Break glass / exceptions
14. escalation_log - CEO escalation tracking

Zero Mock Policy: Real SQLAlchemy models with all fields
=========================================================================
"""

from app.models.governance.submission import GovernanceSubmission
from app.models.governance.rejection import GovernanceRejection
from app.models.governance.evidence import EvidenceVaultEntry
from app.models.governance.audit import GovernanceAuditLog
from app.models.governance.ownership import OwnershipRegistry
from app.models.governance.contract import QualityContract
from app.models.governance.context import ContextAuthority, GovernanceContextSnapshot
from app.models.governance.contract_version import ContractVersion
from app.models.governance.violation import ContractViolation
from app.models.governance.attestation import AIAttestation
from app.models.governance.review import HumanReview
from app.models.governance.exception import GovernanceException
from app.models.governance.escalation import EscalationLog

__all__ = [
    "GovernanceSubmission",
    "GovernanceRejection",
    "EvidenceVaultEntry",
    "GovernanceAuditLog",
    "OwnershipRegistry",
    "QualityContract",
    "ContextAuthority",
    "GovernanceContextSnapshot",
    "ContractVersion",
    "ContractViolation",
    "AIAttestation",
    "HumanReview",
    "GovernanceException",
    "EscalationLog",
]
