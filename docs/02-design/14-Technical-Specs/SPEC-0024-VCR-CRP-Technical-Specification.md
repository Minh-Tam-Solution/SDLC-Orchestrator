# SPEC-0024: VCR/CRP Technical Specification

**Status**: APPROVED
**Version**: 1.0.0
**Date**: February 5, 2026
**Sprint**: 151 (SASE Artifacts Enhancement)
**Author**: Backend Lead
**ADR Reference**: [ADR-048](../01-ADRs/ADR-048-SASE-VCR-CRP-Architecture.md)

---

## Overview

This specification defines the technical implementation details for VCR (Version Controlled Resolution) and CRP (Consultation Request Pack) workflows in SDLC Orchestrator.

---

## 1. Database Schema

### 1.1 VCR Table

```sql
CREATE TABLE version_controlled_resolutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- PR Reference
    pr_number INTEGER,
    pr_url VARCHAR(500),

    -- Content
    title VARCHAR(255) NOT NULL,
    problem_statement TEXT NOT NULL,
    root_cause_analysis TEXT,
    solution_approach TEXT NOT NULL,
    implementation_notes TEXT,

    -- Linkage
    evidence_ids UUID[] DEFAULT '{}',
    adr_ids UUID[] DEFAULT '{}',

    -- AI Attribution
    ai_generated_percentage FLOAT DEFAULT 0.0,
    ai_tools_used VARCHAR[] DEFAULT '{}',
    ai_generation_details JSONB DEFAULT '{}',

    -- Workflow
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'submitted', 'approved', 'rejected')),
    created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,

    -- Indexes
    CONSTRAINT fk_vcr_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes
CREATE INDEX idx_vcr_project ON version_controlled_resolutions(project_id);
CREATE INDEX idx_vcr_status ON version_controlled_resolutions(status);
CREATE INDEX idx_vcr_created_by ON version_controlled_resolutions(created_by_id);
CREATE INDEX idx_vcr_created_at ON version_controlled_resolutions(created_at DESC);
```

### 1.2 CRP Table

```sql
CREATE TABLE consultation_request_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Consultation Details
    title VARCHAR(255) NOT NULL,
    context TEXT NOT NULL,
    question TEXT NOT NULL,
    options_considered JSONB DEFAULT '[]',
    recommended_option VARCHAR(255),

    -- Participants
    requested_by_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    consultant_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Response
    response TEXT,
    decision VARCHAR(20)
        CHECK (decision IN ('approved', 'rejected', 'needs_revision') OR decision IS NULL),

    -- Workflow
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'submitted', 'responded', 'closed')),

    -- Linkage
    adr_id UUID REFERENCES adrs(id) ON DELETE SET NULL,
    evidence_ids UUID[] DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    CONSTRAINT fk_crp_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes
CREATE INDEX idx_crp_project ON consultation_request_packs(project_id);
CREATE INDEX idx_crp_status ON consultation_request_packs(status);
CREATE INDEX idx_crp_consultant ON consultation_request_packs(consultant_id);
CREATE INDEX idx_crp_requested_by ON consultation_request_packs(requested_by_id);
CREATE INDEX idx_crp_created_at ON consultation_request_packs(created_at DESC);
```

---

## 2. Pydantic Schemas

### 2.1 VCR Schemas

