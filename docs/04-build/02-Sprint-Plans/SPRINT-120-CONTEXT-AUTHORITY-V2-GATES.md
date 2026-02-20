# Sprint 120: Context Authority V2 + Gates Engine Core

**Dates**: February 3-14, 2026 (10 working days)
**Status**: 📋 PLANNED
**Total Estimated LOC**: ~3,500
**Framework**: SDLC 6.1.0

---

## Executive Summary

Sprint 120 implements SPEC-0011 (Context Authority V2) and begins Gates Engine development. This dual-track approach maximizes delivery while maintaining quality standards.

### Sprint Objective

```
PRIMARY: Enable gate-aware dynamic context for AI-assisted development
SECONDARY: Establish Gates Engine foundation for G0-G4 evaluation
```

---

## Day 0: Framework Submodule Update (Carried from Sprint 119)

**Date**: February 3, 2026 (Morning)
**Duration**: 2 hours
**Status**: ⏳ PENDING (awaiting Framework v6.0.5 tag)

### Tasks

| Task | Description | Est. Time |
|------|-------------|-----------|
| Check v6.0.5 tag | `cd SDLC-Enterprise-Framework && git fetch --tags` | 5 min |
| Update submodule | `git submodule update --remote --merge` | 10 min |
| Verify specs | Confirm 20 SPEC files present | 15 min |
| Update CLAUDE.md | Change 5.3.0 → 6.0.5 references | 30 min |
| Test CLI | `sdlcctl spec validate` against new specs | 30 min |
| Commit | Submodule pointer update | 10 min |

### Contingency

If v6.0.5 tag NOT available by Feb 3:
- Proceed with Sprint 120 Track A/B
- Revisit submodule update Feb 5 or Feb 7
- No functional impact (Orchestrator already 6.0-ready)

---

## Dual-Track Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        Sprint 120                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Track A (60%): Context Authority V2                            │
│  ├── Days 1-3: Database & Models (~400 LOC)                    │
│  ├── Days 4-6: Service Layer (~600 LOC)                        │
│  ├── Days 7-8: API Endpoints (~500 LOC)                        │
│  └── Days 9-10: Integration Tests (~500 LOC)                   │
│  Total: ~2,000 LOC                                              │
│                                                                 │
│  Track B (40%): Gates Engine Core                               │
│  ├── Days 1-2: Gate Models & State Machine (~300 LOC)          │
│  ├── Days 3-5: OPA Policy Integration (~400 LOC)               │
│  ├── Days 6-8: Evidence Validation (~400 LOC)                  │
│  └── Days 9-10: Unit Tests (~400 LOC)                          │
│  Total: ~1,500 LOC                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Track A: Context Authority V2 (SPEC-0011)

### Phase 1: Database & Models (Days 1-3)

**Estimated LOC**: ~400

#### Database Schema

```sql
-- File: alembic/versions/sprint120_context_authority_v2.py

-- Extend context_authorities table
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS gate_status JSONB;
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS vibecoding_index INTEGER;
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS dynamic_overlay TEXT;
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS tier VARCHAR(20);

-- New table: context_overlay_templates
CREATE TABLE context_overlay_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_type VARCHAR(50) NOT NULL,  -- 'gate_pass', 'gate_fail', 'index_zone'
    trigger_value VARCHAR(100) NOT NULL, -- 'G0.2', 'G1', 'orange', 'red'
    tier VARCHAR(20),                    -- NULL = all tiers
    overlay_content TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_trigger_type CHECK (
        trigger_type IN ('gate_pass', 'gate_fail', 'index_zone', 'stage_constraint')
    )
);

-- New table: context_snapshots
CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES governance_submissions(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    gate_status JSONB NOT NULL,
    vibecoding_index INTEGER NOT NULL,
    dynamic_overlay TEXT NOT NULL,
    tier VARCHAR(20) NOT NULL,
    v1_result JSONB,  -- Store V1 validation result
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_context_snapshots_submission ON context_snapshots(submission_id);
CREATE INDEX idx_context_snapshots_project ON context_snapshots(project_id);
CREATE INDEX idx_context_overlay_templates_trigger ON context_overlay_templates(trigger_type, trigger_value);
```

