"""
Unit tests for OllamaCodegenProvider.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests Ollama integration with Vietnamese prompts.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.codegen.base_provider import CodegenSpec, CodegenResult, ValidationResult, CostEstimate
from app.services.codegen.ollama_provider import OllamaCodegenProvider


class TestOllamaProviderInit:
    """Test OllamaCodegenProvider initialization."""

    def test_default_init(self):
        """Test initialization with defaults."""
        with patch.object(OllamaCodegenProvider, '_check_availability', return_value=False):
            provider = OllamaCodegenProvider()

        assert provider.name == "ollama"
        assert provider.timeout is not None

    def test_custom_init(self):
        """Test initialization with custom values."""
        provider = OllamaCodegenProvider(
            base_url="http://localhost:11434",
            model="qwen2.5:7b",
            timeout=60
        )

        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "qwen2.5:7b"
        assert provider.timeout == 60


class TestOllamaAvailability:
    """Test availability checking."""

    def test_availability_cached(self):
        """Test availability is cached within TTL."""
        provider = OllamaCodegenProvider()
        provider._available = True
        provider._last_health_check = 9999999999  # Far future

        assert provider.is_available is True

    def test_availability_rechecked_after_ttl(self):
        """Test availability is rechecked after TTL expires."""
        provider = OllamaCodegenProvider()
        provider._available = True
        provider._last_health_check = 0  # Past

        with patch.object(provider, '_check_availability', return_value=False) as mock:
            result = provider.is_available

        mock.assert_called_once()
        assert result is False

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        provider = OllamaCodegenProvider()
        provider._available = True
        provider._last_health_check = 9999999999

        provider.invalidate_cache()

        assert provider._available is None
        assert provider._last_health_check == 0


class TestPromptGeneration:
    """Test prompt generation."""

    def test_build_generation_prompt_fastapi(self):
        """Test FastAPI prompt generation uses template."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={
                "name": "TestApp",
                "description": "Ứng dụng test",
                "modules": []
            },
            language="python",
            framework="fastapi"
        )

        prompt = provider._build_generation_prompt(spec)

        # Should use FastAPI template
        assert "FastAPI" in prompt or "fastapi" in prompt.lower()
        assert "TestApp" in prompt

    def test_build_generation_prompt_generic(self):
        """Test generic prompt for unsupported framework."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={
                "name": "TestApp",
                "description": "Test app",
                "modules": []
            },
            language="python",
            framework="django"  # Not in template registry
        )

        prompt = provider._build_generation_prompt(spec)

        # Should use generic prompt
        assert "TestApp" in prompt
        assert "django" in prompt.lower()

    def test_build_generation_prompt_vietnamese(self):
        """Test Vietnamese content in prompts."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={
                "name": "QuanLyCongViec",
                "description": "Hệ thống quản lý công việc cho SME Việt Nam",
                "modules": [
                    {"name": "tasks", "description": "Quản lý công việc"}
                ]
            },
            language="python",
            framework="fastapi"
        )

        prompt = provider._build_generation_prompt(spec)

        assert "Việt Nam" in prompt or "quản lý" in prompt.lower()

    def test_build_generation_prompt_target_module(self):
        """Test prompt with target module specified."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={
                "name": "TestApp",
                "modules": [
                    {"name": "users", "entities": []},
                    {"name": "tasks", "entities": []}
                ]
            },
            language="python",
            framework="fastapi",
            target_module="tasks"
        )

        prompt = provider._build_generation_prompt(spec)

        # Should mention target module
        assert "tasks" in prompt.lower()


class TestOutputParsing:
    """Test output parsing."""

    def test_parse_single_file(self):
        """Test parsing single file output."""
        provider = OllamaCodegenProvider()
        output = """### FILE: app/main.py
```python
from fastapi import FastAPI

app = FastAPI()
```
"""

        files = provider._parse_code_output(output)

        assert len(files) == 1
        assert "app/main.py" in files
        assert "FastAPI" in files["app/main.py"]

    def test_parse_multiple_files(self):
        """Test parsing multiple files output."""
        provider = OllamaCodegenProvider()
        output = """### FILE: app/main.py
```python
from fastapi import FastAPI
app = FastAPI()
```

### FILE: app/models/task.py
```python
class Task:
    pass
```

