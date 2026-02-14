# ADR-046: Validate Consistency Command Architecture

**Version**: 1.0.0
**Status**: APPROVED
**Created**: February 1, 2026
**Sprint**: Sprint 136
**Framework**: SDLC 6.0.5
**Decision Makers**: CTO, Backend Lead
**Related Requirements**: FR-036 Validate Consistency Command
**Related Spec**: SPEC-0021 Stage Consistency Validation

---

## Context

SPEC-0021 (Stage Consistency Validation) requires a CLI command `sdlcctl validate-consistency` that validates consistency between SDLC stages:
- Stage 01 (Planning) ↔ Stage 02 (Design)
- Stage 02 (Design) ↔ Stage 03 (Integrate)
- Stage 03 (Integrate) ↔ Stage 04 (Build)
- Stage 01 (Planning) ↔ Stage 04 (Build)

The command must support tier-specific enforcement levels, multiple output formats, and CI/CD integration.

### Constraints

1. **Must integrate with existing sdlcctl architecture** - Typer-based CLI, Rich console output
2. **Must follow validation engine pattern** - Use existing `ViolationReport`, `Severity` enums
3. **Must support tier-specific rules** - Different severity per tier
4. **Performance budget** - <30 seconds for 1000 files

---

## Decision

### 1. Command Architecture

Create a new command module `commands/consistency.py` with a dedicated validation service `validation/consistency/`.

```
backend/sdlcctl/sdlcctl/
├── commands/
│   └── consistency.py          # CLI command entry point
├── validation/
│   └── consistency/
│       ├── __init__.py
│       ├── engine.py           # Main orchestrator
│       ├── checkers/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract base checker
│       │   ├── stage_01_02.py  # Planning ↔ Design
│       │   ├── stage_02_03.py  # Design ↔ Integrate
│       │   ├── stage_03_04.py  # Integrate ↔ Build
│       │   └── stage_01_04.py  # Planning ↔ Build
│       ├── models.py           # Data models
│       └── report.py           # Report generation
```

### 2. Consistency Engine Design

```python
@dataclass
class ConsistencyConfig:
    """Configuration for consistency validation."""
    tier: Tier
    stage_paths: Dict[str, Path]  # {"01": Path, "02": Path, ...}
    strict: bool = False
    check_checksums: bool = False
    checksums_path: Optional[Path] = None

@dataclass
class ConsistencyResult:
    """Result of consistency validation."""
    stage_pairs: Dict[str, StageConsistencyResult]
    violations: List[ViolationReport]
    overall_consistency_percent: float
    execution_time_seconds: float

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.stage_pairs.values())

class ConsistencyEngine:
    """Orchestrates cross-stage consistency validation."""

    def __init__(self, config: ConsistencyConfig):
        self.config = config
        self.checkers = [
            Stage01To02Checker(config),
            Stage02To03Checker(config),
            Stage03To04Checker(config),
            Stage01To04Checker(config),
        ]

    def validate(self) -> ConsistencyResult:
        """Run all consistency checks."""
        results = {}
        all_violations = []

        for checker in self.checkers:
            result = checker.check()
            results[checker.pair_id] = result
            all_violations.extend(result.violations)

        return ConsistencyResult(
            stage_pairs=results,
            violations=self._apply_tier_severity(all_violations),
            overall_consistency_percent=self._calculate_percent(results),
            execution_time_seconds=...
        )
```

### 3. Checker Interface

```python
class BaseConsistencyChecker(ABC):
    """Abstract base class for stage-to-stage consistency checkers."""

    @property
    @abstractmethod
    def pair_id(self) -> str:
        """Return checker ID, e.g., 'stage_01_02'."""
        ...

    @property
    @abstractmethod
    def source_stage(self) -> str:
        """Return source stage ID, e.g., '01'."""
        ...

    @property
    @abstractmethod
    def target_stage(self) -> str:
        """Return target stage ID, e.g., '02'."""
        ...

    @abstractmethod
    def check(self) -> StageConsistencyResult:
        """Perform consistency check between stages."""
        ...

    def get_rules(self) -> List[ConsistencyRule]:
        """Return rules for this checker."""
        ...
```

### 4. Tier-Specific Rule Severity

```python
TIER_SEVERITY_OVERRIDE = {
    Tier.LITE: {
        # All rules become INFO
        "CONS-*": Severity.INFO,
    },
    Tier.STANDARD: {
        # All rules become WARNING
        "CONS-*": Severity.WARNING,
    },
    Tier.PROFESSIONAL: {
        # Specific rules become ERROR
        "CONS-001": Severity.ERROR,  # ADRs must reference requirements
        "CONS-004": Severity.ERROR,  # API contracts must match design
        "CONS-007": Severity.ERROR,  # Endpoints must match contracts
        "CONS-010": Severity.ERROR,  # Implementation must satisfy requirements
        # Others remain WARNING
    },
    Tier.ENTERPRISE: {
        # All rules become ERROR
        "CONS-*": Severity.ERROR,
    },
}
```

### 5. CLI Command Implementation

