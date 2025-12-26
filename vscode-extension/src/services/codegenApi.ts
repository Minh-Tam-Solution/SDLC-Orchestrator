/**
 * Code Generation API Service for SDLC Orchestrator
 *
 * Handles API calls to backend codegen endpoints.
 * Sprint 53 Day 1 - Codegen API Integration
 *
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import type { AuthService } from './authService';
import type {
    AppBlueprint,
    GenerateRequest,
    MagicRequest,
    MagicParseResult,
    OnboardingSession,
    ContractLockResponse,
    ContractUnlockResponse,
    ContractLockStatus,
    HashVerifyResponse,
    CodegenSession,
    UnlockReason,
} from '../types/codegen';

// ApiResponse interface reserved for future use with typed responses

/**
 * Code Generation API Service
 *
 * Provides methods for interacting with the SDLC Orchestrator
 * code generation backend endpoints.
 */
export class CodegenApiService {
    private readonly config: ConfigManager;

    constructor(
        _context: vscode.ExtensionContext,
        private readonly authService: AuthService
    ) {
        this.config = ConfigManager.getInstance();
    }

    /**
     * Get the base API URL
     */
    private getBaseUrl(): string {
        return this.config.apiUrl;
    }

    /**
     * Get authorization headers
     */
    private async getAuthHeaders(): Promise<Record<string, string>> {
        const token = await this.authService.getToken();
        if (!token) {
            throw new Error('Not authenticated. Please login first.');
        }
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        };
    }

    /**
     * Make an API request with error handling
     */
    private async request<T>(
        method: string,
        endpoint: string,
        body?: unknown
    ): Promise<T> {
        const url = `${this.getBaseUrl()}${endpoint}`;
        const headers = await this.getAuthHeaders();

        const requestInit: RequestInit = {
            method,
            headers,
        };

        if (body) {
            requestInit.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, requestInit);

            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `API error: ${response.status}`;
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || errorJson.message || errorMessage;
                } catch {
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            return await response.json() as T;
        } catch (error) {
            if (error instanceof Error) {
                Logger.error(`Codegen API error: ${error.message}`);
                throw error;
            }
            throw new Error('Unknown API error');
        }
    }

    // ========================================
    // Onboarding Session APIs
    // ========================================

    /**
     * Create a new onboarding session
     */
    public async createSession(projectId: string): Promise<OnboardingSession> {
        return this.request<OnboardingSession>(
            'POST',
            `/api/v1/onboarding/sessions`,
            { project_id: projectId }
        );
    }

    /**
     * Get an onboarding session by ID
     */
    public async getSession(sessionId: string): Promise<OnboardingSession> {
        return this.request<OnboardingSession>(
            'GET',
            `/api/v1/onboarding/sessions/${sessionId}`
        );
    }

    /**
     * Update an onboarding session
     */
    public async updateSession(
        sessionId: string,
        updates: Partial<OnboardingSession>
    ): Promise<OnboardingSession> {
        return this.request<OnboardingSession>(
            'PATCH',
            `/api/v1/onboarding/sessions/${sessionId}`,
            updates
        );
    }

    /**
     * List onboarding sessions for a project
     */
    public async listSessions(projectId: string): Promise<OnboardingSession[]> {
        return this.request<OnboardingSession[]>(
            'GET',
            `/api/v1/onboarding/sessions?project_id=${projectId}`
        );
    }

    // ========================================
    // Code Generation APIs
    // ========================================

    /**
     * Start code generation from a blueprint
     *
     * Returns session ID for SSE streaming connection
     */
    public async startGeneration(request: GenerateRequest): Promise<{ session_id: string }> {
        return this.request<{ session_id: string }>(
            'POST',
            '/api/v1/codegen/generate',
            request
        );
    }

    /**
     * Get streaming URL for a generation session
     */
    public getStreamUrl(sessionId: string): string {
        return `${this.getBaseUrl()}/api/v1/codegen/stream/${sessionId}`;
    }

    /**
     * Get current auth token for SSE connection
     */
    public async getAuthToken(): Promise<string> {
        const token = await this.authService.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }
        return token;
    }

    /**
     * Get generation session status
     */
    public async getGenerationStatus(sessionId: string): Promise<CodegenSession> {
        return this.request<CodegenSession>(
            'GET',
            `/api/v1/codegen/sessions/${sessionId}`
        );
    }

    /**
     * Resume a failed generation session
     */
    public async resumeGeneration(sessionId: string): Promise<{ session_id: string }> {
        return this.request<{ session_id: string }>(
            'POST',
            `/api/v1/codegen/resume/${sessionId}`
        );
    }

    /**
     * Cancel an in-progress generation
     */
    public async cancelGeneration(sessionId: string): Promise<{ success: boolean }> {
        return this.request<{ success: boolean }>(
            'POST',
            `/api/v1/codegen/cancel/${sessionId}`
        );
    }

    // ========================================
    // Magic Mode APIs
    // ========================================

    /**
     * Parse natural language description into blueprint
     */
    public async parseMagicDescription(request: MagicRequest): Promise<MagicParseResult> {
        return this.request<MagicParseResult>(
            'POST',
            '/api/v1/codegen/magic/parse',
            request
        );
    }

    /**
     * Start magic mode generation (parse + generate in one call)
     */
    public async startMagicGeneration(request: MagicRequest): Promise<{ session_id: string }> {
        return this.request<{ session_id: string }>(
            'POST',
            '/api/v1/codegen/magic/generate',
            request
        );
    }

    // ========================================
    // Contract Lock APIs
    // ========================================

    /**
     * Lock a contract specification
     */
    public async lockContract(
        sessionId: string,
        reason?: string
    ): Promise<ContractLockResponse> {
        return this.request<ContractLockResponse>(
            'POST',
            `/api/v1/onboarding/${sessionId}/lock`,
            { reason }
        );
    }

    /**
     * Unlock a contract specification
     */
    public async unlockContract(
        sessionId: string,
        reason: UnlockReason = 'modification_needed'
    ): Promise<ContractUnlockResponse> {
        return this.request<ContractUnlockResponse>(
            'POST',
            `/api/v1/onboarding/${sessionId}/unlock`,
            { reason }
        );
    }

    /**
     * Force unlock a contract specification (admin only)
     */
    public async forceUnlockContract(
        sessionId: string,
        reason?: string
    ): Promise<ContractUnlockResponse> {
        return this.request<ContractUnlockResponse>(
            'POST',
            `/api/v1/onboarding/${sessionId}/force-unlock`,
            { reason }
        );
    }

    /**
     * Get contract lock status
     */
    public async getContractStatus(sessionId: string): Promise<ContractLockStatus> {
        return this.request<ContractLockStatus>(
            'GET',
            `/api/v1/onboarding/${sessionId}/status`
        );
    }

    /**
     * Verify contract hash
     */
    public async verifyContractHash(
        sessionId: string,
        expectedHash: string
    ): Promise<HashVerifyResponse> {
        return this.request<HashVerifyResponse>(
            'POST',
            `/api/v1/onboarding/${sessionId}/verify-hash`,
            { expected_hash: expectedHash }
        );
    }

    // ========================================
    // Blueprint APIs
    // ========================================

    /**
     * Validate a blueprint without generating code
     */
    public async validateBlueprint(blueprint: AppBlueprint): Promise<{
        valid: boolean;
        errors: string[];
        warnings: string[];
    }> {
        return this.request(
            'POST',
            '/api/v1/codegen/validate',
            { blueprint }
        );
    }

    /**
     * Get available domain templates
     */
    public async getDomainTemplates(): Promise<{
        domains: Array<{
            id: string;
            name: string;
            description: string;
            modules: string[];
        }>;
    }> {
        return this.request(
            'GET',
            '/api/v1/codegen/templates/domains'
        );
    }

    /**
     * Get template for a specific domain
     */
    public async getDomainTemplate(domainId: string): Promise<AppBlueprint> {
        return this.request<AppBlueprint>(
            'GET',
            `/api/v1/codegen/templates/domains/${domainId}`
        );
    }
}
