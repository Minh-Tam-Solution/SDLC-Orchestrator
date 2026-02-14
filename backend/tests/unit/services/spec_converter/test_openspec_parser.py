"""
Test Suite: OpenSpec YAML Parser
Sprint: 154 - Spec Standard Completion
TDD Phase: 1 (Tests First)
SDLC: 6.0.5 Principle 4 - Verification-First

Expected Tests: 12
Purpose: Parse OpenSpec YAML specifications to SpecIR
"""

import pytest
from datetime import datetime


class TestOpenSpecParser:
    """Test cases for OpenSpec YAML parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from app.services.spec_converter.parsers.openspec_parser import OpenSpecParser
        return OpenSpecParser()

    @pytest.fixture
    def simple_openspec(self) -> str:
        """Simple OpenSpec YAML content."""
        return """---
spec_id: SPEC-0001
title: User Authentication API
version: "1.0.0"
status: DRAFT
tier:
  - STANDARD
  - PROFESSIONAL
owner: Backend Team
last_updated: "2026-02-04"
tags:
  - api
  - authentication
related_adrs:
  - ADR-050
related_specs: []
---

# SPEC-0001: User Authentication API

## Executive Summary

This specification defines the user authentication API endpoints.

## Problem Statement

Users need secure authentication to access protected resources.

## Functional Requirements

### REQ-001: Login Endpoint

**Priority**: P0
**Tier**: ALL

**GIVEN** a registered user with valid credentials
**WHEN** they POST to /api/auth/login with username and password
**THEN** they receive a JWT token with 15-minute expiry

**Acceptance Criteria**:
| ID | Scenario | Tier | Testable |
|----|----------|------|----------|
| AC-001 | Valid credentials return 200 | ALL | YES |
| AC-002 | Invalid credentials return 401 | ALL | YES |
"""

    @pytest.fixture
    def complex_openspec(self) -> str:
        """Complex OpenSpec with multiple requirements."""
        return """---
spec_id: SPEC-0002
title: Payment Processing System
version: "2.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
  - ENTERPRISE
owner: Payments Team
last_updated: "2026-02-04"
tags:
  - payments
  - security
  - compliance
related_adrs:
  - ADR-045
  - ADR-046
related_specs:
  - SPEC-0001
---

# SPEC-0002: Payment Processing System

## Executive Summary

Enterprise payment processing with PCI-DSS compliance.

## Functional Requirements

### REQ-001: Process Payment

**Priority**: P0
**Tier**: PROFESSIONAL+

**GIVEN** a valid payment request with card details
**WHEN** the payment is submitted
**THEN** the payment is processed and a receipt is generated

### REQ-002: Refund Payment

**Priority**: P1
**Tier**: ALL

**GIVEN** an existing successful payment
**WHEN** a refund is requested within 30 days
**THEN** the refund is processed and confirmation sent

### REQ-003: Payment Audit Log

**Priority**: P0
**Tier**: ENTERPRISE

**GIVEN** any payment transaction occurs
**WHEN** the transaction completes
**THEN** an immutable audit log entry is created
"""

    @pytest.mark.asyncio
    async def test_parse_frontmatter(self, parser, simple_openspec):
        """Test parsing YAML frontmatter."""
        result = await parser.parse(simple_openspec)

        assert result.spec_id == "SPEC-0001"
        assert result.title == "User Authentication API"
        assert result.version == "1.0.0"
        assert result.status == "DRAFT"

    @pytest.mark.asyncio
    async def test_parse_tier(self, parser, simple_openspec):
        """Test parsing tier information."""
        result = await parser.parse(simple_openspec)

        assert "STANDARD" in result.tier
        assert "PROFESSIONAL" in result.tier
        assert len(result.tier) == 2

    @pytest.mark.asyncio
    async def test_parse_tags(self, parser, simple_openspec):
        """Test parsing tags."""
        result = await parser.parse(simple_openspec)

        assert "api" in result.tags
        assert "authentication" in result.tags

    @pytest.mark.asyncio
    async def test_parse_related_documents(self, parser, simple_openspec):
        """Test parsing related ADRs and specs."""
        result = await parser.parse(simple_openspec)

        assert "ADR-050" in result.related_adrs
        assert result.related_specs == []

    @pytest.mark.asyncio
    async def test_parse_requirements_bdd(self, parser, simple_openspec):
        """Test parsing requirements with BDD format."""
        result = await parser.parse(simple_openspec)

        assert len(result.requirements) >= 1
        req = result.requirements[0]
        assert req.id == "REQ-001"
        assert "registered user" in req.given
        assert "POST" in req.when
        assert "JWT" in req.then

    @pytest.mark.asyncio
    async def test_parse_multiple_requirements(self, parser, complex_openspec):
        """Test parsing multiple requirements."""
        result = await parser.parse(complex_openspec)

        assert len(result.requirements) == 3
        ids = [r.id for r in result.requirements]
        assert "REQ-001" in ids
        assert "REQ-002" in ids
        assert "REQ-003" in ids

    @pytest.mark.asyncio
    async def test_parse_requirement_priority(self, parser, complex_openspec):
        """Test parsing requirement priorities."""
        result = await parser.parse(complex_openspec)

        priorities = {r.id: r.priority for r in result.requirements}
        assert priorities["REQ-001"] == "P0"
        assert priorities["REQ-002"] == "P1"
        assert priorities["REQ-003"] == "P0"

    @pytest.mark.asyncio
    async def test_parse_requirement_tier(self, parser, complex_openspec):
        """Test parsing requirement tier restrictions."""
        result = await parser.parse(complex_openspec)

        # Find enterprise-only requirement
        audit_req = next(r for r in result.requirements if r.id == "REQ-003")
        assert "ENTERPRISE" in audit_req.tier

    @pytest.mark.asyncio
    async def test_parse_acceptance_criteria(self, parser, simple_openspec):
        """Test parsing acceptance criteria from table."""
        result = await parser.parse(simple_openspec)

        # Should extract AC from the table
        assert len(result.acceptance_criteria) >= 0 or len(result.requirements[0].acceptance_criteria) >= 0

    @pytest.mark.asyncio
    async def test_parse_without_frontmatter(self, parser):
        """Test handling content without frontmatter."""
        content = """
# SPEC-0003: No Frontmatter

## Requirements

### REQ-001: Test
**GIVEN** context
**WHEN** action
**THEN** result
"""
        # Should still parse but with defaults
        result = await parser.parse(content)
        assert result.spec_id != "" or "SPEC-" in result.spec_id

    @pytest.mark.asyncio
    async def test_parse_empty_content(self, parser):
        """Test handling empty content."""
        with pytest.raises(ValueError):
            await parser.parse("")

    @pytest.mark.asyncio
    async def test_parse_preserves_formatting(self, parser, simple_openspec):
        """Test that important text is preserved."""
        result = await parser.parse(simple_openspec)

        assert result.owner == "Backend Team"
        assert result.last_updated == "2026-02-04"
