"""
=========================================================================
Governance Services - Auto-Generation Layer & Signals Engine
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 2
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Services:
- AutoGenerationService: 4 generators for compliance artifacts
- SignalsEngine: Vibecoding Index calculation (Day 3)
- FeedbackService: Actionable error messages (Day 3)

Zero Mock Policy: Real implementations only
=========================================================================
"""

from app.services.governance.auto_generator import (
    AutoGenerationService,
    IntentGenerator,
    OwnershipGenerator,
    ContextAttachmentGenerator,
    AttestationGenerator,
    GenerationResult,
    FallbackLevel,
    create_auto_generation_service,
    get_auto_generation_service,
)

__all__ = [
    # Main Service
    "AutoGenerationService",
    # Individual Generators
    "IntentGenerator",
    "OwnershipGenerator",
    "ContextAttachmentGenerator",
    "AttestationGenerator",
    # Data Classes
    "GenerationResult",
    "FallbackLevel",
    # Factory Functions
    "create_auto_generation_service",
    "get_auto_generation_service",
]
