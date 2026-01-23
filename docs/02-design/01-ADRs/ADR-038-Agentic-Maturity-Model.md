# ADR-038: Agentic Maturity Model (L0-L3)

**Status**: APPROVED
**Date**: January 23, 2026
**Sprint**: Sprint 104
**Deciders**: CTO, Backend Lead

---

## Context

Organizations adopting AI-assisted development need to understand their maturity level:
- What AI capabilities are they using?
- What governance controls are appropriate?
- How do they progress to more automation?

SDLC Framework 5.2.0 defines the Agentic Maturity Model:

```
┌──────────────────────────────────────────────────────────────┐
│                  AGENTIC MATURITY MODEL                      │
├──────────────────────────────────────────────────────────────┤
│  L0: MANUAL (0-20) - Human writes all code                  │
│  L1: ASSISTANT (21-50) - AI suggests, human decides         │
│  L2: ORCHESTRATED (51-80) - Agent workflows, human oversight│
│  L3: AUTONOMOUS (81-100) - Agents act, human audits         │
└──────────────────────────────────────────────────────────────┘
```

## Decision

Implement Agentic Maturity Assessment with the following architecture:

### 1. Maturity Factors

Score is calculated from enabled features:

| Factor | Points | Level |
|--------|--------|-------|
| Planning Sub-agent | 30 | L2 |
| CRP (Consultation Request Protocol) | 20 | L2 |
| Evidence Vault | 15 | L2 |
| Automated Testing | 15 | L1 |
| GitHub Check Runs | 10 | L1 |
| Policy Enforcement | 10 | L2 |
| **Total** | **100** | |

### 2. Level Mapping

```python
def _map_score_to_level(score: int) -> MaturityLevel:
    if score >= 81:
        return MaturityLevel.L3_AUTONOMOUS
    elif score >= 51:
        return MaturityLevel.L2_ORCHESTRATED
    elif score >= 21:
        return MaturityLevel.L1_ASSISTANT
    else:
        return MaturityLevel.L0_MANUAL
```

### 3. API Endpoints

```
GET /api/v1/maturity/{project_id}        # Get latest assessment
POST /api/v1/maturity/{project_id}/assess # Fresh assessment
GET /api/v1/maturity/{project_id}/history # Assessment history
GET /api/v1/maturity/org/{org_id}         # Org-wide report
GET /api/v1/maturity/levels               # Level definitions
```

### 4. Database Schema

```sql
CREATE TABLE maturity_assessments (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    level VARCHAR(10) NOT NULL,  -- L0, L1, L2, L3
    score INTEGER NOT NULL,       -- 0-100
    enabled_features JSON,
    disabled_features JSON,
    recommendations JSON,
    assessed_at TIMESTAMP
);
```

### 5. Recommendations Engine

Level-specific recommendations for progression:

**L0 → L1:**
- Enable GitHub Copilot
- Set up automated linting
- Configure basic CI/CD

**L1 → L2:**
- Enable Planning Sub-agent
- Set up Evidence Vault
- Configure CRP

**L2 → L3:**
- Enable autonomous PR creation
- Self-healing CI/CD
- Full compliance automation

## Consequences

**Positive:**
- Clear visibility into AI adoption level
- Actionable recommendations for progression
- Compliance tracking (which level requires what controls)
- Benchmark against other projects/orgs

**Negative:**
- Assessment accuracy depends on config detection
- May need manual verification for some factors

## Migration Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATURITY PROGRESSION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  L0 ────► L1 ────► L2 ────► L3                                  │
│  Manual   Assistant  Orchestrated  Autonomous                    │
│                                                                  │
│  Typical timeline: 3-6 months per level                         │
│                                                                  │
│  Prerequisites for each level:                                   │
│  L1: AI tools, basic CI/CD                                      │
│  L2: Sub-agents, CRP, Evidence Vault                            │
│  L3: Full automation, audit-only oversight                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## References

- Sprint 104: Agentic Maturity L0-L3 + Documentation
- SDLC Framework 5.2.0, 03-AI-GOVERNANCE/02-Agentic-Maturity-Model.md
- ADR-029: AGENTS.md Integration Strategy
