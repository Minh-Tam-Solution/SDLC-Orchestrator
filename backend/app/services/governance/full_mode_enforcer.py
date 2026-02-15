"""
=========================================================================
FULL Mode Enforcer - DEPRECATED FACADE
SDLC Orchestrator - Sprint 173 (Governance Loop Completion)

Version: 1.0.0-DEPRECATED
Date: February 15, 2026
Status: DEPRECATED - Use enforcement_strategy.py instead
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0.5 Quality Assurance System

Sprint 173 Merge (Strategy Pattern):
- All enforcer code moved to enforcement_strategy.py (unified module)
- This file is a thin re-export facade for backward compatibility
- Will be removed in Sprint 174

Migration:
  BEFORE: from app.services.governance.full_mode_enforcer import ...
  AFTER:  from app.services.governance.enforcement_strategy import ...
=========================================================================
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "full_mode_enforcer module is deprecated. "
    "Import from enforcement_strategy instead. "
    "This facade will be removed in Sprint 174.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the unified strategy module
from app.services.governance.enforcement_strategy import (  # noqa: E402, F401
    # Enums from soft
    EnforcementAction,
    ExemptionType,
    OverrideAuthority,
    # FULL mode enums
    ApprovalRequirement,
    ApprovalStatus,
    # Data Classes from soft
    ExemptionResult,
    BlockRuleResult,
    WarnRuleResult,
    EnforcementResult,
    # FULL mode data classes
    ApprovalRequest,
    CEOTimeEntry,
    FullModeEnforcementResult,
    # Strategy (aliased as old class name)
    FullEnforcement as FullModeEnforcer,
    # Soft strategy (aliased as old class name)
    SoftEnforcement as SoftModeEnforcer,
    # Factory Functions
    create_full_enforcement as create_full_mode_enforcer,
    get_full_enforcement as get_full_mode_enforcer,
)

__all__ = [
    "EnforcementAction",
    "ExemptionType",
    "OverrideAuthority",
    "ApprovalRequirement",
    "ApprovalStatus",
    "ExemptionResult",
    "BlockRuleResult",
    "WarnRuleResult",
    "EnforcementResult",
    "ApprovalRequest",
    "CEOTimeEntry",
    "FullModeEnforcementResult",
    "FullModeEnforcer",
    "SoftModeEnforcer",
    "create_full_mode_enforcer",
    "get_full_mode_enforcer",
]
