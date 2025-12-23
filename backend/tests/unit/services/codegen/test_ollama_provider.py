"""
Unit tests for OllamaCodegenProvider.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests for ollama_provider.py functionality.

Author: Backend Lead
Date: December 23, 2025
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
import json

from app.services.codegen.ollama_provider import OllamaCodegenProvider
from app.services.codegen.base_provider import (
    CodegenSpec,
    CodegenResult,
    ValidationResult,
    CostEstimate
)


class TestOllamaProviderProperties:
    """Tests for OllamaProvider properties."""

    def test_name(self):
        """Test provider name is 'ollama'."""
        provider = OllamaCodegenProvider()
        assert provider.name == "ollama"

    def test_custom_config(self):
        """Test custom configuration."""
        provider = OllamaCodegenProvider(
            base_url="http://custom:11434",
            model="qwen2:7b",
            timeout=60
        )
        assert provider.base_url == "http://custom:11434"
        assert provider.model == "qwen2:7b"
        assert provider.timeout == 60


class TestOllamaAvailability:
    """Tests for availability checking."""

    @patch('httpx.Client')
    def test_available_when_api_responds(self, mock_client):
        """Test is_available returns True when API responds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen2.5-coder:32b"}]
        }

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        provider = OllamaCodegenProvider()
        provider._available = None  # Force recheck

        assert provider.is_available is True

    @patch('httpx.Client')
    def test_unavailable_on_connection_error(self, mock_client):
        """Test is_available returns False on connection error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.side_effect = httpx.ConnectError(
            "Connection refused"
        )
        mock_client.return_value = mock_client_instance

        provider = OllamaCodegenProvider()
        provider._available = None

        assert provider.is_available is False

    @patch('httpx.Client')
    def test_unavailable_on_timeout(self, mock_client):
        """Test is_available returns False on timeout."""
        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.side_effect = httpx.TimeoutException(
            "Request timed out"
        )
        mock_client.return_value = mock_client_instance

        provider = OllamaCodegenProvider()
        provider._available = None

        assert provider.is_available is False

    def test_availability_cache(self):
        """Test availability is cached."""
        provider = OllamaCodegenProvider()
        provider._available = True
        provider._last_health_check = 99999999999  # Far future

        # Should use cached value, not make API call
        assert provider.is_available is True

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        provider = OllamaCodegenProvider()
        provider._available = True
        provider._last_health_check = 99999999999

        provider.invalidate_cache()

        assert provider._available is None
        assert provider._last_health_check == 0


class TestOllamaGenerate:
    """Tests for generate method."""

    @pytest.fixture
    def provider(self):
        """Create provider instance."""
        return OllamaCodegenProvider()

    @pytest.fixture
    def spec(self):
        """Create test spec."""
        return CodegenSpec(
            app_blueprint={
                "name": "TestApp",
                "modules": [
                    {
                        "name": "users",
                        "entities": [
                            {"name": "User", "fields": []}
                        ]
                    }
                ]
            }
        )

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_generate_success(self, mock_client, provider, spec):
        """Test successful code generation."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": """### FILE: app/models/user.py
```python
from sqlalchemy import Column, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
```

### FILE: app/schemas/user.py
```python
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: str
```""",
            "prompt_eval_count": 500,
            "eval_count": 300
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        result = await provider.generate(spec)

        assert isinstance(result, CodegenResult)
        assert result.provider == "ollama"
        assert "app/models/user.py" in result.files
        assert "app/schemas/user.py" in result.files
        assert result.tokens_used == 800  # 500 + 300

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_generate_with_vietnamese_prompt(
        self, mock_client, provider, spec
    ):
        """Test prompt contains Vietnamese instructions."""
        captured_request = None

        async def capture_post(*args, **kwargs):
            nonlocal captured_request
            captured_request = kwargs.get('json', {})
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "response": "# code",
                "eval_count": 100
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_instance.post = capture_post
        mock_client.return_value = mock_client_instance

        await provider.generate(spec)

        prompt = captured_request.get("prompt", "")
        assert "Việt Nam" in prompt or "Vietnamese" in prompt.lower() or "SME" in prompt


