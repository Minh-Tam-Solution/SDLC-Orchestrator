"""
E2E Integration Tests - Spec Converter
Sprint 154 Day 5 - TDD Phase 1 (RED)

End-to-end tests for the complete spec conversion workflow.

Test Scenarios:
1. Full BDD → OpenSpec → BDD roundtrip
2. User Story → BDD → OpenSpec conversion chain
3. Format detection + auto-conversion
4. Template instantiation + export
5. Import from external format

Architecture: ADR-050 Integration Testing
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """Create async HTTP client for E2E testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


class TestSpecConverterE2EWorkflow:
    """End-to-end workflow tests for spec converter."""

    @pytest.mark.asyncio
    async def test_bdd_to_openspec_roundtrip(self, client: AsyncClient):
        """Test full BDD → OpenSpec → BDD roundtrip preserves content."""
        # Original BDD content
        bdd_content = """Feature: User Authentication
  As a user
  I want to login with my credentials
  So that I can access my account

  Scenario: Valid login
    Given a registered user with email "test@example.com"
    When they enter valid credentials
    Then they should see the dashboard
    And their session should be active"""

        # Step 1: Parse BDD to IR
        parse_response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": bdd_content, "source_format": "BDD"},
        )
        assert parse_response.status_code == 200
        ir_data = parse_response.json()
        assert ir_data["title"] == "User Authentication"
        assert len(ir_data["requirements"]) >= 1

        # Step 2: Render IR to OpenSpec
        render_response = await client.post(
            "/api/v1/spec-converter/render",
            json={"ir": ir_data, "target_format": "OPENSPEC"},
        )
        assert render_response.status_code == 200
        openspec_content = render_response.json()["content"]
        assert "spec_id:" in openspec_content
        assert "User Authentication" in openspec_content

        # Step 3: Parse OpenSpec back to IR
        parse_back_response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": openspec_content, "source_format": "OPENSPEC"},
        )
        assert parse_back_response.status_code == 200
        ir_back = parse_back_response.json()
        assert ir_back["title"] == "User Authentication"

        # Step 4: Render back to BDD
        final_response = await client.post(
            "/api/v1/spec-converter/render",
            json={"ir": ir_back, "target_format": "BDD"},
        )
        assert final_response.status_code == 200
        final_bdd = final_response.json()["content"]
        assert "Feature:" in final_bdd
        assert "Scenario:" in final_bdd

    @pytest.mark.asyncio
    async def test_user_story_to_bdd_to_openspec_chain(self, client: AsyncClient):
        """Test User Story → BDD → OpenSpec conversion chain."""
        user_story = "As a customer, I want to add items to my cart so that I can purchase them later"

        # Step 1: Parse User Story
        parse_response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": user_story, "source_format": "USER_STORY"},
        )
        assert parse_response.status_code == 200
        ir_data = parse_response.json()
        assert len(ir_data["requirements"]) >= 1

        # Step 2: Render to BDD
        bdd_response = await client.post(
            "/api/v1/spec-converter/render",
            json={"ir": ir_data, "target_format": "BDD"},
        )
        assert bdd_response.status_code == 200
        bdd_content = bdd_response.json()["content"]
        assert "Feature:" in bdd_content

        # Step 3: Use direct convert endpoint
        convert_response = await client.post(
            "/api/v1/spec-converter/convert",
            json={
                "content": user_story,
                "source_format": "USER_STORY",
                "target_format": "OPENSPEC",
            },
        )
        assert convert_response.status_code == 200
        openspec_content = convert_response.json()["content"]
        assert "spec_id:" in openspec_content

    @pytest.mark.asyncio
    async def test_format_detection_and_auto_conversion(self, client: AsyncClient):
        """Test format auto-detection followed by conversion."""
        # Test BDD detection
        bdd_content = """Feature: Test Feature
  Scenario: Test Scenario
    Given a condition
    When an action
    Then a result"""

        detect_response = await client.post(
            "/api/v1/spec-converter/detect",
            json={"content": bdd_content},
        )
        assert detect_response.status_code == 200
        assert detect_response.json()["format"] == "BDD"

        # Test OpenSpec detection
        openspec_content = """---
spec_id: SPEC-001
title: Test Spec
status: DRAFT
---
# Content"""

        detect_response = await client.post(
            "/api/v1/spec-converter/detect",
            json={"content": openspec_content},
        )
        assert detect_response.status_code == 200
        assert detect_response.json()["format"] == "OPENSPEC"

        # Test User Story detection
        user_story = "As a user, I want to do something so that I get value"

        detect_response = await client.post(
            "/api/v1/spec-converter/detect",
            json={"content": user_story},
        )
        assert detect_response.status_code == 200
        assert detect_response.json()["format"] == "USER_STORY"

    @pytest.mark.asyncio
    async def test_complex_spec_with_multiple_requirements(self, client: AsyncClient):
        """Test parsing and rendering spec with multiple requirements."""
        complex_bdd = """Feature: E-commerce Checkout
  As a customer
  I want to complete my purchase
  So that I receive my ordered items

  Scenario: Add item to cart
    Given I am on a product page
    When I click "Add to Cart"
    Then the item should be in my cart
    And the cart count should increase

  Scenario: Apply discount code
    Given I have items in my cart
    When I enter a valid discount code
    Then the discount should be applied
    And the total should be reduced

  Scenario: Complete checkout
    Given I have items in my cart
    And I am logged in
    When I click "Checkout"
    And I enter my shipping address
    And I enter my payment details
    Then my order should be confirmed
    And I should receive a confirmation email"""

        # Parse
        parse_response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": complex_bdd, "source_format": "BDD"},
        )
        assert parse_response.status_code == 200
        ir_data = parse_response.json()
        assert ir_data["title"] == "E-commerce Checkout"
        assert len(ir_data["requirements"]) >= 3

        # Convert to OpenSpec
        convert_response = await client.post(
            "/api/v1/spec-converter/convert",
            json={
                "content": complex_bdd,
                "source_format": "BDD",
                "target_format": "OPENSPEC",
            },
        )
        assert convert_response.status_code == 200
        openspec = convert_response.json()["content"]
        assert "E-commerce Checkout" in openspec
        assert "REQ-" in openspec or "Scenario" in openspec


