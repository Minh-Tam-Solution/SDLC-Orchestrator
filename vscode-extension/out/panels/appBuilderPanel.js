"use strict";
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
exports.AppBuilderPanel = void 0;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
/**
 * App Builder Panel Manager
 *
 * Manages the lifecycle and state of the App Builder webview panel.
 */
class AppBuilderPanel {
    codegenApi;
    blueprintProvider;
    static currentPanel;
    static viewType = 'sdlc.appBuilderPanel';
    _panel;
    _disposables = [];
    _blueprint;
    _isLocked = false;
    _generatedFiles = [];
    _isGenerating = false;
    constructor(panel, _extensionUri, codegenApi, blueprintProvider) {
        this.codegenApi = codegenApi;
        this.blueprintProvider = blueprintProvider;
        this._panel = panel;
        // Set initial HTML content
        this._update();
        // Listen for panel disposal
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from webview
        this._panel.webview.onDidReceiveMessage((message) => this._handleMessage(message), null, this._disposables);
        // Listen for panel visibility changes
        this._panel.onDidChangeViewState(() => {
            if (this._panel.visible) {
                this._update();
            }
        }, null, this._disposables);
        logger_1.Logger.info('AppBuilderPanel created');
    }
    /**
     * Create or show the App Builder panel
     */
    static createOrShow(extensionUri, codegenApi, blueprintProvider) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;
        // If panel exists, show it
        if (AppBuilderPanel.currentPanel) {
            AppBuilderPanel.currentPanel._panel.reveal(column);
            return AppBuilderPanel.currentPanel;
        }
        // Create new panel
        const panel = vscode.window.createWebviewPanel(AppBuilderPanel.viewType, '🏗️ App Builder', column || vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.joinPath(extensionUri, 'media'),
            ],
        });
        AppBuilderPanel.currentPanel = new AppBuilderPanel(panel, extensionUri, codegenApi, blueprintProvider);
        return AppBuilderPanel.currentPanel;
    }
    /**
     * Set the current blueprint
     */
    setBlueprint(blueprint) {
        this._blueprint = blueprint;
        this.blueprintProvider.setBlueprint(blueprint);
        this._postMessage({ command: 'blueprintUpdated', payload: blueprint });
    }
    /**
     * Set lock status
     */
    setLocked(locked) {
        this._isLocked = locked;
        this.blueprintProvider.setLocked(locked);
        this._postMessage({ command: 'lockStatusUpdated', payload: locked });
    }
    /**
     * Update generated files
     */
    updateGeneratedFiles(files) {
        this._generatedFiles = files;
        this._postMessage({ command: 'filesUpdated', payload: files });
    }
    /**
     * Update generation status
     */
    updateGenerationStatus(status) {
        this._isGenerating = status.isGenerating;
        this._postMessage({ command: 'generationStatus', payload: status });
    }
    /**
     * Dispose the panel
     */
    dispose() {
        AppBuilderPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
        logger_1.Logger.info('AppBuilderPanel disposed');
    }
    /**
     * Handle messages from webview
     */
    async _handleMessage(message) {
        switch (message.command) {
            case 'ready':
                // Webview is ready, send initial state
                this._sendInitialState();
                break;
            case 'loadBlueprint':
                await this._loadBlueprint();
                break;
            case 'saveBlueprint':
                await this._saveBlueprint();
                break;
            case 'newBlueprint':
                await this._createNewBlueprint();
                break;
            case 'updateBlueprint':
                this._updateBlueprint(message.payload);
                break;
            case 'addModule':
                await this._addModule();
                break;
            case 'removeModule':
                this._removeModule(message.payload);
                break;
            case 'addEntity':
                await this._addEntity(message.payload);
                break;
            case 'removeEntity':
                this._removeEntity(message.payload);
                break;
            case 'generate':
                await this._startGeneration();
                break;
            case 'magic':
                await vscode.commands.executeCommand('sdlc.magic');
                break;
            case 'lock':
                await this._lockBlueprint();
                break;
            case 'unlock':
                await this._unlockBlueprint();
                break;
            case 'preview':
                await vscode.commands.executeCommand('sdlc.preview');
                break;
            case 'openFile':
                await this._openGeneratedFile(message.payload);
                break;
            case 'saveAllFiles':
                await this._saveAllFiles();
                break;
            case 'loadTemplate':
                await this._loadTemplate(message.payload);
                break;
            default:
                logger_1.Logger.warn(`Unknown message command: ${message.command}`);
        }
    }
    /**
     * Send initial state to webview
     */
    _sendInitialState() {
        this._postMessage({
            command: 'initialState',
            payload: {
                blueprint: this._blueprint,
                isLocked: this._isLocked,
                generatedFiles: this._generatedFiles,
                isGenerating: this._isGenerating,
            },
        });
    }
    /**
     * Load blueprint from file
     */
    async _loadBlueprint() {
        const fileUri = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: false,
            filters: {
                'Blueprint Files': ['json'],
            },
            title: 'Load Blueprint',
        });
        const selectedFile = fileUri?.[0];
        if (!selectedFile) {
            return;
        }
        try {
            const content = await vscode.workspace.fs.readFile(selectedFile);
            const blueprint = JSON.parse(Buffer.from(content).toString('utf-8'));
            this.setBlueprint(blueprint);
            void vscode.window.showInformationMessage(`Blueprint "${blueprint.name}" loaded`);
        }
        catch (error) {
            void vscode.window.showErrorMessage(`Failed to load blueprint: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    /**
     * Save blueprint to file
     */
    async _saveBlueprint() {
        if (!this._blueprint) {
            void vscode.window.showWarningMessage('No blueprint to save');
            return;
        }
        const fileUri = await vscode.window.showSaveDialog({
            filters: {
                'Blueprint Files': ['json'],
            },
            defaultUri: vscode.Uri.file(`${this._blueprint.name.toLowerCase().replace(/\s+/g, '-')}.json`),
            title: 'Save Blueprint',
        });
        if (!fileUri) {
            return;
        }
        try {
            const content = JSON.stringify(this._blueprint, null, 2);
            await vscode.workspace.fs.writeFile(fileUri, Buffer.from(content, 'utf-8'));
            void vscode.window.showInformationMessage(`Blueprint saved to ${fileUri.fsPath}`);
        }
        catch (error) {
            void vscode.window.showErrorMessage(`Failed to save blueprint: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    /**
     * Create a new blueprint
     */
    async _createNewBlueprint() {
        const name = await vscode.window.showInputBox({
            prompt: 'Enter application name',
            placeHolder: 'My Application',
            validateInput: (value) => {
                if (!value || value.trim().length === 0) {
                    return 'Name is required';
                }
                return null;
            },
        });
        if (!name) {
            return;
        }
        const domains = [
            { label: 'E-commerce', value: 'ecommerce' },
            { label: 'HRM', value: 'hrm' },
            { label: 'CRM', value: 'crm' },
            { label: 'LMS', value: 'lms' },
            { label: 'Custom', value: 'custom' },
        ];
        const domain = await vscode.window.showQuickPick(domains, {
            placeHolder: 'Select business domain',
        });
        if (!domain) {
            return;
        }
        const blueprint = {
            name: name.trim(),
            version: '1.0.0',
            business_domain: domain.value,
            description: `${name.trim()} - ${domain.label} application`,
            modules: [],
        };
        this.setBlueprint(blueprint);
        void vscode.window.showInformationMessage(`Blueprint "${name}" created`);
    }
    /**
     * Update blueprint properties
     */
    _updateBlueprint(updates) {
        if (!this._blueprint || this._isLocked) {
            return;
        }
        this._blueprint = { ...this._blueprint, ...updates };
        this.blueprintProvider.setBlueprint(this._blueprint);
        this._postMessage({ command: 'blueprintUpdated', payload: this._blueprint });
    }
    /**
     * Add a new module
     */
    async _addModule() {
        if (this._isLocked) {
            void vscode.window.showWarningMessage('Blueprint is locked');
            return;
        }
        const name = await vscode.window.showInputBox({
            prompt: 'Enter module name',
            placeHolder: 'e.g., users, products, orders',
            validateInput: (value) => {
                if (!value || value.trim().length === 0) {
                    return 'Module name is required';
                }
                if (!/^[a-z][a-z0-9_]*$/.test(value.trim())) {
                    return 'Module name must be lowercase with underscores only';
                }
                return null;
            },
        });
        if (!name) {
            return;
        }
        if (this.blueprintProvider.addModule(name.trim())) {
            this._blueprint = this.blueprintProvider.getBlueprint();
            this._postMessage({ command: 'blueprintUpdated', payload: this._blueprint });
        }
    }
    /**
     * Remove a module
     */
    _removeModule(moduleName) {
        if (this._isLocked) {
            return;
        }
        if (this.blueprintProvider.removeModule(moduleName)) {
            this._blueprint = this.blueprintProvider.getBlueprint();
            this._postMessage({ command: 'blueprintUpdated', payload: this._blueprint });
        }
    }
    /**
     * Add an entity to a module
     */
    async _addEntity(moduleName) {
        if (this._isLocked) {
            void vscode.window.showWarningMessage('Blueprint is locked');
            return;
        }
        const entityName = await vscode.window.showInputBox({
            prompt: `Enter entity name for module "${moduleName}"`,
            placeHolder: 'e.g., User, Product, Order',
            validateInput: (value) => {
                if (!value || value.trim().length === 0) {
                    return 'Entity name is required';
                }
                if (!/^[A-Z][a-zA-Z0-9]*$/.test(value.trim())) {
                    return 'Entity name must be PascalCase';
                }
                return null;
            },
        });
        if (!entityName) {
            return;
        }
        if (this.blueprintProvider.addEntity(moduleName, entityName.trim())) {
            this._blueprint = this.blueprintProvider.getBlueprint();
            this._postMessage({ command: 'blueprintUpdated', payload: this._blueprint });
        }
    }
    /**
     * Remove an entity from a module
     */
    _removeEntity(data) {
        if (this._isLocked) {
            return;
        }
        if (this.blueprintProvider.removeEntity(data.moduleName, data.entityName)) {
            this._blueprint = this.blueprintProvider.getBlueprint();
            this._postMessage({ command: 'blueprintUpdated', payload: this._blueprint });
        }
    }
    /**
     * Start code generation
     */
    async _startGeneration() {
        if (!this._blueprint) {
            void vscode.window.showWarningMessage('No blueprint loaded');
            return;
        }
        await vscode.commands.executeCommand('sdlc.generate');
    }
    /**
     * Lock the blueprint
     */
    async _lockBlueprint() {
        await vscode.commands.executeCommand('sdlc.lock');
    }
    /**
     * Unlock the blueprint
     */
    async _unlockBlueprint() {
        await vscode.commands.executeCommand('sdlc.unlock');
    }
    /**
     * Open a generated file
     */
    async _openGeneratedFile(filePath) {
        const file = this._generatedFiles.find(f => f.path === filePath);
        if (!file) {
            return;
        }
        const doc = await vscode.workspace.openTextDocument({
            content: file.content,
            language: file.language,
        });
        await vscode.window.showTextDocument(doc);
    }
    /**
     * Save all generated files
     */
    async _saveAllFiles() {
        if (this._generatedFiles.length === 0) {
            void vscode.window.showWarningMessage('No files to save');
            return;
        }
        const folderUri = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            title: 'Select Output Directory',
        });
        const selectedFolder = folderUri?.[0];
        if (!selectedFolder) {
            return;
        }
        let savedCount = 0;
        for (const file of this._generatedFiles) {
            try {
                const targetPath = vscode.Uri.joinPath(selectedFolder, file.path);
                const dirPath = vscode.Uri.joinPath(targetPath, '..');
                try {
                    await vscode.workspace.fs.createDirectory(dirPath);
                }
                catch {
                    // Directory may exist
                }
                await vscode.workspace.fs.writeFile(targetPath, Buffer.from(file.content, 'utf-8'));
                savedCount++;
            }
            catch (error) {
                logger_1.Logger.error(`Failed to save ${file.path}: ${error}`);
            }
        }
        void vscode.window.showInformationMessage(`Saved ${savedCount} of ${this._generatedFiles.length} files`);
    }
    /**
     * Load a domain template
     */
    async _loadTemplate(domainId) {
        try {
            const blueprint = await this.codegenApi.getDomainTemplate(domainId);
            this.setBlueprint(blueprint);
            void vscode.window.showInformationMessage(`Template "${domainId}" loaded`);
        }
        catch (error) {
            void vscode.window.showErrorMessage(`Failed to load template: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    /**
     * Post message to webview
     */
    _postMessage(message) {
        this._panel.webview.postMessage(message);
    }
    /**
     * Update webview HTML
     */
    _update() {
        this._panel.webview.html = this._getHtmlForWebview();
    }
    /**
     * Get HTML content for webview
     */
    _getHtmlForWebview() {
        const webview = this._panel.webview;
        const nonce = this._getNonce();
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>App Builder</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 0;
            overflow: hidden;
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 280px;
            border-right: 1px solid var(--vscode-panel-border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header h1 {
            font-size: 16px;
            font-weight: 600;
            flex: 1;
        }
        .toolbar {
            padding: 8px 16px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .content {
            flex: 1;
            overflow: auto;
            padding: 16px;
        }
        .sidebar-header {
            padding: 12px;
            border-bottom: 1px solid var(--vscode-panel-border);
            font-weight: 600;
        }
        .sidebar-content {
            flex: 1;
            overflow: auto;
            padding: 8px;
        }
        .sidebar-footer {
            padding: 12px;
            border-top: 1px solid var(--vscode-panel-border);
        }
        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 12px;
            cursor: pointer;
            border-radius: 2px;
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        button.secondary {
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        button.danger {
            background-color: var(--vscode-errorForeground);
        }
        .module-card {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
        }
        .module-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .module-name {
            font-weight: 600;
            flex: 1;
        }
        .module-actions {
            display: flex;
            gap: 4px;
        }
        .module-actions button {
            padding: 4px 8px;
            font-size: 11px;
        }
        .entity-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        .entity-tag {
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .entity-tag .remove {
            cursor: pointer;
            opacity: 0.7;
        }
        .entity-tag .remove:hover {
            opacity: 1;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--vscode-descriptionForeground);
        }
        .empty-state h3 {
            margin-bottom: 8px;
        }
        .blueprint-info {
            padding: 12px;
            background-color: var(--vscode-textBlockQuote-background);
            border-radius: 6px;
            margin-bottom: 16px;
        }
        .blueprint-info h2 {
            font-size: 18px;
            margin-bottom: 4px;
        }
        .blueprint-info .meta {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
        }
        .lock-indicator {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            border-radius: 3px;
            font-size: 11px;
        }
        .lock-indicator.locked {
            background-color: var(--vscode-errorForeground);
        }
        .template-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 12px;
        }
        .template-card {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            padding: 12px;
            cursor: pointer;
            text-align: center;
        }
        .template-card:hover {
            border-color: var(--vscode-focusBorder);
        }
        .template-icon {
            font-size: 24px;
            margin-bottom: 8px;
        }
        .template-name {
            font-weight: 600;
            font-size: 13px;
        }
        .file-list {
            max-height: 200px;
            overflow: auto;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 6px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .file-item:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        .file-item .icon {
            margin-right: 6px;
        }
        .file-item .name {
            flex: 1;
        }
        .file-item .status {
            margin-left: 6px;
        }
        .progress-bar {
            height: 4px;
            background-color: var(--vscode-progressBar-background);
            border-radius: 2px;
            overflow: hidden;
        }
        .progress-bar .fill {
            height: 100%;
            background-color: var(--vscode-button-background);
            transition: width 0.3s;
        }
        .status-message {
            padding: 8px 12px;
            background-color: var(--vscode-textBlockQuote-background);
            border-radius: 4px;
            font-size: 12px;
            margin-top: 8px;
        }
        input, select {
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            padding: 6px 8px;
            border-radius: 2px;
            font-size: 12px;
            width: 100%;
        }
        input:focus, select:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }
        .form-group {
            margin-bottom: 12px;
        }
        .form-group label {
            display: block;
            margin-bottom: 4px;
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-header">
                📁 Templates
            </div>
            <div class="sidebar-content">
                <div class="template-grid" id="templates">
                    <div class="template-card" data-id="ecommerce">
                        <div class="template-icon">🛒</div>
                        <div class="template-name">E-commerce</div>
                    </div>
                    <div class="template-card" data-id="hrm">
                        <div class="template-icon">👥</div>
                        <div class="template-name">HRM</div>
                    </div>
                    <div class="template-card" data-id="crm">
                        <div class="template-icon">📊</div>
                        <div class="template-name">CRM</div>
                    </div>
                    <div class="template-card" data-id="lms">
                        <div class="template-icon">📚</div>
                        <div class="template-name">LMS</div>
                    </div>
                </div>
            </div>
            <div class="sidebar-footer">
                <div id="generated-files-section" style="display: none;">
                    <div style="font-weight: 600; margin-bottom: 8px;">📄 Generated Files</div>
                    <div class="file-list" id="file-list"></div>
                    <button id="btn-save-all" style="width: 100%; margin-top: 8px;">Save All</button>
                </div>
            </div>
        </div>
        <div class="main">
            <div class="header">
                <h1>🏗️ App Builder</h1>
                <span id="lock-status" class="lock-indicator" style="display: none;">🔓 Unlocked</span>
            </div>
            <div class="toolbar">
                <button id="btn-new">➕ New</button>
                <button id="btn-load" class="secondary">📂 Load</button>
                <button id="btn-save" class="secondary">💾 Save</button>
                <button id="btn-magic">✨ Magic</button>
                <button id="btn-generate">🚀 Generate</button>
                <button id="btn-lock">🔒 Lock</button>
            </div>
            <div class="content" id="content">
                <div id="empty-state" class="empty-state">
                    <h3>No Blueprint Loaded</h3>
                    <p>Create a new blueprint, load from file, or select a template</p>
                </div>
                <div id="blueprint-view" style="display: none;">
                    <div class="blueprint-info" id="blueprint-info"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h3>Modules</h3>
                        <button id="btn-add-module">➕ Add Module</button>
                    </div>
                    <div id="modules-container"></div>
                </div>
                <div id="generation-view" style="display: none;">
                    <div class="progress-bar">
                        <div class="fill" id="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="status-message" id="status-message">Preparing...</div>
                </div>
            </div>
        </div>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        let blueprint = null;
        let isLocked = false;
        let generatedFiles = [];
        let isGenerating = false;

        // DOM elements
        const emptyState = document.getElementById('empty-state');
        const blueprintView = document.getElementById('blueprint-view');
        const blueprintInfo = document.getElementById('blueprint-info');
        const modulesContainer = document.getElementById('modules-container');
        const generationView = document.getElementById('generation-view');
        const progressFill = document.getElementById('progress-fill');
        const statusMessage = document.getElementById('status-message');
        const lockStatus = document.getElementById('lock-status');
        const fileList = document.getElementById('file-list');
        const generatedFilesSection = document.getElementById('generated-files-section');

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            vscode.postMessage({ command: 'ready' });
        });

        // Button handlers
        document.getElementById('btn-new').addEventListener('click', () => {
            vscode.postMessage({ command: 'newBlueprint' });
        });

        document.getElementById('btn-load').addEventListener('click', () => {
            vscode.postMessage({ command: 'loadBlueprint' });
        });

        document.getElementById('btn-save').addEventListener('click', () => {
            vscode.postMessage({ command: 'saveBlueprint' });
        });

        document.getElementById('btn-magic').addEventListener('click', () => {
            vscode.postMessage({ command: 'magic' });
        });

        document.getElementById('btn-generate').addEventListener('click', () => {
            vscode.postMessage({ command: 'generate' });
        });

        document.getElementById('btn-lock').addEventListener('click', () => {
            if (isLocked) {
                vscode.postMessage({ command: 'unlock' });
            } else {
                vscode.postMessage({ command: 'lock' });
            }
        });

        document.getElementById('btn-add-module').addEventListener('click', () => {
            vscode.postMessage({ command: 'addModule' });
        });

        document.getElementById('btn-save-all').addEventListener('click', () => {
            vscode.postMessage({ command: 'saveAllFiles' });
        });

        // Template cards
        document.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', () => {
                vscode.postMessage({ command: 'loadTemplate', payload: card.dataset.id });
            });
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'initialState':
                    handleInitialState(message.payload);
                    break;
                case 'blueprintUpdated':
                    updateBlueprint(message.payload);
                    break;
                case 'lockStatusUpdated':
                    updateLockStatus(message.payload);
                    break;
                case 'filesUpdated':
                    updateFiles(message.payload);
                    break;
                case 'generationStatus':
                    updateGenerationStatus(message.payload);
                    break;
            }
        });

        function handleInitialState(state) {
            blueprint = state.blueprint;
            isLocked = state.isLocked;
            generatedFiles = state.generatedFiles || [];
            isGenerating = state.isGenerating;
            render();
        }

        function updateBlueprint(bp) {
            blueprint = bp;
            render();
        }

        function updateLockStatus(locked) {
            isLocked = locked;
            renderLockStatus();
        }

        function updateFiles(files) {
            generatedFiles = files;
            renderFiles();
        }

        function updateGenerationStatus(status) {
            isGenerating = status.isGenerating;
            if (isGenerating) {
                generationView.style.display = 'block';
                blueprintView.style.display = 'none';
                progressFill.style.width = (status.progress || 0) + '%';
                statusMessage.textContent = status.message || 'Generating...';
            } else {
                generationView.style.display = 'none';
                if (blueprint) {
                    blueprintView.style.display = 'block';
                }
            }
        }

        function render() {
            if (!blueprint) {
                emptyState.style.display = 'block';
                blueprintView.style.display = 'none';
                generationView.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            blueprintView.style.display = 'block';

            // Render blueprint info
            blueprintInfo.innerHTML = \`
                <h2>\${blueprint.name}</h2>
                <div class="meta">
                    v\${blueprint.version} | \${blueprint.business_domain} | \${blueprint.modules.length} modules
                </div>
                <div style="margin-top: 8px; font-size: 13px;">\${blueprint.description || ''}</div>
            \`;

            // Render modules
            modulesContainer.innerHTML = blueprint.modules.map(module => \`
                <div class="module-card">
                    <div class="module-header">
                        <span class="module-name">📦 \${module.name}</span>
                        <div class="module-actions">
                            <button onclick="addEntity('\${module.name}')" \${isLocked ? 'disabled' : ''}>+ Entity</button>
                            <button class="danger" onclick="removeModule('\${module.name}')" \${isLocked ? 'disabled' : ''}>×</button>
                        </div>
                    </div>
                    <div style="font-size: 12px; color: var(--vscode-descriptionForeground);">
                        \${module.description || ''}
                    </div>
                    <div class="entity-list">
                        \${module.entities.map(entity => \`
                            <span class="entity-tag">
                                \${entity}
                                <span class="remove" onclick="removeEntity('\${module.name}', '\${entity}')">\${isLocked ? '' : '×'}</span>
                            </span>
                        \`).join('')}
                    </div>
                </div>
            \`).join('');

            renderLockStatus();
            renderFiles();
        }

        function renderLockStatus() {
            if (blueprint) {
                lockStatus.style.display = 'inline-flex';
                lockStatus.textContent = isLocked ? '🔒 Locked' : '🔓 Unlocked';
                lockStatus.className = 'lock-indicator' + (isLocked ? ' locked' : '');
                document.getElementById('btn-lock').textContent = isLocked ? '🔓 Unlock' : '🔒 Lock';
            } else {
                lockStatus.style.display = 'none';
            }
        }

        function renderFiles() {
            if (generatedFiles.length > 0) {
                generatedFilesSection.style.display = 'block';
                fileList.innerHTML = generatedFiles.map(file => \`
                    <div class="file-item" onclick="openFile('\${file.path}')">
                        <span class="icon">\${getFileIcon(file.path)}</span>
                        <span class="name">\${file.path}</span>
                        <span class="status">\${file.syntax_valid ? '✅' : '❌'}</span>
                    </div>
                \`).join('');
            } else {
                generatedFilesSection.style.display = 'none';
            }
        }

        function getFileIcon(path) {
            const ext = path.split('.').pop();
            const icons = { py: '🐍', ts: '📘', tsx: '⚛️', js: '📒', json: '📋', md: '📝' };
            return icons[ext] || '📄';
        }

        function addEntity(moduleName) {
            vscode.postMessage({ command: 'addEntity', payload: moduleName });
        }

        function removeModule(moduleName) {
            vscode.postMessage({ command: 'removeModule', payload: moduleName });
        }

        function removeEntity(moduleName, entityName) {
            if (!isLocked) {
                vscode.postMessage({ command: 'removeEntity', payload: { moduleName, entityName } });
            }
        }

        function openFile(filePath) {
            vscode.postMessage({ command: 'openFile', payload: filePath });
        }
    </script>
</body>
</html>`;
    }
    /**
     * Generate nonce for CSP
     */
    _getNonce() {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}
exports.AppBuilderPanel = AppBuilderPanel;
//# sourceMappingURL=appBuilderPanel.js.map