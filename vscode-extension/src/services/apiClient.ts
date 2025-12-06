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
import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { AuthService } from './authService';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';

/**
 * API Error class for typed error handling
 */
export class ApiError extends Error {
    constructor(
        public readonly statusCode: number,
        public readonly statusText: string,
        message: string,
        public readonly responseData?: unknown
    ) {
        super(message);
        this.name = 'ApiError';
    }

    static fromAxiosError(error: AxiosError): ApiError {
        const statusCode = error.response?.status ?? 0;
        const statusText = error.response?.statusText ?? 'Network Error';
        const message =
            (error.response?.data as { detail?: string })?.detail ??
            error.message ??
            'Unknown error';
        return new ApiError(statusCode, statusText, message, error.response?.data);
    }
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
 */
export interface Gate {
    id: string;
    project_id: string;
    gate_type: string;
    name: string;
    description: string;
    status: 'not_started' | 'in_progress' | 'pending_approval' | 'approved' | 'rejected';
    evidence_count: number;
    required_evidence_count: number;
    approver_id?: string;
    approved_at?: string;
    created_at: string;
    updated_at: string;
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
export class ApiClient {
    private client: AxiosInstance;
    private authService: AuthService;
    private baseUrl: string;

    constructor(_context: vscode.ExtensionContext, authService: AuthService) {
        this.authService = authService;

        const config = ConfigManager.getInstance();
        this.baseUrl = config.apiUrl;

        this.client = axios.create({
            baseURL: this.baseUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'SDLC-Orchestrator-VSCode/0.1.0',
            },
        });

        this.setupInterceptors();
    }

    /**
     * Updates the base URL for API requests
     */
    updateBaseUrl(newUrl: string): void {
        this.baseUrl = newUrl;
        this.client.defaults.baseURL = newUrl;
        Logger.info(`API base URL updated to: ${newUrl}`);
    }

    /**
     * Sets up request/response interceptors
     */
    private setupInterceptors(): void {
        // Request interceptor - add auth token
        this.client.interceptors.request.use(
            async (config) => {
                const token = await this.authService.getToken();
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                Logger.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
                return config;
            },
            (error: Error) => {
                Logger.error(`Request interceptor error: ${error.message}`);
                return Promise.reject(error);
            }
        );

        // Response interceptor - handle errors
        this.client.interceptors.response.use(
            (response) => {
                Logger.debug(`API Response: ${response.status} ${response.config.url}`);
                return response;
            },
            async (error: AxiosError) => {
                if (error.response?.status === 401) {
                    // Token expired - try to refresh
                    try {
                        await this.authService.refreshToken();
                        // Retry the original request
                        const originalRequest = error.config;
                        if (originalRequest) {
                            const newToken = await this.authService.getToken();
                            originalRequest.headers.Authorization = `Bearer ${newToken}`;
                            return this.client.request(originalRequest);
                        }
                    } catch {
                        // Refresh failed - logout user
                        await this.authService.logout();
                        void vscode.commands.executeCommand(
                            'setContext',
                            'sdlc.isAuthenticated',
                            false
                        );
                        void vscode.window.showErrorMessage(
                            'Session expired. Please log in again.'
                        );
                    }
                }

                const apiError = ApiError.fromAxiosError(error);
                Logger.error(`API Error: ${apiError.statusCode} - ${apiError.message}`);
                return Promise.reject(apiError);
            }
        );
    }

    /**
     * Makes a typed GET request
     */
    private async get<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
        const response = await this.client.get<T>(endpoint, config);
        return response.data;
    }

    /**
     * Makes a typed POST request
     */
    private async post<T>(
        endpoint: string,
        data?: unknown,
        config?: AxiosRequestConfig
    ): Promise<T> {
        const response = await this.client.post<T>(endpoint, data, config);
        return response.data;
    }

    // ============================================
    // Project APIs
    // ============================================

    /**
     * Gets list of projects accessible to the current user
     */
    async getProjects(
        page: number = 1,
        pageSize: number = 50
    ): Promise<Project[]> {
        const response = await this.get<PaginatedResponse<Project>>(
            `/api/v1/projects?page=${page}&page_size=${pageSize}`
        );
        return response.items;
    }

    /**
     * Gets a single project by ID
     */
    async getProject(projectId: string): Promise<Project> {
        return this.get<Project>(`/api/v1/projects/${projectId}`);
    }

    /**
     * Gets the currently selected project ID from configuration
     */
    getCurrentProjectId(): string | undefined {
        const config = ConfigManager.getInstance();
        return config.defaultProjectId || undefined;
    }

