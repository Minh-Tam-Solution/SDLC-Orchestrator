/**
 * File: frontend/web/src/components/sdlc/index.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * Barrel export for SDLC validation components.
 */

// Main Dashboard
export { SDLCComplianceDashboard, CompactComplianceCard } from './SDLCComplianceDashboard'

// Tier Badge
export { SDLCTierBadge, getTierFromScore, getTierColorClasses } from './SDLCTierBadge'

// Score Components
export { ComplianceScoreCircle, ComplianceScoreBar } from './ComplianceScoreCircle'

// Stage Progress
export { StageProgressGrid, CompactStageProgress } from './StageProgressGrid'

// History Charts
export {
  ValidationHistoryChart,
  ValidationHistoryList,
  MiniTrendChart,
} from './ValidationHistoryChart'

// Issue List
export { IssueList, IssueSummary } from './IssueList'
