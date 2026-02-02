# Governance Signals Design
## 5-Signal Algorithm + Vibecoding Index Calculation

**Version**: 1.0.0
**Date**: January 27, 2026
**Authority**: Phase 0 Deliverable #3 (48-hour CTO Gate Review)
**Prerequisites**: CEO-Smell-Calibration.md (CEO + Tech Lead 2-hour session)
**Phase**: PRE-PHASE 0 → PHASE 0 → WEEK 1

---

## 📋 DOCUMENT PURPOSE

**Goal**: Encode CEO's "code smell" intuition into 5 measurable signals that calculate Vibecoding Index (0-100).

**Requirements**:
- Non-blocking governance (signals don't block PRs)
- Explainable scoring (every score >30 must justify itself)
- Progressive routing (Green auto-approve → Red CEO must review)
- MAX CRITICALITY OVERRIDE (critical paths auto-boost to Red)

**Success Criteria**:
- >95% CEO agreement rate with index routing decisions
- <10% false positive rate (CEO disagrees with Red/Orange)
- <500ms calculation latency (P95)

---

## 🎯 VIBECODING INDEX FORMULA

### Composite Score (0-100)

```python
vibecoding_index = (
    architectural_smell * 0.25 +
    abstraction_complexity * 0.15 +
    ai_dependency_ratio * 0.20 +
    change_surface_area * 0.20 +
    drift_velocity * 0.20
)

# Thresholds (from CEO Calibration Session)
if vibecoding_index >= 81:
    routing = "ceo_must_review"      # Red
    color = "#EF4444"
elif vibecoding_index >= 61:
    routing = "ceo_should_review"    # Orange
    color = "#F97316"
elif vibecoding_index >= 31:
    routing = "tech_lead_review"     # Yellow
    color = "#EAB308"
else:
    routing = "auto_approve"         # Green
    color = "#10B981"
```

### Weights Rationale (from CEO-Smell-Calibration.md)

```yaml
Signal Weights (Initial Configuration):
  architectural_smell: 0.25        # CEO's #1 concern (25%)
    Rationale: "God classes and shotgun surgery = rework later"
    Historical data: 68% of rejected PRs had architectural smells

  abstraction_complexity: 0.15     # Medium priority (15%)
    Rationale: "Over-engineering slows development"
    Historical data: 42% of rejected PRs were over-abstracted

  ai_dependency_ratio: 0.20        # High priority (20%)
    Rationale: "AI code without human review = liability"
    Historical data: 55% of rejected PRs had >80% AI content

  change_surface_area: 0.20        # High priority (20%)
    Rationale: "Touching too many files = coordination risk"
    Historical data: 60% of rejected PRs touched >10 files

  drift_velocity: 0.20             # High priority (20%)
    Rationale: "Codebase diverging = technical debt accumulating"
    Historical data: 50% of rejected PRs introduced new patterns

Note: Weights will be recalibrated weekly based on CEO override data
```

---

## 🔍 SIGNAL 1: ARCHITECTURAL SMELL (Weight: 0.25)

### Definition

Detects **anti-patterns** that violate SOLID principles and increase maintenance cost.

### Patterns Detected

```yaml
1. God Class Pattern:
   Detection: Class >500 lines OR >30 methods
   Severity Calculation:
     score = min(100, (line_count - 500) / 5)
     Example: 1000-line class = (1000-500)/5 = 100 severity

2. Feature Envy:
   Detection: Method calls other class methods >2x more than own
   Severity: 70 (fixed)
   Example:
     class OrderService:
       def process_order(self, order):
         self.validate(order)           # 1 internal call
         customer_service.check(order)  # 5 external calls
         payment_service.charge(order)  # 3 external calls
         # 8 external / 1 internal = Feature Envy

3. Shotgun Surgery:
   Detection: Single change touches >10 files
   Severity Calculation:
     score = min(100, file_count * 5)
     Example: 15 files changed = 15*5 = 75 severity

4. Parallel Inheritance Hierarchies:
   Detection: Two class hierarchies with matching names
   Severity: 80 (fixed)
   Example:
     AbstractUser → AdminUser, GuestUser
     AbstractUserView → AdminUserView, GuestUserView

5. Data Clumps:
   Detection: Same 3+ parameters repeated across 3+ methods
   Severity: 60 (fixed)
   Example:
     def method_a(user_id, user_email, user_name): ...
     def method_b(user_id, user_email, user_name): ...
     def method_c(user_id, user_email, user_name): ...
```

### Algorithm

```python
async def calculate_architectural_smell(
    submission: CodeSubmission
) -> float:
    """
    Calculate architectural smell score (0-100).

    Higher score = worse smell.

    Returns:
        float: 0.0 (no smell) to 100.0 (critical smell)
    """
    smells = []

    for file in submission.changed_files:
        ast_tree = await parse_ast(file)

        # Pattern 1: God Class
        for class_def in ast_tree.classes:
            if class_def.line_count > 500:
                severity = min(100, (class_def.line_count - 500) / 5)
                smells.append(ArchitecturalSmell(
                    type="god_class",
                    file=file.path,
                    class_name=class_def.name,
                    severity=severity,
                    evidence=f"{class_def.line_count} lines (limit: 500)"
                ))

            if class_def.method_count > 30:
                severity = min(100, (class_def.method_count - 30) * 2)
                smells.append(ArchitecturalSmell(
                    type="god_class",
                    file=file.path,
                    class_name=class_def.name,
                    severity=severity,
                    evidence=f"{class_def.method_count} methods (limit: 30)"
                ))

        # Pattern 2: Feature Envy
        for method in ast_tree.methods:
            external_calls = method.count_external_calls()
            internal_calls = method.count_internal_calls()

            if internal_calls > 0 and external_calls > internal_calls * 2:
                smells.append(ArchitecturalSmell(
                    type="feature_envy",
                    file=file.path,
                    method=method.name,
                    severity=70,
                    evidence=f"{external_calls} external / {internal_calls} internal"
                ))

    # Pattern 3: Shotgun Surgery
    if len(submission.changed_files) > 10:
        severity = min(100, len(submission.changed_files) * 5)
        smells.append(ArchitecturalSmell(
            type="shotgun_surgery",
            severity=severity,
            evidence=f"{len(submission.changed_files)} files changed (limit: 10)"
        ))

    # Pattern 4: Parallel Inheritance Hierarchies
    hierarchies = detect_parallel_hierarchies(submission)
    if hierarchies:
        for h1, h2 in hierarchies:
            smells.append(ArchitecturalSmell(
                type="parallel_inheritance",
                severity=80,
                evidence=f"{h1.name} || {h2.name}"
            ))

    # Pattern 5: Data Clumps
    data_clumps = detect_data_clumps(submission)
    for clump in data_clumps:
        smells.append(ArchitecturalSmell(
            type="data_clump",
            severity=60,
            evidence=f"Parameters {clump.params} repeated {clump.count} times"
        ))

    # Calculate aggregate score
    if not smells:
        return 0.0

    # Weighted average (worst smell contributes more)
    sorted_smells = sorted(smells, key=lambda s: s.severity, reverse=True)
    weights = [1.0, 0.7, 0.5, 0.3, 0.1]  # Diminishing importance
    weighted_sum = sum(
        smell.severity * weight
        for smell, weight in zip(sorted_smells, weights)
    )
    weight_total = sum(weights[:len(sorted_smells)])

    return min(100.0, weighted_sum / weight_total)
```

### Example Output

```json
{
  "signal": "architectural_smell",
  "score": 72.5,
  "contribution": 18.1,  // 72.5 * 0.25 = 18.1 points to vibecoding_index
  "smells_detected": [
    {
      "type": "god_class",
      "severity": 100,
      "file": "backend/app/services/user_service.py",
      "class": "UserService",
      "evidence": "680 lines (limit: 500)"
    },
    {
      "type": "shotgun_surgery",
      "severity": 70,
      "evidence": "14 files changed (limit: 10)"
    },
    {
      "type": "feature_envy",
      "severity": 70,
      "file": "backend/app/services/order_service.py",
      "method": "process_order",
      "evidence": "8 external / 1 internal"
    }
  ]
}
```

---

## 🧩 SIGNAL 2: ABSTRACTION COMPLEXITY (Weight: 0.15)

### Definition

Measures **over-engineering** through excessive abstraction layers, interfaces, and generic types.

### Patterns Detected

```yaml
1. Deep Inheritance:
   Detection: Inheritance depth >3 levels
   Severity Calculation:
     score = min(100, (depth - 3) * 20)
     Example: 5-level inheritance = (5-3)*20 = 40 severity

2. Interface Proliferation:
   Detection: >5 interfaces for single implementation
   Severity: 80 (fixed)
   Example:
     IUserRepository + IUserService + IUserValidator + IUserMapper
     + IUserFactory + IUserBuilder = 6 interfaces for UserService

3. Generic Type Depth:
   Detection: Nested generics >3 levels (T<U<V<W>>>)
   Severity: 90 (fixed, very hard to understand)

4. Factory Pattern Abuse:
   Detection: Factory for single implementation
   Severity: 60 (fixed)

5. Premature Abstraction:
   Detection: Abstract class with 1 concrete implementation
   Severity: 50 (fixed)
```

### Algorithm

```python
async def calculate_abstraction_complexity(
    submission: CodeSubmission
) -> float:
    """
    Calculate abstraction complexity score (0-100).

    Higher score = more over-engineered.

    Returns:
        float: 0.0 (simple) to 100.0 (over-abstracted)
    """
    complexities = []

    for file in submission.changed_files:
        ast_tree = await parse_ast(file)

        # Pattern 1: Deep Inheritance
        for class_def in ast_tree.classes:
            depth = class_def.inheritance_depth()
            if depth > 3:
                severity = min(100, (depth - 3) * 20)
                complexities.append(AbstractionComplexity(
                    type="deep_inheritance",
                    file=file.path,
                    class_name=class_def.name,
                    severity=severity,
                    evidence=f"{depth} levels (limit: 3)"
                ))

        # Pattern 2: Interface Proliferation
        interfaces = ast_tree.count_interfaces()
        implementations = ast_tree.count_concrete_classes()
        if interfaces > 5 and implementations == 1:
            complexities.append(AbstractionComplexity(
                type="interface_proliferation",
                file=file.path,
                severity=80,
                evidence=f"{interfaces} interfaces for 1 implementation"
            ))

        # Pattern 3: Generic Type Depth
        for type_hint in ast_tree.type_hints:
            generic_depth = count_generic_depth(type_hint)
            if generic_depth > 3:
                complexities.append(AbstractionComplexity(
                    type="generic_depth",
                    file=file.path,
                    severity=90,
                    evidence=f"Generic depth {generic_depth}: {type_hint}"
                ))

        # Pattern 4: Factory Pattern Abuse
        factories = ast_tree.find_factory_patterns()
        for factory in factories:
            products = factory.count_products()
            if products == 1:
                complexities.append(AbstractionComplexity(
                    type="factory_abuse",
                    file=file.path,
                    class_name=factory.name,
                    severity=60,
                    evidence="Factory for single product"
                ))

        # Pattern 5: Premature Abstraction
        abstract_classes = ast_tree.find_abstract_classes()
        for abstract_class in abstract_classes:
            concrete_count = abstract_class.count_implementations()
            if concrete_count == 1:
                complexities.append(AbstractionComplexity(
                    type="premature_abstraction",
                    file=file.path,
                    class_name=abstract_class.name,
                    severity=50,
                    evidence="Abstract class with 1 implementation"
                ))

    # Calculate aggregate score
    if not complexities:
        return 0.0

    # Worst complexity dominates
    max_severity = max(c.severity for c in complexities)
    return float(max_severity)
```

---

## 🤖 SIGNAL 3: AI DEPENDENCY RATIO (Weight: 0.20)

### Definition

Measures **AI-generated code percentage** and **human modification ratio**.

**Red Flag**: >80% AI content AND <10% human modification = "copy-paste without understanding"

### Algorithm

```python
async def calculate_ai_dependency_ratio(
    submission: CodeSubmission
) -> float:
    """
    Calculate AI dependency ratio score (0-100).

    Higher score = more AI-dependent (potential liability).

    Returns:
        float: 0.0 (all human) to 100.0 (all AI, no review)
    """
    total_lines = 0
    ai_lines = 0
    human_modified_lines = 0

    for file in submission.changed_files:
        file_stats = await analyze_file_authorship(file)

        total_lines += file_stats.total_lines
        ai_lines += file_stats.ai_generated_lines
        human_modified_lines += file_stats.human_modified_lines

    # Avoid division by zero
    if total_lines == 0:
        return 0.0

    # Calculate ratios
    ai_ratio = ai_lines / total_lines
    human_modification_ratio = human_modified_lines / ai_lines if ai_lines > 0 else 1.0

    # Scoring logic
    if ai_ratio > 0.8 and human_modification_ratio < 0.1:
        # RED FLAG: >80% AI, <10% human modification
        score = 100.0
    elif ai_ratio > 0.8:
        # High AI content but human reviewed
        score = 70.0
    elif ai_ratio > 0.6:
        # Moderate AI content
        score = 50.0
    elif ai_ratio > 0.4:
        # Balanced AI-human
        score = 30.0
    else:
        # Mostly human
        score = ai_ratio * 50  # 0-20 range

    return score
```

### Example Output

```json
{
  "signal": "ai_dependency_ratio",
  "score": 85.0,
  "contribution": 17.0,  // 85.0 * 0.20 = 17.0 points to vibecoding_index
  "details": {
    "total_lines": 450,
    "ai_lines": 380,
    "human_modified_lines": 25,
    "ai_ratio": 0.844,
    "human_modification_ratio": 0.066,
    "red_flag": true,
    "reason": "High AI content (84%) with minimal human review (6.6%)"
  }
}
```

---

## 📏 SIGNAL 4: CHANGE SURFACE AREA (Weight: 0.20)

### Definition

Measures **coordination risk** by counting files, modules, API contracts, and database schemas touched.

### Factors

```yaml
1. Files Changed:
   Weight: 0.3
   Scoring: min(100, file_count * 5)

2. Modules Touched:
   Weight: 0.25
   Scoring: min(100, module_count * 10)

3. API Contracts Affected:
   Weight: 0.25
   Scoring: min(100, api_count * 20)

4. Database Schema Touched:
   Weight: 0.15
   Scoring: 100 if touched, 0 otherwise

5. Security-Sensitive Files:
   Weight: 0.05
   Scoring: 100 if touched, 0 otherwise
```

### Algorithm

```python
async def calculate_change_surface_area(
    submission: CodeSubmission
) -> float:
    """
    Calculate change surface area score (0-100).

    Higher score = more coordination risk.

    Returns:
        float: 0.0 (small change) to 100.0 (massive change)
    """
    # Factor 1: Files Changed
    file_count = len(submission.changed_files)
    file_score = min(100, file_count * 5)

    # Factor 2: Modules Touched
    modules = extract_modules_from_files(submission.changed_files)
    module_count = len(modules)
    module_score = min(100, module_count * 10)

    # Factor 3: API Contracts Affected
    api_files = [
        f for f in submission.changed_files
        if f.path.endswith((".yaml", ".yml", "openapi.json", "/routes/"))
    ]
    api_score = min(100, len(api_files) * 20)

    # Factor 4: Database Schema Touched
    schema_files = [
        f for f in submission.changed_files
        if f.path.endswith(("schema.prisma", "migrations/", "alembic/"))
    ]
    schema_score = 100 if schema_files else 0

    # Factor 5: Security-Sensitive Files
    security_files = [
        f for f in submission.changed_files
        if any(pattern in f.path for pattern in [
            "auth", "security", "crypto", ".env", "secrets", "credentials"
        ])
    ]
    security_score = 100 if security_files else 0

    # Weighted sum
    surface_area_score = (
        file_score * 0.3 +
        module_score * 0.25 +
        api_score * 0.25 +
        schema_score * 0.15 +
        security_score * 0.05
    )

    return surface_area_score
```

---

## 📈 SIGNAL 5: DRIFT VELOCITY (Weight: 0.20)

### Definition

Measures **codebase divergence rate** over 7 days by tracking new patterns, deprecated usage, and style violations.

### Metrics

```yaml
1. New Patterns Introduced:
   Detection: New class/function/module patterns not in existing codebase
   Severity: 10 per new pattern

2. Deprecated Patterns Used:
   Detection: Using patterns marked as @deprecated
   Severity: 20 per deprecated usage

3. Inconsistent Naming:
   Detection: snake_case vs camelCase within same module
   Severity: 5 per inconsistency

4. Style Violations:
   Detection: Ruff/ESLint violations
   Severity: 1 per violation
```

### Algorithm

```python
async def calculate_drift_velocity(
    submission: CodeSubmission,
    context: ProjectContext
) -> float:
    """
    Calculate drift velocity score (0-100).

    Higher score = codebase diverging faster.

    Returns:
        float: 0.0 (no drift) to 100.0 (rapid divergence)
    """
    # Get 7-day historical data
    historical_submissions = await get_submissions_last_7_days(
        context.project_id
    )

    drift_events = []

    # Metric 1: New Patterns Introduced
    existing_patterns = await extract_patterns(context.codebase)
    new_patterns = await extract_patterns(submission)
    novel_patterns = new_patterns - existing_patterns

    for pattern in novel_patterns:
        drift_events.append(DriftEvent(
            type="new_pattern",
            severity=10,
            evidence=f"New pattern: {pattern}"
        ))

    # Metric 2: Deprecated Patterns Used
    deprecated_patterns = await get_deprecated_patterns(context)
    for file in submission.changed_files:
        deprecated_usage = find_deprecated_usage(file, deprecated_patterns)
        for usage in deprecated_usage:
            drift_events.append(DriftEvent(
                type="deprecated_usage",
                severity=20,
                evidence=f"Deprecated: {usage.pattern} in {file.path}"
            ))

    # Metric 3: Inconsistent Naming
    naming_violations = await check_naming_consistency(submission)
    for violation in naming_violations:
        drift_events.append(DriftEvent(
            type="naming_inconsistency",
            severity=5,
            evidence=f"{violation.file}: {violation.details}"
        ))

    # Metric 4: Style Violations
    style_violations = await run_linter(submission)
    for violation in style_violations:
        drift_events.append(DriftEvent(
            type="style_violation",
            severity=1,
            evidence=f"{violation.file}:{violation.line} {violation.rule}"
        ))

    # Calculate drift velocity (events per day over 7 days)
    total_severity = sum(event.severity for event in drift_events)
    drift_velocity_score = min(100.0, total_severity / 7.0)

    return drift_velocity_score
```

---

## 🚨 MAX CRITICALITY OVERRIDE

### Principle

**"One-line change to auth.py can score 0 by algorithm but is still HIGH RISK"**

### Override Logic

```python
async def apply_max_criticality_override(
    submission: CodeSubmission,
    calculated_index: float
) -> float:
    """
    Apply MAX CRITICALITY OVERRIDE.

    Critical path files auto-boost index to 80 (Red).

    Returns:
        float: max(calculated_index, 80) if critical path touched
    """
    critical_paths = await load_critical_paths()

    # Check if any changed file matches critical path
    for file in submission.changed_files:
        for category, patterns in critical_paths.items():
            if any(fnmatch(file.path, pattern) for pattern in patterns):
                logger.warning(
                    f"CRITICAL PATH TOUCHED: {file.path} matches {category}"
                )
                return max(calculated_index, 80.0)  # Force Red

    return calculated_index  # No override
```

### Critical Paths (from critical_paths.yaml)

```yaml
critical_paths:
  security:
    - "auth/**"
    - "security/**"
    - "**/authentication*"
    - "**/authorization*"
    - "**/jwt*"
    - "**/oauth*"

  payment:
    - "payment/**"
    - "billing/**"
    - "**/stripe*"
    - "**/payment_service*"

  database_schema:
    - "prisma/schema.prisma"
    - "migrations/**"
    - "alembic/**"
    - "**/models/*.py"

  infrastructure:
    - "docker-compose*.yml"
    - "Dockerfile"
    - "k8s/**"
    - ".github/workflows/**"

  secrets:
    - "**/.env*"
    - "**/secrets*"
    - "**/credentials*"
    - "**/api_keys*"
```

### Example Override

```json
{
  "submission_id": "PR-234",
  "calculated_index": 15,  // Would be Green
  "critical_override": {
    "applied": true,
    "reason": "backend/app/services/auth_service.py matches security/**",
    "category": "security",
    "final_index": 80  // Forced Red
  },
  "routing": "ceo_must_review"
}
```

---

## 📊 EXPLAINABILITY REQUIREMENTS

### Principle (from VIBECODING-INDEX-EXPLAINABILITY-SPEC.md)

**"EVERY SCORE > 30 MUST BE EXPLAINABLE"**

### Explainability Output Format

```json
{
  "vibecoding_index": {
    "score": 72,
    "category": "orange",
    "routing": "ceo_should_review",
    "critical_override": false
  },

  "top_contributors": [
    {
      "signal": "architectural_smell",
      "score": 72.5,
      "contribution": 18.1,
      "contribution_percent": 25.1,
      "evidence": [
        {
          "type": "god_class",
          "severity": 100,
          "file": "backend/app/services/user_service.py",
          "class": "UserService",
          "details": "680 lines (limit: 500)"
        },
        {
          "type": "shotgun_surgery",
          "severity": 70,
          "details": "14 files changed (limit: 10)"
        }
      ]
    },
    {
      "signal": "ai_dependency_ratio",
      "score": 85.0,
      "contribution": 17.0,
      "contribution_percent": 23.6,
      "evidence": {
        "ai_ratio": 0.844,
        "human_modification_ratio": 0.066,
        "red_flag": true,
        "reason": "High AI content (84%) with minimal human review (6.6%)"
      }
    },
    {
      "signal": "change_surface_area",
      "score": 70.0,
      "contribution": 14.0,
      "contribution_percent": 19.4,
      "evidence": {
        "files_changed": 14,
        "modules_touched": 5,
        "api_contracts_affected": 2,
        "database_schema_touched": false,
        "security_sensitive_files": 1
      }
    }
  ],

  "suggested_focus": {
    "file": "backend/app/services/user_service.py",
    "reason": "God class pattern (680 lines), highest severity",
    "lines_to_review": [
      {"start": 120, "end": 180, "reason": "Authentication logic"},
      {"start": 450, "end": 520, "reason": "Validation methods"}
    ],
    "estimated_review_time": "15 minutes"
  },

  "baseline_comparison": {
    "category": "backend_service_update",
    "historical_avg": 42.5,
    "this_pr": 72.0,
    "deviation": "+69%",
    "interpretation": "Higher than typical for backend service updates",
    "similar_prs": [
      {"pr": "#201", "index": 68, "outcome": "approved_with_changes"},
      {"pr": "#189", "index": 75, "outcome": "rejected"}
    ]
  }
}
```

---

## 🎯 ROUTING RULES

### Progressive Routing Logic

```python
def route_submission(
    vibecoding_index: float,
    critical_override: bool
) -> str:
    """
    Route submission based on Vibecoding Index.

    Returns:
        str: "auto_approve" | "tech_lead_review" | "ceo_should_review" | "ceo_must_review"
    """
    if critical_override:
        return "ceo_must_review"  # Red - Critical path

    if vibecoding_index >= 81:
        return "ceo_must_review"  # Red
    elif vibecoding_index >= 61:
        return "ceo_should_review"  # Orange
    elif vibecoding_index >= 31:
        return "tech_lead_review"  # Yellow
    else:
        return "auto_approve"  # Green
```

### Routing Behavior

```yaml
Green (0-30):
  Action: Auto-approve (no CEO involvement)
  SLA: <1 minute
  Notification: None
  Evidence: Store for audit

Yellow (31-60):
  Action: Tech Lead review required
  SLA: <4 hours
  Notification: Slack DM to Tech Lead
  Evidence: Store + Tech Lead feedback

Orange (61-80):
  Action: CEO should review (not mandatory)
  SLA: <24 hours
  Notification: Slack + Email to CEO
  Evidence: Store + CEO feedback if reviewed

Red (81-100):
  Action: CEO must review (mandatory)
  SLA: <48 hours
  Notification: Slack + Email + SMS to CEO
  Evidence: Store + CEO approval required
```

---

## ⚡ PERFORMANCE BUDGET

### Latency Targets

```yaml
Signal Calculation (P95):
  architectural_smell: <150ms       # AST parsing is expensive
  abstraction_complexity: <100ms
  ai_dependency_ratio: <50ms        # Simple ratio calculation
  change_surface_area: <80ms
  drift_velocity: <120ms            # Historical query

Total (Sequential): <500ms (P95)
Total (Parallel): <150ms (P95)     # Run signals in parallel
```

### Optimization Strategy

```python
async def calculate_vibecoding_index(
    submission: CodeSubmission,
    context: ProjectContext
) -> VibecodingIndex:
    """
    Calculate Vibecoding Index with parallelization.

    Performance target: <150ms (P95) via parallel execution.
    """
    # Run all 5 signals in parallel
    signal_results = await asyncio.gather(
        calculate_architectural_smell(submission),
        calculate_abstraction_complexity(submission),
        calculate_ai_dependency_ratio(submission),
        calculate_change_surface_area(submission),
        calculate_drift_velocity(submission, context),
        return_exceptions=True,  # Don't fail if one signal errors
    )

    # Unpack results
    arch_smell, abstraction, ai_ratio, surface_area, drift = signal_results

    # Calculate composite index
    index = (
        arch_smell * 0.25 +
        abstraction * 0.15 +
        ai_ratio * 0.20 +
        surface_area * 0.20 +
        drift * 0.20
    )

    # Apply MAX CRITICALITY OVERRIDE
    index = await apply_max_criticality_override(submission, index)

    # Generate explainability data
    explainability = generate_explainability(
        index, arch_smell, abstraction, ai_ratio, surface_area, drift
    )

    return VibecodingIndex(
        score=index,
        routing=route_submission(index, explainability.critical_override),
        signals={
            "architectural_smell": arch_smell,
            "abstraction_complexity": abstraction,
            "ai_dependency_ratio": ai_ratio,
            "change_surface_area": surface_area,
            "drift_velocity": drift,
        },
        explainability=explainability
    )
```

---

## 📈 CALIBRATION & LEARNING

### Weekly Calibration Process

```yaml
Data Collection:
  - CEO overrides (approved Red → reject, or rejected Green → approve)
  - False positives (CEO disagrees with Red/Orange)
  - False negatives (CEO escalates Yellow/Green)

Weight Adjustment Algorithm:
  1. Count CEO overrides per signal
  2. If signal contributed to false positive → decrease weight by 10%
  3. If signal missed true positive → increase weight by 10%
  4. Maintain weight sum = 1.0 (renormalize)

Example:
  Week 1 Overrides:
    - 3 false positives from architectural_smell
    - 2 false negatives from ai_dependency_ratio

  Weight Adjustment:
    - architectural_smell: 0.25 → 0.22 (-10% for 3 false positives)
    - ai_dependency_ratio: 0.20 → 0.22 (+10% for 2 false negatives)
    - Renormalize other weights to sum = 1.0

  Updated Weights:
    - architectural_smell: 0.22
    - abstraction_complexity: 0.15
    - ai_dependency_ratio: 0.22
    - change_surface_area: 0.20
    - drift_velocity: 0.21
```

### Success Metrics

```yaml
Target Metrics (from Success-Criteria-v2.yaml):
  CEO Agreement Rate: >95%
    Measurement: (CEO agrees / Total routing decisions) * 100

  False Positive Rate: <10%
    Measurement: (CEO disagrees with Red/Orange / Total Red/Orange) * 100

  False Negative Rate: <5%
    Measurement: (CEO escalates Green/Yellow / Total Green/Yellow) * 100

  Calculation Latency: <500ms (P95)
    Measurement: 95th percentile of index calculation time

  Explainability Coverage: 100%
    Measurement: All scores >30 have full explainability data
```

---

## ✅ VALIDATION CHECKLIST

**Before Week 1 execution:**

- [ ] CEO Calibration Session completed (2 hours)
- [ ] Initial weights configured in `governance_signals.yaml`
- [ ] MAX CRITICALITY OVERRIDE logic implemented
- [ ] Explainability output format validated
- [ ] Performance benchmark: <500ms P95 (sequential) or <150ms (parallel)
- [ ] Unit tests for all 5 signals (95%+ coverage)
- [ ] Integration test with real PR data
- [ ] CEO reviews 10 sample outputs, confirms explainability

**CTO Gate Review Criteria:**

- [ ] All 5 signals implemented with clear algorithms
- [ ] Explainability meets spec (VIBECODING-INDEX-EXPLAINABILITY-SPEC.md)
- [ ] Performance budget met (<500ms P95)
- [ ] Critical path override logic correct
- [ ] Weekly calibration process documented
- [ ] Success metrics defined and measurable

---

**Document Status**: ✅ **COMPLETE**
**Next**: Document 4 - Success-Criteria-v2.yaml
**Phase 0 Progress**: 3/6 documents complete (50%)
