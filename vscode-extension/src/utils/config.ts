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
    showProjectsPanel: boolean;
}

/**
 * Default configuration values
 * Production: https://sdlc.nhatquangholding.com
 * Local development: http://localhost:8300 (IT Admin: PORT_ALLOCATION_MANAGEMENT.md)
 */
const DEFAULT_CONFIG: SDLCConfig = {
    apiUrl: 'https://sdlc.nhatquangholding.com',
    autoRefreshInterval: 30,
    defaultProjectId: '',
    enableNotifications: true,
    aiCouncilEnabled: true,
    showViolationBadge: true,
    showProjectsPanel: false,
};

/**
 * Configuration Manager singleton
 */
export class ConfigManager {
    private static instance: ConfigManager | undefined;

    private constructor() {
        // Private constructor for singleton
    }

    /**
     * Gets the singleton instance
     */
    static getInstance(): ConfigManager {
        if (!ConfigManager.instance) {
            ConfigManager.instance = new ConfigManager();
        }
        return ConfigManager.instance;
    }

    /**
     * Gets the VS Code configuration section
     */
    private getConfig(): vscode.WorkspaceConfiguration {
        return vscode.workspace.getConfiguration('sdlc');
    }

    /**
     * Gets a configuration value with type safety
     */
    private get<T>(key: keyof SDLCConfig, defaultValue: T): T {
        return this.getConfig().get<T>(key, defaultValue);
    }

    /**
     * Gets the API URL
     */
    get apiUrl(): string {
        return this.get('apiUrl', DEFAULT_CONFIG.apiUrl);
    }

    /**
     * Gets the auto-refresh interval in seconds
     */
    get autoRefreshInterval(): number {
        return this.get('autoRefreshInterval', DEFAULT_CONFIG.autoRefreshInterval);
    }

    /**
     * Gets the default project ID
     */
    get defaultProjectId(): string {
        return this.get('defaultProjectId', DEFAULT_CONFIG.defaultProjectId);
    }

    /**
     * Gets whether notifications are enabled
     */
    get enableNotifications(): boolean {
        return this.get('enableNotifications', DEFAULT_CONFIG.enableNotifications);
    }

    /**
     * Gets whether AI Council is enabled
     */
    get aiCouncilEnabled(): boolean {
        return this.get('aiCouncilEnabled', DEFAULT_CONFIG.aiCouncilEnabled);
    }

    /**
     * Gets whether violation badge is shown
     */
    get showViolationBadge(): boolean {
        return this.get('showViolationBadge', DEFAULT_CONFIG.showViolationBadge);
    }

    /**
     * Gets whether Projects panel should always be shown
     */
    get showProjectsPanel(): boolean {
        return this.get('showProjectsPanel', DEFAULT_CONFIG.showProjectsPanel);
    }

    /**
     * Gets all configuration as an object
     */
    getAll(): SDLCConfig {
        return {
            apiUrl: this.apiUrl,
            autoRefreshInterval: this.autoRefreshInterval,
            defaultProjectId: this.defaultProjectId,
            enableNotifications: this.enableNotifications,
            aiCouncilEnabled: this.aiCouncilEnabled,
            showViolationBadge: this.showViolationBadge,
            showProjectsPanel: this.showProjectsPanel,
        };
    }

    /**
     * Updates a configuration value
     */
    async update<K extends keyof SDLCConfig>(
        key: K,
        value: SDLCConfig[K],
        target: vscode.ConfigurationTarget = vscode.ConfigurationTarget.Workspace
    ): Promise<void> {
        await this.getConfig().update(key, value, target);
    }

    /**
     * Resets all configuration to defaults
     */
    async resetToDefaults(): Promise<void> {
        const config = this.getConfig();
        const keys = Object.keys(DEFAULT_CONFIG) as Array<keyof SDLCConfig>;

        for (const key of keys) {
            await config.update(key, undefined, vscode.ConfigurationTarget.Workspace);
            await config.update(key, undefined, vscode.ConfigurationTarget.Global);
        }
    }
}