    // ============================================
    // Gate APIs
    // ============================================

    /**
     * Gets gates for a project
     */
    async getGates(projectId: string): Promise<Gate[]> {
        const response = await this.get<PaginatedResponse<Gate>>(
            `/api/v1/projects/${projectId}/gates`
        );
        return response.items;
    }

    /**
     * Gets a single gate by ID
     */
    async getGate(gateId: string): Promise<Gate> {
        return this.get<Gate>(`/api/v1/gates/${gateId}`);
    }

    /**
     * Gets gates for current project
     */
    async getCurrentProjectGates(): Promise<Gate[]> {
        const projectId = this.getCurrentProjectId();
        if (!projectId) {
            return [];
        }
        return this.getGates(projectId);
    }

    // ============================================
    // Violation APIs
    // ============================================

    /**
     * Gets violations for a project
     */
    async getViolations(
        projectId: string,
        status?: string,
        severity?: string
    ): Promise<Violation[]> {
        const params = new URLSearchParams();
        params.append('project_id', projectId);
        if (status) {
            params.append('status', status);
        }
        if (severity) {
            params.append('severity', severity);
        }

        const response = await this.get<PaginatedResponse<Violation>>(
            `/api/v1/compliance/violations?${params.toString()}`
        );
        return response.items;
    }

    /**
     * Gets a single violation by ID
     */
    async getViolation(violationId: string): Promise<Violation> {
        return this.get<Violation>(`/api/v1/compliance/violations/${violationId}`);
    }

    /**
     * Gets violations for current project
     */
    async getCurrentProjectViolations(
        status?: string,
        severity?: string
    ): Promise<Violation[]> {
        const projectId = this.getCurrentProjectId();
        if (!projectId) {
            return [];
        }
        return this.getViolations(projectId, status, severity);
    }

    // ============================================
    // AI Council APIs
    // ============================================

    /**
     * Gets AI recommendation for a violation
     *
     * @param violationId - ID of the violation to get recommendation for
     * @param councilMode - If true, uses 3-stage AI Council deliberation
     */
    async getAIRecommendation(
        violationId: string,
        councilMode: boolean = true
    ): Promise<AIRecommendation> {
        return this.post<AIRecommendation>('/api/v1/ai/council/recommend', {
            violation_id: violationId,
            council_mode: councilMode,
        });
    }

    /**
     * Gets AI Council deliberation status for an async request
     */
    async getCouncilStatus(requestId: string): Promise<{
        status: 'pending' | 'processing' | 'completed' | 'failed';
        result?: AIRecommendation;
        error?: string;
    }> {
        return this.get(`/api/v1/ai/council/status/${requestId}`);
    }

    /**
     * Gets AI Council deliberation history for a project
     */
    async getCouncilHistory(
        projectId: string,
        limit: number = 10
    ): Promise<
        {
            id: string;
            violation_id: string;
            recommendation: string;
            confidence_score: number;
            created_at: string;
        }[]
    > {
        const response = await this.get<
            PaginatedResponse<{
                id: string;
                violation_id: string;
                recommendation: string;
                confidence_score: number;
                created_at: string;
            }>
        >(`/api/v1/ai/council/history/${projectId}?limit=${limit}`);
        return response.items;
    }

    // ============================================
    // Compliance Scan APIs
    // ============================================

    /**
     * Triggers a compliance scan for a project
     */
    async triggerComplianceScan(projectId: string): Promise<{
        scan_id: string;
        status: string;
        message: string;
    }> {
        return this.post('/api/v1/compliance/scan', { project_id: projectId });
    }

    /**
     * Gets compliance scan status
     */
    async getScanStatus(scanId: string): Promise<{
        status: 'pending' | 'running' | 'completed' | 'failed';
        progress: number;
        violations_found: number;
        completed_at?: string;
    }> {
        return this.get(`/api/v1/compliance/scan/${scanId}`);
    }

    // ============================================
    // User & Auth APIs
    // ============================================

    /**
     * Gets current user profile
     */
    async getCurrentUser(): Promise<{
        id: string;
        email: string;
        username: string;
        full_name: string;
        role: string;
        team_id?: string;
    }> {
        return this.get('/api/v1/users/me');
    }

    /**
     * Validates the current token
     */
    async validateToken(): Promise<boolean> {
        try {
            await this.get('/api/v1/auth/validate');
            return true;
        } catch {
            return false;
        }
    }
}
