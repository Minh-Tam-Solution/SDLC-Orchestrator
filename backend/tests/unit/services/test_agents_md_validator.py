"""
=========================================================================
Unit Tests - AgentsMdValidator
SDLC Orchestrator - Sprint 80 (AGENTS.md Integration)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 80 Implementation
Authority: QA Lead + Backend Lead Approved
Reference: TDS-080-001 AGENTS.md Technical Design

Purpose:
- Test secret detection patterns
- Test line limit enforcement
- Test section validation
- Test lint functionality

Coverage Target: 95%+
=========================================================================
"""

import pytest
from app.services.agents_md_validator import (
    AgentsMdValidator,
    ValidationResult,
    ValidationError,
)


class TestSecretDetection:
    """Test secret detection patterns."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return AgentsMdValidator()

    def test_detect_openai_api_key(self, validator):
        """Test OpenAI API key detection."""
        content = """
# AGENTS.md
Use this key: sk-abc123def456ghi789jkl012mno345pqr678stu901
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("OpenAI" in e.message for e in result.errors)

    def test_detect_github_pat(self, validator):
        """Test GitHub PAT detection."""
        content = """
# AGENTS.md
Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("GitHub" in e.message for e in result.errors)

    def test_detect_github_oauth(self, validator):
        """Test GitHub OAuth token detection."""
        content = """
# AGENTS.md
OAuth: gho_1234567890abcdefghijklmnopqrstuvwxyz
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("GitHub" in e.message for e in result.errors)

    def test_detect_aws_access_key(self, validator):
        """Test AWS access key detection."""
        content = """
# AGENTS.md
AWS Key: AKIAIOSFODNN7EXAMPLE
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("AWS" in e.message for e in result.errors)

    def test_detect_aws_secret_key(self, validator):
        """Test AWS secret key detection."""
        content = """
# AGENTS.md
Secret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("AWS" in e.message for e in result.errors)

    def test_detect_stripe_key(self, validator):
        """Test Stripe key detection."""
        content = """
# AGENTS.md
Stripe: sk_live_1234567890abcdefghijklmn
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("Stripe" in e.message for e in result.errors)

    def test_detect_slack_token(self, validator):
        """Test Slack token detection."""
        content = """
# AGENTS.md
Slack: xoxb-123456789012-123456789012-abcdefghijklmnopqrstuvwx
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("Slack" in e.message for e in result.errors)

    def test_detect_anthropic_key(self, validator):
        """Test Anthropic API key detection."""
        content = """
# AGENTS.md
API: sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("Anthropic" in e.message for e in result.errors)

    def test_detect_password_in_url(self, validator):
        """Test password detection in URL."""
        content = """
# AGENTS.md
Database: postgresql://user:password123@localhost:5432/db
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("credentials" in e.message.lower() for e in result.errors)

    def test_detect_jwt_token(self, validator):
        """Test JWT token detection."""
        content = """
# AGENTS.md
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w
"""
        result = validator.validate(content)
        assert not result.valid
        assert any("JWT" in e.message for e in result.errors)

    def test_clean_content_passes(self, validator):
        """Test that clean content passes validation."""
        content = """
# AGENTS.md - My Project

## Quick Start
- Run: `docker compose up -d`

## Architecture
- Backend: Python FastAPI
- Frontend: React TypeScript

## Security
- Use environment variables for secrets
- Never commit API keys

## DO NOT
- Add mocks or placeholders
"""
        result = validator.validate(content)
        assert result.valid
        assert len(result.errors) == 0


