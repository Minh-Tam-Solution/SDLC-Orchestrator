# AI COUNCIL CHAT UI DESIGN SPECIFICATION
## Sprint 28 - Web Dashboard AI Assistant

**Document Type**: SDLC 6.1.0 Stage 02 (WHAT - Design/Architecture) - UI Component Design
**Version**: 1.0.0
**Date**: December 4, 2025
**Status**: ACTIVE - STAGE 02 (DESIGN)
**Authority**: Frontend Lead + UX Lead + CTO Approved
**Framework**: SDLC 6.1.0
**Sprint**: 28 - Web Dashboard AI Assistant

---

## 1. DESIGN OVERVIEW

### 1.1 Purpose

Design a conversational AI interface that integrates with the Compliance Dashboard, providing:
- Real-time compliance recommendations
- 3-stage AI Council deliberation visualization
- Tiered compliance status (Lite/Standard/Enterprise)
- Gate progress visualization (G0.1 → G5)

### 1.2 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-28.1 | As a PM, I want to ask compliance questions in natural language | P0 |
| US-28.2 | As a Dev, I want to see how AI Council reached its recommendation | P1 |
| US-28.3 | As a PM, I want to see my current gate progress at a glance | P0 |
| US-28.4 | As a QA, I want to apply AI recommendations with one click | P1 |

### 1.3 Design Principles

1. **Progressive Disclosure**: Show summary first, expand for details
2. **Context Awareness**: Recommendations based on current project/gate
3. **Visual Hierarchy**: Clear differentiation between stages
4. **Performance**: <3s AI response, <100ms UI interactions
5. **Accessibility**: WCAG 2.1 AA compliance

---

## 2. COMPONENT ARCHITECTURE

### 2.1 Component Hierarchy

```
CompliancePage (existing)
├── Header
│   ├── TierBadge              [NEW]
│   └── PageTitle
├── Content
│   ├── GateProgressBar        [NEW]
│   ├── ComplianceOverview     (existing)
│   ├── ViolationList          (existing)
│   └── AIAssistantButton      [NEW] → Opens Sheet
└── Sheet (Slide from right)
    └── AICouncilChat          [NEW]
        ├── ChatHeader
        │   ├── Title
        │   └── CouncilToggle  [NEW]
        ├── MessageList
        │   └── ChatMessage[]  [NEW]
        │       └── CouncilDeliberationView [NEW]
        │           ├── Stage1View [NEW]
        │           ├── Stage2View [NEW]
        │           └── Stage3View [NEW]
        └── InputArea
            ├── Textarea
            └── SendButton
```

### 2.2 File Structure

```
frontend/web/src/
├── components/
│   └── council/
│       ├── AICouncilChat.tsx       # Main chat container
│       ├── ChatMessage.tsx         # Individual message bubble
│       ├── CouncilToggle.tsx       # Council mode switch
│       ├── CouncilDeliberationView.tsx  # Expandable 3-stage view
│       ├── Stage1View.tsx          # AI responses display
│       ├── Stage2View.tsx          # Rankings display
│       ├── Stage3View.tsx          # Synthesis + action
│       ├── GateProgressBar.tsx     # Horizontal gate progress
│       ├── TierBadge.tsx           # Tier indicator badge
│       └── index.ts                # Exports
├── hooks/
│   └── useCouncil.ts               # API hooks
└── types/
    └── council.ts                  # TypeScript types [DONE]
```

---

## 3. VISUAL DESIGN

### 3.1 Color Palette (Tier-based)

```css
/* Lite Tier - Green (Startup/Small Team) */
--tier-lite-bg: hsl(142, 76%, 95%);        /* bg-green-100 */
--tier-lite-border: hsl(142, 76%, 73%);    /* border-green-300 */
--tier-lite-text: hsl(142, 76%, 25%);      /* text-green-800 */
--tier-lite-icon: "🌱";

/* Standard Tier - Blue (Growth/Medium Team) */
--tier-standard-bg: hsl(217, 91%, 95%);    /* bg-blue-100 */
--tier-standard-border: hsl(217, 91%, 73%); /* border-blue-300 */
--tier-standard-text: hsl(217, 91%, 25%);  /* text-blue-800 */
--tier-standard-icon: "⚡";

/* Enterprise Tier - Amber (Enterprise/Large Team) */
--tier-enterprise-bg: hsl(45, 93%, 95%);   /* bg-amber-100 */
--tier-enterprise-border: hsl(45, 93%, 73%); /* border-amber-300 */
--tier-enterprise-text: hsl(45, 93%, 25%); /* text-amber-800 */
--tier-enterprise-icon: "👑";
```

