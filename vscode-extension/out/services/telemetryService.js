"use strict";
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
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.trackSpecValidation = exports.trackValidationRun = exports.trackProjectCreated = exports.trackDeactivation = exports.trackActivation = exports.trackCommand = exports.TelemetryService = exports.ExtensionEvents = void 0;
exports.getTelemetry = getTelemetry;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const config_1 = require("../utils/config");
/**
 * Extension telemetry event names (snake_case past tense convention).
 */
exports.ExtensionEvents = {
    // General extension events
    COMMAND_EXECUTED: 'extension_command_executed',
    EXTENSION_ACTIVATED: 'extension_activated',
    EXTENSION_DEACTIVATED: 'extension_deactivated',
    // Activation funnel events
    PROJECT_CREATED: 'project_created',
    PROJECT_CONNECTED_GITHUB: 'project_connected_github',
    FIRST_VALIDATION_RUN: 'first_validation_run',
    SPEC_VALIDATED: 'spec_validated',
    FIRST_EVIDENCE_UPLOADED: 'first_evidence_uploaded',
    FIRST_GATE_PASSED: 'first_gate_passed',
    // Engagement events
    AI_COUNCIL_USED: 'ai_council_used',
    CODE_GENERATED: 'code_generated',
    MAGIC_MODE_USED: 'magic_mode_used',
};
/**
 * Telemetry Service for VSCode Extension
 *
 * Sends telemetry events to the SDLC Orchestrator backend.
 * Events are sent asynchronously and failures are silently logged.
 * Telemetry should never break the extension operation.
 */
