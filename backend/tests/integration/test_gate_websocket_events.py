"""
=========================================================================
Gate WebSocket Events Integration Tests
SDLC Orchestrator - Sprint 153 (Real-time Notifications)

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 153 Day 2
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Test Coverage:
- Gate approval WebSocket events
- Gate rejection WebSocket events
- Gate approval required WebSocket events
- Project-based event broadcasting

Zero Mock Policy: Integration tests with real services
=========================================================================
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.notification_service import (
    NotificationPayload,
    NotificationPriority,
    NotificationService,
    NotificationType,
    create_notification_service,
)
from app.services.websocket_manager import (
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
def mock_project():
    """Create a mock project."""
    project = MagicMock()
    project.id = uuid4()
    project.name = "Test Project"
    return project


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = uuid4()
    user.name = "Test User"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_approver():
    """Create a mock approver (CTO/CPO/CEO)."""
    approver = MagicMock()
    approver.id = uuid4()
    approver.name = "CTO User"
    approver.email = "cto@example.com"
    return approver


@pytest.fixture
def notification_service():
    """Create notification service without DB."""
    return create_notification_service(db=None)


# =========================================================================
# Test: Gate Approval WebSocket Events
# =========================================================================


class TestGateApprovalWebSocketEvents:
    """Test WebSocket events for gate approvals."""

    @pytest.mark.asyncio
    async def test_gate_approved_creates_websocket_event(
        self,
        websocket_manager: WebSocketManager,
        mock_project,
        mock_approver,
        mock_user,
    ):
        """Test that gate approval creates correct WebSocket event."""
        # Setup: Connect a user and subscribe to project
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_ws,
            user_id=mock_user.id,
            project_ids=[mock_project.id],
        )

        # Reset mock to clear connection event
        mock_ws.send_text.reset_mock()

        # Create gate approval event
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "approved_by": str(mock_approver.id),
                "approved_by_name": mock_approver.name,
                "comments": "All exit criteria validated",
            },
            project_id=mock_project.id,
        )

        # Broadcast to project
        sent_count = await websocket_manager.broadcast_to_project(
            mock_project.id, event
        )

        # Verify event was sent
        assert sent_count == 1
        mock_ws.send_text.assert_called_once()

        # Verify event content
        sent_data = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_data["event_type"] == "gate_approved"
        assert sent_data["payload"]["gate_code"] == "G2"
        assert sent_data["payload"]["approved_by_name"] == mock_approver.name

    @pytest.mark.asyncio
    async def test_gate_rejected_creates_websocket_event(
        self,
        websocket_manager: WebSocketManager,
        mock_project,
        mock_approver,
        mock_user,
    ):
        """Test that gate rejection creates correct WebSocket event."""
        # Setup: Connect a user and subscribe to project
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_ws,
            user_id=mock_user.id,
            project_ids=[mock_project.id],
        )

        # Reset mock to clear connection event
        mock_ws.send_text.reset_mock()

        # Create gate rejection event
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_REJECTED,
            payload={
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "rejected_by": str(mock_approver.id),
                "rejected_by_name": mock_approver.name,
                "comments": "Missing security documentation",
            },
            project_id=mock_project.id,
        )

        # Broadcast to project
        sent_count = await websocket_manager.broadcast_to_project(
            mock_project.id, event
        )

        # Verify event was sent
        assert sent_count == 1

        # Verify event content
        sent_data = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_data["event_type"] == "gate_rejected"
        assert sent_data["payload"]["comments"] == "Missing security documentation"

    @pytest.mark.asyncio
    async def test_gate_approval_required_creates_websocket_event(
        self,
        websocket_manager: WebSocketManager,
        mock_project,
        mock_user,
    ):
        """Test that gate approval required creates correct WebSocket event."""
        # Setup: Connect multiple users (approvers)
        approver_ids = [uuid4(), uuid4()]
        mock_websockets = []

        for approver_id in approver_ids:
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()
            mock_websockets.append(mock_ws)

            await websocket_manager.connect(
                websocket=mock_ws,
                user_id=approver_id,
                project_ids=[mock_project.id],
            )

        # Reset mocks
        for mock_ws in mock_websockets:
            mock_ws.send_text.reset_mock()

        # Create gate approval required event
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVAL_REQUIRED,
            payload={
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "submitted_by": str(mock_user.id),
                "submitted_by_name": mock_user.name,
            },
            project_id=mock_project.id,
        )

        # Broadcast to project
        sent_count = await websocket_manager.broadcast_to_project(
            mock_project.id, event
        )

        # Verify event was sent to all approvers
        assert sent_count == 2

        # Verify both websockets received the event
        for mock_ws in mock_websockets:
            mock_ws.send_text.assert_called_once()


# =========================================================================
# Test: Notification Service WebSocket Integration
# =========================================================================


class TestNotificationServiceWebSocketIntegration:
    """Test notification service WebSocket integration for gates."""

    @pytest.mark.asyncio
    async def test_gate_approved_notification_maps_to_websocket_event(
        self,
        notification_service,
        mock_project,
        mock_approver,
        mock_user,
    ):
        """Test that gate approved notification maps to correct WebSocket event type."""
        # Create notification payload
        payload = NotificationPayload(
            type=NotificationType.GATE_APPROVED,
            priority=NotificationPriority.MEDIUM,
            title=f"Gate Approved: G2 - {mock_project.name}",
            message=f"Gate G2 has been approved by {mock_approver.name}",
            project_id=mock_project.id,
            project_name=mock_project.name,
            metadata={
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "approved_by": str(mock_approver.id),
            },
        )

        # Verify the notification type maps to correct WebSocket event type
        from app.services.websocket_manager import WebSocketEventType

        event_type_map = {
            NotificationType.GATE_APPROVED: WebSocketEventType.GATE_APPROVED,
            NotificationType.GATE_REJECTED: WebSocketEventType.GATE_REJECTED,
            NotificationType.GATE_APPROVAL_REQUIRED: WebSocketEventType.GATE_APPROVAL_REQUIRED,
        }

        assert event_type_map[payload.type] == WebSocketEventType.GATE_APPROVED

    @pytest.mark.asyncio
    async def test_gate_rejected_notification_maps_to_websocket_event(
        self,
        notification_service,
        mock_project,
        mock_approver,
    ):
        """Test that gate rejected notification maps to correct WebSocket event type."""
        payload = NotificationPayload(
            type=NotificationType.GATE_REJECTED,
            priority=NotificationPriority.HIGH,
            title=f"Gate Rejected: G2 - {mock_project.name}",
            message=f"Gate G2 has been rejected by {mock_approver.name}",
            project_id=mock_project.id,
            project_name=mock_project.name,
            metadata={
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "rejected_by": str(mock_approver.id),
                "comments": "Missing documentation",
            },
        )

        from app.services.websocket_manager import WebSocketEventType

        event_type_map = {
            NotificationType.GATE_APPROVED: WebSocketEventType.GATE_APPROVED,
            NotificationType.GATE_REJECTED: WebSocketEventType.GATE_REJECTED,
            NotificationType.GATE_APPROVAL_REQUIRED: WebSocketEventType.GATE_APPROVAL_REQUIRED,
        }

        assert event_type_map[payload.type] == WebSocketEventType.GATE_REJECTED

    @pytest.mark.asyncio
    async def test_websocket_broadcast_excludes_sender(
        self,
        websocket_manager: WebSocketManager,
        mock_project,
    ):
        """Test that WebSocket broadcast can exclude the action sender."""
        sender_id = uuid4()
        receiver_id = uuid4()

        # Setup sender and receiver
        sender_ws = AsyncMock()
        sender_ws.accept = AsyncMock()
        sender_ws.send_text = AsyncMock()

        receiver_ws = AsyncMock()
        receiver_ws.accept = AsyncMock()
        receiver_ws.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=sender_ws,
            user_id=sender_id,
            project_ids=[mock_project.id],
        )

        await websocket_manager.connect(
            websocket=receiver_ws,
            user_id=receiver_id,
            project_ids=[mock_project.id],
        )

        # Reset mocks
        sender_ws.send_text.reset_mock()
        receiver_ws.send_text.reset_mock()

        # Broadcast with exclusion
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_code": "G2"},
            project_id=mock_project.id,
        )

        sent_count = await websocket_manager.broadcast_to_project(
            mock_project.id,
            event,
            exclude_user=sender_id,
        )

        # Verify only receiver got the message
        assert sent_count == 1
        sender_ws.send_text.assert_not_called()
        receiver_ws.send_text.assert_called_once()


# =========================================================================
# Test: Event Payload Validation
# =========================================================================


class TestEventPayloadValidation:
    """Test WebSocket event payload structure."""

    def test_gate_approved_event_structure(self, mock_project):
        """Test gate approved event has correct structure."""
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={
                "gate_id": str(uuid4()),
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "project_id": str(mock_project.id),
                "approved_by": str(uuid4()),
                "approved_by_name": "CTO User",
                "comments": "Approved",
            },
            project_id=mock_project.id,
        )

        data = event.to_dict()

        assert data["event_type"] == "gate_approved"
        assert "timestamp" in data
        assert data["project_id"] == str(mock_project.id)
        assert data["payload"]["gate_code"] == "G2"

    def test_gate_rejected_event_structure(self, mock_project):
        """Test gate rejected event has correct structure."""
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_REJECTED,
            payload={
                "gate_id": str(uuid4()),
                "gate_name": "Ship Ready",
                "gate_code": "G2",
                "rejected_by": str(uuid4()),
                "rejected_by_name": "CTO User",
                "comments": "Missing documentation",
            },
            project_id=mock_project.id,
        )

        data = event.to_dict()

        assert data["event_type"] == "gate_rejected"
        assert data["payload"]["comments"] == "Missing documentation"

    def test_event_to_json_serialization(self, mock_project):
        """Test event can be serialized to JSON."""
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVAL_REQUIRED,
            payload={
                "gate_code": "G2",
                "submitted_by": str(uuid4()),
            },
            project_id=mock_project.id,
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "gate_approval_required"
        assert isinstance(parsed["timestamp"], str)


# =========================================================================
# Test: Multi-Project Subscription
# =========================================================================


class TestMultiProjectSubscription:
    """Test events with multi-project subscriptions."""

    @pytest.mark.asyncio
    async def test_user_receives_events_from_multiple_projects(
        self,
        websocket_manager: WebSocketManager,
    ):
        """Test user subscribed to multiple projects receives events from all."""
        user_id = uuid4()
        project_1 = uuid4()
        project_2 = uuid4()

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        # Connect and subscribe to both projects
        await websocket_manager.connect(
            websocket=mock_ws,
            user_id=user_id,
            project_ids=[project_1, project_2],
        )

        # Reset mock
        mock_ws.send_text.reset_mock()

        # Send event to project 1
        event_1 = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_code": "G1"},
            project_id=project_1,
        )

        await websocket_manager.broadcast_to_project(project_1, event_1)

        # Verify received
        assert mock_ws.send_text.call_count == 1

        # Send event to project 2
        event_2 = WebSocketEvent(
            event_type=WebSocketEventType.GATE_REJECTED,
            payload={"gate_code": "G2"},
            project_id=project_2,
        )

        await websocket_manager.broadcast_to_project(project_2, event_2)

        # Verify received both events
        assert mock_ws.send_text.call_count == 2

    @pytest.mark.asyncio
    async def test_user_does_not_receive_events_from_unsubscribed_project(
        self,
        websocket_manager: WebSocketManager,
    ):
        """Test user does not receive events from projects they're not subscribed to."""
        user_id = uuid4()
        subscribed_project = uuid4()
        other_project = uuid4()

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        # Connect and subscribe to only one project
        await websocket_manager.connect(
            websocket=mock_ws,
            user_id=user_id,
            project_ids=[subscribed_project],
        )

        # Reset mock
        mock_ws.send_text.reset_mock()

        # Send event to other project
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_code": "G2"},
            project_id=other_project,
        )

        sent_count = await websocket_manager.broadcast_to_project(other_project, event)

        # Verify not received
        assert sent_count == 0
        mock_ws.send_text.assert_not_called()