```python
# backend/app/schemas/vcr.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

class VCRStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"

class VCRCreate(BaseModel):
    """Schema for creating a new VCR."""
    project_id: UUID
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    title: str = Field(..., max_length=255)
    problem_statement: str
    root_cause_analysis: Optional[str] = None
    solution_approach: str
    implementation_notes: Optional[str] = None
    evidence_ids: List[UUID] = []
    adr_ids: List[UUID] = []
    ai_generated_percentage: float = Field(0.0, ge=0.0, le=1.0)
    ai_tools_used: List[str] = []
    ai_generation_details: dict = {}

class VCRUpdate(BaseModel):
    """Schema for updating a VCR."""
    title: Optional[str] = Field(None, max_length=255)
    problem_statement: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    solution_approach: Optional[str] = None
    implementation_notes: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None
    adr_ids: Optional[List[UUID]] = None
    ai_generated_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)
    ai_tools_used: Optional[List[str]] = None
    ai_generation_details: Optional[dict] = None

class VCRResponse(BaseModel):
    """Schema for VCR API response."""
    id: UUID
    project_id: UUID
    pr_number: Optional[int]
    pr_url: Optional[str]
    title: str
    problem_statement: str
    root_cause_analysis: Optional[str]
    solution_approach: str
    implementation_notes: Optional[str]
    evidence_ids: List[UUID]
    adr_ids: List[UUID]
    ai_generated_percentage: float
    ai_tools_used: List[str]
    ai_generation_details: dict
    status: VCRStatus
    created_by_id: Optional[UUID]
    approved_by_id: Optional[UUID]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True

class VCRAutoGenerateRequest(BaseModel):
    """Request for AI-assisted VCR generation."""
    project_id: UUID
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    context: Optional[str] = None  # Additional context

class VCRAutoGenerateResponse(BaseModel):
    """Response from AI-assisted VCR generation."""
    title: str
    problem_statement: str
    root_cause_analysis: Optional[str]
    solution_approach: str
    implementation_notes: Optional[str]
    ai_confidence: float = Field(..., ge=0.0, le=1.0)

class VCRRejectRequest(BaseModel):
    """Request for rejecting a VCR."""
    reason: str = Field(..., min_length=10)
```

### 2.2 CRP Schemas

```python
# backend/app/schemas/crp.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

class CRPStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RESPONDED = "responded"
    CLOSED = "closed"

class CRPDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class CRPOption(BaseModel):
    """Single option in CRP."""
    name: str
    description: str
    pros: List[str] = []
    cons: List[str] = []

class CRPCreate(BaseModel):
    """Schema for creating a new CRP."""
    project_id: UUID
    title: str = Field(..., max_length=255)
    context: str
    question: str
    options_considered: List[CRPOption] = []
    recommended_option: Optional[str] = None
    consultant_id: Optional[UUID] = None
    evidence_ids: List[UUID] = []

class CRPUpdate(BaseModel):
    """Schema for updating a CRP."""
    title: Optional[str] = Field(None, max_length=255)
    context: Optional[str] = None
    question: Optional[str] = None
    options_considered: Optional[List[CRPOption]] = None
    recommended_option: Optional[str] = None
    consultant_id: Optional[UUID] = None
    evidence_ids: Optional[List[UUID]] = None

class CRPResponse(BaseModel):
    """Schema for CRP API response."""
    id: UUID
    project_id: UUID
    title: str
    context: str
    question: str
    options_considered: List[CRPOption]
    recommended_option: Optional[str]
    requested_by_id: UUID
    consultant_id: Optional[UUID]
    response: Optional[str]
    decision: Optional[CRPDecision]
    status: CRPStatus
    adr_id: Optional[UUID]
    evidence_ids: List[UUID]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    responded_at: Optional[datetime]
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True

class CRPRespondRequest(BaseModel):
    """Request for consultant responding to CRP."""
    response: str
    decision: CRPDecision
    create_adr: bool = False  # Whether to create ADR from this decision

class CRPAIAssistRequest(BaseModel):
    """Request for AI-assisted CRP generation."""
    project_id: UUID
    context: str
    question: str

class CRPAIAssistResponse(BaseModel):
    """Response from AI-assisted CRP generation."""
    clarified_question: str
    options: List[CRPOption]
    recommended_option: str
    rationale: str
    ai_confidence: float = Field(..., ge=0.0, le=1.0)
```

---

## 3. Service Layer

### 3.1 VCR Service

