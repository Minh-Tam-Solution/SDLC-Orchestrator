# Auto-Generation Requirements - Latency Targets & Fallback Specifications

**Document Version:** 1.0.0
**Date Created:** January 27, 2026
**Author:** CTO + AI Team
**Status:** PHASE 0 Technical Deliverable
**Purpose:** Define latency targets and fallback specifications for auto-generation layer

**Authority:** AUTO-GENERATION-FAIL-SAFE-POLICY.md

---

## 📊 EXECUTIVE SUMMARY

**Goal:** Reduce developer compliance overhead from **30 minutes → <5 minutes per PR** (83% reduction)

**Strategy:** Auto-generate 80% of compliance artifacts (intent, ownership, context, attestation)

**Critical Requirement:** Developer NEVER blocked by auto-generation failure (<2 min fallback guaranteed)

---

## 🎯 BASELINE: MANUAL COMPLIANCE (BEFORE AUTO-GENERATION)

### Time Breakdown per PR (Manual)

| Artifact | Manual Time | Failure Rate | Pain Point |
|----------|-------------|--------------|------------|
| **Intent Statement** | 10 min | 30% forget | "Why" not captured at time of writing |
| **Ownership Annotation** | 5 min | 40% skip | Tedious, forgotten until PR rejected |
| **Context Attachment (ADRs)** | 8 min | 50% incomplete | Hard to find relevant ADRs |
| **AI Code Attestation** | 7 min | 20% skip | Form filling feels like busywork |
| **TOTAL** | **30 min** | - | Developer frustration + CEO time waste |

**Key Insight:** Developers don't refuse compliance out of malice, they forget or find it tedious.

---

## ⚡ TARGET: AUTO-GENERATED COMPLIANCE

### Time Breakdown per PR (With Auto-Generation)

| Artifact | Auto-Gen Time | Human Review | Total Time | Savings |
|----------|---------------|--------------|------------|---------|
| **Intent Statement** | 8s (LLM) | 2 min (edit) | **2min 8s** | **7min 52s** |
| **Ownership Annotation** | 2s (git blame) | 30s (confirm) | **32s** | **4min 28s** |
| **Context Attachment** | 5s (ADR search) | 1 min (validate) | **1min 5s** | **6min 55s** |
| **AI Code Attestation** | 3s (session data) | 1 min (confirm) | **1min 3s** | **5min 57s** |
| **TOTAL** | **18s** | **4min 30s** | **4min 48s** | **25min 12s** |

**Achievement:** Developer spends <5 min per PR (83% faster), no waiting for LLM.

---

## 🔧 AUTO-GENERATION COMPONENT 1: INTENT STATEMENT

### Current State (Manual)

**Developer Process:**
1. Creates PR
2. Governance rejects: "Missing intent statement"
3. Developer writes docs/intents/TASK-123-intent.md from scratch
4. **Time:** 10 minutes
5. **Failure Rate:** 30% forget, re-submit after rejection

**Pain Points:**
- Developer context: "Why did I write this?" (2 weeks ago, forgot)
- Blank page syndrome: "Where do I start?"
- No template: Each developer invents format

---

### Target State (Auto-Generated)

**Auto-Generation Process:**
1. PR created → Governance calls `generate_intent(task)`
2. LLM reads:
   - Task description from Linear/Jira
   - PR diff summary
   - Recent commit messages
3. LLM generates intent document (3 sections):
   - **Why This Change?** (business reason)
   - **What Problem Does It Solve?** (user pain point)
   - **Alternatives Considered** (trade-offs)
4. Developer reviews (2 min), edits if needed
5. **Total Time:** 2 min 8s (10min → 2min = 8min saved)

**Requirements:**

| Requirement | Spec | Acceptance Criteria |
|-------------|------|---------------------|
| **Latency** | <10s (p95) | LLM response within 10 seconds |
| **Quality** | >0.7 score | 70% of content usable without edit |
| **Fallback** | <15s total | If LLM fails, template ready in 5s |
| **Accuracy** | >80% | Developer accepts without major rewrite |

