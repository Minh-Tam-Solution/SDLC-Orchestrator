"use strict";
/**
 * Code Generation API Service for SDLC Orchestrator
 *
 * Handles API calls to backend codegen endpoints.
 * Sprint 53 Day 1 - Codegen API Integration
 *
 * @version 1.0.0
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.CodegenApiService = void 0;
const logger_1 = require("../utils/logger");
const config_1 = require("../utils/config");
// ApiResponse interface reserved for future use with typed responses
/**
 * Code Generation API Service
 *
 * Provides methods for interacting with the SDLC Orchestrator
 * code generation backend endpoints.
 */
class CodegenApiService {
    authService;
    config;
    constructor(_context, authService) {
        this.authService = authService;
        this.config = config_1.ConfigManager.getInstance();
    }
    /**
     * Get the base API URL
     */
    getBaseUrl() {
        return this.config.apiUrl;
    }
    /**
     * Get authorization headers
     */
    async getAuthHeaders() {
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
    async request(method, endpoint, body) {
        const url = `${this.getBaseUrl()}${endpoint}`;
        const headers = await this.getAuthHeaders();
        const requestInit = {
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
                }
                catch {
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            return await response.json();
        }
        catch (error) {
            if (error instanceof Error) {
                logger_1.Logger.error(`Codegen API error: ${error.message}`);
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
    async createSession(projectId) {
        return this.request('POST', `/api/v1/onboarding/sessions`, { project_id: projectId });
    }
    /**
     * Get an onboarding session by ID
     */
    async getSession(sessionId) {
        return this.request('GET', `/api/v1/onboarding/sessions/${sessionId}`);
    }
    /**
     * Update an onboarding session
     */
    async updateSession(sessionId, updates) {
        return this.request('PATCH', `/api/v1/onboarding/sessions/${sessionId}`, updates);
    }
    /**
     * List onboarding sessions for a project
     */
    async listSessions(projectId) {
        return this.request('GET', `/api/v1/onboarding/sessions?project_id=${projectId}`);
    }
    // ========================================
    // Code Generation APIs
    // ========================================
    /**
     * Start code generation from a blueprint
     *
     * Returns session ID for SSE streaming connection
     */
    async startGeneration(request) {
        return this.request('POST', '/api/v1/codegen/generate', request);
    }
    /**
     * Get streaming URL for a generation session
     */
    getStreamUrl(sessionId) {
        return `${this.getBaseUrl()}/api/v1/codegen/stream/${sessionId}`;
    }
    /**
     * Get current auth token for SSE connection
     */
    async getAuthToken() {
        const token = await this.authService.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }
        return token;
    }
    /**
     * Get generation session status
     */
    async getGenerationStatus(sessionId) {
        return this.request('GET', `/api/v1/codegen/sessions/${sessionId}`);
    }
    /**
     * Resume a failed generation session
     */
    async resumeGeneration(sessionId) {
        return this.request('POST', `/api/v1/codegen/resume/${sessionId}`);
    }
    /**
     * Cancel an in-progress generation
     */
    async cancelGeneration(sessionId) {
        return this.request('POST', `/api/v1/codegen/cancel/${sessionId}`);
    }
    // ========================================
    // Magic Mode APIs
    // ========================================
    /**
     * Parse natural language description into blueprint
     */
    async parseMagicDescription(request) {
        return this.request('POST', '/api/v1/codegen/magic/parse', request);
    }
    /**
     * Start magic mode generation (parse + generate in one call)
     */
    async startMagicGeneration(request) {
        return this.request('POST', '/api/v1/codegen/magic/generate', request);
    }
    // ========================================
    // Contract Lock APIs
    // ========================================
    /**
     * Lock a contract specification
     */
    async lockContract(sessionId, reason) {
        return this.request('POST', `/api/v1/onboarding/${sessionId}/lock`, { reason });
    }
    /**
     * Unlock a contract specification
     */
    async unlockContract(sessionId, reason = 'modification_needed') {
        return this.request('POST', `/api/v1/onboarding/${sessionId}/unlock`, { reason });
    }
    /**
     * Force unlock a contract specification (admin only)
     */
    async forceUnlockContract(sessionId, reason) {
        return this.request('POST', `/api/v1/onboarding/${sessionId}/force-unlock`, { reason });
    }
    /**
     * Get contract lock status
     */
    async getContractStatus(sessionId) {
        return this.request('GET', `/api/v1/onboarding/${sessionId}/status`);
    }
    /**
     * Verify contract hash
     */
    async verifyContractHash(sessionId, expectedHash) {
        return this.request('POST', `/api/v1/onboarding/${sessionId}/verify-hash`, { expected_hash: expectedHash });
    }
    // ========================================
    // Blueprint APIs
    // ========================================
    /**
     * Validate a blueprint without generating code
     */
    async validateBlueprint(blueprint) {
        return this.request('POST', '/api/v1/codegen/validate', { blueprint });
    }
    /**
     * Get available domain templates
     */
    async getDomainTemplates() {
        return this.request('GET', '/api/v1/codegen/templates/domains');
    }
    /**
     * Get template for a specific domain
     */
    async getDomainTemplate(domainId) {
        return this.request('GET', `/api/v1/codegen/templates/domains/${domainId}`);
    }
}
exports.CodegenApiService = CodegenApiService;
//# sourceMappingURL=codegenApi.js.map