```python
# backend/app/services/vcr_service.py

class VCRService:
    """Business logic for VCR operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: VCRCreate, user_id: UUID) -> VCR:
        """Create new VCR."""
        vcr = VersionControlledResolution(
            **data.model_dump(),
            created_by_id=user_id,
            status=VCRStatus.DRAFT
        )
        self.db.add(vcr)
        await self.db.commit()
        await self.db.refresh(vcr)

        # Track telemetry
        await self._track_event("vcr_created", vcr)

        return vcr

    async def get(self, vcr_id: UUID) -> Optional[VCR]:
        """Get VCR by ID."""
        return await self.db.get(VersionControlledResolution, vcr_id)

    async def list(
        self,
        project_id: UUID,
        status: Optional[VCRStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[VCR]:
        """List VCRs for project with optional status filter."""
        query = select(VersionControlledResolution).where(
            VersionControlledResolution.project_id == project_id
        )
        if status:
            query = query.where(VersionControlledResolution.status == status)
        query = query.order_by(desc(VersionControlledResolution.created_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, vcr_id: UUID, data: VCRUpdate) -> Optional[VCR]:
        """Update VCR (only if draft status)."""
        vcr = await self.get(vcr_id)
        if not vcr or vcr.status != VCRStatus.DRAFT:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(vcr, key, value)

        await self.db.commit()
        await self.db.refresh(vcr)
        return vcr

    async def submit(self, vcr_id: UUID) -> Optional[VCR]:
        """Submit VCR for approval."""
        vcr = await self.get(vcr_id)
        if not vcr or vcr.status != VCRStatus.DRAFT:
            return None

        vcr.status = VCRStatus.SUBMITTED
        vcr.submitted_at = datetime.utcnow()
        await self.db.commit()

        # Track telemetry
        await self._track_event("vcr_submitted", vcr)

        # Notify CTO/CEO
        await self._notify_approvers(vcr)

        return vcr

    async def approve(self, vcr_id: UUID, approver_id: UUID) -> Optional[VCR]:
        """Approve VCR (CTO/CEO only)."""
        vcr = await self.get(vcr_id)
        if not vcr or vcr.status != VCRStatus.SUBMITTED:
            return None

        vcr.status = VCRStatus.APPROVED
        vcr.approved_by_id = approver_id
        vcr.approved_at = datetime.utcnow()
        await self.db.commit()

        # Track telemetry
        await self._track_event("vcr_approved", vcr)

        # Store in Evidence Vault
        await self._store_in_evidence_vault(vcr)

        return vcr

    async def reject(
        self,
        vcr_id: UUID,
        approver_id: UUID,
        reason: str
    ) -> Optional[VCR]:
        """Reject VCR with reason."""
        vcr = await self.get(vcr_id)
        if not vcr or vcr.status != VCRStatus.SUBMITTED:
            return None

        vcr.status = VCRStatus.REJECTED
        vcr.approved_by_id = approver_id
        vcr.rejection_reason = reason
        await self.db.commit()

        # Track telemetry
        await self._track_event("vcr_rejected", vcr)

        return vcr

    async def auto_generate(
        self,
        request: VCRAutoGenerateRequest,
        user_id: UUID
    ) -> VCRAutoGenerateResponse:
        """AI-assisted VCR generation."""
        # Gather context
        context = await self._gather_pr_context(
            request.project_id,
            request.pr_number,
            request.pr_url,
            request.context
        )

        # Call AI Council
        ai_council = get_ai_council_service(self.db)
        draft = await ai_council.generate_vcr_draft(context)

        return VCRAutoGenerateResponse(
            title=draft["title"],
            problem_statement=draft["problem_statement"],
            root_cause_analysis=draft.get("root_cause_analysis"),
            solution_approach=draft["solution_approach"],
            implementation_notes=draft.get("implementation_notes"),
            ai_confidence=draft.get("confidence", 0.7)
        )
```

### 3.2 CRP Service

