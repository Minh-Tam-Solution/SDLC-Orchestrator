"use strict";
/**
 * SDLC Orchestrator Configuration Manager
 *
 * Provides centralized access to extension configuration settings.
 *
 * Sprint 27 Day 1 - Utilities
 * @version 0.1.0
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
exports.ConfigManager = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Default configuration values
 * Production: https://sdlc.nhatquangholding.com
 * Local development: http://localhost:8300 (IT Admin: PORT_ALLOCATION_MANAGEMENT.md)
 */
const DEFAULT_CONFIG = {
    apiUrl: 'https://sdlc.nhatquangholding.com',
    autoRefreshInterval: 30,
    defaultProjectId: '',
    enableNotifications: true,
    aiCouncilEnabled: true,
    showViolationBadge: true,
};
/**
 * Configuration Manager singleton
 */
class ConfigManager {
    static instance;
    constructor() {
        // Private constructor for singleton
    }
    /**
     * Gets the singleton instance
     */
    static getInstance() {
        if (!ConfigManager.instance) {
            ConfigManager.instance = new ConfigManager();
        }
        return ConfigManager.instance;
    }
    /**
     * Gets the VS Code configuration section
     */
    getConfig() {
        return vscode.workspace.getConfiguration('sdlc');
    }
    /**
     * Gets a configuration value with type safety
     */
    get(key, defaultValue) {
        return this.getConfig().get(key, defaultValue);
    }
    /**
     * Gets the API URL
     */
    get apiUrl() {
        return this.get('apiUrl', DEFAULT_CONFIG.apiUrl);
    }
    /**
     * Gets the auto-refresh interval in seconds
     */
    get autoRefreshInterval() {
        return this.get('autoRefreshInterval', DEFAULT_CONFIG.autoRefreshInterval);
    }
    /**
     * Gets the default project ID
     */
    get defaultProjectId() {
        return this.get('defaultProjectId', DEFAULT_CONFIG.defaultProjectId);
    }
    /**
     * Gets whether notifications are enabled
     */
    get enableNotifications() {
        return this.get('enableNotifications', DEFAULT_CONFIG.enableNotifications);
    }
    /**
     * Gets whether AI Council is enabled
     */
    get aiCouncilEnabled() {
        return this.get('aiCouncilEnabled', DEFAULT_CONFIG.aiCouncilEnabled);
    }
    /**
     * Gets whether violation badge is shown
     */
    get showViolationBadge() {
        return this.get('showViolationBadge', DEFAULT_CONFIG.showViolationBadge);
    }
    /**
     * Gets all configuration as an object
     */
    getAll() {
        return {
            apiUrl: this.apiUrl,
            autoRefreshInterval: this.autoRefreshInterval,
            defaultProjectId: this.defaultProjectId,
            enableNotifications: this.enableNotifications,
            aiCouncilEnabled: this.aiCouncilEnabled,
            showViolationBadge: this.showViolationBadge,
        };
    }
    /**
     * Updates a configuration value
     */
    async update(key, value, target = vscode.ConfigurationTarget.Workspace) {
        await this.getConfig().update(key, value, target);
    }
    /**
     * Resets all configuration to defaults
     */
    async resetToDefaults() {
        const config = this.getConfig();
        const keys = Object.keys(DEFAULT_CONFIG);
        for (const key of keys) {
            await config.update(key, undefined, vscode.ConfigurationTarget.Workspace);
            await config.update(key, undefined, vscode.ConfigurationTarget.Global);
        }
    }
}
exports.ConfigManager = ConfigManager;
//# sourceMappingURL=config.js.map