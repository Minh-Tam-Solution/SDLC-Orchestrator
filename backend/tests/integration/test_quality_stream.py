"""
Quality Stream API Integration Tests.

Sprint 56: Backend Integration for Quality Pipeline
Tests for GET /api/v1/codegen/sessions/{session_id}/quality/stream endpoint.

Test Coverage:
- SSE streaming connection
- Quality event types (quality_started, quality_gate, quality_issue, quality_completed)
- Authentication requirements
- Session validation
- Error handling

Author: Backend Lead
Date: December 26, 2025
Status: ACTIVE
"""

import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_requires_auth(client: AsyncClient):
    """Test GET /sessions/{session_id}/quality/stream requires authentication."""
    session_id = str(uuid4())
    response = await client.get(f"/api/v1/codegen/sessions/{session_id}/quality/stream")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_quality_stream_invalid_session_format(
    client: AsyncClient,
    auth_headers: dict
):
    """Test quality stream returns 400 for invalid session ID format."""
    response = await client.get(
        "/api/v1/codegen/sessions/invalid-uuid-format/quality/stream",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "Invalid session ID format" in response.json()["detail"]


# ============================================================================
# Session Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_session_not_found(
    client: AsyncClient,
    auth_headers: dict
):
    """Test quality stream returns error event for non-existent session."""
    session_id = str(uuid4())

    # Mock Redis/SessionManager
    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = None

            response = await client.get(
                f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Parse SSE event
            content = response.text
            assert "Session not found" in content


@pytest.mark.asyncio
async def test_quality_stream_unauthorized_session(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream returns error for session owned by different user."""
    session_id = str(uuid4())

    # Create mock session state owned by different user
    mock_session = MagicMock()
    mock_session.user_id = uuid4()  # Different user ID

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            response = await client.get(
                f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                headers=auth_headers
            )

            assert response.status_code == 200
            content = response.text
            assert "Not authorized" in content


# ============================================================================
# SSE Event Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_sends_started_event(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream sends quality_started event."""
    session_id = str(uuid4())

    # Create mock session state
    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = []  # Empty files

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Check for quality_started event
                assert '"type": "quality_started"' in content or "'type': 'quality_started'" in content


@pytest.mark.asyncio
async def test_quality_stream_sends_gate_events(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream sends quality_gate events for all 4 gates."""
    session_id = str(uuid4())

    # Create mock session state with files
    mock_file = MagicMock()
    mock_file.path = "test.py"
    mock_file.content = "print('hello')"

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = [mock_file]

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Check for all 4 gates
                assert "Syntax" in content
                assert "Security" in content
                assert "Context" in content
                assert "Tests" in content


@pytest.mark.asyncio
async def test_quality_stream_sends_completed_event(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream sends quality_completed event at the end."""
    session_id = str(uuid4())

    # Create mock session state
    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = []

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Check for quality_completed event
                assert '"type": "quality_completed"' in content or "'type': 'quality_completed'" in content


# ============================================================================
# Syntax Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_detects_syntax_error(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream detects Python syntax errors."""
    session_id = str(uuid4())

    # Create mock session with invalid Python syntax
    mock_file = MagicMock()
    mock_file.path = "bad_syntax.py"
    mock_file.content = "def invalid syntax {}"  # Invalid Python

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = [mock_file]

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Should have quality_issue event for syntax error
                assert "quality_issue" in content or "failed" in content


@pytest.mark.asyncio
async def test_quality_stream_valid_python_passes_syntax(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream passes valid Python through syntax gate."""
    session_id = str(uuid4())

    # Create mock session with valid Python
    mock_file = MagicMock()
    mock_file.path = "valid.py"
    mock_file.content = """
def hello_world():
    print('Hello, World!')

if __name__ == '__main__':
    hello_world()
"""

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = [mock_file]

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Should pass syntax gate
                assert "passed" in content


# ============================================================================
# Headers Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_correct_headers(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream returns correct SSE headers."""
    session_id = str(uuid4())

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = []

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200

                # Check SSE headers
                content_type = response.headers.get("content-type", "")
                assert "text/event-stream" in content_type

                cache_control = response.headers.get("cache-control", "")
                assert "no-cache" in cache_control


# ============================================================================
# Empty Session Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_empty_files_skips_gates(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream skips gates when no files are present."""
    session_id = str(uuid4())

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = []  # No files

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Should have skipped gates
                assert "skipped" in content


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_handles_pipeline_error(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream handles pipeline errors gracefully."""
    session_id = str(uuid4())

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = [MagicMock(path="test.py", content="x")]

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.side_effect = Exception("Pipeline error")

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # Should have error event
                assert "error" in content


# ============================================================================
# Event Format Tests
# ============================================================================


@pytest.mark.asyncio
async def test_quality_stream_event_format(
    client: AsyncClient,
    auth_headers: dict,
    test_user
):
    """Test quality stream events are properly formatted as SSE."""
    session_id = str(uuid4())

    mock_session = MagicMock()
    mock_session.user_id = test_user.id
    mock_session.generated_files = []

    with patch('app.api.routes.codegen.get_redis', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()

        with patch(
            'app.services.codegen.session_manager.SessionManager.get_session',
            new_callable=AsyncMock
        ) as mock_get_session:
            mock_get_session.return_value = mock_session

            with patch(
                'app.services.codegen.quality_pipeline.get_quality_pipeline'
            ) as mock_pipeline:
                mock_pipeline.return_value = MagicMock()

                response = await client.get(
                    f"/api/v1/codegen/sessions/{session_id}/quality/stream",
                    headers=auth_headers
                )

                assert response.status_code == 200
                content = response.text

                # SSE format should have "data: " prefix
                assert "data: " in content

                # Events should be separated by double newlines
                # At minimum we should have started and completed events
                lines = [l for l in content.split('\n') if l.startswith('data: ')]
                assert len(lines) >= 2  # At least started + completed