```python
# backend/app/services/crp_service.py

class CRPService:
    """Business logic for CRP operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CRPCreate, user_id: UUID) -> CRP:
        """Create new CRP."""
        crp = ConsultationRequestPack(
            **data.model_dump(),
            requested_by_id=user_id,
            status=CRPStatus.DRAFT
        )
        self.db.add(crp)
        await self.db.commit()
        await self.db.refresh(crp)

        # Track telemetry
        await self._track_event("crp_created", crp)

        return crp

    async def submit(self, crp_id: UUID) -> Optional[CRP]:
        """Submit CRP to consultant."""
        crp = await self.get(crp_id)
        if not crp or crp.status != CRPStatus.DRAFT:
            return None

        if not crp.consultant_id:
            raise ValueError("Consultant must be assigned before submitting")

        crp.status = CRPStatus.SUBMITTED
        crp.submitted_at = datetime.utcnow()
        await self.db.commit()

        # Track telemetry
        await self._track_event("crp_submitted", crp)

        # Notify consultant
        await self._notify_consultant(crp)

        return crp

    async def respond(
        self,
        crp_id: UUID,
        consultant_id: UUID,
        request: CRPRespondRequest
    ) -> Optional[CRP]:
        """Consultant responds to CRP."""
        crp = await self.get(crp_id)
        if not crp or crp.status != CRPStatus.SUBMITTED:
            return None

        if crp.consultant_id != consultant_id:
            raise PermissionError("Only assigned consultant can respond")

        crp.response = request.response
        crp.decision = request.decision
        crp.status = CRPStatus.RESPONDED
        crp.responded_at = datetime.utcnow()

        # Create ADR if requested
        if request.create_adr:
            adr = await self._create_adr_from_crp(crp)
            crp.adr_id = adr.id

        await self.db.commit()

        # Track telemetry
        await self._track_event("crp_responded", crp)

        # Notify requester
        await self._notify_requester(crp)

        return crp

    async def ai_assist(
        self,
        request: CRPAIAssistRequest,
        user_id: UUID
    ) -> CRPAIAssistResponse:
        """AI-assisted CRP generation."""
        # Call AI Council for question clarification
        ai_council = get_ai_council_service(self.db)

        # Step 1: Clarify question
        clarified = await ai_council.clarify_question(
            request.context,
            request.question
        )

        # Step 2: Generate options
        options = await ai_council.generate_options(
            request.project_id,
            clarified["question"]
        )

        # Step 3: Recommend option
        recommendation = await ai_council.recommend_option(
            options,
            request.context
        )

        return CRPAIAssistResponse(
            clarified_question=clarified["question"],
            options=[CRPOption(**opt) for opt in options],
            recommended_option=recommendation["option"],
            rationale=recommendation["rationale"],
            ai_confidence=recommendation.get("confidence", 0.7)
        )
```

---

## 4. API Endpoints

### 4.1 VCR Routes

```python
# backend/app/api/routes/vcr.py

router = APIRouter(prefix="/vcr", tags=["VCR"])

@router.post("", response_model=VCRResponse)
async def create_vcr(
    data: VCRCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VCRResponse:
    """Create a new VCR."""
    service = VCRService(db)
    vcr = await service.create(data, current_user.id)
    return VCRResponse.model_validate(vcr)

@router.get("/{vcr_id}", response_model=VCRResponse)
async def get_vcr(
    vcr_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VCRResponse:
    """Get VCR by ID."""
    service = VCRService(db)
    vcr = await service.get(vcr_id)
    if not vcr:
        raise HTTPException(status_code=404, detail="VCR not found")
    return VCRResponse.model_validate(vcr)

@router.get("", response_model=List[VCRResponse])
async def list_vcrs(
    project_id: UUID,
    status: Optional[VCRStatus] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[VCRResponse]:
    """List VCRs for project."""
    service = VCRService(db)
    vcrs = await service.list(project_id, status, limit, offset)
    return [VCRResponse.model_validate(v) for v in vcrs]

@router.put("/{vcr_id}", response_model=VCRResponse)
async def update_vcr(
    vcr_id: UUID,
    data: VCRUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VCRResponse:
    """Update VCR (draft only)."""
    service = VCRService(db)
    vcr = await service.update(vcr_id, data)
    if not vcr:
        raise HTTPException(status_code=400, detail="Cannot update non-draft VCR")
    return VCRResponse.model_validate(vcr)

@router.post("/{vcr_id}/submit", response_model=VCRResponse)
async def submit_vcr(
    vcr_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VCRResponse:
    """Submit VCR for approval."""
    service = VCRService(db)
    vcr = await service.submit(vcr_id)
    if not vcr:
        raise HTTPException(status_code=400, detail="Cannot submit VCR")
    return VCRResponse.model_validate(vcr)

@router.post("/{vcr_id}/approve", response_model=VCRResponse)
async def approve_vcr(
    vcr_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["cto", "ceo"]))
) -> VCRResponse:
    """Approve VCR (CTO/CEO only)."""
    service = VCRService(db)
    vcr = await service.approve(vcr_id, current_user.id)
    if not vcr:
        raise HTTPException(status_code=400, detail="Cannot approve VCR")
    return VCRResponse.model_validate(vcr)

@router.post("/{vcr_id}/reject", response_model=VCRResponse)
async def reject_vcr(
    vcr_id: UUID,
    request: VCRRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["cto", "ceo"]))
) -> VCRResponse:
    """Reject VCR (CTO/CEO only)."""
    service = VCRService(db)
    vcr = await service.reject(vcr_id, current_user.id, request.reason)
    if not vcr:
        raise HTTPException(status_code=400, detail="Cannot reject VCR")
    return VCRResponse.model_validate(vcr)

@router.post("/auto-generate", response_model=VCRAutoGenerateResponse)
async def auto_generate_vcr(
    request: VCRAutoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VCRAutoGenerateResponse:
    """AI-assisted VCR generation."""
    service = VCRService(db)
    return await service.auto_generate(request, current_user.id)
```

