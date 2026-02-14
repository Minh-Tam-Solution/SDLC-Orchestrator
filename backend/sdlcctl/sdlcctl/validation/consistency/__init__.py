"""Stage consistency validation module.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.

This module provides cross-stage consistency validation to ensure
alignment between Planning (Stage 01), Design (Stage 02),
Integrate (Stage 03), and Build (Stage 04) artifacts.

Usage:
    from sdlcctl.validation.consistency import ConsistencyEngine

    engine = ConsistencyEngine.from_paths(
        stage_01=Path("docs/01-planning/"),
        stage_02=Path("docs/02-design/"),
        stage_03=Path("docs/03-integrate/"),
        stage_04=Path("backend/app/"),
        tier=Tier.PROFESSIONAL,
    )
    result = engine.validate()
"""

from .engine import ConsistencyEngine
from .models import (
    ConsistencyConfig,
    ConsistencyResult,
    ConsistencyRule,
    ConsistencyStatus,
    ConsistencyViolation,
    StageConsistencyResult,
)
from .report import ConsistencyReportFormatter

__all__ = [
    # Engine
    "ConsistencyEngine",
    # Models
    "ConsistencyConfig",
    "ConsistencyResult",
    "ConsistencyRule",
    "ConsistencyStatus",
    "ConsistencyViolation",
    "StageConsistencyResult",
    # Report
    "ConsistencyReportFormatter",
]