### 3.2 Gate Progress States

```css
/* Passed Gate */
--gate-passed-bg: hsl(142, 76%, 50%);      /* bg-green-500 */
--gate-passed-icon: "✓";

/* Current Gate (Active) */
--gate-current-bg: hsl(217, 91%, 60%);     /* bg-blue-500 */
--gate-current-icon: "●";
--gate-current-animation: pulse 2s infinite;

/* Pending Gate */
--gate-pending-bg: hsl(220, 13%, 91%);     /* bg-gray-300 */
--gate-pending-icon: "○";

/* Blocked Gate */
--gate-blocked-bg: hsl(0, 84%, 60%);       /* bg-red-500 */
--gate-blocked-icon: "⊘";
```

### 3.3 AI Provider Colors

```css
/* Claude (Anthropic) */
--provider-claude: hsl(24, 100%, 50%);     /* Orange */

/* GPT-4 (OpenAI) */
--provider-openai: hsl(160, 84%, 39%);     /* Teal */

/* Gemini (Google) */
--provider-gemini: hsl(217, 91%, 60%);     /* Blue */

/* Ollama (Local) */
--provider-ollama: hsl(280, 60%, 50%);     /* Purple */
```

---

## 4. WIREFRAMES

### 4.1 Compliance Page with AI Assistant Button

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back    Compliance Dashboard                    [Enterprise 👑]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Gate Progress                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [G0.1]──[G0.2]──[G1]──[●G2]──[G3]──[G4]──[G5]          │   │
│  │   ✓       ✓      ✓   current  ○     ○     ○            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │ Compliance Score    │  │ Violations by Severity          │  │
│  │                     │  │                                 │  │
│  │     ████████░░      │  │ CRITICAL  ████░░░░ 3            │  │
│  │        78%          │  │ HIGH      ██████░░ 5            │  │
│  │                     │  │ MEDIUM    ████████ 8            │  │
│  │ Standard Tier       │  │ LOW       ██░░░░░░ 2            │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Recent Violations                                        │   │
│  │ ├─ 🔴 Missing security review evidence      [Fix →]     │   │
│  │ ├─ 🔴 No load test results                  [Fix →]     │   │
│  │ ├─ 🔴 API documentation incomplete          [Fix →]     │   │
│  │ └─ 🟡 Code coverage below 80%               [Fix →]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                                            ┌────────────────┐  │
│                                            │ 🤖 AI Assistant │  │
│                                            └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 AI Council Chat Sheet (Expanded)

