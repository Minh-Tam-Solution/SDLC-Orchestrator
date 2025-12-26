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
export type SSEEventType = 'started' | 'file_generating' | 'file_generated' | 'quality_started' | 'quality_gate' | 'completed' | 'error' | 'checkpoint';
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
export type SSEEvent = SSEStartedEvent | SSEFileGeneratingEvent | SSEFileGeneratedEvent | SSEQualityStartedEvent | SSEQualityGateEvent | SSECompletedEvent | SSEErrorEvent | SSECheckpointEvent;
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
export type UnlockReason = 'modification_needed' | 'generation_failed' | 'admin_override' | 'session_expired';
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
//# sourceMappingURL=codegen.d.ts.map