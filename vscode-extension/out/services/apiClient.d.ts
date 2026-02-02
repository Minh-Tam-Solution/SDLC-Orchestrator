/**
 * SDLC Orchestrator API Client
 *
 * Provides typed HTTP client for communicating with the SDLC Orchestrator backend.
 * Handles authentication, request/response transformation, and error handling.
 *
 * Sprint 27 Day 1 - API Client Service
 * @version 0.1.0
 */
import * as vscode from 'vscode';
import { AxiosError, AxiosRequestConfig } from 'axios';
import { AuthService } from './authService';
/**
 * API Error class for typed error handling
 */
export declare class ApiError extends Error {
    readonly statusCode: number;
    readonly statusText: string;
    readonly responseData?: unknown | undefined;
    constructor(statusCode: number, statusText: string, message: string, responseData?: unknown | undefined);
    static fromAxiosError(error: AxiosError): ApiError;
}
/**
 * Project type definition
 */
export interface Project {
    id: string;
    name: string;
    description: string;
    status: 'active' | 'archived' | 'draft';
    created_at: string;
    updated_at: string;
    owner_id: string;
    team_id?: string;
    github_repo?: string;
    current_gate?: string;
    compliance_score?: number;
}
/**
 * Gate type definition
 * Sprint 136: Fixed to match backend GateResponse schema
 * Note: status values are UPPERCASE from backend (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
 * but code may compare with lowercase - normalize when comparing
 */
export interface Gate {
    id: string;
    project_id: string;
    gate_name: string;
    name?: string;
    gate_type: string;
    stage: string;
    description: string;
    status: string;
    evidence_count: number;
    required_evidence_count: number;
    exit_criteria?: Array<{
        criterion: string;
        status: string;
    }>;
    approvals?: Array<{
        approved_by: string;
        is_approved: boolean;
        comments?: string;
    }>;
    policy_violations?: string[];
    approver_id?: string;
    created_by?: string;
    created_at: string;
    updated_at: string;
    approved_at?: string;
    deleted_at?: string;
}
/**
 * Violation type definition
 */
export interface Violation {
    id: string;
    project_id: string;
    gate_id?: string;
    gate_type?: string;
    violation_type: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    description: string;
    file_path?: string;
    line_number?: number;
    status: 'open' | 'resolved' | 'ignored' | 'false_positive';
    remediation?: string;
    created_at: string;
    resolved_at?: string;
}
/**
 * AI Recommendation response type
 */
export interface AIRecommendation {
    recommendation: string;
    confidence_score: number;
    providers_used: string[];
    council_mode: boolean;
    stage1_responses?: AIProviderResponse[];
    stage2_rankings?: PeerRanking[];
    stage3_synthesis?: ChairmanSynthesis;
    total_duration_ms: number;
    total_cost_usd?: number;
}
/**
 * AI Provider response (Stage 1)
 */
export interface AIProviderResponse {
    provider: string;
    model: string;
    response: string;
    duration_ms: number;
    error?: string;
}
/**
 * Peer ranking (Stage 2)
 */
export interface PeerRanking {
    ranker: string;
    rankings: string[];
    reasoning: string;
}
/**
 * Chairman synthesis (Stage 3)
 */
export interface ChairmanSynthesis {
    final_answer: string;
    confidence: number;
    reasoning: string;
    dissenting_opinions?: string[];
}
/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}
/**
 * API Client for SDLC Orchestrator backend
 */
