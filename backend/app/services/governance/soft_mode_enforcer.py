"""
=========================================================================
SOFT Mode Enforcer - DEPRECATED FACADE
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
  BEFORE: from app.services.governance.soft_mode_enforcer import ...
  AFTER:  from app.services.governance.enforcement_strategy import ...
=========================================================================
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "soft_mode_enforcer module is deprecated. "
    "Import from enforcement_strategy instead. "
    "This facade will be removed in Sprint 174.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the unified strategy module
from app.services.governance.enforcement_strategy import (  # noqa: E402, F401
    # Enums
    EnforcementAction,
    ExemptionType,
    OverrideAuthority,
    # Data Classes
    ExemptionResult,
    BlockRuleResult,
    WarnRuleResult,
    EnforcementResult,
    # Strategy (aliased as old class name)
    SoftEnforcement as SoftModeEnforcer,
    # Factory Functions
    create_soft_enforcement as create_soft_mode_enforcer,
    get_soft_enforcement as get_soft_mode_enforcer,
)

__all__ = [
    "EnforcementAction",
    "ExemptionType",
    "OverrideAuthority",
    "ExemptionResult",
    "BlockRuleResult",
    "WarnRuleResult",
    "EnforcementResult",
    "SoftModeEnforcer",
    "create_soft_mode_enforcer",
    "get_soft_mode_enforcer",
]
