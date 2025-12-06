# ADR-011: Context-Aware Stage Requirements Engine

**Status**: APPROVED
**Date**: December 3, 2025
**Decision Makers**: CTO, CPO (joint review)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 4.9.1

---

## Context

SDLC 4.9.1 Framework định nghĩa 10 stages với nhiều requirements cho mỗi stage. Tuy nhiên, không phải tất cả requirements đều phù hợp cho mọi loại dự án:

1. **Startup nhỏ (2-5 người)**: Cần lightweight process, skip enterprise gates
2. **Enterprise (50+ người)**: Cần full compliance, audit trails, security gates
3. **Regulated industry (Healthcare, Finance)**: Cần mandatory compliance gates
4. **Internal tools**: Có thể skip market validation gates

**Problem Statement**: CEO có thể áp dụng SDLC Framework hiệu quả vì hiểu context. PM/Tech Lead khác không biết khi nào nên skip/enforce requirements nào.

**Goal**: Encode "CEO's brain" vào hệ thống để bất kỳ PM nào cũng có thể áp dụng đúng requirements cho đúng context.

---

## Decision

Implement **Context-Aware Requirements Engine** với 3-tier classification:

### Tier Classification

```yaml
MANDATORY (Red):
  - Không thể skip dù bất kỳ context nào
  - Ví dụ: Security review cho production code
  - Enforcement: Block gate passage

RECOMMENDED (Yellow):
  - Nên thực hiện nhưng có thể skip với justification
  - Ví dụ: Performance testing cho internal tools
  - Enforcement: Warning + require justification

OPTIONAL (Gray):
  - Nice-to-have, depends on project scale
  - Ví dụ: Load testing cho MVP <1000 users
  - Enforcement: Information only
```

### Context Dimensions

```yaml
1. Project Scale:
   - small: 1-5 team members
   - medium: 6-20 team members
   - large: 21-50 team members
   - enterprise: 50+ team members

2. Team Structure:
   - solo: Single developer
   - small_team: 2-5 developers
   - cross_functional: Multiple disciplines
   - distributed: Multiple locations/timezones

3. Industry:
   - general: No specific regulations
   - finance: PCI-DSS, SOX compliance
   - healthcare: HIPAA, FDA requirements
   - government: FedRAMP, security clearance
   - education: FERPA compliance

4. Risk Profile:
   - low: Internal tools, experiments
   - medium: Customer-facing, non-critical
   - high: Production systems, revenue-impacting
   - critical: Life-safety, financial transactions

5. Software Development Practices:
   - methodology: Waterfall, Agile, Kanban, DevOps, Lean
   - team_maturity: CMM Level 1-5
   - release_cadence: Daily, Weekly, Monthly, Quarterly
   - tech_ecosystem: Web, Mobile, Embedded, Enterprise
```

---

## Architecture Design

### 1. Data Model

```python
# models/stage_requirements.py
from sqlalchemy import Column, String, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship

class StageRequirement(Base):
    """Stage requirement with context-aware classification"""
    __tablename__ = "stage_requirements"

    id = Column(String(50), primary_key=True)  # e.g., "STG00-REQ-001"
    stage_id = Column(String(10), nullable=False)  # e.g., "00", "01"
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Default classification (can be overridden by context)
    default_tier = Column(
        Enum("MANDATORY", "RECOMMENDED", "OPTIONAL"),
        default="RECOMMENDED"
    )

    # Evidence requirements
    evidence_types = Column(JSON)  # ["document", "approval", "test_report"]
    evidence_templates = Column(JSON)  # Template IDs for each evidence type

    # Context rules (JSON for flexibility)
    context_rules = Column(JSON)
    """
    Example context_rules:
    {
        "upgrade_to_mandatory": {
            "conditions": [
                {"dimension": "industry", "values": ["healthcare", "finance"]},
                {"dimension": "risk_profile", "values": ["critical"]}
            ],
            "logic": "OR"
        },
        "downgrade_to_optional": {
            "conditions": [
                {"dimension": "project_scale", "values": ["small"]},
                {"dimension": "risk_profile", "values": ["low"]}
            ],
            "logic": "AND"
        }
    }
    """

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_by = Column(String(100))


class RequirementOverride(Base):
    """Project-specific requirement overrides"""
    __tablename__ = "requirement_overrides"

    id = Column(UUID, primary_key=True, default=uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(String(50), ForeignKey("stage_requirements.id"))

    # Override details
    original_tier = Column(Enum("MANDATORY", "RECOMMENDED", "OPTIONAL"))
    override_tier = Column(Enum("MANDATORY", "RECOMMENDED", "OPTIONAL"))
    justification = Column(Text, nullable=False)

    # Approval chain
    requested_by = Column(UUID, ForeignKey("users.id"))
    approved_by = Column(UUID, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Requirements Engine Service

```python
# services/requirements_engine.py
from typing import List, Dict, Optional
from enum import Enum

