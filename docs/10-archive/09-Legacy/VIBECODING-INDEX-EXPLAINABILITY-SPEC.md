# Vibecoding Index Explainability Specification
## SDLC Orchestrator Governance System

**Version:** 1.0
**Effective Date:** January 27, 2026
**Owner:** CPO

---

## 1. CORE PRINCIPLE

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   EVERY SCORE > 30 MUST BE EXPLAINABLE                         │
│                                                                 │
│   If CEO sees "Index = 67" but doesn't know                    │
│   WHY it's 67 and WHAT TO LOOK AT FIRST,                       │
│   → CEO will ignore the system                                  │
│   → CEO will go back to manual review                          │
│   → Product fails                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. EXPLAINABILITY REQUIREMENTS

### 2.1 For Every Score > 30

The system MUST display:

1. **Composite Score** (0-100)
2. **Top 3 Contributing Signals** with:
   - Signal name
   - Signal score
   - Contribution percentage
   - Specific evidence (file, line, metric)
3. **Suggested Focus Area** (where to look first)
4. **Comparison to Baseline** (is this normal for this type of PR?)

### 2.2 Example Output

```
┌─────────────────────────────────────────────────────────────────┐
│ PR #234: "Add user authentication flow"                         │
│ VIBECODING INDEX: 72 🟠 ORANGE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📊 TOP 3 CONTRIBUTORS                                          │
│                                                                 │
│ 1. CHANGE SURFACE AREA (32% of score)                          │
│    Score: 85/100                                                │
│    Evidence:                                                    │
│    • 14 files changed (threshold: 5)                           │
│    • 3 modules touched: auth, users, api                       │
│    • 2 API contracts modified                                  │
│    Suggestion: Consider splitting into smaller PRs             │
│                                                                 │
│ 2. AI DEPENDENCY RATIO (28% of score)                          │
│    Score: 92/100                                                │
│    Evidence:                                                    │
│    • 92% of code is AI-generated (340/370 lines)              │
│    • Only 8% human modification                                │
│    • AI Session: Claude Code, 2 hours ago                      │
│    Suggestion: Review AI output carefully, add more tests      │
│                                                                 │
│ 3. ARCHITECTURAL SMELL (22% of score)                          │
│    Score: 68/100                                                │
│    Evidence:                                                    │
│    • God class detected: UserService.py (680 LOC)             │
│    • Feature envy: auth_handler uses UserRepo 12 times        │
│    Suggestion: Consider extracting AuthenticationService       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 👁️ SUGGESTED FOCUS                                             │
│                                                                 │
│ Start with: backend/app/services/user_service.py               │
│ Reason: God class pattern, high AI dependency                  │
│ Lines to review: 120-180 (auth logic), 450-520 (validation)   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 📈 COMPARISON                                                   │
│                                                                 │
│ • Average index for "auth" PRs: 45                             │
│ • This PR: 72 (+60% above average)                             │
│ • Similar PRs that passed: PR #198 (index 48), PR #215 (52)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. SIGNAL BREAKDOWN SPECIFICATION

### 3.1 Architectural Smell (Weight: 0.25)

| Smell Type | Detection Method | Evidence Format |
|------------|-----------------|-----------------|
| God Class | LOC > 500 | `{file}: {loc} lines (threshold: 500)` |
| Feature Envy | External calls > 2× internal | `{method} uses {class} {n} times` |
| Shotgun Surgery | Files > 10 | `{n} files changed across {m} modules` |
| Parallel Inheritance | Duplicate hierarchies | `{class_a} and {class_b} have parallel structure` |

**Explainability Output:**
```yaml
architectural_smell:
  score: 68
  weight: 0.25
  contribution: 17  # 68 × 0.25
  top_issues:
    - type: "god_class"
      file: "backend/app/services/user_service.py"
      evidence: "680 lines (threshold: 500)"
      suggestion: "Extract AuthenticationService, ProfileService"
    - type: "feature_envy"
      file: "backend/app/handlers/auth_handler.py"
      evidence: "Uses UserRepository 12 times, own methods 3 times"
      suggestion: "Move auth logic to UserService or create AuthService"
```

### 3.2 Abstraction Complexity (Weight: 0.15)

| Metric | Threshold | Evidence Format |
|--------|-----------|-----------------|
| Inheritance Depth | > 3 levels | `{class} has {n}-level inheritance` |
| Interface Count | > 5 for simple feature | `{n} interfaces for {feature}` |
| Generic Type Depth | > 2 levels | `{type} has {n}-level generics` |
| Factory Abuse | Factory for 1 impl | `{factory} creates only {impl}` |

### 3.3 AI Dependency Ratio (Weight: 0.20)

| Metric | Red Flag | Evidence Format |
|--------|----------|-----------------|
| AI Lines / Total | > 80% | `{ai_lines}/{total_lines} ({ratio}%)` |
| Human Modification | < 10% | `Only {mod_lines} lines modified by human` |
| AI Session Age | < 1 hour | `Generated {time} ago, minimal review time` |

**Red Flag Combination:**
```
IF ai_ratio > 0.8 AND human_modification < 0.1:
    flag: "HIGH_AI_DEPENDENCY_LOW_REVIEW"
    message: "92% AI-generated with minimal human review.
              Potential rubber-stamping detected."
