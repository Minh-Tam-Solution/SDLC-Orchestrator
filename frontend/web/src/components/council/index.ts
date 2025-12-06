/**
 * File: frontend/web/src/components/council/index.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Barrel export for AI Council chat components.
 */

// Day 1 Components
export { TierBadge } from './TierBadge'
export { CouncilToggle } from './CouncilToggle'
export { GateProgressBar } from './GateProgressBar'

// Day 2 Components
export { Stage1View } from './Stage1View'
export { Stage2View } from './Stage2View'
export { Stage3View } from './Stage3View'
export { ChatMessage } from './ChatMessage'
export { AICouncilChat } from './AICouncilChat'

// Day 4: Lazy-loaded components for performance
export { AICouncilChatLazy } from './AICouncilChatLazy'

// Re-export types from council.ts for convenience
export type {
  ChatMessage as ChatMessageType,
  CouncilDeliberation,
  AIResponse,
  Ranking,
  FinalAnswer,
  ComplianceTier,
  TierConfig,
  GateType,
  GateProgressStatus,
  GateProgress,
  EvidenceStatus,
  EvidenceItem,
  CouncilRecommendRequest,
  CouncilRecommendResponse,
  GateStatusResponse,
  EvidenceChecklistResponse,
  AICouncilChatProps,
  Stage1ViewProps,
  Stage2ViewProps,
  Stage3ViewProps,
  CouncilToggleProps,
  GateProgressBarProps,
  TierBadgeProps,
  EvidenceChecklistProps,
} from '@/types/council'