---

## 5. Telemetry Events

### 5.1 VCR Events

```yaml
vcr_created:
  properties:
    vcr_id: UUID
    project_id: UUID
    pr_number: int (optional)
    ai_tools_count: int

vcr_submitted:
  properties:
    vcr_id: UUID
    project_id: UUID
    time_to_submit_seconds: int

vcr_approved:
  properties:
    vcr_id: UUID
    project_id: UUID
    approver_id: UUID
    time_to_approve_seconds: int

vcr_rejected:
  properties:
    vcr_id: UUID
    project_id: UUID
    rejection_reason_length: int
```

### 5.2 CRP Events

```yaml
crp_created:
  properties:
    crp_id: UUID
    project_id: UUID
    options_count: int

crp_submitted:
  properties:
    crp_id: UUID
    project_id: UUID
    consultant_id: UUID

crp_responded:
  properties:
    crp_id: UUID
    project_id: UUID
    decision: string
    response_time_hours: float
    created_adr: boolean
```

---

## 6. Performance Requirements

| Operation | Target | SLA |
|-----------|--------|-----|
| Create VCR | <200ms | p95 |
| List VCRs | <100ms | p95 |
| Submit VCR | <300ms | p95 |
| Approve/Reject | <200ms | p95 |
| Auto-generate | <15s | p95 |
| AI Assist (CRP) | <10s | p95 |

---

## 7. Test Coverage Requirements

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| VCR Model | 10 | - |
| VCR Service | 15 | 8 |
| VCR API | - | 8 |
| CRP Model | 10 | - |
| CRP Service | 15 | 8 |
| CRP API | - | 8 |
| **Total** | **50** | **32** |

---

## 8. Migration Plan

### 8.1 Alembic Migration

```python
# s151_001_vcr_crp_tables.py

def upgrade():
    # Create VCR table
    op.create_table(
        "version_controlled_resolutions",
        # ... columns from schema above
    )

    # Create CRP table
    op.create_table(
        "consultation_request_packs",
        # ... columns from schema above
    )

    # Create indexes
    # ... indexes from schema above

def downgrade():
    op.drop_table("consultation_request_packs")
    op.drop_table("version_controlled_resolutions")
```

---

## 9. References

- [ADR-048: SASE VCR/CRP Architecture](../01-ADRs/ADR-048-SASE-VCR-CRP-Architecture.md)
- [Sprint 151 Plan](../../04-build/02-Sprint-Plans/SPRINT-151-SASE-ARTIFACTS.md)
- [SDLC Enterprise Framework - SASE](../../SDLC-Enterprise-Framework/)
