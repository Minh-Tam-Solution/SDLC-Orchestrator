/**
 * File: frontend/web/src/types/api.ts
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-11-27
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * TypeScript types for SDLC Orchestrator API.
 * Generated from backend Pydantic schemas.
 */

// =========================================================================
// AUTHENTICATION TYPES
// =========================================================================

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface LogoutRequest {
  refresh_token: string
}

export interface UserProfile {
  id: string
  email: string
  name: string
  is_active: boolean
  is_superuser: boolean
  roles: string[]
  oauth_providers: string[]
  created_at: string
  last_login_at: string | null
}

// =========================================================================
// PROJECT TYPES
// =========================================================================

export type GateStatus = 'passed' | 'failed' | 'pending' | 'not_started'

export interface Project {
  id: string
  name: string
  description: string
  current_stage: string
  gate_status: GateStatus
  progress: number
  created_at: string | null
  updated_at: string | null
}

export interface ProjectDetail extends Project {
  owner_id: string
  is_active: boolean
  gates: GateResponse[]
}

export interface ProjectCreateRequest {
  name: string
  description?: string
}

export interface ProjectUpdateRequest {
  name?: string
  description?: string
}

// =========================================================================
// GATE TYPES
// =========================================================================

export type GateStatusEnum = 'DRAFT' | 'PENDING' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED'

export interface GateCreateRequest {
  project_id: string
  gate_name: string
  gate_type: string
  stage: string
  description?: string
  exit_criteria?: Array<{ criterion: string; status: string }>
}

export interface GateUpdateRequest {
  gate_name?: string
  gate_type?: string
  description?: string
  exit_criteria?: Array<{ criterion: string; status: string }>
}

export interface GateResponse {
  id: string
  project_id: string
  gate_name: string
  gate_type: string
  stage: string
  status: GateStatusEnum
  description: string | null
  exit_criteria: Array<{ criterion: string; status: string }>
  created_by: string | null
  created_at: string
  updated_at: string
  approved_at: string | null
  deleted_at: string | null
  approvals: GateApproval[]
  evidence_count: number
  policy_violations: PolicyViolation[]
}

