# Sprint 28: Web Dashboard AI Assistant - Conversational Compliance

**Version**: 1.0.0
**Date**: December 2, 2025
**Status**: APPROVED - Awaiting Implementation
**Authority**: CTO + CPO (9.2/10 Rating)
**Foundation**: Expert Analysis (Policy Pack v0.9, Market & OSS Landscape)
**Framework**: SDLC 4.9.1 Complete Lifecycle
**Week**: 13 of 13 (Final Sprint)

---

## Sprint Overview

**Sprint Goal**: Integrate AI Council chat interface into Web Dashboard with 3-stage deliberation visualization and tiered compliance UI.

**Duration**: 5 days
**Team**: Frontend 100%, Backend 20%
**Priority**: P1 - High (AI Visualization)

---

## Context: Why Web Dashboard AI?

```yaml
Problem:
  - AI recommendations exist but hidden in API responses
  - Users cannot see AI deliberation process (transparency)
  - No conversational interface for compliance questions
  - Gate progression (G0-G5) not visualized

Solution (AI Council UI):
  - Chat interface embedded in Compliance Dashboard
  - 3-stage visualization (see how AI reached conclusion)
  - Gate progress bar (G0 → G5 horizontal progression)
  - Tier-aware UI (Lite green, Standard blue, Enterprise gold)

Expert Alignment:
  - Policy Pack v0.9: Tiered compliance visualization
  - Market & OSS: User-friendly compliance UX
  - Deep Research: Metadata layer presentation
```

---

## Dependencies on Previous Sprints

| Dependency | Sprint | Status | Required For |
|------------|--------|--------|--------------|
| AI Council Service | Sprint 26 | ⏳ PENDING | API endpoints |
| Council API (`/api/v1/ai/council/recommend`) | Sprint 26 | ⏳ PENDING | Chat backend |
| Compliance Scanner Integration | Sprint 26 | ⏳ PENDING | Violation data |
| Existing CompliancePage.tsx | Sprint 22 | ✅ DONE | Integration point |

---

## Day 1-2: AI Council Chat Component

### Day 1: Core Chat Interface

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Create `AICouncilChat.tsx` | `frontend/web/src/components/ai/AICouncilChat.tsx` | 4h | FE |
| 1.2 | Create chat message types | `frontend/web/src/types/council.ts` | 1h | FE |
| 1.3 | Implement message rendering | `AICouncilChat.tsx` | 2h | FE |
| 1.4 | Add input with slash commands | `AICouncilChat.tsx` | 1h | FE |

### Day 2: Stage Visualization Components

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Create `Stage1View.tsx` | `frontend/web/src/components/ai/Stage1View.tsx` | 2h | FE |
| 2.2 | Create `Stage2View.tsx` | `frontend/web/src/components/ai/Stage2View.tsx` | 2h | FE |
| 2.3 | Create `Stage3View.tsx` | `frontend/web/src/components/ai/Stage3View.tsx` | 2h | FE |
| 2.4 | Create `CouncilToggle.tsx` | `frontend/web/src/components/ai/CouncilToggle.tsx` | 2h | FE |

### Technical Specifications

```typescript
// frontend/web/src/components/ai/AICouncilChat.tsx (~400 lines)

interface AICouncilChatProps {
  projectId: string
  violationId?: string
  defaultCouncilMode?: boolean
  onRecommendationApplied?: (recommendation: string) => void
}

/**
 * AI Council Chat Component
 *
 * Features:
 * - Conversational chat interface
 * - 3-stage deliberation visualization
 * - Single/Council mode toggle
 * - Slash command support (/fix, /explain, /council)
 *
 * Usage:
 * <AICouncilChat
 *   projectId="uuid"
 *   violationId="uuid"
 *   defaultCouncilMode={true}
 * />
 */
export function AICouncilChat({
  projectId,
  violationId,
  defaultCouncilMode = false,
  onRecommendationApplied,
}: AICouncilChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [councilMode, setCouncilMode] = useState(defaultCouncilMode)
  const [isLoading, setIsLoading] = useState(false)
  const [showDeliberation, setShowDeliberation] = useState(false)

  // ... implementation
}
```

