"""
=========================================================================
Context Authority Engine V1 - DEPRECATED FACADE
SDLC Orchestrator - Sprint 173 (Governance Loop Completion)

Version: 1.0.0-DEPRECATED
Date: February 15, 2026
Status: DEPRECATED - Use context_authority_v2.py instead
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0.5 Quality Assurance System

Sprint 173 Merge (Strangler Fig):
- All V1 code moved to context_authority_v2.py (unified module)
- This file is a thin re-export facade for backward compatibility
- Will be removed in Sprint 174

Migration:
  BEFORE: from app.services.governance.context_authority import ...
  AFTER:  from app.services.governance.context_authority_v2 import ...
=========================================================================
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "context_authority module is deprecated. "
    "Import from context_authority_v2 instead. "
    "This facade will be removed in Sprint 174.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the unified V2 module
from app.services.governance.context_authority_v2 import (  # noqa: E402, F401
    # Enums
    ContextViolationType,
    ViolationSeverity,
    ADRStatus,
    # Data Classes
    ADR,
    DesignSpec,
    AgentsMdInfo,
    ModuleAnnotation,
    ContextViolation,
    ContextValidationResult,
    CodeSubmission,
    # Engine
    ContextAuthorityEngineV1,
    # Factory Functions
    create_context_authority_engine,
    get_context_authority_engine,
)

__all__ = [
    "ContextViolationType",
    "ViolationSeverity",
    "ADRStatus",
    "ADR",
    "DesignSpec",
    "AgentsMdInfo",
    "ModuleAnnotation",
    "ContextViolation",
    "ContextValidationResult",
    "CodeSubmission",
    "ContextAuthorityEngineV1",
    "create_context_authority_engine",
    "get_context_authority_engine",
]
