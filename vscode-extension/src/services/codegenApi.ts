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
    SpecValidationResult,
    SpecValidationRequest,
    SpecListResponse,
    SpecTier,
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
                    const errorJson = JSON.parse(errorText) as { detail?: string; message?: string };
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
            '/api/v1/onboarding/sessions',
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

    // ========================================
    // Specification Validation APIs (Sprint 126 - S126-06)
    // SDLC 6.0.5 Spec Validation
    // ========================================

    /**
     * Validate a specification against SDLC 6.0.5 SPEC-0002 standard
     *
     * Validates:
     * - YAML frontmatter (required fields, format)
     * - BDD requirements (GIVEN-WHEN-THEN format)
     * - Cross-references (spec, ADR, file links)
     * - Tier-specific required sections
     *
     * @param request - Specification validation request
     * @returns Validation result with errors and warnings
     */
    public async validateSpecification(
        request: SpecValidationRequest
    ): Promise<SpecValidationResult> {
        return this.request<SpecValidationResult>(
            'POST',
            '/api/v1/specs/validate',
            request
        );
    }

    /**
     * Validate a specification file by path (local validation)
     *
     * This performs local validation without sending content to backend.
     * Uses the same validation rules as the CLI sdlcctl spec validate.
     *
     * @param content - Specification file content
     * @param tier - Optional tier for tier-specific validation
     * @returns Validation result
     */
    public validateSpecificationLocal(
        content: string,
        tier?: SpecTier
    ): SpecValidationResult {
        const errors: Array<{
            code: string;
            field: string;
            message: string;
            severity: 'critical' | 'high';
            line_number?: number;
            suggestion?: string;
        }> = [];
        const warnings: Array<{
            code: string;
            field: string;
            message: string;
            suggestion?: string;
            line_number?: number;
        }> = [];

        // Extract YAML frontmatter
        const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
        const frontmatterValid = !!frontmatterMatch;
        const requiredFields = ['spec_id', 'title', 'version', 'status', 'tier', 'owner', 'last_updated'];
        const presentFields: string[] = [];
        const missingFields: string[] = [];
        let specId = 'UNKNOWN';
        let version = '0.0.0';
        const detectedTiers: SpecTier[] = [];

        if (frontmatterMatch && frontmatterMatch[1]) {
            const frontmatterContent = frontmatterMatch[1];
            for (const field of requiredFields) {
                const fieldMatch = new RegExp(`^${field}:`, 'm').test(frontmatterContent);
                if (fieldMatch) {
                    presentFields.push(field);
                    // Extract values
                    if (field === 'spec_id') {
                        const match = frontmatterContent.match(/^spec_id:\s*(.+)$/m);
                        if (match && match[1]) {
                            specId = match[1].trim();
                        }
                    }
                    if (field === 'version') {
                        const match = frontmatterContent.match(/^version:\s*(.+)$/m);
                        if (match && match[1]) {
                            version = match[1].trim();
                        }
                    }
                    if (field === 'tier') {
                        const match = frontmatterContent.match(/^tier:\s*\[?([^\]]+)\]?$/m);
                        if (match && match[1]) {
                            const tierStr = match[1].replace(/[\[\]]/g, '').trim();
                            const tiers = tierStr.split(',').map(t => t.trim().toUpperCase() as SpecTier);
                            detectedTiers.push(...tiers);
                        }
                    }
                } else {
                    missingFields.push(field);
                    errors.push({
                        code: 'SPC-001',
                        field,
                        message: `Missing required frontmatter field: ${field}`,
                        severity: 'critical',
                        suggestion: `Add "${field}:" to the YAML frontmatter`,
                    });
                }
            }
        } else {
            errors.push({
                code: 'SPC-000',
                field: 'frontmatter',
                message: 'Missing YAML frontmatter block',
                severity: 'critical',
                suggestion: 'Add YAML frontmatter at the beginning of the file: ---\\nspec_id: SPEC-XXXX\\n...',
            });
            missingFields.push(...requiredFields);
        }

        // Validate BDD requirements (GIVEN-WHEN-THEN)
        const bddPattern = /^(GIVEN|WHEN|THEN|AND|BUT)\s+.+$/gim;
        const bddMatches = content.match(bddPattern) || [];
        const bddValid = bddMatches.length > 0;
        const requirementsSection = content.includes('## Requirements') || content.includes('## Functional Requirements');

        if (requirementsSection && !bddValid) {
            warnings.push({
                code: 'SPC-BDD-001',
                field: 'requirements',
                message: 'Requirements section found but no BDD format (GIVEN-WHEN-THEN) detected',
                suggestion: 'Use BDD format: GIVEN <precondition> WHEN <action> THEN <result>',
            });
        }

        // Check for required sections based on tier
        const effectiveTier = tier || (detectedTiers[0] as SpecTier) || 'PROFESSIONAL';
        const tierSections: Record<SpecTier, string[]> = {
            'LITE': ['## Overview', '## Requirements'],
            'STANDARD': ['## Overview', '## Requirements', '## Data Model'],
            'PROFESSIONAL': ['## Overview', '## Requirements', '## Data Model', '## API Specification', '## Security'],
            'ENTERPRISE': ['## Overview', '## Requirements', '## Data Model', '## API Specification', '## Security', '## Performance', '## Compliance'],
        };

        const requiredSections = tierSections[effectiveTier] || tierSections['PROFESSIONAL'];
        const presentSections: string[] = [];
        const missingSections: string[] = [];

        for (const section of requiredSections) {
            if (content.includes(section)) {
                presentSections.push(section);
            } else {
                missingSections.push(section);
                warnings.push({
                    code: 'SPC-SEC-001',
                    field: 'sections',
                    message: `Missing recommended section for ${effectiveTier} tier: ${section}`,
                    suggestion: `Add ${section} section to the specification`,
                });
            }
        }

        // Cross-reference validation (basic)
        const specRefPattern = /SPEC-\d{4}/g;
        const adrRefPattern = /ADR-\d{3}/g;
        const specRefs = content.match(specRefPattern) || [];
        const adrRefs = content.match(adrRefPattern) || [];
        const totalRefs = specRefs.length + adrRefs.length;

        const result: SpecValidationResult = {
            valid: errors.length === 0,
            spec_id: specId,
            spec_path: '',
            version,
            tier: detectedTiers.length > 0 ? detectedTiers : [effectiveTier],
            errors,
            warnings,
            frontmatter: {
                valid: frontmatterValid && missingFields.length === 0,
                required_fields_present: presentFields,
                required_fields_missing: missingFields,
                optional_fields_present: [],
                invalid_field_values: [],
            },
            bdd_validation: {
                valid: bddValid || !requirementsSection,
                total_requirements: bddMatches.length,
                valid_requirements: bddMatches.length,
                invalid_requirements: [],
                coverage_percentage: bddMatches.length > 0 ? 100 : 0,
            },
            cross_references: {
                valid: true,
                total_references: totalRefs,
                valid_references: totalRefs,
                broken_references: [],
            },
            tier_sections: {
                valid: missingSections.length === 0,
                tier: effectiveTier,
                required_sections: requiredSections,
                present_sections: presentSections,
                missing_sections: missingSections,
            },
            validation_timestamp: new Date().toISOString(),
            validator_version: '1.2.0',
        };

        return result;
    }

    /**
     * List all specifications in a project
     *
     * @param projectId - Optional project ID filter
     * @param tier - Optional tier filter
     * @returns List of specifications
     */
    public async listSpecifications(
        projectId?: string,
        tier?: SpecTier
    ): Promise<SpecListResponse> {
        let endpoint = '/api/v1/specs';
        const params: string[] = [];

        if (projectId) {
            params.push(`project_id=${projectId}`);
        }
        if (tier) {
            params.push(`tier=${tier}`);
        }

        if (params.length > 0) {
            endpoint += `?${params.join('&')}`;
        }

        return this.request<SpecListResponse>('GET', endpoint);
    }

    /**
     * Get SDLC 6.0.5 specification JSON schema
     *
     * @returns JSON schema for specification frontmatter validation
     */
    public async getSpecSchema(): Promise<Record<string, unknown>> {
        return this.request<Record<string, unknown>>(
            'GET',
            '/api/v1/specs/schema'
        );
    }
}
