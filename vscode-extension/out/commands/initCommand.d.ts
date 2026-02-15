/**
 * SDLC Init Command Handler
 *
 * Implements the /init command for creating SDLC 6.0.5 compliant project structures.
 * Similar to Claude Code's /init command but for SDLC governance.
 *
 * SDLC 6.0.5 Rules:
 * - Only /docs folders are mapped to stages (00-09)
 * - Code folders (src, backend, frontend, tests) are NOT stage-mapped
 *
 * Sprint 53 - SDLC 6.0.5 Compliance
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
import { AuthService } from '../services/authService';
/**
 * Init command options
 */
interface InitOptions {
    offline?: boolean;
    skipTemplates?: boolean;
    force?: boolean;
}
/**
 * SDLC Init Command Handler
 */
export declare class InitCommandHandler {
    private readonly structureService;
    private readonly apiClient;
    private readonly authService;
    constructor(apiClient?: ApiClient, authService?: AuthService);
    /**
     * Execute the /init command
     */
    execute(options?: InitOptions): Promise<boolean>;
    /**
     * Handle initialization for new (empty) projects
     */
    private handleNewProject;
    /**
     * Handle initialization for existing projects (gap analysis)
     */
    private handleExistingProject;
    /**
     * Select SDLC tier via quick pick
     */
    private selectTier;
    /**
     * Confirm whether to create template files
     */
    private confirmCreateTemplates;
    /**
     * Show gap analysis results
     */
    private showGapAnalysisResults;
    /**
     * Generate HTML for gap analysis results
     */
    private generateGapAnalysisHtml;
    /**
     * Show success message with summary
     */
    private showSuccessMessage;
    /**
     * Open the Getting Started guide
     */
    private openGettingStarted;
    /**
     * Open the SDLC config file
     */
    private openConfig;
    /**
     * Get workspace root folder
     */
    private getWorkspaceRoot;
    /**
     * Get project name from folder or user input
     */
    private getProjectName;
    /**
     * Format folder name to project name
     */
    private formatProjectName;
    /**
     * Get server URL based on offline mode
     */
    private getServerUrl;
    /**
     * Sync project with SDLC Orchestrator server
     *
     * Returns true if sync succeeded, false otherwise.
     * Shows user-facing error messages on failure instead of silently swallowing.
     */
    private syncWithServer;
    /**
     * Run standalone gap analysis
     */
    runGapAnalysis(): Promise<void>;
}
/**
 * Register the init command
 */
export declare function registerInitCommand(context: vscode.ExtensionContext, apiClient?: ApiClient, authService?: AuthService): void;
export {};
//# sourceMappingURL=initCommand.d.ts.map