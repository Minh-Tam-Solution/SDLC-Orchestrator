"""
Unit Tests for SpecificationService

Sprint 118: Governance System v2.0
SPEC-0002: Specification Standard (Framework 6.0.5)

Zero Mock Policy: Real database integration tests
Coverage Target: 95%+

Test Categories:
1. Specification Creation (10 tests)
2. Version Management (8 tests)
3. Status Transitions (8 tests)
4. Frontmatter Validation (6 tests)
5. Cross-Reference Graph (5 tests)
6. Validation (5 tests)
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance_specification import (
    GovernanceSpecification,
    SpecVersion,
    SpecFrontmatterMetadata,
    SpecFunctionalRequirement,
    SpecAcceptanceCriterion,
    SpecCrossReference,
)
from app.models.governance_vibecoding import SpecValidationResult
from app.models.project import Project
from app.models.user import User
from app.services.specification_service import (
    SpecificationService,
    SpecificationValidationError,
    SpecificationVersionConflictError,
)


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
async def spec_service(db_session: AsyncSession) -> SpecificationService:
    """Create SpecificationService instance with test database session."""
    return SpecificationService(db_session)


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project for specification tests."""
    project = Project(
        id=uuid4(),
        name="Test Project for Specifications",
        slug=f"test-project-spec-{uuid4().hex[:8]}",
        description="Test project for Sprint 118 specification tests",
        owner_id=test_user.id,
        policy_pack_tier="STANDARD",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for specification tests."""
    user = User(
        id=uuid4(),
        email="test-author@example.com",
        full_name="Test Author",
        password_hash="hashed_test_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def sample_spec_content() -> str:
    """Sample specification content with valid YAML frontmatter."""
    return """---
authors:
  - Test Author <test@example.com>
reviewers:
  - Senior Dev <senior@example.com>
stakeholders:
  - Product Manager
tags:
  - sprint-118
  - governance
dependencies:
  - SPEC-0001
---

# SPEC-0002: Specification Standard

## Overview

This specification defines the standard format for all SDLC specifications.

## Requirements

### FR-001: YAML Frontmatter

All specifications MUST include YAML frontmatter.

## Acceptance Criteria

- AC-001: Frontmatter is parseable YAML
- AC-002: Authors field is present and non-empty
"""


@pytest.fixture
def minimal_spec_content() -> str:
    """Minimal specification content with only mandatory fields."""
    return """---
authors:
  - Minimal Author
---

# Minimal Specification

This is a minimal specification with only mandatory fields.
"""


@pytest.fixture
def invalid_spec_content() -> str:
    """Specification content missing mandatory fields."""
    return """---
reviewers:
  - Reviewer Only
---

# Invalid Specification

This specification is missing the mandatory 'authors' field.
"""


# ═══════════════════════════════════════════════════════════════════
# 1. SPECIFICATION CREATION TESTS (10 tests)
# ═══════════════════════════════════════════════════════════════════

class TestSpecificationCreation:
    """Tests for specification creation."""

    @pytest.mark.asyncio
    async def test_create_specification_success(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        test_user: User,
        sample_spec_content: str,
    ):
        """Should create specification with valid content."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0002",
            spec_type="technical_spec",
            title="Specification Standard",
            file_path="docs/02-design/14-Technical-Specs/SPEC-0002.md",
            content=sample_spec_content,
            tier="STANDARD",
            created_by_id=test_user.id,
        )

        assert spec is not None
        assert spec.spec_number == "SPEC-0002"
        assert spec.title == "Specification Standard"
        assert spec.status == "draft"
        assert spec.version == "1.0.0"
        assert spec.tier == "STANDARD"

    @pytest.mark.asyncio
    async def test_create_specification_creates_version_record(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Should create initial version 1.0.0 record."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0003",
            spec_type="technical_spec",
            title="Version Test Spec",
            file_path="docs/specs/SPEC-0003.md",
            content=sample_spec_content,
        )

        # Query version record
        from sqlalchemy import select
        query = select(SpecVersion).where(SpecVersion.spec_id == spec.id)
        result = await db_session.execute(query)
        versions = list(result.scalars().all())

        assert len(versions) == 1
        assert versions[0].version == "1.0.0"
        assert versions[0].content_snapshot == sample_spec_content

    @pytest.mark.asyncio
    async def test_create_specification_creates_frontmatter_metadata(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Should create frontmatter metadata record."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0004",
            spec_type="technical_spec",
            title="Frontmatter Test Spec",
            file_path="docs/specs/SPEC-0004.md",
            content=sample_spec_content,
        )

        # Query frontmatter
        from sqlalchemy import select
        query = select(SpecFrontmatterMetadata).where(
            SpecFrontmatterMetadata.spec_id == spec.id
        )
        result = await db_session.execute(query)
        frontmatter = result.scalar_one_or_none()

        assert frontmatter is not None
        assert "Test Author" in str(frontmatter.authors)
        assert frontmatter.tags == ["sprint-118", "governance"]
        assert frontmatter.dependencies == ["SPEC-0001"]

    @pytest.mark.asyncio
    async def test_create_specification_calculates_content_hash(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Should calculate SHA256 content hash."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0005",
            spec_type="technical_spec",
            title="Hash Test Spec",
            file_path="docs/specs/SPEC-0005.md",
            content=sample_spec_content,
        )

        assert spec.content_hash is not None
        assert len(spec.content_hash) == 64  # SHA256 hex digest length

    @pytest.mark.asyncio
    async def test_create_specification_invalid_type_fails(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Should reject invalid spec type."""
        with pytest.raises(ValueError, match="Invalid spec_type"):
            await spec_service.create_specification(
                project_id=test_project.id,
                spec_number="SPEC-0006",
                spec_type="invalid_type",
                title="Invalid Type Spec",
                file_path="docs/specs/SPEC-0006.md",
                content=sample_spec_content,
            )

    @pytest.mark.asyncio
    async def test_create_specification_missing_authors_fails(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        invalid_spec_content: str,
    ):
        """Should reject content missing mandatory authors field."""
        with pytest.raises(SpecificationValidationError, match="Missing mandatory field: authors"):
            await spec_service.create_specification(
                project_id=test_project.id,
                spec_number="SPEC-0007",
                spec_type="technical_spec",
                title="Missing Authors Spec",
                file_path="docs/specs/SPEC-0007.md",
                content=invalid_spec_content,
            )

    @pytest.mark.asyncio
    async def test_create_specification_minimal_content_success(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        minimal_spec_content: str,
    ):
        """Should accept minimal content with only mandatory fields."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0008",
            spec_type="technical_spec",
            title="Minimal Spec",
            file_path="docs/specs/SPEC-0008.md",
            content=minimal_spec_content,
        )

        assert spec is not None
        assert spec.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_create_specification_adr_type(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        minimal_spec_content: str,
    ):
        """Should accept ADR spec type."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="ADR-041",
            spec_type="adr",
            title="Stage Dependency Matrix",
            file_path="docs/02-design/01-ADRs/ADR-041.md",
            content=minimal_spec_content,
        )

        assert spec.spec_type == "adr"
        assert spec.spec_number == "ADR-041"

    @pytest.mark.asyncio
    async def test_create_specification_stores_validation_result(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Should store validation result."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0009",
            spec_type="technical_spec",
            title="Validation Result Spec",
            file_path="docs/specs/SPEC-0009.md",
            content=sample_spec_content,
        )

        # Query validation result
        from sqlalchemy import select
        query = select(SpecValidationResult).where(
            SpecValidationResult.spec_id == spec.id
        )
        result = await db_session.execute(query)
        validation = result.scalar_one_or_none()

        assert validation is not None
        assert validation.is_valid is True
        assert validation.validation_type == "frontmatter"

    @pytest.mark.asyncio
    async def test_create_specification_unique_file_path(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Should enforce unique file path constraint."""
        # Create first spec
        await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-0010",
            spec_type="technical_spec",
            title="First Spec",
            file_path="docs/specs/unique-path.md",
            content=sample_spec_content,
        )

        # Attempt to create second spec with same path
        with pytest.raises(Exception):  # IntegrityError or similar
            await spec_service.create_specification(
                project_id=test_project.id,
                spec_number="SPEC-0011",
                spec_type="technical_spec",
                title="Second Spec",
                file_path="docs/specs/unique-path.md",  # Duplicate
                content=sample_spec_content,
            )


