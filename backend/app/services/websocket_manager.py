"""
=========================================================================
WebSocket Connection Manager - Real-time Notifications
SDLC Orchestrator - Sprint 153 (Real-time Notifications)

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 153 Day 1
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Purpose:
- Manage WebSocket connections per user/project
- Broadcast real-time events to connected clients
- Handle connection lifecycle (connect, disconnect, reconnect)
- Authentication via JWT token in query params

Events:
- gate_approved: Gate approval notification
- evidence_uploaded: New evidence uploaded
- policy_violation: Policy violation detected
- comment_added: New comment on entity
- notification_read: Notification marked as read

Zero Mock Policy: Production-ready WebSocket implementation
=========================================================================
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


# ============================================================================
# WebSocket Event Types
# ============================================================================


class WebSocketEventType(str, Enum):
    """Types of WebSocket events."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"

    # Notification events
    GATE_APPROVED = "gate_approved"
    GATE_REJECTED = "gate_rejected"
    GATE_APPROVAL_REQUIRED = "gate_approval_required"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    POLICY_VIOLATION = "policy_violation"
    COMMENT_ADDED = "comment_added"
    NOTIFICATION_READ = "notification_read"
    NOTIFICATION_CREATED = "notification_created"

    # Project events
    PROJECT_UPDATED = "project_updated"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"

    # MRP/VCR events (Sprint 152+)
    VCR_CREATED = "vcr_created"
    VCR_UPDATED = "vcr_updated"
    MRP_VALIDATED = "mrp_validated"

    # Context Authority events
    CONTEXT_SNAPSHOT_CREATED = "context_snapshot_created"
    TEMPLATE_UPDATED = "template_updated"


@dataclass
class WebSocketEvent:
    """WebSocket event payload."""

    event_type: WebSocketEventType
    payload: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)
    project_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "project_id": str(self.project_id) if self.project_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""

    websocket: WebSocket
    user_id: UUID
    connected_at: datetime = field(default_factory=datetime.utcnow)
    subscribed_projects: Set[UUID] = field(default_factory=set)
    last_ping: datetime = field(default_factory=datetime.utcnow)

    def is_subscribed_to(self, project_id: UUID) -> bool:
        """Check if connection is subscribed to a project."""
        return project_id in self.subscribed_projects


# ============================================================================
# WebSocket Connection Manager
# ============================================================================


