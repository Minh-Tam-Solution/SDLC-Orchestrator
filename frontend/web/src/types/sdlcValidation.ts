/**
 * File: frontend/web/src/types/sdlcValidation.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-06
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 30 - CI/CD & Web Integration (Day 4)
 *
 * Description:
 * TypeScript types for SDLC 5.0.0 Structure Validation API.
 * Supports 4-tier classification and 11-stage lifecycle.
 */

// =========================================================================
// SDLC 5.0.0 TIER TYPES
// =========================================================================

export type SDLCTier = 'lite' | 'standard' | 'professional' | 'enterprise'

export interface TierConfig {
  name: SDLCTier
  label: string
  icon: string
  color: string
  bgColor: string
  borderColor: string
  textColor: string
  requiredStages: number
  description: string
}

export const SDLC_TIER_CONFIGS: Record<SDLCTier, TierConfig> = {
  lite: {
    name: 'lite',
    label: 'Lite',
    icon: '🌱',
    color: 'green',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-300',
    textColor: 'text-green-800',
    requiredStages: 5,
    description: 'Minimal SDLC structure for small projects',
  },
  standard: {
    name: 'standard',
    label: 'Standard',
    icon: '⚡',
    color: 'blue',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-300',
    textColor: 'text-blue-800',
    requiredStages: 8,
    description: 'Standard SDLC structure for mid-size projects',
  },
  professional: {
    name: 'professional',
    label: 'Professional',
    icon: '🏆',
    color: 'purple',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-300',
    textColor: 'text-purple-800',
    requiredStages: 10,
    description: 'Full SDLC structure for enterprise projects',
  },
  enterprise: {
    name: 'enterprise',
    label: 'Enterprise',
    icon: '👑',
    color: 'amber',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-300',
    textColor: 'text-amber-800',
    requiredStages: 11,
    description: 'Complete SDLC structure with all stages including Archive',
  },
}

// =========================================================================
// SDLC 5.0.0 STAGE TYPES
// =========================================================================

export type SDLCStageId =
  | '00'
  | '01'
  | '02'
  | '03'
  | '04'
  | '05'
  | '06'
  | '07'
  | '08'
  | '09'
  | '10'

export interface SDLCStageConfig {
  id: SDLCStageId
  name: string
  folderName: string
  description: string
  p0Artifacts: string[]
}

export const SDLC_STAGES: Record<SDLCStageId, SDLCStageConfig> = {
  '00': {
    id: '00',
    name: 'Project Foundation',
    folderName: '00-Project-Foundation',
    description: 'Vision, Design Thinking, Problem Statement, Roadmap',
    p0Artifacts: ['Product-Vision.md', 'Problem-Statement.md'],
  },
  '01': {
    id: '01',
    name: 'Planning & Analysis',
    folderName: '01-Planning-Analysis',
    description: 'Requirements, User Stories, Data Model',
    p0Artifacts: ['Functional-Requirements-Document.md'],
  },
  '02': {
    id: '02',
    name: 'Design & Architecture',
    folderName: '02-Design-Architecture',
    description: 'System Architecture, API Design, ADRs',
    p0Artifacts: ['System-Architecture-Document.md', 'openapi.yml'],
  },
  '03': {
    id: '03',
    name: 'Development & Implementation',
    folderName: '03-Development-Implementation',
    description: 'Sprint Plans, Setup Guides, Code Standards',
    p0Artifacts: ['Sprint-Plans/', 'Setup-Guides/'],
  },
  '04': {
    id: '04',
    name: 'Testing & QA',
    folderName: '04-Testing-QA',
    description: 'Test Plans, Test Cases, QA Reports',
    p0Artifacts: ['Test-Plan.md'],
  },
  '05': {
    id: '05',
    name: 'Deployment & Release',
    folderName: '05-Deployment-Release',
    description: 'Deployment Guides, Release Notes',
    p0Artifacts: ['Deployment-Guide.md'],
  },
  '06': {
    id: '06',
    name: 'Operations & Support',
    folderName: '06-Operations-Support',
    description: 'Runbooks, Incident Response, SLAs',
    p0Artifacts: ['Runbook.md'],
  },
  '07': {
    id: '07',
    name: 'Maintenance & Evolution',
    folderName: '07-Maintenance-Evolution',
    description: 'Change Management, Technical Debt',
    p0Artifacts: [],
  },
  '08': {
    id: '08',
    name: 'Training & Knowledge',
    folderName: '08-Training-Knowledge',
    description: 'User Guides, Training Materials',
    p0Artifacts: [],
  },
  '09': {
    id: '09',
    name: 'Executive Reports',
    folderName: '09-Executive-Reports',
    description: 'CTO Reports, CPO Reports, Gate Reviews',
    p0Artifacts: [],
  },
  '10': {
    id: '10',
    name: 'Archive',
    folderName: '10-Archive',
    description: 'Historical Documents, Deprecated Content',
    p0Artifacts: [],
  },
}

