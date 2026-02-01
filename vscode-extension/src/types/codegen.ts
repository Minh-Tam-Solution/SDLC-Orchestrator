/**
 * Code Generation Types for SDLC Orchestrator VS Code Extension
 *
 * Sprint 53 Day 1 - Type definitions for App Builder functionality
 * @version 1.0.0
 */

/**
 * App Blueprint structure for code generation
 */
export interface AppBlueprint {
    name: string;
    version: string;
    business_domain: string;
    description: string;
    modules: BlueprintModule[];
    metadata?: BlueprintMetadata;
}

/**
 * Blueprint module with entities
 */
export interface BlueprintModule {
    name: string;
    entities: string[];
    description?: string;
}

/**
 * Blueprint metadata
 */
export interface BlueprintMetadata {
    generated_by?: string;
    language?: string;
    source_description?: string;
    created_at?: string;
}

/**
 * Generated file from code generation
 */
export interface GeneratedFile {
    path: string;
    content: string;
    lines: number;
    language: string;
    syntax_valid: boolean;
    status: 'generating' | 'valid' | 'error';
}

/**
 * Quality gate result
 */
export interface QualityGateResult {
    gate_number: number;
    gate_name: string;
    status: 'passed' | 'failed' | 'skipped';
    issues: number;
    duration_ms: number;
    details?: string[];
}

/**
 * Code generation session
 */
export interface CodegenSession {
    id: string;
    status: 'pending' | 'generating' | 'validating' | 'completed' | 'failed';
    blueprint: AppBlueprint;
    files: GeneratedFile[];
    quality_gates: QualityGateResult[];
    started_at: string;
    completed_at?: string;
    error_message?: string;
}

/**
 * SSE Event types for streaming generation
 */
export type SSEEventType =
    | 'started'
    | 'file_generating'
    | 'file_generated'
    | 'quality_started'
    | 'quality_gate'
    | 'completed'
    | 'error'
    | 'checkpoint';

/**
 * Base SSE event structure
 */
export interface SSEBaseEvent {
    type: SSEEventType;
    timestamp: string;
    session_id: string;
}

/**
 * Generation started event
 */
export interface SSEStartedEvent extends SSEBaseEvent {
    type: 'started';
    model: string;
    provider: string;
}

/**
 * File generating event
 */
export interface SSEFileGeneratingEvent extends SSEBaseEvent {
    type: 'file_generating';
    path: string;
}

/**
 * File generated event
 */
export interface SSEFileGeneratedEvent extends SSEBaseEvent {
    type: 'file_generated';
    path: string;
    content: string;
    lines: number;
    language: string;
    syntax_valid?: boolean;
}

/**
 * Quality gate started event
 */
export interface SSEQualityStartedEvent extends SSEBaseEvent {
    type: 'quality_started';
    total_gates: number;
}

/**
 * Quality gate event
 */
export interface SSEQualityGateEvent extends SSEBaseEvent {
    type: 'quality_gate';
    gate_number: number;
    gate_name: string;
    status: 'passed' | 'failed' | 'skipped';
    issues: number;
    duration_ms: number;
}

/**
 * Generation completed event
 */
export interface SSECompletedEvent extends SSEBaseEvent {
    type: 'completed';
    total_files: number;
    total_lines: number;
    duration_ms: number;
    success: boolean;
}

/**
 * Error event
 */
export interface SSEErrorEvent extends SSEBaseEvent {
    type: 'error';
    message: string;
    recovery_id?: string;
}

/**
 * Checkpoint event for resumable sessions
 */
export interface SSECheckpointEvent extends SSEBaseEvent {
    type: 'checkpoint';
    files_completed: number;
    last_file_path: string;
}

/**
 * Union type for all SSE events
 */
export type SSEEvent =
    | SSEStartedEvent
    | SSEFileGeneratingEvent
    | SSEFileGeneratedEvent
    | SSEQualityStartedEvent
    | SSEQualityGateEvent
    | SSECompletedEvent
    | SSEErrorEvent
    | SSECheckpointEvent;

/**
 * Contract lock status
 */
export interface ContractLockStatus {
    session_id: string;
    is_locked: boolean;
    locked_at?: string;
    locked_by?: string;
    spec_hash?: string;
    version?: number;
}

/**
 * Contract lock request
 */
export interface ContractLockRequest {
    reason?: string;
}

/**
 * Contract lock response
 */
export interface ContractLockResponse {
    success: boolean;
    session_id: string;
    is_locked: boolean;
    locked_at: string;
    locked_by: string;
    spec_hash: string;
    version: number;
    message: string;
}

/**
 * Unlock reason enum values
 */
export type UnlockReason =
    | 'modification_needed'
    | 'generation_failed'
    | 'admin_override'
    | 'session_expired';

/**
 * Contract unlock request
 */