```

### 3.4 Change Surface Area (Weight: 0.20)

| Factor | Threshold | Evidence Format |
|--------|-----------|-----------------|
| Files Changed | > 5 | `{n} files changed` |
| Modules Touched | > 2 | `{n} modules: {list}` |
| API Contracts | > 1 | `{n} API contracts modified` |
| Database Schema | Any | `Schema change detected: {tables}` |
| Security Files | Any | `Security-sensitive file: {file}` |

### 3.5 Drift Velocity (Weight: 0.20)

| Metric | Threshold | Evidence Format |
|--------|-----------|-----------------|
| New Patterns | > 2/week | `{n} new patterns introduced` |
| Deprecated Patterns | > 1/week | `{n} deprecated patterns used` |
| Naming Inconsistency | > 5% | `{n} naming convention violations` |

---

## 4. MAX CRITICALITY OVERRIDE

### 4.1 Problem

Expert 2 identified: A 1-line change to `auth.py` could have:
- `architectural_smell`: 0
- `change_surface`: 0
- `ai_dependency`: 0
- **Average Index: 0 (Green)** ← DANGER!

### 4.2 Solution: Critical Path Override

```yaml
# backend/app/config/critical_paths.yaml

critical_paths:
  description: |
    Files in these paths automatically boost Vibecoding Index to minimum 80 (Red)
    regardless of other signal scores.

  paths:
    security:
      - "auth/**"
      - "security/**"
      - "backend/app/services/auth*"
      - "backend/app/middleware/auth*"
      - "**/authentication*"
      - "**/authorization*"

    payment:
      - "payment/**"
      - "billing/**"
      - "**/payment*"
      - "**/stripe*"
      - "**/paypal*"

    database_schema:
      - "prisma/schema.prisma"
      - "migrations/**"
      - "alembic/**"

    infrastructure:
      - "docker-compose*.yml"
      - "k8s/**"
      - ".github/workflows/**"
      - "terraform/**"

    secrets:
      - "**/.env*"
      - "**/secrets*"
      - "**/credentials*"

  override_rule:
    if_touches_critical_path: true
    minimum_index: 80
    routing: "ceo_must_review"
    message: "Critical path modified. CEO review required regardless of other signals."
```

### 4.3 Implementation

```python
def calculate_vibecoding_index(submission: CodeSubmission) -> VibecodingIndex:
    # Calculate base signals
    arch_smell = calculate_architectural_smell(submission)
    abstraction = calculate_abstraction_complexity(submission)
    ai_dependency = calculate_ai_dependency_ratio(submission)
    surface_area = calculate_change_surface_area(submission)
    drift = calculate_drift_velocity(submission)

    # Weighted average
    base_index = (
        arch_smell * 0.25 +
        abstraction * 0.15 +
        ai_dependency * 0.20 +
        surface_area * 0.20 +
        drift * 0.20
    )

    # CRITICAL PATH OVERRIDE
    critical_hit = check_critical_paths(submission.changed_files)

    if critical_hit:
        final_index = max(base_index, 80)  # Minimum 80 for critical paths
        override_reason = f"Critical path modified: {critical_hit.path}"
    else:
        final_index = base_index
        override_reason = None

    return VibecodingIndex(
        score=final_index,
        base_score=base_index,
        critical_override=critical_hit is not None,
        override_reason=override_reason,
        # ... rest of signals
    )
```

---

## 5. SUGGESTED FOCUS ALGORITHM

### 5.1 Focus Selection Logic

```python
def suggest_focus(submission: CodeSubmission, signals: Signals) -> FocusSuggestion:
    """
    Determine where CEO should look first.

    Priority:
    1. Critical path files
    2. Highest-scoring signal's evidence files
    3. Files with multiple issues
    4. Largest files changed
    """

    focus_candidates = []

    # Priority 1: Critical paths
    for file in submission.changed_files:
        if is_critical_path(file):
            focus_candidates.append(FocusCandidate(
                file=file,
                reason="Critical path (security/payment/infra)",
                priority=1
            ))

    # Priority 2: Top signal evidence
    top_signal = max(signals, key=lambda s: s.contribution)
    for evidence in top_signal.evidence:
        focus_candidates.append(FocusCandidate(
            file=evidence.file,
            reason=f"Top signal ({top_signal.name}): {evidence.issue}",
            priority=2
        ))

    # Priority 3: Files with multiple issues
    issue_count = count_issues_per_file(signals)
    for file, count in issue_count.items():
        if count >= 2:
            focus_candidates.append(FocusCandidate(
                file=file,
                reason=f"{count} issues detected in this file",
                priority=3
            ))

    # Return top suggestion
    focus_candidates.sort(key=lambda c: c.priority)
    top = focus_candidates[0]

    # Get specific lines to review
    lines_to_review = get_interesting_lines(top.file, signals)

    return FocusSuggestion(
        file=top.file,
        reason=top.reason,
        lines=lines_to_review,
        estimated_review_time=estimate_review_time(top.file)
    )