class WebSocketManager:
    """
    Manages WebSocket connections for real-time notifications.

    Features:
    - User-based connection tracking
    - Project-based message routing
    - Broadcast to all users or specific users
    - Connection health monitoring (ping/pong)

    Usage:
        manager = WebSocketManager()

        # Connect user
        await manager.connect(websocket, user_id)

        # Subscribe to project
        await manager.subscribe_to_project(user_id, project_id)

        # Broadcast event
        await manager.broadcast_to_project(
            project_id=project_id,
            event=WebSocketEvent(
                event_type=WebSocketEventType.GATE_APPROVED,
                payload={"gate_id": "...", "gate_code": "G2"},
                project_id=project_id,
            )
        )

        # Disconnect user
        await manager.disconnect(user_id)
    """

    def __init__(self):
        """Initialize the connection manager."""
        # Map user_id -> ConnectionInfo
        self._connections: dict[UUID, ConnectionInfo] = {}

        # Map project_id -> Set[user_id] for efficient project broadcasts
        self._project_subscriptions: dict[UUID, Set[UUID]] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        logger.info("WebSocketManager initialized")

    @property
    def active_connections(self) -> int:
        """Get number of active connections."""
        return len(self._connections)

    async def connect(
        self,
        websocket: WebSocket,
        user_id: UUID,
        project_ids: Optional[list[UUID]] = None,
    ) -> bool:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: User ID from JWT token
            project_ids: Optional list of projects to subscribe to immediately

        Returns:
            True if connection successful
        """
        try:
            await websocket.accept()

            async with self._lock:
                # Close existing connection if any (single connection per user)
                if user_id in self._connections:
                    old_conn = self._connections[user_id]
                    try:
                        await old_conn.websocket.close(code=1000, reason="New connection established")
                    except Exception:
                        pass
                    # Clean up old subscriptions
                    for project_id in old_conn.subscribed_projects:
                        if project_id in self._project_subscriptions:
                            self._project_subscriptions[project_id].discard(user_id)

                # Create new connection
                conn_info = ConnectionInfo(
                    websocket=websocket,
                    user_id=user_id,
                )

                # Subscribe to projects
                if project_ids:
                    for project_id in project_ids:
                        conn_info.subscribed_projects.add(project_id)
                        if project_id not in self._project_subscriptions:
                            self._project_subscriptions[project_id] = set()
                        self._project_subscriptions[project_id].add(user_id)

                self._connections[user_id] = conn_info

            # Send connection confirmation
            await self._send_event(
                websocket,
                WebSocketEvent(
                    event_type=WebSocketEventType.CONNECTED,
                    payload={
                        "message": "Connected to SDLC Orchestrator",
                        "user_id": str(user_id),
                        "subscribed_projects": [str(p) for p in conn_info.subscribed_projects],
                    },
                    user_id=user_id,
                ),
            )

            logger.info(
                f"WebSocket connected: user={user_id}, "
                f"projects={len(conn_info.subscribed_projects)}, "
                f"total_connections={self.active_connections}"
            )

            return True

        except Exception as e:
            logger.error(f"WebSocket connection failed for user {user_id}: {e}")
            return False

    async def disconnect(self, user_id: UUID) -> None:
        """
        Disconnect a user's WebSocket.

        Args:
            user_id: User ID to disconnect
        """
        async with self._lock:
            if user_id not in self._connections:
                return

            conn_info = self._connections[user_id]

            # Clean up project subscriptions
            for project_id in conn_info.subscribed_projects:
                if project_id in self._project_subscriptions:
                    self._project_subscriptions[project_id].discard(user_id)
                    # Remove empty project sets
                    if not self._project_subscriptions[project_id]:
                        del self._project_subscriptions[project_id]

            # Remove connection
            del self._connections[user_id]

            logger.info(
                f"WebSocket disconnected: user={user_id}, "
                f"total_connections={self.active_connections}"
            )

    async def subscribe_to_project(self, user_id: UUID, project_id: UUID) -> bool:
        """
        Subscribe a user to project events.

        Args:
            user_id: User ID
            project_id: Project ID to subscribe to

        Returns:
            True if subscription successful
        """
        async with self._lock:
            if user_id not in self._connections:
                return False

            conn_info = self._connections[user_id]
            conn_info.subscribed_projects.add(project_id)

            if project_id not in self._project_subscriptions:
                self._project_subscriptions[project_id] = set()
            self._project_subscriptions[project_id].add(user_id)

            logger.debug(f"User {user_id} subscribed to project {project_id}")
            return True

    async def unsubscribe_from_project(self, user_id: UUID, project_id: UUID) -> bool:
        """
        Unsubscribe a user from project events.

        Args:
            user_id: User ID
            project_id: Project ID to unsubscribe from

        Returns:
            True if unsubscription successful
        """
        async with self._lock:
            if user_id not in self._connections:
                return False

            conn_info = self._connections[user_id]
            conn_info.subscribed_projects.discard(project_id)

            if project_id in self._project_subscriptions:
                self._project_subscriptions[project_id].discard(user_id)
                if not self._project_subscriptions[project_id]:
                    del self._project_subscriptions[project_id]

            logger.debug(f"User {user_id} unsubscribed from project {project_id}")
            return True

    async def send_to_user(self, user_id: UUID, event: WebSocketEvent) -> bool:
        """
        Send event to a specific user.

        Args:
            user_id: Target user ID
            event: Event to send

        Returns:
            True if sent successfully
        """
        if user_id not in self._connections:
            return False

        conn_info = self._connections[user_id]
        return await self._send_event(conn_info.websocket, event)

    async def broadcast_to_project(
        self,
        project_id: UUID,
        event: WebSocketEvent,
        exclude_user: Optional[UUID] = None,
    ) -> int:
        """
        Broadcast event to all users subscribed to a project.

        Args:
            project_id: Project ID
            event: Event to broadcast
            exclude_user: Optional user to exclude from broadcast

        Returns:
            Number of users successfully notified
        """
        if project_id not in self._project_subscriptions:
            return 0

        event.project_id = project_id
        sent_count = 0
        failed_users: list[UUID] = []

        for user_id in self._project_subscriptions[project_id]:
            if exclude_user and user_id == exclude_user:
                continue

            if user_id in self._connections:
                success = await self._send_event(
                    self._connections[user_id].websocket,
                    event,
                )
                if success:
                    sent_count += 1
                else:
                    failed_users.append(user_id)

        # Clean up failed connections
        for user_id in failed_users:
            await self.disconnect(user_id)

        logger.debug(
            f"Broadcast to project {project_id}: "
            f"sent={sent_count}, failed={len(failed_users)}"
        )

        return sent_count

    async def broadcast_to_users(
        self,
        user_ids: list[UUID],
        event: WebSocketEvent,
    ) -> int:
        """
        Broadcast event to specific users.

        Args:
            user_ids: List of user IDs
            event: Event to broadcast

        Returns:
            Number of users successfully notified
        """
        sent_count = 0
        failed_users: list[UUID] = []

        for user_id in user_ids:
            if user_id in self._connections:
                success = await self._send_event(
                    self._connections[user_id].websocket,
                    event,
                )
                if success:
                    sent_count += 1
                else:
                    failed_users.append(user_id)

        # Clean up failed connections
        for user_id in failed_users:
            await self.disconnect(user_id)

        return sent_count

    async def broadcast_to_all(
        self,
        event: WebSocketEvent,
        exclude_user: Optional[UUID] = None,
    ) -> int:
        """
        Broadcast event to all connected users.

        Args:
            event: Event to broadcast
            exclude_user: Optional user to exclude

        Returns:
            Number of users successfully notified
        """
        sent_count = 0
        failed_users: list[UUID] = []

        for user_id, conn_info in list(self._connections.items()):
            if exclude_user and user_id == exclude_user:
                continue

            success = await self._send_event(conn_info.websocket, event)
            if success:
                sent_count += 1
            else:
                failed_users.append(user_id)

        # Clean up failed connections
        for user_id in failed_users:
            await self.disconnect(user_id)

        return sent_count

    async def _send_event(
        self,
        websocket: WebSocket,
        event: WebSocketEvent,
    ) -> bool:
        """
        Send event to a WebSocket connection.

        Args:
            websocket: Target WebSocket
            event: Event to send

        Returns:
            True if sent successfully
        """
        try:
            await websocket.send_text(event.to_json())
            return True
        except Exception as e:
            logger.warning(f"Failed to send WebSocket event: {e}")
            return False

    async def handle_client_message(
        self,
        user_id: UUID,
        message: str,
    ) -> Optional[WebSocketEvent]:
        """
        Handle incoming message from client.

        Args:
            user_id: User ID
            message: Raw message string

        Returns:
            Response event if any
        """
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "ping":
                # Update last ping time
                if user_id in self._connections:
                    self._connections[user_id].last_ping = datetime.utcnow()
                return WebSocketEvent(
                    event_type=WebSocketEventType.PONG,
                    payload={"timestamp": datetime.utcnow().isoformat()},
                    user_id=user_id,
                )

            elif action == "subscribe":
                project_id = data.get("project_id")
                if project_id:
                    await self.subscribe_to_project(user_id, UUID(project_id))
                    return WebSocketEvent(
                        event_type=WebSocketEventType.CONNECTED,
                        payload={
                            "message": f"Subscribed to project {project_id}",
                            "project_id": project_id,
                        },
                        user_id=user_id,
                    )

            elif action == "unsubscribe":
                project_id = data.get("project_id")
                if project_id:
                    await self.unsubscribe_from_project(user_id, UUID(project_id))
                    return WebSocketEvent(
                        event_type=WebSocketEventType.DISCONNECTED,
                        payload={
                            "message": f"Unsubscribed from project {project_id}",
                            "project_id": project_id,
                        },
                        user_id=user_id,
                    )

            elif action == "mark_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    return WebSocketEvent(
                        event_type=WebSocketEventType.NOTIFICATION_READ,
                        payload={"notification_id": notification_id},
                        user_id=user_id,
                    )

            return None

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from user {user_id}: {message[:100]}")
            return None
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            return None

    def get_connection_stats(self) -> dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection stats
        """
        return {
            "total_connections": len(self._connections),
            "total_projects_subscribed": len(self._project_subscriptions),
            "connections_by_project": {
                str(pid): len(users)
                for pid, users in self._project_subscriptions.items()
            },
        }


# ============================================================================
# Global WebSocket Manager Instance
# ============================================================================

# Singleton instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.

    Returns:
        WebSocketManager singleton
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
