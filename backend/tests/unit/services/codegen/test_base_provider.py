"""
Unit tests for CodegenProvider base classes.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests for base_provider.py models and abstract interface.

Author: Backend Lead
Date: December 23, 2025
"""

import pytest
from typing import Dict, Any

from app.services.codegen.base_provider import (
    CodegenProvider,
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate
)


class TestCodegenSpec:
    """Tests for CodegenSpec model."""

    def test_default_values(self):
        """Test default values are applied."""
        spec = CodegenSpec(
            app_blueprint={"name": "TestApp"}
        )
        assert spec.language == "python"
        assert spec.framework == "fastapi"
        assert spec.target_module is None
        assert spec.options == {}

    def test_custom_values(self):
        """Test custom values are preserved."""
        spec = CodegenSpec(
            app_blueprint={"name": "TestApp", "modules": []},
            target_module="users",
            language="typescript",
            framework="nextjs",
            options={"typescript_strict": True}
        )
        assert spec.language == "typescript"
        assert spec.framework == "nextjs"
        assert spec.target_module == "users"
        assert spec.options == {"typescript_strict": True}

    def test_complex_blueprint(self):
        """Test with complex app blueprint."""
        blueprint = {
            "name": "TaskManager",
            "description": "Quản lý công việc",
            "modules": [
                {
                    "name": "tasks",
                    "entities": [
                        {
                            "name": "Task",
                            "fields": [
                                {"name": "id", "type": "uuid"},
                                {"name": "title", "type": "string"}
                            ]
                        }
                    ]
                }
            ]
        }
        spec = CodegenSpec(app_blueprint=blueprint)
        assert spec.app_blueprint["name"] == "TaskManager"
        assert len(spec.app_blueprint["modules"]) == 1

    def test_model_json_schema(self):
        """Test model has valid JSON schema."""
        schema = CodegenSpec.model_json_schema()
        assert "properties" in schema
        assert "app_blueprint" in schema["properties"]
        assert "language" in schema["properties"]


class TestCodegenResult:
    """Tests for CodegenResult model."""

    def test_minimal_result(self):
        """Test result with minimal fields."""
        result = CodegenResult(
            code="print('hello')",
            provider="ollama"
        )
        assert result.code == "print('hello')"
        assert result.provider == "ollama"
        assert result.files == {}
        assert result.metadata == {}
        assert result.tokens_used == 0
        assert result.generation_time_ms == 0

    def test_full_result(self):
        """Test result with all fields."""
        result = CodegenResult(
            code="# Full code output",
            files={
                "app/main.py": "from fastapi import FastAPI",
                "app/models.py": "from sqlalchemy import Column"
            },
            metadata={
                "model": "qwen2.5-coder:32b",
                "temperature": 0.3
            },
            provider="ollama",
            tokens_used=1500,
            generation_time_ms=2500
        )
        assert len(result.files) == 2
        assert "app/main.py" in result.files
        assert result.tokens_used == 1500
        assert result.generation_time_ms == 2500

    def test_tokens_validation(self):
        """Test tokens_used must be >= 0."""
        with pytest.raises(ValueError):
            CodegenResult(
                code="test",
                provider="ollama",
                tokens_used=-1
            )

    def test_time_validation(self):
        """Test generation_time_ms must be >= 0."""
        with pytest.raises(ValueError):
            CodegenResult(
                code="test",
                provider="ollama",
                generation_time_ms=-100
            )


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_result(self):
        """Test valid code result."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.suggestions == []

    def test_invalid_result_with_errors(self):
        """Test invalid code with errors."""
        result = ValidationResult(
            valid=False,
            errors=["Missing import", "Syntax error line 5"],
            warnings=["Function too long"],
            suggestions=["Add type hints"]
        )
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1

    def test_vietnamese_messages(self):
        """Test Vietnamese error messages."""
        result = ValidationResult(
            valid=False,
            errors=["Thiếu import cần thiết"],
            warnings=["Hàm quá dài (>50 dòng)"],
            suggestions=["Nên thêm type hints"]
        )
        assert "Thiếu import" in result.errors[0]


class TestCostEstimate:
    """Tests for CostEstimate model."""

    def test_ollama_estimate(self):
        """Test Ollama (cheap) estimate."""
        estimate = CostEstimate(
            estimated_tokens=5000,
            estimated_cost_usd=0.005,
            provider="ollama",
            confidence=0.85
        )
        assert estimate.estimated_tokens == 5000
        assert estimate.estimated_cost_usd == 0.005
        assert estimate.provider == "ollama"
        assert estimate.confidence == 0.85

    def test_claude_estimate(self):
        """Test Claude (expensive) estimate."""
        estimate = CostEstimate(
            estimated_tokens=5000,
            estimated_cost_usd=0.09,  # ~$18/1M tokens average
            provider="claude",
            confidence=0.7
        )
        assert estimate.estimated_cost_usd > 0.005  # More expensive

    def test_confidence_bounds(self):
        """Test confidence must be 0-1."""
        # Valid
        CostEstimate(
            estimated_tokens=100,
            estimated_cost_usd=0.01,
            provider="test",
            confidence=0.0
        )
        CostEstimate(
            estimated_tokens=100,
            estimated_cost_usd=0.01,
            provider="test",
            confidence=1.0
        )

        # Invalid
        with pytest.raises(ValueError):
            CostEstimate(
                estimated_tokens=100,
                estimated_cost_usd=0.01,
                provider="test",
                confidence=1.5
            )
        with pytest.raises(ValueError):
            CostEstimate(
                estimated_tokens=100,
                estimated_cost_usd=0.01,
                provider="test",
                confidence=-0.1
            )

    def test_tokens_must_be_positive(self):
        """Test estimated_tokens must be >= 0."""
        with pytest.raises(ValueError):
            CostEstimate(
                estimated_tokens=-100,
                estimated_cost_usd=0.01,
                provider="test",
                confidence=0.5
            )


class TestCodegenProviderInterface:
    """Tests for CodegenProvider abstract interface."""

    def test_cannot_instantiate_abstract(self):
        """Test cannot instantiate abstract class."""
        with pytest.raises(TypeError):
            CodegenProvider()

    def test_concrete_implementation(self):
        """Test concrete implementation works."""

        class MockProvider(CodegenProvider):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def is_available(self) -> bool:
                return True

            async def generate(self, spec: CodegenSpec) -> CodegenResult:
                return CodegenResult(
                    code="# mock",
                    provider="mock"
                )

            async def validate(
                self, code: str, context: Dict[str, Any]
            ) -> ValidationResult:
                return ValidationResult(valid=True)

            def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
                return CostEstimate(
                    estimated_tokens=100,
                    estimated_cost_usd=0.001,
                    provider="mock",
                    confidence=0.9
                )

        provider = MockProvider()
        assert provider.name == "mock"
        assert provider.is_available is True
        assert "mock" in repr(provider)
        assert "available" in repr(provider)

    def test_repr_unavailable(self):
        """Test repr shows unavailable status."""

        class UnavailableProvider(CodegenProvider):
            @property
            def name(self) -> str:
                return "down"

            @property
            def is_available(self) -> bool:
                return False

            async def generate(self, spec: CodegenSpec) -> CodegenResult:
                raise NotImplementedError

            async def validate(
                self, code: str, context: Dict[str, Any]
            ) -> ValidationResult:
                raise NotImplementedError

            def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
                raise NotImplementedError

        provider = UnavailableProvider()
        assert "unavailable" in repr(provider)