class RequirementTier(Enum):
    MANDATORY = "MANDATORY"
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"

class RequirementsEngine:
    """Context-aware requirements classification engine"""

    def __init__(self, db: Session):
        self.db = db
        self.cache = RedisCache()

    async def get_stage_requirements(
        self,
        project_id: str,
        stage_id: str
    ) -> List[Dict]:
        """Get requirements for a stage with context-aware classification"""

        # Get project profile
        project = await self._get_project_profile(project_id)

        # Get base requirements for stage
        requirements = await self._get_base_requirements(stage_id)

        # Apply context rules
        classified = []
        for req in requirements:
            tier = self._classify_requirement(req, project)

            # Check for project-specific overrides
            override = await self._get_override(project_id, req.id)
            if override:
                tier = RequirementTier(override.override_tier)

            classified.append({
                "id": req.id,
                "name": req.name,
                "description": req.description,
                "tier": tier.value,
                "original_tier": req.default_tier,
                "is_overridden": override is not None,
                "override_justification": override.justification if override else None,
                "evidence_required": req.evidence_types,
                "templates": req.evidence_templates
            })

        return classified

    def _classify_requirement(
        self,
        requirement: StageRequirement,
        project: ProjectProfile
    ) -> RequirementTier:
        """Apply context rules to classify requirement"""

        rules = requirement.context_rules or {}
        current_tier = RequirementTier(requirement.default_tier)

        # Check upgrade conditions
        if "upgrade_to_mandatory" in rules:
            if self._evaluate_conditions(
                rules["upgrade_to_mandatory"],
                project
            ):
                return RequirementTier.MANDATORY

        # Check downgrade conditions
        if "downgrade_to_optional" in rules:
            if self._evaluate_conditions(
                rules["downgrade_to_optional"],
                project
            ):
                return RequirementTier.OPTIONAL

        return current_tier

    def _evaluate_conditions(
        self,
        rule: Dict,
        project: ProjectProfile
    ) -> bool:
        """Evaluate context rule conditions"""

        conditions = rule.get("conditions", [])
        logic = rule.get("logic", "AND")

        results = []
        for condition in conditions:
            dimension = condition["dimension"]
            allowed_values = condition["values"]

            # Get project's value for this dimension
            project_value = getattr(project, dimension, None)

            # Check if matches
            matches = project_value in allowed_values
            results.append(matches)

        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)

        return False

    async def request_override(
        self,
        project_id: str,
        requirement_id: str,
        new_tier: RequirementTier,
        justification: str,
        requested_by: str
    ) -> RequirementOverride:
        """Request to override a requirement's tier"""

        requirement = await self._get_requirement(requirement_id)

        # Validate: Cannot downgrade MANDATORY without approval
        if requirement.default_tier == "MANDATORY" and new_tier != RequirementTier.MANDATORY:
            # Requires CTO/Security Lead approval
            return await self._create_pending_override(
                project_id=project_id,
                requirement_id=requirement_id,
                new_tier=new_tier,
                justification=justification,
                requested_by=requested_by,
                requires_approval=["CTO", "SECURITY_LEAD"]
            )

        # Auto-approve for RECOMMENDED/OPTIONAL changes
        override = RequirementOverride(
            project_id=project_id,
            requirement_id=requirement_id,
            original_tier=requirement.default_tier,
            override_tier=new_tier.value,
            justification=justification,
            requested_by=requested_by,
            approved_by=requested_by,  # Self-approved
            approved_at=datetime.utcnow()
        )

        self.db.add(override)
        await self.db.commit()

        # Audit log
        await self._audit_override(override)

        return override
