"""
agent_bridge — OTT channel abstraction layer.

Provides the canonical OrchestratorMessage type and dispatcher
for normalizing external OTT channel payloads into a unified format
for the Multi-Agent Team Engine.

Sprint 181 — ADR-059 (Enterprise-First) + ADR-060 (Channel Abstraction).
Channels: telegram (Sprint 181), zalo (Sprint 181), teams (Sprint 182), slack (Sprint 183).
"""

from app.services.agent_bridge.protocol_adapter import (
    OrchestratorMessage,
    normalize,
    route_to_normalizer,
)

__all__ = [
    "OrchestratorMessage",
    "normalize",
    "route_to_normalizer",
]