```typescript
// frontend/web/src/types/council.ts (~100 lines)

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  councilDeliberation?: CouncilDeliberation
}

export interface CouncilDeliberation {
  stage1_responses: AIResponse[]
  stage2_rankings: Ranking[]
  stage3_synthesis: FinalAnswer
  total_duration_ms: number
  total_cost_usd: number
  providers_used: string[]
}

export interface AIResponse {
  provider: string
  model: string
  response: string
  duration_ms: number
}

export interface Ranking {
  ranker: string
  rankings: string[]  // ["Response A", "Response B", "Response C"]
  reasoning?: string
}

export interface FinalAnswer {
  answer: string
  confidence: number  // 1-10
  reasoning: string
  suggested_action?: string
}

export type ComplianceTier = 'lite' | 'standard' | 'enterprise'
```

```typescript
// frontend/web/src/components/ai/Stage1View.tsx (~200 lines)

interface Stage1ViewProps {
  responses: AIResponse[]
  isLoading?: boolean
}

/**
 * Stage 1 Visualization - Parallel LLM Responses
 *
 * Shows individual responses from each LLM provider in tabs.
 * Displays provider name, model, response content, and latency.
 */
export function Stage1View({ responses, isLoading }: Stage1ViewProps) {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <Card className="border-blue-200">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            Stage 1
          </Badge>
          <CardTitle className="text-sm">Parallel Queries</CardTitle>
        </div>
        <CardDescription>
          {responses.length} LLM responses collected
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={String(activeTab)} onValueChange={(v) => setActiveTab(Number(v))}>
          <TabsList>
            {responses.map((r, i) => (
              <TabsTrigger key={i} value={String(i)}>
                {r.provider}
              </TabsTrigger>
            ))}
          </TabsList>
          {responses.map((r, i) => (
            <TabsContent key={i} value={String(i)}>
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{r.model}</span>
                  <span>{r.duration_ms}ms</span>
                </div>
                <div className="prose prose-sm max-w-none">
                  {r.response}
                </div>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  )
}
```

```typescript
// frontend/web/src/components/ai/Stage2View.tsx (~200 lines)

interface Stage2ViewProps {
  rankings: Ranking[]
  isLoading?: boolean
}

/**
 * Stage 2 Visualization - Anonymized Peer Review
 *
 * Shows how each LLM ranked the other responses.
 * Uses anonymized labels (Response A, B, C) for fairness.
 */
export function Stage2View({ rankings, isLoading }: Stage2ViewProps) {
  return (
    <Card className="border-purple-200">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-purple-50 text-purple-700">
            Stage 2
          </Badge>
          <CardTitle className="text-sm">Peer Review</CardTitle>
        </div>
        <CardDescription>
          Anonymized ranking by each LLM
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {rankings.map((ranking, i) => (
            <div key={i} className="space-y-2">
              <div className="font-medium text-sm">{ranking.ranker}</div>
              <div className="flex gap-2">
                {ranking.rankings.map((r, j) => (
                  <Badge
                    key={j}
                    variant={j === 0 ? 'default' : 'outline'}
                    className={j === 0 ? 'bg-green-500' : ''}
                  >
                    #{j + 1} {r}
                  </Badge>
                ))}
              </div>
              {ranking.reasoning && (
                <p className="text-xs text-muted-foreground">
                  {ranking.reasoning}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

```typescript
// frontend/web/src/components/ai/Stage3View.tsx (~150 lines)

interface Stage3ViewProps {
  synthesis: FinalAnswer
  isLoading?: boolean
}

/**
 * Stage 3 Visualization - Chairman Synthesis
 *
 * Shows the final synthesized answer from the chairman LLM.
 * Highlighted in green to indicate final recommendation.
 */