```
┌──────────────────────────────────────────┐
│  AI Compliance Assistant           [X]   │
│  ┌────────────────────────────────────┐  │
│  │ Council Mode      [═══════●═] ON   │  │
│  │ 3 AI providers for best answer     │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 🤖 System                          │  │
│  │ Welcome! I can help with:          │  │
│  │ • Fixing compliance violations     │  │
│  │ • Understanding gate requirements  │  │
│  │ • Generating evidence templates    │  │
│  └────────────────────────────────────┘  │
│                                          │
│            ┌──────────────────────────┐  │
│            │ How do I fix the         │  │
│            │ security review issue?   │  │
│            │                     You  │  │
│            └──────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 🤖 Assistant              2.3s     │  │
│  │                                    │  │
│  │ To fix the security review issue,  │  │
│  │ you need to:                       │  │
│  │                                    │  │
│  │ 1. Schedule a security review with │  │
│  │    your security team              │  │
│  │ 2. Complete the review checklist   │  │
│  │ 3. Upload the signed-off document  │  │
│  │                                    │  │
│  │ ▼ Council Deliberation (3 stages)  │  │
│  │ ┌──────────────────────────────┐   │  │
│  │ │ ▼ Stage 1: AI Responses      │   │  │
│  │ │   Claude:  ████████░░ 85%    │   │  │
│  │ │   GPT-4o:  ███████░░░ 78%    │   │  │
│  │ │   Gemini:  ██████░░░░ 72%    │   │  │
│  │ ├──────────────────────────────┤   │  │
│  │ │ ▼ Stage 2: Peer Rankings     │   │  │
│  │ │   #1 Claude (consensus)      │   │  │
│  │ │   #2 GPT-4o                  │   │  │
│  │ │   #3 Gemini                  │   │  │
│  │ ├──────────────────────────────┤   │  │
│  │ │ ▼ Stage 3: Synthesis         │   │  │
│  │ │   Confidence: 92%            │   │  │
│  │ │   Reasoning: Combined best   │   │  │
│  │ │   insights from all 3...     │   │  │
│  │ │                              │   │  │
│  │ │   [Apply Recommendation]     │   │  │
│  │ └──────────────────────────────┘   │  │
│  └────────────────────────────────────┘  │
│                                          │
├──────────────────────────────────────────┤
│  ┌────────────────────────────────────┐  │
│  │ Ask about compliance...            │  │
│  │                                    │  │
│  └────────────────────────────────────┘  │
│                              [Send ➤]   │
└──────────────────────────────────────────┘
```

### 4.3 Stage 1: AI Responses (Expanded)

```
┌──────────────────────────────────────┐
│ ▼ Stage 1: AI Responses    1.2s     │
├──────────────────────────────────────┤
│                                      │
│ ┌────────────────────────────────┐   │
│ │ 🟠 Claude (Anthropic)          │   │
│ │ Model: claude-3-5-sonnet       │   │
│ │ Duration: 450ms                │   │
│ │ Confidence: 85%                │   │
│ │ ─────────────────────────────  │   │
│ │ "To resolve the security       │   │
│ │ review violation, I recommend  │   │
│ │ following these steps:         │   │
│ │                                │   │
│ │ 1. Identify the security lead  │   │
│ │ 2. Schedule a 2-hour review    │   │
│ │ 3. Prepare documentation..."   │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ 🟢 GPT-4o (OpenAI)             │   │
│ │ Model: gpt-4o                  │   │
│ │ Duration: 380ms                │   │
│ │ Confidence: 78%                │   │
│ │ ─────────────────────────────  │   │
│ │ "The security review evidence  │   │
│ │ can be obtained by..."         │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ 🔵 Gemini (Google)             │   │
│ │ Model: gemini-1.5-pro          │   │
│ │ Duration: 420ms                │   │
│ │ Confidence: 72%                │   │
│ │ ─────────────────────────────  │   │
│ │ "Based on your project's       │   │
│ │ current gate (G2), you need..."│   │
│ └────────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
```

### 4.4 Stage 2: Rankings (Expanded)

```
┌──────────────────────────────────────┐
│ ▼ Stage 2: Peer Rankings    0.8s    │
├──────────────────────────────────────┤
│                                      │
│ Rankings by each AI:                 │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ Claude ranked:                 │   │
│ │   1st: Claude (self)           │   │
│ │   2nd: GPT-4o                  │   │
│ │   3rd: Gemini                  │   │
│ │ Reason: "Most actionable..."   │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ GPT-4o ranked:                 │   │
│ │   1st: Claude                  │   │
│ │   2nd: GPT-4o (self)           │   │
│ │   3rd: Gemini                  │   │
│ │ Reason: "More comprehensive..."│   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ Gemini ranked:                 │   │
│ │   1st: Claude                  │   │
│ │   2nd: Gemini (self)           │   │
│ │   3rd: GPT-4o                  │   │
│ │ Reason: "Better structure..."  │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ 🏆 Consensus Winner: Claude    │   │
│ │    3/3 AIs ranked #1           │   │
│ └────────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
```

### 4.5 Stage 3: Synthesis (Expanded)