class TelemetryService {
    static instance;
    enabled = true;
    sessionId;
    apiUrl;
    constructor() {
        this.sessionId = this.generateSessionId();
        const config = config_1.ConfigManager.getInstance();
        this.apiUrl = config.apiUrl;
        // Check if telemetry is disabled via settings
        const disableConfig = vscode.workspace
            .getConfiguration('sdlc')
            .get('telemetry.disabled');
        this.enabled = !disableConfig;
        logger_1.Logger.debug(`[Telemetry] Initialized, enabled: ${this.enabled}`);
    }
    /**
     * Get singleton instance
     */
    static getInstance() {
        if (!TelemetryService.instance) {
            TelemetryService.instance = new TelemetryService();
        }
        return TelemetryService.instance;
    }
    /**
     * Generate a unique session ID for correlating events
     */
    generateSessionId() {
        return `ext-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    }
    /**
     * Get extension version from package.json
     */
    getExtensionVersion() {
        try {
            const extension = vscode.extensions.getExtension('sdlc-orchestrator.sdlc-orchestrator');
            return extension?.packageJSON?.version ?? 'unknown';
        }
        catch {
            return 'unknown';
        }
    }
    /**
     * Track a telemetry event
     *
     * @param eventName - Event name (use ExtensionEvents constants)
     * @param properties - Optional event properties
     * @param projectId - Optional project ID for project-scoped events
     * @returns Promise<boolean> - True if event was tracked successfully
     */
    async trackEvent(eventName, properties, projectId) {
        if (!this.enabled) {
            return false;
        }
        try {
            const payload = {
                event_name: eventName,
                properties: {
                    ...properties,
                    timestamp: new Date().toISOString(),
                    extension_version: this.getExtensionVersion(),
                    vscode_version: vscode.version,
                },
                session_id: this.sessionId,
                interface: 'extension',
                ...(projectId ? { project_id: projectId } : {}),
            };
            // Get auth token if available
            const token = await this.getAuthToken();
            const headers = {
                'Content-Type': 'application/json',
            };
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            // Use fetch API for HTTP request
            const response = await fetch(`${this.apiUrl}/telemetry/events`, {
                method: 'POST',
                headers,
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                logger_1.Logger.debug(`[Telemetry] Failed to track event: ${eventName}, status: ${response.status}`);
                return false;
            }
            logger_1.Logger.debug(`[Telemetry] Event tracked: ${eventName}`);
            return true;
        }
        catch (error) {
            // Silently log - telemetry should never break the extension
            logger_1.Logger.debug(`[Telemetry] Error tracking event ${eventName}: ${error}`);
            return false;
        }
    }
    /**
     * Get auth token from SecretStorage
     */
    async getAuthToken() {
        try {
            // Access the secret storage through the extension context
            // This is a simplified version - in production, use AuthService
            // For now, return undefined if not authenticated
            // The AuthService handles token retrieval properly
            return undefined;
        }
        catch {
            return undefined;
        }
    }
    /**
     * Track command execution
     */
    async trackCommand(command, success = true, durationMs, projectId) {
        return this.trackEvent(exports.ExtensionEvents.COMMAND_EXECUTED, {
            command,
            success,
            duration_ms: durationMs,
        }, projectId);
    }
    /**
     * Track extension activation
     */
    async trackActivation() {
        return this.trackEvent(exports.ExtensionEvents.EXTENSION_ACTIVATED, {
            vscode_version: vscode.version,
            platform: process.platform,
        });
    }
    /**
     * Track extension deactivation
     */
    async trackDeactivation() {
        return this.trackEvent(exports.ExtensionEvents.EXTENSION_DEACTIVATED);
    }
    /**
     * Track project initialization via extension
     */
    async trackProjectCreated(projectId, tier, template) {
        return this.trackEvent(exports.ExtensionEvents.PROJECT_CREATED, {
            tier,
            template_used: template,
            source: 'extension',
        }, projectId);
    }
    /**
     * Track GitHub connection
     */
    async trackGitHubConnected(projectId, githubRepo) {
        return this.trackEvent(exports.ExtensionEvents.PROJECT_CONNECTED_GITHUB, { github_repo: githubRepo }, projectId);
    }
    /**
     * Track validation run
     */
    async trackValidationRun(projectId, validationType, result, errorsCount) {
        return this.trackEvent(exports.ExtensionEvents.FIRST_VALIDATION_RUN, {
            validation_type: validationType,
            result,
            errors_count: errorsCount,
        }, projectId);
    }
    /**
     * Track spec validation
     */
    async trackSpecValidation(specCount, validCount, invalidCount, projectId) {
        return this.trackEvent(exports.ExtensionEvents.SPEC_VALIDATED, {
            spec_count: specCount,
            valid_count: validCount,
            invalid_count: invalidCount,
            pass_rate: specCount > 0 ? (validCount / specCount) * 100 : 0,
        }, projectId);
    }
    /**
     * Track evidence upload
     */
    async trackEvidenceUploaded(projectId, evidenceType, fileSizeBytes) {
        return this.trackEvent(exports.ExtensionEvents.FIRST_EVIDENCE_UPLOADED, {
            evidence_type: evidenceType,
            file_size_bytes: fileSizeBytes,
        }, projectId);
    }
    /**
     * Track AI Council usage
     */
    async trackAICouncilUsed(projectId, queryType, responseTimeMs) {
        return this.trackEvent(exports.ExtensionEvents.AI_COUNCIL_USED, {
            query_type: queryType,
            response_time_ms: responseTimeMs,
        }, projectId);
    }
    /**
     * Track code generation via Magic Mode
     */
    async trackMagicModeUsed(projectId, filesGenerated, durationMs) {
        return this.trackEvent(exports.ExtensionEvents.MAGIC_MODE_USED, {
            files_generated: filesGenerated,
            duration_ms: durationMs,
        }, projectId);
    }
    /**
     * Track code generation
     */
    async trackCodeGenerated(projectId, language, linesGenerated) {
        return this.trackEvent(exports.ExtensionEvents.CODE_GENERATED, {
            language,
            lines_generated: linesGenerated,
        }, projectId);
    }
}
exports.TelemetryService = TelemetryService;
// Export singleton getter
function getTelemetry() {
    return TelemetryService.getInstance();
}
// Convenience functions for quick access
const trackCommand = (command, success, durationMs, projectId) => getTelemetry().trackCommand(command, success, durationMs, projectId);
exports.trackCommand = trackCommand;
const trackActivation = () => getTelemetry().trackActivation();
exports.trackActivation = trackActivation;
const trackDeactivation = () => getTelemetry().trackDeactivation();
exports.trackDeactivation = trackDeactivation;
const trackProjectCreated = (projectId, tier, template) => getTelemetry().trackProjectCreated(projectId, tier, template);
exports.trackProjectCreated = trackProjectCreated;
const trackValidationRun = (projectId, validationType, result, errorsCount) => getTelemetry().trackValidationRun(projectId, validationType, result, errorsCount);
exports.trackValidationRun = trackValidationRun;
const trackSpecValidation = (specCount, validCount, invalidCount, projectId) => getTelemetry().trackSpecValidation(specCount, validCount, invalidCount, projectId);
exports.trackSpecValidation = trackSpecValidation;
//# sourceMappingURL=telemetryService.js.map