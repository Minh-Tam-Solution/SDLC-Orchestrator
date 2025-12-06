/**
 * File: frontend/web/src/types/council.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * TypeScript types for AI Council chat interface and
 * 3-stage deliberation visualization.
 */

// =========================================================================
// CHAT MESSAGE TYPES
// =========================================================================

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  councilDeliberation?: CouncilDeliberation
  isLoading?: boolean
  error?: string
}

// =========================================================================
// AI COUNCIL DELIBERATION TYPES
// =========================================================================

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
  confidence?: number
}

export interface Ranking {
  ranker: string
  rankings: string[]
  reasoning?: string
}

export interface FinalAnswer {
  answer: string
  confidence: number
  reasoning: string
  suggested_action?: string
}

// =========================================================================
// COMPLIANCE TIER TYPES
// =========================================================================

export type ComplianceTier = 'lite' | 'standard' | 'enterprise'

export interface TierConfig {
  name: string
  label: string
  icon: string
  color: string
  bgColor: string
  borderColor: string
  textColor: string
  coverage: number
  features: string[]
}

export const TIER_CONFIGS: Record<ComplianceTier, TierConfig> = {
  lite: {
    name: 'lite',
    label: 'Lite',
    icon: '🌱',
    color: 'green',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-300',
    textColor: 'text-green-800',
    coverage: 70,
    features: ['Basic gates', 'Manual evidence', 'Single LLM'],
  },
  standard: {
    name: 'standard',
    label: 'Standard',
    icon: '⚡',
    color: 'blue',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-300',
    textColor: 'text-blue-800',
    coverage: 80,
    features: ['All gates', 'SAST scanning', 'Council mode'],
  },
  enterprise: {
    name: 'enterprise',
    label: 'Enterprise',
    icon: '👑',
    color: 'amber',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-300',
    textColor: 'text-amber-800',
    coverage: 85,
    features: ['Full compliance', 'DAST + Pen Test', 'Priority support'],
  },
}

// =========================================================================
// GATE PROGRESS TYPES
// =========================================================================

export type GateType = 'G0.1' | 'G0.2' | 'G1' | 'G2' | 'G3' | 'G4' | 'G5'

export type GateProgressStatus = 'passed' | 'current' | 'pending' | 'blocked'

export interface GateProgress {
  gate: GateType
  status: GateProgressStatus
  label: string
  description: string
  evidenceRequired: number
  evidenceUploaded: number
}

export const GATE_DEFINITIONS: Record<GateType, { label: string; description: string }> = {
  'G0.1': { label: 'Problem', description: 'Problem definition validated' },
  'G0.2': { label: 'Solution', description: 'Solution diversity explored' },
  'G1': { label: 'Market', description: 'Market & legal validation' },
  'G2': { label: 'Design', description: 'Architecture ready' },
  'G3': { label: 'Ship', description: 'Ready for release' },
  'G4': { label: 'Operate', description: 'Production ready' },
  'G5': { label: 'Learn', description: 'Retrospective complete' },
}

// =========================================================================
// EVIDENCE CHECKLIST TYPES
// =========================================================================

export type EvidenceStatus = 'uploaded' | 'missing' | 'pending_review' | 'rejected'

export interface EvidenceItem {
  type: string
  label: string
  required: boolean
  status: EvidenceStatus
  uploadedAt?: Date
  reviewedBy?: string
  tier: ComplianceTier
}

// =========================================================================
// API REQUEST/RESPONSE TYPES
// =========================================================================

export interface CouncilRecommendRequest {
  project_id: string
  violation_id?: string
  question: string
  council_mode: boolean
  context?: Record<string, unknown>
}

export interface CouncilRecommendResponse {
  request_id: string
  recommendation: string
  confidence_score: number
  council_mode: boolean
  council_deliberation?: CouncilDeliberation
  total_duration_ms: number
  total_cost_usd: number
  providers_used: string[]
}

export interface GateStatusResponse {
  project_id: string
  current_gate: GateType
  gates: Record<GateType, GateProgressStatus>
  tier: ComplianceTier
  overall_progress: number
}

export interface EvidenceChecklistResponse {
  gate_type: GateType
  tier: ComplianceTier
  items: EvidenceItem[]
  total: number
  uploaded: number
  missing: number
  progress: number
}

// =========================================================================
// CHAT COMPONENT PROPS TYPES
// =========================================================================

export interface AICouncilChatProps {
  projectId: string
  violationId?: string
  defaultCouncilMode?: boolean
  onRecommendationApplied?: (recommendation: string) => void
  className?: string
}

export interface Stage1ViewProps {
  responses: AIResponse[]
  isLoading?: boolean
}

export interface Stage2ViewProps {
  rankings: Ranking[]
  isLoading?: boolean
}

export interface Stage3ViewProps {
  synthesis: FinalAnswer
  isLoading?: boolean
  onApply?: () => void
}

export interface CouncilToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  disabled?: boolean
}

export interface GateProgressBarProps {
  currentGate: GateType
  gateStatuses: Record<GateType, GateProgressStatus>
  tier: ComplianceTier
  onGateClick?: (gate: GateType) => void
}

export interface TierBadgeProps {
  tier: ComplianceTier
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export interface EvidenceChecklistProps {
  gateType: GateType
  tier: ComplianceTier
  evidenceItems: EvidenceItem[]
  onUpload?: (evidenceType: string) => void
}