class TestLineLimitEnforcement:
    """Test line limit enforcement."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return AgentsMdValidator()

    def test_under_recommended_limit(self, validator):
        """Test content under recommended 150 lines."""
        content = "\n".join([f"Line {i}" for i in range(100)])
        result = validator.validate(content)
        assert result.valid
        assert len(result.warnings) == 0

    def test_at_recommended_limit(self, validator):
        """Test content at recommended 150 lines."""
        content = "\n".join([f"Line {i}" for i in range(150)])
        result = validator.validate(content)
        assert result.valid
        assert len(result.warnings) == 0

    def test_over_recommended_under_max(self, validator):
        """Test content over 150 but under 200 lines."""
        content = "\n".join([f"Line {i}" for i in range(175)])
        result = validator.validate(content)
        assert result.valid  # Still valid but warning
        assert any("over recommended" in w.message.lower() for w in result.warnings)

    def test_at_max_limit(self, validator):
        """Test content at max 200 lines."""
        content = "\n".join([f"Line {i}" for i in range(200)])
        result = validator.validate(content)
        # At 200 should still be valid
        assert result.valid

    def test_over_max_limit(self, validator):
        """Test content over max 200 lines."""
        content = "\n".join([f"Line {i}" for i in range(250)])
        result = validator.validate(content)
        assert not result.valid
        assert any("exceeds maximum" in e.message.lower() for e in result.errors)


class TestSectionValidation:
    """Test section structure validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return AgentsMdValidator()

    def test_missing_header(self, validator):
        """Test content without main header."""
        content = """
Just some content without a header.
"""
        result = validator.validate(content)
        assert any("header" in w.message.lower() or "missing" in w.message.lower() for w in result.warnings)

    def test_valid_structure(self, validator):
        """Test valid AGENTS.md structure."""
        content = """# AGENTS.md - Test Project

## Quick Start
- `docker compose up`

## Architecture
- Python backend

## DO NOT
- Add mocks
"""
        result = validator.validate(content)
        assert result.valid

    def test_empty_content(self, validator):
        """Test empty content."""
        content = ""
        result = validator.validate(content)
        # Empty should generate warning
        assert len(result.warnings) > 0 or not result.valid


class TestLintFunctionality:
    """Test lint and auto-fix functionality."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return AgentsMdValidator()

    def test_lint_trailing_whitespace(self, validator):
        """Test lint removes trailing whitespace."""
        content = "# AGENTS.md   \n\nSome content  \n"
        fixed, changes = validator.lint(content)
        assert "  " not in fixed.split("\n")[0]
        assert any("whitespace" in c.lower() for c in changes)

    def test_lint_multiple_blank_lines(self, validator):
        """Test lint removes multiple consecutive blank lines."""
        content = "# AGENTS.md\n\n\n\nContent"
        fixed, changes = validator.lint(content)
        assert "\n\n\n" not in fixed
        assert any("blank" in c.lower() for c in changes)

    def test_lint_no_changes_needed(self, validator):
        """Test lint with clean content."""
        content = """# AGENTS.md

## Quick Start
- Run tests

## DO NOT
- Add mocks
"""
        fixed, changes = validator.lint(content)
        # Should have minimal or no changes
        assert len(changes) <= 1  # Maybe just trailing whitespace


class TestValidationResult:
    """Test ValidationResult model."""

    def test_valid_result(self):
        """Test valid result creation."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
        )
        assert result.valid
        assert len(result.errors) == 0

    def test_invalid_result(self):
        """Test invalid result creation."""
        error = ValidationError(
            code="SECRET_DETECTED",
            message="API key found",
            line=5,
            severity="error",
        )
        result = ValidationResult(
            valid=False,
            errors=[error],
            warnings=[],
        )
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].code == "SECRET_DETECTED"


class TestCustomPatterns:
    """Test custom validation patterns."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return AgentsMdValidator()

    def test_detect_localhost_with_port(self, validator):
        """Test that localhost URLs don't trigger false positives."""
        content = """
# AGENTS.md

## Quick Start
- API: http://localhost:8000/api
- Frontend: http://localhost:3000
"""
        result = validator.validate(content)
        # Localhost URLs should be OK
        assert result.valid

    def test_example_tokens_ok(self, validator):
        """Test that example/placeholder tokens don't trigger."""
        content = """
# AGENTS.md

## Environment
- Set `OPENAI_API_KEY=your_key_here`
- Set `API_TOKEN=<your-token>`
"""
        result = validator.validate(content)
        # Example placeholders should be OK
        assert result.valid

    def test_base64_image_ok(self, validator):
        """Test that base64 images don't trigger JWT detection."""
        content = """
# AGENTS.md

![Logo](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)
"""
        result = validator.validate(content)
        # Base64 images should not trigger JWT detection
        assert result.valid
