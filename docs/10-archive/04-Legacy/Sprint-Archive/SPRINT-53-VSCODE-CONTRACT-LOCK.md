# SPRINT-53: VS Code Extension + Contract Lock
## EP-06: IR-Based Vietnamese SME Codegen | Developer Experience

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-53 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 5 days (Jan 6-10, 2026) |
| **Status** | PLANNED ⏳ |
| **Priority** | P0 Must Have |
| **Dependencies** | Sprint 52 complete |
| **Framework** | SDLC 6.1.0 Universal Framework |

---

## Sprint Goal

Integrate App Builder into VS Code Extension with Contract Lock for spec immutability.

---

## Sprint Objectives

| Day | Focus | Deliverables | Effort |
|-----|-------|--------------|--------|
| Day 1 | Extension Foundation | Sidebar, activation | 8h |
| Day 2 | App Builder Panel | Blueprint editor, preview | 8h |
| Day 3 | Streaming Integration | Real-time generation view | 8h |
| Day 4 | Contract Lock | Spec immutability, hash validation | 6h |
| Day 5 | Testing + Publish | E2E tests, marketplace prep | 6h |

---

## Feature 1: VS Code Extension - App Builder

**Extension Structure**:
```
vscode-extension/
├── src/
│   ├── extension.ts              # Entry point
│   ├── commands/
│   │   ├── generate.ts           # Generate command
│   │   ├── magic.ts              # Magic mode command
│   │   └── lock.ts               # Contract lock command
│   ├── panels/
│   │   ├── AppBuilderPanel.ts    # Main sidebar panel
│   │   └── GenerationPanel.ts    # Streaming view
│   ├── providers/
│   │   ├── BlueprintProvider.ts  # Tree view provider
│   │   └── PreviewProvider.ts    # Code preview provider
│   └── lib/
│       ├── api.ts                # Backend API client
│       └── sse.ts                # SSE client for streaming
├── package.json
└── README.md
```

**Commands**:

| Command | Keybinding | Description |
|---------|------------|-------------|
| `sdlc.generate` | `Cmd+Shift+G` | Generate from blueprint |
| `sdlc.magic` | `Cmd+Shift+M` | Magic mode (natural language) |
| `sdlc.lock` | `Cmd+Shift+L` | Lock current spec |
| `sdlc.preview` | `Cmd+Shift+P` | Preview generated code |
| `sdlc.resume` | `Cmd+Shift+R` | Resume failed generation |

---

## Feature 2: Contract Lock

**Purpose**: Prevent spec changes during active generation

**Implementation**:

| File | Change |
|------|--------|
| `backend/app/models/onboarding.py` | Add `spec_hash`, `locked_at`, `locked_by` |
| `backend/app/api/routes/onboarding.py` | Add `/onboarding/{id}/lock` endpoint |
| `backend/app/schemas/onboarding.py` | Add `SpecLock` schema |
| `vscode-extension/src/commands/lock.ts` | Lock command implementation |

**Lock API**:
```python
# POST /api/v1/onboarding/{id}/lock
{
    "locked": true,
    "spec_hash": "sha256:abc123...",
    "locked_at": "2026-01-08T10:00:00Z",
    "locked_by": "user-uuid"
}

# POST /api/v1/onboarding/{id}/unlock
{
    "locked": false,
    "unlock_reason": "Generation complete"
}
```

---

## Feature 3: Real-time Generation View

**VS Code Webview Features**:
- File tree updates in real-time
- Click to preview generated code
- Inline error display with suggestions
- One-click retry for failed files
- QR code button for mobile preview

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Extension activation time | <1s |
| Generation streaming lag | <200ms |
| Contract lock accuracy | 100% hash match |
| Marketplace rating target | 4.5+ stars |

---

## Files Summary

| Category | Files | Lines (Est.) |
|----------|-------|--------------|
| Extension Core | 5 | ~800 |
| Commands | 3 | ~400 |
| Panels | 2 | ~600 |
| Providers | 2 | ~300 |
| Backend (Lock) | 3 | ~250 |
| Tests | 4 | ~500 |
| **Total** | **19** | **~2,850** |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Last Updated** | December 27, 2025 |
| **Owner** | Frontend Lead |
| **Approved By** | CTO (Pending) |
