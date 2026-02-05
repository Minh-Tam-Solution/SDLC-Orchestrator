"""
Conftest for Unit API Tests
Sprint 154 - Spec Converter

Provides fixtures for API route unit tests using ASGITransport.
These tests hit the actual FastAPI app directly, not through HTTP.
"""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_external_http():
    """
    Override the root conftest mock_external_http.

    API unit tests use ASGITransport which doesn't go through
    the standard HTTP stack. No mocking needed.
    """
    # Do nothing - just yield to override the parent fixture
    yield


@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for API testing using ASGITransport.

    This bypasses the external HTTP mock since ASGITransport
    calls the ASGI app directly.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
