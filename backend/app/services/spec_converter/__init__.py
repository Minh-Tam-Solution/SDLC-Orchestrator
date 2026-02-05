"""
Spec Converter Service
Sprint 154 - Spec Standard Completion

SDLC 6.0.3 Section 8: Unified Specification Standard

Provides:
- Bidirectional format conversion (BDD ↔ OpenSpec ↔ User Story)
- Intermediate Representation (IR) for deterministic transformations
- AI-assisted natural language to spec generation
- Visual editor support

Architecture: ADR-050
Technical Spec: SPEC-0026
"""

from .models import (
    SpecFormat,
    SpecIR,
    SpecRequirement,
    AcceptanceCriterion,
)
from .spec_converter_service import SpecConverterService

__all__ = [
    "SpecFormat",
    "SpecIR",
    "SpecRequirement",
    "AcceptanceCriterion",
    "SpecConverterService",
]