export interface GateListResponse {
  items: GateResponse[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface GateSubmitRequest {
  message?: string
}

export interface GateApprovalRequest {
  approved: boolean
  comments?: string
}

export interface GateApproval {
  id: string
  gate_id: string
  approved_by: string
  approved_by_name: string
  approved_by_role: string
  is_approved: boolean
  comments: string | null
  approved_at: string
}

export interface PolicyViolation {
  message: string
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  location?: string
}

// =========================================================================
// EVIDENCE TYPES
// =========================================================================

export type EvidenceType =
  | 'DESIGN_DOCUMENT'
  | 'TEST_RESULTS'
  | 'CODE_REVIEW'
  | 'DEPLOYMENT_PROOF'
  | 'DOCUMENTATION'
  | 'COMPLIANCE'

export interface EvidenceUploadRequest {
  gate_id: string
  evidence_type: EvidenceType
  description?: string
}

export interface EvidenceResponse {
  id: string
  gate_id: string
  file_name: string
  file_size: number
  file_size_mb: number
  file_type: string
  evidence_type: string
  sha256_hash: string
  description: string | null
  uploaded_by: string
  uploaded_by_name: string
  uploaded_at: string
  s3_url: string
  download_url: string
  integrity_status: 'valid' | 'failed' | 'pending'
  last_integrity_check: string | null
}

export interface EvidenceListResponse {
  items: EvidenceResponse[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface IntegrityCheckResponse {
  evidence_id: string
  file_name: string
  is_valid: boolean
  original_hash: string
  current_hash: string
  checked_at: string
  checked_by: string
  error_message: string | null
}

// =========================================================================
// POLICY TYPES
// =========================================================================

export type PolicySeverity = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

export interface PolicyResponse {
  id: string
  policy_name: string
  policy_code: string
  stage: string
  description: string
  rego_code: string
  severity: PolicySeverity
  is_active: boolean
  version: string
  created_at: string
  updated_at: string
}

export interface PolicyListResponse {
  items: PolicyResponse[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface PolicyEvaluationRequest {
  gate_id: string
  policy_id: string
  input_data: Record<string, unknown>
}

export interface PolicyEvaluationResponse {
  id: string
  gate_id: string
  policy_id: string
  policy_name: string
  result: 'pass' | 'fail'
  violations: string[]
  evaluated_at: string
  evaluated_by: string
}

export interface PolicyEvaluationListResponse {
  items: PolicyEvaluationResponse[]
  total: number
  passed: number
  failed: number
  pass_rate: number
}

// =========================================================================
// DASHBOARD TYPES
// =========================================================================

export interface DashboardStats {
  total_projects: number
  total_gates: number
  approved_gates: number
  pending_gates: number
  rejected_gates: number
  total_evidence: number
  total_policies: number
  pass_rate: number
}

export interface RecentGate {
  id: string
  gate_name: string
  project_name: string
  status: GateStatusEnum
  stage: string
  updated_at: string
}

// =========================================================================
// COMMON TYPES
// =========================================================================

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface ApiError {
  detail: string
  status_code?: number
}

/**
 * SDLC 5.1.1 Stage Definitions (10 Stages: 00-09 + Archive folder)
 * Reference: SDLC-Enterprise-Framework/README.md (v5.1.1)
 * Note: 10-archive is a project-level archive folder, not a formal stage
 */
export const SDLC_STAGES = [
  { code: '00', name: 'FOUNDATION', description: 'Strategic Discovery & Validation', question: 'WHY?' },
  { code: '01', name: 'PLANNING', description: 'Requirements & User Stories', question: 'WHAT?' },
  { code: '02', name: 'DESIGN', description: 'Architecture & Technical Design', question: 'HOW?' },
  { code: '03', name: 'INTEGRATE', description: 'API Contracts & Third-party Setup', question: 'How connect?' },
  { code: '04', name: 'BUILD', description: 'Development & Implementation', question: 'Building right?' },
  { code: '05', name: 'TEST', description: 'Quality Assurance & Validation', question: 'Works correctly?' },
  { code: '06', name: 'DEPLOY', description: 'Release & Deployment', question: 'Ship safely?' },
  { code: '07', name: 'OPERATE', description: 'Production Operations & Monitoring', question: 'Running reliably?' },
  { code: '08', name: 'COLLABORATE', description: 'Team Coordination & Knowledge', question: 'Team effective?' },
  { code: '09', name: 'GOVERN', description: 'Compliance & Strategic Oversight', question: 'Compliant?' },
  { code: '10', name: 'ARCHIVE', description: 'Project Archive (Legacy Docs)', question: 'Archived?' },
] as const

export type SDLCStageCode = typeof SDLC_STAGES[number]['code']
export type SDLCStageName = typeof SDLC_STAGES[number]['name']

// =========================================================================
// GITHUB INTEGRATION TYPES
// =========================================================================

// GitHub OAuth Types
export interface GitHubOAuthURLResponse {
  authorization_url: string
  state: string
}

export interface GitHubOAuthCallbackRequest {
  code: string
  state: string
}

export interface GitHubOAuthCallbackResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  github_connected: boolean
  user_id: string
  email: string
  name: string | null
  avatar_url: string | null
}

export interface GitHubConnectionStatus {
  connected: boolean
  github_username: string | null
  github_avatar: string | null
  scopes: string[]
  connected_at: string | null
  rate_limit: GitHubRateLimitInfo | null
}

export interface GitHubRateLimitInfo {
  limit: number
  remaining: number
  reset: string
  used: number
}

// GitHub Repository Types
export interface GitHubRepositoryOwner {
  login: string
  id: number
  avatar_url: string | null
  type: 'User' | 'Organization'
}

export interface GitHubRepository {
  id: number
  name: string
  full_name: string
  description: string | null
  html_url: string
  clone_url: string | null
  default_branch: string
  language: string | null
  private: boolean
  fork: boolean
  stargazers_count: number
  forks_count: number
  open_issues_count: number
  owner: GitHubRepositoryOwner
  created_at: string | null
  updated_at: string | null
  pushed_at: string | null
}

export interface GitHubRepositoryListResponse {
  repositories: GitHubRepository[]
  total: number
  page: number
  per_page: number
}

export interface GitHubRepositoryContents {
  name: string
  path: string
  type: 'file' | 'dir'
  size: number
  sha: string
  download_url: string | null
}

export interface GitHubRepositoryLanguages {
  languages: Record<string, number>
  primary_language: string | null
}

/**
 * Stage mapping item for SDLC 5.1.2
 * Only /docs folders are stage-mapped
 */
export interface StageMappingItem {
  folder_path: string
  stage_code: SDLCStageCode
  stage_name: SDLCStageName | null
  is_auto_detected: boolean
  confidence: number | null
}

/**
 * Structure validation result (SDLC 5.1.2)
 * Code folders are validated for presence, NOT stage-mapped
 */
export interface StructureValidationResult {
  code_folders: Record<string, {
    found: boolean
    required_for: string
    description?: string
  }>
  required_files: Record<string, {
    found: boolean
    required_for: string
    description?: string
  }>
  compliance_score: null  // Per CTO: null for now, use breakdown
  breakdown: {
    found: number
    missing: number
    total: number
  }
}

/**
 * GitHub repository analysis result (SDLC 5.1.2)
 * Separates stage_mappings from structure_validation
 */
export interface GitHubAnalysisResult {
  repository: GitHubRepository
  languages: Record<string, number>
  primary_language: string | null
  project_type: string
  team_size_estimate: number
  recommendations: {
    policy_pack: 'lite' | 'standard' | 'professional' | 'enterprise'
    policy_pack_reason: string
    initial_gates: string[]
    tier: 'LITE' | 'STANDARD' | 'PROFESSIONAL' | 'ENTERPRISE'
  }
  // SDLC 5.1.2: Only /docs folders (backward compatible)
  stage_mappings: StageMappingItem[]
  // SDLC 5.1.2: Code folder validation (NEW)
  structure_validation: StructureValidationResult
}

/**
 * Request to save stage mappings
 */
export interface SaveStageMappingsRequest {
  project_id: string
  stage_mappings: StageMappingItem[]
}

/**
 * Response after saving stage mappings
 */
export interface SaveStageMappingsResponse {
  project_id: string
  mappings_saved: number
  mappings: StageMappingItem[]
}

// GitHub Sync Types
export interface GitHubSyncRequest {
  github_repo_id: number
  github_repo_full_name: string
  project_name?: string
  auto_setup?: boolean
}

export interface GitHubSyncResponse {
  project_id: string
  project_name: string
  project_slug: string
  github_repo_id: number
  github_repo_full_name: string
  sync_status: 'synced' | 'syncing' | 'error'
  synced_at: string
}

// GitHub Webhook Types
export interface GitHubWebhookEvent {
  event_type: string
  repository: Record<string, unknown>
  sender: Record<string, unknown>
  action: string | null
  timestamp: string
  data: Record<string, unknown>
}

export interface GitHubWebhookResponse {
  received: boolean
  event_type: string
  repository: string
  message: string
}