class TestSpecConverterErrorHandling:
    """Error handling tests for spec converter."""

    @pytest.mark.asyncio
    async def test_parse_invalid_format_returns_400(self, client: AsyncClient):
        """Test that invalid format returns 400."""
        response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": "some content", "source_format": "INVALID"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_parse_empty_content_returns_400(self, client: AsyncClient):
        """Test that empty content returns 400."""
        response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": "", "source_format": "BDD"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_render_invalid_format_returns_400(self, client: AsyncClient):
        """Test that rendering to invalid format returns 400."""
        response = await client.post(
            "/api/v1/spec-converter/render",
            json={
                "ir": {"spec_id": "SPEC-001", "title": "Test"},
                "target_format": "INVALID",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_convert_missing_fields_returns_422(self, client: AsyncClient):
        """Test that missing required fields returns 422."""
        response = await client.post(
            "/api/v1/spec-converter/convert",
            json={"content": "some content"},
        )
        assert response.status_code == 422


class TestSpecConverterPerformance:
    """Performance tests for spec converter."""

    @pytest.mark.asyncio
    async def test_parse_large_spec_under_timeout(self, client: AsyncClient):
        """Test parsing large spec completes within timeout."""
        # Generate a large BDD spec
        scenarios = []
        for i in range(20):
            scenarios.append(f"""
  Scenario: Test scenario {i}
    Given precondition {i}
    When action {i}
    Then result {i}""")

        large_bdd = f"""Feature: Large Feature
  As a tester
  I want to test large specs
  So that I know performance is acceptable
{"".join(scenarios)}"""

        response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": large_bdd, "source_format": "BDD"},
            timeout=10.0,  # 10 second timeout
        )
        assert response.status_code == 200
        ir_data = response.json()
        assert len(ir_data["requirements"]) >= 10

    @pytest.mark.asyncio
    async def test_convert_response_time(self, client: AsyncClient):
        """Test conversion completes in reasonable time."""
        import time

        content = """Feature: Performance Test
  Scenario: Quick conversion
    Given a simple spec
    When converted
    Then it should be fast"""

        start = time.time()
        response = await client.post(
            "/api/v1/spec-converter/convert",
            json={
                "content": content,
                "source_format": "BDD",
                "target_format": "OPENSPEC",
            },
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0  # Should complete in under 2 seconds


class TestSpecConverterDataIntegrity:
    """Data integrity tests for spec converter."""

    @pytest.mark.asyncio
    async def test_metadata_preserved_through_conversion(self, client: AsyncClient):
        """Test that metadata is preserved through conversion."""
        openspec_with_metadata = """---
spec_id: SPEC-TEST-001
title: Metadata Test
version: 2.0.0
status: PROPOSED
tier: [PROFESSIONAL, ENTERPRISE]
owner: test@example.com
tags: [critical, security, auth]
related_adrs: [ADR-001, ADR-002]
---

## Requirements

### REQ-001: Test Requirement [P0] [PROFESSIONAL]

**GIVEN** a precondition
**WHEN** an action
**THEN** a result
"""

        # Parse
        parse_response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": openspec_with_metadata, "source_format": "OPENSPEC"},
        )
        assert parse_response.status_code == 200
        ir_data = parse_response.json()

        # Verify metadata preserved
        assert ir_data["spec_id"] == "SPEC-TEST-001"
        assert ir_data["title"] == "Metadata Test"
        assert ir_data["version"] == "2.0.0"
        assert ir_data["status"] == "PROPOSED"
        assert ir_data["owner"] == "test@example.com"

        # Render back and verify
        render_response = await client.post(
            "/api/v1/spec-converter/render",
            json={"ir": ir_data, "target_format": "OPENSPEC"},
        )
        assert render_response.status_code == 200
        rendered = render_response.json()["content"]

        assert "SPEC-TEST-001" in rendered
        assert "Metadata Test" in rendered
        assert "2.0.0" in rendered

    @pytest.mark.asyncio
    async def test_requirements_preserved_through_roundtrip(self, client: AsyncClient):
        """Test that requirements are preserved through BDD roundtrip."""
        bdd_content = """Feature: Requirement Preservation
  Scenario: First requirement
    Given first precondition
    When first action
    Then first result

  Scenario: Second requirement
    Given second precondition
    When second action
    Then second result"""

        # Parse to IR
        parse_response = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": bdd_content, "source_format": "BDD"},
        )
        assert parse_response.status_code == 200
        ir_data = parse_response.json()
        original_req_count = len(ir_data["requirements"])
        assert original_req_count >= 2

        # Convert to OpenSpec and back
        convert_response = await client.post(
            "/api/v1/spec-converter/convert",
            json={
                "content": bdd_content,
                "source_format": "BDD",
                "target_format": "OPENSPEC",
            },
        )
        openspec = convert_response.json()["content"]

        # Parse OpenSpec
        parse_back = await client.post(
            "/api/v1/spec-converter/parse",
            json={"content": openspec, "source_format": "OPENSPEC"},
        )
        ir_back = parse_back.json()

        # Verify requirement count preserved
        assert len(ir_back["requirements"]) >= original_req_count
