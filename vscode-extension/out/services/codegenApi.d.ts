/**
 * Code Generation API Service for SDLC Orchestrator
 *
 * Handles API calls to backend codegen endpoints.
 * Sprint 53 Day 1 - Codegen API Integration
 *
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import type { AuthService } from './authService';
import type { AppBlueprint, GenerateRequest, MagicRequest, MagicParseResult, OnboardingSession, ContractLockResponse, ContractUnlockResponse, ContractLockStatus, HashVerifyResponse, CodegenSession, UnlockReason, SpecValidationResult, SpecValidationRequest, SpecListResponse, SpecTier } from '../types/codegen';
/**
 * Code Generation API Service
 *
 * Provides methods for interacting with the SDLC Orchestrator
 * code generation backend endpoints.
 */
export declare class CodegenApiService {
    private readonly authService;
    private readonly config;
    constructor(_context: vscode.ExtensionContext, authService: AuthService);
    /**
     * Get the base API URL
     */
    private getBaseUrl;
    /**
     * Get authorization headers
     */
    private getAuthHeaders;
    /**
     * Make an API request with error handling
     */
    private request;
    /**
     * Create a new onboarding session
     */
    createSession(projectId: string): Promise<OnboardingSession>;
    /**
     * Get an onboarding session by ID
     */
    getSession(sessionId: string): Promise<OnboardingSession>;
    /**
     * Update an onboarding session
     */
    updateSession(sessionId: string, updates: Partial<OnboardingSession>): Promise<OnboardingSession>;
    /**
     * List onboarding sessions for a project
     */
    listSessions(projectId: string): Promise<OnboardingSession[]>;
    /**
     * Start code generation from a blueprint
     *
     * Returns session ID for SSE streaming connection
     */
    startGeneration(request: GenerateRequest): Promise<{
        session_id: string;
    }>;
    /**
     * Get streaming URL for a generation session
     */
    getStreamUrl(sessionId: string): string;
    /**
     * Get current auth token for SSE connection
     */
    getAuthToken(): Promise<string>;
    /**
     * Get generation session status
     */
    getGenerationStatus(sessionId: string): Promise<CodegenSession>;
    /**
     * Resume a failed generation session
     */
    resumeGeneration(sessionId: string): Promise<{
        session_id: string;
    }>;
    /**
     * Cancel an in-progress generation
     */
    cancelGeneration(sessionId: string): Promise<{
        success: boolean;
    }>;
    /**
     * Parse natural language description into blueprint
     */
    parseMagicDescription(request: MagicRequest): Promise<MagicParseResult>;
    /**
     * Start magic mode generation (parse + generate in one call)
     */
    startMagicGeneration(request: MagicRequest): Promise<{
        session_id: string;
    }>;
    /**
     * Lock a contract specification
     */
    lockContract(sessionId: string, reason?: string): Promise<ContractLockResponse>;
    /**
     * Unlock a contract specification
     */
    unlockContract(sessionId: string, reason?: UnlockReason): Promise<ContractUnlockResponse>;
    /**
     * Force unlock a contract specification (admin only)
     */
    forceUnlockContract(sessionId: string, reason?: string): Promise<ContractUnlockResponse>;
    /**
     * Get contract lock status
     */
    getContractStatus(sessionId: string): Promise<ContractLockStatus>;
    /**
     * Verify contract hash
     */
    verifyContractHash(sessionId: string, expectedHash: string): Promise<HashVerifyResponse>;
    /**
     * Validate a blueprint without generating code
     */
    validateBlueprint(blueprint: AppBlueprint): Promise<{
        valid: boolean;
        errors: string[];
        warnings: string[];
    }>;
    /**
     * Get available domain templates
     */
    getDomainTemplates(): Promise<{
        domains: Array<{
            id: string;
            name: string;
            description: string;
            modules: string[];
        }>;
    }>;
    /**
     * Get template for a specific domain
     */
    getDomainTemplate(domainId: string): Promise<AppBlueprint>;
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
    validateSpecification(request: SpecValidationRequest): Promise<SpecValidationResult>;
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
    validateSpecificationLocal(content: string, tier?: SpecTier): SpecValidationResult;
    /**
     * List all specifications in a project
     *
     * @param projectId - Optional project ID filter
     * @param tier - Optional tier filter
     * @returns List of specifications
     */
    listSpecifications(projectId?: string, tier?: SpecTier): Promise<SpecListResponse>;
    /**
     * Get SDLC 6.0.5 specification JSON schema
     *
     * @returns JSON schema for specification frontmatter validation
     */
    getSpecSchema(): Promise<Record<string, unknown>>;
}
//# sourceMappingURL=codegenApi.d.ts.map