**Latency Budget:**
```
Primary (Ollama qwen3:32b):
  - Token count: ~200 tokens input, ~500 tokens output
  - Expected latency: 5-8 seconds (60 tok/s)
  - Timeout: 10 seconds

Fallback 1 (Template):
  - Load template from disk: <100ms
  - Fill placeholders (task title, description): <50ms
  - Total fallback latency: <150ms

Fallback 2 (Minimal Placeholder):
  - Generate empty intent template: <10ms
  - Developer fills manually: 10 minutes (acceptable if rare)
```

**Failure Handling:**
- **LLM Timeout (>10s):** Switch to template, notify developer: "Auto-generation slow, using template instead"
- **LLM Quality Low (<0.7):** Show warning badge: "🟡 Generated from template. Please review carefully."
- **LLM Rate Limited:** Queue request, show estimated wait time: "Queue: 2 requests ahead, ETA 30s"

---

### Implementation Spec: generate_intent()

```python
async def generate_intent(
    task: Task,
    pr: PullRequest,
    timeout: int = 10
) -> IntentDocument:
    """
    Generate intent statement with LLM + template fallback.

    Requirements:
      - Latency: <10s (p95)
      - Quality: >0.7 score
      - Fallback: <2 min developer time if failure

    Returns:
      IntentDocument with content, quality score, generation method
    """

    # LEVEL 1: Try LLM generation
    try:
        prompt = f"""
        Task: {task.title}
        Description: {task.description}
        Acceptance Criteria: {task.acceptance_criteria}

        PR Summary: {pr.diff_summary}
        Files Changed: {pr.files_changed}

        Generate an intent document with:
        1. Why This Change? (business reason, not technical details)
        2. What Problem Does It Solve? (user pain point)
        3. Alternatives Considered (what you rejected and why)

        Output in Markdown format, 200-300 words.
        """

        intent_content = await ollama_service.generate(
            model="qwen3:32b",
            prompt=prompt,
            timeout=timeout,  # 10s
            max_tokens=500,
        )

        # Assess quality
        quality_score = await assess_intent_quality(intent_content, task)

        if quality_score >= 0.7:
            return IntentDocument(
                content=intent_content,
                quality_score=quality_score,
                generation_method="llm",
                auto_generated=True,
                requires_review=False,
            )
        else:
            logger.warning(f"LLM quality low ({quality_score:.2f}), falling back to template")
            # Fall through to template

    except (LLMTimeout, LLMServiceError) as e:
        logger.warning(f"LLM generation failed: {e}, falling back to template")
        # Fall through to template

    # LEVEL 2: Template fallback
    template_content = generate_intent_template(task, pr)

    return IntentDocument(
        content=template_content,
        quality_score=0.5,  # Template quality
        generation_method="template",
        auto_generated=True,
        requires_review=True,  # Template needs human review
    )


def generate_intent_template(task: Task, pr: PullRequest) -> str:
    """
    Template fallback for intent generation.

    Latency: <150ms (guaranteed)
    """
    return f"""
# Intent: {task.title}

## Why This Change?
[TODO: Explain the business reason for this change]

Business Context:
- Task: {task.title}
- Requested by: {task.requester}
- Due date: {task.due_date}

## What Problem Does It Solve?
[TODO: Describe the user pain point or system issue]

Current State:
- {task.problem_statement or "Describe current state..."}

## Alternatives Considered
[TODO: What other approaches did you reject? Why?]

1. Alternative A: [Describe] → Rejected because [reason]
2. Alternative B: [Describe] → Rejected because [reason]

---

**Auto-Generated:** This intent was generated from a template because AI generation failed.
Please review and fill in the [TODO] sections.

**Estimated Time to Complete:** 5 minutes
"""


async def assess_intent_quality(intent: str, task: Task) -> float:
    """
    Assess intent quality (0.0 to 1.0).

    Criteria:
      - Has all 3 sections (Why, What, Alternatives): 0.3
      - Mentions task title/description: 0.2
      - Explains business reason (not just technical details): 0.2
      - Considers alternatives (at least 2): 0.2
      - No placeholders like [TODO] or [INSERT]: 0.1

    Latency: <100ms
    """
    score = 0.0

    # Check sections
    if "Why This Change?" in intent:
        score += 0.1
    if "What Problem Does It Solve?" in intent:
        score += 0.1
    if "Alternatives Considered" in intent:
        score += 0.1

    # Check task context
    if task.title.lower() in intent.lower():
        score += 0.1
    if task.description and task.description[:50].lower() in intent.lower():
        score += 0.1

    # Check business context (not just technical)
    business_keywords = ["user", "customer", "business", "revenue", "cost", "value", "pain point"]
    if any(keyword in intent.lower() for keyword in business_keywords):
        score += 0.2

    # Check alternatives (at least 2 mentioned)
    alternatives_count = intent.lower().count("alternative")
    if alternatives_count >= 2:
        score += 0.2
    elif alternatives_count == 1:
        score += 0.1

    # Check no placeholders
    placeholders = ["[TODO]", "[INSERT]", "[FILL IN]", "..."]
    if not any(placeholder.lower() in intent.lower() for placeholder in placeholders):
        score += 0.1

    return min(1.0, score)
```

