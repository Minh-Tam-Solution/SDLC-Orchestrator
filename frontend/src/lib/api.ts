/**
 * API Client - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/lib/api
 * @description API client for backend communication
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 58 - Registration + VNPay
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * API error response type
 */
interface APIError {
  detail: string;
  status: number;
}

/**
 * Generic API request function
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: "include", // Include cookies for auth
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "An unexpected error occurred",
    }));

    const error: APIError = {
      detail: errorData.detail || "Request failed",
      status: response.status,
    };

    throw error;
  }

  return response.json();
}

// =============================================================================
// Authentication API
// =============================================================================

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  name: string | null;
  is_active: boolean;
  created_at: string;
  message: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_superuser: boolean;
  roles: string[];
  oauth_providers: string[];
  created_at: string;
  last_login_at: string | null;
}

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Login with email and password
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get current user profile
 * Uses httpOnly cookie for authentication (Sprint 63)
 */
export async function getCurrentUser(): Promise<UserProfile> {
  return apiRequest<UserProfile>("/auth/me");
}

/**
 * Refresh access token
 * Reads refresh_token from httpOnly cookie (Sprint 63)
 */
export async function refreshToken(): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/refresh", {
    method: "POST",
  });
}

/**
 * Logout (revoke refresh token and clear cookies)
 * Backend clears httpOnly cookies via Set-Cookie (Sprint 63)
 */
export async function logout(): Promise<void> {
  await apiRequest("/auth/logout", {
    method: "POST",
  });
}

// =============================================================================
// Subscription API (Sprint 58)
// =============================================================================

