"""
Conftest for unit service tests.
Sprint 154 - Override fixtures for service-level tests.
"""

import pytest


@pytest.fixture(autouse=False)
def mock_external_http(monkeypatch):
    """
    Override parent's mock_external_http to allow ASGITransport.

    This fixture is NOT autouse so it doesn't interfere with
    httpx.ASGITransport calls used for API testing.
    """
    pass
