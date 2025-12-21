"""
AI Detection Service - Base Interfaces

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Base classes and enums for AI detection strategies.
Provides unified interface for multiple detection methods.

Architecture:
- Strategy pattern for extensible detectors
- Combined weighted voting for accuracy
- Support for 8+ AI coding tools
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class AIToolType(str, Enum):
    """Supported AI coding tools."""

    CURSOR = "cursor"
    COPILOT = "copilot"
    CLAUDE_CODE = "claude_code"
    CHATGPT = "chatgpt"
    WINDSURF = "windsurf"
    CODY = "cody"
    TABNINE = "tabnine"
    OTHER = "other"
    MANUAL_TAG = "manual_tag"


class DetectionMethod(str, Enum):
    """Detection strategy used."""

    METADATA = "metadata"  # PR title/body/commits
    COMMIT_MESSAGE = "commit_message"  # Commit message patterns
    PATTERN_ANALYSIS = "pattern_analysis"  # Code pattern heuristics
    GITHUB_API = "github_api"  # GitHub Copilot API
    MANUAL_LABEL = "manual_label"  # User applied label
    MANUAL_COMMENT = "manual_comment"  # User comment
    COMBINED = "combined"  # Multiple strategies


@dataclass
class DetectionResult:
    """Result from AI detection process."""

    # Detection outcome
    detected: bool  # Whether AI code was detected
    confidence: float  # 0.0 - 1.0
    tool: Optional[AIToolType]  # Detected AI tool
    method: DetectionMethod  # Detection method used
    evidence: Dict  # Detection evidence/metadata

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "detected": self.detected,
            "confidence": self.confidence,
            "tool": self.tool.value if self.tool else None,
            "method": self.method.value,
            "evidence": self.evidence,
        }


@dataclass
class AIDetectionResult:
    """Combined detection result from multiple strategies."""

    # Detection outcome
    is_ai_generated: bool
    confidence: float  # 0.0 - 1.0

    # Tool identification
    detected_tool: Optional[AIToolType]
    detected_model: Optional[str]  # e.g., "gpt-4-turbo", "claude-3-opus"
    detected_model_version: Optional[str]

    # Detection metadata
    detection_method: DetectionMethod
    strategies_used: List[str]  # ["metadata", "commit", "pattern"]
    detection_evidence: Dict  # Strategy-specific evidence

    # Performance metrics
    detection_duration_ms: int

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "is_ai_generated": self.is_ai_generated,
            "confidence": self.confidence,
            "detected_tool": self.detected_tool.value if self.detected_tool else None,
            "detected_model": self.detected_model,
            "detected_model_version": self.detected_model_version,
            "detection_method": self.detection_method.value,
            "strategies_used": self.strategies_used,
            "detection_evidence": self.detection_evidence,
            "detection_duration_ms": self.detection_duration_ms,
        }


class AIDetectionStrategy(ABC):
    """Base class for detection strategies."""

    @abstractmethod
    async def detect(
        self,
        pr_data: dict,
        commits: List[dict],
        diff: str,
    ) -> DetectionResult:
        """
        Detect AI-generated code.

        Args:
            pr_data: GitHub PR object (from webhook payload)
            commits: List of commit objects for this PR
            diff: Unified diff of all changes

        Returns:
            DetectionResult with confidence score
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return strategy name for logging."""
        pass


class AIDetectionService(ABC):
    """Service for orchestrating AI detection."""

    @abstractmethod
    async def detect(
        self,
        pr_data: dict,
        commits: List[dict],
        diff: str,
    ) -> AIDetectionResult:
        """
        Detect if PR contains AI-generated code.

        Args:
            pr_data: GitHub PR object
            commits: List of commits
            diff: Unified diff

        Returns:
            AIDetectionResult with aggregated confidence
        """
        pass