// =========================================================================
// VALIDATION ISSUE TYPES
// =========================================================================

export type IssueSeverity = 'error' | 'warning' | 'info'

export interface ValidationIssue {
  code: string
  severity: IssueSeverity
  message: string
  path?: string
  stageId?: SDLCStageId
  fixSuggestion?: string
}

// =========================================================================
// STAGE INFO TYPES
// =========================================================================

export interface StageInfo {
  stageId: SDLCStageId
  stageName: string
  folderName: string
  fileCount: number
  hasReadme: boolean
}

// =========================================================================
// P0 ARTIFACT STATUS
// =========================================================================

export interface P0Status {
  total: number
  found: number
  missing: number
  coverage: number
  missingArtifacts?: string[]
}

// =========================================================================
// API REQUEST/RESPONSE TYPES
// =========================================================================

export interface ValidateStructureRequest {
  tier?: SDLCTier
  docsRoot?: string
  strictMode?: boolean
  includeP0?: boolean
}

export interface ValidateStructureResponse {
  id: string
  projectId: string
  isCompliant: boolean
  complianceScore: number
  tier: SDLCTier
  tierDetected: boolean
  stagesFound: StageInfo[]
  stagesMissing: string[]
  stagesRequired: number
  p0Status: P0Status
  errorCount: number
  warningCount: number
  issues: ValidationIssue[]
  validatedAt: string
  validationTimeMs: number
}

export interface ValidationHistoryItem {
  id: string
  isCompliant: boolean
  complianceScore: number
  tier: SDLCTier
  stagesFound: number
  stagesRequired: number
  errorCount: number
  warningCount: number
  validatedAt: string
}

export interface ComplianceSummary {
  projectId: string
  projectName: string
  tier: SDLCTier
  currentScore: number
  isCompliant: boolean
  validationCount: number
  lastValidatedAt?: string
  scoreTrend: number[]
  complianceHistory: {
    date: string
    score: number
    isCompliant: boolean
  }[]
  stagesSummary: {
    found: number
    required: number
    missing: string[]
  }
  p0Summary: P0Status
  issueSummary: {
    errors: number
    warnings: number
    info: number
  }
}

// =========================================================================
// COMPONENT PROP TYPES
// =========================================================================

export interface SDLCComplianceDashboardProps {
  projectId: string
  onValidate?: () => void
  className?: string
}

export interface TierBadgeSDLCProps {
  tier: SDLCTier
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export interface ComplianceScoreCircleProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  animate?: boolean
}

export interface ValidationHistoryChartProps {
  history: ValidationHistoryItem[]
  maxItems?: number
}

export interface StageProgressGridProps {
  stagesFound: StageInfo[]
  stagesMissing: string[]
  tier: SDLCTier
}

export interface IssueListProps {
  issues: ValidationIssue[]
  maxItems?: number
  showSuggestions?: boolean
}

// =========================================================================
// UTILITY TYPES
// =========================================================================

export interface ValidationState {
  isLoading: boolean
  isValidating: boolean
  lastValidation?: ValidateStructureResponse
  error?: string
}

export type ScoreTrend = 'up' | 'down' | 'stable'

export function calculateScoreTrend(history: number[]): ScoreTrend {
  if (history.length < 2) return 'stable'
  const latest = history[history.length - 1] ?? 0
  const previous = history[history.length - 2] ?? 0
  if (latest > previous) return 'up'
  if (latest < previous) return 'down'
  return 'stable'
}

export function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  if (score >= 50) return 'text-orange-600'
  return 'text-red-600'
}

export function getScoreBgColor(score: number): string {
  if (score >= 90) return 'bg-green-100'
  if (score >= 70) return 'bg-yellow-100'
  if (score >= 50) return 'bg-orange-100'
  return 'bg-red-100'
}

export function getSeverityColor(severity: IssueSeverity): string {
  switch (severity) {
    case 'error':
      return 'text-red-600'
    case 'warning':
      return 'text-yellow-600'
    case 'info':
      return 'text-blue-600'
    default:
      return 'text-gray-600'
  }
}

export function getSeverityIcon(severity: IssueSeverity): string {
  switch (severity) {
    case 'error':
      return '❌'
    case 'warning':
      return '⚠️'
    case 'info':
      return 'ℹ️'
    default:
      return '•'
  }
}
