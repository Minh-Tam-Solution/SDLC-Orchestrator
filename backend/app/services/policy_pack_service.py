"""
Policy Pack Service - CRUD Operations

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1 (10-Stage Lifecycle, 4-Tier Classification)
Epic: EP-02 AI Safety Layer v1

Purpose:
- CRUD operations for PolicyPack and PolicyRule
- Default policy pack creation
- Policy evaluation coordination
- Permission checks for policy management

Architecture:
- Repository pattern for database operations
- Service layer for business logic
- Async operations for performance

Reference:
- docs/02-design/14-Technical-Specs/Policy-Guards-Design.md
- docs/04-build/05-SASE-Artifacts/BRS-2026-003-POLICY-GUARDS.yaml

Version: 1.0.0
Updated: December 2025
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.policy_pack import PolicyEvaluationHistory, PolicyPack, PolicyRule
from app.schemas.policy_pack import (
    PolicyPackCreate,
    PolicyPackUpdate,
    PolicyPackWithRules,
    PolicyRuleCreate,
    PolicyRuleUpdate,
    PolicyTier,
    get_default_policies,
)

logger = logging.getLogger(__name__)


class PolicyPackService:
    """
    Service for managing Policy Packs and Rules.

    Features:
    - CRUD operations for policy packs
    - Default policy pack creation with AI safety policies
    - Permission checks for policy management
    - Policy evaluation coordination

    Usage:
        service = PolicyPackService(db_session)
        pack = await service.get_by_project(project_id)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    # =========================================================================
    # Policy Pack CRUD
    # =========================================================================

    async def get_by_project(self, project_id: UUID) -> Optional[PolicyPack]:
        """
        Get policy pack for a project.

        Args:
            project_id: Project UUID

        Returns:
            PolicyPack if exists, None otherwise
        """
        stmt = (
            select(PolicyPack)
            .options(selectinload(PolicyPack.rules))
            .where(PolicyPack.project_id == project_id)
            .where(PolicyPack.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, pack_id: UUID) -> Optional[PolicyPack]:
        """
        Get policy pack by ID.

        Args:
            pack_id: PolicyPack UUID

        Returns:
            PolicyPack if exists, None otherwise
        """
        stmt = (
            select(PolicyPack)
            .options(selectinload(PolicyPack.rules))
            .where(PolicyPack.id == pack_id)
            .where(PolicyPack.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        project_id: UUID,
        data: PolicyPackCreate,
        created_by: Optional[UUID] = None,
    ) -> PolicyPack:
        """
        Create a new policy pack for a project.

        Args:
            project_id: Project UUID
            data: Policy pack creation data
            created_by: Creator user ID

        Returns:
            Created PolicyPack

        Raises:
            ValueError: If project already has a policy pack
        """
        # Check if project already has a pack
        existing = await self.get_by_project(project_id)
        if existing:
            raise ValueError(f"Project {project_id} already has a policy pack")

        # Create policy pack
        pack = PolicyPack(
            project_id=project_id,
            name=data.name,
            description=data.description,
            version=data.version,
            tier=data.tier.value if isinstance(data.tier, PolicyTier) else data.tier,
            validators=[v.model_dump() for v in data.validators],
            coverage_threshold=data.coverage_threshold,
            coverage_blocking=data.coverage_blocking,
            forbidden_imports=data.forbidden_imports,
            required_patterns=data.required_patterns,
            created_by=created_by,
        )
        self.db.add(pack)
        await self.db.flush()

        # Create policy rules
        for policy_data in data.policies:
            rule = PolicyRule(
                policy_pack_id=pack.id,
                policy_id=policy_data.policy_id,
                name=policy_data.name,
                description=policy_data.description,
                rego_policy=policy_data.rego_policy,
                severity=policy_data.severity.value,
                blocking=policy_data.blocking,
                enabled=policy_data.enabled,
                message_template=policy_data.message_template,
                tags=policy_data.tags,
            )
            self.db.add(rule)

        await self.db.commit()
        await self.db.refresh(pack)

        logger.info(f"Created policy pack for project {project_id}: {pack.name}")
        return pack

    async def create_or_update(
        self,
        project_id: UUID,
        data: PolicyPackCreate,
        user_id: Optional[UUID] = None,
    ) -> PolicyPack:
        """
        Create or update policy pack for a project.

        Args:
            project_id: Project UUID
            data: Policy pack data
            user_id: User making the change

        Returns:
            Created or updated PolicyPack
        """
        existing = await self.get_by_project(project_id)

        if existing:
            # Update existing
            return await self.update(existing.id, PolicyPackUpdate(
                name=data.name,
                description=data.description,
                version=data.version,
                tier=data.tier,
                validators=data.validators,
                coverage_threshold=data.coverage_threshold,
                coverage_blocking=data.coverage_blocking,
                forbidden_imports=data.forbidden_imports,
                required_patterns=data.required_patterns,
            ))
        else:
            # Create new
            return await self.create(project_id, data, user_id)

    async def update(
        self,
        pack_id: UUID,
        data: PolicyPackUpdate,
    ) -> Optional[PolicyPack]:
        """
        Update a policy pack.

        Args:
            pack_id: PolicyPack UUID
            data: Update data

        Returns:
            Updated PolicyPack if exists, None otherwise
        """
        pack = await self.get_by_id(pack_id)
        if not pack:
            return None

        # Update fields if provided
        if data.name is not None:
            pack.name = data.name
        if data.description is not None:
            pack.description = data.description
        if data.version is not None:
            pack.version = data.version
        if data.tier is not None:
            pack.tier = data.tier.value if isinstance(data.tier, PolicyTier) else data.tier
        if data.validators is not None:
            pack.validators = [v.model_dump() for v in data.validators]
        if data.coverage_threshold is not None:
            pack.coverage_threshold = data.coverage_threshold
        if data.coverage_blocking is not None:
            pack.coverage_blocking = data.coverage_blocking
        if data.forbidden_imports is not None:
            pack.forbidden_imports = data.forbidden_imports
        if data.required_patterns is not None:
            pack.required_patterns = data.required_patterns

        await self.db.commit()
        await self.db.refresh(pack)

        logger.info(f"Updated policy pack: {pack_id}")
        return pack

    async def delete(self, pack_id: UUID) -> bool:
        """
        Soft delete a policy pack.

        Args:
            pack_id: PolicyPack UUID

        Returns:
            True if deleted, False if not found
        """
        pack = await self.get_by_id(pack_id)
        if not pack:
            return False

        from datetime import datetime
        pack.deleted_at = datetime.utcnow()
        await self.db.commit()

        logger.info(f"Deleted policy pack: {pack_id}")
        return True

    # =========================================================================
    # Policy Rule Operations
    # =========================================================================

    async def add_rule(
        self,
        project_id: UUID,
        rule_data: PolicyRuleCreate,
    ) -> Optional[PolicyRule]:
        """
        Add a policy rule to a project's pack.

        Args:
            project_id: Project UUID
            rule_data: Policy rule data

        Returns:
            Created PolicyRule, None if pack doesn't exist
        """
        pack = await self.get_by_project(project_id)
        if not pack:
            return None

        # Check for duplicate policy_id
        for existing_rule in pack.rules:
            if existing_rule.policy_id == rule_data.policy_id:
                raise ValueError(f"Policy {rule_data.policy_id} already exists in pack")

        rule = PolicyRule(
            policy_pack_id=pack.id,
            policy_id=rule_data.policy_id,
            name=rule_data.name,
            description=rule_data.description,
            rego_policy=rule_data.rego_policy,
            severity=rule_data.severity.value,
            blocking=rule_data.blocking,
            enabled=rule_data.enabled,
            message_template=rule_data.message_template,
            tags=rule_data.tags,
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"Added policy rule {rule_data.policy_id} to project {project_id}")
        return rule

    async def update_rule(
        self,
        pack_id: UUID,
        policy_id: str,
        data: PolicyRuleUpdate,
    ) -> Optional[PolicyRule]:
        """
        Update a policy rule.

        Args:
            pack_id: PolicyPack UUID
            policy_id: Policy identifier (e.g., "no-hardcoded-secrets")
            data: Update data

        Returns:
            Updated PolicyRule, None if not found
        """
        pack = await self.get_by_id(pack_id)
        if not pack:
            return None

        rule = None
        for r in pack.rules:
            if r.policy_id == policy_id:
                rule = r
                break

        if not rule:
            return None

        # Update fields if provided
        if data.name is not None:
            rule.name = data.name
        if data.description is not None:
            rule.description = data.description
        if data.rego_policy is not None:
            rule.rego_policy = data.rego_policy
        if data.severity is not None:
            rule.severity = data.severity.value
        if data.blocking is not None:
            rule.blocking = data.blocking
        if data.enabled is not None:
            rule.enabled = data.enabled
        if data.message_template is not None:
            rule.message_template = data.message_template
        if data.tags is not None:
            rule.tags = data.tags

        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"Updated policy rule: {policy_id}")
        return rule

    async def delete_rule(
        self,
        project_id: UUID,
        policy_id: str,
    ) -> bool:
        """
        Delete a policy rule.

        Args:
            project_id: Project UUID
            policy_id: Policy identifier

        Returns:
            True if deleted, False if not found
        """
        pack = await self.get_by_project(project_id)
        if not pack:
            return False

        for rule in pack.rules:
            if rule.policy_id == policy_id:
                await self.db.delete(rule)
                await self.db.commit()
                logger.info(f"Deleted policy rule: {policy_id}")
                return True

        return False

    # =========================================================================
    # Default Pack Creation
    # =========================================================================

    async def create_default_pack(
        self,
        project_id: UUID,
        tier: PolicyTier = PolicyTier.STANDARD,
        created_by: Optional[UUID] = None,
    ) -> PolicyPack:
        """
        Create default policy pack with AI safety policies.

        Args:
            project_id: Project UUID
            tier: SDLC tier (affects default policies)
            created_by: Creator user ID

        Returns:
            Created PolicyPack with default policies
        """
        # Get default policies
        default_policies = get_default_policies()

        # Create pack data
        pack_data = PolicyPackCreate(
            name=f"AI Safety Pack ({tier.value})",
            description=(
                "Default AI safety policy pack with security and architecture rules. "
                "Policies detect hardcoded secrets, enforce architecture boundaries, "
                "and prevent forbidden imports (AGPL)."
            ),
            version="1.0.0",
            tier=tier,
            validators=[
                {"name": "lint", "enabled": True, "blocking": True, "config": {}},
                {"name": "test", "enabled": True, "blocking": True, "config": {}},
                {"name": "coverage", "enabled": True, "blocking": False, "config": {}},
                {"name": "policy_guards", "enabled": True, "blocking": True, "config": {}},
            ],
            coverage_threshold=self._get_coverage_threshold(tier),
            coverage_blocking=tier in (PolicyTier.PROFESSIONAL, PolicyTier.ENTERPRISE),
            forbidden_imports=["minio", "grafana_sdk", "grafana_client"],
            required_patterns=[],
            policies=default_policies,
        )

        return await self.create(project_id, pack_data, created_by)

    def _get_coverage_threshold(self, tier: PolicyTier) -> int:
        """Get default coverage threshold by tier."""
        thresholds = {
            PolicyTier.LITE: 50,
            PolicyTier.STANDARD: 80,
            PolicyTier.PROFESSIONAL: 90,
            PolicyTier.ENTERPRISE: 95,
        }
        return thresholds.get(tier, 80)

    # =========================================================================
    # Permission Checks
    # =========================================================================

    async def can_manage_policies(
        self,
        user: Any,
        project_id: UUID,
    ) -> bool:
        """
        Check if user can manage policies for a project.

        Args:
            user: User model instance
            project_id: Project UUID

        Returns:
            True if user can manage policies
        """
        # Project admins and owners can manage policies
        # This should be replaced with actual permission check
        if hasattr(user, "is_admin") and user.is_admin:
            return True

        # TODO: Check project membership and role
        return True

    # =========================================================================
    # Policy Evaluation
    # =========================================================================

    async def evaluate(
        self,
        project_id: UUID,
        files: List[Dict[str, Any]],
        diff: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluate policies against files.

        Args:
            project_id: Project UUID
            files: List of files with path and content
            diff: Unified diff

        Returns:
            Evaluation results
        """
        from app.services.opa_policy_service import get_opa_policy_service

        pack = await self.get_by_project(project_id)
        if not pack:
            return {
                "status": "skipped",
                "message": "No policy pack configured",
                "results": [],
            }

        # Convert rules to PolicyRuleCreate format for OPA service
        policies = []
        for rule in pack.rules:
            if rule.enabled:
                policies.append(PolicyRuleCreate(
                    policy_id=rule.policy_id,
                    name=rule.name,
                    description=rule.description,
                    rego_policy=rule.rego_policy,
                    severity=rule.severity,
                    blocking=rule.blocking,
                    enabled=rule.enabled,
                    message_template=rule.message_template,
                    tags=rule.tags,
                ))

        if not policies:
            return {
                "status": "skipped",
                "message": "No enabled policies",
                "results": [],
            }

        # Prepare input
        input_data = {
            "files": files,
            "diff": diff,
            "config": {
                "forbidden_imports": pack.forbidden_imports,
                "required_patterns": pack.required_patterns,
                "coverage_threshold": pack.coverage_threshold,
            },
        }

        # Evaluate via OPA
        opa = get_opa_policy_service()
        results = await opa.evaluate_policies(policies, input_data)

        # Aggregate
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        blocking = [r for r in failed if r.blocking]

        return {
            "status": "failed" if blocking else "passed",
            "total": len(results),
            "passed": len(passed),
            "failed": len(failed),
            "blocked": len(blocking) > 0,
            "results": [r.model_dump() for r in results],
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_policy_pack_service: Optional[PolicyPackService] = None


def get_policy_pack_service(db: Optional[AsyncSession] = None) -> PolicyPackService:
    """
    Get PolicyPackService instance.

    Note: In production, this should be injected via FastAPI Depends.
    """
    global _policy_pack_service
    if db is not None:
        return PolicyPackService(db)
    if _policy_pack_service is None:
        raise RuntimeError("PolicyPackService not initialized. Provide db session.")
    return _policy_pack_service
