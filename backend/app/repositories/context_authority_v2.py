"""
Repository classes for Context Authority V2 (SPEC-0011)

Sprint 120: Context Authority V2 + Gates Engine Core
Date: January 29, 2026
Status: ACTIVE

Repositories:
1. ContextOverlayTemplateRepository - Manage overlay templates
2. ContextSnapshotRepository - Manage context snapshots
3. ContextOverlayApplicationRepository - Track template applications

References:
- SPEC-0011: Context Authority V2 - Gate-Aware Dynamic Context
- ADR-041: Framework 6.0 Governance System Design
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.context_authority_v2 import (
    ContextOverlayTemplate,
    ContextSnapshot,
    ContextOverlayApplication,
)

logger = logging.getLogger(__name__)


class ContextOverlayTemplateRepository:
    """
    Repository for ContextOverlayTemplate CRUD operations.

    Provides:
    - Template lookup by trigger type and value
    - Tier-aware template filtering
    - Priority-based ordering
    - Caching support for performance
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def get_by_id(self, template_id: UUID) -> Optional[ContextOverlayTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template UUID

        Returns:
            ContextOverlayTemplate or None
        """
        result = await self.db.execute(
            select(ContextOverlayTemplate).where(
                ContextOverlayTemplate.id == template_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_trigger(
        self,
        trigger_type: str,
        trigger_value: str,
        tier: Optional[str] = None,
        active_only: bool = True,
    ) -> List[ContextOverlayTemplate]:
        """
        Get templates matching trigger conditions.

        Retrieves templates that match:
        1. Exact trigger_type and trigger_value
        2. tier=NULL (applies to all) OR tier matches project tier

        Args:
            trigger_type: Type of trigger (gate_pass, gate_fail, index_zone, stage_constraint)
            trigger_value: Value of trigger (G0.2, orange, stage_02_code_block)
            tier: Project tier for filtering (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
            active_only: Only return active templates

        Returns:
            List of matching templates ordered by priority DESC
        """
        conditions = [
            ContextOverlayTemplate.trigger_type == trigger_type,
            ContextOverlayTemplate.trigger_value == trigger_value,
        ]

        if active_only:
            conditions.append(ContextOverlayTemplate.is_active == True)

        # Tier filtering: NULL applies to all, or exact match
        if tier:
            conditions.append(
                (ContextOverlayTemplate.tier == None) |
                (ContextOverlayTemplate.tier == tier)
            )
        else:
            # If no tier specified, only get universal templates
            conditions.append(ContextOverlayTemplate.tier == None)

        query = (
            select(ContextOverlayTemplate)
            .where(and_(*conditions))
            .order_by(desc(ContextOverlayTemplate.priority))
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(
        self,
        trigger_type: Optional[str] = None,
        tier: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContextOverlayTemplate]:
        """
        List templates with optional filtering.

        Args:
            trigger_type: Filter by trigger type
            tier: Filter by tier
            active_only: Only return active templates
            limit: Maximum results
            offset: Skip N results

        Returns:
            List of templates
        """
        conditions = []

        if trigger_type:
            conditions.append(ContextOverlayTemplate.trigger_type == trigger_type)
        if tier:
            conditions.append(
                (ContextOverlayTemplate.tier == None) |
                (ContextOverlayTemplate.tier == tier)
            )
        if active_only:
            conditions.append(ContextOverlayTemplate.is_active == True)

        query = (
            select(ContextOverlayTemplate)
            .where(and_(*conditions)) if conditions else select(ContextOverlayTemplate)
        )
        query = query.order_by(
            ContextOverlayTemplate.trigger_type,
            desc(ContextOverlayTemplate.priority),
        ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        trigger_type: str,
        trigger_value: str,
        overlay_content: str,
        name: str,
        tier: Optional[str] = None,
        priority: int = 0,
        is_active: bool = True,
        description: Optional[str] = None,
        created_by_id: Optional[UUID] = None,
    ) -> ContextOverlayTemplate:
        """
        Create a new overlay template.

        Args:
            trigger_type: Type of trigger
            trigger_value: Value of trigger
            overlay_content: Template content with {variable} placeholders
            name: Human-readable name
            tier: Tier scope (NULL = all tiers)
            priority: Priority for ordering
            is_active: Whether template is active
            description: Optional description
            created_by_id: User who created this template

        Returns:
            Created ContextOverlayTemplate
        """
        template = ContextOverlayTemplate(
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            tier=tier,
            overlay_content=overlay_content,
            priority=priority,
            is_active=is_active,
            name=name,
            description=description,
            created_by_id=created_by_id,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(
            f"Created overlay template: {template.name} "
            f"(trigger={trigger_type}:{trigger_value}, tier={tier or 'ALL'})"
        )
        return template

    async def update(
        self,
        template_id: UUID,
        **kwargs: Any,
    ) -> Optional[ContextOverlayTemplate]:
        """
        Update an existing template.

        Args:
            template_id: Template UUID
            **kwargs: Fields to update

        Returns:
            Updated template or None if not found
        """
        template = await self.get_by_id(template_id)
        if not template:
            return None

        allowed_fields = {
            "trigger_type", "trigger_value", "tier", "overlay_content",
            "priority", "is_active", "name", "description",
        }

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(template)

        logger.info(f"Updated overlay template: {template.name}")
        return template

    async def delete(self, template_id: UUID) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template UUID

        Returns:
            True if deleted, False if not found
        """
        template = await self.get_by_id(template_id)
        if not template:
            return False

        await self.db.delete(template)
        await self.db.commit()

        logger.info(f"Deleted overlay template: {template.name}")
        return True

    async def count(
        self,
        trigger_type: Optional[str] = None,
        tier: Optional[str] = None,
        active_only: bool = True,
    ) -> int:
        """Count templates matching criteria."""
        conditions = []
        if trigger_type:
            conditions.append(ContextOverlayTemplate.trigger_type == trigger_type)
        if tier:
            conditions.append(
                (ContextOverlayTemplate.tier == None) |
                (ContextOverlayTemplate.tier == tier)
            )
        if active_only:
            conditions.append(ContextOverlayTemplate.is_active == True)

        query = select(func.count(ContextOverlayTemplate.id))
        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return result.scalar() or 0


class ContextSnapshotRepository:
    """
    Repository for ContextSnapshot CRUD operations.

    Provides:
    - Snapshot creation (immutable)
    - Query by submission/project
    - Time-series analysis support
    - Audit trail retrieval
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def get_by_id(self, snapshot_id: UUID) -> Optional[ContextSnapshot]:
        """
        Get snapshot by ID.

        Args:
            snapshot_id: Snapshot UUID

        Returns:
            ContextSnapshot or None
        """
        result = await self.db.execute(
            select(ContextSnapshot)
            .options(selectinload(ContextSnapshot.overlay_applications))
            .where(ContextSnapshot.id == snapshot_id)
        )
        return result.scalar_one_or_none()

    async def get_by_submission(
        self,
        submission_id: UUID,
    ) -> Optional[ContextSnapshot]:
        """
        Get snapshot for a governance submission.

        Args:
            submission_id: Governance submission UUID

        Returns:
            Most recent snapshot for submission
        """
        result = await self.db.execute(
            select(ContextSnapshot)
            .where(ContextSnapshot.submission_id == submission_id)
            .order_by(desc(ContextSnapshot.snapshot_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
        valid_only: Optional[bool] = None,
        zone: Optional[str] = None,
    ) -> List[ContextSnapshot]:
        """
        List snapshots for a project.

        Args:
            project_id: Project UUID
            limit: Maximum results
            offset: Skip N results
            valid_only: Filter by validation result
            zone: Filter by vibecoding zone

        Returns:
            List of snapshots ordered by snapshot_at DESC
        """
        conditions = [ContextSnapshot.project_id == project_id]

        if valid_only is not None:
            conditions.append(ContextSnapshot.is_valid == valid_only)
        if zone:
            conditions.append(ContextSnapshot.vibecoding_zone == zone)

        query = (
            select(ContextSnapshot)
            .where(and_(*conditions))
            .order_by(desc(ContextSnapshot.snapshot_at))
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        submission_id: UUID,
        project_id: UUID,
        gate_status: Dict[str, Any],
        vibecoding_index: int,
        vibecoding_zone: str,
        dynamic_overlay: str,
        tier: str,
        is_valid: bool,
        v1_result: Optional[Dict[str, Any]] = None,
        gate_violations: Optional[List[Dict[str, Any]]] = None,
        index_warnings: Optional[List[Dict[str, Any]]] = None,
        applied_template_ids: Optional[List[str]] = None,
    ) -> ContextSnapshot:
        """
        Create a new context snapshot.

        Snapshots are immutable - created once and never modified.

        Args:
            submission_id: Governance submission UUID
            project_id: Project UUID
            gate_status: Gate status at validation time
            vibecoding_index: Vibecoding index (0-100)
            vibecoding_zone: Zone (GREEN, YELLOW, ORANGE, RED)
            dynamic_overlay: Generated overlay content
            tier: Project tier at validation time
            is_valid: Overall validation result
            v1_result: Context Authority V1 result
            gate_violations: Gate constraint violations
            index_warnings: Vibecoding index warnings
            applied_template_ids: Template IDs used

        Returns:
            Created ContextSnapshot
        """
        snapshot = ContextSnapshot(
            submission_id=submission_id,
            project_id=project_id,
            gate_status=gate_status,
            vibecoding_index=vibecoding_index,
            vibecoding_zone=vibecoding_zone,
            dynamic_overlay=dynamic_overlay,
            tier=tier,
            is_valid=is_valid,
            v1_result=v1_result,
            gate_violations=gate_violations,
            index_warnings=index_warnings,
            applied_template_ids=applied_template_ids,
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)

        logger.info(
            f"Created context snapshot: submission={submission_id}, "
            f"index={vibecoding_index}, zone={vibecoding_zone}, valid={is_valid}"
        )
        return snapshot

    async def count_by_project(
        self,
        project_id: UUID,
        valid_only: Optional[bool] = None,
        zone: Optional[str] = None,
    ) -> int:
        """Count snapshots for a project."""
        conditions = [ContextSnapshot.project_id == project_id]
        if valid_only is not None:
            conditions.append(ContextSnapshot.is_valid == valid_only)
        if zone:
            conditions.append(ContextSnapshot.vibecoding_zone == zone)

        query = select(func.count(ContextSnapshot.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_recent(self, hours: int = 24) -> int:
        """
        Count snapshots in the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            Count of snapshots
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(func.count(ContextSnapshot.id))
            .where(ContextSnapshot.snapshot_at >= since)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_aggregate_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregate statistics for all snapshots.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with aggregated stats
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Total snapshots and validations
        total_query = (
            select(func.count(ContextSnapshot.id))
            .where(ContextSnapshot.snapshot_at >= since)
        )
        total_result = await self.db.execute(total_query)
        total_snapshots = total_result.scalar() or 0

        # Pass rate
        pass_query = (
            select(func.count(ContextSnapshot.id))
            .where(
                and_(
                    ContextSnapshot.snapshot_at >= since,
                    ContextSnapshot.is_valid == True,
                )
            )
        )
        pass_result = await self.db.execute(pass_query)
        passed = pass_result.scalar() or 0
        pass_rate = passed / total_snapshots if total_snapshots > 0 else 0.0

        # Zone distribution
        zone_query = (
            select(
                ContextSnapshot.vibecoding_zone,
                func.count(ContextSnapshot.id).label("count"),
            )
            .where(ContextSnapshot.snapshot_at >= since)
            .group_by(ContextSnapshot.vibecoding_zone)
        )
        zone_result = await self.db.execute(zone_query)
        zone_distribution = {row.vibecoding_zone: row.count for row in zone_result.all()}

        # Tier distribution
        tier_query = (
            select(
                ContextSnapshot.tier,
                func.count(ContextSnapshot.id).label("count"),
            )
            .where(ContextSnapshot.snapshot_at >= since)
            .group_by(ContextSnapshot.tier)
        )
        tier_result = await self.db.execute(tier_query)
        tier_distribution = {row.tier: row.count for row in tier_result.all()}

        return {
            "total_validations": total_snapshots,
            "total_snapshots": total_snapshots,
            "pass_rate": pass_rate,
            "zone_distribution": zone_distribution,
            "tier_distribution": tier_distribution,
            "avg_templates": 0.0,  # Would need join with applications
        }

    async def get_zone_distribution(
        self,
        project_id: UUID,
        days: int = 30,
    ) -> Dict[str, int]:
        """
        Get zone distribution for a project.

        Args:
            project_id: Project UUID
            days: Number of days to analyze

        Returns:
            Dict mapping zone to count
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ContextSnapshot.vibecoding_zone,
                func.count(ContextSnapshot.id).label("count"),
            )
            .where(
                and_(
                    ContextSnapshot.project_id == project_id,
                    ContextSnapshot.snapshot_at >= since,
                )
            )
            .group_by(ContextSnapshot.vibecoding_zone)
        )

        result = await self.db.execute(query)
        return {row.vibecoding_zone: row.count for row in result.all()}

    async def get_average_index(
        self,
        project_id: UUID,
        days: int = 7,
    ) -> Optional[float]:
        """
        Get average vibecoding index for a project.

        Args:
            project_id: Project UUID
            days: Number of days to analyze

        Returns:
            Average index or None if no data
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(func.avg(ContextSnapshot.vibecoding_index))
            .where(
                and_(
                    ContextSnapshot.project_id == project_id,
                    ContextSnapshot.snapshot_at >= since,
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalar()


class ContextOverlayApplicationRepository:
    """
    Repository for ContextOverlayApplication CRUD operations.

    Provides:
    - Track which templates were applied
    - Template usage analytics
    - Audit trail for overlay generation
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create(
        self,
        snapshot_id: UUID,
        template_id: UUID,
        template_content_snapshot: str,
        rendered_content: str,
        variables_used: Optional[Dict[str, Any]] = None,
        application_order: int = 0,
    ) -> ContextOverlayApplication:
        """
        Record a template application.

        Args:
            snapshot_id: Context snapshot UUID
            template_id: Template UUID
            template_content_snapshot: Template content at application time
            rendered_content: Content after variable substitution
            variables_used: Variables used for rendering
            application_order: Order in final overlay

        Returns:
            Created ContextOverlayApplication
        """
        application = ContextOverlayApplication(
            snapshot_id=snapshot_id,
            template_id=template_id,
            template_content_snapshot=template_content_snapshot,
            rendered_content=rendered_content,
            variables_used=variables_used,
            application_order=application_order,
        )
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def create_batch(
        self,
        applications: List[Dict[str, Any]],
    ) -> List[ContextOverlayApplication]:
        """
        Create multiple application records.

        Args:
            applications: List of application data dicts

        Returns:
            List of created applications
        """
        created = []
        for app_data in applications:
            application = ContextOverlayApplication(**app_data)
            self.db.add(application)
            created.append(application)

        await self.db.commit()
        for app in created:
            await self.db.refresh(app)

        return created

    async def get_by_snapshot(
        self,
        snapshot_id: UUID,
    ) -> List[ContextOverlayApplication]:
        """
        Get all applications for a snapshot.

        Args:
            snapshot_id: Context snapshot UUID

        Returns:
            List of applications ordered by application_order
        """
        result = await self.db.execute(
            select(ContextOverlayApplication)
            .where(ContextOverlayApplication.snapshot_id == snapshot_id)
            .order_by(ContextOverlayApplication.application_order)
        )
        return list(result.scalars().all())

    async def get_template_usage_count(
        self,
        template_id: UUID,
        days: int = 30,
    ) -> int:
        """
        Count how many times a template was used.

        Args:
            template_id: Template UUID
            days: Number of days to analyze

        Returns:
            Usage count
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(func.count(ContextOverlayApplication.id))
            .where(
                and_(
                    ContextOverlayApplication.template_id == template_id,
                    ContextOverlayApplication.applied_at >= since,
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_most_used_templates(
        self,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get most frequently used templates.

        Args:
            days: Number of days to analyze
            limit: Maximum results

        Returns:
            List of dicts with template_id and usage_count
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ContextOverlayApplication.template_id,
                func.count(ContextOverlayApplication.id).label("usage_count"),
            )
            .where(ContextOverlayApplication.applied_at >= since)
            .group_by(ContextOverlayApplication.template_id)
            .order_by(desc("usage_count"))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return [
            {"template_id": str(row.template_id), "usage_count": row.usage_count}
            for row in result.all()
        ]

    async def get_recent_applications(
        self,
        template_id: UUID,
        limit: int = 10,
    ) -> List[ContextOverlayApplication]:
        """
        Get recent applications for a template.

        Args:
            template_id: Template UUID
            limit: Maximum results

        Returns:
            List of recent applications ordered by applied_at DESC
        """
        query = (
            select(ContextOverlayApplication)
            .where(ContextOverlayApplication.template_id == template_id)
            .order_by(desc(ContextOverlayApplication.applied_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_top_templates(
        self,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top templates by usage with template details.

        Args:
            days: Number of days to analyze
            limit: Maximum results

        Returns:
            List of dicts with template details and usage count
        """
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                ContextOverlayApplication.template_id,
                func.count(ContextOverlayApplication.id).label("usage_count"),
            )
            .where(ContextOverlayApplication.applied_at >= since)
            .group_by(ContextOverlayApplication.template_id)
            .order_by(desc("usage_count"))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return [
            {
                "template_id": str(row.template_id),
                "usage_count": row.usage_count,
            }
            for row in result.all()
        ]