export function Stage3View({ synthesis, isLoading }: Stage3ViewProps) {
  return (
    <Card className="border-green-300 bg-green-50">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-green-100 text-green-800">
            Stage 3
          </Badge>
          <CardTitle className="text-sm">Final Recommendation</CardTitle>
          <Badge className="ml-auto bg-green-600">
            {synthesis.confidence}/10 Confidence
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="prose prose-sm max-w-none prose-green">
          {synthesis.answer}
        </div>

        {synthesis.suggested_action && (
          <div className="p-3 bg-white rounded-lg border border-green-200">
            <div className="text-xs font-medium text-green-700 mb-1">
              Suggested Action
            </div>
            <code className="text-sm">{synthesis.suggested_action}</code>
          </div>
        )}

        <Collapsible>
          <CollapsibleTrigger className="text-xs text-green-700 hover:underline">
            View reasoning
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2 text-sm text-muted-foreground">
            {synthesis.reasoning}
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
```

---

## Day 3: Gate Progress & Tier Components

### Gate Progress Bar

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Create `GateProgressBar.tsx` | `frontend/web/src/components/ai/GateProgressBar.tsx` | 3h | FE |
| 3.2 | Create `TierBadge.tsx` | `frontend/web/src/components/ai/TierBadge.tsx` | 1h | FE |
| 3.3 | Create `EvidenceChecklist.tsx` | `frontend/web/src/components/ai/EvidenceChecklist.tsx` | 3h | FE |
| 3.4 | Add API hooks | `frontend/web/src/api/council.ts` | 1h | FE |

### Technical Specifications

```typescript
// frontend/web/src/components/ai/GateProgressBar.tsx (~150 lines)

interface GateProgressBarProps {
  currentGate: GateType
  gateStatuses: Record<GateType, GateStatus>
  tier: ComplianceTier
  onGateClick?: (gate: GateType) => void
}

type GateType = 'G0.1' | 'G0.2' | 'G1' | 'G2' | 'G3' | 'G4' | 'G5'
type GateStatus = 'passed' | 'current' | 'pending' | 'blocked'

/**
 * Gate Progress Bar - G0 → G5 Horizontal Visualization
 *
 * Shows progression through SDLC 4.9.1 gates.
 * Color-coded by tier (Lite=green, Standard=blue, Enterprise=gold).
 *
 * Visual:
 * ┌─────────────────────────────────────────────────────────────────┐
 * │  G0.1     G0.2      G1       G2       G3       G4       G5     │
 * │   ●━━━━━━━●━━━━━━━●━━━━━━━○━━━━━━━○━━━━━━━○━━━━━━━○          │
 * │   ✓       ✓       ✓       ←       ←       ←       ←          │
 * │  Done    Done    Done   Current Pending Pending Pending       │
 * └─────────────────────────────────────────────────────────────────┘
 */
export function GateProgressBar({
  currentGate,
  gateStatuses,
  tier,
  onGateClick,
}: GateProgressBarProps) {
  const gates: GateType[] = ['G0.1', 'G0.2', 'G1', 'G2', 'G3', 'G4', 'G5']
  const tierColors = {
    lite: 'bg-green-500',
    standard: 'bg-blue-500',
    enterprise: 'bg-amber-500',
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Gate Progress</CardTitle>
          <TierBadge tier={tier} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between relative">
          {/* Progress line */}
          <div className="absolute top-4 left-0 right-0 h-1 bg-muted" />
          <div
            className={`absolute top-4 left-0 h-1 ${tierColors[tier]}`}
            style={{
              width: `${(gates.indexOf(currentGate) / (gates.length - 1)) * 100}%`,
            }}
          />

          {/* Gate nodes */}
          {gates.map((gate) => {
            const status = gateStatuses[gate]
            return (
              <button
                key={gate}
                onClick={() => onGateClick?.(gate)}
                className="relative z-10 flex flex-col items-center"
              >
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center
                    ${status === 'passed' ? tierColors[tier] + ' text-white' : ''}
                    ${status === 'current' ? 'ring-2 ring-offset-2 ring-' + tier : ''}
                    ${status === 'pending' ? 'bg-muted text-muted-foreground' : ''}
                    ${status === 'blocked' ? 'bg-red-100 text-red-600' : ''}
                  `}
                >
                  {status === 'passed' ? '✓' : gate.replace('G', '')}
                </div>
                <span className="mt-1 text-xs">{gate}</span>
              </button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
```

```typescript
// frontend/web/src/components/ai/TierBadge.tsx (~50 lines)

interface TierBadgeProps {
  tier: ComplianceTier
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

/**
 * Tier Badge - Visual indicator for compliance tier
 *
 * Colors:
 * - Lite: Green (coverage 70%)
 * - Standard: Blue (coverage 80% + SAST)
 * - Enterprise: Gold (coverage 85% + DAST + pen_test)
 */
export function TierBadge({ tier, showLabel = true, size = 'md' }: TierBadgeProps) {
  const config = {
    lite: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      border: 'border-green-300',
      label: 'Lite',
      icon: '🌱',
    },
    standard: {
      bg: 'bg-blue-100',
      text: 'text-blue-800',
      border: 'border-blue-300',
      label: 'Standard',
      icon: '⚡',
    },
    enterprise: {
      bg: 'bg-amber-100',
      text: 'text-amber-800',
      border: 'border-amber-300',
      label: 'Enterprise',
      icon: '👑',
    },
  }

  const c = config[tier]
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  }

  return (
    <Badge className={`${c.bg} ${c.text} ${c.border} ${sizeClasses[size]}`}>
      {c.icon} {showLabel && c.label}
    </Badge>
  )
}
```

```typescript
// frontend/web/src/components/ai/EvidenceChecklist.tsx (~200 lines)

interface EvidenceChecklistProps {
  gateType: GateType
  tier: ComplianceTier
  evidenceItems: EvidenceItem[]
  onUpload?: (evidenceType: string) => void
}

interface EvidenceItem {
  type: string
  label: string
  required: boolean
  status: 'uploaded' | 'missing' | 'pending_review'
  uploadedAt?: Date
  reviewedBy?: string
}

/**
 * Evidence Checklist - Required evidence per gate
 *
 * Shows what evidence is required for the current gate,
 * based on the selected compliance tier.
 *
 * Policy Pack v0.9 Requirements:
 * - G0.1: Problem statement, user interviews
 * - G1: Market analysis, legal review
 * - G2: Architecture diagram, API spec
 * - G3: Test results, security scan
 */
export function EvidenceChecklist({
  gateType,
  tier,
  evidenceItems,
  onUpload,
}: EvidenceChecklistProps) {
  const requiredItems = evidenceItems.filter((e) => e.required)
  const uploadedCount = evidenceItems.filter((e) => e.status === 'uploaded').length
  const progress = (uploadedCount / evidenceItems.length) * 100

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Evidence Checklist</CardTitle>
            <CardDescription>
              {uploadedCount}/{evidenceItems.length} items for {gateType}
            </CardDescription>
          </div>
          <TierBadge tier={tier} size="sm" />
        </div>
        <Progress value={progress} className="mt-2" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {evidenceItems.map((item) => (
            <div
              key={item.type}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50"
            >
              <div className="flex items-center gap-2">
                {item.status === 'uploaded' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : item.status === 'pending_review' ? (
                  <Clock className="h-5 w-5 text-yellow-500" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <span className="text-sm">{item.label}</span>
                  {item.required && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      Required
                    </Badge>
                  )}
                </div>
              </div>
              {item.status === 'missing' && onUpload && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onUpload(item.type)}
                >
                  <Upload className="h-4 w-4 mr-1" />
                  Upload
                </Button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Day 4: Dashboard Integration

### Integration with Existing Pages

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Integrate chat into CompliancePage | `frontend/web/src/pages/CompliancePage.tsx` | 3h | FE |
| 4.2 | Add chat to ViolationCard | `frontend/web/src/components/compliance/ViolationCard.tsx` | 2h | FE |
| 4.3 | Create GateDetailPage AI section | `frontend/web/src/pages/GateDetailPage.tsx` | 2h | FE |
| 4.4 | Add tier selector to ProjectSettings | `frontend/web/src/pages/ProjectSettingsPage.tsx` | 1h | FE |

### Integration Code Sketch

```typescript
// frontend/web/src/pages/CompliancePage.tsx (MODIFIED +100 lines)

import { AICouncilChat } from '@/components/ai/AICouncilChat'
import { GateProgressBar } from '@/components/ai/GateProgressBar'
import { TierBadge } from '@/components/ai/TierBadge'

export default function CompliancePage() {
  const [selectedViolation, setSelectedViolation] = useState<string | null>(null)
  const [showAIChat, setShowAIChat] = useState(false)

  // ... existing code ...

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* NEW: Gate Progress Bar */}
        <GateProgressBar
          currentGate={projectGateStatus?.currentGate ?? 'G0.1'}
          gateStatuses={projectGateStatus?.gates ?? {}}
          tier={project?.tier ?? 'standard'}
        />

        {/* ... existing stats grid ... */}

        {/* NEW: AI Chat Drawer */}
        <Sheet open={showAIChat} onOpenChange={setShowAIChat}>
          <SheetContent side="right" className="w-[500px] sm:w-[600px]">
            <SheetHeader>
              <SheetTitle>AI Compliance Assistant</SheetTitle>
              <SheetDescription>
                Ask questions or get fix recommendations
              </SheetDescription>
            </SheetHeader>
            <AICouncilChat
              projectId={selectedProjectId}
              violationId={selectedViolation ?? undefined}
              defaultCouncilMode={true}
            />
          </SheetContent>
        </Sheet>

        {/* ... existing violations section with AI button ... */}
      </div>
    </DashboardLayout>
  )
}
```

```typescript
// frontend/web/src/components/compliance/ViolationCard.tsx (MODIFIED +50 lines)

import { Button } from '@/components/ui/button'
import { Sparkles } from 'lucide-react'

interface ViolationCardProps {
  violation: Violation
  onResolved?: () => void
  onAskAI?: (violationId: string) => void  // NEW
}

export function ViolationCard({ violation, onResolved, onAskAI }: ViolationCardProps) {
  // ... existing code ...

  return (
    <Card className={severityStyles[violation.severity]}>
      {/* ... existing header ... */}

      <CardContent>
        {/* ... existing content ... */}

        {/* NEW: AI Fix Button */}
        <div className="mt-4 flex gap-2">
          {violation.ai_recommendation ? (
            <div className="p-3 bg-blue-50 rounded-lg text-sm">
              <div className="flex items-center gap-1 text-blue-700 font-medium mb-1">
                <Sparkles className="h-4 w-4" />
                AI Recommendation
                {violation.ai_council_used && (
                  <Badge variant="outline" className="ml-2 text-xs">
                    Council Mode
                  </Badge>
                )}
              </div>
              <p>{violation.ai_recommendation}</p>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onAskAI?.(violation.id)}
            >
              <Sparkles className="h-4 w-4 mr-1" />
              Get AI Fix
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## Day 5: Tests + Documentation

### Test Coverage

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Unit tests for chat component | `frontend/web/src/__tests__/AICouncilChat.test.tsx` | 2h | FE |
| 5.2 | Unit tests for stage views | `frontend/web/src/__tests__/StageViews.test.tsx` | 2h | FE |
| 5.3 | E2E tests | `frontend/web/e2e/ai-council-chat.spec.ts` | 2h | FE |
| 5.4 | Documentation + CTO review | `docs/` | 2h | FE |

### E2E Test Specification

```typescript
// frontend/web/e2e/ai-council-chat.spec.ts (~150 lines)

import { test, expect } from '@playwright/test'
import { setupAuthenticatedUser, createTestViolation } from './helpers'

test.describe('AI Council Chat', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedUser(page)
    await createTestViolation(page, { severity: 'critical' })
  })

  test('should open chat drawer from violation card', async ({ page }) => {
    await page.goto('/compliance')
    await page.getByRole('button', { name: 'Get AI Fix' }).first().click()

    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText('AI Compliance Assistant')).toBeVisible()
  })

  test('should toggle between single and council mode', async ({ page }) => {
    await page.goto('/compliance')
    await page.getByRole('button', { name: 'Get AI Fix' }).first().click()

    const toggle = page.getByRole('switch', { name: 'Council Mode' })
    await expect(toggle).toBeVisible()

    // Default: Council mode ON for CRITICAL violations
    await expect(toggle).toBeChecked()

    // Toggle OFF
    await toggle.click()
    await expect(toggle).not.toBeChecked()
  })

  test('should display 3-stage deliberation in council mode', async ({ page }) => {
    await page.goto('/compliance')
    await page.getByRole('button', { name: 'Get AI Fix' }).first().click()

    // Send message
    await page.getByPlaceholder('Ask about this violation...').fill('How do I fix this?')
    await page.getByRole('button', { name: 'Send' }).click()

    // Wait for response
    await expect(page.getByText('Stage 1')).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('Stage 2')).toBeVisible()
    await expect(page.getByText('Stage 3')).toBeVisible()
    await expect(page.getByText('Final Recommendation')).toBeVisible()
  })

  test('should show gate progress bar', async ({ page }) => {
    await page.goto('/compliance')

    await expect(page.getByText('Gate Progress')).toBeVisible()
    await expect(page.getByText('G0.1')).toBeVisible()
    await expect(page.getByText('G5')).toBeVisible()
  })

  test('should display tier badge', async ({ page }) => {
    await page.goto('/compliance')

    await expect(page.getByText(/Lite|Standard|Enterprise/)).toBeVisible()
  })
})
```

### Documentation Checklist

| # | Document | Location | Status |
|---|----------|----------|--------|
| 5.5 | Component storybook | `frontend/web/src/stories/AICouncilChat.stories.tsx` | ⏳ |
| 5.6 | API integration guide | `docs/04-API/ai-council-frontend.md` | ⏳ |
| 5.7 | User guide | `docs/05-User-Guide/ai-assistant.md` | ⏳ |
| 5.8 | CTO sign-off document | `docs/09-Executive-Reports/` | ⏳ |

---

## Deliverables Summary

### New Files (~1,800 lines)

| File | Lines | Description |
|------|-------|-------------|
| `frontend/web/src/components/ai/AICouncilChat.tsx` | 400 | Main chat interface |
| `frontend/web/src/components/ai/Stage1View.tsx` | 200 | Individual LLM responses (tabs) |
| `frontend/web/src/components/ai/Stage2View.tsx` | 200 | Peer rankings visualization |
| `frontend/web/src/components/ai/Stage3View.tsx` | 150 | Final synthesized answer (green) |
| `frontend/web/src/components/ai/CouncilToggle.tsx` | 100 | Single vs Council mode toggle |
| `frontend/web/src/components/ai/TierBadge.tsx` | 50 | Tier indicator badge |
| `frontend/web/src/components/ai/GateProgressBar.tsx` | 150 | G0→G5 horizontal progress |
| `frontend/web/src/components/ai/EvidenceChecklist.tsx` | 200 | Required evidence per gate |
| `frontend/web/src/types/council.ts` | 100 | TypeScript types |
| `frontend/web/src/api/council.ts` | 100 | API hooks |
| `frontend/web/e2e/ai-council-chat.spec.ts` | 150 | E2E tests |

### Modified Files (~200 lines)

| File | Changes | Description |
|------|---------|-------------|
| `frontend/web/src/pages/CompliancePage.tsx` | +100 | AI chat integration |
| `frontend/web/src/components/compliance/ViolationCard.tsx` | +50 | AI button |
| `frontend/web/src/pages/GateDetailPage.tsx` | +50 | Gate-specific AI |

---

## API Dependencies (Sprint 26)

### Required Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ai/council/recommend` | POST | Generate council recommendation |
| `/api/v1/ai/council/deliberation/{id}` | GET | Get full deliberation history |
| `/api/v1/projects/{id}/gate-status` | GET | Get current gate + progress |
| `/api/v1/projects/{id}/evidence-checklist` | GET | Evidence requirements by gate |

### API Response Types

```typescript
// Expected response from POST /api/v1/ai/council/recommend
interface CouncilRecommendResponse {
  request_id: string
  recommendation: string
  confidence_score: number
  council_mode: boolean
  council_deliberation?: {
    stage1_responses: AIResponse[]
    stage2_rankings: Ranking[]
    stage3_synthesis: FinalAnswer
  }
  total_duration_ms: number
  total_cost_usd: number
  providers_used: string[]
}
```

---

## Design System Integration

### shadcn/ui Components Used

| Component | Purpose |
|-----------|---------|
| `Card` | Container for stage views |
| `Badge` | Tier indicator, stage labels |
| `Tabs` | Stage 1 provider tabs |
| `Sheet` | Chat drawer |
| `Progress` | Evidence checklist progress |
| `Collapsible` | Reasoning expandable sections |
| `Button` | Actions, toggles |

### Color System (Tier-Aware)

```css
/* Tier Colors */
--tier-lite: theme(colors.green.500);
--tier-standard: theme(colors.blue.500);
--tier-enterprise: theme(colors.amber.500);

/* Stage Colors */
--stage-1: theme(colors.blue.500);    /* Parallel Queries */
--stage-2: theme(colors.purple.500);  /* Peer Review */
--stage-3: theme(colors.green.500);   /* Final Answer */
```

---

## Performance Budget

| Metric | Target | Measurement |
|--------|--------|-------------|
| Chat component render | <100ms | React Profiler |
| Stage view render | <50ms | React Profiler |
| API response display | <500ms | Network + render |
| Gate progress bar render | <50ms | React Profiler |
| LCP (Largest Contentful Paint) | <2.5s | Lighthouse |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Council API slow (>8s) | Medium | High | Loading skeletons, timeout fallback |
| API not ready (Sprint 26 delay) | Low | High | Mock API for UI development |
| Complex state management | Medium | Medium | Use React Query for server state |
| Accessibility issues | Low | Medium | ARIA labels, keyboard navigation |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| AI Chat Adoption | 60%+ | Users clicking "Get AI Fix" |
| Deliberation View Rate | 40%+ | Users expanding stage views |
| Recommendation Apply Rate | 30%+ | Applied recommendations |
| User Satisfaction | 4.5★+ | In-app feedback |

---

## Sign-off Checklist

| # | Criteria | Target | Status |
|---|----------|--------|--------|
| 1 | All components implemented | Complete | ⏳ |
| 2 | Unit tests passing | 95%+ coverage | ⏳ |
| 3 | E2E tests passing | 100% | ⏳ |
| 4 | Performance budget met | <100ms render | ⏳ |
| 5 | Accessibility (WCAG 2.1 AA) | PASS | ⏳ |
| 6 | Design review | PASS | ⏳ |
| 7 | CTO approval | ✅ | ⏳ |

---

**Sprint Status**: ✅ APPROVED - Awaiting Implementation
**CTO Rating**: 9.2/10
**Pre-Planning**: Complete (Sprint 22)
**Target Start**: Sprint 28 (Week 13)
**Dependencies**: Sprint 26 (AI Council Service), Sprint 27 (VS Code Extension)