```
┌──────────────────────────────────────┐
│ ▼ Stage 3: Final Synthesis   0.3s   │
├──────────────────────────────────────┤
│                                      │
│ ┌────────────────────────────────┐   │
│ │ Confidence Score               │   │
│ │ ████████████████████░░░░ 92%   │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ Reasoning                      │   │
│ │ ─────────────────────────────  │   │
│ │ The recommendation combines    │   │
│ │ Claude's actionable steps with │   │
│ │ GPT-4o's compliance context    │   │
│ │ and Gemini's gate-specific     │   │
│ │ requirements.                  │   │
│ │                                │   │
│ │ All 3 AIs agreed on the core   │   │
│ │ approach: schedule review,     │   │
│ │ complete checklist, upload     │   │
│ │ signed evidence.               │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ Suggested Action               │   │
│ │ ─────────────────────────────  │   │
│ │ Create a new evidence item     │   │
│ │ of type "Security Review" and  │   │
│ │ attach the signed document.    │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │     [Apply Recommendation]       │ │
│ │     Creates evidence template    │ │
│ └──────────────────────────────────┘ │
│                                      │
└──────────────────────────────────────┘
```

### 4.6 Gate Progress Bar

```
┌─────────────────────────────────────────────────────────────┐
│                      Gate Progress                           │
│                                                              │
│  ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐          │
│  │ G0.1  │────│ G0.2  │────│  G1   │────│  G2   │          │
│  │  ✓    │    │  ✓    │    │  ✓    │    │  ●    │          │
│  │Problem│    │Solution│    │Market │    │Design │          │
│  └───────┘    └───────┘    └───────┘    └───────┘          │
│     │            │            │            │                 │
│  ┌──┴────┐    ┌──┴────┐    ┌──┴────┐    ┌──┴────┐          │
│  │ G3    │────│ G4    │────│ G5    │                        │
│  │ ○     │    │ ○     │    │ ○     │                        │
│  │ Ship  │    │Operate│    │ Learn │                        │
│  └───────┘    └───────┘    └───────┘                        │
│                                                              │
│  Legend: ✓ Passed   ● Current   ○ Pending   ⊘ Blocked      │
└─────────────────────────────────────────────────────────────┘
```

### 4.7 Tier Badge Variants

```
┌─────────────────────────────────────────────────────────────┐
│                      Tier Badges                             │
│                                                              │
│  Size: Small (sm)                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │ 🌱 Lite     │  │ ⚡ Standard │  │ 👑 Enterprise │         │
│  └─────────────┘  └─────────────┘  └──────────────┘         │
│                                                              │
│  Size: Medium (md) - Default                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐   │
│  │   🌱 Lite     │  │  ⚡ Standard  │  │ 👑 Enterprise  │   │
│  │   70% coverage│  │  80% coverage │  │  85% coverage  │   │
│  └───────────────┘  └───────────────┘  └────────────────┘   │
│                                                              │
│  Size: Large (lg)                                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  🌱 Lite Tier                                        │    │
│  │  70% compliance coverage                             │    │
│  │  • Basic gates • Manual evidence • Single LLM       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. INTERACTION PATTERNS

### 5.1 Chat Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Interaction Flow                     │
│                                                              │
│  1. User clicks "AI Assistant" button                        │
│     └─→ Sheet slides in from right (300ms ease-out)         │
│                                                              │
│  2. User types question and presses Enter/Send              │
│     └─→ Message appears in chat (user bubble, right-aligned)│
│     └─→ Loading indicator shows ("AI is thinking...")       │
│                                                              │
│  3. AI responds                                              │
│     └─→ Council Mode OFF: Single response (1-2s)            │
│     └─→ Council Mode ON: 3-stage deliberation (2-5s)        │
│         └─→ Stage 1: 3 cards appear progressively           │
│         └─→ Stage 2: Rankings animate in                    │
│         └─→ Stage 3: Synthesis with confidence bar          │
│                                                              │
│  4. User clicks "Apply Recommendation"                       │
│     └─→ Action executed (create evidence, fix violation)    │
│     └─→ Toast notification: "Recommendation applied"        │
│     └─→ Compliance page refreshes affected data             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Council Mode Toggle

```
┌─────────────────────────────────────────────────────────────┐
│                    Council Toggle States                     │
│                                                              │
│  OFF State:                                                  │
│  ┌────────────────────────────────────────────┐             │
│  │ Council Mode      [●═══════════] OFF       │             │
│  │ Single AI for faster responses              │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  ON State:                                                   │
│  ┌────────────────────────────────────────────┐             │
│  │ Council Mode      [═══════════●] ON        │             │
│  │ 3 AI providers for best answer             │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  Transition: 200ms ease-in-out with color change            │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Collapsible Sections

