/**
 * SDLC Orchestrator Configuration Manager
 *
 * Provides centralized access to extension configuration settings.
 *
 * Sprint 27 Day 1 - Utilities
 * @version 0.1.0
 */
import * as vscode from 'vscode';
/**
 * Configuration interface
 */
export interface SDLCConfig {
    apiUrl: string;
    autoRefreshInterval: number;
    defaultProjectId: string;
    enableNotifications: boolean;
    aiCouncilEnabled: boolean;
    showViolationBadge: boolean;
}
/**
 * Configuration Manager singleton
 */
export declare class ConfigManager {
    private static instance;
    private constructor();
    /**
     * Gets the singleton instance
     */
    static getInstance(): ConfigManager;
    /**
     * Gets the VS Code configuration section
     */
    private getConfig;
    /**
     * Gets a configuration value with type safety
     */
    private get;
    /**
     * Gets the API URL
     */
    get apiUrl(): string;
    /**
     * Gets the auto-refresh interval in seconds
     */
    get autoRefreshInterval(): number;
    /**
     * Gets the default project ID
     */
    get defaultProjectId(): string;
    /**
     * Gets whether notifications are enabled
     */
    get enableNotifications(): boolean;
    /**
     * Gets whether AI Council is enabled
     */
    get aiCouncilEnabled(): boolean;
    /**
     * Gets whether violation badge is shown
     */
    get showViolationBadge(): boolean;
    /**
     * Gets all configuration as an object
     */
    getAll(): SDLCConfig;
    /**
     * Updates a configuration value
     */
    update<K extends keyof SDLCConfig>(key: K, value: SDLCConfig[K], target?: vscode.ConfigurationTarget): Promise<void>;
    /**
     * Resets all configuration to defaults
     */
    resetToDefaults(): Promise<void>;
}
//# sourceMappingURL=config.d.ts.map