class TestOllamaValidate:
    """Tests for validate method."""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_validate_valid_code(self, mock_client):
        """Test validation of valid code."""
        provider = OllamaCodegenProvider()

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "response": '{"valid": true, "errors": [], "warnings": [], "suggestions": []}'
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        result = await provider.validate(
            code="def hello(): pass",
            context={"language": "python"}
        )

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.errors == []

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_validate_invalid_code(self, mock_client):
        """Test validation of invalid code."""
        provider = OllamaCodegenProvider()

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "response": '{"valid": false, "errors": ["Missing import"], "warnings": ["Long function"], "suggestions": ["Add docstring"]}'
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        result = await provider.validate(
            code="invalid code here",
            context={}
        )

        assert result.valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_validate_parse_failure_defaults_valid(self, mock_client):
        """Test validation defaults to valid on parse failure."""
        provider = OllamaCodegenProvider()

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "response": "This is not valid JSON at all"
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        result = await provider.validate(code="test", context={})

        assert result.valid is True
        assert len(result.warnings) == 1
        assert "parse" in result.warnings[0].lower()


class TestOllamaEstimateCost:
    """Tests for estimate_cost method."""

    def test_estimate_small_blueprint(self):
        """Test cost estimate for small blueprint."""
        provider = OllamaCodegenProvider()
        spec = CodegenSpec(
            app_blueprint={"name": "Small", "modules": []}
        )

        estimate = provider.estimate_cost(spec)

        assert isinstance(estimate, CostEstimate)
        assert estimate.provider == "ollama"
        assert estimate.estimated_tokens > 0
        assert estimate.estimated_cost_usd < 0.01  # Ollama is cheap
        assert estimate.confidence >= 0.8

    def test_estimate_large_blueprint(self):
        """Test cost estimate scales with blueprint size."""
        provider = OllamaCodegenProvider()

        small_spec = CodegenSpec(
            app_blueprint={"name": "Small"}
        )
        large_spec = CodegenSpec(
            app_blueprint={
                "name": "Large",
                "modules": [{"name": f"mod{i}"} for i in range(100)]
            }
        )

        small_estimate = provider.estimate_cost(small_spec)
        large_estimate = provider.estimate_cost(large_spec)

        assert large_estimate.estimated_tokens > small_estimate.estimated_tokens
        assert large_estimate.estimated_cost_usd > small_estimate.estimated_cost_usd


class TestOllamaCodeParsing:
    """Tests for code output parsing."""

    def test_parse_single_file(self):
        """Test parsing single file output."""
        provider = OllamaCodegenProvider()
        output = """### FILE: app/main.py
```python
from fastapi import FastAPI
app = FastAPI()
```"""

        files = provider._parse_code_output(output)

        assert len(files) == 1
        assert "app/main.py" in files
        assert "FastAPI" in files["app/main.py"]

    def test_parse_multiple_files(self):
        """Test parsing multiple files."""
        provider = OllamaCodegenProvider()
        output = """### FILE: app/models.py
```python
class User:
    pass
```

### FILE: app/schemas.py
```python
class UserSchema:
    pass
```

### FILE: app/routes.py
```python
@router.get("/")
def index():
    pass
```"""

        files = provider._parse_code_output(output)

        assert len(files) == 3
        assert "app/models.py" in files
        assert "app/schemas.py" in files
        assert "app/routes.py" in files

    def test_parse_strips_code_markers(self):
        """Test code block markers are stripped."""
        provider = OllamaCodegenProvider()
        output = """### FILE: test.py
```python
print("hello")
```"""

        files = provider._parse_code_output(output)

        content = files["test.py"]
        assert "```" not in content
        assert 'print("hello")' in content

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        provider = OllamaCodegenProvider()

        files = provider._parse_code_output("")

        assert files == {}

    def test_parse_no_file_markers(self):
        """Test parsing output without file markers."""
        provider = OllamaCodegenProvider()
        output = "Just some random text without file markers"

        files = provider._parse_code_output(output)

        assert files == {}

    def test_clean_code_content(self):
        """Test code content cleaning."""
        provider = OllamaCodegenProvider()

        # Test stripping markers
        assert provider._clean_code_content("```python\ncode\n```") == "code"
        assert provider._clean_code_content("code") == "code"
        assert provider._clean_code_content("  code  ") == "code"