#### SQLAlchemy Models

```python
# File: backend/app/models/context_authority_v2.py

class ContextOverlayTemplate(Base):
    """Template for dynamic context overlay."""
    __tablename__ = "context_overlay_templates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_value: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    overlay_content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class ContextSnapshot(Base):
    """Point-in-time context snapshot for audit."""
    __tablename__ = "context_snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(ForeignKey("governance_submissions.id"), nullable=False)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    gate_status: Mapped[dict] = mapped_column(JSONB, nullable=False)
    vibecoding_index: Mapped[int] = mapped_column(nullable=False)
    dynamic_overlay: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    v1_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

#### Day 1-3 Deliverables

| Day | Deliverable | LOC |
|-----|-------------|-----|
| Day 1 | Alembic migration + models | 150 |
| Day 2 | Pydantic schemas + repository | 150 |
| Day 3 | Seed overlay templates | 100 |
| **Total** | | **400** |

---

### Phase 2: Service Layer (Days 4-6)

**Estimated LOC**: ~600

#### Core Service

```python
# File: backend/app/services/governance/context_authority_v2.py

class ContextAuthorityEngineV2(ContextAuthorityEngineV1):
    """
    Context Authority V2 - Gate-Aware Dynamic Context.

    Extends V1 with:
    - Gate status integration
    - Vibecoding Index awareness
    - Dynamic AGENTS.md overlay
    - Context snapshots for audit
    """

    def __init__(
        self,
        db: AsyncSession,
        gate_service: GateService,
        vibecoding_service: VibecodingIndexService,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.db = db
        self.gate_service = gate_service
        self.vibecoding_service = vibecoding_service
        self._template_cache: Dict[str, List[ContextOverlayTemplate]] = {}

    async def validate_context_v2(
        self,
        submission: CodeSubmission,
    ) -> ContextValidationResultV2:
        """Gate-aware context validation."""
        # Get current project state
        gate_status = await self.gate_service.get_gate_status(submission.project_id)
        vibecoding_index = await self.vibecoding_service.get_recent_index(submission.project_id)
        tier = await self._get_project_tier(submission.project_id)

        # Run V1 validation
        v1_result = await super().validate_context(submission)

        # Add gate-aware violations
        gate_violations = await self._check_gate_constraints(submission, gate_status)

        # Add index-aware warnings
        index_warnings = await self._check_index_constraints(submission, vibecoding_index)

        # Calculate dynamic overlay
        overlay = await self._calculate_dynamic_overlay(gate_status, vibecoding_index, tier)

        # Create snapshot for audit
        snapshot_id = await self._create_snapshot(
            submission, gate_status, vibecoding_index, overlay, tier, v1_result
        )

        return ContextValidationResultV2(
            valid=v1_result.valid and len(gate_violations) == 0,
            v1_result=v1_result,
            gate_violations=gate_violations,
            index_warnings=index_warnings,
            dynamic_overlay=overlay,
            snapshot_id=snapshot_id,
            tier=tier,
        )

    async def _check_gate_constraints(
        self,
        submission: CodeSubmission,
        gate_status: GateStatus,
    ) -> List[ContextViolation]:
        """Check if submission violates gate constraints."""
        violations = []
        current_stage = gate_status.current_stage

        # Stage-aware file path rules
        stage_rules = {
            "00": {"allowed": ["docs/00-*/**"], "blocked": ["src/**", "backend/**"]},
            "01": {"allowed": ["docs/01-*/**"], "blocked": ["src/**", "backend/**"]},
            "02": {"allowed": ["docs/02-*/**", "*.prisma", "openapi/**"], "blocked": ["backend/app/**"]},
            "04": {"allowed": ["**"], "blocked": []},
            "05": {"allowed": ["tests/**", "**/fix_*"], "blocked": ["**/feat_*"]},
        }

        if current_stage in stage_rules:
            rules = stage_rules[current_stage]
            for file_path in submission.changed_files:
                if self._matches_patterns(file_path, rules["blocked"]):
                    violations.append(ContextViolation(
                        type=ContextViolationType.STAGE_BLOCKED,
                        severity=ViolationSeverity.ERROR,
                        message=f"File '{file_path}' blocked in Stage {current_stage}",
                        file_path=file_path,
                        fix=f"Complete Stage {current_stage} gates before modifying this file",
                        cli_command=f"sdlcctl gate status",
                    ))

        return violations

    async def _check_index_constraints(
        self,
        submission: CodeSubmission,
        vibecoding_index: int,
    ) -> List[ContextViolation]:
        """Check vibecoding index constraints."""
        warnings = []

        if vibecoding_index > 80:
            warnings.append(ContextViolation(
                type=ContextViolationType.HIGH_VIBECODING_INDEX,
                severity=ViolationSeverity.ERROR,
                message=f"Vibecoding Index {vibecoding_index} exceeds threshold (80)",
                fix="CEO review required. Reduce architectural smell or AI dependency.",
                cli_command="sdlcctl vibecoding analyze",
            ))
        elif vibecoding_index > 60:
            warnings.append(ContextViolation(
                type=ContextViolationType.HIGH_VIBECODING_INDEX,
                severity=ViolationSeverity.WARNING,
                message=f"Vibecoding Index {vibecoding_index} in Orange zone (61-80)",
                fix="Tech Lead review recommended.",
            ))

        return warnings

    async def _calculate_dynamic_overlay(
        self,
        gate_status: GateStatus,
        vibecoding_index: int,
        tier: str,
    ) -> str:
        """Calculate dynamic overlay from templates."""
        overlays = []

        # Get gate-based overlays
        gate_templates = await self._get_templates("gate_pass", gate_status.last_passed_gate, tier)
        overlays.extend([t.overlay_content for t in gate_templates])

        # Get index-based overlays
        index_zone = self._get_index_zone(vibecoding_index)
        index_templates = await self._get_templates("index_zone", index_zone, tier)
        overlays.extend([t.overlay_content for t in index_templates])

        # Get stage constraint overlays
        stage_templates = await self._get_templates("stage_constraint", f"stage_{gate_status.current_stage}", tier)
        overlays.extend([t.overlay_content for t in stage_templates])

        # Format with variables
        overlay_text = "\n\n---\n\n".join(overlays)
        return overlay_text.format(
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            index=vibecoding_index,
            stage=gate_status.current_stage,
            tier=tier,
        )

    async def _create_snapshot(
        self,
        submission: CodeSubmission,
        gate_status: GateStatus,
        vibecoding_index: int,
        overlay: str,
        tier: str,
        v1_result: ContextValidationResult,
    ) -> UUID:
        """Create context snapshot for audit."""
        snapshot = ContextSnapshot(
            submission_id=submission.submission_id,
            project_id=submission.project_id,
            gate_status=gate_status.to_dict(),
            vibecoding_index=vibecoding_index,
            dynamic_overlay=overlay,
            tier=tier,
            v1_result=v1_result.to_dict(),
        )
        self.db.add(snapshot)
        await self.db.commit()
        return snapshot.id
```

#### Day 4-6 Deliverables

| Day | Deliverable | LOC |
|-----|-------------|-----|
| Day 4 | Core V2 service (extends V1) | 200 |
| Day 5 | Gate/Index constraint checkers | 200 |
| Day 6 | Dynamic overlay + snapshot | 200 |
| **Total** | | **600** |

---

### Phase 3: API Endpoints (Days 7-8)

**Estimated LOC**: ~500

#### New Endpoints

```python
# File: backend/app/api/routes/context_authority_v2.py

router = APIRouter(prefix="/context-authority/v2", tags=["Context Authority V2"])

@router.post("/validate", response_model=ContextValidationResultV2Response)
async def validate_context_v2(
    request: ContextValidationV2Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gate-aware context validation."""
    engine = get_context_authority_engine_v2(db)
    submission = CodeSubmission(
        submission_id=request.submission_id,
        project_id=request.project_id,
        changed_files=request.changed_files,
        affected_modules=request.affected_modules,
        task_id=request.task_id,
        is_new_feature=request.is_new_feature,
    )
    result = await engine.validate_context_v2(submission)
    return result.to_response()


@router.get("/overlay/{project_id}", response_model=DynamicOverlayResponse)
async def get_dynamic_overlay(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current dynamic overlay for project."""
    engine = get_context_authority_engine_v2(db)
    overlay = await engine.get_dynamic_overlay(project_id)
    return DynamicOverlayResponse(
        project_id=project_id,
        overlay=overlay.content,
        gate_status=overlay.gate_status,
        vibecoding_index=overlay.vibecoding_index,
        generated_at=overlay.generated_at,
    )


@router.get("/templates", response_model=List[ContextOverlayTemplateResponse])
async def list_templates(
    trigger_type: Optional[str] = None,
    tier: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List overlay templates."""
    repo = ContextOverlayTemplateRepository(db)
    templates = await repo.list(trigger_type=trigger_type, tier=tier)
    return [t.to_response() for t in templates]


@router.post("/templates", response_model=ContextOverlayTemplateResponse)
async def create_template(
    request: CreateContextOverlayTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create new overlay template."""
    repo = ContextOverlayTemplateRepository(db)
    template = await repo.create(request)
    return template.to_response()


@router.put("/templates/{template_id}", response_model=ContextOverlayTemplateResponse)
async def update_template(
    template_id: UUID,
    request: UpdateContextOverlayTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update overlay template."""
    repo = ContextOverlayTemplateRepository(db)
    template = await repo.update(template_id, request)
    return template.to_response()


@router.get("/snapshot/{submission_id}", response_model=ContextSnapshotResponse)
async def get_snapshot(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get context snapshot for submission."""
    repo = ContextSnapshotRepository(db)
    snapshot = await repo.get_by_submission(submission_id)
    if not snapshot:
        raise HTTPException(404, "Snapshot not found")
    return snapshot.to_response()


@router.get("/snapshots/{project_id}", response_model=List[ContextSnapshotSummary])
async def list_project_snapshots(
    project_id: UUID,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List context snapshots for project."""
    repo = ContextSnapshotRepository(db)
    snapshots = await repo.list_by_project(project_id, limit=limit, offset=offset)
    return [s.to_summary() for s in snapshots]
```

#### Day 7-8 Deliverables

| Day | Deliverable | LOC |
|-----|-------------|-----|
| Day 7 | Core endpoints (validate, overlay) | 250 |
| Day 8 | Template + snapshot endpoints | 250 |
| **Total** | | **500** |

---

### Phase 4: Integration Tests (Days 9-10)

**Estimated LOC**: ~500

#### Test Suites

```python
# File: backend/tests/integration/test_context_authority_v2.py

class TestContextAuthorityV2Integration:
    """Integration tests for Context Authority V2."""

    async def test_gate_constraint_blocks_code_in_design_stage(self, client, db):
        """Code changes blocked in Stage 02."""
        # Create project in Stage 02
        project = await create_test_project(db, current_stage="02")

        # Submit code change to backend/app/
        response = await client.post("/context-authority/v2/validate", json={
            "project_id": str(project.id),
            "changed_files": ["backend/app/services/new_feature.py"],
            "affected_modules": ["services"],
        })

        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert any(v["type"] == "stage_blocked" for v in result["gate_violations"])

    async def test_vibecoding_index_triggers_warning(self, client, db):
        """High vibecoding index triggers CEO review."""
        project = await create_test_project(db, vibecoding_index=75)

        response = await client.post("/context-authority/v2/validate", json={
            "project_id": str(project.id),
            "changed_files": ["backend/app/services/ai_heavy.py"],
            "affected_modules": ["services"],
        })

        result = response.json()
        assert any(w["type"] == "high_vibecoding_index" for w in result["index_warnings"])

    async def test_dynamic_overlay_updates_on_gate_pass(self, client, db):
        """Dynamic overlay changes when gate passes."""
        project = await create_test_project(db, last_passed_gate="G0.2")

        response = await client.get(f"/context-authority/v2/overlay/{project.id}")

        result = response.json()
        assert "Design approved" in result["overlay"]
        assert "Stage 04: BUILD" in result["overlay"]

    async def test_snapshot_created_on_validation(self, client, db):
        """Context snapshot created for audit trail."""
        project = await create_test_project(db)

        # Validate
        response = await client.post("/context-authority/v2/validate", json={
            "project_id": str(project.id),
            "changed_files": ["docs/02-design/spec.md"],
            "affected_modules": ["design"],
        })

        result = response.json()
        snapshot_id = result["snapshot_id"]

        # Retrieve snapshot
        snapshot_response = await client.get(f"/context-authority/v2/snapshot/{snapshot_id}")
        snapshot = snapshot_response.json()

        assert snapshot["project_id"] == str(project.id)
        assert "gate_status" in snapshot
        assert "vibecoding_index" in snapshot
```

#### Day 9-10 Deliverables

| Day | Deliverable | LOC |
|-----|-------------|-----|
| Day 9 | Gate/Index constraint tests | 250 |
| Day 10 | Overlay/Snapshot tests | 250 |
| **Total** | | **500** |

---

## Track B: Gates Engine Core

### Phase 1: Gate Models & State Machine (Days 1-2)

**Estimated LOC**: ~300

```python
# File: backend/app/models/gates.py

class GateType(str, Enum):
    """Gate types in SDLC lifecycle."""
    G0_1 = "G0.1"  # Problem Definition
    G0_2 = "G0.2"  # Solution Diversity
    G1 = "G1"      # Legal + Market
    G2 = "G2"      # Design Ready
    G3 = "G3"      # Ship Ready
    G4 = "G4"      # Market Validation


class GateStatus(str, Enum):
    """Gate evaluation status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    WAIVED = "waived"


class Gate(Base):
    """Gate instance for a project."""
    __tablename__ = "gates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    gate_type: Mapped[GateType] = mapped_column(nullable=False)
    status: Mapped[GateStatus] = mapped_column(default=GateStatus.NOT_STARTED)
    evidence_ids: Mapped[List[UUID]] = mapped_column(ARRAY(UUID), default=[])
    evaluation_result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    passed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    waived_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    waived_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Phase 2: OPA Policy Integration (Days 3-5)

**Estimated LOC**: ~400

```python
# File: backend/app/services/gates/opa_evaluator.py

class OPAGateEvaluator:
    """Evaluate gates using OPA policies."""

    GATE_POLICIES = {
        GateType.G0_1: "sdlc/gates/g0_1_problem_definition",
        GateType.G0_2: "sdlc/gates/g0_2_solution_diversity",
        GateType.G1: "sdlc/gates/g1_legal_market",
        GateType.G2: "sdlc/gates/g2_design_ready",
        GateType.G3: "sdlc/gates/g3_ship_ready",
        GateType.G4: "sdlc/gates/g4_market_validation",
    }

    async def evaluate(
        self,
        gate: Gate,
        evidence: List[Evidence],
    ) -> GateEvaluationResult:
        """Evaluate gate against OPA policy."""
        policy_path = self.GATE_POLICIES[gate.gate_type]

        input_data = {
            "gate": gate.gate_type.value,
            "project_id": str(gate.project_id),
            "evidence": [e.to_opa_input() for e in evidence],
            "tier": gate.project.tier,
        }

        result = await self.opa_client.query(policy_path, input_data)

        return GateEvaluationResult(
            passed=result.get("allow", False),
            violations=result.get("violations", []),
            warnings=result.get("warnings", []),
            evidence_coverage=result.get("coverage", 0.0),
        )
```

### Phase 3: Evidence Validation (Days 6-8)

**Estimated LOC**: ~400

```python
# File: backend/app/services/gates/evidence_validator.py

class GateEvidenceValidator:
    """Validate evidence for gate evaluation."""

    REQUIRED_EVIDENCE = {
        GateType.G0_1: ["problem_statement", "user_interviews"],
        GateType.G0_2: ["solution_options", "evaluation_matrix"],
        GateType.G1: ["market_analysis", "legal_review"],
        GateType.G2: ["architecture_doc", "adr_list", "api_spec"],
        GateType.G3: ["test_report", "security_scan", "performance_baseline"],
        GateType.G4: ["user_feedback", "metrics_dashboard"],
    }

    async def validate(
        self,
        gate: Gate,
        evidence: List[Evidence],
    ) -> EvidenceValidationResult:
        """Validate evidence completeness and quality."""
        required = self.REQUIRED_EVIDENCE.get(gate.gate_type, [])
        provided = {e.evidence_type for e in evidence}

        missing = set(required) - provided
        extra = provided - set(required)

        return EvidenceValidationResult(
            complete=len(missing) == 0,
            missing_types=list(missing),
            extra_types=list(extra),
            quality_scores={e.id: await self._score_evidence(e) for e in evidence},
        )
```

### Phase 4: Unit Tests (Days 9-10)

**Estimated LOC**: ~400

---

## Daily Schedule

| Day | Track A (60%) | Track B (40%) | Total LOC |
|-----|---------------|---------------|-----------|
| **0** | Framework submodule update | - | 50 |
| **1** | Alembic migration | Gate models | 200 |
| **2** | Pydantic schemas | State machine | 200 |
| **3** | Seed templates | OPA evaluator start | 200 |
| **4** | V2 service core | OPA evaluator cont. | 200 |
| **5** | Constraint checkers | OPA policies | 300 |
| **6** | Overlay + snapshot | Evidence validator start | 300 |
| **7** | API endpoints (core) | Evidence validator cont. | 350 |
| **8** | API endpoints (admin) | Evidence validator tests | 350 |
| **9** | Integration tests | Unit tests | 350 |
| **10** | Integration tests + docs | Unit tests + docs | 350 |
| **TOTAL** | **2,000** | **1,500** | **3,500** |

---

## Success Criteria

### Track A (Context Authority V2)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **V2 API functional** | 100% | All 7 endpoints working |
| **Gate awareness** | 95% accuracy | Violations match stage |
| **Snapshot completeness** | 100% | All validations logged |
| **Test coverage** | >90% | pytest-cov report |
| **Performance** | <500ms | V2 validate p95 |

### Track B (Gates Engine Core)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Gate models** | 100% | All 6 gate types |
| **OPA integration** | 100% | Policies loaded |
| **Evidence validation** | 100% | Required types checked |
| **Test coverage** | >85% | pytest-cov report |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Framework submodule delay | Medium | Low | Proceed without, update later |
| V2 complexity higher than estimate | Low | Medium | Reuse V1 patterns extensively |
| OPA policy debugging | Medium | Low | Use OPA playground for testing |
| Track coordination conflicts | Low | High | Clear ownership boundaries |

---

## Dependencies

### Internal

- [x] Context Authority V1 (Sprint 109) - ✅ Complete
- [x] Vibecoding Index Service (Sprint 114) - ✅ Complete
- [x] Governance Submissions (Sprint 118) - ✅ Complete
- [ ] OPA Policy Engine (existing) - ✅ Available

### External

- [ ] Framework v6.0.5 tag - ⏳ Expected Jan 31 - Feb 1

---

## Stakeholder Communication

### Daily Standup Template

```
Sprint 120 Day X Status:

Track A (Context Authority V2):
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

Track B (Gates Engine Core):
- Yesterday: [completed tasks]
- Today: [planned tasks]
- Blockers: [if any]

LOC Progress: XXXX / 3,500 (XX%)
```

### End-of-Sprint Report Template

```
Sprint 120 Complete:

Track A: Context Authority V2
- LOC: XXXX / 2,000
- Tests: XX / XX passing
- Endpoints: 7 functional
- Performance: XXXms p95

Track B: Gates Engine Core
- LOC: XXXX / 1,500
- Tests: XX / XX passing
- Gate types: 6 implemented
- OPA policies: X loaded

Total: XXXX LOC
Quality: XX% coverage
Status: [COMPLETE/PARTIAL]
```

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 29, 2026 |
| **Author** | Backend Team |
| **Sprint** | 120 |
| **Status** | PLANNED |
| **Predecessor** | Sprint 119 (COMPLETE) |
| **Successor** | Sprint 121 (TBD) |
