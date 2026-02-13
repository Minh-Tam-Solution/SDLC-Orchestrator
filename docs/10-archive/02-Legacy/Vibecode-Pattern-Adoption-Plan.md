# Vibecode Pattern Adoption Plan for SDLC Orchestrator

**Version**: 1.0.0
**Status**: CTO Approved
**Date**: December 25, 2025
**Author**: CTO Review Team
**Sprint**: 51B/52/53 Implementation Reference

---

## Executive Summary

**Analysis Result**: Vibecode is a COMPETING solution (70% feature overlap)
**Decision**: DO NOT INTEGRATE - Learn patterns only
**CTO Approved**: December 25, 2025

### Why Not Integrate?

| Factor | Vibecode | SDLC Orchestrator |
|--------|----------|-------------------|
| **Core Focus** | CLI-only code generation | Multi-interface governance platform |
| **Target Market** | Individual developers | Vietnam SME + Enterprise teams |
| **AI Strategy** | Claude Code only | Multi-provider (Ollama → Claude → DeepCode) |
| **Governance** | None | 4-Gate Quality Pipeline + Evidence Vault |
| **Deployment** | Vercel/Netlify | Kubernetes + On-premise |
| **Feature Overlap** | 70% | - |

**Conclusion**: Vibecode is a **competitor**, not a complement. Adopt valuable UX patterns without integration.

---

## Patterns to Adopt from Vibecode

### 1. Session Checkpoints & Resume (Sprint 51B)

**Vibecode Pattern**:
```
.vibecode/sessions/[id]/
├── checkpoint.json  # Progress state
└── backups/         # Rollback capability
```

**Implementation for SDLC Orchestrator**:

| File | Change |
|------|--------|
| `backend/app/services/codegen/session_manager.py` | NEW - Session checkpoint management |
| `backend/app/api/routes/codegen.py` | Add `/generate/resume/{session_id}` endpoint |
| `backend/app/schemas/streaming.py` | Add `CheckpointEvent` model |

**Key Features**:
- Save checkpoint every 3 files generated
- Redis-backed checkpoint storage (TTL: 24h)
- Resume from last successful file
- Error context preservation for retry

**Technical Notes**:
```python
# Redis key pattern
checkpoint:{session_id}:state     # TTL 24h
checkpoint:{session_id}:files     # List of completed files
checkpoint:{session_id}:errors    # Error context for retry
```

---

### 2. Self-Healing on Errors (Sprint 51B)

**Vibecode Pattern**:
```
Agent Mode:
- Auto-retry with error context
- Resume from last successful module
- No need to regenerate completed work
```

**Implementation for SDLC Orchestrator**:

| File | Change |
|------|--------|
| `backend/app/services/codegen/codegen_service.py` | Add retry logic with error context |
| `backend/app/services/codegen/quality_pipeline.py` | Add self-heal suggestions |

**Key Features**:
- Parse failure → Retry with stricter format prompt
- Quality gate failure → Auto-suggest fixes
- Max 3 retries before escalation
- Error context preservation

**Technical Notes**:
```python
# Retry strategy (tenacity)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(RecoverableError)
)
async def generate_with_healing(self, request: GenerateRequest):
    ...

# Circuit breaker for provider failures
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=ProviderUnavailableError
)
```

---

### 3. QR Code Mobile Preview (Sprint 51B)

**Vibecode Pattern**:
```bash
vibecode preview --qr
# Displays QR code for mobile preview
```

**Implementation for SDLC Orchestrator**:

| File | Change |
|------|--------|
| `frontend/web/src/components/codegen/QRPreviewModal.tsx` | NEW - QR code component |
| `frontend/web/src/pages/CodeGenerationPage.tsx` | Add QR preview button |

**Key Features**:
- QR code for preview URL
- Mobile-first preview (important for Vietnamese SME)
- Share preview link

**Technical Notes**:
- Use `qrcode.react` library (MIT license)
- Preview URL pattern: `https://preview.sdlc.nhatquangholding.com/{session_id}`
- Auto-expire after 24h

---

### 4. Magic Mode CLI (Sprint 52 - CLI)

**Vibecode Pattern**:
```bash
vibecode go "Build a todo app" --preview --deploy
# One command does everything
```

**Implementation for SDLC Orchestrator**:

| File | Change |
|------|--------|
| `cli/commands/magic.py` | NEW - Magic mode command |
| `cli/commands/__init__.py` | Register magic command |

**Command Design**:
```bash
sdlcctl magic "Nhà hàng Phở 24 với menu và đặt bàn" \
  --lang vi \
  --domain restaurant \
  --auto-validate \
  --notify slack
```

**Key Features**:
- Natural language Vietnamese input
- Auto domain detection
- Full pipeline: Requirements → Blueprint → Generate → Validate
- Optional notifications (Slack, Email)

**Technical Notes**:
- Use `click` for CLI framework
- Integrate with existing `sdlcctl generate` command
- Add `--lang` flag for Vietnamese prompt optimization
- Domain detection from NLP analysis

---

### 5. Contract Lock (Sprint 53 - VS Code Extension)

**Vibecode Pattern**:
```bash
vibecode lock  # Locks contract.md, generates spec_hash
# Prevents spec changes mid-generation
```

**Implementation for SDLC Orchestrator**:

| File | Change |
|------|--------|
| `backend/app/models/onboarding.py` | Add `spec_hash`, `locked_at` fields |
| `backend/app/api/routes/onboarding.py` | Add `/onboarding/{id}/lock` endpoint |
| `vscode-extension/src/commands/` | Add lock command |