export interface ContractUnlockRequest {
    reason: UnlockReason;
    force?: boolean;
}

/**
 * Contract unlock response
 */
export interface ContractUnlockResponse {
    success: boolean;
    session_id: string;
    is_locked: boolean;
    unlocked_at: string;
    unlocked_by: string;
    message: string;
}

/**
 * Hash verification request
 */
export interface HashVerifyRequest {
    expected_hash: string;
}

/**
 * Hash verification response
 */
export interface HashVerifyResponse {
    valid: boolean;
    current_hash: string;
    expected_hash: string;
    match: boolean;
    message: string;
}

/**
 * Magic mode domain detection result
 */
export interface DomainDetectionResult {
    domain: string;
    confidence: number;
    matched_keywords: string[];
}

/**
 * Magic mode parse result
 */
export interface MagicParseResult {
    blueprint: AppBlueprint;
    domain_detection: DomainDetectionResult;
    language: string;
}

/**
 * Generate request parameters
 */
export interface GenerateRequest {
    blueprint: AppBlueprint;
    language?: string;
    framework?: string;
    output_path?: string;
}

/**
 * Magic mode request parameters
 */
export interface MagicRequest {
    description: string;
    language?: 'vi' | 'en' | 'auto';
    domain?: string;
    output_path?: string;
}

/**
 * Resume generation request
 */
export interface ResumeRequest {
    session_id: string;
}

/**
 * Onboarding session for code generation
 */
export interface OnboardingSession {
    id: string;
    project_id: string;
    status: 'draft' | 'in_progress' | 'completed' | 'failed';
    current_stage: string;
    business_description?: string;
    selected_domain?: string;
    app_blueprint?: AppBlueprint;
    generated_files?: GeneratedFile[];
    is_locked: boolean;
    locked_at?: string;
    spec_hash?: string;
    created_at: string;
    updated_at: string;
}

// ========================================
// Specification Validation Types (Sprint 126 - S126-06)
// SDLC 6.0.0 Spec Validation for VS Code Extension
// ========================================

/**
 * SDLC 6.0.0 Tier classification
 */
export type SpecTier = 'LITE' | 'STANDARD' | 'PROFESSIONAL' | 'ENTERPRISE';

/**
 * Specification validation error
 */
export interface SpecValidationError {
    code: string;
    field: string;
    message: string;
    severity: 'critical' | 'high';
    line_number?: number;
    suggestion?: string;
}

/**
 * Specification validation warning
 */
export interface SpecValidationWarning {
    code: string;
    field: string;
    message: string;
    suggestion?: string;
    line_number?: number;
}

/**
 * YAML Frontmatter validation result
 */
export interface FrontmatterValidation {
    valid: boolean;
    required_fields_present: string[];
    required_fields_missing: string[];
    optional_fields_present: string[];
    invalid_field_values: Array<{
        field: string;
        value: string;
        expected: string;
    }>;
}

/**
 * BDD Requirements validation result
 */
export interface BDDValidation {
    valid: boolean;
    total_requirements: number;
    valid_requirements: number;
    invalid_requirements: Array<{
        line_number: number;
        content: string;
        issue: string;
    }>;
    coverage_percentage: number;
}

/**
 * Cross-reference validation result
 */
export interface CrossReferenceValidation {
    valid: boolean;
    total_references: number;
    valid_references: number;
    broken_references: Array<{
        reference: string;
        line_number?: number;
        type: 'spec' | 'adr' | 'file' | 'url';
    }>;
}

/**
 * Tier-specific sections validation
 */
export interface TierSectionsValidation {
    valid: boolean;
    tier: SpecTier;
    required_sections: string[];
    present_sections: string[];
    missing_sections: string[];
}

/**
 * Complete specification validation result
 */
export interface SpecValidationResult {
    valid: boolean;
    spec_id: string;
    spec_path: string;
    version: string;
    tier: SpecTier[];
    errors: SpecValidationError[];
    warnings: SpecValidationWarning[];
    frontmatter: FrontmatterValidation;
    bdd_validation: BDDValidation;
    cross_references: CrossReferenceValidation;
    tier_sections: TierSectionsValidation;
    validation_timestamp: string;
    validator_version: string;
}

/**
 * Specification list item
 */
export interface SpecListItem {
    spec_id: string;
    title: string;
    version: string;
    status: string;
    tier: SpecTier[];
    owner: string;
    last_updated: string;
    path: string;
    is_valid: boolean;
}

/**
 * Specification list response
 */
export interface SpecListResponse {
    total: number;
    specs: SpecListItem[];
    by_tier: Record<SpecTier, number>;
    by_status: Record<string, number>;
}

/**
 * Specification validation request
 */
export interface SpecValidationRequest {
    content: string;
    path?: string;
    tier?: SpecTier;
    validate_cross_refs?: boolean;
    validate_bdd?: boolean;
}
