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
 * Generic API request function with timeout support and automatic token refresh
 * Sprint 136 Fix: When access token expires (15 min), automatically refresh and retry
 * @param endpoint API endpoint
 * @param options Fetch options
 * @param timeout Timeout in milliseconds (default: 10000ms = 10s)
 * @param isRetry Internal flag to prevent infinite retry loops
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  timeout: number = 10000,
  isRetry: boolean = false
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Sprint 105: Fallback to localStorage token if cookies don't work
  // This handles cases where httpOnly cookies expire (15 min) but localStorage token is still valid
  if (typeof window !== "undefined") {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      defaultHeaders["Authorization"] = `Bearer ${accessToken}`;
    }
  }

  // Create AbortController for timeout
  const controller = new AbortController();
  const startTime = Date.now();
  const timeoutId = setTimeout(() => {
    console.log(`[apiRequest] Timeout after ${timeout}ms for ${endpoint}`);
    controller.abort();
  }, timeout);

  console.log(`[apiRequest] Starting ${options.method || 'GET'} ${endpoint} (timeout: ${timeout}ms)`);

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      credentials: "include", // Include cookies for auth
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    console.log(`[apiRequest] Response ${response.status} for ${endpoint} in ${Date.now() - startTime}ms`);

    // Sprint 136: Auto-refresh token on 401 (except for auth endpoints and retries)
    if (response.status === 401 && !isRetry && !endpoint.includes("/auth/")) {
      console.log("[apiRequest] Access token expired, attempting refresh...");
      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (refreshResponse.ok) {
          console.log("[apiRequest] Token refreshed, retrying original request...");
          // Retry the original request
          return apiRequest<T>(endpoint, options, timeout, true);
        }
      } catch (refreshError) {
        console.error("[apiRequest] Token refresh failed:", refreshError);
      }

      // Refresh failed - throw 401 to trigger login redirect
      console.log("[apiRequest] Session expired");
      const error: APIError = {
        detail: "Session expired. Please log in again.",
        status: 401,
      };
      throw error;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "An unexpected error occurred",
      }));

      const error: APIError = {
        detail: errorData.detail || "Request failed",
        status: response.status,
      };

      console.log("[apiRequest] Throwing error:", error);
      throw error;
    }

    return response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    const elapsed = Date.now() - startTime;
    if (err instanceof Error && err.name === "AbortError") {
      console.log(`[apiRequest] Aborted after ${elapsed}ms for ${endpoint}`);
      throw { detail: "Request timeout", status: 408 } as APIError;
    }
    console.log(`[apiRequest] Error after ${elapsed}ms for ${endpoint}:`, err);
    throw err;
  }
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
  is_superuser: boolean; // DEPRECATED - use is_platform_admin (Sprint 88)
  is_platform_admin: boolean; // Sprint 88: Platform admin flag
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
 * Sprint 105: Increased timeout to 30s for OAuth operations
 * Sprint 133: Pass dynamic redirect_uri based on current origin
 */
export async function getOAuthAuthorizeUrl(
  provider: "github" | "google"
): Promise<OAuthAuthorizeResponse> {
  // Construct redirect_uri based on current origin to support localhost testing
  const callbackPath = provider === "github" ? "/auth/github/callback" : "/auth/callback";
  const redirectUri = typeof window !== "undefined"
    ? `${window.location.origin}${callbackPath}`
    : undefined;

  const queryParams = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : "";
  return apiRequest<OAuthAuthorizeResponse>(`/auth/oauth/${provider}/authorize${queryParams}`, {}, 30000);
}

/**
 * Exchange OAuth code for tokens (for login/signup flow)
 * Sprint 105: Increased timeout to 120s for OAuth token exchange
 * External OAuth providers (GitHub, Google) may have network latency
 */
export async function exchangeOAuthCode(
  provider: "github" | "google",
  data: OAuthCallbackRequest
): Promise<TokenResponse> {
  console.log("[exchangeOAuthCode] Starting with 120s timeout for", provider);
  return apiRequest<TokenResponse>(`/auth/oauth/${provider}/callback`, {
    method: "POST",
    body: JSON.stringify(data),
  }, 120000);
}

/**
 * Exchange GitHub OAuth code for tokens (for connect flow from Settings)
 * This uses the /github/callback endpoint which doesn't validate state encoding
 * Sprint 105: Increased timeout to 30s for OAuth token exchange
 */
export async function exchangeGitHubConnectCode(
  data: OAuthCallbackRequest
): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(`/github/callback`, {
    method: "POST",
    body: JSON.stringify(data),
  }, 30000);
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
 * Sprint 90: Added team_id, github_repo_id, github_repo_full_name for project linking
 */
