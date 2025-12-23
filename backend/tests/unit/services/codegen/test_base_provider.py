"""
Unit tests for CodegenProvider base interface and data models.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests Pydantic models and provider interface contracts.
"""

import pytest
from typing import Dict, Any

from app.services.codegen.base_provider import (
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate,
    CodegenProvider,
)


class TestCodegenSpec:
    """Test CodegenSpec Pydantic model."""

    def test_minimal_spec(self):
        """Test minimal spec with only required fields."""
        spec = CodegenSpec(
            app_blueprint={"name": "TestApp", "modules": []},
            language="python",
            framework="fastapi"
        )

        assert spec.app_blueprint == {"name": "TestApp", "modules": []}
        assert spec.language == "python"
        assert spec.framework == "fastapi"
        assert spec.target_module is None

    def test_full_spec(self):
        """Test spec with all fields."""
        blueprint = {
            "name": "TaskManager",
            "description": "Quản lý công việc",
            "modules": [
                {"name": "tasks", "entities": []}
            ]
        }

        spec = CodegenSpec(
            app_blueprint=blueprint,
            language="python",
            framework="fastapi",
            target_module="tasks"
        )

        assert spec.app_blueprint == blueprint
        assert spec.target_module == "tasks"

    def test_vietnamese_description(self):
        """Test Vietnamese characters in blueprint."""
        blueprint = {
            "name": "QuanLyCongViec",
            "description": "Hệ thống quản lý công việc cho doanh nghiệp SME Việt Nam",
            "modules": []
        }

        spec = CodegenSpec(
            app_blueprint=blueprint,
            language="python",
            framework="fastapi"
        )

        assert "Việt Nam" in spec.app_blueprint["description"]


class TestCodegenResult:
    """Test CodegenResult Pydantic model."""

    def test_minimal_result(self):
        """Test minimal result."""
        result = CodegenResult(
            code="def main(): pass",
            files={},
            metadata={},
            provider="test"
        )

        assert result.code == "def main(): pass"
        assert result.files == {}
        assert result.provider == "test"
        # tokens_used defaults to 0, not None
        assert result.tokens_used == 0
        assert result.generation_time_ms == 0

    def test_full_result(self):
        """Test result with all fields."""
        result = CodegenResult(
            code="# Generated code",
            files={
                "app/main.py": "from fastapi import FastAPI",
                "app/models/task.py": "class Task: pass"
            },
            metadata={
                "model": "qwen2.5-coder:32b",
                "temperature": 0.3
            },
            provider="ollama",
            tokens_used=1500,
            generation_time_ms=3500
        )

        assert len(result.files) == 2
        assert result.tokens_used == 1500
        assert result.generation_time_ms == 3500
        assert result.metadata["model"] == "qwen2.5-coder:32b"

    def test_has_files_with_files(self):
        """Test when files exist."""
        result = CodegenResult(
            code="code",
            files={"app/main.py": "content"},
            metadata={},
            provider="test"
        )

        assert len(result.files) > 0

    def test_has_files_empty_files(self):
        """Test when no files parsed."""
        result = CodegenResult(
            code="code without file markers",
            files={},
            metadata={},
            provider="test"
        )

        assert len(result.files) == 0

    def test_has_code(self):
        """Test code presence."""
        result = CodegenResult(
            code="some code",
            files={},
            metadata={},
            provider="test"
        )

        assert len(result.code) > 0


class TestValidationResult:
    """Test ValidationResult Pydantic model."""

    def test_valid_result(self):
        """Test valid code result."""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_invalid_result(self):
        """Test invalid code result."""
        result = ValidationResult(
            valid=False,
            errors=["Missing type hints", "SQL injection vulnerability"],
            warnings=["Could optimize this loop"],
            suggestions=["Consider using async/await"]
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert "SQL injection" in result.errors[1]

    def test_vietnamese_messages(self):
        """Test Vietnamese error messages."""
        result = ValidationResult(
            valid=False,
            errors=["Thiếu xử lý lỗi cho trường hợp rỗng"],
            warnings=["Nên thêm type hints cho function này"],
            suggestions=["Đề xuất tách thành service riêng"]
        )

        assert "Thiếu" in result.errors[0]
        assert "Nên" in result.warnings[0]


class TestCostEstimate:
    """Test CostEstimate Pydantic model."""

    def test_full_estimate(self):
        """Test full cost estimate with confidence (required field)."""
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

    def test_ollama_cost_efficiency(self):
        """Test Ollama is more cost-efficient."""
        ollama_estimate = CostEstimate(
            estimated_tokens=5000,
            estimated_cost_usd=0.005,
            provider="ollama",
            confidence=0.85
        )

        claude_estimate = CostEstimate(
            estimated_tokens=5000,
            estimated_cost_usd=0.09,
            provider="claude",
            confidence=0.7
        )

        # Ollama should be ~18x cheaper
        assert ollama_estimate.estimated_cost_usd < claude_estimate.estimated_cost_usd
        assert claude_estimate.estimated_cost_usd / ollama_estimate.estimated_cost_usd >= 10


class MockProvider(CodegenProvider):
    """Mock provider for testing interface."""

    def __init__(self, name: str = "mock", available: bool = True):
        self._name = name
        self._available = available

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        return CodegenResult(
            code=f"# Generated by {self._name}",
            files={"app/main.py": "content"},
            metadata={"mock": True},
            provider=self._name
        )

    async def validate(self, code: str, context: Dict[str, Any]) -> ValidationResult:
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )

    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        return CostEstimate(
            estimated_tokens=1000,
            estimated_cost_usd=0.001,
            provider=self._name,
            confidence=0.85
        )


class TestCodegenProviderInterface:
    """Test CodegenProvider abstract interface."""

    def test_provider_name(self):
        """Test provider name property."""
        provider = MockProvider(name="test-provider")
        assert provider.name == "test-provider"

    def test_provider_availability(self):
        """Test provider availability property."""
        available_provider = MockProvider(available=True)
        unavailable_provider = MockProvider(available=False)

        assert available_provider.is_available is True
        assert unavailable_provider.is_available is False

    @pytest.mark.asyncio
    async def test_generate_method(self):
        """Test generate method returns CodegenResult."""
        provider = MockProvider()
        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        result = await provider.generate(spec)

        assert isinstance(result, CodegenResult)
        assert result.provider == "mock"

    @pytest.mark.asyncio
    async def test_validate_method(self):
        """Test validate method returns ValidationResult."""
        provider = MockProvider()

        result = await provider.validate("def foo(): pass", {})

        assert isinstance(result, ValidationResult)

    def test_estimate_cost_method(self):
        """Test estimate_cost method returns CostEstimate."""
        provider = MockProvider()
        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        estimate = provider.estimate_cost(spec)

        assert isinstance(estimate, CostEstimate)
        assert estimate.provider == "mock"
