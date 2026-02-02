# Auto-Generation Fail-Safe Policy
## SDLC Orchestrator Governance System

**Version:** 1.0
**Effective Date:** January 27, 2026
**Owner:** CTO

---

## 1. CORE PRINCIPLE

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   AUTO-GENERATION MAY FAIL                                      │
│   BUT GOVERNANCE MUST NEVER HARD-BLOCK                          │
│   DUE TO AUTO-GENERATION FAILURE                                │
│                                                                 │
│   Developer productivity > Auto-generation elegance             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Rationale:** Auto-generation is a convenience feature, not a gate.
If it fails, developers must have a fast manual path to compliance.

---

## 2. FAILURE MODES & RESPONSES

### 2.1 LLM Service Failures

| Failure Mode | Detection | Response | Developer Experience |
|--------------|-----------|----------|---------------------|
| LLM Timeout (>10s) | `LLMTimeoutError` | Fallback to template | "LLM slow, using template. Edit as needed." |
| LLM Rate Limited | `LLMRateLimitError` | Fallback to template | "LLM busy, using template. Edit as needed." |
| LLM Error (500) | `LLMServiceError` | Fallback to template | "LLM unavailable, using template." |
| LLM Quality Low | `quality_score < 0.7` | Fallback to template | "LLM output unclear, using template." |
| LLM Hallucination | Detected by validator | Flag + template | "LLM may have hallucinated. Review carefully." |

### 2.2 Fallback Chain

```
LLM Generation
     ↓ (fail)
Template Generation
     ↓ (fail)
Minimal Placeholder
     ↓ (always succeeds)
Developer Edits
```

**Guarantee:** Developer can ALWAYS proceed to governance validation within 2 minutes,
regardless of auto-generation state.

---

## 3. IMPLEMENTATION

### 3.1 Intent Generation Fallback

```python
async def generate_intent(task: Task) -> IntentDocument:
    """
    Intent generation with fail-safe chain.

    GUARANTEE: Always returns a valid IntentDocument within 15 seconds.
    """

    # Level 1: Try LLM generation
    try:
        intent = await self._generate_with_llm(task, timeout=10)
        quality = await self._assess_quality(intent)

        if quality >= 0.7:
            return IntentDocument(
                content=intent,
                generation_method="llm",
                quality_score=quality,
                is_auto_generated=True,
                requires_review=False,
            )
        else:
            logger.warning(f"LLM quality low ({quality}), falling back to template")
            # Fall through to template

    except (LLMTimeout, LLMRateLimited, LLMServiceError) as e:
        logger.warning(f"LLM failed: {e}, falling back to template")
        # Fall through to template

    # Level 2: Template generation (always works)
    template = self._generate_template(task)

    return IntentDocument(
        content=template,
        generation_method="template",
        quality_score=0.5,
        is_auto_generated=True,
        requires_review=True,  # Flag for human review
        fallback_reason="LLM unavailable or quality low",
    )

def _generate_template(self, task: Task) -> str:
    """
    Template-based intent generation.

    GUARANTEE: Always succeeds, always fast (<100ms).
    """
    return f"""
# Intent: {task.title}

## Why This Change?
[TODO: Explain the business reason for this change]

Task: {task.id}
Description: {task.description}

## What Problem Does It Solve?
[TODO: Describe the problem this change addresses]

## Alternatives Considered
[TODO: List alternatives and why they were rejected]

---
⚠️ This intent was auto-generated from a template.
   Please fill in the [TODO] sections before submitting.
"""
```

### 3.2 Ownership Suggestion Fallback

```python
async def suggest_ownership(file_path: str, repo: Repository) -> OwnershipSuggestion:
    """
    Ownership suggestion with fail-safe chain.

    GUARANTEE: Always returns a suggestion.
    """

    suggestions = []

    # Try CODEOWNERS (most reliable)
    try:
        codeowners = await self._check_codeowners(file_path, repo)
        if codeowners:
            suggestions.append(Suggestion(owner=codeowners, confidence=1.0, source="CODEOWNERS"))
    except Exception as e:
        logger.warning(f"CODEOWNERS check failed: {e}")

    # Try git blame
    try:
        blame = await self._get_git_blame_owner(file_path, repo)
        if blame:
            suggestions.append(Suggestion(owner=blame, confidence=0.7, source="git_blame"))
    except Exception as e:
        logger.warning(f"Git blame failed: {e}")

    # Try directory pattern
    try:
        dir_owner = await self._check_directory_pattern(file_path)
        if dir_owner:
            suggestions.append(Suggestion(owner=dir_owner, confidence=0.6, source="directory"))
    except Exception as e:
        logger.warning(f"Directory pattern failed: {e}")

    # Fallback: Task creator or "UNASSIGNED"
    if not suggestions:
        suggestions.append(Suggestion(
            owner="@team-leads",  # Default escalation
            confidence=0.3,
            source="fallback",
            message="Could not determine owner. Please assign manually."
        ))

    return max(suggestions, key=lambda s: s.confidence)
```