# ═══════════════════════════════════════════════════════════════════
# 2. VERSION MANAGEMENT TESTS (8 tests)
# ═══════════════════════════════════════════════════════════════════

class TestVersionManagement:
    """Tests for specification version management."""

    @pytest.mark.asyncio
    async def test_update_content_creates_new_version(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Updating content should create new version."""
        # Create spec
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-001",
            spec_type="technical_spec",
            title="Version Test",
            file_path="docs/specs/SPEC-VER-001.md",
            content=sample_spec_content,
        )

        # Update content
        updated_content = sample_spec_content + "\n## New Section\n"
        updated_spec = await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=updated_content,
            change_summary="Added new section",
        )

        assert updated_spec.version == "1.0.1"  # Patch bump

        # Query versions
        from sqlalchemy import select
        query = select(SpecVersion).where(SpecVersion.spec_id == spec.id)
        result = await db_session.execute(query)
        versions = list(result.scalars().all())

        assert len(versions) == 2

    @pytest.mark.asyncio
    async def test_update_content_patch_version_bump(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Default bump should be patch."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-002",
            spec_type="technical_spec",
            title="Patch Test",
            file_path="docs/specs/SPEC-VER-002.md",
            content=sample_spec_content,
        )

        updated = await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=sample_spec_content + "\nPatch change",
            change_summary="Patch update",
            bump_version="patch",
        )

        assert updated.version == "1.0.1"

    @pytest.mark.asyncio
    async def test_update_content_minor_version_bump(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Minor bump should reset patch."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-003",
            spec_type="technical_spec",
            title="Minor Test",
            file_path="docs/specs/SPEC-VER-003.md",
            content=sample_spec_content,
        )

        updated = await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=sample_spec_content + "\nMinor change",
            change_summary="Minor update",
            bump_version="minor",
        )

        assert updated.version == "1.1.0"

    @pytest.mark.asyncio
    async def test_update_content_major_version_bump(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Major bump should reset minor and patch."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-004",
            spec_type="technical_spec",
            title="Major Test",
            file_path="docs/specs/SPEC-VER-004.md",
            content=sample_spec_content,
        )

        updated = await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=sample_spec_content + "\nBreaking change",
            change_summary="Major update",
            bump_version="major",
        )

        assert updated.version == "2.0.0"

    @pytest.mark.asyncio
    async def test_update_content_no_change_returns_existing(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Identical content should not create new version."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-005",
            spec_type="technical_spec",
            title="No Change Test",
            file_path="docs/specs/SPEC-VER-005.md",
            content=sample_spec_content,
        )

        # Update with same content
        result = await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=sample_spec_content,  # Same content
            change_summary="No actual change",
        )

        assert result.version == "1.0.0"  # No version bump

    @pytest.mark.asyncio
    async def test_update_content_updates_hash(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Content update should update hash."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-006",
            spec_type="technical_spec",
            title="Hash Update Test",
            file_path="docs/specs/SPEC-VER-006.md",
            content=sample_spec_content,
        )
        original_hash = spec.content_hash

        updated = await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=sample_spec_content + "\nNew content",
            change_summary="Update hash",
        )

        assert updated.content_hash != original_hash

    @pytest.mark.asyncio
    async def test_update_content_stores_change_summary(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Change summary should be stored in version record."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-007",
            spec_type="technical_spec",
            title="Summary Test",
            file_path="docs/specs/SPEC-VER-007.md",
            content=sample_spec_content,
        )

        await spec_service.update_specification_content(
            spec_id=spec.id,
            new_content=sample_spec_content + "\nChange",
            change_summary="Added important feature X",
        )

        # Query latest version
        from sqlalchemy import select
        query = select(SpecVersion).where(
            SpecVersion.spec_id == spec.id
        ).order_by(SpecVersion.created_at.desc())
        result = await db_session.execute(query)
        latest = result.scalars().first()

        assert latest.change_summary == "Added important feature X"

    @pytest.mark.asyncio
    async def test_update_content_invalid_bump_type(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Invalid bump type should raise error."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VER-008",
            spec_type="technical_spec",
            title="Invalid Bump Test",
            file_path="docs/specs/SPEC-VER-008.md",
            content=sample_spec_content,
        )

        with pytest.raises(ValueError, match="Invalid bump_type"):
            await spec_service.update_specification_content(
                spec_id=spec.id,
                new_content=sample_spec_content + "\nChange",
                change_summary="Test",
                bump_version="invalid",
            )


# ═══════════════════════════════════════════════════════════════════
# 3. STATUS TRANSITIONS TESTS (8 tests)
# ═══════════════════════════════════════════════════════════════════

class TestStatusTransitions:
    """Tests for specification status workflow."""

    @pytest.mark.asyncio
    async def test_transition_draft_to_review(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Should allow draft → review transition."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-001",
            spec_type="technical_spec",
            title="Status Test",
            file_path="docs/specs/SPEC-STATUS-001.md",
            content=sample_spec_content,
        )

        assert spec.status == "draft"

        updated = await spec_service.transition_status(
            spec_id=spec.id,
            new_status="review",
        )

        assert updated.status == "review"

    @pytest.mark.asyncio
    async def test_transition_review_to_approved(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        test_user: User,
        sample_spec_content: str,
    ):
        """Should allow review → approved transition with approver."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-002",
            spec_type="technical_spec",
            title="Approval Test",
            file_path="docs/specs/SPEC-STATUS-002.md",
            content=sample_spec_content,
        )

        # First transition to review
        await spec_service.transition_status(spec_id=spec.id, new_status="review")

        # Then approve
        approved = await spec_service.transition_status(
            spec_id=spec.id,
            new_status="approved",
            approved_by_id=test_user.id,
        )

        assert approved.status == "approved"
        assert approved.approved_by_id == test_user.id
        assert approved.approved_at is not None

    @pytest.mark.asyncio
    async def test_transition_approved_requires_approver(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Approving without approver_id should fail."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-003",
            spec_type="technical_spec",
            title="No Approver Test",
            file_path="docs/specs/SPEC-STATUS-003.md",
            content=sample_spec_content,
        )

        await spec_service.transition_status(spec_id=spec.id, new_status="review")

        with pytest.raises(ValueError, match="approved_by_id required"):
            await spec_service.transition_status(
                spec_id=spec.id,
                new_status="approved",
                # Missing approved_by_id
            )

    @pytest.mark.asyncio
    async def test_transition_draft_to_deprecated(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Should allow draft → deprecated transition."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-004",
            spec_type="technical_spec",
            title="Deprecate Draft Test",
            file_path="docs/specs/SPEC-STATUS-004.md",
            content=sample_spec_content,
        )

        updated = await spec_service.transition_status(
            spec_id=spec.id,
            new_status="deprecated",
        )

        assert updated.status == "deprecated"

    @pytest.mark.asyncio
    async def test_transition_review_back_to_draft(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Should allow review → draft transition (reject/revise)."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-005",
            spec_type="technical_spec",
            title="Reject Test",
            file_path="docs/specs/SPEC-STATUS-005.md",
            content=sample_spec_content,
        )

        await spec_service.transition_status(spec_id=spec.id, new_status="review")

        updated = await spec_service.transition_status(
            spec_id=spec.id,
            new_status="draft",  # Send back for revisions
        )

        assert updated.status == "draft"

    @pytest.mark.asyncio
    async def test_transition_draft_to_approved_forbidden(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        test_user: User,
        sample_spec_content: str,
    ):
        """Should forbid direct draft → approved transition."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-006",
            spec_type="technical_spec",
            title="Skip Review Test",
            file_path="docs/specs/SPEC-STATUS-006.md",
            content=sample_spec_content,
        )

        with pytest.raises(ValueError, match="Cannot transition from draft to approved"):
            await spec_service.transition_status(
                spec_id=spec.id,
                new_status="approved",
                approved_by_id=test_user.id,
            )

    @pytest.mark.asyncio
    async def test_transition_deprecated_is_terminal(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Deprecated status should be terminal (no transitions out)."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-STATUS-007",
            spec_type="technical_spec",
            title="Terminal Test",
            file_path="docs/specs/SPEC-STATUS-007.md",
            content=sample_spec_content,
        )

        await spec_service.transition_status(spec_id=spec.id, new_status="deprecated")

        with pytest.raises(ValueError, match="Cannot transition from deprecated"):
            await spec_service.transition_status(
                spec_id=spec.id,
                new_status="draft",  # Attempt to un-deprecate
            )

    @pytest.mark.asyncio
    async def test_transition_nonexistent_spec(
        self,
        spec_service: SpecificationService,
    ):
        """Should raise error for non-existent specification."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await spec_service.transition_status(
                spec_id=fake_id,
                new_status="review",
            )


