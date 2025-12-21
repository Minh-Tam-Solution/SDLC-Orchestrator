"""
Shadow Mode Configuration - AI Detection Production Validation

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
CTO P1: Shadow Mode for Production Validation

Purpose:
Enable shadow mode for AI detection to validate accuracy in production
without affecting user experience. Logs detection results for analysis
without blocking or modifying PRs.

Configuration:
- SHADOW_MODE_ENABLED: Enable/disable shadow mode (default: True in production)
- SHADOW_MODE_SAMPLE_RATE: Percentage of PRs to analyze (default: 100%)
- SHADOW_MODE_LOG_LEVEL: Logging verbosity (default: INFO)

Usage:
    from app.services.ai_detection.shadow_mode import shadow_mode_config, log_shadow_result

    if shadow_mode_config.is_enabled:
        result = await detection_service.detect(pr_data, commits, diff)
        log_shadow_result(pr_id, result)
"""

import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from . import AIDetectionResult

logger = logging.getLogger(__name__)


@dataclass
class ShadowModeConfig:
    """Configuration for shadow mode deployment."""

    # Enable shadow mode (default: True for production validation)
    enabled: bool = field(
        default_factory=lambda: os.getenv("AI_DETECTION_SHADOW_MODE", "true").lower()
        == "true"
    )

    # Sample rate for analysis (0.0 - 1.0, default: 1.0 = 100%)
    sample_rate: float = field(
        default_factory=lambda: float(
            os.getenv("AI_DETECTION_SHADOW_SAMPLE_RATE", "1.0")
        )
    )

    # Log level for shadow mode (DEBUG, INFO, WARNING)
    log_level: str = field(
        default_factory=lambda: os.getenv("AI_DETECTION_SHADOW_LOG_LEVEL", "INFO")
    )

    # Metrics collection enabled
    collect_metrics: bool = field(
        default_factory=lambda: os.getenv(
            "AI_DETECTION_SHADOW_METRICS", "true"
        ).lower()
        == "true"
    )

    @property
    def is_enabled(self) -> bool:
        """Check if shadow mode is enabled."""
        return self.enabled

    def should_sample(self) -> bool:
        """Determine if this request should be sampled based on sample rate."""
        if not self.enabled:
            return False
        if self.sample_rate >= 1.0:
            return True
        return random.random() < self.sample_rate


# Singleton configuration
shadow_mode_config = ShadowModeConfig()


@dataclass
class ShadowModeResult:
    """Result of shadow mode detection for logging/analysis."""

    pr_id: str
    pr_title: str
    timestamp: datetime
    is_ai_generated: bool
    confidence: float
    detected_tool: Optional[str]
    detection_method: str
    detection_duration_ms: int
    individual_confidences: Dict[str, float]
    weighted_confidence: float
    detection_threshold: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "pr_id": self.pr_id,
            "pr_title": self.pr_title[:100],  # Truncate for logging
            "timestamp": self.timestamp.isoformat(),
            "is_ai_generated": self.is_ai_generated,
            "confidence": round(self.confidence, 4),
            "detected_tool": self.detected_tool,
            "detection_method": self.detection_method,
            "detection_duration_ms": self.detection_duration_ms,
            "individual_confidences": {
                k: round(v, 4) for k, v in self.individual_confidences.items()
            },
            "weighted_confidence": round(self.weighted_confidence, 4),
            "detection_threshold": self.detection_threshold,
        }


def log_shadow_result(
    pr_id: str,
    pr_title: str,
    result: AIDetectionResult,
) -> Optional[ShadowModeResult]:
    """
    Log shadow mode detection result for production validation.

    Args:
        pr_id: GitHub PR ID or number
        pr_title: PR title for context
        result: AIDetectionResult from detection service

    Returns:
        ShadowModeResult if logged, None if skipped
    """
    if not shadow_mode_config.should_sample():
        return None

    # Extract evidence details
    evidence = result.detection_evidence or {}
    individual_confidences = evidence.get("individual_confidences", {})
    weighted_confidence = evidence.get("weighted_confidence", result.confidence)
    detection_threshold = evidence.get("detection_threshold", 0.5)

    shadow_result = ShadowModeResult(
        pr_id=pr_id,
        pr_title=pr_title,
        timestamp=datetime.utcnow(),
        is_ai_generated=result.is_ai_generated,
        confidence=result.confidence,
        detected_tool=result.detected_tool.value if result.detected_tool else None,
        detection_method=result.detection_method.value,
        detection_duration_ms=result.detection_duration_ms,
        individual_confidences=individual_confidences,
        weighted_confidence=weighted_confidence,
        detection_threshold=detection_threshold,
    )

    # Log based on configured level
    log_data = shadow_result.to_dict()

    if shadow_mode_config.log_level == "DEBUG":
        logger.debug(
            "Shadow mode detection",
            extra={"shadow_result": log_data},
        )
    else:
        logger.info(
            f"[SHADOW] PR {pr_id}: ai={result.is_ai_generated}, "
            f"conf={result.confidence:.2f}, tool={shadow_result.detected_tool}",
            extra={"shadow_result": log_data},
        )

    return shadow_result


def get_shadow_mode_status() -> Dict[str, Any]:
    """
    Get current shadow mode status for monitoring.

    Returns:
        Dict with shadow mode configuration and status
    """
    return {
        "enabled": shadow_mode_config.enabled,
        "sample_rate": shadow_mode_config.sample_rate,
        "log_level": shadow_mode_config.log_level,
        "collect_metrics": shadow_mode_config.collect_metrics,
    }