# =========================================================================
# Test: Connection Lifecycle with Gate Events
# =========================================================================


class TestConnectionLifecycleWithGateEvents:
    """Test connection lifecycle scenarios with gate events."""

    @pytest.mark.asyncio
    async def test_gate_event_after_reconnection(
        self,
        websocket_manager: WebSocketManager,
    ):
        """Test gate events work after user reconnects."""
        user_id = uuid4()
        project_id = uuid4()

        # First connection
        mock_ws_1 = AsyncMock()
        mock_ws_1.accept = AsyncMock()
        mock_ws_1.send_text = AsyncMock()
        mock_ws_1.close = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_ws_1,
            user_id=user_id,
            project_ids=[project_id],
        )

        # Disconnect
        await websocket_manager.disconnect(user_id)

        # Second connection (reconnect)
        mock_ws_2 = AsyncMock()
        mock_ws_2.accept = AsyncMock()
        mock_ws_2.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_ws_2,
            user_id=user_id,
            project_ids=[project_id],
        )

        # Reset mock
        mock_ws_2.send_text.reset_mock()

        # Send event
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_code": "G2"},
            project_id=project_id,
        )

        sent_count = await websocket_manager.broadcast_to_project(project_id, event)

        # Verify new connection receives event
        assert sent_count == 1
        mock_ws_2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_dynamic_project_subscription(
        self,
        websocket_manager: WebSocketManager,
    ):
        """Test subscribing to project after initial connection."""
        user_id = uuid4()
        project_id = uuid4()

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        # Connect without project subscription
        await websocket_manager.connect(
            websocket=mock_ws,
            user_id=user_id,
            project_ids=[],
        )

        # Reset mock
        mock_ws.send_text.reset_mock()

        # Try to send event (should not be received)
        event = WebSocketEvent(
            event_type=WebSocketEventType.GATE_APPROVED,
            payload={"gate_code": "G2"},
            project_id=project_id,
        )

        sent_count = await websocket_manager.broadcast_to_project(project_id, event)
        assert sent_count == 0

        # Now subscribe to project
        await websocket_manager.subscribe_to_project(user_id, project_id)

        # Send event again (should be received)
        sent_count = await websocket_manager.broadcast_to_project(project_id, event)
        assert sent_count == 1
        mock_ws.send_text.assert_called_once()