```

### 5.2 Lines to Review Detection

```python
def get_interesting_lines(file: str, signals: Signals) -> List[LineRange]:
    """
    Get specific line ranges that need CEO attention.
    """
    interesting = []

    # From architectural smell
    if god_class := signals.arch_smell.get_god_class(file):
        # Focus on the longest methods
        for method in god_class.top_methods[:3]:
            interesting.append(LineRange(
                start=method.start_line,
                end=method.end_line,
                reason=f"Long method: {method.name} ({method.loc} lines)"
            ))

    # From AI dependency
    if ai_blocks := signals.ai_dependency.get_ai_blocks(file):
        for block in ai_blocks:
            interesting.append(LineRange(
                start=block.start_line,
                end=block.end_line,
                reason=f"AI-generated block, low human modification"
            ))

    # Security-sensitive patterns
    security_patterns = find_security_patterns(file)
    for pattern in security_patterns:
        interesting.append(LineRange(
            start=pattern.line,
            end=pattern.line + 10,
            reason=f"Security-sensitive: {pattern.type}"
        ))

    return merge_overlapping_ranges(interesting)[:5]  # Top 5 ranges
```

---

## 6. COMPARISON BASELINE

### 6.1 Baseline Calculation

```python
def get_comparison_baseline(submission: CodeSubmission) -> Baseline:
    """
    Compare this PR's index to historical baseline.
    """

    # Determine PR category
    categories = classify_pr(submission)
    # e.g., ["auth", "feature", "backend"]

    # Get historical data for similar PRs
    historical = query_historical_prs(
        categories=categories,
        time_window="90_days",
        limit=100
    )

    avg_index = mean([pr.index for pr in historical])
    stddev = std([pr.index for pr in historical])

    return Baseline(
        category=categories[0],
        average_index=avg_index,
        stddev=stddev,
        this_pr_deviation=(submission.index - avg_index) / stddev,
        similar_prs_passed=[pr for pr in historical if pr.passed and pr.index < submission.index][:3],
        similar_prs_rejected=[pr for pr in historical if not pr.passed and pr.index > submission.index][:3],
    )
```

### 6.2 Display Format

```
📈 COMPARISON TO BASELINE

Category: "Auth Feature"
• Average index for auth PRs: 45
• Standard deviation: 12
• This PR: 72 (+2.25 σ above average)

Similar PRs that PASSED:
• PR #198: index 48 - "OAuth2 integration"
• PR #215: index 52 - "Session management"

Similar PRs that were REJECTED:
• PR #189: index 78 - "Password reset" (rejected: security concern)
• PR #201: index 81 - "API keys" (rejected: missing tests)
```

---

## 7. UI/UX SPECIFICATION

### 7.1 Dashboard Widget

```
┌─────────────────────────────────────────────────────────────────┐
│ VIBECODING INDEX                                                │
│                                                                 │
│     72                                                          │
│   ┌─────────────────────────────────────────┐                  │
│   │████████████████████████████░░░░░░░░░░░░│ 72/100           │
│   └─────────────────────────────────────────┘                  │
│   0        30        60        80       100                    │
│            │         │         │                                │
│          GREEN    YELLOW    ORANGE      RED                    │
│                              ↑ YOU                              │
│                                                                 │
│ 📊 Click to see breakdown →                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Expanded View (On Click)

Full explainability view as shown in Section 2.2.

### 7.3 API Response

```json
{
  "pr_number": 234,
  "vibecoding_index": {
    "score": 72,
    "category": "orange",
    "routing": "ceo_should_review",
    "critical_override": false
  },
  "signals": {
    "architectural_smell": {
      "score": 68,
      "weight": 0.25,
      "contribution": 17,
      "issues": [
        {
          "type": "god_class",
          "file": "backend/app/services/user_service.py",
          "evidence": "680 lines (threshold: 500)",
          "suggestion": "Extract AuthenticationService"
        }
      ]
    }
  },
  "top_contributors": [
    {"signal": "change_surface_area", "contribution_pct": 32},
    {"signal": "ai_dependency_ratio", "contribution_pct": 28},
    {"signal": "architectural_smell", "contribution_pct": 22}
  ],
  "suggested_focus": {
    "file": "backend/app/services/user_service.py",
    "reason": "God class pattern, high AI dependency",
    "lines": [
      {"start": 120, "end": 180, "reason": "auth logic"},
      {"start": 450, "end": 520, "reason": "validation"}
    ],
    "estimated_review_time": "15 minutes"
  },
  "baseline_comparison": {
    "category": "auth",
    "average_index": 45,
    "deviation": "+2.25σ",
    "similar_passed": ["PR #198", "PR #215"]
  }
}
```

---

## 8. SIGNATURES

### CPO Commitment

I, **CPO**, approve this Explainability Specification and commit to:
1. Ensuring every score > 30 has full explainability
2. Monitoring CEO trust in the index
3. Iterating on explainability based on CEO feedback
4. Not deploying index changes without CEO preview

**Signature:** ✅ **APPROVED**
**Date:** January 28, 2026
