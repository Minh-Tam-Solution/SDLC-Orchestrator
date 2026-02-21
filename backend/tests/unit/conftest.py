"""
Conftest for unit tests at tests/unit/ level.

Overrides the root conftest autouse fixtures that interfere with
ASGITransport-based route tests.

Sprint 185 — Audit Trail unit test support
"""

import pytest


@pytest.fixture(autouse=True)
def mock_external_http():
    """
    Override the root conftest mock_external_http for all tests/unit/ tests.

    The root conftest patches httpx.AsyncClient.request to intercept external
    HTTP calls (OPA, MinIO, etc.). However, when unit tests use ASGITransport,
    the URL passed to request() is the raw path (e.g. '/api/v1/enterprise/audit')
    without the 'testserver' hostname prefix. The root fixture's check
    ``if "testserver" in url_str`` therefore fails to pass through the request,
    and the mock returns {"result": True, "allow": True} for ALL requests.

    By overriding this fixture here with an autouse no-op, unit tests that use
    ASGITransport (which calls the ASGI app directly, never making real network
    connections) are not affected by the external HTTP mock.

    Note: If a specific test needs to mock external HTTP calls made FROM within
    the route handler (e.g. OPA calls), it should use patch.object() directly.
    """
    yield
