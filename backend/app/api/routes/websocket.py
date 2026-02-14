"""
=========================================================================
WebSocket API Routes - Real-time Communication
SDLC Orchestrator - Sprint 153 (Real-time Notifications)

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 153 Day 1
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Purpose:
- WebSocket endpoint for real-time notifications
- JWT authentication via query parameter
- Connection lifecycle management
- Event subscription handling

Endpoints:
- WS /ws/notifications - Real-time notification stream

Zero Mock Policy: Production-ready WebSocket endpoint
=========================================================================
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings
from app.services.websocket_manager import (
    WebSocketEvent,
    WebSocketEventType,
    get_websocket_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Authentication Helper
# ============================================================================


async def get_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT access token

    Returns:
        User ID if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id:
            return UUID(user_id)
        return None
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Invalid user ID in token: {e}")
        return None


# ============================================================================
# WebSocket Endpoints
# ============================================================================


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    project_ids: Optional[str] = Query(None, description="Comma-separated project IDs to subscribe"),
):
    """
    WebSocket endpoint for real-time notifications.

    Clients connect with their JWT token and optionally subscribe to specific projects.

    Connection URL:
        ws://host/ws/notifications?token=<jwt>&project_ids=<uuid1>,<uuid2>

    Client Messages:
        {"action": "ping"}
        {"action": "subscribe", "project_id": "<uuid>"}
        {"action": "unsubscribe", "project_id": "<uuid>"}
        {"action": "mark_read", "notification_id": "<uuid>"}

    Server Events:
        {"event_type": "connected", "payload": {...}}
        {"event_type": "gate_approved", "payload": {...}}
        {"event_type": "evidence_uploaded", "payload": {...}}
        {"event_type": "policy_violation", "payload": {...}}
        {"event_type": "notification_created", "payload": {...}}
    """
    # Authenticate user
    user_id = await get_user_id_from_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # Parse project IDs
    project_id_list: list[UUID] = []
    if project_ids:
        try:
            project_id_list = [UUID(pid.strip()) for pid in project_ids.split(",") if pid.strip()]
        except ValueError:
            await websocket.close(code=4002, reason="Invalid project ID format")
            return

    # Get manager and connect
    manager = get_websocket_manager()
    connected = await manager.connect(
        websocket=websocket,
        user_id=user_id,
        project_ids=project_id_list,
    )

    if not connected:
        await websocket.close(code=4003, reason="Connection failed")
        return

    try:
        # Main message loop
        while True:
            # Receive message from client
            message = await websocket.receive_text()

            # Handle the message
            response = await manager.handle_client_message(user_id, message)

            # Send response if any
            if response:
                await manager.send_to_user(user_id, response)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await manager.disconnect(user_id)


# ============================================================================
# REST Endpoints for WebSocket Management
# ============================================================================


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Connection statistics including total connections and subscriptions.
    """
    manager = get_websocket_manager()
    return manager.get_connection_stats()


@router.post("/broadcast/project/{project_id}")
async def broadcast_to_project(
    project_id: UUID,
    event_type: str = Query(..., description="Event type"),
    payload: dict = {},
):
    """
    Broadcast event to all users subscribed to a project.

    This is an internal endpoint for testing and admin use.

    Args:
        project_id: Project UUID
        event_type: Type of event
        payload: Event payload

    Returns:
        Number of users notified
    """
    manager = get_websocket_manager()

    try:
        ws_event_type = WebSocketEventType(event_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {event_type}",
        )

    event = WebSocketEvent(
        event_type=ws_event_type,
        payload=payload,
        project_id=project_id,
    )

    sent_count = await manager.broadcast_to_project(project_id, event)

    return {
        "success": True,
        "project_id": str(project_id),
        "event_type": event_type,
        "users_notified": sent_count,
    }