export interface Subscription {
  id: string;
  user_id: string;
  plan: "free" | "founder" | "standard" | "enterprise";
  status: "active" | "canceled" | "past_due";
  current_period_start: string;
  current_period_end: string;
  vnpay_subscription_id: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Get current user subscription
 */
export async function getSubscription(accessToken: string): Promise<Subscription | null> {
  try {
    return await apiRequest<Subscription>("/payments/subscriptions/me", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  } catch (error) {
    // Return null if no subscription found (404)
    if ((error as APIError).status === 404) {
      return null;
    }
    throw error;
  }
}

// =============================================================================
// VNPay API (Sprint 58)
// =============================================================================

export interface VNPayCreateRequest {
  plan: "founder" | "standard";
  billing_period?: "monthly" | "annual";
}

export interface VNPayCreateResponse {
  payment_url: string;
  vnp_txn_ref: string;
}

/**
 * Create VNPay payment URL
 */
export async function createVNPayPayment(
  accessToken: string,
  data: VNPayCreateRequest
): Promise<VNPayCreateResponse> {
  return apiRequest<VNPayCreateResponse>("/payments/vnpay/create", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  });
}

export interface PaymentStatus {
  vnp_txn_ref: string;
  status: "pending" | "completed" | "failed";
  amount: number;
  currency: string;
  plan: string;
  processed_at: string | null;
}

/**
 * Get payment status by transaction reference
 */
export async function getPaymentStatus(
  accessToken: string,
  vnpTxnRef: string
): Promise<PaymentStatus> {
  return apiRequest<PaymentStatus>(`/payments/${vnpTxnRef}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

// =============================================================================
// OAuth API (Sprint 59)
// =============================================================================

export interface OAuthAuthorizeResponse {
  authorization_url: string;
  state: string;
}

export interface OAuthCallbackRequest {
  code: string;
  state: string;
  code_verifier?: string; // For Google PKCE flow
}

/**
 * Get OAuth authorization URL
 */
export async function getOAuthAuthorizeUrl(
  provider: "github" | "google"
): Promise<OAuthAuthorizeResponse> {
  return apiRequest<OAuthAuthorizeResponse>(`/auth/oauth/${provider}/authorize`);
}

/**
 * Exchange OAuth code for tokens
 */
export async function exchangeOAuthCode(
  provider: "github" | "google",
  data: OAuthCallbackRequest
): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(`/auth/oauth/${provider}/callback`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// =============================================================================
// Password Reset API (Sprint 60)
// =============================================================================

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
  email: string;
}

export interface VerifyResetTokenResponse {
  valid: boolean;
  email: string | null;
  expires_at: string | null;
  error: string | null;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ResetPasswordResponse {
  message: string;
  email: string;
}

/**
 * Request password reset email
 */
export async function forgotPassword(data: ForgotPasswordRequest): Promise<ForgotPasswordResponse> {
  return apiRequest<ForgotPasswordResponse>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Verify password reset token
 */
export async function verifyResetToken(token: string): Promise<VerifyResetTokenResponse> {
  return apiRequest<VerifyResetTokenResponse>(`/auth/verify-reset-token?token=${encodeURIComponent(token)}`);
}

/**
 * Reset password with token
 */
export async function resetPassword(data: ResetPasswordRequest): Promise<ResetPasswordResponse> {
  return apiRequest<ResetPasswordResponse>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Export API error type for error handling
export type { APIError };

// =============================================================================
// Projects API (Sprint 62 - Dashboard Migration)
// =============================================================================

export interface Project {
  id: string;
  name: string;
  description: string;
  current_stage: string;
  gate_status: "passed" | "failed" | "pending" | "not_started";
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  slug: string;
  owner_id: string;
  is_active: boolean;
  gates: GateBasic[];
}

export interface GateBasic {
  id: string;
  gate_name: string;
  gate_type: string;
  stage: string;
  status: string;
  description: string;
  created_at: string;
}

/**
 * List all projects (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getProjects(
  options?: { skip?: number; limit?: number }
): Promise<Project[]> {
  const params = new URLSearchParams();
  if (options?.skip) params.set("skip", options.skip.toString());
  if (options?.limit) params.set("limit", options.limit.toString());

  const queryString = params.toString();
  const url = `/projects${queryString ? `?${queryString}` : ""}`;

  return apiRequest<Project[]>(url);
}

/**
 * Get project by ID (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getProject(projectId: string): Promise<ProjectDetail> {
  return apiRequest<ProjectDetail>(`/projects/${projectId}`);
}

/**
 * Create new project request
 */
export interface CreateProjectRequest {
  name: string;
  description?: string;
  policy_pack_tier?: "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";
}

/**
 * Create new project response
 */
export interface CreateProjectResponse {
  id: string;
  name: string;
  slug: string;
  description: string;
  policy_pack_tier: string;
  created_at: string;
}

/**
 * Create a new project (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function createProject(
  data: CreateProjectRequest
): Promise<CreateProjectResponse> {
  return apiRequest<CreateProjectResponse>(`/projects`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// =============================================================================
// Gates API (Sprint 62 - Dashboard Migration)
// =============================================================================

export interface Gate {
  id: string;
  project_id: string;
  gate_name: string;
  gate_type: string;
  stage: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED";
  description: string;
  exit_criteria: ExitCriterion[];
  created_by: string;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  approvals: GateApproval[];
  evidence_count: number;
  policy_violations: PolicyViolation[];
}

export interface ExitCriterion {
  criterion: string;
  status: "pending" | "met" | "not_met";
}

export interface GateApproval {
  id: string;
  approved_by: string;
  approved_by_name?: string;
  approved_by_role?: string;
  is_approved: boolean;
  comments: string;
  approved_at: string;
}

export interface PolicyViolation {
  policy_id: string;
  policy_code?: string;
  message: string;
  evaluated_at: string;
}

export interface GateListResponse {
  items: Gate[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface GateListOptions {
  project_id?: string;
  stage?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

/**
 * List gates with pagination and filters (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getGates(
  options?: GateListOptions
): Promise<GateListResponse> {
  const params = new URLSearchParams();
  if (options?.project_id) params.set("project_id", options.project_id);
  if (options?.stage) params.set("stage", options.stage);
  if (options?.status) params.set("status", options.status);
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  const queryString = params.toString();
  const url = `/gates${queryString ? `?${queryString}` : ""}`;

  return apiRequest<GateListResponse>(url);
}

/**
 * Get gate by ID (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getGate(gateId: string): Promise<Gate> {
  return apiRequest<Gate>(`/gates/${gateId}`);
}

export interface GateSubmitRequest {
  message?: string;
}

export interface GateApprovalRequest {
  approved: boolean;
  comments?: string;
}

/**
 * Submit gate for approval (authenticated via httpOnly cookie)
 * Sprint 69: Gate workflow - submit DRAFT → PENDING_APPROVAL
 */
export async function submitGate(
  gateId: string,
  data?: GateSubmitRequest
): Promise<Gate> {
  return apiRequest<Gate>(`/gates/${gateId}/submit`, {
    method: "POST",
    body: JSON.stringify(data || {}),
  });
}

/**
 * Approve or reject gate (CTO/CPO/CEO only, authenticated via httpOnly cookie)
 * Sprint 69: Gate workflow - approve/reject PENDING_APPROVAL → APPROVED/REJECTED
 */
export async function approveGate(
  gateId: string,
  data: GateApprovalRequest
): Promise<Gate> {
  return apiRequest<Gate>(`/gates/${gateId}/approve`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get gate approval history (authenticated via httpOnly cookie)
 * Sprint 69: Audit trail for gate approvals
 */
export async function getGateApprovals(gateId: string): Promise<GateApproval[]> {
  return apiRequest<GateApproval[]>(`/gates/${gateId}/approvals`);
}

// =============================================================================
// Evidence API (Sprint 62 - Dashboard Migration)
// =============================================================================

export interface Evidence {
  id: string;
  gate_id: string;
  file_name: string;
  file_size: number;
  file_size_mb: number;
  file_type: string;
  evidence_type: "DESIGN_DOCUMENT" | "TEST_RESULTS" | "CODE_REVIEW" | "DEPLOYMENT_PROOF" | "DOCUMENTATION" | "COMPLIANCE";
  sha256_hash: string;
  description: string | null;
  uploaded_by: string;
  uploaded_by_name: string;
  uploaded_at: string;
  s3_url: string;
  download_url: string;
  integrity_status: "valid" | "failed" | "pending";
  last_integrity_check: string | null;
}

export interface EvidenceListResponse {
  items: Evidence[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface EvidenceListOptions {
  gate_id?: string;
  evidence_type?: string;
  page?: number;
  page_size?: number;
}

/**
 * List evidence with pagination and filters (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getEvidenceList(
  options?: EvidenceListOptions
): Promise<EvidenceListResponse> {
  const params = new URLSearchParams();
  if (options?.gate_id) params.set("gate_id", options.gate_id);
  if (options?.evidence_type) params.set("evidence_type", options.evidence_type);
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  const queryString = params.toString();
  const url = `/evidence${queryString ? `?${queryString}` : ""}`;

  return apiRequest<EvidenceListResponse>(url);
}

/**
 * Get evidence by ID (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getEvidence(evidenceId: string): Promise<Evidence> {
  return apiRequest<Evidence>(`/evidence/${evidenceId}`);
}

export interface EvidenceUploadRequest {
  gate_id: string;
  evidence_type: string;
  description?: string;
}

export interface EvidenceDownloadResponse {
  presigned_url: string;
  file_name: string;
  expires_in: number;
}

export interface IntegrityCheckRequest {
  force?: boolean;
}

export interface IntegrityCheckResponse {
  evidence_id: string;
  file_name: string;
  is_valid: boolean;
  original_hash: string;
  current_hash: string;
  checked_at: string;
  checked_by: string;
  error_message: string | null;
}

/**
 * Upload evidence file (multipart/form-data, authenticated via httpOnly cookie)
 * Sprint 69: File upload to MinIO S3-compatible storage
 */
export async function uploadEvidence(
  data: EvidenceUploadRequest,
  file: File
): Promise<Evidence> {
  const formData = new FormData();
  formData.append("gate_id", data.gate_id);
  formData.append("evidence_type", data.evidence_type);
  if (data.description) {
    formData.append("description", data.description);
  }
  formData.append("file", file);

  const url = `${API_BASE_URL}/evidence/upload`;
  const response = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "Upload failed",
    }));
    throw { detail: errorData.detail || "Upload failed", status: response.status };
  }

  return response.json();
}

/**
 * Get pre-signed download URL for evidence file (authenticated via httpOnly cookie)
 * Sprint 69: Pre-signed URL valid for 15 minutes
 */
export async function downloadEvidence(evidenceId: string): Promise<EvidenceDownloadResponse> {
  return apiRequest<EvidenceDownloadResponse>(`/evidence/${evidenceId}/download`);
}

/**
 * Run integrity check on evidence file (authenticated via httpOnly cookie)
 * Sprint 69: SHA256 verification against stored hash
 */
export async function checkEvidenceIntegrity(
  evidenceId: string,
  data?: IntegrityCheckRequest
): Promise<IntegrityCheckResponse> {
  return apiRequest<IntegrityCheckResponse>(`/evidence/${evidenceId}/integrity-check`, {
    method: "POST",
    body: JSON.stringify(data || {}),
  });
}

// =============================================================================
// Policies API
// =============================================================================

export type PolicySeverity = "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface Policy {
  id: string;
  policy_name: string;
  policy_code: string;
  description: string;
  stage: string;
  severity: PolicySeverity;
  version: string;
  is_active: boolean;
  rego_code: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyListResponse {
  items: Policy[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PolicyListOptions {
  stage?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

/**
 * List policies with pagination and filters (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getPolicies(
  options?: PolicyListOptions
): Promise<PolicyListResponse> {
  const params = new URLSearchParams();
  if (options?.stage) params.set("stage", options.stage);
  if (options?.is_active !== undefined) params.set("is_active", String(options.is_active));
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  const queryString = params.toString();
  const url = queryString ? `/policies?${queryString}` : "/policies";

  return apiRequest<PolicyListResponse>(url);
}

/**
 * Get policy by ID (authenticated via httpOnly cookie)
 * Sprint 69: Removed accessToken param - uses credentials: "include" for cookie auth
 */
export async function getPolicy(policyId: string): Promise<Policy> {
  return apiRequest<Policy>(`/policies/${policyId}`);
}

export interface PolicyUpdateRequest {
  policy_name?: string;
  description?: string;
  rego_code?: string;
  severity?: PolicySeverity;
  is_active?: boolean;
  version?: string;
}

export interface PolicyEvaluationRequest {
  gate_id: string;
  policy_id: string;
  input_data?: Record<string, unknown>;
}

export interface PolicyEvaluationResult {
  id: string;
  gate_id: string;
  policy_id: string;
  policy_name: string;
  result: "pass" | "fail";
  violations: string[];
  evaluated_at: string;
  evaluated_by: string;
}

export interface PolicyEvaluationListResponse {
  items: PolicyEvaluationResult[];
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
}

/**
 * Update policy (authenticated via httpOnly cookie)
 * Sprint 69: Policy management with version tracking
 */
export async function updatePolicy(
  policyId: string,
  data: PolicyUpdateRequest
): Promise<Policy> {
  return apiRequest<Policy>(`/policies/${policyId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Evaluate policy against a gate (authenticated via httpOnly cookie)
 * Sprint 69: Real OPA policy evaluation
 */
export async function evaluatePolicy(
  data: PolicyEvaluationRequest
): Promise<PolicyEvaluationResult> {
  return apiRequest<PolicyEvaluationResult>("/policies/evaluate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get policy evaluations for a gate (authenticated via httpOnly cookie)
 * Sprint 69: Audit trail for policy compliance
 */
export async function getGateEvaluations(gateId: string): Promise<PolicyEvaluationListResponse> {
  return apiRequest<PolicyEvaluationListResponse>(`/policies/evaluations/${gateId}`);
}

// =============================================================================
// Codegen API (Sprint 69 - Zero Mock Policy)
// =============================================================================

export interface CodegenTemplate {
  id: string;
  name: string;
  description: string;
  language: string;
  framework: string;
}

export interface CodegenSession {
  id: string;
  name: string;
  project: string;
  template: string;
  status: "pending" | "validating" | "completed" | "failed";
  quality_score: number | null;
  provider: string;
  gates_passed: number;
  gates_total: number;
  created_at: string;
  duration: string;
}

export interface CodegenSessionListResponse {
  sessions: CodegenSession[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateCodegenRequest {
  name: string;
  template_id: string;
  specification?: string;
  project_id?: string;
}

export interface CreateCodegenResponse {
  session_id: string;
  status: string;
  message: string;
}

export interface CodegenListOptions {
  page?: number;
  page_size?: number;
  status_filter?: string;
}

/**
 * List codegen templates (authenticated via httpOnly cookie)
 * Sprint 69: Zero Mock Policy - Real API for templates
 */
export async function getCodegenTemplates(): Promise<CodegenTemplate[]> {
  return apiRequest<CodegenTemplate[]>("/codegen/templates");
}

/**
 * List codegen sessions with pagination (authenticated via httpOnly cookie)
 * Sprint 69: Zero Mock Policy - Real API for session history
 */
export async function getCodegenSessions(
  options?: CodegenListOptions
): Promise<CodegenSessionListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());
  if (options?.status_filter) params.set("status_filter", options.status_filter);

  const queryString = params.toString();
  const url = queryString ? `/codegen/sessions?${queryString}` : "/codegen/sessions";

  return apiRequest<CodegenSessionListResponse>(url);
}

/**
 * Create a new codegen session (authenticated via httpOnly cookie)
 * Sprint 69: Zero Mock Policy - Real API for code generation
 */
export async function createCodegenSession(
  request: CreateCodegenRequest
): Promise<CreateCodegenResponse> {
  return apiRequest<CreateCodegenResponse>("/codegen/generate/full", {
    method: "POST",
    body: JSON.stringify({
      app_blueprint: {
        name: request.name,
        description: request.specification || "",
        modules: [],
      },
      template_id: request.template_id,
      project_id: request.project_id,
    }),
  });
}

// =============================================================================
// Notifications API (Sprint 69 - CTO Go-Live Requirements)
// =============================================================================

export interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  priority: string;
  project_id: string | null;
  is_read: boolean;
  created_at: string;
  metadata: Record<string, unknown> | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

export interface NotificationSettings {
  email_enabled: boolean;
  slack_enabled: boolean;
  slack_webhook_url: string | null;
  teams_enabled: boolean;
  teams_webhook_url: string | null;
  notification_types: Record<string, boolean>;
}

export interface NotificationListOptions {
  page?: number;
  page_size?: number;
  unread_only?: boolean;
  notification_type?: string;
  project_id?: string;
}

export async function getNotifications(
  options?: NotificationListOptions
): Promise<NotificationListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());
  if (options?.unread_only) params.set("unread_only", "true");
  if (options?.notification_type) params.set("notification_type", options.notification_type);
  if (options?.project_id) params.set("project_id", options.project_id);

  const queryString = params.toString();
  const url = queryString ? `/notifications?${queryString}` : "/notifications";
  return apiRequest<NotificationListResponse>(url);
}

export async function markNotificationRead(notificationId: string): Promise<{ success: boolean }> {
  return apiRequest<{ success: boolean }>(`/notifications/${notificationId}/read`, {
    method: "PUT",
  });
}

export async function markAllNotificationsRead(): Promise<{ success: boolean; updated_count: number }> {
  return apiRequest<{ success: boolean; updated_count: number }>("/notifications/read-all", {
    method: "PUT",
  });
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
  return apiRequest<NotificationSettings>("/notifications/settings");
}

export async function updateNotificationSettings(
  settings: Partial<NotificationSettings>
): Promise<NotificationSettings> {
  return apiRequest<NotificationSettings>("/notifications/settings", {
    method: "PUT",
    body: JSON.stringify(settings),
  });
}

// =============================================================================
// Compliance API (Sprint 69 - CTO Go-Live Requirements)
// =============================================================================

export interface ComplianceScan {
  id: string;
  project_id: string;
  scan_type: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  findings_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  created_at: string;
}

export interface ComplianceFinding {
  id: string;
  scan_id: string;
  rule_id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  file_path: string | null;
  line_number: number | null;
  remediation: string | null;
  status: "open" | "resolved" | "ignored";
}

export interface ComplianceScanListResponse {
  scans: ComplianceScan[];
  total: number;
  page: number;
  page_size: number;
}

export async function getComplianceScans(
  projectId: string,
  options?: { page?: number; page_size?: number }
): Promise<ComplianceScanListResponse> {
  const params = new URLSearchParams();
  params.set("project_id", projectId);
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  return apiRequest<ComplianceScanListResponse>(`/compliance/scans?${params.toString()}`);
}

export async function triggerComplianceScan(
  projectId: string,
  scanType: string = "full"
): Promise<ComplianceScan> {
  return apiRequest<ComplianceScan>("/compliance/scans", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, scan_type: scanType }),
  });
}

export async function getComplianceFindings(
  scanId: string
): Promise<{ findings: ComplianceFinding[]; total: number }> {
  return apiRequest<{ findings: ComplianceFinding[]; total: number }>(
    `/compliance/scans/${scanId}/findings`
  );
}

// =============================================================================
// GitHub API (Sprint 69 - CTO Go-Live Requirements)
// =============================================================================

export interface GitHubRepository {
  id: number;
  full_name: string;
  name: string;
  description: string | null;
  private: boolean;
  html_url: string;
  default_branch: string;
  language: string | null;
  updated_at: string;
}

export interface GitHubPullRequest {
  id: number;
  number: number;
  title: string;
  state: "open" | "closed" | "merged";
  user: { login: string; avatar_url: string };
  created_at: string;
  updated_at: string;
  html_url: string;
  head: { ref: string };
  base: { ref: string };
}

export interface GitHubConnectionStatus {
  connected: boolean;
  username: string | null;
  avatar_url: string | null;
  scopes: string[];
  expires_at: string | null;
}

export async function getGitHubConnectionStatus(): Promise<GitHubConnectionStatus> {
  return apiRequest<GitHubConnectionStatus>("/github/status");
}

export async function getGitHubRepositories(): Promise<GitHubRepository[]> {
  return apiRequest<GitHubRepository[]>("/github/repos");
}

export async function getGitHubPullRequests(
  owner: string,
  repo: string,
  options?: { state?: "open" | "closed" | "all" }
): Promise<GitHubPullRequest[]> {
  const params = new URLSearchParams();
  if (options?.state) params.set("state", options.state);

  const queryString = params.toString();
  const url = queryString
    ? `/github/repos/${owner}/${repo}/pulls?${queryString}`
    : `/github/repos/${owner}/${repo}/pulls`;
  return apiRequest<GitHubPullRequest[]>(url);
}

export async function disconnectGitHub(): Promise<{ success: boolean }> {
  return apiRequest<{ success: boolean }>("/github/disconnect", {
    method: "POST",
  });
}

// =============================================================================
// AI Council API (Sprint 69 - CTO Go-Live Requirements)
// =============================================================================

export interface CouncilSession {
  id: string;
  project_id: string;
  topic: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  participants: string[];
  created_at: string;
  completed_at: string | null;
  summary: string | null;
}

export interface CouncilMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  participant: string | null;
  content: string;
  created_at: string;
}