```python
# commands/consistency.py
def validate_consistency_command(
    stage_01: Path = typer.Option(..., "--stage", "-s", help="Stage 01 path"),
    stage_02: Path = typer.Option(..., "--stage", "-s", help="Stage 02 path"),
    stage_03: Path = typer.Option(..., "--stage", "-s", help="Stage 03 path"),
    stage_04: Path = typer.Option(..., "--stage", "-s", help="Stage 04 path"),
    tier: Optional[str] = typer.Option(None, "--tier", "-t"),
    output_format: str = typer.Option("text", "--format", "-f"),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o"),
    strict: bool = typer.Option(False, "--strict"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    check_checksums: Optional[Path] = typer.Option(None, "--check-checksums"),
) -> None:
    """Validate cross-stage consistency per SPEC-0021."""
    ...
```

### 6. Output Formatters

```python
class ConsistencyReportFormatter:
    """Format consistency results for output."""

    def format_text(self, result: ConsistencyResult, verbose: bool = False) -> str:
        ...

    def format_json(self, result: ConsistencyResult) -> str:
        ...

    def format_github(self, result: ConsistencyResult) -> str:
        ...

    def format_summary(self, result: ConsistencyResult) -> str:
        ...
```

---

## Alternatives Considered

### Alternative 1: Extend Existing `validate` Command

**Approach**: Add `--consistency` flag to existing `sdlcctl validate` command.

**Pros**:
- No new command to learn
- Reuses existing validation infrastructure

**Cons**:
- Command signature becomes complex
- Different validation scope (structure vs. consistency)
- Hard to extend independently

**Decision**: **Rejected** - Consistency validation has different inputs and outputs than structure validation.

### Alternative 2: Single Monolithic Checker

**Approach**: One large checker that validates all stage pairs.

**Pros**:
- Simpler architecture
- Less files to maintain

**Cons**:
- Violates Single Responsibility Principle
- Hard to test independently
- Hard to extend with new rules

**Decision**: **Rejected** - Modular checkers are more maintainable.

### Alternative 3: Plugin-Based Architecture

**Approach**: Allow external plugins to register consistency checkers.

**Pros**:
- Maximum extensibility
- Community contributions

**Cons**:
- Over-engineering for current needs
- Complex plugin loading mechanism

**Decision**: **Rejected for v1.0** - Can be added later if needed.

---

## Consequences

### Positive

1. **Clean separation** - Consistency validation is isolated from structure validation
2. **Tier-specific enforcement** - Different severity levels per tier
3. **CI/CD friendly** - Multiple output formats including GitHub Actions
4. **Extensible** - Easy to add new rules or stage pairs
5. **Testable** - Each checker can be tested independently

### Negative

1. **More code** - New module with multiple files
2. **Learning curve** - Developers need to understand checker pattern
3. **Maintenance** - More files to maintain

### Neutral

1. **Performance** - Comparable to existing validators
2. **Dependencies** - No new external dependencies

---

## Implementation Plan

### Phase 1: Core Infrastructure (Day 1)

1. Create `validation/consistency/` module structure
2. Implement `ConsistencyEngine` class
3. Implement `BaseConsistencyChecker` abstract class
4. Create data models (`ConsistencyConfig`, `ConsistencyResult`)

### Phase 2: Checkers (Day 2)

1. Implement `Stage01To02Checker` - ADR reference validation
2. Implement `Stage02To03Checker` - API contract validation
3. Implement `Stage03To04Checker` - Endpoint matching
4. Implement `Stage01To04Checker` - Requirements satisfaction

### Phase 3: CLI & Output (Day 3)

1. Implement `commands/consistency.py` command
2. Implement `ConsistencyReportFormatter` for all formats
3. Register command in `cli.py`

### Phase 4: Testing & Documentation (Day 4)

1. Write unit tests for each checker (90%+ coverage)
2. Write integration test with sample project
3. Update README.md and CHANGELOG.md

---

## File Structure

```
backend/sdlcctl/sdlcctl/
├── commands/
│   ├── __init__.py
│   ├── consistency.py          # NEW - CLI command
│   └── ... (existing)
├── validation/
│   ├── __init__.py             # UPDATE - export new modules
│   ├── consistency/            # NEW - all new files
│   │   ├── __init__.py
│   │   ├── engine.py           # ConsistencyEngine
│   │   ├── models.py           # Data classes
│   │   ├── report.py           # Formatters
│   │   └── checkers/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── stage_01_02.py
│   │       ├── stage_02_03.py
│   │       ├── stage_03_04.py
│   │       └── stage_01_04.py
│   └── ... (existing)
└── cli.py                      # UPDATE - register command
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | ≥90% | pytest-cov |
| Command execution time | <30s | Timer in output |
| Memory usage | <500MB | py-spy profiling |
| Documentation complete | 100% | Checklist |

---

## Related Documents

- [FR-036: Validate Consistency Command](../../01-planning/03-Functional-Requirements/FR-036-Validate-Consistency-Command.md)
- [SPEC-0021: Stage Consistency Validation](../../../SDLC-Enterprise-Framework/05-Templates-Tools/01-Specification-Standard/SPEC-0021-Stage-Consistency-Validation.md)
- [ADR-014: SDLC Structure Validator](ADR-014-SDLC-Structure-Validator.md)

---

**Document Status**: APPROVED
**Approval Date**: February 1, 2026
**Decision Authority**: CTO + Backend Lead
