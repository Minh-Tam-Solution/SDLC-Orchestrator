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
        return this.request('POST', '/api/v1/onboarding/sessions', { project_id: projectId });
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
    // ========================================
    // Specification Validation APIs (Sprint 126 - S126-06)
    // SDLC 6.0.0 Spec Validation
    // ========================================
    /**
     * Validate a specification against SDLC 6.0.0 SPEC-0002 standard
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
    async validateSpecification(request) {
        return this.request('POST', '/api/v1/specs/validate', request);
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
    validateSpecificationLocal(content, tier) {
        const errors = [];
        const warnings = [];
        // Extract YAML frontmatter
        const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
        const frontmatterValid = !!frontmatterMatch;
        const requiredFields = ['spec_id', 'title', 'version', 'status', 'tier', 'owner', 'last_updated'];
        const presentFields = [];
        const missingFields = [];
        let specId = 'UNKNOWN';
        let version = '0.0.0';
        const detectedTiers = [];
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
                            const tiers = tierStr.split(',').map(t => t.trim().toUpperCase());
                            detectedTiers.push(...tiers);
                        }
                    }
                }
                else {
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
        }
        else {
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
        const effectiveTier = tier || detectedTiers[0] || 'PROFESSIONAL';
        const tierSections = {
            'LITE': ['## Overview', '## Requirements'],
            'STANDARD': ['## Overview', '## Requirements', '## Data Model'],
            'PROFESSIONAL': ['## Overview', '## Requirements', '## Data Model', '## API Specification', '## Security'],
            'ENTERPRISE': ['## Overview', '## Requirements', '## Data Model', '## API Specification', '## Security', '## Performance', '## Compliance'],
        };
        const requiredSections = tierSections[effectiveTier] || tierSections['PROFESSIONAL'];
        const presentSections = [];
        const missingSections = [];
        for (const section of requiredSections) {
            if (content.includes(section)) {
                presentSections.push(section);
            }
            else {
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
        const result = {
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
    async listSpecifications(projectId, tier) {
        let endpoint = '/api/v1/specs';
        const params = [];
        if (projectId) {
            params.push(`project_id=${projectId}`);
        }
        if (tier) {
            params.push(`tier=${tier}`);
        }
        if (params.length > 0) {
            endpoint += `?${params.join('&')}`;
        }
        return this.request('GET', endpoint);
    }
    /**
     * Get SDLC 6.0.0 specification JSON schema
     *
     * @returns JSON schema for specification frontmatter validation
     */
    async getSpecSchema() {
        return this.request('GET', '/api/v1/specs/schema');
    }
}
exports.CodegenApiService = CodegenApiService;
//# sourceMappingURL=codegenApi.js.map