```
┌─────────────────────────────────────────────────────────────┐
│                    Collapsible Behavior                      │
│                                                              │
│  Collapsed (default for Stage 1 & 2):                       │
│  ┌────────────────────────────────────────────┐             │
│  │ ▶ Stage 1: AI Responses        3 providers │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  Expanded (click to toggle):                                 │
│  ┌────────────────────────────────────────────┐             │
│  │ ▼ Stage 1: AI Responses        3 providers │             │
│  ├────────────────────────────────────────────┤             │
│  │ [Content reveals with 200ms slide-down]    │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  Stage 3 is expanded by default (final answer)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. RESPONSIVE DESIGN

### 6.1 Breakpoints

| Breakpoint | Width | Sheet Width | Behavior |
|------------|-------|-------------|----------|
| Mobile | <640px | 100% | Full screen |
| Tablet | 640-1024px | 400px | Slide from right |
| Desktop | 1024-1440px | 450px | Slide from right |
| Wide | >1440px | 500px | Slide from right |

### 6.2 Mobile Adaptations

```
Mobile View (< 640px):
┌────────────────────────┐
│ AI Assistant      [X]  │
├────────────────────────┤
│ Council Mode [══●] ON  │
├────────────────────────┤
│                        │
│ [Chat messages...]     │
│                        │
├────────────────────────┤
│ ┌────────────────────┐ │
│ │ Type message...    │ │
│ └────────────────────┘ │
│              [Send ➤]  │
└────────────────────────┘

- Full screen takeover
- Sticky input at bottom
- Simplified stage views
```

---

## 7. ACCESSIBILITY (WCAG 2.1 AA)

### 7.1 Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Navigate between interactive elements |
| `Enter` | Activate button, send message |
| `Escape` | Close sheet |
| `Space` | Toggle council mode, expand/collapse sections |
| `Arrow Up/Down` | Navigate chat history |

### 7.2 Screen Reader Support

```tsx
// ARIA labels for key elements
<Sheet aria-label="AI Compliance Assistant">
  <Switch
    aria-label="Council Mode toggle"
    aria-describedby="council-mode-description"
  />
  <div role="log" aria-live="polite" aria-label="Chat messages">
    {messages.map(msg => (
      <article aria-label={`Message from ${msg.role}`}>
        {msg.content}
      </article>
    ))}
  </div>
</Sheet>
```

### 7.3 Color Contrast

All text meets WCAG 2.1 AA contrast ratio (4.5:1 for normal text, 3:1 for large text):

| Element | Foreground | Background | Ratio |
|---------|------------|------------|-------|
| Lite badge text | green-800 | green-100 | 7.2:1 ✓ |
| Standard badge text | blue-800 | blue-100 | 6.8:1 ✓ |
| Enterprise badge text | amber-800 | amber-100 | 6.5:1 ✓ |
| Chat text | gray-900 | white | 21:1 ✓ |

---

## 8. PERFORMANCE BUDGET

### 8.1 Component Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Sheet open animation | <300ms | CSS transition |
| Message render | <50ms | React.memo optimization |
| Stage expand | <200ms | CSS transition |
| Total bundle (council/) | <30KB | Tree-shaking |

### 8.2 API Latency

| Operation | Target | Notes |
|-----------|--------|-------|
| Single LLM response | <2s | Council OFF |
| Council deliberation | <5s | All 3 stages |
| Apply recommendation | <500ms | Backend action |

---

## 9. API INTEGRATION

### 9.1 Endpoints

```yaml
# Get recommendation
POST /api/v1/council/recommend
Request:
  project_id: string
  violation_id?: string
  question: string
  council_mode: boolean
Response:
  request_id: string
  recommendation: string
  confidence_score: number
  council_deliberation?: CouncilDeliberation
  total_duration_ms: number

# Get gate status
GET /api/v1/projects/{project_id}/gates/status
Response:
  current_gate: GateType
  gates: Record<GateType, GateProgressStatus>
  tier: ComplianceTier
  overall_progress: number

