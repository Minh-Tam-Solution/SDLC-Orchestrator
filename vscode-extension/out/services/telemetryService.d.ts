/**
 * SDLC Orchestrator Telemetry Service - VSCode Extension
 *
 * Sprint 147 - Product Truth Layer
 * Tracks extension usage events for activation funnels.
 * Interface: "extension" for all events tracked through this module.
 *
 * Core Events Tracked:
 * - extension_command_executed (all commands)
 * - project_created (sdlc.init)
 * - first_validation_run (sdlc.validateSpec)
 * - spec_validated (sdlc.specValidation)
 * - first_evidence_uploaded (sdlc.uploadEvidence)
 *
 * @version 1.0.0
 * @author SDLC Orchestrator Team
 */
/**
 * Extension telemetry event names (snake_case past tense convention).
 */
export declare const ExtensionEvents: {
    readonly COMMAND_EXECUTED: "extension_command_executed";
    readonly EXTENSION_ACTIVATED: "extension_activated";
    readonly EXTENSION_DEACTIVATED: "extension_deactivated";
    readonly PROJECT_CREATED: "project_created";
    readonly PROJECT_CONNECTED_GITHUB: "project_connected_github";
    readonly FIRST_VALIDATION_RUN: "first_validation_run";
    readonly SPEC_VALIDATED: "spec_validated";
    readonly FIRST_EVIDENCE_UPLOADED: "first_evidence_uploaded";
    readonly FIRST_GATE_PASSED: "first_gate_passed";
    readonly AI_COUNCIL_USED: "ai_council_used";
    readonly CODE_GENERATED: "code_generated";
    readonly MAGIC_MODE_USED: "magic_mode_used";
};
export type ExtensionEventName = (typeof ExtensionEvents)[keyof typeof ExtensionEvents];
/**
 * Telemetry event properties
 */
interface TelemetryEventProperties {
    [key: string]: string | number | boolean | undefined | null;
}
/**
 * Telemetry Service for VSCode Extension
 *
 * Sends telemetry events to the SDLC Orchestrator backend.
 * Events are sent asynchronously and failures are silently logged.
 * Telemetry should never break the extension operation.
 */
export declare class TelemetryService {
    private static instance;
    private enabled;
    private sessionId;
    private apiUrl;
    private constructor();
    /**
     * Get singleton instance
     */
    static getInstance(): TelemetryService;
    /**
     * Generate a unique session ID for correlating events
     */
    private generateSessionId;
    /**
     * Get extension version from package.json
     */
    private getExtensionVersion;
    /**
     * Track a telemetry event
     *
     * @param eventName - Event name (use ExtensionEvents constants)
     * @param properties - Optional event properties
     * @param projectId - Optional project ID for project-scoped events
     * @returns Promise<boolean> - True if event was tracked successfully
     */
    trackEvent(eventName: ExtensionEventName | string, properties?: TelemetryEventProperties, projectId?: string): Promise<boolean>;
    /**
     * Get auth token from SecretStorage
     */
    private getAuthToken;
    /**
     * Track command execution
     */
    trackCommand(command: string, success?: boolean, durationMs?: number, projectId?: string): Promise<boolean>;
    /**
     * Track extension activation
     */
    trackActivation(): Promise<boolean>;
    /**
     * Track extension deactivation
     */
    trackDeactivation(): Promise<boolean>;
    /**
     * Track project initialization via extension
     */
    trackProjectCreated(projectId: string, tier: string, template?: string): Promise<boolean>;
    /**
     * Track GitHub connection
     */
    trackGitHubConnected(projectId: string, githubRepo: string): Promise<boolean>;
    /**
     * Track validation run
     */
    trackValidationRun(projectId: string, validationType: string, result: 'pass' | 'fail', errorsCount: number): Promise<boolean>;
    /**
     * Track spec validation
     */
    trackSpecValidation(specCount: number, validCount: number, invalidCount: number, projectId?: string): Promise<boolean>;
    /**
     * Track evidence upload
     */
    trackEvidenceUploaded(projectId: string, evidenceType: string, fileSizeBytes: number): Promise<boolean>;
    /**
     * Track AI Council usage
     */
    trackAICouncilUsed(projectId: string, queryType: string, responseTimeMs: number): Promise<boolean>;
    /**
     * Track code generation via Magic Mode
     */
    trackMagicModeUsed(projectId: string, filesGenerated: number, durationMs: number): Promise<boolean>;
    /**
     * Track code generation
     */
    trackCodeGenerated(projectId: string, language: string, linesGenerated: number): Promise<boolean>;
}
export declare function getTelemetry(): TelemetryService;
export declare const trackCommand: (command: string, success?: boolean, durationMs?: number, projectId?: string) => Promise<boolean>;
export declare const trackActivation: () => Promise<boolean>;
export declare const trackDeactivation: () => Promise<boolean>;
export declare const trackProjectCreated: (projectId: string, tier: string, template?: string) => Promise<boolean>;
export declare const trackValidationRun: (projectId: string, validationType: string, result: "pass" | "fail", errorsCount: number) => Promise<boolean>;
export declare const trackSpecValidation: (specCount: number, validCount: number, invalidCount: number, projectId?: string) => Promise<boolean>;
export {};
//# sourceMappingURL=telemetryService.d.ts.map