```

### 3. API Endpoints

```python
# api/routes/requirements.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/requirements", tags=["Requirements"])

@router.get("/stages/{stage_id}")
async def get_stage_requirements(
    stage_id: str,
    project_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[RequirementResponse]:
    """Get context-aware requirements for a stage"""

    engine = RequirementsEngine(db)
    requirements = await engine.get_stage_requirements(project_id, stage_id)

    return requirements

@router.post("/overrides")
async def request_override(
    request: OverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> OverrideResponse:
    """Request to override a requirement's tier"""

    # Check permission
    if not await has_permission(current_user, "requirements.override"):
        raise HTTPException(403, "Permission denied")

    engine = RequirementsEngine(db)
    override = await engine.request_override(
        project_id=request.project_id,
        requirement_id=request.requirement_id,
        new_tier=request.new_tier,
        justification=request.justification,
        requested_by=current_user.id
    )

    return override

@router.get("/matrix")
async def get_requirements_matrix(
    project_id: str = Query(...),
    db: Session = Depends(get_db)
) -> RequirementsMatrixResponse:
    """Get full requirements matrix for all stages"""

    engine = RequirementsEngine(db)
    matrix = {}

    for stage_id in ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]:
        matrix[stage_id] = await engine.get_stage_requirements(project_id, stage_id)

    return {
        "project_id": project_id,
        "matrix": matrix,
        "summary": {
            "total_requirements": sum(len(reqs) for reqs in matrix.values()),
            "mandatory": sum(
                len([r for r in reqs if r["tier"] == "MANDATORY"])
                for reqs in matrix.values()
            ),
            "recommended": sum(
                len([r for r in reqs if r["tier"] == "RECOMMENDED"])
                for reqs in matrix.values()
            ),
            "optional": sum(
                len([r for r in reqs if r["tier"] == "OPTIONAL"])
                for reqs in matrix.values()
            )
        }
    }
```

---

## Consequences

### Positive

1. **Democratized Expertise**: Any PM can apply CEO-level governance
2. **Reduced Friction**: Small teams get lightweight process automatically
3. **Compliance Assurance**: Regulated industries get mandatory gates
4. **Audit Trail**: All overrides tracked with justification
5. **Flexibility**: Project-specific customization with approval

### Negative

1. **Complexity**: More rules to maintain and test
2. **Learning Curve**: Team needs to understand tier system
3. **Override Abuse**: Risk of too many exceptions

### Risks

1. **Rule Conflicts**: Multiple conditions may produce unexpected results
   - **Mitigation**: Explicit priority order (MANDATORY > upgrade > downgrade)

2. **Stale Rules**: Context may change but rules don't update
   - **Mitigation**: Quarterly rule review with CTO

---

## Approval

| Role | Name | Decision | Date | Comment |
|------|------|----------|------|---------|
| **CTO** | [CTO Name] | ✅ APPROVED | Dec 3, 2025 | Encodes governance expertise |
| **CPO** | [CPO Name] | ✅ APPROVED | Dec 3, 2025 | Improves PM productivity |

---

**Decision**: **APPROVED** - Context-Aware Requirements Engine

**Priority**: **HIGH** - Core AI Governance feature

**Timeline**: Sprint 29 (AI Governance & Docs)