# ═══════════════════════════════════════════════════════════════════
# 4. FRONTMATTER VALIDATION TESTS (6 tests)
# ═══════════════════════════════════════════════════════════════════

class TestFrontmatterValidation:
    """Tests for YAML frontmatter validation."""

    @pytest.mark.asyncio
    async def test_extract_frontmatter_valid(
        self,
        spec_service: SpecificationService,
    ):
        """Should correctly extract valid frontmatter."""
        content = """---
authors:
  - Test Author
tags:
  - test
---

# Content
"""
        frontmatter = spec_service._extract_frontmatter(content)

        assert frontmatter["authors"] == ["Test Author"]
        assert frontmatter["tags"] == ["test"]

    @pytest.mark.asyncio
    async def test_extract_frontmatter_empty(
        self,
        spec_service: SpecificationService,
    ):
        """Content without frontmatter should return empty dict."""
        content = """# Just Content

No frontmatter here.
"""
        frontmatter = spec_service._extract_frontmatter(content)

        assert frontmatter == {}

    @pytest.mark.asyncio
    async def test_extract_frontmatter_invalid_yaml(
        self,
        spec_service: SpecificationService,
    ):
        """Invalid YAML should return empty dict."""
        content = """---
authors: [unclosed bracket
---

# Content
"""
        frontmatter = spec_service._extract_frontmatter(content)

        assert frontmatter == {}

    @pytest.mark.asyncio
    async def test_validate_frontmatter_missing_mandatory(
        self,
        spec_service: SpecificationService,
    ):
        """Missing mandatory field should produce error."""
        frontmatter = {
            "reviewers": ["Reviewer"],
            # Missing "authors"
        }

        errors, warnings = spec_service._validate_frontmatter(frontmatter)

        assert "Missing mandatory field: authors" in errors

    @pytest.mark.asyncio
    async def test_validate_frontmatter_missing_recommended(
        self,
        spec_service: SpecificationService,
    ):
        """Missing recommended field should produce warning."""
        frontmatter = {
            "authors": ["Author"],
            # Missing "reviewers", "stakeholders"
        }

        errors, warnings = spec_service._validate_frontmatter(frontmatter)

        assert len(errors) == 0
        assert any("reviewers" in w for w in warnings)
        assert any("stakeholders" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_validate_frontmatter_authors_must_be_list(
        self,
        spec_service: SpecificationService,
    ):
        """Authors field must be a list."""
        frontmatter = {
            "authors": "Single Author String",  # Should be list
        }

        errors, warnings = spec_service._validate_frontmatter(frontmatter)

        assert any("authors" in e and "list" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════
# 5. CROSS-REFERENCE GRAPH TESTS (5 tests)
# ═══════════════════════════════════════════════════════════════════

class TestCrossReferenceGraph:
    """Tests for specification cross-reference graph."""

    @pytest.mark.asyncio
    async def test_get_graph_no_references(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Spec with no references should have empty graph."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-GRAPH-001",
            spec_type="technical_spec",
            title="Isolated Spec",
            file_path="docs/specs/SPEC-GRAPH-001.md",
            content=sample_spec_content,
        )

        graph = await spec_service.get_specification_graph(spec_id=spec.id)

        assert graph["root"]["spec_number"] == "SPEC-GRAPH-001"
        assert graph["dependencies"] == []
        assert graph["dependents"] == []
        assert graph["related"] == []

    @pytest.mark.asyncio
    async def test_get_graph_with_dependencies(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Should return dependencies in graph."""
        # Create two specs
        spec1 = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-GRAPH-002",
            spec_type="technical_spec",
            title="Dependency Source",
            file_path="docs/specs/SPEC-GRAPH-002.md",
            content=sample_spec_content,
        )

        spec2 = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-GRAPH-003",
            spec_type="technical_spec",
            title="Dependency Target",
            file_path="docs/specs/SPEC-GRAPH-003.md",
            content=sample_spec_content,
        )

        # Create cross-reference
        cross_ref = SpecCrossReference(
            source_spec_id=spec1.id,
            target_spec_id=spec2.id,
            reference_type="depends_on",
        )
        db_session.add(cross_ref)
        await db_session.commit()

        # Get graph for spec1
        graph = await spec_service.get_specification_graph(spec_id=spec1.id)

        assert len(graph["dependencies"]) == 1
        assert graph["dependencies"][0]["type"] == "depends_on"

    @pytest.mark.asyncio
    async def test_get_graph_with_dependents(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Should return dependents (reverse dependencies) in graph."""
        spec1 = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-GRAPH-004",
            spec_type="technical_spec",
            title="Dependent",
            file_path="docs/specs/SPEC-GRAPH-004.md",
            content=sample_spec_content,
        )

        spec2 = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-GRAPH-005",
            spec_type="technical_spec",
            title="Base Spec",
            file_path="docs/specs/SPEC-GRAPH-005.md",
            content=sample_spec_content,
        )

        # spec1 depends on spec2
        cross_ref = SpecCrossReference(
            source_spec_id=spec1.id,
            target_spec_id=spec2.id,
            reference_type="depends_on",
        )
        db_session.add(cross_ref)
        await db_session.commit()

        # Get graph for spec2 (the dependency target)
        graph = await spec_service.get_specification_graph(spec_id=spec2.id)

        assert len(graph["dependents"]) == 1

    @pytest.mark.asyncio
    async def test_get_graph_nonexistent_spec(
        self,
        spec_service: SpecificationService,
    ):
        """Should raise error for non-existent specification."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await spec_service.get_specification_graph(spec_id=fake_id)

    @pytest.mark.asyncio
    async def test_get_graph_root_metadata(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Graph root should include spec metadata."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-GRAPH-006",
            spec_type="adr",
            title="ADR Graph Test",
            file_path="docs/specs/SPEC-GRAPH-006.md",
            content=sample_spec_content,
        )

        graph = await spec_service.get_specification_graph(spec_id=spec.id)

        assert graph["root"]["id"] == str(spec.id)
        assert graph["root"]["spec_number"] == "SPEC-GRAPH-006"
        assert graph["root"]["title"] == "ADR Graph Test"
        assert graph["root"]["version"] == "1.0.0"
        assert graph["root"]["status"] == "draft"


# ═══════════════════════════════════════════════════════════════════
# 6. CROSS-REFERENCE VALIDATION TESTS (5 tests)
# ═══════════════════════════════════════════════════════════════════

class TestCrossReferenceValidation:
    """Tests for cross-reference validation."""

    @pytest.mark.asyncio
    async def test_validate_no_references_valid(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
    ):
        """Spec with no references should be valid."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VAL-001",
            spec_type="technical_spec",
            title="No Refs",
            file_path="docs/specs/SPEC-VAL-001.md",
            content=sample_spec_content,
        )

        result = await spec_service.validate_cross_references(spec_id=spec.id)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_missing_dependency_error(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Missing dependency should produce error."""
        content_with_missing_dep = """---
authors:
  - Author
dependencies:
  - SPEC-NONEXISTENT
---

# Spec
"""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VAL-002",
            spec_type="technical_spec",
            title="Missing Dep",
            file_path="docs/specs/SPEC-VAL-002.md",
            content=content_with_missing_dep,
        )

        result = await spec_service.validate_cross_references(spec_id=spec.id)

        assert result["is_valid"] is False
        assert any("SPEC-NONEXISTENT" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_superseded_not_deprecated_warning(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Superseding non-deprecated spec should warn."""
        # Create spec to be superseded
        old_spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-OLD",
            spec_type="technical_spec",
            title="Old Spec",
            file_path="docs/specs/SPEC-OLD.md",
            content=sample_spec_content,
        )

        # Create new spec that supersedes old
        content_supersedes = """---
authors:
  - Author
supersedes:
  - SPEC-OLD
---

# New Spec
"""
        new_spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-NEW",
            spec_type="technical_spec",
            title="New Spec",
            file_path="docs/specs/SPEC-NEW.md",
            content=content_supersedes,
        )

        result = await spec_service.validate_cross_references(spec_id=new_spec.id)

        # Should have warning since SPEC-OLD is not deprecated
        assert any("deprecated" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_validate_stores_result(
        self,
        spec_service: SpecificationService,
        test_project: Project,
        sample_spec_content: str,
        db_session: AsyncSession,
    ):
        """Validation should store result."""
        spec = await spec_service.create_specification(
            project_id=test_project.id,
            spec_number="SPEC-VAL-004",
            spec_type="technical_spec",
            title="Store Result",
            file_path="docs/specs/SPEC-VAL-004.md",
            content=sample_spec_content,
        )

        await spec_service.validate_cross_references(spec_id=spec.id)

        # Query validation results
        from sqlalchemy import select
        query = select(SpecValidationResult).where(
            SpecValidationResult.spec_id == spec.id,
            SpecValidationResult.validation_type == "cross_references",
        )
        result = await db_session.execute(query)
        validation = result.scalar_one_or_none()

        assert validation is not None

    @pytest.mark.asyncio
    async def test_validate_nonexistent_spec(
        self,
        spec_service: SpecificationService,
    ):
        """Should raise error for non-existent specification."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await spec_service.validate_cross_references(spec_id=fake_id)
