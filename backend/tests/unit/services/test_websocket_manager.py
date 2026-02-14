"""
=========================================================================
WebSocket Manager Service Tests
SDLC Orchestrator - Sprint 153 (Real-time Notifications)

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 153 Testing
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Test Coverage:
- WebSocket connection management
- Event broadcasting to projects/users
- Message handling (subscribe, unsubscribe, ping)
- Connection lifecycle

Zero Mock Policy: Real service tests with mocked WebSocket connections
=========================================================================
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.websocket_manager import (
    ConnectionInfo,
    WebSocketEvent,
    WebSocketEventType,
    WebSocketManager,
    get_websocket_manager,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def websocket_manager():
    """Create a fresh WebSocket manager for testing."""
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def sample_user_id():
    """Sample user UUID."""
    return uuid4()


@pytest.fixture
def sample_project_id():
    """Sample project UUID."""
    return uuid4()


# =========================================================================
# Test: Connection Management
# =========================================================================


class TestConnectionManagement:
    """Test WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connect_user(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
    ):
        """Test connecting a user."""
        connected = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        assert connected is True
        assert websocket_manager.active_connections == 1
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_projects(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
        sample_project_id: UUID,
    ):
        """Test connecting with project subscriptions."""
        connected = await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
            project_ids=[sample_project_id],
        )

        assert connected is True
        assert sample_user_id in websocket_manager._connections
        assert sample_project_id in websocket_manager._project_subscriptions
        assert sample_user_id in websocket_manager._project_subscriptions[sample_project_id]

    @pytest.mark.asyncio
    async def test_disconnect_user(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
    ):
        """Test disconnecting a user."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        assert websocket_manager.active_connections == 1

        await websocket_manager.disconnect(sample_user_id)

        assert websocket_manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_replace_existing_connection(
        self,
        websocket_manager: WebSocketManager,
        sample_user_id: UUID,
    ):
        """Test that new connection replaces existing one for same user."""
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws1.close = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()
        mock_ws2.close = AsyncMock()

        await websocket_manager.connect(websocket=mock_ws1, user_id=sample_user_id)
        assert websocket_manager.active_connections == 1

        await websocket_manager.connect(websocket=mock_ws2, user_id=sample_user_id)
        assert websocket_manager.active_connections == 1
        mock_ws1.close.assert_called_once()


# =========================================================================
# Test: Project Subscriptions
# =========================================================================


class TestProjectSubscriptions:
    """Test project subscription management."""

    @pytest.mark.asyncio
    async def test_subscribe_to_project(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
        sample_project_id: UUID,
    ):
        """Test subscribing to a project."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        result = await websocket_manager.subscribe_to_project(
            sample_user_id, sample_project_id
        )

        assert result is True
        assert sample_project_id in websocket_manager._connections[sample_user_id].subscribed_projects

    @pytest.mark.asyncio
    async def test_unsubscribe_from_project(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
        sample_project_id: UUID,
    ):
        """Test unsubscribing from a project."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
            project_ids=[sample_project_id],
        )

        result = await websocket_manager.unsubscribe_from_project(
            sample_user_id, sample_project_id
        )

        assert result is True
        assert sample_project_id not in websocket_manager._connections[sample_user_id].subscribed_projects

    @pytest.mark.asyncio
    async def test_subscribe_nonexistent_user(
        self,
        websocket_manager: WebSocketManager,
        sample_user_id: UUID,
        sample_project_id: UUID,
    ):
        """Test subscribing with nonexistent user."""
        result = await websocket_manager.subscribe_to_project(
            sample_user_id, sample_project_id
        )

        assert result is False


# =========================================================================
# Test: Event Broadcasting
# =========================================================================


class TestEventBroadcasting:
    """Test event broadcasting functionality."""

    @pytest.mark.asyncio
    async def test_send_to_user(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
    ):
        """Test sending event to specific user."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        # Reset mock to clear connection event
        mock_websocket.send_text.reset_mock()

        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_id": "G2", "project_id": "test"},
        )

        result = await websocket_manager.send_to_user(sample_user_id, event)

        assert result is True
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["event_type"] == "gate_approved"

    @pytest.mark.asyncio
    async def test_broadcast_to_project(
        self,
        websocket_manager: WebSocketManager,
        sample_project_id: UUID,
    ):
        """Test broadcasting to all project subscribers."""
        # Create multiple mock users
        users = []
        for _ in range(3):
            user_id = uuid4()
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()

            await websocket_manager.connect(
                websocket=mock_ws,
                user_id=user_id,
                project_ids=[sample_project_id],
            )
            users.append((user_id, mock_ws))

        event = WebSocketEvent(
            event_type=WebSocketEventType.EVIDENCE_UPLOADED,
            payload={"evidence_id": "test"},
            project_id=sample_project_id,
        )

        sent_count = await websocket_manager.broadcast_to_project(
            sample_project_id, event
        )

        assert sent_count == 3

        # Verify all users received the event
        for _, mock_ws in users:
            # Called twice: once for connect, once for broadcast
            assert mock_ws.send_text.call_count >= 2

    @pytest.mark.asyncio
    async def test_broadcast_exclude_user(
        self,
        websocket_manager: WebSocketManager,
        sample_project_id: UUID,
    ):
        """Test broadcasting with user exclusion."""
        user1_id = uuid4()
        user2_id = uuid4()

        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_ws1,
            user_id=user1_id,
            project_ids=[sample_project_id],
        )

        await websocket_manager.connect(
            websocket=mock_ws2,
            user_id=user2_id,
            project_ids=[sample_project_id],
        )

        # Reset mocks
        mock_ws1.send_text.reset_mock()
        mock_ws2.send_text.reset_mock()

        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_id": "G2"},
        )

        sent_count = await websocket_manager.broadcast_to_project(
            sample_project_id, event, exclude_user=user1_id
        )

        assert sent_count == 1
        mock_ws1.send_text.assert_not_called()
        mock_ws2.send_text.assert_called_once()


