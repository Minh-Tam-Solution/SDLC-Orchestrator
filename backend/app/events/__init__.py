"""
=========================================================================
Events Package - SDLC Orchestrator
Sprint 83 - Dynamic Context Injector

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 83 (Dynamic Context & Analytics)
Authority: CTO Approved
Framework: SDLC 5.1.3 P7 (Documentation Permanence)

Purpose:
- EventBus for pub/sub lifecycle events
- Lifecycle events (GateStatusChanged, SprintChanged, etc)
- Event-driven AGENTS.md updates

TRUE MOAT: Dynamic AGENTS.md by lifecycle stage = TRUE ORCHESTRATION
=========================================================================
"""

from app.events.event_bus import EventBus, EventHandler
from app.events.lifecycle_events import (
    LifecycleEvent,
    GateStatusChanged,
    SprintChanged,
    ConstraintDetected,
    AgentsMdUpdated,
    EvidenceUploaded,
    SecurityScanCompleted,
)

__all__ = [
    # EventBus
    "EventBus",
    "EventHandler",
    # Lifecycle Events
    "LifecycleEvent",
    "GateStatusChanged",
    "SprintChanged",
    "ConstraintDetected",
    "AgentsMdUpdated",
    "EvidenceUploaded",
    "SecurityScanCompleted",
]
