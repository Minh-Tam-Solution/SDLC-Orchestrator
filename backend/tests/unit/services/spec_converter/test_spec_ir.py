"""
Test Suite: Spec IR (Intermediate Representation) Models
Sprint: 154 - Spec Standard Completion
TDD Phase: 1 (Tests First)
SDLC: 6.0.3 Principle 4 - Verification-First

Expected Tests: 8
Purpose: Validate IR Schema models, serialization, validation
"""

import pytest
from datetime import datetime
from typing import Any


class TestSpecIR:
    """Test cases for SpecIR model."""

    def test_spec_ir_creation_minimal(self):
        """Test SpecIR creation with minimal required fields."""
        from app.services.spec_converter.models import SpecIR

        spec = SpecIR(
            spec_id="SPEC-0001",
            title="Test Specification",
            last_updated=datetime.utcnow().isoformat()
        )

        assert spec.spec_id == "SPEC-0001"
        assert spec.title == "Test Specification"
        assert spec.version == "1.0.0"  # Default
        assert spec.status == "DRAFT"  # Default
        assert len(spec.tier) == 4  # All tiers by default

    def test_spec_ir_creation_full(self):
        """Test SpecIR creation with all fields."""
        from app.services.spec_converter.models import SpecIR, SpecRequirement

        req = SpecRequirement(
            id="REQ-001",
            title="Test Requirement",
            given="a user is logged in",
            when="they click submit",
            then="the form is saved"
        )

        spec = SpecIR(
            spec_id="SPEC-0002",
            title="Full Specification",
            version="2.0.0",
            status="APPROVED",
            tier=["PROFESSIONAL", "ENTERPRISE"],
            owner="Backend Team",
            last_updated="2026-02-04",
            tags=["api", "security"],
            related_adrs=["ADR-050"],
            related_specs=["SPEC-0001"],
            executive_summary="Test summary",
            problem_statement="Test problem",
            requirements=[req]
        )

        assert spec.spec_id == "SPEC-0002"
        assert spec.version == "2.0.0"
        assert spec.status == "APPROVED"
        assert len(spec.tier) == 2
        assert len(spec.requirements) == 1
        assert spec.requirements[0].id == "REQ-001"

    def test_spec_ir_serialization(self):
        """Test SpecIR JSON serialization."""
        from app.services.spec_converter.models import SpecIR

        spec = SpecIR(
            spec_id="SPEC-0003",
            title="Serialization Test",
            last_updated="2026-02-04"
        )

        json_data = spec.model_dump()

        assert isinstance(json_data, dict)
        assert json_data["spec_id"] == "SPEC-0003"
        assert "title" in json_data
        assert "requirements" in json_data

    def test_spec_ir_deserialization(self):
        """Test SpecIR creation from dict."""
        from app.services.spec_converter.models import SpecIR

        data = {
            "spec_id": "SPEC-0004",
            "title": "From Dict",
            "version": "1.0.0",
            "status": "DRAFT",
            "tier": ["LITE"],
            "owner": "Test",
            "last_updated": "2026-02-04",
            "tags": [],
            "related_adrs": [],
            "related_specs": [],
            "executive_summary": "",
            "problem_statement": "",
            "requirements": [],
            "acceptance_criteria": []
        }

        spec = SpecIR(**data)

        assert spec.spec_id == "SPEC-0004"
        assert spec.tier == ["LITE"]


class TestSpecRequirement:
    """Test cases for SpecRequirement model."""

    def test_requirement_creation_minimal(self):
        """Test SpecRequirement with minimal BDD fields."""
        from app.services.spec_converter.models import SpecRequirement

        req = SpecRequirement(
            id="REQ-001",
            title="Login Feature",
            given="a registered user",
            when="they enter credentials",
            then="they are logged in"
        )

        assert req.id == "REQ-001"
        assert req.priority == "P1"  # Default
        assert req.tier == ["ALL"]  # Default
        assert "registered user" in req.given
        assert "credentials" in req.when
        assert "logged in" in req.then

    def test_requirement_with_user_story(self):
        """Test SpecRequirement with optional user story."""
        from app.services.spec_converter.models import SpecRequirement

        req = SpecRequirement(
            id="REQ-002",
            title="Login Feature",
            given="a registered user",
            when="they enter credentials",
            then="they are logged in",
            user_story="As a user, I want to login so that I can access my account",
            acceptance_criteria=["AC-001", "AC-002"]
        )

        assert req.user_story is not None
        assert "As a user" in req.user_story
        assert len(req.acceptance_criteria) == 2

    def test_requirement_priority_validation(self):
        """Test SpecRequirement priority values."""
        from app.services.spec_converter.models import SpecRequirement

        for priority in ["P0", "P1", "P2", "P3"]:
            req = SpecRequirement(
                id=f"REQ-{priority}",
                title=f"Priority {priority}",
                priority=priority,
                given="context",
                when="action",
                then="outcome"
            )
            assert req.priority == priority


class TestAcceptanceCriterion:
    """Test cases for AcceptanceCriterion model."""

    def test_acceptance_criterion_creation(self):
        """Test AcceptanceCriterion with BDD format."""
        from app.services.spec_converter.models import AcceptanceCriterion

        ac = AcceptanceCriterion(
            id="AC-001",
            scenario="Successful login",
            given="a valid username and password",
            when="the user clicks login",
            then="the user is redirected to dashboard"
        )

        assert ac.id == "AC-001"
        assert ac.testable == True  # Default
        assert ac.tier == ["ALL"]  # Default

    def test_acceptance_criterion_tier_specific(self):
        """Test AcceptanceCriterion with tier restriction."""
        from app.services.spec_converter.models import AcceptanceCriterion

        ac = AcceptanceCriterion(
            id="AC-002",
            scenario="Enterprise audit logging",
            given="an enterprise tier user",
            when="any action is performed",
            then="the action is logged to audit trail",
            tier=["ENTERPRISE"],
            testable=True
        )

        assert ac.tier == ["ENTERPRISE"]
        assert ac.testable == True
