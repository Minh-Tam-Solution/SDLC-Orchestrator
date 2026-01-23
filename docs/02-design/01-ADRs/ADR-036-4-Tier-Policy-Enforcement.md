# ADR-036: 4-Tier Policy Enforcement

**Status**: APPROVED
**Date**: January 23, 2026
**Sprint**: Sprint 102-104
**Deciders**: CTO, Backend Lead

---

## Context

SDLC Framework 5.2.0 introduces 4-Tier Classification for graduated governance:
- LITE: 1-2 people, advisory only
- STANDARD: 3-10 people, soft enforcement
- PROFESSIONAL: 10-50 people, hard enforcement
- ENTERPRISE: 50+ people, zero tolerance

We need a policy enforcement mechanism that adapts to project tier.

## Decision

Implement 4-Tier Policy Enforcement with the following architecture:

### 1. Tier-Based Policy Packs

Each tier has a policy pack with different enforcement modes:

```python
TIER_POLICIES = {
    PolicyTier.LITE: {
        "enforcement_mode": "advisory",
        "block_on_failure": False,
        "required_checks": ["syntax_validation"],
    },
    PolicyTier.STANDARD: {
        "enforcement_mode": "soft",
        "block_on_failure": False,
        "required_checks": ["syntax_validation", "basic_security"],
    },
    PolicyTier.PROFESSIONAL: {
        "enforcement_mode": "hard",
        "block_on_failure": True,
        "required_checks": ["syntax_validation", "security_scan", "context_validation", "test_coverage"],
    },
    PolicyTier.ENTERPRISE: {
        "enforcement_mode": "strict",
        "block_on_failure": True,
        "required_checks": ["all"],
    },
}
```

### 2. MRP 5-Point Validation

Merge Readiness Protocol (MRP) checks vary by tier:

| Check | LITE | STANDARD | PRO | ENT |
|-------|------|----------|-----|-----|
| Evidence complete | ❌ | ⚠️ | ✅ | ✅ |
| Tests passing | ❌ | ⚠️ | ✅ | ✅ |
| SAST clean | ❌ | ❌ | ✅ | ✅ |
| Context <60 lines | ❌ | ❌ | ⚠️ | ✅ |
| VCR approved | ❌ | ❌ | ⚠️ | ✅ |

### 3. Implementation

- `PolicyEnforcementService`: Evaluates policies per tier
- `MRPValidationService`: 5-point validation per tier
- Database: `policy_pack_tier` column on projects table

## Consequences

**Positive:**
- Graduated governance (startups vs enterprises)
- Flexible enforcement without breaking existing workflows
- Clear upgrade path (LITE → STANDARD → PRO → ENT)

**Negative:**
- More complex policy evaluation logic
- Need to maintain 4 policy configurations

## References

- Sprint 102: MRP/VCR 5-Point + 4-Tier Enforcement
- SDLC Framework 5.2.0, Section 02-GOVERN