# =========================================================================
# Test: Message Handling
# =========================================================================


class TestMessageHandling:
    """Test client message handling."""

    @pytest.mark.asyncio
    async def test_handle_ping_message(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
    ):
        """Test handling ping message."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        response = await websocket_manager.handle_client_message(
            sample_user_id, '{"action": "ping"}'
        )

        assert response is not None
        assert response.event_type == WebSocketEventType.PONG

    @pytest.mark.asyncio
    async def test_handle_subscribe_message(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
        sample_project_id: UUID,
    ):
        """Test handling subscribe message."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        response = await websocket_manager.handle_client_message(
            sample_user_id,
            json.dumps({"action": "subscribe", "project_id": str(sample_project_id)}),
        )

        assert response is not None
        assert response.event_type == WebSocketEventType.CONNECTED
        assert sample_project_id in websocket_manager._connections[sample_user_id].subscribed_projects

    @pytest.mark.asyncio
    async def test_handle_unsubscribe_message(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
        sample_project_id: UUID,
    ):
        """Test handling unsubscribe message."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
            project_ids=[sample_project_id],
        )

        response = await websocket_manager.handle_client_message(
            sample_user_id,
            json.dumps({"action": "unsubscribe", "project_id": str(sample_project_id)}),
        )

        assert response is not None
        assert response.event_type == WebSocketEventType.DISCONNECTED
        assert sample_project_id not in websocket_manager._connections[sample_user_id].subscribed_projects

    @pytest.mark.asyncio
    async def test_handle_invalid_json(
        self,
        websocket_manager: WebSocketManager,
        mock_websocket,
        sample_user_id: UUID,
    ):
        """Test handling invalid JSON message."""
        await websocket_manager.connect(
            websocket=mock_websocket,
            user_id=sample_user_id,
        )

        response = await websocket_manager.handle_client_message(
            sample_user_id, "not valid json"
        )

        assert response is None


# =========================================================================
# Test: WebSocket Event
# =========================================================================


class TestWebSocketEvent:
    """Test WebSocketEvent class."""

    def test_event_to_dict(self, sample_project_id: UUID, sample_user_id: UUID):
        """Test event serialization to dictionary."""
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_id": "G2", "project_name": "Test"},
            project_id=sample_project_id,
            user_id=sample_user_id,
        )

        data = event.to_dict()

        assert data["event_type"] == "gate_approved"
        assert data["payload"]["gate_id"] == "G2"
        assert data["project_id"] == str(sample_project_id)
        assert data["user_id"] == str(sample_user_id)
        assert "timestamp" in data

    def test_event_to_json(self):
        """Test event serialization to JSON."""
        event = WebSocketEvent(
            event_type=WebSocketEventType.EVIDENCE_UPLOADED,
            payload={"evidence_id": "test-123"},
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "evidence_uploaded"
        assert parsed["payload"]["evidence_id"] == "test-123"


# =========================================================================
# Test: Connection Stats
# =========================================================================


class TestConnectionStats:
    """Test connection statistics."""

    @pytest.mark.asyncio
    async def test_get_connection_stats(
        self,
        websocket_manager: WebSocketManager,
        sample_project_id: UUID,
    ):
        """Test getting connection statistics."""
        # Add some connections
        for _ in range(3):
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()

            await websocket_manager.connect(
                websocket=mock_ws,
                user_id=uuid4(),
                project_ids=[sample_project_id],
            )

        stats = websocket_manager.get_connection_stats()

        assert stats["total_connections"] == 3
        assert stats["total_projects_subscribed"] == 1
        assert str(sample_project_id) in stats["connections_by_project"]
        assert stats["connections_by_project"][str(sample_project_id)] == 3


# =========================================================================
# Test: Global Instance
# =========================================================================


class TestGlobalInstance:
    """Test global WebSocket manager instance."""

    def test_get_singleton(self):
        """Test that get_websocket_manager returns singleton."""
        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()

        assert manager1 is manager2


# =========================================================================
# Test: Event Types
# =========================================================================


class TestEventTypes:
    """Test WebSocket event type enumeration."""

    def test_all_event_types_exist(self):
        """Test that all expected event types are defined."""
        expected_types = [
            "connected",
            "disconnected",
            "ping",
            "pong",
            "gate_approved",
            "gate_rejected",
            "gate_approval_required",
            "evidence_uploaded",
            "policy_violation",
            "comment_added",
            "notification_read",
            "notification_created",
            "project_updated",
            "member_added",
            "member_removed",
            "vcr_created",
            "vcr_updated",
            "mrp_validated",
            "context_snapshot_created",
            "template_updated",
        ]

        for event_type in expected_types:
            assert hasattr(WebSocketEventType, event_type.upper())