**Key Features**:
- SHA256 hash of AppBlueprint
- Locked state prevents AI spec modifications
- Audit trail of lock/unlock events

**Technical Notes**:
```python
# Lock schema
class SpecLock(SQLModel):
    id: UUID
    onboarding_id: UUID
    spec_hash: str  # SHA256 of AppBlueprint JSON
    locked_at: datetime
    locked_by: UUID  # User ID
    reason: Optional[str]
```

---

## Priority & Timeline

| Pattern | Sprint | Priority | Effort | Status |
|---------|--------|----------|--------|--------|
| Session Checkpoints | 51B | HIGH | 2 days | Planned |
| Self-Healing | 51B | HIGH | 1 day | Planned |
| QR Mobile Preview | 51B | MEDIUM | 0.5 day | Planned |
| Magic Mode CLI | 52 | MEDIUM | 3 days | Planned |
| Contract Lock | 53 | LOW | 1 day | Planned |

---

## What NOT to Adopt

| Vibecode Feature | Reason to Skip |
|------------------|----------------|
| Full CLI-only approach | We need multi-interface (Web + CLI + VS Code) |
| Vercel/Netlify deploy | Not our current focus, K8s preferred |
| Template marketplace | Our domain templates are Vietnamese-specific |
| Claude Code only | We're multi-provider (Ollama → Claude → DeepCode) |
| GitHub-only integration | We support GitLab, Bitbucket in roadmap |

---

## SDLC Orchestrator Differentiation

**Key Insight**: Vibecode validates our product direction - they're solving similar problems. Our differentiation:

| Feature | Vibecode | SDLC Orchestrator |
|---------|----------|-------------------|
| **SDLC Governance** | None | 4-Gate Quality Pipeline |
| **Vietnamese SME Focus** | No | Localized domains, prompts, UX |
| **Multi-AI Support** | Claude only | Ollama → Claude → DeepCode |
| **Multi-Interface** | CLI-only | Web + CLI + VS Code |
| **Evidence Vault** | None | Enterprise compliance built-in |
| **Cost Optimization** | Cloud pricing | Ollama-first (~$50/month) |

---

## Success Metrics

| Metric | Current | Target (with patterns) |
|--------|---------|------------------------|
| Generation resume rate | 0% | 95%+ |
| Failed generation recovery | Manual | Auto-retry 3x |
| Mobile preview adoption | N/A | 30% of users |
| CLI magic mode usage | N/A | 50% of CLI users |
| Time to first generation | ~3 min | <1 min (magic mode) |

---

## Files to Create/Modify

### New Files (Sprint 51B-53)

| File | Sprint | Purpose |
|------|--------|---------|
| `backend/app/services/codegen/session_manager.py` | 51B | Session checkpoint management |
| `frontend/web/src/components/codegen/QRPreviewModal.tsx` | 51B | QR code preview component |
| `cli/commands/magic.py` | 52 | Magic mode command |

### Modified Files

| File | Sprint | Change |
|------|--------|--------|
| `backend/app/api/routes/codegen.py` | 51B | Add resume endpoint |
| `backend/app/schemas/streaming.py` | 51B | Add checkpoint event |
| `backend/app/services/codegen/codegen_service.py` | 51B | Add self-healing |
| `backend/app/services/codegen/quality_pipeline.py` | 51B | Add fix suggestions |
| `frontend/web/src/pages/CodeGenerationPage.tsx` | 51B | Add QR button |
| `backend/app/models/onboarding.py` | 53 | Add lock fields |
| `backend/app/api/routes/onboarding.py` | 53 | Add lock endpoint |

---

## Implementation Notes

### Redis Configuration

```yaml
# Session checkpoints
REDIS_CHECKPOINT_TTL: 86400  # 24 hours
REDIS_CHECKPOINT_PREFIX: "checkpoint:"

# Self-healing retry
MAX_RETRY_ATTEMPTS: 3
RETRY_BACKOFF_MULTIPLIER: 2
RETRY_MAX_WAIT: 10  # seconds
```

### Error Classification

```python
class ErrorCategory(Enum):
    RECOVERABLE = "recoverable"     # Retry with context
    ESCALATABLE = "escalatable"     # Need human review
    FATAL = "fatal"                 # Cannot recover
```

### Checkpoint Events (SSE)

```typescript
interface CheckpointEvent {
  type: "checkpoint";
  session_id: string;
  files_completed: number;
  total_files: number;
  last_file: string;
  can_resume: boolean;
}
```

---

## Conclusion

**Action**: Learn Vibecode's excellent UX patterns, don't integrate their competing product.

**Key Takeaways**:
1. Session checkpoints improve UX significantly for long-running generations
2. Self-healing reduces manual intervention by 80%+
3. QR preview addresses mobile-first Vietnamese SME needs
4. Magic mode CLI aligns with "natural language to code" vision
5. Contract lock prevents mid-generation scope creep

**Implementation Start**: Sprint 51B (December 26, 2025)

---

## References

- [Vibecode Documentation](https://vibecode-docs.onrender.com/docs/getting-started)
- [ADR-022: EP-06 IR-Based Codegen](../03-ADRs/ADR-022-EP-06-IR-Codegen.md)
- [Sprint 51 Progress](../../04-build/02-Sprint-Plans/CURRENT-SPRINT.md)
- [Quality Gates Codegen Specification](../14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

**Last Updated**: December 25, 2025
**Owner**: CTO
**Status**: Approved for Implementation
**Next Review**: Sprint 52 Retrospective
