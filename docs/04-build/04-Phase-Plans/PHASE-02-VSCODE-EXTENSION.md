# PHASE-02: VS Code Extension
## AI-Assisted Development in IDE

**Version**: 1.0.0
**Date**: December 3, 2025
**Status**: PLANNED - Sprint 27
**Duration**: 5 days (Dec 16-20, 2025)
**Owner**: Frontend Lead + Extension Team
**Framework**: SDLC 5.1.3.1 Complete Lifecycle
**Prerequisite**: PHASE-01 Complete

---

## Executive Summary

PHASE-02 implements the **SDLC Orchestrator VS Code Extension** - bringing AI-assisted development directly into the developer's IDE. Developers can access project context, submit evidence, and get AI assistance without leaving VS Code.

**Key Deliverables**:
1. VS Code Extension MVP (sidebar integration)
2. AI Chat Panel (project-aware conversations)
3. Evidence Submit (quick upload from IDE)
4. Template Generator (stage-aware templates)

**Success Criteria**:
- Extension installs and connects in <2min
- AI chat responds in <3s (p95)
- Evidence upload <5s (10MB limit)
- 5+ template types available

---

## 1. Problem Statement

### Current State (Before PHASE-02)

**Pain Points**:
1. **Context Switching**: Developers leave IDE to access SDLC Orchestrator web dashboard
2. **Evidence Upload Friction**: Screenshot, open browser, navigate, upload - 2-5 min process
3. **No IDE AI Integration**: ChatGPT/Claude in browser, not integrated with project context
4. **Template Discovery**: Finding the right template requires navigating docs

**Evidence**:
- Developer survey: 73% want IDE integration
- Average context switch: 2-3 min (4-6x/day = 10-18 min lost/day)
- Evidence upload abandonment: 30% (too many steps)

### Target State (After PHASE-02)

- AI assistance in sidebar (no browser needed)
- One-click evidence upload (Cmd+Shift+E)
- Template generation in seconds
- Full project context in every interaction

---

## 2. Technical Architecture

### 2.1 Extension Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VS CODE EXTENSION                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Sidebar View    │  │ AI Chat Panel   │  │ Evidence Panel  │ │
│  │                 │  │                 │  │                 │ │
│  │ - Project list  │  │ - Chat history  │  │ - Quick upload  │ │
│  │ - Gate status   │  │ - Context aware │  │ - Screenshot    │ │
│  │ - Quick actions │  │ - Multi-turn    │  │ - File attach   │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┘           │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │    Extension Core     │                    │
│                    │                       │                    │
│                    │ - Auth (OAuth)        │                    │
│                    │ - API Client          │                    │
│                    │ - State Management    │                    │
│                    │ - Settings            │                    │
│                    └───────────────────────┘                    │
│                                │                                 │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   SDLC Orchestrator API │
                    │   (Backend Service)     │
                    └─────────────────────────┘
```

### 2.2 Authentication Flow

```yaml
OAuth Device Flow:
  1. User clicks "Sign In" in extension sidebar
  2. Extension requests device code from SDLC Orchestrator
  3. User opens browser link, authenticates
  4. Extension polls for access token
  5. Token stored in VS Code SecretStorage
  6. Auto-refresh on token expiry

Security:
  - Tokens stored in SecretStorage (encrypted)
  - Refresh tokens rotated on use
  - Session timeout: 24 hours
  - MFA supported (web-based)
