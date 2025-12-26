/**
 * App Builder Webview Panel
 *
 * Main webview panel for the App Builder interface.
 * Provides visual blueprint editing, code generation controls,
 * and real-time streaming display.
 *
 * Sprint 53 Day 2 - App Builder Panel Implementation
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import type { CodegenApiService } from '../services/codegenApi';
import type { BlueprintProvider } from '../providers/blueprintProvider';
import type { AppBlueprint, GeneratedFile } from '../types/codegen';
/**
 * App Builder Panel Manager
 *
 * Manages the lifecycle and state of the App Builder webview panel.
 */
export declare class AppBuilderPanel {
    private readonly codegenApi;
    private readonly blueprintProvider;
    static currentPanel: AppBuilderPanel | undefined;
    private static readonly viewType;
    private readonly _panel;
    private _disposables;
    private _blueprint;
    private _isLocked;
    private _generatedFiles;
    private _isGenerating;
    private constructor();
    /**
     * Create or show the App Builder panel
     */
    static createOrShow(extensionUri: vscode.Uri, codegenApi: CodegenApiService, blueprintProvider: BlueprintProvider): AppBuilderPanel;
    /**
     * Set the current blueprint
     */
    setBlueprint(blueprint: AppBlueprint): void;
    /**
     * Set lock status
     */
    setLocked(locked: boolean): void;
    /**
     * Update generated files
     */
    updateGeneratedFiles(files: GeneratedFile[]): void;
    /**
     * Update generation status
     */
    updateGenerationStatus(status: {
        isGenerating: boolean;
        currentFile?: string;
        progress?: number;
        message?: string;
    }): void;
    /**
     * Dispose the panel
     */
    dispose(): void;
    /**
     * Handle messages from webview
     */
    private _handleMessage;
    /**
     * Send initial state to webview
     */
    private _sendInitialState;
    /**
     * Load blueprint from file
     */
    private _loadBlueprint;
    /**
     * Save blueprint to file
     */
    private _saveBlueprint;
    /**
     * Create a new blueprint
     */
    private _createNewBlueprint;
    /**
     * Update blueprint properties
     */
    private _updateBlueprint;
    /**
     * Add a new module
     */
    private _addModule;
    /**
     * Remove a module
     */
    private _removeModule;
    /**
     * Add an entity to a module
     */
    private _addEntity;
    /**
     * Remove an entity from a module
     */
    private _removeEntity;
    /**
     * Start code generation
     */
    private _startGeneration;
    /**
     * Lock the blueprint
     */
    private _lockBlueprint;
    /**
     * Unlock the blueprint
     */
    private _unlockBlueprint;
    /**
     * Open a generated file
     */
    private _openGeneratedFile;
    /**
     * Save all generated files
     */
    private _saveAllFiles;
    /**
     * Load a domain template
     */
    private _loadTemplate;
    /**
     * Post message to webview
     */
    private _postMessage;
    /**
     * Update webview HTML
     */
    private _update;
    /**
     * Get HTML content for webview
     */
    private _getHtmlForWebview;
    /**
     * Generate nonce for CSP
     */
    private _getNonce;
}
//# sourceMappingURL=appBuilderPanel.d.ts.map