**Performance Requirements:**
- **LLM Latency P95:** <10s (measured at Ollama endpoint)
- **Template Fallback P95:** <150ms (file I/O + string formatting)
- **Quality Assessment P95:** <100ms (regex parsing + scoring)
- **Total End-to-End P95:** <10.25s (LLM path) or <0.25s (template path)

---

## 🔧 AUTO-GENERATION COMPONENT 2: OWNERSHIP ANNOTATION

### Current State (Manual)

**Developer Process:**
1. Creates new file or modifies existing file
2. Governance rejects: "Missing @owner annotation"
3. Developer adds header manually:
   ```python
   # @owner: @backend-lead
   # @module: user_management
   # @created: 2026-01-27
   ```
4. **Time:** 5 minutes (find correct owner, add header, commit)
5. **Failure Rate:** 40% skip (tedious busywork)

---

### Target State (Auto-Generated)

**Auto-Generation Process:**
1. PR created → Governance calls `suggest_ownership(file)`
2. Algorithm checks 4 sources (no LLM needed, deterministic):
   - **CODEOWNERS file:** Declared owner for path pattern
   - **Git blame:** Most recent committer (last 90 days)
   - **Directory pattern:** backend/app/services/** → Backend Team
   - **Fallback:** Task creator
3. Pre-fill @owner annotation in file header
4. Developer confirms (30s) or changes owner
5. **Total Time:** 32s (5min → 32s = 4min 28s saved)

**Requirements:**

| Requirement | Spec | Acceptance Criteria |
|-------------|------|---------------------|
| **Latency** | <2s (p95) | Suggestion ready immediately |
| **Accuracy** | >90% | Developer accepts without change |
| **Fallback** | Always succeeds | Even if all sources fail, use task creator |

**Latency Budget:**
```
Source 1 (CODEOWNERS):
  - Parse CODEOWNERS file: <50ms (cached in Redis)
  - Match path pattern: <10ms (regex)

Source 2 (Git Blame):
  - Run `git blame <file>`: <500ms (subprocess)
  - Parse output: <50ms

Source 3 (Directory Pattern):
  - Lookup directory → owner map: <10ms (hash table)

Source 4 (Fallback):
  - Read task creator from DB: <20ms

Total Latency: <630ms (all sources checked)
Optimization: Run sources in parallel → <500ms
```

**Failure Handling:**
- **CODEOWNERS missing:** Skip to git blame
- **Git blame fails (new file):** Skip to directory pattern
- **Directory pattern not found:** Use fallback (task creator)
- **All sources fail:** **ALWAYS SUCCEEDS** with task creator as owner

---

### Implementation Spec: suggest_ownership()

```python
async def suggest_ownership(
    file_path: str,
    task: Task,
    repo: Repository
) -> OwnershipSuggestion:
    """
    Suggest file owner from 4 sources (deterministic, no LLM).

    Requirements:
      - Latency: <2s (p95)
      - Accuracy: >90%
      - Always succeeds (fallback to task creator)

    Returns:
      OwnershipSuggestion with owner, confidence, reason
    """

    suggestions = []

    # Run all 4 sources in parallel (optimization)
    results = await asyncio.gather(
        check_codeowners(file_path, repo),
        get_git_blame_owner(file_path, repo),
        check_directory_pattern(file_path),
        get_task_creator(task),
        return_exceptions=True,  # Don't fail if one source fails
    )

    codeowners_owner, git_blame_owner, directory_owner, task_creator = results

    # SOURCE 1: CODEOWNERS (highest confidence)
    if codeowners_owner and not isinstance(codeowners_owner, Exception):
        suggestions.append(OwnershipSuggestion(
            owner=codeowners_owner,
            confidence=1.0,
            reason="Declared in CODEOWNERS file"
        ))

    # SOURCE 2: Git Blame (high confidence)
    if git_blame_owner and not isinstance(git_blame_owner, Exception):
        suggestions.append(OwnershipSuggestion(
            owner=git_blame_owner,
            confidence=0.8,
            reason="Most recent committer (git blame)"
        ))

    # SOURCE 3: Directory Pattern (medium confidence)
    if directory_owner and not isinstance(directory_owner, Exception):
        suggestions.append(OwnershipSuggestion(
            owner=directory_owner,
            confidence=0.6,
            reason="Directory ownership pattern"
        ))

    # SOURCE 4: Task Creator (fallback, low confidence)
    if task_creator and not isinstance(task_creator, Exception):
        suggestions.append(OwnershipSuggestion(
            owner=task_creator,
            confidence=0.3,
            reason="Task creator (fallback)"
        ))

    # ALWAYS return highest confidence suggestion
    # (cannot fail, at minimum returns task creator)
    best_suggestion = max(suggestions, key=lambda s: s.confidence)

    return best_suggestion


async def check_codeowners(file_path: str, repo: Repository) -> str | None:
    """
    Check CODEOWNERS file for declared owner.

    Latency: <50ms (cached)
    """
    codeowners_content = await redis.get(f"codeowners:{repo.id}")

    if not codeowners_content:
        # Cache miss, load from file
        codeowners_file = repo.read_file(".github/CODEOWNERS")
        if codeowners_file:
            await redis.set(f"codeowners:{repo.id}", codeowners_file, ex=3600)  # 1h cache
            codeowners_content = codeowners_file

    if not codeowners_content:
        return None

    # Parse CODEOWNERS (format: pattern @owner)
    for line in codeowners_content.split("\n"):
        if line.startswith("#") or not line.strip():
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        pattern, owner = parts[0], parts[1]

        # Match pattern against file_path
        if fnmatch.fnmatch(file_path, pattern):
            return owner

    return None


async def get_git_blame_owner(file_path: str, repo: Repository) -> str | None:
    """
    Get most recent committer from git blame.

    Latency: <500ms (subprocess)
    """
    try:
        result = await asyncio.subprocess.run(
            ["git", "blame", "--line-porcelain", file_path],
            cwd=repo.path,
            capture_output=True,
            timeout=1.0,  # 1s timeout
        )

        if result.returncode != 0:
            return None

        # Parse git blame output (format: author <email>)
        authors = {}
        for line in result.stdout.decode().split("\n"):
            if line.startswith("author "):
                author = line.split("author ")[1].strip()
                authors[author] = authors.get(author, 0) + 1

        # Return most frequent author
        if authors:
            return max(authors, key=authors.get)

    except asyncio.TimeoutError:
        logger.warning(f"Git blame timeout for {file_path}")
        return None


def check_directory_pattern(file_path: str) -> str | None:
    """
    Match directory to ownership pattern.

    Latency: <10ms (hash table lookup)
    """
    directory_patterns = {
        "backend/app/services/": "@backend-lead",
        "backend/app/api/": "@backend-lead",
        "frontend/src/": "@frontend-lead",
        "docs/": "@tech-writer",
        "tests/": "@qa-lead",
    }

    for pattern, owner in directory_patterns.items():
        if file_path.startswith(pattern):
            return owner

    return None


async def get_task_creator(task: Task) -> str:
    """
    Get task creator as fallback owner.

    Latency: <20ms (DB query, likely cached)
    """
    return f"@{task.creator.username}"
```

**Performance Requirements:**
- **CODEOWNERS Lookup P95:** <50ms (Redis cache)
- **Git Blame P95:** <500ms (subprocess, timeout at 1s)
- **Directory Pattern P95:** <10ms (hash table)
- **Task Creator P95:** <20ms (DB query)
- **Total End-to-End P95:** <580ms (parallel execution)

---

## 🔧 AUTO-GENERATION COMPONENT 3: CONTEXT ATTACHMENT (ADRs)

### Current State (Manual)

**Developer Process:**
1. Creates PR with code changes
2. Governance rejects: "No linked ADRs found"
3. Developer manually searches `docs/ADRs/` for relevant ADRs
4. Developer adds to PR description: `Related: ADR-007, ADR-015`
5. **Time:** 8 minutes (search, read ADRs, link)
6. **Failure Rate:** 50% incomplete (hard to find relevant ADRs)

---

### Target State (Auto-Generated)

**Auto-Generation Process:**
1. PR created → Governance calls `attach_context(pr)`
2. Algorithm extracts changed modules from diff
3. Searches ADRs mentioning those modules (full-text search)
4. Pre-populates PR description with: `Related ADRs: ADR-007, ADR-015`
5. Developer validates (1 min), removes irrelevant ADRs
6. **Total Time:** 1 min 5s (8min → 1min 5s = 6min 55s saved)

**Requirements:**

| Requirement | Spec | Acceptance Criteria |
|-------------|------|---------------------|
| **Latency** | <5s (p95) | ADR search completes within 5 seconds |
| **Relevance** | >70% | Developer keeps at least 70% of suggestions |
| **Fallback** | <10s | If search fails, use directory-based heuristic |

**Latency Budget:**
```
Step 1 (Extract Modules):
  - Parse PR diff: <200ms (regex on file paths)
  - Example: backend/app/services/auth.py → module "auth"

Step 2 (Search ADRs):
  - Full-text search in docs/ADRs/: <2s (Elasticsearch or PostgreSQL FTS)
  - Example: Search "auth" → matches ADR-007, ADR-015

Step 3 (Rank Relevance):
  - Score ADRs by: keyword frequency, date, module match
  - Latency: <500ms

Step 4 (Generate Links):
  - Format markdown links: <10ms

Total Latency: <2.71s (p50), <5s (p95)
```

**Failure Handling:**
- **Search timeout (>5s):** Use directory heuristic (auth/ → ADR-007)
- **Search returns 0 results:** Warn developer: "No ADRs found. Consider creating one?"
- **Search returns >10 results:** Show top 5 by relevance, link to full list

---

### Implementation Spec: attach_context()

```python
async def attach_context(pr: PullRequest) -> PRContextAttachment:
    """
    Auto-attach relevant ADRs and specs to PR description.

    Requirements:
      - Latency: <5s (p95)
      - Relevance: >70% (developer keeps suggestions)
      - Fallback: Directory heuristic if search fails

    Returns:
      PRContextAttachment with ADRs, specs, confidence
    """

    # STEP 1: Extract modules from PR diff
    changed_modules = extract_modules_from_diff(pr.diff)
    # Example: ["auth", "user_management", "api"]

    # STEP 2: Search ADRs (full-text search)
    try:
        relevant_adrs = await search_adrs(
            modules=changed_modules,
            timeout=5.0,  # 5s timeout
        )

        if len(relevant_adrs) > 0:
            return PRContextAttachment(
                adrs=relevant_adrs[:5],  # Top 5
                specs=[],  # TODO: Spec search not yet implemented
                confidence=0.8,
                search_method="full_text",
            )

    except SearchTimeout:
        logger.warning("ADR search timeout, falling back to directory heuristic")
        # Fall through to directory heuristic

    # STEP 3: Fallback - Directory Heuristic
    directory_adrs = map_directory_to_adrs(changed_modules)

    return PRContextAttachment(
        adrs=directory_adrs,
        specs=[],
        confidence=0.5,  # Lower confidence for heuristic
        search_method="directory_heuristic",
    )


def extract_modules_from_diff(diff: str) -> List[str]:
    """
    Extract module names from PR diff.

    Latency: <200ms
    """
    modules = set()

    # Parse file paths from diff
    for line in diff.split("\n"):
        if line.startswith("+++") or line.startswith("---"):
            file_path = line.split()[1]

            # Extract module from path
            # Example: backend/app/services/auth_service.py → "auth"
            if "services/" in file_path:
                module = file_path.split("services/")[1].split("_")[0]
                modules.add(module)

            elif "api/routes/" in file_path:
                module = file_path.split("routes/")[1].split(".")[0]
                modules.add(module)

    return list(modules)


async def search_adrs(modules: List[str], timeout: float) -> List[ADR]:
    """
    Search ADRs mentioning any of the modules.

    Latency: <2s (p50), <5s (p95)
    Uses: PostgreSQL Full-Text Search or Elasticsearch
    """
    try:
        # Build full-text search query
        query = " OR ".join(modules)

        # Search ADRs (PostgreSQL FTS example)
        results = await db.execute(
            """
            SELECT id, title, file_path, ts_rank(content_vector, query) AS rank
            FROM adrs, to_tsquery(:query) query
            WHERE content_vector @@ query
            ORDER BY rank DESC
            LIMIT 10
            """,
            {"query": query},
            timeout=timeout,
        )

        adrs = []
        for row in results:
            adrs.append(ADR(
                id=row["id"],
                title=row["title"],
                file_path=row["file_path"],
                relevance_score=row["rank"],
            ))

        return adrs

    except asyncio.TimeoutError:
        raise SearchTimeout("ADR search exceeded timeout")


def map_directory_to_adrs(modules: List[str]) -> List[ADR]:
    """
    Fallback: Map directory to known ADRs.

    Latency: <50ms (hash table lookup)
    """
    directory_adr_map = {
        "auth": ["ADR-007"],
        "payment": ["ADR-012"],
        "user_management": ["ADR-003", "ADR-015"],
    }

    adrs = []
    for module in modules:
        if module in directory_adr_map:
            for adr_id in directory_adr_map[module]:
                adrs.append(ADR(
                    id=adr_id,
                    title=f"Architecture Decision: {module}",
                    file_path=f"docs/ADRs/{adr_id}.md",
                    relevance_score=0.5,  # Lower confidence
                ))

    return adrs
```

**Performance Requirements:**
- **Module Extraction P95:** <200ms (regex parsing)
- **ADR Search P95:** <5s (PostgreSQL FTS or Elasticsearch)
- **Directory Heuristic P95:** <50ms (hash table)
- **Total End-to-End P95:** <5.25s (search path) or <0.25s (heuristic path)

---

## 🔧 AUTO-GENERATION COMPONENT 4: AI CODE ATTESTATION

### Current State (Manual)

**Developer Process:**
1. Uses AI to generate code (Claude, Copilot, GPT-4)
2. Governance detects AI-generated lines (>50% of PR)
3. Governance rejects: "AI code requires attestation"
4. Developer fills form manually:
   - AI provider: Claude
   - Model: claude-sonnet-4-5
   - Review time: 15 minutes
   - Modifications: Refactored error handling
   - Understanding: ✓ I understand this code
5. **Time:** 7 minutes (form filling, context recall)
6. **Failure Rate:** 20% skip (feels like busywork)

---

### Target State (Auto-Generated)

**Auto-Generation Process:**
1. AI code detected → Governance calls `pre_fill_attestation(pr, ai_session)`
2. Pre-fill attestation form (80% complete):
   - AI provider: Claude (from session metadata)
   - Model: claude-sonnet-4-5-20250929
   - Prompt hash: abc123xyz
   - Generated lines: 450
   - Session timestamp: 2026-01-27T10:30:00Z
3. Developer confirms (1 min):
   - Review time: 20 minutes (self-reported)
   - Modifications: Refactored error handling (text input)
   - Understanding: ✓ I understand this code (checkbox)
4. **Total Time:** 1 min 3s (7min → 1min 3s = 5min 57s saved)

**Requirements:**

| Requirement | Spec | Acceptance Criteria |
|-------------|------|---------------------|
| **Latency** | <3s (p95) | Pre-filled form ready within 3 seconds |
| **Accuracy** | >95% | Auto-filled fields are correct |
| **Fallback** | Manual form | If session data missing, show empty form |

**Latency Budget:**
```
Step 1 (Detect AI Lines):
  - Parse PR diff: <200ms
  - Count AI-generated lines (heuristic or metadata): <100ms

Step 2 (Fetch AI Session):
  - Query AI session log from DB: <500ms
  - Example: SELECT * FROM ai_sessions WHERE pr_id = 123

Step 3 (Pre-fill Form):
  - Extract: provider, model, prompt_hash, timestamp
  - Generate form HTML: <50ms

Total Latency: <850ms (p50), <3s (p95 with slow DB)
```

**Failure Handling:**
- **AI session not found:** Show empty form, developer fills manually
- **Session metadata incomplete:** Pre-fill what's available, mark missing fields with ⚠️
- **Multiple AI sessions:** Aggregate (e.g., "Claude: 300 lines, Copilot: 150 lines")

---

### Implementation Spec: pre_fill_attestation()

```python
async def pre_fill_attestation(
    pr: PullRequest,
    ai_session: AISession | None
) -> AttestationForm:
    """
    Pre-fill AI code attestation form (80% complete).

    Requirements:
      - Latency: <3s (p95)
      - Accuracy: >95% (auto-filled fields correct)
      - Fallback: Empty form if session not found

    Returns:
      AttestationForm with auto-filled and manual fields
    """

    # Detect AI-generated lines
    ai_lines_count = count_ai_lines(pr.diff)

    if ai_lines_count == 0:
        # No AI code detected, no attestation needed
        return None

    # Fetch AI session metadata (if available)
    if not ai_session:
        ai_session = await fetch_ai_session(pr.id)

    if ai_session:
        # AUTO-FILL (80% of form)
        return AttestationForm(
            pr_id=pr.id,
            # Auto-filled fields
            ai_provider=ai_session.provider,  # e.g., "Claude"
            model_version=ai_session.model,  # e.g., "claude-sonnet-4-5-20250929"
            prompt_hash=ai_session.prompt_hash,  # e.g., "abc123xyz"
            generated_lines=ai_lines_count,  # e.g., 450
            session_timestamp=ai_session.created_at,  # e.g., "2026-01-27T10:30:00Z"

            # Manual fields (developer confirms)
            review_time_minutes=None,  # ⚠️ REQUIRED
            modifications_made=None,  # ⚠️ REQUIRED
            understanding_confirmed=False,  # ⚠️ REQUIRED (checkbox)

            # Metadata
            auto_filled=True,
            requires_confirmation=True,
        )

    else:
        # FALLBACK: Empty form (developer fills manually)
        return AttestationForm(
            pr_id=pr.id,
            # All fields empty
            ai_provider=None,  # ⚠️ REQUIRED
            model_version=None,  # ⚠️ REQUIRED
            prompt_hash=None,
            generated_lines=ai_lines_count,  # Only line count known
            session_timestamp=None,

            # Manual fields
            review_time_minutes=None,  # ⚠️ REQUIRED
            modifications_made=None,  # ⚠️ REQUIRED
            understanding_confirmed=False,  # ⚠️ REQUIRED

            # Metadata
            auto_filled=False,
            requires_confirmation=True,
        )


def count_ai_lines(diff: str) -> int:
    """
    Count AI-generated lines in PR diff.

    Heuristic: Lines with AI metadata comment or >80% similarity to LLM output

    Latency: <200ms
    """
    ai_lines = 0

    for line in diff.split("\n"):
        # Check for AI metadata comment
        # Example: # Generated by Claude (claude-sonnet-4-5)
        if "Generated by" in line or "AI-generated" in line:
            ai_lines += 1

        # TODO: Advanced heuristic (similarity to known LLM patterns)
        # Not implemented in v1

    return ai_lines


async def fetch_ai_session(pr_id: int) -> AISession | None:
    """
    Fetch AI session metadata from database.

    Latency: <500ms (DB query)
    """
    session = await db.query(AISession).filter(
        AISession.pr_id == pr_id
    ).first()

    return session
```

**Performance Requirements:**
- **AI Line Detection P95:** <200ms (regex parsing)
- **AI Session Fetch P95:** <500ms (DB query, indexed)
- **Form Generation P95:** <50ms (HTML template)
- **Total End-to-End P95:** <750ms

---

## 📊 LATENCY SUMMARY - ALL COMPONENTS

| Component | Primary (LLM/API) | Fallback (Template) | P95 Target |
|-----------|-------------------|---------------------|------------|
| **Intent Statement** | 5-8s (Ollama) | <150ms (Template) | <10s |
| **Ownership Annotation** | <500ms (git blame) | <50ms (Directory) | <2s |
| **Context Attachment (ADRs)** | <2s (Full-text search) | <50ms (Heuristic) | <5s |
| **AI Code Attestation** | <500ms (DB query) | <50ms (Empty form) | <3s |
| **TOTAL (Sequential)** | **8-11s** | **<300ms** | **<20s** |
| **TOTAL (Parallel)** | **8-11s** | **<300ms** | **<10s** |

**Optimization:** Run all 4 components in parallel (not sequential) → **<10s total latency**

---

## 🎯 DEVELOPER EXPERIENCE TARGET

### Scenario 1: All Auto-Generation Succeeds (80% of cases)

**Timeline:**
1. **t=0s:** Developer creates PR
2. **t=8s:** All 4 components ready (parallel execution)
3. **t=10s:** Developer reviews auto-generated artifacts (2 min)
4. **t=130s:** Developer confirms, PR passes governance

**Total Time:** **2 min 10s** (vs 30 min manual = **27 min 50s saved**)

**Developer Experience:** ✅ "Governance is fast, not annoying"

---

### Scenario 2: LLM Fails, Template Fallback (15% of cases)

**Timeline:**
1. **t=0s:** Developer creates PR
2. **t=10s:** LLM timeout, template fallback kicks in
3. **t=10.3s:** All components ready (template path)
4. **t=12.3s:** Developer reviews, notices 🟡 "Generated from template"
5. **t=270s:** Developer edits template (5 min instead of 2 min)

**Total Time:** **4 min 30s** (vs 30 min manual = **25 min 30s saved**)

**Developer Experience:** ⚠️ "Slower than usual, but still faster than manual"

---

### Scenario 3: All Auto-Generation Fails (5% of cases)

**Timeline:**
1. **t=0s:** Developer creates PR
2. **t=10s:** All components timeout/fail
3. **t=10.5s:** Minimal placeholders shown
4. **t=15min:** Developer fills forms manually

**Total Time:** **15 min** (vs 30 min manual = **15 min saved**)

**Developer Experience:** 🟠 "Annoying, but not blocked. Can proceed within 2 min."

**Key:** Developer never blocked >2 min, can always proceed to write code

---

## 🔧 MONITORING & ALERTS

### Metric 1: Auto-Generation Success Rate

**Target:** >90% (healthy), <70% (critical)

**Measurement:**
- Success: LLM generates quality >0.7 content
- Partial: Template fallback used
- Failure: Minimal placeholder (developer fills manually)

**Alert Trigger:**
- If success rate <70% for 24 hours → Page on-call engineer
- If success rate <50% for 1 hour → Disable auto-generation, use templates only

---

### Metric 2: Template Fallback Rate

**Target:** <10% (healthy), >30% (critical)

**Measurement:**
- % of PRs using template fallback instead of LLM

**Alert Trigger:**
- If fallback rate >30% for 24 hours → Investigate Ollama performance
- If fallback rate >50% for 1 hour → Switch to template-only mode

---

### Metric 3: Developer Complaints

**Target:** <1/day (healthy), >3/day (critical)

**Measurement:**
- Count Slack messages in #sdlc-governance with keywords: "slow", "annoying", "broken"
- Count exception requests: "Can I skip auto-generation?"

**Alert Trigger:**
- If complaints >3/day for 3 days → CEO dashboard alert, investigate friction

---

### Metric 4: Time to Compliance (per PR)

**Baseline:** 30 minutes (manual)
**Target:** <5 minutes (auto-generation)

**Measurement:**
- Track: Time from "PR created" to "governance passed"

**Alert Trigger:**
- If avg time >10 min for 24 hours → Investigate latency bottleneck

---

## ✅ CONCLUSION: <5 MIN PER PR GUARANTEED

**Baseline (Manual Compliance):**
- Intent: 10 min
- Ownership: 5 min
- Context: 8 min
- Attestation: 7 min
- **Total:** **30 min**

**Target (Auto-Generated Compliance):**
- Intent: 2 min (LLM pre-fills 80%)
- Ownership: 30s (deterministic suggestion)
- Context: 1 min (ADR search)
- Attestation: 1 min (session data pre-filled)
- **Total:** **4 min 30s**

**Achievement:** **83% faster** (30 min → 4 min 30s = 25 min 30s saved)

**Critical Guarantee:** Developer NEVER blocked >2 min (fallback always succeeds)

---

**Document Status:** ✅ **COMPLETE - READY FOR CTO REVIEW**
**Next Document:** Governance-Signals-Design.md
