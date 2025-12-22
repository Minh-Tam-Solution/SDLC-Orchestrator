"""
Test Policy Guard Validator

SDLC Stage: 05 - TEST
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1

Purpose:
Unit tests for PolicyGuardValidator.
Tests policy evaluation, input preparation, and result aggregation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.validators.policy_guard_validator import PolicyGuardValidator
from app.services.validators import ValidatorConfig, ValidatorStatus
from app.schemas.policy_pack import PolicyResult, PolicyRuleCreate, PolicySeverity


class TestPolicyGuardValidator:
    """Test cases for PolicyGuardValidator."""

    @pytest.fixture
    def mock_opa_service(self):
        """Create mock OPA service."""
        service = AsyncMock()
        service.health_check.return_value = True
        return service

    @pytest.fixture
    def mock_policy_pack_service(self):
        """Create mock PolicyPackService."""
        service = AsyncMock()
        return service

    @pytest.fixture
    def validator(self, mock_opa_service, mock_policy_pack_service):
        """Create validator with mocked services."""
        validator = PolicyGuardValidator()
        validator._opa_service = mock_opa_service
        validator._policy_pack_service = mock_policy_pack_service
        return validator

    @pytest.fixture
    def sample_policy(self):
        """Create sample policy for testing."""
        return PolicyRuleCreate(
            policy_id="no-hardcoded-secrets",
            name="No Hardcoded Secrets",
            description="Detect hardcoded secrets in code",
            rego_policy="""
                package ai_safety.no_hardcoded_secrets
                default allow = true
                allow = false { input.test == "fail" }
            """,
            severity=PolicySeverity.CRITICAL,
            blocking=True,
            enabled=True,
            message_template="Secret detected in {file}",
            tags=["security"],
        )

    @pytest.fixture
    def sample_policy_pack(self, sample_policy):
        """Create sample policy pack."""
        pack = MagicMock()
        pack.id = uuid4()
        pack.project_id = uuid4()
        pack.name = "Test Pack"
        pack.validators = [{"name": "policy_guards", "enabled": True}]
        pack.policies = [sample_policy]
        pack.forbidden_imports = ["minio"]
        pack.required_patterns = []
        pack.coverage_threshold = 80
        return pack

    # =========================================================================
    # Test: No Policy Pack
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_no_policy_pack(self, validator, mock_policy_pack_service):
        """Test validation when project has no policy pack."""
        mock_policy_pack_service.get_by_project.return_value = None

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/main.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.SKIPPED
        assert "No policy pack" in result.message
        assert result.blocking is False

    # =========================================================================
    # Test: Validator Disabled
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_validator_disabled(
        self, validator, mock_policy_pack_service, sample_policy_pack
    ):
        """Test validation when policy_guards is disabled."""
        sample_policy_pack.validators = [
            {"name": "policy_guards", "enabled": False}
        ]
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/main.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.SKIPPED
        assert "disabled" in result.message.lower()

    # =========================================================================
    # Test: No Policies
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_no_policies(
        self, validator, mock_policy_pack_service, sample_policy_pack
    ):
        """Test validation when pack has no policies."""
        sample_policy_pack.policies = []
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/main.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.SKIPPED
        assert "No policies" in result.message

    # =========================================================================
    # Test: All Policies Pass
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_all_pass(
        self,
        validator,
        mock_opa_service,
        mock_policy_pack_service,
        sample_policy_pack,
    ):
        """Test validation when all policies pass."""
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack

        mock_opa_service.evaluate_policies.return_value = [
            PolicyResult(
                policy_id="no-hardcoded-secrets",
                policy_name="No Hardcoded Secrets",
                passed=True,
                severity=PolicySeverity.CRITICAL,
                blocking=True,
                message=None,
                violations=[],
                evaluation_time_ms=50,
            )
        ]

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/main.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.PASSED
        assert "All" in result.message and "passed" in result.message
        assert result.blocking is False
        assert result.details["passed_count"] == 1
        assert result.details["failed_count"] == 0

    # =========================================================================
    # Test: Blocking Failure
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_blocking_failure(
        self,
        validator,
        mock_opa_service,
        mock_policy_pack_service,
        sample_policy_pack,
    ):
        """Test validation when a blocking policy fails."""
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack

        mock_opa_service.evaluate_policies.return_value = [
            PolicyResult(
                policy_id="no-hardcoded-secrets",
                policy_name="No Hardcoded Secrets",
                passed=False,
                severity=PolicySeverity.CRITICAL,
                blocking=True,
                message="Secret detected in app/config.py",
                violations=[
                    {"file": "app/config.py", "line": 10, "message": "hardcoded secret"}
                ],
                evaluation_time_ms=50,
            )
        ]

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/config.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.FAILED
        assert "blocking" in result.message.lower()
        assert result.blocking is True
        assert result.details["blocking_count"] == 1
        assert "blocking_violations" in result.details

    # =========================================================================
    # Test: Non-Blocking Warning
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_non_blocking_warning(
        self,
        validator,
        mock_opa_service,
        mock_policy_pack_service,
        sample_policy_pack,
    ):
        """Test validation when a non-blocking policy fails (warning)."""
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack

        mock_opa_service.evaluate_policies.return_value = [
            PolicyResult(
                policy_id="code-style",
                policy_name="Code Style",
                passed=False,
                severity=PolicySeverity.LOW,
                blocking=False,
                message="Code style issue",
                violations=[],
                evaluation_time_ms=20,
            )
        ]

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/main.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.PASSED
        assert "warning" in result.message.lower()
        assert result.blocking is False
        assert result.details["warning_count"] == 1

    # =========================================================================
    # Test: Mixed Results
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_mixed_results(
        self,
        validator,
        mock_opa_service,
        mock_policy_pack_service,
        sample_policy_pack,
    ):
        """Test validation with mixed pass/fail results."""
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack

        mock_opa_service.evaluate_policies.return_value = [
            PolicyResult(
                policy_id="no-hardcoded-secrets",
                policy_name="No Hardcoded Secrets",
                passed=True,
                severity=PolicySeverity.CRITICAL,
                blocking=True,
                message=None,
                violations=[],
                evaluation_time_ms=50,
            ),
            PolicyResult(
                policy_id="architecture-boundaries",
                policy_name="Architecture Boundaries",
                passed=False,
                severity=PolicySeverity.HIGH,
                blocking=True,
                message="Layer violation",
                violations=[{"file": "app/api/routes.py", "message": "Direct DB access"}],
                evaluation_time_ms=30,
            ),
            PolicyResult(
                policy_id="code-style",
                policy_name="Code Style",
                passed=False,
                severity=PolicySeverity.LOW,
                blocking=False,
                message="Minor style issue",
                violations=[],
                evaluation_time_ms=10,
            ),
        ]

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/api/routes.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.FAILED
        assert result.blocking is True
        assert result.details["passed_count"] == 1
        assert result.details["failed_count"] == 2
        assert result.details["blocking_count"] == 1
        assert result.details["warning_count"] == 1

    # =========================================================================
    # Test: Error Handling
    # =========================================================================

    @pytest.mark.asyncio
    async def test_validate_error_handling(
        self,
        validator,
        mock_opa_service,
        mock_policy_pack_service,
        sample_policy_pack,
    ):
        """Test validation handles errors gracefully."""
        mock_policy_pack_service.get_by_project.return_value = sample_policy_pack
        mock_opa_service.evaluate_policies.side_effect = Exception("OPA connection failed")

        result = await validator.validate(
            project_id=uuid4(),
            pr_number="123",
            files=["app/main.py"],
            diff="",
        )

        assert result.status == ValidatorStatus.ERROR
        assert "error" in result.message.lower()
        assert result.blocking is False  # Fail open

    # =========================================================================
    # Test: Language Detection
    # =========================================================================

    def test_detect_language(self, validator):
        """Test programming language detection from file path."""
        assert validator._detect_language("app/main.py") == "python"
        assert validator._detect_language("src/index.ts") == "typescript"
        assert validator._detect_language("lib/utils.js") == "javascript"
        assert validator._detect_language("cmd/main.go") == "go"
        assert validator._detect_language("src/main.rs") == "rust"
        assert validator._detect_language("README.md") == "unknown"

    # =========================================================================
    # Test: Layer Detection
    # =========================================================================

    def test_detect_layer(self, validator):
        """Test architectural layer detection from file path."""
        assert validator._detect_layer("app/api/routes/users.py") == "presentation"
        assert validator._detect_layer("app/services/user_service.py") == "business"
        assert validator._detect_layer("app/repositories/user_repo.py") == "data"
        assert validator._detect_layer("app/schemas/user.py") == "domain"
        assert validator._detect_layer("app/utils/helpers.py") == "unknown"

    # =========================================================================
    # Test: Import Extraction
    # =========================================================================

    def test_extract_imports_python(self, validator):
        """Test Python import extraction."""
        content = """
import os
import sys
from fastapi import FastAPI
from app.services import UserService
"""
        imports = validator._extract_imports(content, "python")

        assert "os" in imports
        assert "sys" in imports
        assert "fastapi" in imports
        assert "app.services" in imports

    def test_extract_imports_typescript(self, validator):
        """Test TypeScript import extraction."""
        content = """
import React from 'react';
import { useState } from 'react';
const axios = require('axios');
"""
        imports = validator._extract_imports(content, "typescript")

        assert "react" in imports
        assert "axios" in imports

    # =========================================================================
    # Test: Validator Config
    # =========================================================================

    def test_validator_name(self, validator):
        """Test validator name."""
        assert validator.name == "policy_guards"

    def test_default_blocking(self, validator):
        """Test default blocking behavior."""
        assert validator.default_blocking is True

    def test_default_timeout(self, validator):
        """Test default timeout."""
        assert validator.default_timeout_seconds == 30