export interface CouncilSessionListResponse {
  sessions: CouncilSession[];
  total: number;
  page: number;
  page_size: number;
}

export async function getCouncilSessions(
  projectId: string,
  options?: { page?: number; page_size?: number }
): Promise<CouncilSessionListResponse> {
  const params = new URLSearchParams();
  params.set("project_id", projectId);
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  return apiRequest<CouncilSessionListResponse>(`/council/sessions?${params.toString()}`);
}

export async function createCouncilSession(
  projectId: string,
  topic: string
): Promise<CouncilSession> {
  return apiRequest<CouncilSession>("/council/sessions", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, topic }),
  });
}

export async function getCouncilMessages(sessionId: string): Promise<CouncilMessage[]> {
  return apiRequest<CouncilMessage[]>(`/council/sessions/${sessionId}/messages`);
}

export async function sendCouncilMessage(
  sessionId: string,
  content: string
): Promise<CouncilMessage> {
  return apiRequest<CouncilMessage>(`/council/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

// =============================================================================
// SAST API (Sprint 69 - CTO Go-Live Requirements)
// =============================================================================

export interface SASTScan {
  id: string;
  project_id: string;
  status: "pending" | "running" | "completed" | "failed";
  engine: string;
  started_at: string | null;
  completed_at: string | null;
  findings_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  duration_ms: number | null;
  created_at: string;
}

export interface SASTFinding {
  id: string;
  scan_id: string;
  rule_id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  file_path: string;
  start_line: number;
  end_line: number;
  code_snippet: string | null;
  remediation: string | null;
  cwe_id: string | null;
  owasp_category: string | null;
}

export interface SASTScanListResponse {
  scans: SASTScan[];
  total: number;
  page: number;
  page_size: number;
}

export async function getSASTScans(
  projectId: string,
  options?: { page?: number; page_size?: number }
): Promise<SASTScanListResponse> {
  const params = new URLSearchParams();
  params.set("project_id", projectId);
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  return apiRequest<SASTScanListResponse>(`/sast/scans?${params.toString()}`);
}

export async function triggerSASTScan(projectId: string): Promise<SASTScan> {
  return apiRequest<SASTScan>("/sast/scans", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export async function getSASTFindings(
  scanId: string
): Promise<{ findings: SASTFinding[]; total: number }> {
  return apiRequest<{ findings: SASTFinding[]; total: number }>(
    `/sast/scans/${scanId}/findings`
  );
}

export async function getSASTScanDetails(scanId: string): Promise<SASTScan> {
  return apiRequest<SASTScan>(`/sast/scans/${scanId}`);
}

// =============================================================================
// Teams API (Sprint 84 - Teams & Organizations UI)
// =============================================================================

import type {
  Team,
  TeamCreate,
  TeamUpdate,
  TeamListResponse,
  TeamListParams,
  TeamStatistics,
  TeamMember,
  TeamMemberListResponse,
  TeamMemberListParams,
  TeamMemberAdd,
  TeamMemberRoleUpdate,
} from "./types/team";

import type {
  Organization,
  OrganizationCreate,
  OrganizationUpdate,
  OrganizationListResponse,
  OrganizationListParams,
  OrganizationStatistics,
} from "./types/organization";

// Re-export types for convenience
export type {
  Team,
  TeamCreate,
  TeamUpdate,
  TeamListResponse,
  TeamListParams,
  TeamStatistics,
  TeamMember,
  TeamMemberListResponse,
  TeamMemberListParams,
  TeamMemberAdd,
  TeamMemberRoleUpdate,
  Organization,
  OrganizationCreate,
  OrganizationUpdate,
  OrganizationListResponse,
  OrganizationListParams,
  OrganizationStatistics,
};

/**
 * Create a new team (authenticated via httpOnly cookie)
 * Sprint 84: POST /teams - Creator becomes owner (SE4H Coach)
 */
export async function createTeam(data: TeamCreate): Promise<Team> {
  return apiRequest<Team>("/teams", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List teams user is member of (authenticated via httpOnly cookie)
 * Sprint 84: GET /teams - Paginated list
 */
export async function getTeams(options?: TeamListParams): Promise<TeamListResponse> {
  const params = new URLSearchParams();
  if (options?.skip !== undefined) params.set("skip", options.skip.toString());
  if (options?.limit !== undefined) params.set("limit", options.limit.toString());
  if (options?.organization_id) params.set("organization_id", options.organization_id);

  const queryString = params.toString();
  const url = queryString ? `/teams?${queryString}` : "/teams";

  return apiRequest<TeamListResponse>(url);
}

/**
 * Get team by ID (authenticated via httpOnly cookie)
 * Sprint 84: GET /teams/{team_id}
 */
export async function getTeam(teamId: string): Promise<Team> {
  return apiRequest<Team>(`/teams/${teamId}`);
}

/**
 * Update team (authenticated via httpOnly cookie)
 * Sprint 84: PATCH /teams/{team_id} - Admin/Owner only
 */
export async function updateTeam(teamId: string, data: TeamUpdate): Promise<Team> {
  return apiRequest<Team>(`/teams/${teamId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete team (authenticated via httpOnly cookie)
 * Sprint 84: DELETE /teams/{team_id} - Soft delete, Owner only
 */
export async function deleteTeam(teamId: string): Promise<void> {
  await apiRequest(`/teams/${teamId}`, {
    method: "DELETE",
  });
}

/**
 * Get team statistics (authenticated via httpOnly cookie)
 * Sprint 84: GET /teams/{team_id}/stats
 */
export async function getTeamStats(teamId: string): Promise<TeamStatistics> {
  return apiRequest<TeamStatistics>(`/teams/${teamId}/stats`);
}

/**
 * Add member to team (authenticated via httpOnly cookie)
 * Sprint 84: POST /teams/{team_id}/members - Admin/Owner only
 */
export async function addTeamMember(teamId: string, data: TeamMemberAdd): Promise<TeamMember> {
  return apiRequest<TeamMember>(`/teams/${teamId}/members`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List team members (authenticated via httpOnly cookie)
 * Sprint 84: GET /teams/{team_id}/members - Paginated list
 */
export async function getTeamMembers(
  teamId: string,
  options?: TeamMemberListParams
): Promise<TeamMemberListResponse> {
  const params = new URLSearchParams();
  if (options?.skip !== undefined) params.set("skip", options.skip.toString());
  if (options?.limit !== undefined) params.set("limit", options.limit.toString());

  const queryString = params.toString();
  const url = queryString ? `/teams/${teamId}/members?${queryString}` : `/teams/${teamId}/members`;

  return apiRequest<TeamMemberListResponse>(url);
}

/**
 * Update member role (authenticated via httpOnly cookie)
 * Sprint 84: PATCH /teams/{team_id}/members/{user_id} - Owner only
 */
export async function updateTeamMemberRole(
  teamId: string,
  userId: string,
  data: TeamMemberRoleUpdate
): Promise<TeamMember> {
  return apiRequest<TeamMember>(`/teams/${teamId}/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Remove member from team (authenticated via httpOnly cookie)
 * Sprint 84: DELETE /teams/{team_id}/members/{user_id} - Admin/Owner only
 */
export async function removeTeamMember(teamId: string, userId: string): Promise<void> {
  await apiRequest(`/teams/${teamId}/members/${userId}`, {
    method: "DELETE",
  });
}

// =============================================================================
// Organizations API (Sprint 84 - Teams & Organizations UI)
// =============================================================================

/**
 * Create a new organization (authenticated via httpOnly cookie)
 * Sprint 84: POST /organizations
 */
export async function createOrganization(data: OrganizationCreate): Promise<Organization> {
  return apiRequest<Organization>("/organizations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List organizations user has access to (authenticated via httpOnly cookie)
 * Sprint 84: GET /organizations - Paginated list
 */
export async function getOrganizations(
  options?: OrganizationListParams
): Promise<OrganizationListResponse> {
  const params = new URLSearchParams();
  if (options?.skip !== undefined) params.set("skip", options.skip.toString());
  if (options?.limit !== undefined) params.set("limit", options.limit.toString());

  const queryString = params.toString();
  const url = queryString ? `/organizations?${queryString}` : "/organizations";

  return apiRequest<OrganizationListResponse>(url);
}

/**
 * Get organization by ID (authenticated via httpOnly cookie)
 * Sprint 84: GET /organizations/{org_id}
 */
export async function getOrganization(orgId: string): Promise<Organization> {
  return apiRequest<Organization>(`/organizations/${orgId}`);
}

/**
 * Update organization (authenticated via httpOnly cookie)
 * Sprint 84: PATCH /organizations/{org_id} - Member required
 */
export async function updateOrganization(
  orgId: string,
  data: OrganizationUpdate
): Promise<Organization> {
  return apiRequest<Organization>(`/organizations/${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Get organization statistics (authenticated via httpOnly cookie)
 * Sprint 84: GET /organizations/{org_id}/stats
 */
export async function getOrganizationStats(orgId: string): Promise<OrganizationStatistics> {
  return apiRequest<OrganizationStatistics>(`/organizations/${orgId}/stats`);
}

// =============================================================================
// AGENTS.md API (Sprint 85 - TRUE MOAT)
// =============================================================================

import type {
  AgentsMdRepo,
  AgentsMdRepoDetail,
  AgentsMdReposResponse,
  RegenerateRequest,
  RegenerateResponse,
  BulkRegenerateRequest,
  BulkRegenerateResponse,
  ValidateRequest,
  ValidationResult,
  AgentsMdDiff,
  ContextOverlay,
  ContextHistoryEntry,
  OverlayMetrics,
  EngagementMetrics,
  AnalyticsSummary,
  TimeSeriesResponse,
  ProjectAnalytics,
} from "./types/agents-md";

// Re-export types for convenience
export type {
  AgentsMdRepo,
  AgentsMdRepoDetail,
  AgentsMdReposResponse,
  RegenerateRequest,
  RegenerateResponse,
  BulkRegenerateRequest,
  BulkRegenerateResponse,
  ValidateRequest,
  ValidationResult,
  AgentsMdDiff,
  ContextOverlay,
  ContextHistoryEntry,
  OverlayMetrics,
  EngagementMetrics,
  AnalyticsSummary,
  TimeSeriesResponse,
  ProjectAnalytics,
};

/**
 * List AGENTS.md params
 */
export interface AgentsMdListParams {
  page?: number;
  page_size?: number;
  status?: "valid" | "invalid" | "outdated" | "missing";
  project_id?: string;
}

/**
 * List all repositories with AGENTS.md status
 * Sprint 85: GET /agents-md/repos
 */
export async function getAgentsMdRepos(
  options?: AgentsMdListParams
): Promise<AgentsMdReposResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());
  if (options?.status) params.set("status", options.status);
  if (options?.project_id) params.set("project_id", options.project_id);

  const queryString = params.toString();
  const url = queryString ? `/agents-md/repos?${queryString}` : "/agents-md/repos";

  return apiRequest<AgentsMdReposResponse>(url);
}

/**
 * Get AGENTS.md detail for a specific repository
 * Sprint 85: GET /agents-md/{repo_id}
 */
export async function getAgentsMdRepo(repoId: string): Promise<AgentsMdRepoDetail> {
  return apiRequest<AgentsMdRepoDetail>(`/agents-md/${repoId}`);
}

/**
 * Regenerate AGENTS.md file for a repository
 * Sprint 85: POST /agents-md/{repo_id}/regenerate
 */
export async function regenerateAgentsMd(
  repoId: string,
  data?: RegenerateRequest
): Promise<RegenerateResponse> {
  return apiRequest<RegenerateResponse>(`/agents-md/${repoId}/regenerate`, {
    method: "POST",
    body: JSON.stringify(data || {}),
  });
}

/**
 * Bulk regenerate AGENTS.md files for multiple repositories
 * Sprint 85: POST /agents-md/bulk/regenerate
 */
export async function bulkRegenerateAgentsMd(
  data: BulkRegenerateRequest
): Promise<BulkRegenerateResponse> {
  return apiRequest<BulkRegenerateResponse>("/agents-md/bulk/regenerate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get diff between AGENTS.md versions
 * Sprint 85: GET /agents-md/{repo_id}/diff
 */
export async function getAgentsMdDiff(
  repoId: string,
  options?: { from_version?: string; to_version?: string }
): Promise<AgentsMdDiff> {
  const params = new URLSearchParams();
  if (options?.from_version) params.set("from_version", options.from_version);
  if (options?.to_version) params.set("to_version", options.to_version);

  const queryString = params.toString();
  const url = queryString
    ? `/agents-md/${repoId}/diff?${queryString}`
    : `/agents-md/${repoId}/diff`;

  return apiRequest<AgentsMdDiff>(url);
}

/**
 * Validate AGENTS.md content
 * Sprint 85: POST /agents-md/validate
 */
export async function validateAgentsMd(data: ValidateRequest): Promise<ValidationResult> {
  return apiRequest<ValidationResult>("/agents-md/validate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get dynamic context overlay for a repository
 * Sprint 85: GET /agents-md/{repo_id}/context
 */
export async function getAgentsMdContext(repoId: string): Promise<ContextOverlay> {
  return apiRequest<ContextOverlay>(`/agents-md/${repoId}/context`);
}

// =============================================================================
// Context Overlay API (Sprint 85 - Dynamic Context)
// =============================================================================

/**
 * Get context overlay history for a project
 * Sprint 85: GET /context-overlays/project/{project_id}/history
 */
export async function getContextHistory(
  projectId: string,
  options?: { page?: number; page_size?: number }
): Promise<{ history: ContextHistoryEntry[]; total: number }> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", options.page.toString());
  if (options?.page_size) params.set("page_size", options.page_size.toString());

  const queryString = params.toString();
  const url = queryString
    ? `/context-overlays/project/${projectId}/history?${queryString}`
    : `/context-overlays/project/${projectId}/history`;

  return apiRequest<{ history: ContextHistoryEntry[]; total: number }>(url);
}

/**
 * Get context overlay detail by ID
 * Sprint 85: GET /context-overlays/{overlay_id}
 */
export async function getContextOverlay(overlayId: string): Promise<ContextOverlay> {
  return apiRequest<ContextOverlay>(`/context-overlays/${overlayId}`);
}

// =============================================================================
// Analytics API (Sprint 85 - AGENTS.md Analytics)
// =============================================================================

/**
 * Get overlay metrics
 * Sprint 85: GET /analytics/overlay
 */
export async function getOverlayMetrics(
  options?: { period_start?: string; period_end?: string }
): Promise<OverlayMetrics> {
  const params = new URLSearchParams();
  if (options?.period_start) params.set("period_start", options.period_start);
  if (options?.period_end) params.set("period_end", options.period_end);

  const queryString = params.toString();
  const url = queryString ? `/analytics/overlay?${queryString}` : "/analytics/overlay";

  return apiRequest<OverlayMetrics>(url);
}

/**
 * Get engagement metrics
 * Sprint 85: GET /analytics/engagement
 */
export async function getEngagementMetrics(
  options?: { period_start?: string; period_end?: string }
): Promise<EngagementMetrics> {
  const params = new URLSearchParams();
  if (options?.period_start) params.set("period_start", options.period_start);
  if (options?.period_end) params.set("period_end", options.period_end);

  const queryString = params.toString();
  const url = queryString ? `/analytics/engagement?${queryString}` : "/analytics/engagement";

  return apiRequest<EngagementMetrics>(url);
}

/**
 * Get analytics summary combining all metrics
 * Sprint 85: GET /analytics/summary
 */
export async function getAnalyticsSummary(
  options?: { period_start?: string; period_end?: string }
): Promise<AnalyticsSummary> {
  const params = new URLSearchParams();
  if (options?.period_start) params.set("period_start", options.period_start);
  if (options?.period_end) params.set("period_end", options.period_end);

  const queryString = params.toString();
  const url = queryString ? `/analytics/summary?${queryString}` : "/analytics/summary";

  return apiRequest<AnalyticsSummary>(url);
}

/**
 * Get time series data for a specific metric
 * Sprint 85: GET /analytics/time-series/{metric}
 */
export async function getAnalyticsTimeSeries(
  metric: string,
  options?: {
    period_start?: string;
    period_end?: string;
    granularity?: "hour" | "day" | "week" | "month";
  }
): Promise<TimeSeriesResponse> {
  const params = new URLSearchParams();
  if (options?.period_start) params.set("period_start", options.period_start);
  if (options?.period_end) params.set("period_end", options.period_end);
  if (options?.granularity) params.set("granularity", options.granularity);

  const queryString = params.toString();
  const url = queryString
    ? `/analytics/time-series/${metric}?${queryString}`
    : `/analytics/time-series/${metric}`;

  return apiRequest<TimeSeriesResponse>(url);
}

/**
 * Export analytics data
 * Sprint 85: GET /analytics/export
 */
export async function exportAnalytics(
  format: "json" | "csv",
  options?: {
    metrics?: string[];
    period_start?: string;
    period_end?: string;
  }
): Promise<Blob> {
  const params = new URLSearchParams();
  params.set("format", format);
  if (options?.metrics) params.set("metrics", options.metrics.join(","));
  if (options?.period_start) params.set("period_start", options.period_start);
  if (options?.period_end) params.set("period_end", options.period_end);

  const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/analytics/export?${params.toString()}`;

  const response = await fetch(url, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to export analytics");
  }

  return response.blob();
}

/**
 * Get project-specific analytics
 * Sprint 85: GET /analytics/projects/{project_id}
 */
export async function getProjectAnalytics(projectId: string): Promise<ProjectAnalytics> {
  return apiRequest<ProjectAnalytics>(`/analytics/projects/${projectId}`);
}

// =============================================================================
// CLI Token API (Sprint 85 - CLI Authentication)
// =============================================================================

import type {
  CliToken,
  CliTokenListParams,
  CliTokensResponse,
  CliTokenCreatedResponse,
  CreateCliTokenRequest,
  RefreshCliTokenResponse,
  CliTokenStats,
  CliSession,
  CliLoginRequest,
  CliLoginVerification,
  CliDevice,
} from "./types/cli-token";

/**
 * Get list of CLI tokens
 * Sprint 85: GET /cli/tokens
 */
export async function getCliTokens(
  params?: CliTokenListParams
): Promise<CliTokensResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
  if (params?.is_active !== undefined)
    searchParams.set("is_active", params.is_active.toString());
  if (params?.include_expired !== undefined)
    searchParams.set("include_expired", params.include_expired.toString());

  const query = searchParams.toString();
  return apiRequest<CliTokensResponse>(`/cli/tokens${query ? `?${query}` : ""}`);
}

/**
 * Get single CLI token details
 * Sprint 85: GET /cli/tokens/{token_id}
 */
export async function getCliToken(tokenId: string): Promise<CliToken> {
  return apiRequest<CliToken>(`/cli/tokens/${tokenId}`);
}

/**
 * Create a new CLI token
 * Sprint 85: POST /cli/tokens
 */
export async function createCliToken(
  data: CreateCliTokenRequest
): Promise<CliTokenCreatedResponse> {
  return apiRequest<CliTokenCreatedResponse>("/cli/tokens", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Revoke a CLI token
 * Sprint 85: DELETE /cli/tokens/{token_id}
 */
export async function revokeCliToken(tokenId: string): Promise<void> {
  return apiRequest<void>(`/cli/tokens/${tokenId}`, {
    method: "DELETE",
  });
}

/**
 * Refresh/rotate a CLI token
 * Sprint 85: POST /cli/tokens/{token_id}/refresh
 */
export async function refreshCliToken(
  tokenId: string,
  extendDays?: number
): Promise<RefreshCliTokenResponse> {
  return apiRequest<RefreshCliTokenResponse>(`/cli/tokens/${tokenId}/refresh`, {
    method: "POST",
    body: JSON.stringify({ extend_days: extendDays }),
  });
}

/**
 * Get CLI token statistics
 * Sprint 85: GET /cli/tokens/stats
 */
export async function getCliTokenStats(): Promise<CliTokenStats> {
  return apiRequest<CliTokenStats>("/cli/tokens/stats");
}

/**
 * Get active CLI sessions
 * Sprint 85: GET /cli/sessions
 */
export async function getCliSessions(): Promise<CliSession[]> {
  return apiRequest<CliSession[]>("/cli/sessions");
}

/**
 * Revoke a CLI session
 * Sprint 85: DELETE /cli/sessions/{session_id}
 */
export async function revokeCliSession(sessionId: string): Promise<void> {
  return apiRequest<void>(`/cli/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

/**
 * Initiate CLI login (device flow)
 * Sprint 85: POST /cli/login/initiate
 */
export async function initiateCliLogin(): Promise<CliLoginRequest> {
  return apiRequest<CliLoginRequest>("/cli/login/initiate", {
    method: "POST",
  });
}

/**
 * Verify CLI login status
 * Sprint 85: GET /cli/login/verify/{device_code}
 */
export async function verifyCliLogin(
  deviceCode: string
): Promise<CliLoginVerification> {
  return apiRequest<CliLoginVerification>(`/cli/login/verify/${deviceCode}`);
}

/**
 * Approve CLI login from web
 * Sprint 85: POST /cli/login/approve/{device_code}
 */
export async function approveCliLogin(
  deviceCode: string,
  userCode: string
): Promise<{ success: boolean; message: string }> {
  return apiRequest<{ success: boolean; message: string }>(
    `/cli/login/approve/${deviceCode}`,
    {
      method: "POST",
      body: JSON.stringify({ user_code: userCode }),
    }
  );
}

/**
 * Deny CLI login from web
 * Sprint 85: POST /cli/login/deny/{device_code}
 */
export async function denyCliLogin(
  deviceCode: string
): Promise<{ success: boolean; message: string }> {
  return apiRequest<{ success: boolean; message: string }>(
    `/cli/login/deny/${deviceCode}`,
    {
      method: "POST",
    }
  );
}

/**
 * Get registered CLI devices
 * Sprint 85: GET /cli/devices
 */
export async function getCliDevices(): Promise<CliDevice[]> {
  return apiRequest<CliDevice[]>("/cli/devices");
}

/**
 * Remove a CLI device
 * Sprint 85: DELETE /cli/devices/{device_id}
 */
export async function removeCliDevice(deviceId: string): Promise<void> {
  return apiRequest<void>(`/cli/devices/${deviceId}`, {
    method: "DELETE",
  });
}

/**
 * Trust/untrust a CLI device
 * Sprint 85: PATCH /cli/devices/{device_id}
 */
export async function updateCliDevice(
  deviceId: string,
  data: { is_trusted: boolean }
): Promise<CliDevice> {
  return apiRequest<CliDevice>(`/cli/devices/${deviceId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// =============================================================================
// GitHub Check Run API (Sprint 86 - P0 Blocker)
// =============================================================================

import type {
  CheckRunDetail,
  CheckRunListParams,
  CheckRunsResponse,
  CreateCheckRunRequest,
  CreateCheckRunResponse,
  RerunCheckRunRequest,
  CheckRunStats,
  ProjectCheckRunConfig,
  UpdateCheckRunConfigRequest,
} from "./types/github-checks";

/**
 * Get list of Check Runs
 * Sprint 86: GET /check-runs
 */
export async function getCheckRuns(
  params?: CheckRunListParams
): Promise<CheckRunsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
  if (params?.project_id) searchParams.set("project_id", params.project_id);
  if (params?.repository) searchParams.set("repository", params.repository);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.conclusion) searchParams.set("conclusion", params.conclusion);
  if (params?.mode) searchParams.set("mode", params.mode);
  if (params?.from_date) searchParams.set("from_date", params.from_date);
  if (params?.to_date) searchParams.set("to_date", params.to_date);

  const query = searchParams.toString();
  return apiRequest<CheckRunsResponse>(`/check-runs${query ? `?${query}` : ""}`);
}

/**
 * Get single Check Run detail
 * Sprint 86: GET /check-runs/{check_run_id}
 */
export async function getCheckRun(checkRunId: string): Promise<CheckRunDetail> {
  return apiRequest<CheckRunDetail>(`/check-runs/${checkRunId}`);
}

/**
 * Create a new Check Run
 * Sprint 86: POST /check-runs
 */
export async function createCheckRun(
  data: CreateCheckRunRequest
): Promise<CreateCheckRunResponse> {
  return apiRequest<CreateCheckRunResponse>("/check-runs", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Re-run a Check Run
 * Sprint 86: POST /check-runs/{check_run_id}/rerun
 */
export async function rerunCheckRun(
  data: RerunCheckRunRequest
): Promise<CreateCheckRunResponse> {
  return apiRequest<CreateCheckRunResponse>(
    `/check-runs/${data.check_run_id}/rerun`,
    {
      method: "POST",
      body: JSON.stringify({ force: data.force }),
    }
  );
}

/**
 * Get Check Run statistics
 * Sprint 86: GET /check-runs/stats
 */
export async function getCheckRunStats(options?: {
  project_id?: string;
  period_days?: number;
}): Promise<CheckRunStats> {
  const searchParams = new URLSearchParams();
  if (options?.project_id) searchParams.set("project_id", options.project_id);
  if (options?.period_days)
    searchParams.set("period_days", options.period_days.toString());

  const query = searchParams.toString();
  return apiRequest<CheckRunStats>(`/check-runs/stats${query ? `?${query}` : ""}`);
}

/**
 * Get project Check Run configuration
 * Sprint 86: GET /projects/{project_id}/check-runs/config
 */
export async function getProjectCheckRunConfig(
  projectId: string
): Promise<ProjectCheckRunConfig> {
  return apiRequest<ProjectCheckRunConfig>(
    `/projects/${projectId}/check-runs/config`
  );
}

/**
 * Update project Check Run configuration
 * Sprint 86: PATCH /projects/{project_id}/check-runs/config
 */
export async function updateProjectCheckRunConfig(
  projectId: string,
  data: UpdateCheckRunConfigRequest
): Promise<ProjectCheckRunConfig> {
  return apiRequest<ProjectCheckRunConfig>(
    `/projects/${projectId}/check-runs/config`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

// =============================================================================
// Evidence Manifest API (Sprint 87 - P0 Blocker - Hash Chain v1)
// =============================================================================

import type {
  EvidenceManifest,
  ManifestListResponse,
  ManifestListParams,
  CreateManifestRequest,
  VerifyChainRequest,
  VerifyChainResponse,
  ChainStatusResponse,
  VerificationHistoryResponse,
} from "./types/evidence-manifest";

/**
 * Get list of Evidence Manifests for a project
 * Sprint 87: GET /evidence-manifests
 */
export async function getEvidenceManifests(
  params: ManifestListParams
): Promise<ManifestListResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("project_id", params.project_id);
  if (params.limit) searchParams.set("limit", params.limit.toString());
  if (params.offset) searchParams.set("offset", params.offset.toString());

  return apiRequest<ManifestListResponse>(
    `/evidence-manifests?${searchParams.toString()}`
  );
}

/**
 * Get single Evidence Manifest by ID
 * Sprint 87: GET /evidence-manifests/{manifest_id}
 */
export async function getEvidenceManifest(
  manifestId: string
): Promise<EvidenceManifest> {
  return apiRequest<EvidenceManifest>(`/evidence-manifests/${manifestId}`);
}

/**
 * Create a new Evidence Manifest
 * Sprint 87: POST /evidence-manifests
 */
export async function createEvidenceManifest(
  data: CreateManifestRequest
): Promise<EvidenceManifest> {
  return apiRequest<EvidenceManifest>("/evidence-manifests", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Verify Evidence Chain integrity
 * Sprint 87: POST /evidence-manifests/verify
 */
export async function verifyEvidenceChain(
  data: VerifyChainRequest
): Promise<VerifyChainResponse> {
  return apiRequest<VerifyChainResponse>("/evidence-manifests/verify", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get chain status for a project
 * Sprint 87: GET /evidence-manifests/chain-status/{project_id}
 */
export async function getChainStatus(
  projectId: string
): Promise<ChainStatusResponse> {
  return apiRequest<ChainStatusResponse>(
    `/evidence-manifests/chain-status/${projectId}`
  );
}

/**
 * Get verification history for a project
 * Sprint 87: GET /evidence-manifests/verification-history/{project_id}
 */
export async function getVerificationHistory(
  projectId: string,
  limit?: number,
  offset?: number
): Promise<VerificationHistoryResponse> {
  const searchParams = new URLSearchParams();
  if (limit) searchParams.set("limit", limit.toString());
  if (offset) searchParams.set("offset", offset.toString());

  const query = searchParams.toString();
  return apiRequest<VerificationHistoryResponse>(
    `/evidence-manifests/verification-history/${projectId}${query ? `?${query}` : ""}`
  );
}
