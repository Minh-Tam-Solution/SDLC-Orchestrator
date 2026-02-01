"""
Compliance Scorer Service - Sprint 123 (SPEC-0013)

SDLC 6.0.0 Compliance Scoring Engine.
10 categories × 10 points = 100 maximum score.

Categories:
1. documentation_structure: Stage folders (00-10), no duplicates
2. specifications_management: YAML frontmatter, SPEC-XXXX numbering
3. claude_agents_md: Version headers, required sections
4. sase_artifacts: CRP, MRP, VCR templates present
5. code_file_naming: snake_case (Python), camelCase/PascalCase (TS)
6. migration_tracking: Progress percentage, deadline compliance
7. framework_alignment: 7-Pillar + Section 7 compliance
8. team_organization: SDLC Compliance Hub, roles defined
9. legacy_archival: Proper 99-legacy/ or 10-Archive/ usage
10. governance_documentation: CEO/CTO approvals, ADRs
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_validation import (
    ComplianceCategory,
    ComplianceIssue as ComplianceIssueModel,
    ComplianceScore as ComplianceScoreModel,
    IssueSeverity,
)
from app.schemas.compliance import (
    CategoryResultResponse,
    ComplianceIssueBase,
    ComplianceScoreResponse,
    IssuesSummary,
    QuickScoreResponse,
)
from app.services.validation.checkers import CATEGORY_CHECKERS
from app.services.validation.checkers.base import CategoryCheckResult


class ComplianceScorerService:
    """
    SDLC 6.0.0 Compliance Scoring Engine.

    Calculates compliance score based on 10 categories, each worth 10 points.
    Total possible score: 100 points.

    Usage:
        scorer = ComplianceScorerService(db, file_service)
        result = await scorer.calculate_score(project_id)
        # result.overall_score = 87
        # result.categories = [CategoryResultResponse, ...]
    """

    CACHE_TTL_HOURS = 1
    VALIDATION_VERSION = "1.0.0"
    FRAMEWORK_VERSION = "6.0.0"

    def __init__(self, db: AsyncSession, file_service):
        """
        Initialize scorer with database session and file service.

        Args:
            db: Async database session
            file_service: Service for file operations
        """
        self.db = db
        self.file_service = file_service

    async def calculate_score(
        self,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        include_categories: Optional[list[ComplianceCategory]] = None,
        exclude_categories: Optional[list[ComplianceCategory]] = None,
        force_refresh: bool = False,
    ) -> ComplianceScoreResponse:
        """
        Calculate compliance score for project.

        Args:
            project_id: Project UUID
            user_id: User who triggered the calculation
            include_categories: Only check these categories (optional)
            exclude_categories: Skip these categories (optional)
            force_refresh: Bypass cache and recalculate

        Returns:
            ComplianceScoreResponse with overall score and category breakdown
        """
        start_time = time.time()

        # Check cache first
        if not force_refresh:
            cached = await self._get_cached_score(project_id)
            if cached:
                return cached

        # Determine categories to check
        categories_to_check = self._get_categories(include_categories, exclude_categories)

        # Run all category checkers concurrently
        check_tasks = []
        for category in categories_to_check:
            checker_class = CATEGORY_CHECKERS.get(category)
            if checker_class:
                checker = checker_class(self.db, self.file_service)
                check_tasks.append(checker.check(project_id))

        results: list[CategoryCheckResult] = await asyncio.gather(*check_tasks)

        # Calculate totals
        total_score = sum(r.score for r in results)
        all_issues = []
        category_responses = []

        for result in results:
            # Convert to response schema
            issues_base = [
                ComplianceIssueBase(
                    category=issue.category,
                    severity=issue.severity,
                    issue_code=issue.issue_code,
                    message=issue.message,
                    file_path=issue.file_path,
                    line_number=issue.line_number,
                    fix_suggestion=issue.fix_suggestion,
                    fix_command=issue.fix_command,
                    auto_fixable=issue.auto_fixable,
                )
                for issue in result.issues
            ]

            category_responses.append(CategoryResultResponse(
                name=result.category,
                score=result.score,
                max_score=result.max_score,
                issues=issues_base,
                passed_checks=result.passed_checks,
            ))

            all_issues.extend(result.issues)

        # Calculate summary
        summary = IssuesSummary(
            total=len(all_issues),
            critical=sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL),
            warning=sum(1 for i in all_issues if i.severity == IssueSeverity.WARNING),
            info=sum(1 for i in all_issues if i.severity == IssueSeverity.INFO),
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(category_responses, summary)

        # Calculate scan duration
        scan_duration_ms = int((time.time() - start_time) * 1000)

        # Build response
        response = ComplianceScoreResponse(
            project_id=project_id,
            overall_score=total_score,
            categories=category_responses,
            summary=summary,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
            framework_version=self.FRAMEWORK_VERSION,
            validation_version=self.VALIDATION_VERSION,
            scan_duration_ms=scan_duration_ms,
            is_cached=False,
        )

        # Save to database and cache
        await self._save_score(project_id, user_id, response, all_issues)

        return response

    async def get_quick_score(self, project_id: UUID) -> Optional[QuickScoreResponse]:
        """
        Get cached score only (fast lookup for dashboards).

        Args:
            project_id: Project UUID

        Returns:
            QuickScoreResponse if cached, None otherwise
        """
        stmt = (
            select(ComplianceScoreModel)
            .where(ComplianceScoreModel.project_id == project_id)
            .order_by(ComplianceScoreModel.calculated_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        score = result.scalar_one_or_none()

        if not score:
            return None

        return QuickScoreResponse(
            project_id=project_id,
            score=score.overall_score,
            last_calculated=score.calculated_at,
            is_cached=True,
            framework_version=score.framework_version,
        )

    def _get_categories(
        self,
        include: Optional[list[ComplianceCategory]],
        exclude: Optional[list[ComplianceCategory]],
    ) -> list[ComplianceCategory]:
        """Determine which categories to check."""
        all_categories = list(ComplianceCategory)

        if include:
            return [c for c in include if c in all_categories]

        if exclude:
            return [c for c in all_categories if c not in exclude]

        return all_categories

    def _generate_recommendations(
        self,
        results: list[CategoryResultResponse],
        summary: IssuesSummary,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Critical issues first
        if summary.critical > 0:
            recommendations.append(
                f"Fix {summary.critical} critical issue(s) immediately to avoid gate failures"
            )

        # Low-scoring categories
        for result in sorted(results, key=lambda r: r.score):
            if result.score < 7:
                potential_gain = result.max_score - result.score
                category_name = result.name.value.replace("_", " ").title()
                recommendations.append(
                    f"Improve '{category_name}' (+{potential_gain} points possible)"
                )

        # Warnings
        if summary.warning > 0:
            recommendations.append(
                f"Address {summary.warning} warning(s) to reach 90+ score"
            )

        # Positive reinforcement
        if summary.total == 0:
            recommendations.append(
                "Excellent! No compliance issues found."
            )

        return recommendations[:5]  # Top 5 recommendations

    async def _get_cached_score(
        self, project_id: UUID
    ) -> Optional[ComplianceScoreResponse]:
        """Get cached score if not expired."""
        stmt = (
            select(ComplianceScoreModel)
            .where(ComplianceScoreModel.project_id == project_id)
            .where(ComplianceScoreModel.expires_at > datetime.utcnow())
            .order_by(ComplianceScoreModel.calculated_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        cached = result.scalar_one_or_none()

        if not cached:
            return None

        # Reconstruct response from cached data
        # Note: We don't cache full issues, so return summary only
        return ComplianceScoreResponse(
            project_id=project_id,
            overall_score=cached.overall_score,
            categories=[],  # Not cached in detail
            summary=IssuesSummary(**cached.issues_summary),
            recommendations=cached.recommendations or [],
            generated_at=cached.calculated_at,
            framework_version=cached.framework_version,
            validation_version=cached.validation_version,
            scan_duration_ms=cached.scan_duration_ms,
            is_cached=True,
        )

    async def _save_score(
        self,
        project_id: UUID,
        user_id: Optional[UUID],
        response: ComplianceScoreResponse,
        issues: list,
    ) -> None:
        """Save score to database with TTL."""
        expires_at = datetime.utcnow() + timedelta(hours=self.CACHE_TTL_HOURS)

        # Create score record
        score_model = ComplianceScoreModel(
            project_id=project_id,
            overall_score=response.overall_score,
            category_scores={
                cat.name.value: cat.score
                for cat in response.categories
            },
            issues_summary={
                "total": response.summary.total,
                "critical": response.summary.critical,
                "warning": response.summary.warning,
                "info": response.summary.info,
            },
            recommendations=response.recommendations,
            calculated_at=response.generated_at,
            calculated_by_id=user_id,
            validation_version=self.VALIDATION_VERSION,
            framework_version=self.FRAMEWORK_VERSION,
            expires_at=expires_at,
            scan_duration_ms=response.scan_duration_ms,
        )

        self.db.add(score_model)
        await self.db.flush()

        # Save individual issues
        for issue in issues:
            issue_model = ComplianceIssueModel(
                score_id=score_model.id,
                category=issue.category.value,
                severity=issue.severity.value,
                issue_code=issue.issue_code,
                message=issue.message,
                file_path=issue.file_path,
                line_number=issue.line_number,
                fix_suggestion=issue.fix_suggestion,
                fix_command=issue.fix_command,
                auto_fixable=issue.auto_fixable,
                context=issue.context,
            )
            self.db.add(issue_model)

        await self.db.commit()