```

### 2.3 Extension Components

```typescript
// Extension Structure
sdlc-orchestrator-vscode/
├── src/
│   ├── extension.ts           // Entry point
│   ├── auth/
│   │   ├── authProvider.ts    // OAuth device flow
│   │   └── tokenManager.ts    // Token storage
│   ├── views/
│   │   ├── sidebarProvider.ts // Sidebar webview
│   │   ├── chatPanel.ts       // AI chat panel
│   │   └── evidencePanel.ts   // Evidence upload
│   ├── api/
│   │   ├── client.ts          // HTTP client
│   │   └── endpoints.ts       // API definitions
│   ├── commands/
│   │   ├── submitEvidence.ts  // Cmd+Shift+E
│   │   ├── generateTemplate.ts// Cmd+Shift+T
│   │   └── askAI.ts           // Cmd+Shift+A
│   └── utils/
│       ├── context.ts         // Project context
│       └── notifications.ts   // Status bar
├── webview/                   // React webview UI
│   ├── sidebar/
│   ├── chat/
│   └── evidence/
├── package.json               // Extension manifest
└── tsconfig.json
```

---

## 3. Features Specification

### 3.1 Sidebar View

**Components**:
- Project selector (dropdown)
- Gate status cards (green/yellow/red)
- Quick actions (new evidence, AI chat, templates)
- Recent activity feed

**Wireframe**:
```
┌──────────────────────────┐
│ SDLC Orchestrator        │
├──────────────────────────┤
│ [Project: Bflow ▼]       │
├──────────────────────────┤
│ Gate Status              │
│ ┌──────────────────────┐ │
│ │ G0.1 ✅ Problem Def  │ │
│ │ G0.2 ✅ Solution     │ │
│ │ G1   🔄 Planning     │ │
│ │ G2   ⏳ Design       │ │
│ └──────────────────────┘ │
├──────────────────────────┤
│ Quick Actions            │
│ [📎 Submit Evidence]     │
│ [🤖 Ask AI]              │
│ [📄 Generate Template]   │
├──────────────────────────┤
│ Recent Activity          │
│ • Evidence uploaded (2m) │
│ • Gate G0.2 passed (1h)  │
│ • Task decomposed (3h)   │
└──────────────────────────┘
```

### 3.2 AI Chat Panel

**Features**:
- Project-aware context (current project, stage, gates)
- Multi-turn conversation
- Code snippet support
- Quick actions (decompose, template, explain)

**Chat Protocol**:
```json
{
  "type": "chat_message",
  "project_id": "uuid",
  "context": {
    "current_file": "src/services/gate.ts",
    "current_stage": "03-development",
    "open_gates": ["G1", "G2"]
  },
  "message": "How should I structure this gate evaluation?"
}
```

### 3.3 Evidence Upload

**Workflow**:
1. Select text/code in editor OR take screenshot
2. Press Cmd+Shift+E
3. Panel opens with pre-filled context
4. Select gate, add description
5. Click Upload (progress indicator)
6. Success notification with link

**Supported Types**:
- Code snippets (auto-detected language)
- Screenshots (clipboard paste)
- Files (drag & drop, max 10MB)
- URLs (auto-fetch metadata)

### 3.4 Template Generator

**Templates Available**:
- Stage 00: PRD, Problem Statement, HMW Questions
- Stage 01: Functional Spec, API Design, Data Model
- Stage 02: Architecture Doc, ADR, Security Review
- Stage 03: Sprint Plan, Task Breakdown, Code Review
- Stage 04: Test Plan, Bug Report, E2E Scenario

**Generation Flow**:
1. Cmd+Shift+T opens template picker
2. Select template type
3. AI generates content with project context
4. Opens in new editor tab
5. User edits and saves

---

## 4. Implementation Plan

### Day 1: Extension Scaffold (Dec 16)

**Tasks**:
1. Initialize VS Code extension project
2. Set up TypeScript, ESLint, Prettier
3. Create basic sidebar webview
4. Implement OAuth device flow

**Deliverables**:
- Extension runs in VS Code
- Sidebar visible
- Auth flow working (dev environment)

### Day 2: API Integration (Dec 17)

**Tasks**:
1. Implement API client (axios-based)
2. Create project listing endpoint integration
3. Display gate status in sidebar
4. Handle auth token refresh

**Deliverables**:
- Project list loads
- Gate status displays
- Token management working

### Day 3: AI Chat Panel (Dec 18)

**Tasks**:
1. Create chat panel webview
2. Implement chat API integration
3. Add context builder (project, file, stage)
4. Support multi-turn conversations

**Deliverables**:
- AI chat functional
- Project context included
- Response streaming

### Day 4: Evidence Upload (Dec 19)

**Tasks**:
1. Create evidence upload panel
2. Implement file/screenshot handling
3. Add progress indicator
4. Create evidence API integration

**Deliverables**:
- Evidence upload working
- Cmd+Shift+E shortcut
- Success/error notifications

### Day 5: Templates & Polish (Dec 20)

**Tasks**:
1. Implement template generator
2. Add 5+ template types
3. End-to-end testing
4. Package for marketplace (internal)

**Deliverables**:
- Template generation working
- All features tested
- VSIX package ready

---

## 5. Success Criteria

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Extension activation | <1s | VS Code telemetry |
| Sidebar load | <500ms | Performance.now() |
| AI chat response | <3s (p95) | API latency + render |
| Evidence upload (10MB) | <5s | Upload API latency |

### UX Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first value | <2min | User testing |
| Task success rate | >90% | Usability testing |
| NPS (internal beta) | >50 | Survey |
| Daily active users | 80%+ | Telemetry |

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Extension size | <5MB | Package size |
| Memory usage | <50MB | VS Code profiler |
| Error rate | <0.5% | Sentry |
| Crash-free rate | >99% | VS Code crash reports |

---

## 6. Risk Assessment

### Risk 1: OAuth Device Flow Issues

**Probability**: Medium (25%)
**Impact**: High (blocks all features)
**Mitigation**: Fallback to API key auth, detailed error messages
**Contingency**: Personal access token alternative

### Risk 2: Webview Performance

**Probability**: Low (15%)
**Impact**: Medium
**Mitigation**: Virtual scrolling, lazy loading, minimal bundle
**Contingency**: Native tree view instead of webview

### Risk 3: API Latency in IDE

**Probability**: Low (10%)
**Impact**: Medium
**Mitigation**: Caching, optimistic updates, skeleton loading
**Contingency**: Background sync with local state

---

## 7. Dependencies

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| VS Code API | 1.85+ | Extension development |
| React | 18.x | Webview UI |
| Axios | 1.x | HTTP client |

### Internal Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| PHASE-01 AI Council | Backend | Required |
| OAuth endpoints | Auth team | ✅ Complete |
| Evidence API | Sprint 18 | ✅ Complete |

---

## 8. Team Allocation

| Role | Person | Allocation | Focus |
|------|--------|------------|-------|
| Extension Lead | TBD | 100% | Architecture, core |
| Frontend Dev 1 | TBD | 100% | Sidebar, webview |
| Frontend Dev 2 | TBD | 100% | Chat panel, evidence |
| Backend Dev | TBD | 25% | API endpoints |
| Designer | TBD | 25% | UI/UX refinement |

---

## 9. Acceptance Criteria (Phase Gate)

### Phase Complete When:

1. ✅ Extension installable from VSIX
2. ✅ OAuth authentication working
3. ✅ Sidebar shows projects and gates
4. ✅ AI chat functional with context
5. ✅ Evidence upload <5s
6. ✅ 5+ template types available
7. ✅ Internal beta feedback >NPS 40

### Phase Blocked If:

- ❌ OAuth cannot complete (auth architecture issue)
- ❌ Webview crashes consistently (stability issue)
- ❌ AI chat latency >10s (backend bottleneck)

---

## 10. References

- [ADR-009: VS Code Extension Architecture](../../02-design/01-ADRs/ADR-009-VSCode-Extension.md) (to be created)
- [Product Roadmap v3.0.0](../../00-Project-Foundation/04-Roadmap/Product-Roadmap.md)
- [Sprint 27 Plan](../02-Sprint-Plans/SPRINT-27-VSCODE-EXTENSION.md)
- [VS Code Extension API](https://code.visualstudio.com/api)

---

**Document Status**: ✅ APPROVED - Ready for Sprint 27
**Last Updated**: December 3, 2025
**Owner**: Frontend Lead + CTO