export declare class ApiClient {
    private client;
    private authService;
    private baseUrl;
    constructor(_context: vscode.ExtensionContext, authService: AuthService);
    /**
     * Updates the base URL for API requests
     */
    updateBaseUrl(newUrl: string): void;
    /**
     * Sets up request/response interceptors
     */
    private setupInterceptors;
    /**
     * Makes a typed GET request
     */
    get<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T>;
    /**
     * Makes a typed POST request
     */
    post<T>(endpoint: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
    /**
     * Makes a typed DELETE request
     */
    delete<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T>;
    /**
     * Makes a typed PUT request
     */
    put<T>(endpoint: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
    /**
     * Gets list of projects accessible to the current user
     */
    getProjects(page?: number, pageSize?: number): Promise<Project[]>;
    /**
     * Gets a single project by ID
     */
    getProject(projectId: string): Promise<Project>;
    /**
     * Updates a project (Sprint 136 - Sync local state to backend)
     */
    updateProject(projectId: string, data: {
        name?: string;
        description?: string;
        current_stage?: string;
        gate_status?: string;
        sprint_number?: number;
        sprint_goal?: string;
        tier?: string;
    }): Promise<Project>;
    /**
     * Updates project context overlay (stage, gate, sprint info)
     * This syncs local project state to backend
     */
    updateProjectContext(projectId: string, context: {
        stage_name: string;
        gate_status: string;
        sprint?: {
            number: number;
            goal: string;
            days_remaining?: number;
        };
        strict_mode?: boolean;
    }): Promise<void>;
    /**
     * Gets the currently selected project ID from configuration
     */
    getCurrentProjectId(): string | undefined;
    /**
     * Gets gates for a project
     * Sprint 136: Fixed endpoint to use /gates?project_id= instead of /projects/{id}/gates
     */
    getGates(projectId: string): Promise<Gate[]>;
    /**
     * Gets a single gate by ID
     */
    getGate(gateId: string): Promise<Gate>;
    /**
     * Gets gates for current project
     */
    getCurrentProjectGates(): Promise<Gate[]>;
    /**
     * Gets violations for a project
     */
    getViolations(projectId: string, status?: string, severity?: string): Promise<Violation[]>;
    /**
     * Gets a single violation by ID
     */
    getViolation(violationId: string): Promise<Violation>;
    /**
     * Gets violations for current project
     */
    getCurrentProjectViolations(status?: string, severity?: string): Promise<Violation[]>;
    /**
     * Gets AI recommendation for a violation
     *
     * @param violationId - ID of the violation to get recommendation for
     * @param councilMode - If true, uses 3-stage AI Council deliberation
     */
    getAIRecommendation(violationId: string, councilMode?: boolean): Promise<AIRecommendation>;
    /**
     * Gets AI Council deliberation status for an async request
     */
    getCouncilStatus(requestId: string): Promise<{
        status: 'pending' | 'processing' | 'completed' | 'failed';
        result?: AIRecommendation;
        error?: string;
    }>;
    /**
     * Gets AI Council deliberation history for a project
     */
    getCouncilHistory(projectId: string, limit?: number): Promise<{
        id: string;
        violation_id: string;
        recommendation: string;
        confidence_score: number;
        created_at: string;
    }[]>;
    /**
     * Triggers a compliance scan for a project
     */
    triggerComplianceScan(projectId: string): Promise<{
        scan_id: string;
        status: string;
        message: string;
    }>;
    /**
     * Gets compliance scan status
     */
    getScanStatus(scanId: string): Promise<{
        status: 'pending' | 'running' | 'completed' | 'failed';
        progress: number;
        violations_found: number;
        completed_at?: string;
    }>;
    /**
     * Gets current user profile
     */
    getCurrentUser(): Promise<{
        id: string;
        email: string;
        username: string;
        full_name: string;
        role: string;
        team_id?: string;
    }>;
    /**
     * Validates the current token
     */
    validateToken(): Promise<boolean>;
    /**
     * Gets the base URL for API requests
     */
    getBaseUrl(): string;
    /**
     * Initialize a new SDLC project on the server
     */
    initProject(data: {
        name: string;
        tier: string;
        source: string;
    }): Promise<{
        project_id: string;
        config: unknown;
    }>;
    /**
     * Get SDLC structure template for a tier
     */
    getSDLCTemplate(tier: string): Promise<{
        folders: string[];
        files: {
            path: string;
            content: string;
        }[];
    }>;
    /**
     * Gets SDLC context overlay for a project
     *
     * Returns current stage, gate status, sprint info, and active constraints.
     * This is the same data posted to GitHub Check Runs.
     *
     * @param projectId - Project ID to get context for
     * @returns Context overlay with stage, gate, sprint, and constraints
     */
    getContextOverlay(projectId: string): Promise<{
        project_id: string;
        stage_name: string;
        gate_status: string;
        strict_mode: boolean;
        sprint?: {
            number: number;
            goal: string;
            days_remaining: number;
            start_date?: string;
            end_date?: string;
        };
        constraints: Array<{
            type: string;
            severity: 'info' | 'warning' | 'error';
            message: string;
            affected_files?: string[];
        }>;
        generated_at: string;
        formatted?: {
            pr_comment?: string;
            cli?: string;
        };
    }>;
    /**
     * Triggers context refresh for a project
     *
     * Forces re-evaluation of gate status and constraints.
     *
     * @param projectId - Project ID to refresh context for
     */
    refreshContextOverlay(projectId: string): Promise<{
        success: boolean;
        message: string;
    }>;
}
//# sourceMappingURL=apiClient.d.ts.map