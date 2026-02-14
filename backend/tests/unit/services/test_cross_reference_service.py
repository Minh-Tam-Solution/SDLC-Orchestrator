"""
=========================================================================
Cross-Reference Validation Service Tests
SDLC Orchestrator - Sprint 155 Day 3 (Track 2: Cross-Reference Validation)

Version: 1.0.0
Date: February 4, 2026
Status: ACTIVE - Sprint 155 Testing
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Test Coverage:
- ADR ↔ Spec bidirectional link validation
- Spec ↔ Test Case reference checking
- Broken link detection
- Circular dependency detection
- Orphaned document alerts

Zero Mock Policy: Real service tests with mocked file system
=========================================================================
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.cross_reference_service import (
    CrossReferenceService,
    CrossReferenceViolation,
    LinkType,
    ValidationResult,
    get_cross_reference_service,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def cross_ref_service():
    """Create cross-reference validation service for testing."""
    return CrossReferenceService()


@pytest.fixture
def sample_project_id():
    """Sample project UUID."""
    return uuid4()


@pytest.fixture
def sample_adr_files():
    """Sample ADR document files."""
    return [
        "docs/02-design/01-ADRs/ADR-001-Database-Choice.md",
        "docs/02-design/01-ADRs/ADR-002-API-Framework.md",
        "docs/02-design/01-ADRs/ADR-003-Auth-Strategy.md",
    ]


@pytest.fixture
def sample_spec_files():
    """Sample spec files."""
    return [
        "docs/02-design/14-Technical-Specs/SPEC-0001-User-Authentication.md",
        "docs/02-design/14-Technical-Specs/SPEC-0002-API-Gateway.md",
    ]


@pytest.fixture
def sample_test_files():
    """Sample test files."""
    return [
        "backend/tests/unit/services/test_auth_service.py",
        "backend/tests/unit/services/test_api_gateway.py",
    ]


# =========================================================================
# Test: Link Extraction
# =========================================================================


class TestLinkExtraction:
    """Test extracting links from documents."""

    @pytest.mark.asyncio
    async def test_extract_adr_links_from_spec(
        self,
        cross_ref_service: CrossReferenceService,
    ):
        """Test extracting ADR references from a spec document."""
        spec_content = """
        # SPEC-0001: User Authentication

        ## Related ADRs
        - [ADR-001: Database Choice](../../01-ADRs/ADR-001-Database-Choice.md)
        - [ADR-003: Auth Strategy](../../01-ADRs/ADR-003-Auth-Strategy.md)

        ## Requirements
        This spec implements requirements from ADR-003.
        """

        links = await cross_ref_service.extract_links(
            content=spec_content,
            source_file="docs/02-design/14-Technical-Specs/SPEC-0001-User-Authentication.md",
        )

        assert len(links) >= 2
        adr_links = [l for l in links if l.link_type == LinkType.ADR_REF]
        assert len(adr_links) == 2

    @pytest.mark.asyncio
    async def test_extract_spec_links_from_adr(
        self,
        cross_ref_service: CrossReferenceService,
    ):
        """Test extracting Spec references from an ADR document."""
        adr_content = """
        # ADR-003: Authentication Strategy

        ## Context
        We need to decide on authentication approach.

        ## Related Specs
        - [SPEC-0001: User Authentication](../14-Technical-Specs/SPEC-0001-User-Authentication.md)

        ## Decision
        Use JWT with refresh tokens.
        """

        links = await cross_ref_service.extract_links(
            content=adr_content,
            source_file="docs/02-design/01-ADRs/ADR-003-Auth-Strategy.md",
        )

        spec_links = [l for l in links if l.link_type == LinkType.SPEC_REF]
        assert len(spec_links) == 1

    @pytest.mark.asyncio
    async def test_extract_test_links_from_spec(
        self,
        cross_ref_service: CrossReferenceService,
    ):
        """Test extracting test file references from spec."""
        spec_content = """
        # SPEC-0001: User Authentication

        ## Test Coverage
        - Unit tests: `backend/tests/unit/services/test_auth_service.py`
        - Integration tests: `backend/tests/integration/test_auth_flow.py`
        """

        links = await cross_ref_service.extract_links(
            content=spec_content,
            source_file="docs/02-design/14-Technical-Specs/SPEC-0001-User-Authentication.md",
        )

        test_links = [l for l in links if l.link_type == LinkType.TEST_REF]
        assert len(test_links) >= 1


# =========================================================================
# Test: Broken Link Detection
# =========================================================================


class TestBrokenLinkDetection:
    """Test detecting broken links in documents."""

    @pytest.mark.asyncio
    async def test_detect_broken_link(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test detecting a broken link (target file doesn't exist)."""
        with patch.object(
            cross_ref_service,
            "_file_exists",
            return_value=False,
        ):
            result = await cross_ref_service.validate_link(
                project_id=sample_project_id,
                source_file="docs/02-design/14-Technical-Specs/SPEC-0001.md",
                target_file="docs/02-design/01-ADRs/ADR-999-NonExistent.md",
                link_type=LinkType.ADR_REF,
            )

            assert result.is_valid is False
            assert result.violation is not None
            assert result.violation.violation_type == "broken_link"

    @pytest.mark.asyncio
    async def test_valid_link(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test validating an existing link."""
        with patch.object(
            cross_ref_service,
            "_file_exists",
            return_value=True,
        ):
            result = await cross_ref_service.validate_link(
                project_id=sample_project_id,
                source_file="docs/02-design/14-Technical-Specs/SPEC-0001.md",
                target_file="docs/02-design/01-ADRs/ADR-001-Database-Choice.md",
                link_type=LinkType.ADR_REF,
            )

            assert result.is_valid is True
            assert result.violation is None


# =========================================================================
# Test: Bidirectional Link Validation
# =========================================================================


class TestBidirectionalValidation:
    """Test bidirectional link validation (ADR ↔ Spec)."""

    @pytest.mark.asyncio
    async def test_detect_missing_backlink(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test detecting when ADR references Spec but Spec doesn't reference ADR."""
        # ADR-001 references SPEC-0001, but SPEC-0001 doesn't reference ADR-001
        forward_links = {
            "docs/02-design/01-ADRs/ADR-001.md": [
                "docs/02-design/14-Technical-Specs/SPEC-0001.md"
            ]
        }
        back_links = {
            "docs/02-design/14-Technical-Specs/SPEC-0001.md": []  # No backlink!
        }

        violations = await cross_ref_service.validate_bidirectional_links(
            project_id=sample_project_id,
            forward_links=forward_links,
            back_links=back_links,
        )

        assert len(violations) >= 1
        assert any(v.violation_type == "missing_backlink" for v in violations)

    @pytest.mark.asyncio
    async def test_valid_bidirectional_links(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test valid bidirectional links."""
        forward_links = {
            "docs/02-design/01-ADRs/ADR-001.md": [
                "docs/02-design/14-Technical-Specs/SPEC-0001.md"
            ]
        }
        back_links = {
            "docs/02-design/14-Technical-Specs/SPEC-0001.md": [
                "docs/02-design/01-ADRs/ADR-001.md"
            ]
        }

        violations = await cross_ref_service.validate_bidirectional_links(
            project_id=sample_project_id,
            forward_links=forward_links,
            back_links=back_links,
        )

        # No missing backlink violations
        backlink_violations = [v for v in violations if v.violation_type == "missing_backlink"]
        assert len(backlink_violations) == 0


# =========================================================================
# Test: Circular Dependency Detection
# =========================================================================


class TestCircularDependencyDetection:
    """Test detecting circular dependencies in document links."""

    @pytest.mark.asyncio
    async def test_detect_simple_circular_dependency(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test detecting A → B → A circular dependency."""
        dependencies = {
            "A.md": ["B.md"],
            "B.md": ["A.md"],  # Circular!
        }

        violations = await cross_ref_service.detect_circular_dependencies(
            project_id=sample_project_id,
            dependencies=dependencies,
        )

        assert len(violations) >= 1
        assert any(v.violation_type == "circular_dependency" for v in violations)

    @pytest.mark.asyncio
    async def test_detect_chain_circular_dependency(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test detecting A → B → C → A circular dependency."""
        dependencies = {
            "A.md": ["B.md"],
            "B.md": ["C.md"],
            "C.md": ["A.md"],  # Circular through chain!
        }

        violations = await cross_ref_service.detect_circular_dependencies(
            project_id=sample_project_id,
            dependencies=dependencies,
        )

        assert len(violations) >= 1
        circular = [v for v in violations if v.violation_type == "circular_dependency"]
        assert len(circular) >= 1

    @pytest.mark.asyncio
    async def test_no_circular_dependency(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test valid DAG with no circular dependencies."""
        dependencies = {
            "A.md": ["B.md", "C.md"],
            "B.md": ["D.md"],
            "C.md": ["D.md"],
            "D.md": [],
        }

        violations = await cross_ref_service.detect_circular_dependencies(
            project_id=sample_project_id,
            dependencies=dependencies,
        )

        circular = [v for v in violations if v.violation_type == "circular_dependency"]
        assert len(circular) == 0


# =========================================================================
# Test: Orphaned Document Detection
# =========================================================================


class TestOrphanedDocumentDetection:
    """Test detecting orphaned documents (no incoming/outgoing links)."""

    @pytest.mark.asyncio
    async def test_detect_orphaned_spec(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test detecting a spec with no ADR references."""
        all_specs = [
            "docs/02-design/14-Technical-Specs/SPEC-0001.md",
            "docs/02-design/14-Technical-Specs/SPEC-0002.md",
        ]
        linked_specs = ["docs/02-design/14-Technical-Specs/SPEC-0001.md"]

        orphaned = await cross_ref_service.detect_orphaned_documents(
            project_id=sample_project_id,
            all_documents=all_specs,
            linked_documents=linked_specs,
            doc_type="SPEC",
        )

        assert len(orphaned) == 1
        assert orphaned[0].violation_type == "orphaned_document"
        assert "SPEC-0002" in orphaned[0].source_file

    @pytest.mark.asyncio
    async def test_no_orphaned_documents(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test when all documents have proper links."""
        all_specs = [
            "docs/02-design/14-Technical-Specs/SPEC-0001.md",
            "docs/02-design/14-Technical-Specs/SPEC-0002.md",
        ]
        linked_specs = all_specs  # All specs are linked

        orphaned = await cross_ref_service.detect_orphaned_documents(
            project_id=sample_project_id,
            all_documents=all_specs,
            linked_documents=linked_specs,
            doc_type="SPEC",
        )

        assert len(orphaned) == 0


# =========================================================================
# Test: Full Project Validation
# =========================================================================


class TestFullProjectValidation:
    """Test full project cross-reference validation."""

    @pytest.mark.asyncio
    async def test_validate_project_success(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test successful project validation with no violations."""
        with patch.object(
            cross_ref_service,
            "_scan_project_files",
            return_value={
                "adrs": ["ADR-001.md"],
                "specs": ["SPEC-0001.md"],
                "tests": ["test_auth.py"],
            },
        ), patch.object(
            cross_ref_service,
            "_extract_all_links",
            return_value={},
        ), patch.object(
            cross_ref_service,
            "_file_exists",
            return_value=True,
        ):
            result = await cross_ref_service.validate_project(
                project_id=sample_project_id,
                project_path="/path/to/project",
            )

            assert isinstance(result, ValidationResult)
            assert result.is_valid is True
            assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_validate_project_with_violations(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test project validation with multiple violations."""
        mock_violations = [
            CrossReferenceViolation(
                violation_type="broken_link",
                source_file="SPEC-0001.md",
                target_file="ADR-999.md",
                message="Target file does not exist",
            ),
        ]

        with patch.object(
            cross_ref_service,
            "_run_all_validations",
            return_value=(mock_violations, 5),
        ):
            result = await cross_ref_service.validate_project(
                project_id=sample_project_id,
                project_path="/path/to/project",
            )

            assert result.is_valid is False
            assert len(result.violations) >= 1


# =========================================================================
# Test: Get Links for Document
# =========================================================================


class TestGetDocumentLinks:
    """Test getting links for a specific document."""

    @pytest.mark.asyncio
    async def test_get_incoming_links(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test getting all incoming links for a document."""
        with patch.object(
            cross_ref_service,
            "_find_incoming_links",
            return_value=[
                {"source": "ADR-001.md", "type": "adr_ref"},
                {"source": "ADR-002.md", "type": "adr_ref"},
            ],
        ):
            result = await cross_ref_service.get_document_links(
                project_id=sample_project_id,
                document_path="docs/02-design/14-Technical-Specs/SPEC-0001.md",
                direction="incoming",
            )

            assert len(result.incoming) == 2

    @pytest.mark.asyncio
    async def test_get_outgoing_links(
        self,
        cross_ref_service: CrossReferenceService,
        sample_project_id: UUID,
    ):
        """Test getting all outgoing links from a document."""
        with patch.object(
            cross_ref_service,
            "_find_outgoing_links",
            return_value=[
                {"target": "ADR-001.md", "type": "adr_ref"},
            ],
        ):
            result = await cross_ref_service.get_document_links(
                project_id=sample_project_id,
                document_path="docs/02-design/14-Technical-Specs/SPEC-0001.md",
                direction="outgoing",
            )

            assert len(result.outgoing) == 1


# =========================================================================
# Test: Factory Function
# =========================================================================


class TestFactoryFunction:
    """Test service factory function."""

    def test_get_cross_reference_service(self):
        """Test factory function returns service instance."""
        service = get_cross_reference_service()
        assert isinstance(service, CrossReferenceService)