### 3.3 Context Attachment Fallback

```python
async def attach_context(pr: PullRequest) -> ContextAttachment:
    """
    Context attachment with fail-safe.

    GUARANTEE: PR can proceed even if context lookup fails.
    """

    try:
        # Try auto-detection
        modules = await self._extract_modules_from_diff(pr.diff)
        adrs = await self._find_adrs_for_modules(modules)
        specs = await self._find_specs_for_modules(modules)

        if adrs or specs:
            return ContextAttachment(
                adrs=adrs,
                specs=specs,
                auto_attached=True,
            )

    except Exception as e:
        logger.warning(f"Context auto-attachment failed: {e}")

    # Fallback: Prompt developer
    return ContextAttachment(
        adrs=[],
        specs=[],
        auto_attached=False,
        message="Could not auto-detect context. Please manually link relevant ADRs/specs.",
        prompt_required=True,
    )
```

---

## 4. UI/UX FOR FALLBACK STATES

### 4.1 Visual Indicators

| State | Visual | Message |
|-------|--------|---------|
| LLM Generated | 🟢 Green badge | "Auto-generated by AI" |
| Template Generated | 🟡 Yellow badge | "Generated from template. Please review." |
| Fallback | 🟠 Orange badge | "Auto-generation failed. Manual input required." |
| Manual | ⚪ No badge | (User wrote it) |

### 4.2 Developer Messages

**On LLM Success:**
```
✅ Intent auto-generated successfully.
   Review and edit if needed, then submit.
   [Edit] [Submit]
```

**On Template Fallback:**
```
⚠️ AI generation unavailable. Template provided.
   Please fill in the [TODO] sections.
   [Edit Template] [Submit]
```

**On Complete Failure:**
```
❌ Auto-generation failed. Please write manually.
   Use the template below as a starting point.
   [Use Template] [Write from Scratch]
```

---

## 5. MONITORING & ALERTS

### 5.1 Auto-Generation Health Metrics

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| LLM Success Rate | > 90% | 70-90% | < 70% |
| Average Generation Time | < 5s | 5-10s | > 10s |
| Template Fallback Rate | < 10% | 10-30% | > 30% |
| Developer Complaints | < 1/day | 1-3/day | > 3/day |

### 5.2 Alert Configuration

```yaml
auto_generation_alerts:
  llm_failure_rate:
    threshold: 30%
    window: 1_hour
    severity: critical
    action: "Notify DevOps, consider LLM service restart"

  template_fallback_spike:
    threshold: 50%
    window: 30_minutes
    severity: warning
    action: "Check LLM health, notify Tech Lead"

  developer_friction:
    threshold: ">10 minutes average generation time"
    window: 1_day
    severity: major
    action: "Investigate auto-generation performance"
```

---

## 6. GOVERNANCE IMPACT

### 6.1 Fail-Safe Does NOT Bypass Governance

```
IMPORTANT: This policy ensures developers can SUBMIT to governance quickly.
           It does NOT allow bypassing governance checks.

Auto-generation → Fallback → Template → Manual Edit
                                            ↓
                              Governance Validation (STILL REQUIRED)
                                            ↓
                              Pass / Fail (same rules apply)
```

### 6.2 Quality Tracking for Fallback Submissions

```python
# Track if fallback submissions have higher rejection rate
submission_analytics:
  segment_by: generation_method  # llm, template, manual
  track:
    - first_pass_rate
    - rejection_reasons
    - time_to_compliance
```

---

## 7. SIGNATURES

### CTO Commitment

I, **Nhat Quang (CTO)**, approve this Fail-Safe Policy and commit to:
1. Never blocking developers due to auto-generation failure
2. Maintaining fallback chain availability
3. Monitoring auto-generation health
4. Escalating issues within 1 hour of critical alerts

**Signature:** ✅ **APPROVED**
**Date:** January 28, 2026