# Get evidence checklist
GET /api/v1/gates/{gate_id}/evidence/checklist
Response:
  items: EvidenceItem[]
  progress: number
```

### 9.2 React Query Hooks

```typescript
// frontend/web/src/hooks/useCouncil.ts
export function useCouncilRecommend() {
  return useMutation({
    mutationFn: (request: CouncilRecommendRequest) =>
      api.post('/council/recommend', request),
    onSuccess: (data) => {
      queryClient.invalidateQueries(['violations'])
    }
  })
}

export function useGateStatus(projectId: string) {
  return useQuery({
    queryKey: ['gateStatus', projectId],
    queryFn: () => api.get(`/projects/${projectId}/gates/status`),
    staleTime: 30_000 // 30 seconds
  })
}
```

---

## 10. IMPLEMENTATION PLAN

### 10.1 Day 1 Tasks

| # | Component | Priority | Est. Hours |
|---|-----------|----------|------------|
| 1.1 | TierBadge.tsx | P0 | 1h |
| 1.2 | CouncilToggle.tsx | P0 | 1h |
| 1.3 | GateProgressBar.tsx | P0 | 2h |
| 1.4 | Types (council.ts) | P0 | 1h ✅ DONE |

### 10.2 Day 2 Tasks

| # | Component | Priority | Est. Hours |
|---|-----------|----------|------------|
| 2.1 | Stage1View.tsx | P0 | 2h |
| 2.2 | Stage2View.tsx | P0 | 1.5h |
| 2.3 | Stage3View.tsx | P0 | 1.5h |
| 2.4 | ChatMessage.tsx | P0 | 1h |

### 10.3 Day 3 Tasks

| # | Component | Priority | Est. Hours |
|---|-----------|----------|------------|
| 3.1 | AICouncilChat.tsx | P0 | 3h |
| 3.2 | useCouncil.ts hooks | P0 | 2h |
| 3.3 | Integration with CompliancePage | P0 | 2h |

### 10.4 Day 4 Tasks

| # | Task | Priority | Est. Hours |
|---|------|----------|------------|
| 4.1 | Unit tests | P0 | 3h |
| 4.2 | E2E tests | P1 | 2h |
| 4.3 | Accessibility audit | P1 | 1h |

### 10.5 Day 5 Tasks

| # | Task | Priority | Est. Hours |
|---|------|----------|------------|
| 5.1 | Performance optimization | P1 | 2h |
| 5.2 | Documentation | P1 | 1h |
| 5.3 | CTO review | P0 | 2h |

---

## 11. SUCCESS CRITERIA

### 11.1 Functional Requirements

- [ ] User can open AI chat from Compliance page
- [ ] User can send questions and receive responses
- [ ] Council mode toggle works correctly
- [ ] 3-stage deliberation displays properly
- [ ] Apply recommendation creates action
- [ ] Gate progress displays current state
- [ ] Tier badge shows correct tier

### 11.2 Non-Functional Requirements

- [ ] Sheet animation <300ms
- [ ] AI response <5s (council mode)
- [ ] Bundle size <30KB
- [ ] WCAG 2.1 AA compliant
- [ ] Works on mobile (responsive)

---

## 12. APPENDIX

### 12.1 TypeScript Types Reference

See: [frontend/web/src/types/council.ts](../../../frontend/web/src/types/council.ts)

### 12.2 Related Documents

- [Frontend Design Specification](./FRONTEND-DESIGN-SPECIFICATION.md)
- [Interface Design Document](../04-Interface-Design/Interface-Design-Document.md)
- [ADR-007: AI Context Engine](../01-System-Architecture/Architecture-Decisions/ADR-007-AI-Context-Engine.md)
- [Sprint 28 Plan](../../03-Development-Implementation/02-Sprint-Plans/SPRINT-28-WEB-DASHBOARD-AI.md)

---

**Document Status**: ✅ APPROVED
**Next Step**: Begin implementation Day 1 (TierBadge, CouncilToggle, GateProgressBar)
**CTO Sign-off Required**: Before Day 5 release

---

*SDLC Orchestrator - AI Council Chat UI Design*
*Version 1.0.0 | December 4, 2025*