export interface CreateProjectRequest {
  name: string;
  description?: string;
  policy_pack_tier?: "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";
  team_id?: string;
  github_repo_id?: number;
  github_repo_full_name?: string;
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
 * Sprint 90: Map policy_pack_tier to policy_pack for backend compatibility
 */
export async function createProject(
  data: CreateProjectRequest
): Promise<CreateProjectResponse> {
  // Map frontend field names to backend field names
  const backendData = {
    name: data.name,
    description: data.description,
    policy_pack: data.policy_pack_tier?.toLowerCase(), // Backend uses policy_pack, not policy_pack_tier
    team_id: data.team_id,
    github_repo_id: data.github_repo_id,
    github_repo_full_name: data.github_repo_full_name,
  };

  return apiRequest<CreateProjectResponse>(`/projects`, {
    method: "POST",
    body: JSON.stringify(backendData),
  });
}

/**
 * Delete a project (soft delete)
 * Sprint 145: Only project owners can delete projects
 */
export async function deleteProject(projectId: string): Promise<void> {
  return apiRequest<void>(`/projects/${projectId}`, {
    method: "DELETE",
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
  const response = await apiRequest<{ repositories: GitHubRepository[]; total: number }>("/github/repositories");
  return response.repositories;
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
    method: "DELETE",
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

// =============================================================================
// System Settings API (Sprint 86 Phase 2 - ADR-027)
// =============================================================================

import type {
  SystemSettingsListResponse,
  SystemSettingItem,
  SystemSettingUpdate,
} from "./types/system-settings";

/**
 * Get all system settings grouped by category
 * Sprint 86: GET /admin/settings
 * Requires: superuser access
 */
export async function getSystemSettings(): Promise<SystemSettingsListResponse> {
  return apiRequest<SystemSettingsListResponse>("/admin/settings");
}

/**
 * Get a specific system setting by key
 * Sprint 86: GET /admin/settings/{key}
 * Requires: superuser access
 */
export async function getSystemSetting(key: string): Promise<SystemSettingItem> {
  return apiRequest<SystemSettingItem>(`/admin/settings/${key}`);
}

/**
 * Update a system setting value
 * Sprint 86: PATCH /admin/settings/{key}
 * Requires: superuser access
 * Note: Change propagates within 5 minutes (Redis cache TTL)
 */
export async function updateSystemSetting(
  key: string,
  data: SystemSettingUpdate
): Promise<SystemSettingItem> {
  return apiRequest<SystemSettingItem>(`/admin/settings/${key}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Rollback a system setting to previous value
 * Sprint 86: POST /admin/settings/{key}/rollback
 * Requires: superuser access
 */
export async function rollbackSystemSetting(
  key: string
): Promise<SystemSettingItem> {
  return apiRequest<SystemSettingItem>(`/admin/settings/${key}/rollback`, {
    method: "POST",
  });
}

// =============================================================================
// Planning Hierarchy API (Sprint 87 - SDLC 5.1.3 Pillar 2)
// =============================================================================

import type {
  Roadmap,
  RoadmapInput,
  RoadmapsListResponse,
  Phase,
  PhaseInput,
  PhasesListResponse,
  Sprint,
  SprintInput,
  SprintUpdateInput,
  SprintsListResponse,
  BacklogItem,
  BacklogItemInput,
  BacklogItemUpdateInput,
  BacklogItemsListResponse,
  BulkMoveItemsInput,
  PlanningHierarchyResponse,
  ActiveSprintDashboard,
} from "./types/planning";

import type {
  SprintGate,
  SprintGateType,
  ChecklistItem,
  GateEvaluationRequest,
  GateEvaluationResponse,
  SprintGateApprovalRequest,
  UpdateChecklistItemRequest,
  DocumentationDeadline,
  SprintGovernanceMetrics,
  SprintComparison,
  SprintGovernanceDashboard,
} from "./types/sprint-governance";

// -----------------------------------------------------------------------------
// Roadmaps API
// -----------------------------------------------------------------------------

/**
 * Get roadmaps for a project
 * Sprint 87: GET /projects/{id}/roadmaps
 */
export async function getRoadmaps(projectId: string): Promise<RoadmapsListResponse> {
  return apiRequest<RoadmapsListResponse>(`/projects/${projectId}/roadmaps`);
}

/**
 * Get a specific roadmap by ID
 * Sprint 87: GET /roadmaps/{id}
 */
export async function getRoadmap(id: string): Promise<Roadmap> {
  return apiRequest<Roadmap>(`/roadmaps/${id}`);
}

/**
 * Create a new roadmap
 * Sprint 87: POST /roadmaps
 */
export async function createRoadmap(data: RoadmapInput): Promise<Roadmap> {
  return apiRequest<Roadmap>("/roadmaps", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a roadmap
 * Sprint 87: PATCH /roadmaps/{id}
 */
export async function updateRoadmap(
  id: string,
  data: Partial<RoadmapInput>
): Promise<Roadmap> {
  return apiRequest<Roadmap>(`/roadmaps/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a roadmap
 * Sprint 87: DELETE /roadmaps/{id}
 */
export async function deleteRoadmap(id: string): Promise<void> {
  return apiRequest<void>(`/roadmaps/${id}`, {
    method: "DELETE",
  });
}

// -----------------------------------------------------------------------------
// Phases API
// -----------------------------------------------------------------------------

/**
 * Get phases for a roadmap
 * Sprint 87: GET /roadmaps/{id}/phases
 */
export async function getPhases(roadmapId: string): Promise<PhasesListResponse> {
  return apiRequest<PhasesListResponse>(`/roadmaps/${roadmapId}/phases`);
}

/**
 * Get a specific phase by ID
 * Sprint 87: GET /phases/{id}
 */
export async function getPhase(id: string): Promise<Phase> {
  return apiRequest<Phase>(`/phases/${id}`);
}

/**
 * Create a new phase
 * Sprint 87: POST /phases
 */
export async function createPhase(data: PhaseInput): Promise<Phase> {
  return apiRequest<Phase>("/phases", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a phase
 * Sprint 87: PATCH /phases/{id}
 */
export async function updatePhase(id: string, data: Partial<PhaseInput>): Promise<Phase> {
  return apiRequest<Phase>(`/phases/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a phase
 * Sprint 87: DELETE /phases/{id}
 */
export async function deletePhase(id: string): Promise<void> {
  return apiRequest<void>(`/phases/${id}`, {
    method: "DELETE",
  });
}

// -----------------------------------------------------------------------------
// Sprints API
// -----------------------------------------------------------------------------

/**
 * Get sprints with optional filters
 * Sprint 87: GET /projects/{id}/sprints or GET /phases/{id}/sprints
 */
export async function getSprints(params: {
  projectId?: string;
  phaseId?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<SprintsListResponse> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.page) searchParams.set("page", params.page.toString());
  if (params.page_size) searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();

  if (params.phaseId) {
    return apiRequest<SprintsListResponse>(
      `/phases/${params.phaseId}/sprints${query ? `?${query}` : ""}`
    );
  }

  return apiRequest<SprintsListResponse>(
    `/projects/${params.projectId}/sprints${query ? `?${query}` : ""}`
  );
}

/**
 * Get a specific sprint by ID
 * Sprint 87: GET /sprints/{id}
 */
export async function getSprint(id: string): Promise<Sprint> {
  return apiRequest<Sprint>(`/sprints/${id}`);
}

/**
 * Get the active sprint for a project
 * Sprint 87: GET /projects/{id}/sprints/active
 */
export async function getActiveSprint(projectId: string): Promise<Sprint | null> {
  try {
    return await apiRequest<Sprint>(`/projects/${projectId}/sprints/active`);
  } catch (error) {
    // Return null if no active sprint (404)
    if ((error as { status?: number }).status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Create a new sprint
 * Sprint 87: POST /sprints
 */
export async function createSprint(data: SprintInput): Promise<Sprint> {
  return apiRequest<Sprint>("/sprints", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a sprint
 * Sprint 87: PATCH /sprints/{id}
 */
export async function updateSprint(
  id: string,
  data: SprintUpdateInput
): Promise<Sprint> {
  return apiRequest<Sprint>(`/sprints/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a sprint
 * Sprint 87: DELETE /sprints/{id}
 */
export async function deleteSprint(id: string): Promise<void> {
  return apiRequest<void>(`/sprints/${id}`, {
    method: "DELETE",
  });
}

// -----------------------------------------------------------------------------
// Backlog Items API
// -----------------------------------------------------------------------------

/**
 * Get backlog items with optional filters
 * Sprint 87: GET /sprints/{id}/items or GET /projects/{id}/backlog
 */
export async function getBacklogItems(params: {
  sprintId?: string;
  projectId?: string;
  status?: string;
  priority?: string;
  page?: number;
  page_size?: number;
}): Promise<BacklogItemsListResponse> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.priority) searchParams.set("priority", params.priority);
  if (params.page) searchParams.set("page", params.page.toString());
  if (params.page_size) searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();

  if (params.sprintId) {
    return apiRequest<BacklogItemsListResponse>(
      `/sprints/${params.sprintId}/items${query ? `?${query}` : ""}`
    );
  }

  return apiRequest<BacklogItemsListResponse>(
    `/projects/${params.projectId}/backlog${query ? `?${query}` : ""}`
  );
}

/**
 * Get a specific backlog item by ID
 * Sprint 87: GET /backlog-items/{id}
 */
export async function getBacklogItem(id: string): Promise<BacklogItem> {
  return apiRequest<BacklogItem>(`/backlog-items/${id}`);
}

/**
 * Create a new backlog item
 * Sprint 87: POST /backlog-items
 */
export async function createBacklogItem(data: BacklogItemInput): Promise<BacklogItem> {
  return apiRequest<BacklogItem>("/backlog-items", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a backlog item
 * Sprint 87: PATCH /backlog-items/{id}
 */
export async function updateBacklogItem(
  id: string,
  data: BacklogItemUpdateInput
): Promise<BacklogItem> {
  return apiRequest<BacklogItem>(`/backlog-items/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a backlog item
 * Sprint 87: DELETE /backlog-items/{id}
 */
export async function deleteBacklogItem(id: string): Promise<void> {
  return apiRequest<void>(`/backlog-items/${id}`, {
    method: "DELETE",
  });
}

/**
 * Bulk move backlog items (drag and drop)
 * Sprint 87: POST /projects/{id}/backlog/bulk-move
 */
export async function bulkMoveBacklogItems(
  projectId: string,
  data: BulkMoveItemsInput
): Promise<BacklogItem[]> {
  return apiRequest<BacklogItem[]>(`/projects/${projectId}/backlog/bulk-move`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// -----------------------------------------------------------------------------
// Planning Hierarchy API
// -----------------------------------------------------------------------------

/**
 * Get full planning hierarchy for a project
 * Sprint 87: GET /projects/{id}/planning-hierarchy
 */
export async function getPlanningHierarchy(
  projectId: string
): Promise<PlanningHierarchyResponse> {
  return apiRequest<PlanningHierarchyResponse>(
    `/projects/${projectId}/planning-hierarchy`
  );
}

/**
 * Get active sprint dashboard data
 * Sprint 87: GET /projects/{id}/sprints/dashboard
 */
export async function getActiveSprintDashboard(
  projectId: string
): Promise<ActiveSprintDashboard | null> {
  try {
    return await apiRequest<ActiveSprintDashboard>(
      `/projects/${projectId}/sprints/dashboard`
    );
  } catch (error) {
    if ((error as { status?: number }).status === 404) {
      return null;
    }
    throw error;
  }
}

// =============================================================================
// Sprint Governance API (Sprint 87 - SDLC 5.1.3 Pillar 2)
// =============================================================================

// -----------------------------------------------------------------------------
// Sprint Gates API (G-Sprint, G-Sprint-Close)
// -----------------------------------------------------------------------------

/**
 * Get sprint gate (G-Sprint or G-Sprint-Close)
 * Sprint 87: GET /sprints/{id}/gates/{type}
 */
export async function getSprintGate(
  sprintId: string,
  gateType: SprintGateType
): Promise<SprintGate> {
  return apiRequest<SprintGate>(`/sprints/${sprintId}/gates/${gateType}`);
}

/**
 * Get gate checklist items
 * Sprint 87: GET /sprints/{id}/gates/{type}/checklist
 */
export async function getSprintGateChecklist(
  sprintId: string,
  gateType: SprintGateType
): Promise<ChecklistItem[]> {
  return apiRequest<ChecklistItem[]>(
    `/sprints/${sprintId}/gates/${gateType}/checklist`
  );
}

/**
 * Evaluate sprint gate
 * Sprint 87: POST /sprints/{id}/gates/{type}/evaluate
 */
export async function evaluateSprintGate(
  sprintId: string,
  gateType: SprintGateType,
  data?: GateEvaluationRequest
): Promise<GateEvaluationResponse> {
  return apiRequest<GateEvaluationResponse>(
    `/sprints/${sprintId}/gates/${gateType}/evaluate`,
    {
      method: "POST",
      body: JSON.stringify(data || {}),
    }
  );
}

/**
 * Approve sprint gate
 * Sprint 87: POST /sprints/{id}/gates/{type}/approve
 */
export async function approveSprintGate(
  sprintId: string,
  gateType: SprintGateType,
  data?: SprintGateApprovalRequest
): Promise<SprintGate> {
  return apiRequest<SprintGate>(`/sprints/${sprintId}/gates/${gateType}/approve`, {
    method: "POST",
    body: JSON.stringify(data || {}),
  });
}

/**
 * Update a checklist item
 * Sprint 87: PATCH /sprints/{id}/gates/{type}/checklist/{itemId}
 */
export async function updateChecklistItem(
  sprintId: string,
  gateType: SprintGateType,
  itemId: string,
  data: UpdateChecklistItemRequest
): Promise<ChecklistItem> {
  return apiRequest<ChecklistItem>(
    `/sprints/${sprintId}/gates/${gateType}/checklist/${itemId}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

// -----------------------------------------------------------------------------
// Documentation Deadline API (24h Rule)
// -----------------------------------------------------------------------------

/**
 * Get documentation deadline for sprint close
 * Sprint 87: GET /sprints/{id}/documentation-deadline
 */
export async function getDocumentationDeadline(
  sprintId: string
): Promise<DocumentationDeadline> {
  return apiRequest<DocumentationDeadline>(
    `/sprints/${sprintId}/documentation-deadline`
  );
}

// -----------------------------------------------------------------------------
// Sprint Governance Metrics API
// -----------------------------------------------------------------------------

/**
 * Get sprint governance metrics
 * Sprint 87: GET /sprints/{id}/governance-metrics
 */
export async function getSprintGovernanceMetrics(
  sprintId: string
): Promise<SprintGovernanceMetrics> {
  return apiRequest<SprintGovernanceMetrics>(
    `/sprints/${sprintId}/governance-metrics`
  );
}

/**
 * Get sprint comparison data
 * Sprint 87: POST /sprints/compare
 */
export async function getSprintComparison(
  sprintIds: string[]
): Promise<SprintComparison> {
  return apiRequest<SprintComparison>("/sprints/compare", {
    method: "POST",
    body: JSON.stringify({ sprint_ids: sprintIds }),
  });
}

// -----------------------------------------------------------------------------
// Sprint Governance Dashboard API
// -----------------------------------------------------------------------------

/**
 * Get sprint governance dashboard data
 * Sprint 87: GET /projects/{id}/sprint-governance/dashboard
 */
export async function getSprintGovernanceDashboard(
  projectId: string
): Promise<SprintGovernanceDashboard> {
  return apiRequest<SprintGovernanceDashboard>(
    `/projects/${projectId}/sprint-governance/dashboard`
  );
}

// =============================================================================
// Planning Sub-agent API (Sprint 99 - ADR-034)
// =============================================================================

import type {
  PlanningRequest,
  PlanningResult,
  PlanApprovalRequest,
  ConformanceCheckRequest,
  ConformanceResult,
  PlanningSessionListResponse,
  PlanningStatus,
} from "@/lib/types/planning-subagent";

/**
 * Create a new planning session with sub-agent orchestration
 * Sprint 99: POST /planning/subagent/plan
 */
export async function createPlanningSession(
  request: PlanningRequest
): Promise<PlanningResult> {
  return apiRequest<PlanningResult>("/planning/subagent/plan", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Get planning session by ID
 * Sprint 99: GET /planning/subagent/{id}
 */
export async function getPlanningSession(
  planningId: string
): Promise<PlanningResult> {
  return apiRequest<PlanningResult>(`/planning/subagent/${planningId}`);
}

/**
 * Approve or reject a planning session
 * Sprint 99: POST /planning/subagent/{id}/approve
 */
export async function approvePlanningSession(
  planningId: string,
  request: PlanApprovalRequest
): Promise<PlanningResult> {
  return apiRequest<PlanningResult>(`/planning/subagent/${planningId}/approve`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Check PR/diff conformance against established patterns
 * Sprint 99: POST /planning/subagent/conformance
 */
export async function checkConformance(
  request: ConformanceCheckRequest
): Promise<ConformanceResult> {
  return apiRequest<ConformanceResult>("/planning/subagent/conformance", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * List planning sessions with optional filters
 * Sprint 99: GET /planning/subagent/sessions
 */
export async function listPlanningSessions(params?: {
  status?: PlanningStatus;
  limit?: number;
}): Promise<PlanningSessionListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status) {
    searchParams.set("status_filter", params.status);
  }
  if (params?.limit) {
    searchParams.set("limit", params.limit.toString());
  }

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/planning/subagent/sessions?${queryString}`
    : "/planning/subagent/sessions";

  return apiRequest<PlanningSessionListResponse>(endpoint);
}

/**
 * Check planning sub-agent service health
 * Sprint 99: GET /planning/subagent/health
 */
export async function getPlanningSubagentHealth(): Promise<{
  status: string;
  service: string;
  version: string;
}> {
  return apiRequest<{ status: string; service: string; version: string }>(
    "/planning/subagent/health"
  );
}

// =============================================================================
// Sprint 100 (EP-11): Feedback Learning API
// =============================================================================

/**
 * Feedback Types for PR review learnings
 */
export type FeedbackType =
  | "pattern_violation"
  | "missing_requirement"
  | "edge_case"
  | "performance"
  | "security_issue"
  | "test_coverage"
  | "documentation"
  | "refactoring"
  | "other";

/**
 * Severity levels for learnings
 */
export type Severity = "low" | "medium" | "high" | "critical";

/**
 * Learning status values
 */
export type LearningStatus = "extracted" | "reviewed" | "applied" | "archived";

/**
 * Hint types for decomposition
 */
export type HintType =
  | "pattern"
  | "antipattern"
  | "convention"
  | "checklist"
  | "dependency";

/**
 * Hint status values
 */
export type HintStatus = "active" | "deprecated" | "merged" | "archived";

/**
 * Aggregation period types
 */
export type AggregationPeriod = "weekly" | "monthly" | "quarterly";

/**
 * PR Learning entity
 */
export interface PRLearning {
  id: string;
  project_id: string;
  pr_number: number;
  pr_title: string | null;
  pr_url: string | null;
  pr_merged_at: string | null;
  feedback_type: FeedbackType;
  severity: Severity;
  original_code: string | null;
  original_spec_section: string | null;
  review_comment: string;
  corrected_approach: string | null;
  pattern_extracted: string | null;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  related_adr: string | null;
  reviewer_id: string | null;
  reviewer_github_login: string | null;
  status: LearningStatus;
  applied_to_claude_md: boolean;
  applied_to_decomposition: boolean;
  applied_at: string | null;
  ai_extracted: boolean;
  ai_confidence: number | null;
  ai_model: string | null;
  tags: string[];
  related_learnings: string[];
  created_at: string;
  updated_at: string;
}

/**
 * Decomposition Hint entity
 */
export interface DecompositionHint {
  id: string;
  project_id: string;
  hint_type: HintType;
  category: string;
  subcategory: string | null;
  title: string;
  description: string;
  example_good: string | null;
  example_bad: string | null;
  rationale: string | null;
  applies_to: string[];
  languages: string[];
  frameworks: string[];
  source_learning_id: string | null;
  aggregation_id: string | null;
  confidence: number;
  usage_count: number;
  effectiveness_score: number | null;
  prevented_errors: number;
  last_used_at: string | null;
  status: HintStatus;
  deprecated_reason: string | null;
  merged_into_id: string | null;
  ai_generated: boolean;
  ai_model: string | null;
  human_verified: boolean;
  verified_by: string | null;
  verified_at: string | null;
  tags: string[];
  related_adrs: string[];
  created_at: string;
  updated_at: string;
}

/**
 * Learning Aggregation entity
 */
export interface LearningAggregation {
  id: string;
  project_id: string;
  period_type: AggregationPeriod;
  period_start: string;
  period_end: string;
  total_learnings: number;
  by_feedback_type: Record<string, number>;
  by_severity: Record<string, number>;
  top_patterns: Array<{
    pattern: string;
    count: number;
    severity: string;
  }>;
  top_files: Array<{
    file_path: string;
    count: number;
  }>;
  claude_md_suggestions: Array<{
    section: string;
    content: string;
    rationale: string;
  }> | null;
  decomposition_hints: Array<{
    hint_type: string;
    title: string;
    description: string;
  }> | null;
  adr_recommendations: Array<{
    title: string;
    description: string;
    priority: string;
  }> | null;
  status: string;
  processed_at: string | null;
  applied_at: string | null;
  rejection_reason: string | null;
  processed_by: string | null;
  ai_model: string | null;
  ai_processing_time_ms: number | null;
  created_at: string;
  updated_at: string;
}

/**
 * Learning list response with pagination
 */
export interface LearningListResponse {
  items: PRLearning[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

/**
 * Hints list response with pagination
 */
export interface HintListResponse {
  items: DecompositionHint[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

/**
 * Aggregation list response with pagination
 */
export interface AggregationListResponse {
  items: LearningAggregation[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

/**
 * Learning filter parameters
 */
export interface LearningFilterParams {
  feedback_type?: FeedbackType;
  severity?: Severity;
  status?: LearningStatus;
  pr_number?: number;
  applied?: boolean;
  ai_extracted?: boolean;
  date_from?: string;
  date_to?: string;
  page?: number;
  per_page?: number;
}

/**
 * Hint filter parameters
 */
export interface HintFilterParams {
  hint_type?: HintType;
  category?: string;
  status?: HintStatus;
  verified_only?: boolean;
  effective_only?: boolean;
  page?: number;
  per_page?: number;
}

/**
 * Learning statistics
 */
export interface LearningStats {
  total_learnings: number;
  by_feedback_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  ai_extracted_count: number;
  applied_to_claude_md: number;
  applied_to_decomposition: number;
  average_confidence: number | null;
  top_patterns: Array<{ pattern: string; count: number }>;
  top_files: Array<{ file: string; count: number }>;
  recent_activity: Array<{
    date: string;
    count: number;
  }>;
}

/**
 * Manual learning creation request
 */
export interface CreateLearningRequest {
  pr_number: number;
  pr_title?: string;
  pr_url?: string;
  feedback_type: FeedbackType;
  severity?: Severity;
  review_comment: string;
  original_code?: string;
  original_spec_section?: string;
  corrected_approach?: string;
  pattern_extracted?: string;
  file_path?: string;
  line_start?: number;
  line_end?: number;
  related_adr?: string;
  reviewer_github_login?: string;
  tags?: string[];
}

/**
 * Learning update request
 */
export interface UpdateLearningRequest {
  feedback_type?: FeedbackType;
  severity?: Severity;
  corrected_approach?: string;
  pattern_extracted?: string;
  related_adr?: string;
  status?: LearningStatus;
  tags?: string[];
}

/**
 * Hint creation request
 */
export interface CreateHintRequest {
  hint_type: HintType;
  category: string;
  subcategory?: string;
  title: string;
  description: string;
  example_good?: string;
  example_bad?: string;
  rationale?: string;
  applies_to?: string[];
  languages?: string[];
  frameworks?: string[];
  source_learning_id?: string;
  confidence?: number;
  tags?: string[];
  related_adrs?: string[];
}

/**
 * Hint update request
 */
export interface UpdateHintRequest {
  title?: string;
  description?: string;
  example_good?: string;
  example_bad?: string;
  rationale?: string;
  applies_to?: string[];
  languages?: string[];
  frameworks?: string[];
  confidence?: number;
  status?: HintStatus;
  deprecated_reason?: string;
  tags?: string[];
  related_adrs?: string[];
}

/**
 * Aggregation creation request
 */
export interface CreateAggregationRequest {
  period_type: AggregationPeriod;
  period_start: string;
  period_end?: string;
}

// =============================================================================
// Sprint 100 (EP-11): Learnings API Functions
// =============================================================================

/**
 * Get learnings for a project
 * Sprint 100: GET /projects/{project_id}/learnings
 */
export async function getLearnings(
  projectId: string,
  params?: LearningFilterParams
): Promise<LearningListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.feedback_type) searchParams.set("feedback_type", params.feedback_type);
  if (params?.severity) searchParams.set("severity", params.severity);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.pr_number) searchParams.set("pr_number", params.pr_number.toString());
  if (params?.applied !== undefined) searchParams.set("applied", params.applied.toString());
  if (params?.ai_extracted !== undefined)
    searchParams.set("ai_extracted", params.ai_extracted.toString());
  if (params?.date_from) searchParams.set("date_from", params.date_from);
  if (params?.date_to) searchParams.set("date_to", params.date_to);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.per_page) searchParams.set("per_page", params.per_page.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/projects/${projectId}/learnings?${queryString}`
    : `/projects/${projectId}/learnings`;

  return apiRequest<LearningListResponse>(endpoint);
}

/**
 * Get a single learning by ID
 * Sprint 100: GET /projects/{project_id}/learnings/{learning_id}
 */
export async function getLearning(
  projectId: string,
  learningId: string
): Promise<PRLearning> {
  return apiRequest<PRLearning>(`/projects/${projectId}/learnings/${learningId}`);
}

/**
 * Create a manual learning
 * Sprint 100: POST /projects/{project_id}/learnings
 */
export async function createLearning(
  projectId: string,
  data: CreateLearningRequest
): Promise<PRLearning> {
  return apiRequest<PRLearning>(`/projects/${projectId}/learnings`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a learning
 * Sprint 100: PATCH /projects/{project_id}/learnings/{learning_id}
 */
export async function updateLearning(
  projectId: string,
  learningId: string,
  data: UpdateLearningRequest
): Promise<PRLearning> {
  return apiRequest<PRLearning>(`/projects/${projectId}/learnings/${learningId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a learning
 * Sprint 100: DELETE /projects/{project_id}/learnings/{learning_id}
 */
export async function deleteLearning(
  projectId: string,
  learningId: string
): Promise<void> {
  return apiRequest<void>(`/projects/${projectId}/learnings/${learningId}`, {
    method: "DELETE",
  });
}

/**
 * Get learning statistics for a project
 * Sprint 100: GET /projects/{project_id}/learnings/stats
 */
export async function getLearningStats(projectId: string): Promise<LearningStats> {
  return apiRequest<LearningStats>(`/projects/${projectId}/learnings/stats`);
}

/**
 * Mark a learning as applied
 * Sprint 100: POST /projects/{project_id}/learnings/{learning_id}/apply
 */
export async function applyLearning(
  projectId: string,
  learningId: string,
  target: "claude_md" | "decomposition" | "both"
): Promise<PRLearning> {
  return apiRequest<PRLearning>(
    `/projects/${projectId}/learnings/${learningId}/apply`,
    {
      method: "POST",
      body: JSON.stringify({ target }),
    }
  );
}

// =============================================================================
// Sprint 100 (EP-11): Hints API Functions
// =============================================================================

/**
 * Get decomposition hints for a project
 * Sprint 100: GET /projects/{project_id}/hints
 */
export async function getHints(
  projectId: string,
  params?: HintFilterParams
): Promise<HintListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.hint_type) searchParams.set("hint_type", params.hint_type);
  if (params?.category) searchParams.set("category", params.category);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.verified_only) searchParams.set("verified_only", "true");
  if (params?.effective_only) searchParams.set("effective_only", "true");
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.per_page) searchParams.set("per_page", params.per_page.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/projects/${projectId}/hints?${queryString}`
    : `/projects/${projectId}/hints`;

  return apiRequest<HintListResponse>(endpoint);
}

/**
 * Get a single hint by ID
 * Sprint 100: GET /projects/{project_id}/hints/{hint_id}
 */
export async function getHint(projectId: string, hintId: string): Promise<DecompositionHint> {
  return apiRequest<DecompositionHint>(`/projects/${projectId}/hints/${hintId}`);
}

/**
 * Create a new hint
 * Sprint 100: POST /projects/{project_id}/hints
 */
export async function createHint(
  projectId: string,
  data: CreateHintRequest
): Promise<DecompositionHint> {
  return apiRequest<DecompositionHint>(`/projects/${projectId}/hints`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a hint
 * Sprint 100: PATCH /projects/{project_id}/hints/{hint_id}
 */
export async function updateHint(
  projectId: string,
  hintId: string,
  data: UpdateHintRequest
): Promise<DecompositionHint> {
  return apiRequest<DecompositionHint>(`/projects/${projectId}/hints/${hintId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Verify a hint (human review)
 * Sprint 100: POST /projects/{project_id}/hints/{hint_id}/verify
 */
export async function verifyHint(projectId: string, hintId: string): Promise<DecompositionHint> {
  return apiRequest<DecompositionHint>(`/projects/${projectId}/hints/${hintId}/verify`, {
    method: "POST",
  });
}

/**
 * Record hint usage during decomposition
 * Sprint 100: POST /projects/{project_id}/hints/{hint_id}/usage
 */
export async function recordHintUsage(
  projectId: string,
  hintId: string,
  data: {
    decomposition_session_id?: string;
    task_description?: string;
    plan_generated?: string;
  }
): Promise<{ usage_id: string; hint_id: string }> {
  return apiRequest<{ usage_id: string; hint_id: string }>(
    `/projects/${projectId}/hints/${hintId}/usage`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

/**
 * Provide feedback on hint usage
 * Sprint 100: POST /projects/{project_id}/hints/{hint_id}/feedback
 */
export async function provideHintFeedback(
  projectId: string,
  hintId: string,
  data: {
    usage_id: string;
    outcome: "prevented_error" | "no_effect" | "false_positive";
    feedback?: string;
    pr_id?: number;
  }
): Promise<DecompositionHint> {
  return apiRequest<DecompositionHint>(
    `/projects/${projectId}/hints/${hintId}/feedback`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

/**
 * Get active hints for decomposition
 * Sprint 100: GET /projects/{project_id}/hints/active
 */
export async function getActiveHints(
  projectId: string,
  context?: {
    applies_to?: string[];
    languages?: string[];
    frameworks?: string[];
    min_confidence?: number;
  }
): Promise<DecompositionHint[]> {
  const searchParams = new URLSearchParams();
  if (context?.applies_to) searchParams.set("applies_to", context.applies_to.join(","));
  if (context?.languages) searchParams.set("languages", context.languages.join(","));
  if (context?.frameworks) searchParams.set("frameworks", context.frameworks.join(","));
  if (context?.min_confidence)
    searchParams.set("min_confidence", context.min_confidence.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/projects/${projectId}/hints/active?${queryString}`
    : `/projects/${projectId}/hints/active`;

  return apiRequest<DecompositionHint[]>(endpoint);
}

// =============================================================================
// Sprint 100 (EP-11): Aggregations API Functions
// =============================================================================

/**
 * Get learning aggregations for a project
 * Sprint 100: GET /projects/{project_id}/aggregations
 */
export async function getAggregations(
  projectId: string,
  params?: {
    period_type?: AggregationPeriod;
    status?: string;
    page?: number;
    per_page?: number;
  }
): Promise<AggregationListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.period_type) searchParams.set("period_type", params.period_type);
  if (params?.status) searchParams.set("status", params.status);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.per_page) searchParams.set("per_page", params.per_page.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/projects/${projectId}/aggregations?${queryString}`
    : `/projects/${projectId}/aggregations`;

  return apiRequest<AggregationListResponse>(endpoint);
}

/**
 * Get a single aggregation by ID
 * Sprint 100: GET /projects/{project_id}/aggregations/{aggregation_id}
 */
export async function getAggregation(
  projectId: string,
  aggregationId: string
): Promise<LearningAggregation> {
  return apiRequest<LearningAggregation>(
    `/projects/${projectId}/aggregations/${aggregationId}`
  );
}

/**
 * Create a new aggregation
 * Sprint 100: POST /projects/{project_id}/aggregations
 */
export async function createAggregation(
  projectId: string,
  data: CreateAggregationRequest
): Promise<LearningAggregation> {
  return apiRequest<LearningAggregation>(`/projects/${projectId}/aggregations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Apply an aggregation (implement suggestions)
 * Sprint 100: POST /projects/{project_id}/aggregations/{aggregation_id}/apply
 */
export async function applyAggregation(
  projectId: string,
  aggregationId: string
): Promise<LearningAggregation> {
  return apiRequest<LearningAggregation>(
    `/projects/${projectId}/aggregations/${aggregationId}/apply`,
    { method: "POST" }
  );
}

/**
 * Reject an aggregation
 * Sprint 100: POST /projects/{project_id}/aggregations/{aggregation_id}/reject
 */
export async function rejectAggregation(
  projectId: string,
  aggregationId: string,
  reason: string
): Promise<LearningAggregation> {
  return apiRequest<LearningAggregation>(
    `/projects/${projectId}/aggregations/${aggregationId}/reject`,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    }
  );
}

// =============================================================================
// CEO Dashboard API (Sprint 110)
// =============================================================================

import type {
  CEODashboardSummary,
  TimeSavedMetrics,
  RoutingBreakdown,
  PendingDecision,
  WeeklySummary,
  TimeSavedTrendPoint,
  VibecodingTrendPoint,
  TopRejection,
  CEOOverride,
  SystemHealth,
  TimeRange,
  ResolveDecisionRequest,
  RecordOverrideRequest,
  CEODashboardHealth,
} from "./types/ceo-dashboard";

export type {
  CEODashboardSummary,
  TimeSavedMetrics,
  RoutingBreakdown,
  PendingDecision,
  WeeklySummary,
  TimeSavedTrendPoint,
  VibecodingTrendPoint,
  TopRejection,
  CEOOverride,
  SystemHealth,
  TimeRange,
  ResolveDecisionRequest,
  RecordOverrideRequest,
  CEODashboardHealth,
};

/**
 * Get complete CEO dashboard summary
 * Sprint 110: GET /ceo-dashboard/summary
 */
export async function getCEODashboardSummary(options?: {
  projectId?: string;
  timeRange?: TimeRange;
}): Promise<CEODashboardSummary> {
  const params = new URLSearchParams();
  if (options?.projectId) params.set("project_id", options.projectId);
  if (options?.timeRange) params.set("time_range", options.timeRange);
  const query = params.toString();
  return apiRequest<CEODashboardSummary>(
    `/ceo-dashboard/summary${query ? `?${query}` : ""}`
  );
}

/**
 * Get CEO time saved metrics
 * Sprint 110: GET /ceo-dashboard/time-saved
 */
export async function getCEOTimeSaved(
  timeRange: TimeRange = "this_week"
): Promise<TimeSavedMetrics> {
  return apiRequest<TimeSavedMetrics>(
    `/ceo-dashboard/time-saved?time_range=${timeRange}`
  );
}

/**
 * Get PR routing breakdown
 * Sprint 110: GET /ceo-dashboard/routing-breakdown
 */
export async function getCEORoutingBreakdown(options?: {
  projectId?: string;
  timeRange?: TimeRange;
}): Promise<RoutingBreakdown> {
  const params = new URLSearchParams();
  if (options?.projectId) params.set("project_id", options.projectId);
  if (options?.timeRange) params.set("time_range", options.timeRange);
  const query = params.toString();
  return apiRequest<RoutingBreakdown>(
    `/ceo-dashboard/routing-breakdown${query ? `?${query}` : ""}`
  );
}

/**
 * Get pending CEO decisions queue
 * Sprint 110: GET /ceo-dashboard/pending-decisions
 */
export async function getCEOPendingDecisions(options?: {
  projectId?: string;
  limit?: number;
}): Promise<PendingDecision[]> {
  const params = new URLSearchParams();
  if (options?.projectId) params.set("project_id", options.projectId);
  if (options?.limit) params.set("limit", options.limit.toString());
  const query = params.toString();
  return apiRequest<PendingDecision[]>(
    `/ceo-dashboard/pending-decisions${query ? `?${query}` : ""}`
  );
}

/**
 * Get weekly governance summary
 * Sprint 110: GET /ceo-dashboard/weekly-summary
 */
export async function getCEOWeeklySummary(): Promise<WeeklySummary> {
  return apiRequest<WeeklySummary>("/ceo-dashboard/weekly-summary");
}

/**
 * Get time saved trend (8 weeks)
 * Sprint 110: GET /ceo-dashboard/trends/time-saved
 */
export async function getCEOTimeSavedTrend(): Promise<TimeSavedTrendPoint[]> {
  return apiRequest<TimeSavedTrendPoint[]>("/ceo-dashboard/trends/time-saved");
}

/**
 * Get vibecoding index trend (7 days)
 * Sprint 110: GET /ceo-dashboard/trends/vibecoding-index
 */
export async function getCEOVibecodingTrend(
  projectId?: string
): Promise<VibecodingTrendPoint[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return apiRequest<VibecodingTrendPoint[]>(
    `/ceo-dashboard/trends/vibecoding-index${query}`
  );
}

/**
 * Get top rejection reasons
 * Sprint 110: GET /ceo-dashboard/top-rejections
 */
export async function getCEOTopRejections(options?: {
  projectId?: string;
  timeRange?: TimeRange;
}): Promise<TopRejection[]> {
  const params = new URLSearchParams();
  if (options?.projectId) params.set("project_id", options.projectId);
  if (options?.timeRange) params.set("time_range", options.timeRange);
  const query = params.toString();
  return apiRequest<TopRejection[]>(
    `/ceo-dashboard/top-rejections${query ? `?${query}` : ""}`
  );
}

/**
 * Get CEO overrides this week
 * Sprint 110: GET /ceo-dashboard/overrides
 */
export async function getCEOOverrides(): Promise<CEOOverride[]> {
  return apiRequest<CEOOverride[]>("/ceo-dashboard/overrides");
}

/**
 * Get system health snapshot
 * Sprint 110: GET /ceo-dashboard/system-health
 */
export async function getCEOSystemHealth(): Promise<SystemHealth> {
  return apiRequest<SystemHealth>("/ceo-dashboard/system-health");
}

/**
 * Resolve pending CEO decision
 * Sprint 110: POST /ceo-dashboard/decisions/{submission_id}/resolve
 */
export async function resolveCEODecision(
  submissionId: string,
  request: ResolveDecisionRequest
): Promise<{ status: string; submission_id: string; decision: string }> {
  return apiRequest(
    `/ceo-dashboard/decisions/${submissionId}/resolve`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Record CEO override for calibration
 * Sprint 110: POST /ceo-dashboard/decisions/{submission_id}/override
 */
export async function recordCEOOverride(
  submissionId: string,
  request: RecordOverrideRequest
): Promise<{ status: string; submission_id: string; override_type: string }> {
  return apiRequest(
    `/ceo-dashboard/decisions/${submissionId}/override`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * CEO Dashboard health check
 * Sprint 110: GET /ceo-dashboard/health
 */
export async function getCEODashboardHealth(): Promise<CEODashboardHealth> {
  return apiRequest<CEODashboardHealth>("/ceo-dashboard/health");
}

// =============================================================================
// Auto-Generation API (Sprint 113)
// =============================================================================

import type {
  GenerateIntentRequest,
  GenerateIntentResponse,
  SuggestOwnershipRequest,
  OwnershipSuggestionResponse,
  BatchOwnershipRequest,
  BatchOwnershipResponse,
  AttachContextRequest,
  AttachContextResponse,
  PreFillAttestationRequest,
  PreFillAttestationResponse,
  SubmitAttestationRequest,
  AttestationForm,
  AutoGenerationMetrics,
  RecentAutoGeneration,
  AutoGenerationHealth,
} from "@/lib/types/auto-generation";

/**
 * Generate intent skeleton from task
 * Sprint 113: POST /governance/auto-generate/intent
 *
 * Goal: Reduce intent document creation from ~15 min to <1 min
 */
export async function generateIntentSkeleton(
  request: GenerateIntentRequest
): Promise<GenerateIntentResponse> {
  return apiRequest<GenerateIntentResponse>(
    "/governance/auto-generate/intent",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
    30000 // 30s timeout for LLM operations
  );
}

/**
 * Suggest ownership for a file
 * Sprint 113: POST /governance/auto-generate/ownership
 *
 * Goal: Reduce ownership annotation from ~2 min to <30 sec
 */
export async function suggestOwnership(
  request: SuggestOwnershipRequest
): Promise<OwnershipSuggestionResponse> {
  return apiRequest<OwnershipSuggestionResponse>(
    "/governance/auto-generate/ownership",
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Suggest ownership for multiple files
 * Sprint 113: POST /governance/auto-generate/ownership/batch
 */
export async function suggestOwnershipBatch(
  request: BatchOwnershipRequest
): Promise<BatchOwnershipResponse> {
  return apiRequest<BatchOwnershipResponse>(
    "/governance/auto-generate/ownership/batch",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
    15000 // 15s timeout for batch
  );
}

/**
 * Auto-attach context (ADRs, specs) to PR
 * Sprint 113: POST /governance/auto-generate/context
 *
 * Goal: Reduce context attachment from ~5 min to automatic
 */
export async function attachContext(
  request: AttachContextRequest
): Promise<AttachContextResponse> {
  return apiRequest<AttachContextResponse>(
    "/governance/auto-generate/context",
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Pre-fill AI attestation form
 * Sprint 113: POST /governance/auto-generate/attestation
 *
 * Goal: Reduce attestation from ~8 min to ~2 min (human confirmation only)
 */
export async function preFillAttestation(
  request: PreFillAttestationRequest
): Promise<PreFillAttestationResponse> {
  return apiRequest<PreFillAttestationResponse>(
    "/governance/auto-generate/attestation",
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Submit completed attestation
 * Sprint 113: POST /governance/attestations/{id}/submit
 */
export async function submitAttestation(
  request: SubmitAttestationRequest
): Promise<AttestationForm> {
  return apiRequest<AttestationForm>(
    `/governance/attestations/${request.attestation_id}/submit`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Get attestation by ID
 * Sprint 113: GET /governance/attestations/{id}
 */
export async function getAttestation(
  attestationId: string
): Promise<AttestationForm> {
  return apiRequest<AttestationForm>(
    `/governance/attestations/${attestationId}`
  );
}

/**
 * Get auto-generation usage metrics
 * Sprint 113: GET /governance/auto-generate/metrics
 */
export async function getAutoGenerationMetrics(options?: {
  projectId?: string;
  timeRange?: string;
}): Promise<AutoGenerationMetrics> {
  const params = new URLSearchParams();
  if (options?.projectId) params.append("project_id", options.projectId);
  if (options?.timeRange) params.append("time_range", options.timeRange);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<AutoGenerationMetrics>(
    `/governance/auto-generate/metrics${query}`
  );
}

/**
 * Get recent auto-generation activity
 * Sprint 113: GET /governance/auto-generate/recent
 */
export async function getRecentAutoGenerations(options?: {
  projectId?: string;
  limit?: number;
}): Promise<RecentAutoGeneration[]> {
  const params = new URLSearchParams();
  if (options?.projectId) params.append("project_id", options.projectId);
  if (options?.limit) params.append("limit", options.limit.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<RecentAutoGeneration[]>(
    `/governance/auto-generate/recent${query}`
  );
}

/**
 * Get auto-generation health status
 * Sprint 113: GET /governance/auto-generate/health
 */
export async function getAutoGenerationHealth(): Promise<AutoGenerationHealth> {
  return apiRequest<AutoGenerationHealth>("/governance/auto-generate/health");
}

// =============================================================================
// Kill Switch & Governance Mode API (Sprint 113)
// =============================================================================

import type {
  GovernanceModeStatus,
  SetGovernanceModeRequest,
  SetGovernanceModeResponse,
  KillSwitchResult,
  TriggerRollbackRequest,
  TriggerRollbackResponse,
  BreakGlassRequest,
  CreateBreakGlassRequest,
  CreateBreakGlassResponse,
  ResolveBreakGlassRequest,
  GetAuditLogRequest,
  AuditLogResponse,
  ModeHistoryResponse,
  KillSwitchDashboard,
} from "@/lib/types/kill-switch";

/**
 * Get current governance mode
 * Sprint 113: GET /governance/mode
 */
export async function getGovernanceMode(): Promise<GovernanceModeStatus> {
  return apiRequest<GovernanceModeStatus>("/governance/mode");
}

/**
 * Set governance mode
 * Sprint 113: POST /governance/mode
 *
 * Requires: CTO or CEO role
 */
export async function setGovernanceMode(
  request: SetGovernanceModeRequest
): Promise<SetGovernanceModeResponse> {
  return apiRequest<SetGovernanceModeResponse>("/governance/mode", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Check kill switch criteria
 * Sprint 113: GET /governance/kill-switch/check
 */
export async function checkKillSwitch(): Promise<KillSwitchResult> {
  return apiRequest<KillSwitchResult>("/governance/kill-switch/check");
}

/**
 * Trigger governance rollback
 * Sprint 113: POST /governance/kill-switch/rollback
 *
 * Requires: CTO or CEO role
 */
export async function triggerRollback(
  request: TriggerRollbackRequest
): Promise<TriggerRollbackResponse> {
  return apiRequest<TriggerRollbackResponse>("/governance/kill-switch/rollback", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Get break glass requests
 * Sprint 113: GET /governance/break-glass
 */
export async function getBreakGlassRequests(options?: {
  status?: string;
  limit?: number;
}): Promise<BreakGlassRequest[]> {
  const params = new URLSearchParams();
  if (options?.status) params.append("status", options.status);
  if (options?.limit) params.append("limit", options.limit.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<BreakGlassRequest[]>(`/governance/break-glass${query}`);
}

/**
 * Create break glass request
 * Sprint 113: POST /governance/break-glass
 */
export async function createBreakGlass(
  request: CreateBreakGlassRequest
): Promise<CreateBreakGlassResponse> {
  return apiRequest<CreateBreakGlassResponse>("/governance/break-glass", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Approve or reject break glass request
 * Sprint 113: POST /governance/break-glass/{id}/resolve
 */
export async function resolveBreakGlass(
  requestId: string,
  request: ResolveBreakGlassRequest
): Promise<BreakGlassRequest> {
  return apiRequest<BreakGlassRequest>(
    `/governance/break-glass/${requestId}/resolve`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

/**
 * Get governance mode history
 * Sprint 113: GET /governance/mode/history
 */
export async function getModeHistory(options?: {
  limit?: number;
}): Promise<ModeHistoryResponse> {
  const params = new URLSearchParams();
  if (options?.limit) params.append("limit", options.limit.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<ModeHistoryResponse>(`/governance/mode/history${query}`);
}

/**
 * Get governance audit log
 * Sprint 113: GET /governance/audit-log
 */
export async function getGovernanceAuditLog(
  request?: GetAuditLogRequest
): Promise<AuditLogResponse> {
  const params = new URLSearchParams();
  if (request?.type) params.append("type", request.type);
  if (request?.actor) params.append("actor", request.actor);
  if (request?.from_date) params.append("from_date", request.from_date);
  if (request?.to_date) params.append("to_date", request.to_date);
  if (request?.limit) params.append("limit", request.limit.toString());
  if (request?.offset) params.append("offset", request.offset.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<AuditLogResponse>(`/governance/audit-log${query}`);
}

/**
 * Get kill switch admin dashboard data
 * Sprint 113: GET /governance/kill-switch/dashboard
 */
export async function getKillSwitchDashboard(): Promise<KillSwitchDashboard> {
  return apiRequest<KillSwitchDashboard>("/governance/kill-switch/dashboard");
}

// =============================================================================
// Sprint 151: VCR (Version Controlled Resolution) - SASE Artifacts Enhancement
// =============================================================================

/**
 * VCR Status enum matching backend VCRStatus
 */
export type VCRStatus = "draft" | "submitted" | "approved" | "rejected";

/**
 * VCR User Summary for responses
 */
export interface VCRUserSummary {
  id: string;
  name: string;
  email: string;
}

/**
 * VCR (Version Controlled Resolution) interface
 */
export interface VCR {
  id: string;
  project_id: string;
  pr_number?: number;
  pr_url?: string;
  title: string;
  problem_statement: string;
  root_cause_analysis?: string;
  solution_approach: string;
  implementation_notes?: string;
  evidence_ids: string[];
  adr_ids: string[];
  ai_generated_percentage: number;
  ai_tools_used: string[];
  ai_generation_details: Record<string, unknown>;
  status: VCRStatus;
  created_by_id?: string;
  approved_by_id?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
  approved_at?: string;
  created_by?: VCRUserSummary;
  approved_by?: VCRUserSummary;
}

/**
 * VCR Create request
 */
export interface VCRCreate {
  project_id: string;
  pr_number?: number;
  pr_url?: string;
  title: string;
  problem_statement: string;
  root_cause_analysis?: string;
  solution_approach: string;
  implementation_notes?: string;
  evidence_ids?: string[];
  adr_ids?: string[];
  ai_generated_percentage?: number;
  ai_tools_used?: string[];
  ai_generation_details?: Record<string, unknown>;
}

/**
 * VCR Update request
 */
export interface VCRUpdate {
  title?: string;
  problem_statement?: string;
  root_cause_analysis?: string;
  solution_approach?: string;
  implementation_notes?: string;
  evidence_ids?: string[];
  adr_ids?: string[];
  ai_generated_percentage?: number;
  ai_tools_used?: string[];
  ai_generation_details?: Record<string, unknown>;
  pr_number?: number;
  pr_url?: string;
}

/**
 * VCR Reject request
 */
export interface VCRRejectRequest {
  reason: string;
}

/**
 * VCR List response (paginated)
 */
export interface VCRListResponse {
  items: VCR[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * VCR Statistics response
 */
export interface VCRStats {
  total: number;
  draft: number;
  submitted: number;
  approved: number;
  rejected: number;
  avg_approval_time_hours?: number;
  ai_involvement_percentage: number;
}

/**
 * VCR Auto-generate request - Sprint 151 Day 4
 * Matches backend SASEGenerationService.generate_vcr parameters
 */
export interface VCRAutoGenerateRequest {
  pr_diff: string;
  commit_messages: string[];
  pr_title?: string;
  pr_description?: string;
  branch_name?: string;
  file_paths?: string[];
}

/**
 * VCR Auto-generate response - Sprint 151 Day 4
 * Matches backend VCRGenerationResult
 */
export interface VCRAutoGenerateResponse {
  title: string;
  problem_statement: string;
  root_cause_analysis: string | null;
  solution_approach: string;
  implementation_notes: string | null;
  ai_generated_percentage: number;
  ai_tools_used: string[];
  ai_tool_context: Record<string, unknown> | null;
  confidence: number;
  generation_time_ms: number;
  provider_used: string;
  fallback_used: boolean;
}

/**
 * VCR List query options
 */
export interface VCRListOptions {
  project_id?: string;
  status?: VCRStatus;
  created_by_id?: string;
  limit?: number;
  offset?: number;
}

/**
 * Get VCRs with optional filters
 * Sprint 151: GET /vcr
 */
export async function getVcrs(options?: VCRListOptions): Promise<VCRListResponse> {
  const params = new URLSearchParams();
  if (options?.project_id) params.append("project_id", options.project_id);
  if (options?.status) params.append("status", options.status);
  if (options?.created_by_id) params.append("created_by_id", options.created_by_id);
  if (options?.limit) params.append("limit", options.limit.toString());
  if (options?.offset) params.append("offset", options.offset.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<VCRListResponse>(`/vcr${query}`);
}

/**
 * Get a single VCR by ID
 * Sprint 151: GET /vcr/{vcr_id}
 */
export async function getVcr(vcrId: string): Promise<VCR> {
  return apiRequest<VCR>(`/vcr/${vcrId}`);
}

/**
 * Create a new VCR
 * Sprint 151: POST /vcr
 */
export async function createVcr(data: VCRCreate): Promise<VCR> {
  return apiRequest<VCR>("/vcr", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a VCR (draft only)
 * Sprint 151: PUT /vcr/{vcr_id}
 */
export async function updateVcr(vcrId: string, data: VCRUpdate): Promise<VCR> {
  return apiRequest<VCR>(`/vcr/${vcrId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a VCR (draft only)
 * Sprint 151: DELETE /vcr/{vcr_id}
 */
export async function deleteVcr(vcrId: string): Promise<{ success: boolean; message: string }> {
  return apiRequest<{ success: boolean; message: string }>(`/vcr/${vcrId}`, {
    method: "DELETE",
  });
}

/**
 * Submit a VCR for approval
 * Sprint 151: POST /vcr/{vcr_id}/submit
 */
export async function submitVcr(vcrId: string): Promise<VCR> {
  return apiRequest<VCR>(`/vcr/${vcrId}/submit`, {
    method: "POST",
  });
}

/**
 * Approve a VCR (CTO/CEO only)
 * Sprint 151: POST /vcr/{vcr_id}/approve
 */
export async function approveVcr(vcrId: string): Promise<VCR> {
  return apiRequest<VCR>(`/vcr/${vcrId}/approve`, {
    method: "POST",
  });
}

/**
 * Reject a VCR (CTO/CEO only)
 * Sprint 151: POST /vcr/{vcr_id}/reject
 */
export async function rejectVcr(vcrId: string, request: VCRRejectRequest): Promise<VCR> {
  return apiRequest<VCR>(`/vcr/${vcrId}/reject`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Reopen a rejected VCR
 * Sprint 151: POST /vcr/{vcr_id}/reopen
 */
export async function reopenVcr(vcrId: string): Promise<VCR> {
  return apiRequest<VCR>(`/vcr/${vcrId}/reopen`, {
    method: "POST",
  });
}

/**
 * Get VCR statistics for a project
 * Sprint 151: GET /vcr/stats/{project_id}
 */
export async function getVcrStats(projectId: string): Promise<VCRStats> {
  return apiRequest<VCRStats>(`/vcr/stats/${projectId}`);
}

/**
 * Auto-generate VCR content using AI
 * Sprint 151: POST /vcr/auto-generate
 */
export async function autoGenerateVcr(
  request: VCRAutoGenerateRequest
): Promise<VCRAutoGenerateResponse> {
  return apiRequest<VCRAutoGenerateResponse>("/vcr/auto-generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Sprint 151: CRP (Consultation Request Protocol) - SASE Artifacts Enhancement
// Backend already exists from Sprint 101, this adds frontend types
// =============================================================================

/**
 * CRP Status enum matching backend ConsultationStatus
 */
export type CRPStatus = "pending" | "in_review" | "approved" | "rejected" | "cancelled" | "expired";

/**
 * CRP Priority enum matching backend ConsultationPriority
 */
export type CRPPriority = "low" | "medium" | "high" | "urgent";

/**
 * Reviewer Expertise enum
 */
export type ReviewerExpertise = "security" | "database" | "api" | "architecture" | "concurrency" | "general";

/**
 * CRP Comment interface
 */
export interface CRPComment {
  id: string;
  consultation_id: string;
  user_id: string;
  user_name?: string;
  comment: string;
  is_resolution_note: boolean;
  created_at: string;
}

/**
 * Risk Analysis interface (simplified for frontend)
 */
export interface RiskAnalysis {
  id: string;
  risk_score: number;
  risk_factors: string[];
  recommendation: string;
}

/**
 * CRP (Consultation Request Protocol) interface
 */
export interface CRP {
  id: string;
  project_id: string;
  pr_id?: string;
  risk_analysis_id: string;
  risk_analysis?: RiskAnalysis;
  title: string;
  description: string;
  priority: CRPPriority;
  required_expertise: ReviewerExpertise[];
  diff_url?: string;
  status: CRPStatus;
  requester_id: string;
  requester_name?: string;
  assigned_reviewer_id?: string;
  reviewer_name?: string;
  resolution_notes?: string;
  conditions?: string[];
  resolved_at?: string;
  resolved_by_id?: string;
  created_at: string;
  updated_at: string;
  comments?: CRPComment[];
  comment_count: number;
}

/**
 * CRP Create request
 */
export interface CRPCreate {
  project_id: string;
  pr_id?: string;
  risk_analysis_id: string;
  title: string;
  description: string;
  priority?: CRPPriority;
  required_expertise?: ReviewerExpertise[];
  diff_url?: string;
}

/**
 * CRP Assign Reviewer request
 */
export interface CRPAssignRequest {
  reviewer_id: string;
  notes?: string;
}

/**
 * CRP Resolve request
 */
export interface CRPResolveRequest {
  status: "approved" | "rejected" | "cancelled";
  resolution_notes: string;
  conditions?: string[];
}

/**
 * CRP Add Comment request
 */
export interface CRPAddCommentRequest {
  comment: string;
  is_resolution_note?: boolean;
}

/**
 * CRP List response (paginated)
 */
export interface CRPListResponse {
  consultations: CRP[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * CRP List query options
 */
export interface CRPListOptions {
  project_id?: string;
  status?: CRPStatus;
  priority?: CRPPriority;
  requester_id?: string;
  reviewer_id?: string;
  expertise?: ReviewerExpertise;
  search?: string;
  page?: number;
  page_size?: number;
}

/**
 * CRP Auto-Generate Request - Sprint 151 Day 4
 * Used for AI-assisted CRP content generation
 */
export interface CRPAutoGenerateRequest {
  context: string;
  code_snippet?: string;
  related_files?: string[];
  project_tech_stack?: string[];
}

/**
 * Option considered for CRP - Sprint 151 Day 4
 */
export interface CRPOption {
  name: string;
  description: string;
  pros: string[];
  cons: string[];
  complexity: string;
  risk_level: string;
}

/**
 * CRP Auto-Generate Response - Sprint 151 Day 4
 * Contains AI-generated CRP content
 */
export interface CRPAutoGenerateResponse {
  title: string;
  question: string;
  context: string;
  options_considered: CRPOption[];
  recommendation: string | null;
  impact_assessment: string;
  required_expertise: string[];
  priority_suggestion: string;
  confidence: number;
  generation_time_ms: number;
  provider_used: string;
  fallback_used: boolean;
}

/**
 * Get CRPs with optional filters
 * Sprint 151: GET /consultations
 */
export async function getCrps(options?: CRPListOptions): Promise<CRPListResponse> {
  const params = new URLSearchParams();
  if (options?.project_id) params.append("project_id", options.project_id);
  if (options?.status) params.append("status", options.status);
  if (options?.priority) params.append("priority", options.priority);
  if (options?.requester_id) params.append("requester_id", options.requester_id);
  if (options?.reviewer_id) params.append("reviewer_id", options.reviewer_id);
  if (options?.expertise) params.append("expertise", options.expertise);
  if (options?.search) params.append("search", options.search);
  if (options?.page) params.append("page", options.page.toString());
  if (options?.page_size) params.append("page_size", options.page_size.toString());
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiRequest<CRPListResponse>(`/consultations${query}`);
}

/**
 * Get a single CRP by ID
 * Sprint 151: GET /consultations/{id}
 */
export async function getCrp(crpId: string): Promise<CRP> {
  return apiRequest<CRP>(`/consultations/${crpId}`);
}

/**
 * Create a new CRP
 * Sprint 151: POST /consultations
 */
export async function createCrp(data: CRPCreate): Promise<CRP> {
  return apiRequest<CRP>("/consultations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Assign a reviewer to a CRP
 * Sprint 151: POST /consultations/{id}/assign
 */
export async function assignCrpReviewer(crpId: string, data: CRPAssignRequest): Promise<CRP> {
  return apiRequest<CRP>(`/consultations/${crpId}/assign`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Resolve a CRP (approve/reject/cancel)
 * Sprint 151: POST /consultations/{id}/resolve
 */
export async function resolveCrp(crpId: string, data: CRPResolveRequest): Promise<CRP> {
  return apiRequest<CRP>(`/consultations/${crpId}/resolve`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Add a comment to a CRP
 * Sprint 151: POST /consultations/{id}/comments
 */
export async function addCrpComment(crpId: string, data: CRPAddCommentRequest): Promise<CRPComment> {
  return apiRequest<CRPComment>(`/consultations/${crpId}/comments`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get pending reviews for current user
 * Sprint 151: GET /consultations/my-reviews
 */
export async function getMyPendingReviews(): Promise<CRP[]> {
  return apiRequest<CRP[]>("/consultations/my-reviews");
}

/**
 * Auto-generate CRP content using AI
 * Sprint 151 Day 4: POST /consultations/auto-generate
 */
export async function autoGenerateCrp(
  request: CRPAutoGenerateRequest
): Promise<CRPAutoGenerateResponse> {
  return apiRequest<CRPAutoGenerateResponse>("/consultations/auto-generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Sprint 136: Axios-style API object for backwards compatibility with hooks
// Hooks like useGitHub and useInvitations use api.get/post/delete syntax
// =============================================================================

interface ApiResponse<T> {
  data: T;
}

/**
 * Axios-style API client object for backwards compatibility
 * Used by hooks that expect api.get/post/put/delete syntax
 */
export const api = {
  /**
   * Make a GET request
   * @param endpoint API endpoint (e.g., "/github/connection")
   */
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    const data = await apiRequest<T>(endpoint, { method: "GET" });
    return { data };
  },

  /**
   * Make a POST request
   * @param endpoint API endpoint
   * @param body Request body (will be JSON stringified)
   */
  async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    const data = await apiRequest<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
    return { data };
  },

  /**
   * Make a PUT request
   * @param endpoint API endpoint
   * @param body Request body (will be JSON stringified)
   */
  async put<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    const data = await apiRequest<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
    return { data };
  },

  /**
   * Make a PATCH request
   * @param endpoint API endpoint
   * @param body Request body (will be JSON stringified)
   */
  async patch<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    const data = await apiRequest<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
    return { data };
  },

  /**
   * Make a DELETE request
   * @param endpoint API endpoint
   */
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    const data = await apiRequest<T>(endpoint, { method: "DELETE" });
    return { data };
  },
};
