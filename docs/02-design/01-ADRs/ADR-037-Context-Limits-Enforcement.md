# ADR-037: Context Limits Enforcement (<60 Lines)

**Status**: APPROVED
**Date**: January 23, 2026
**Sprint**: Sprint 103
**Deciders**: CTO, Backend Lead

---

## Context

AGENTS.md files are growing too large, leading to:
- Context window bloat (AI tools have token limits)
- "Context creep" where irrelevant information accumulates
- Slower agent startup times
- Reduced comprehension by AI assistants

SDLC Framework 5.2.0 mandates per-file context limits:
> "Each file's context in AGENTS.md MUST be ≤60 lines for optimal AI comprehension."

## Decision

Implement Context Limits Enforcement with the following architecture:

### 1. Per-File Context Parsing

Parse AGENTS.md to extract file-specific code blocks:

```python
# Supported header formats
- ### File: path/to/file.py
- ## path/to/file.py
- ### `path/to/file.ts`

# Each file header followed by code block(s)
# Count lines within code blocks
```

### 2. Validation Service

`ContextValidationService` validates per-file limits:

```python
class ContextValidationService:
    MAX_CONTEXT_LINES = 60

    def validate_content(self, content: str) -> ContextValidation:
        file_contexts = self._parse_file_contexts(content)
        violations = [ctx for ctx in file_contexts if ctx.line_count > 60]
        return ContextValidation(valid=len(violations) == 0, ...)
```

### 3. CLI Command

```bash
sdlcctl agents validate-context AGENTS.md
sdlcctl agents validate-context AGENTS.md --max-lines 80
sdlcctl agents validate-context AGENTS.md --format github --strict
```

### 4. GitHub Integration

Output formats for CI/CD:
- `cli`: Human-readable table
- `json`: Machine-readable for scripts
- `github`: GitHub Check Run annotations

## Consequences

**Positive:**
- Prevents context bloat
- Forces concise, focused file summaries
- Better AI tool comprehension
- Faster agent startup

**Negative:**
- May require refactoring existing AGENTS.md files
- Additional validation step in CI/CD

**Recommendations for Large Files:**
1. Focus on critical information only
2. Extract patterns to 'Conventions' section
3. Reference detailed docs instead of inline
4. Use PR comments for dynamic context (Sprint 81)

## References

- Sprint 103: Context <60 Lines + Framework Version Tracking
- SDLC Framework 5.2.0, 03-AI-GOVERNANCE
- ADR-029: AGENTS.md Integration Strategy