### FILE: app/schemas/task.py
```python
from pydantic import BaseModel

class TaskSchema(BaseModel):
    name: str
```
"""

        files = provider._parse_code_output(output)

        assert len(files) == 3
        assert "app/main.py" in files
        assert "app/models/task.py" in files
        assert "app/schemas/task.py" in files

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        provider = OllamaCodegenProvider()

        files = provider._parse_code_output("")

        assert files == {}

    def test_parse_no_file_markers(self):
        """Test parsing output without file markers."""
        provider = OllamaCodegenProvider()
        output = "Just some text without file markers"

        files = provider._parse_code_output(output)

        assert files == {}

    def test_clean_code_content(self):
        """Test code content cleaning."""
        provider = OllamaCodegenProvider()

        # Test with markdown markers
        content = "```python\ndef foo(): pass\n```"
        cleaned = provider._clean_code_content(content)

        assert "```" not in cleaned
        assert "def foo()" in cleaned


class TestValidationParsing:
    """Test validation output parsing."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON output."""
        provider = OllamaCodegenProvider()
        output = """
        Here's my analysis:
        {"valid": true, "errors": [], "warnings": ["Minor issue"], "suggestions": ["Use async"]}
        """

        result = provider._parse_validation_result(output)

        assert result.valid is True
        assert len(result.warnings) == 1

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON defaults to valid."""
        provider = OllamaCodegenProvider()
        output = "This is not JSON at all"

        result = provider._parse_validation_result(output)

        assert result.valid is True
        assert len(result.warnings) == 1  # Should have parse warning

    def test_parse_validation_errors(self):
        """Test parsing validation errors."""
        provider = OllamaCodegenProvider()
        output = """
        {"valid": false, "errors": ["Lỗi bảo mật SQL injection", "Thiếu type hints"], "warnings": [], "suggestions": []}
        """

        result = provider._parse_validation_result(output)

        assert result.valid is False
        assert len(result.errors) == 2
        assert "SQL injection" in result.errors[0]


class TestCostEstimation:
    """Test cost estimation."""

    def test_estimate_cost_small_blueprint(self):
        """Test cost estimation for small blueprint."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={
                "name": "Small",
                "modules": [{"name": "test", "entities": []}]
            },
            language="python",
            framework="fastapi"
        )

        estimate = provider.estimate_cost(spec)

        assert estimate.provider == "ollama"
        assert estimate.estimated_tokens > 0
        assert estimate.estimated_cost_usd > 0
        assert estimate.confidence == 0.85

    def test_estimate_cost_large_blueprint(self):
        """Test cost estimation for large blueprint."""
        provider = OllamaCodegenProvider()

        # Create larger blueprint
        modules = [
            {
                "name": f"module_{i}",
                "entities": [
                    {"name": f"Entity{i}", "fields": [
                        {"name": "id", "type": "uuid"},
                        {"name": "name", "type": "string"},
                        {"name": "created_at", "type": "datetime"}
                    ]}
                ]
            }
            for i in range(5)
        ]

        spec = CodegenSpec(
            app_blueprint={
                "name": "Large",
                "modules": modules
            },
            language="python",
            framework="fastapi"
        )

        estimate = provider.estimate_cost(spec)

        assert estimate.estimated_tokens > 1000  # Should be larger

    def test_ollama_cost_vs_cloud(self):
        """Test Ollama cost is lower than cloud providers."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        estimate = provider.estimate_cost(spec)

        # Ollama cost should be ~$0.001 per 1K tokens
        cost_per_1k = estimate.estimated_cost_usd / (estimate.estimated_tokens / 1000)
        assert cost_per_1k < 0.01  # Much cheaper than cloud ($0.018+ for Claude)


class TestFileExtensions:
    """Test file extension mapping."""

    def test_python_extension(self):
        """Test Python extension."""
        provider = OllamaCodegenProvider()
        assert provider._get_extension("python") == "py"

    def test_typescript_extension(self):
        """Test TypeScript extension."""
        provider = OllamaCodegenProvider()
        assert provider._get_extension("typescript") == "ts"

    def test_unknown_extension(self):
        """Test unknown language defaults to txt."""
        provider = OllamaCodegenProvider()
        assert provider._get_extension("brainfuck") == "txt"

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        provider = OllamaCodegenProvider()
        assert provider._get_extension("PYTHON") == "py"
        assert provider._get_extension("Python") == "py"


class TestGenerateAsync:
    """Test async generate method."""

    @pytest.mark.asyncio
    async def test_generate_returns_result(self):
        """Test generate returns CodegenResult."""
        provider = OllamaCodegenProvider(
            base_url="http://localhost:11434",
            model="test-model",
            timeout=30
        )

        spec = CodegenSpec(
            app_blueprint={"name": "Test", "modules": []},
            language="python",
            framework="fastapi"
        )

        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "### FILE: app/main.py\n```python\nprint('hello')\n```",
            "prompt_eval_count": 100,
            "eval_count": 50
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await provider.generate(spec)

        assert isinstance(result, CodegenResult)
        assert result.provider == "ollama"
        assert result.tokens_used == 150  # 100 + 50


class TestValidateAsync:
    """Test async validate method."""

    @pytest.mark.asyncio
    async def test_validate_returns_result(self):
        """Test validate returns ValidationResult."""
        provider = OllamaCodegenProvider(
            base_url="http://localhost:11434",
            model="test-model"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"valid": true, "errors": [], "warnings": [], "suggestions": []}'
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await provider.validate("def foo(): pass", {"language": "python"})

        assert isinstance(result, ValidationResult)
        assert result.valid is True
