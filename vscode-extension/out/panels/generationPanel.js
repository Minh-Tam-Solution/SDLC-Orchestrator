"use strict";
/**
 * Generation Panel - Real-time Code Generation View
 *
 * Displays live streaming progress of code generation with:
 * - Real-time file tree updates
 * - Quality gate status
 * - Progress indicators
 * - Error display with retry options
 *
 * Sprint 53 Day 3 - Streaming Integration
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
exports.GenerationPanel = void 0;
exports.registerGenerationPanelCommand = registerGenerationPanelCommand;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const sseClient_1 = require("../services/sseClient");
const config_1 = require("../utils/config");
/**
 * Generation Panel Manager
 *
 * Manages real-time code generation display with SSE streaming.
 */
class GenerationPanel {
    codegenApi;
    static currentPanel;
    static viewType = 'sdlc.generationPanel';
    _panel;
    _disposables = [];
    _sseClient = null;
    _state = null;
    _statusBarItem;
    constructor(panel, codegenApi) {
        this.codegenApi = codegenApi;
        this._panel = panel;
        // Create status bar item
        this._statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this._statusBarItem.command = 'sdlc.showGenerationPanel';
        // Set initial HTML
        this._update();
        // Listen for panel disposal
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from webview
        this._panel.webview.onDidReceiveMessage((message) => this._handleMessage(message), null, this._disposables);
        // Listen for visibility changes
        this._panel.onDidChangeViewState(() => {
            if (this._panel.visible) {
                this._update();
            }
        }, null, this._disposables);
        logger_1.Logger.info('GenerationPanel created');
    }
    /**
     * Create or show the generation panel
     */
    static createOrShow(_extensionUri, codegenApi) {
        const column = vscode.ViewColumn.Two;
        // If panel exists, reveal it
        if (GenerationPanel.currentPanel) {
            GenerationPanel.currentPanel._panel.reveal(column);
            return GenerationPanel.currentPanel;
        }
        // Create new panel
        const panel = vscode.window.createWebviewPanel(GenerationPanel.viewType, '🚀 Code Generation', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
        });
        GenerationPanel.currentPanel = new GenerationPanel(panel, codegenApi);
        return GenerationPanel.currentPanel;
    }
    /**
     * Start generation with streaming
     */
    async startGeneration(blueprint, outputPath) {
        try {
            // Initialize state
            const result = await this.codegenApi.startGeneration({
                blueprint,
                output_path: outputPath,
            });
            this._state = {
                sessionId: result.session_id,
                status: 'generating',
                startedAt: new Date(),
                blueprint,
                files: [],
                qualityGates: [],
                progress: 0,
                totalFiles: 0,
                totalLines: 0,
            };
            // Update UI
            this._updateStatusBar('generating');
            this._postMessage({ command: 'stateUpdated', payload: this._state });
            // Connect to SSE stream
            await this._connectToStream(result.session_id, outputPath);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to start generation: ${errorMessage}`);
            if (this._state) {
                this._state.status = 'failed';
                this._state.errorMessage = errorMessage;
                this._postMessage({ command: 'stateUpdated', payload: this._state });
            }
            this._updateStatusBar('failed');
            void vscode.window.showErrorMessage(`Generation failed: ${errorMessage}`);
        }
    }
    /**
     * Resume failed generation
     */
    async resumeGeneration(sessionId, outputPath) {
        try {
            const result = await this.codegenApi.resumeGeneration(sessionId);
            // Get previous session state
            const session = await this.codegenApi.getGenerationStatus(sessionId);
            this._state = {
                sessionId: result.session_id,
                status: 'generating',
                startedAt: new Date(),
                blueprint: session.blueprint || { name: 'Unknown', version: '1.0.0', business_domain: 'unknown', modules: [] },
                files: session.files || [],
                qualityGates: session.quality_gates || [],
                progress: 0,
                totalFiles: session.files?.length || 0,
                totalLines: session.files?.reduce((sum, f) => sum + f.lines, 0) || 0,
            };
            this._updateStatusBar('generating');
            this._postMessage({ command: 'stateUpdated', payload: this._state });
            await this._connectToStream(result.session_id, outputPath);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to resume generation: ${errorMessage}`);
            void vscode.window.showErrorMessage(`Resume failed: ${errorMessage}`);
        }
    }
    /**
     * Cancel current generation
     */
    async cancelGeneration() {
        if (!this._state || this._state.status !== 'generating') {
            return;
        }
        try {
            await this.codegenApi.cancelGeneration(this._state.sessionId);
            this._state.status = 'cancelled';
            this._postMessage({ command: 'stateUpdated', payload: this._state });
            this._updateStatusBar('cancelled');
            if (this._sseClient) {
                this._sseClient.disconnect();
                this._sseClient = null;
            }
            void vscode.window.showInformationMessage('Generation cancelled');
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to cancel generation: ${errorMessage}`);
        }
    }
    /**
     * Get current generation state
     */
    getState() {
        return this._state;
    }
    /**
     * Dispose the panel
     */
    dispose() {
        GenerationPanel.currentPanel = undefined;
        // Disconnect SSE
        if (this._sseClient) {
            this._sseClient.disconnect();
            this._sseClient = null;
        }
        // Dispose status bar
        this._statusBarItem.dispose();
        // Dispose panel
        this._panel.dispose();
        // Dispose all disposables
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
        logger_1.Logger.info('GenerationPanel disposed');
    }
    /**
     * Connect to SSE stream
     */
    async _connectToStream(sessionId, outputPath) {
        const config = config_1.ConfigManager.getInstance();
        const token = await this.codegenApi.getAuthToken();
        this._sseClient = (0, sseClient_1.createCodegenSSEClient)(config.apiUrl, sessionId, token);
        // Handle file generating event
        this._sseClient.on('file_generating', (event) => {
            const e = event;
            if (this._state) {
                this._state.currentFile = e.path;
                this._postMessage({
                    command: 'fileGenerating',
                    payload: { path: e.path },
                });
            }
        });
        // Handle file generated event
        this._sseClient.on('file_generated', (event) => {
            const e = event;
            if (this._state) {
                const syntaxValid = e.syntax_valid ?? true;
                const file = {
                    path: e.path,
                    content: e.content,
                    lines: e.lines,
                    language: e.language,
                    syntax_valid: syntaxValid,
                    status: syntaxValid ? 'valid' : 'error',
                };
                this._state.files.push(file);
                this._state.totalFiles++;
                this._state.totalLines += e.lines;
                this._state.progress = Math.min((this._state.files.length / (this._state.blueprint.modules.length * 5)) * 80, 80);
                this._postMessage({
                    command: 'fileGenerated',
                    payload: file,
                });
            }
        });
        // Handle quality gate started
        this._sseClient.on('quality_started', () => {
            if (this._state) {
                this._state.status = 'quality_check';
                this._state.progress = 80;
                this._updateStatusBar('quality_check');
                this._postMessage({
                    command: 'qualityStarted',
                    payload: {},
                });
            }
        });
        // Handle quality gate result
        this._sseClient.on('quality_gate', (event) => {
            const e = event;
            if (this._state) {
                const gate = {
                    gate_number: e.gate_number,
                    gate_name: e.gate_name,
                    status: e.status,
                    issues: e.issues,
                    duration_ms: e.duration_ms,
                };
                this._state.qualityGates.push(gate);
                this._state.progress = 80 + (this._state.qualityGates.length / 4) * 20;
                this._postMessage({
                    command: 'qualityGate',
                    payload: gate,
                });
            }
        });
        // Handle completion
        this._sseClient.on('completed', async (event) => {
            const e = event;
            if (this._state) {
                this._state.status = 'completed';
                this._state.progress = 100;
                this._state.totalFiles = e.total_files;
                this._state.totalLines = e.total_lines;
                this._updateStatusBar('completed');
                this._postMessage({
                    command: 'completed',
                    payload: {
                        totalFiles: e.total_files,
                        totalLines: e.total_lines,
                        durationMs: e.duration_ms,
                    },
                });
                // Write files to disk
                await this._writeFilesToDisk(outputPath);
                void vscode.window.showInformationMessage(`✅ Generated ${e.total_files} files (${e.total_lines} lines) in ${(e.duration_ms / 1000).toFixed(1)}s`, 'Open Folder', 'View Files').then(async (action) => {
                    if (action === 'Open Folder') {
                        const folderUri = vscode.Uri.file(outputPath);
                        await vscode.commands.executeCommand('revealInExplorer', folderUri);
                    }
                    else if (action === 'View Files' && this._state?.files[0]) {
                        const firstFile = vscode.Uri.file(`${outputPath}/${this._state.files[0].path}`);
                        await vscode.window.showTextDocument(firstFile);
                    }
                });
            }
            if (this._sseClient) {
                this._sseClient.disconnect();
                this._sseClient = null;
            }
        });
        // Handle checkpoint
        this._sseClient.on('checkpoint', (event) => {
            const e = event;
            this._postMessage({
                command: 'checkpoint',
                payload: {
                    filesCompleted: e.files_completed,
                    lastFilePath: e.last_file_path,
                },
            });
        });
        // Handle error
        this._sseClient.on('error', (event) => {
            const e = event;
            if (this._state) {
                this._state.status = 'failed';
                this._state.errorMessage = e.message;
                if (e.recovery_id) {
                    this._state.recoveryId = e.recovery_id;
                }
                this._updateStatusBar('failed');
                this._postMessage({
                    command: 'error',
                    payload: {
                        message: e.message,
                        recoveryId: e.recovery_id,
                    },
                });
            }
            void vscode.window.showErrorMessage(`Generation error: ${e.message}`, 'Retry', 'Dismiss').then(async (action) => {
                if (action === 'Retry' && this._state) {
                    await this.resumeGeneration(this._state.sessionId, outputPath);
                }
            });
            if (this._sseClient) {
                this._sseClient.disconnect();
                this._sseClient = null;
            }
        });
        // Handle connection error
        this._sseClient.onError((error) => {
            logger_1.Logger.error(`SSE connection error: ${error.message}`);
            if (this._state && this._state.status === 'generating') {
                this._state.status = 'failed';
                this._state.errorMessage = 'Connection lost';
                this._updateStatusBar('failed');
                this._postMessage({ command: 'stateUpdated', payload: this._state });
            }
        });
        // Connect
        await this._sseClient.connect();
    }
    /**
     * Write generated files to disk
     */
    async _writeFilesToDisk(outputPath) {
        if (!this._state) {
            return;
        }
        for (const file of this._state.files) {
            try {
                const targetPath = vscode.Uri.file(`${outputPath}/${file.path}`);
                const dirPath = vscode.Uri.file(targetPath.fsPath.substring(0, targetPath.fsPath.lastIndexOf('/')));
                try {
                    await vscode.workspace.fs.createDirectory(dirPath);
                }
                catch {
                    // Directory may exist
                }
                await vscode.workspace.fs.writeFile(targetPath, Buffer.from(file.content, 'utf-8'));
            }
            catch (error) {
                logger_1.Logger.error(`Failed to write file ${file.path}: ${error}`);
            }
        }
        logger_1.Logger.info(`Wrote ${this._state.files.length} files to ${outputPath}`);
    }
    /**
     * Handle messages from webview
     */
    async _handleMessage(message) {
        switch (message.command) {
            case 'ready':
                this._sendInitialState();
                break;
            case 'cancel':
                await this.cancelGeneration();
                break;
            case 'retry':
                if (this._state) {
                    const outputPath = await this._selectOutputDirectory();
                    if (outputPath) {
                        await this.resumeGeneration(this._state.sessionId, outputPath);
                    }
                }
                break;
            case 'openFile':
                await this._openFile(message.payload);
                break;
            case 'copyContent':
                await this._copyFileContent(message.payload);
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
            payload: this._state,
        });
    }
    /**
     * Select output directory
     */
    async _selectOutputDirectory() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        const options = {
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            title: 'Select Output Directory',
        };
        const firstWorkspace = workspaceFolders?.[0];
        if (firstWorkspace) {
            options.defaultUri = firstWorkspace.uri;
        }
        const folderUri = await vscode.window.showOpenDialog(options);
        const selectedFolder = folderUri?.[0];
        return selectedFolder?.fsPath;
    }
    /**
     * Open a file in editor
     */
    async _openFile(filePath) {
        const file = this._state?.files.find(f => f.path === filePath);
        if (!file) {
            return;
        }
        const doc = await vscode.workspace.openTextDocument({
            content: file.content,
            language: file.language,
        });
        await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
    }
    /**
     * Copy file content to clipboard
     */
    async _copyFileContent(filePath) {
        const file = this._state?.files.find(f => f.path === filePath);
        if (!file) {
            return;
        }
        await vscode.env.clipboard.writeText(file.content);
        void vscode.window.showInformationMessage(`Copied ${filePath} to clipboard`);
    }
    /**
     * Update status bar
     */
    _updateStatusBar(status) {
        switch (status) {
            case 'generating':
                this._statusBarItem.text = '$(sync~spin) Generating...';
                this._statusBarItem.backgroundColor = undefined;
                this._statusBarItem.show();
                break;
            case 'quality_check':
                this._statusBarItem.text = '$(beaker) Quality Gates...';
                this._statusBarItem.backgroundColor = undefined;
                this._statusBarItem.show();
                break;
            case 'completed':
                this._statusBarItem.text = '$(check) Generation Complete';
                this._statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.prominentBackground');
                this._statusBarItem.show();
                setTimeout(() => this._statusBarItem.hide(), 5000);
                break;
            case 'failed':
                this._statusBarItem.text = '$(error) Generation Failed';
                this._statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                this._statusBarItem.show();
                break;
            case 'cancelled':
                this._statusBarItem.text = '$(circle-slash) Generation Cancelled';
                this._statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                this._statusBarItem.show();
                setTimeout(() => this._statusBarItem.hide(), 3000);
                break;
            default:
                this._statusBarItem.hide();
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
        const nonce = this._getNonce();
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>Code Generation</title>
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
            padding: 16px;
            overflow-y: auto;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        .header h1 {
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header .status {
            font-size: 12px;
            padding: 4px 12px;
            border-radius: 12px;
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
        }
        .header .status.generating {
            background-color: var(--vscode-charts-blue);
        }
        .header .status.quality_check {
            background-color: var(--vscode-charts-yellow);
        }
        .header .status.completed {
            background-color: var(--vscode-charts-green);
        }
        .header .status.failed {
            background-color: var(--vscode-errorForeground);
        }
        .header .status.cancelled {
            background-color: var(--vscode-charts-orange);
        }
        .progress-section {
            margin-bottom: 20px;
        }
        .progress-bar-container {
            height: 8px;
            background-color: var(--vscode-progressBar-background);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .progress-bar {
            height: 100%;
            background-color: var(--vscode-progressBar-background);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .progress-bar.active {
            background: linear-gradient(90deg,
                var(--vscode-charts-blue) 0%,
                var(--vscode-charts-purple) 100%
            );
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .progress-bar.complete {
            background-color: var(--vscode-charts-green);
        }
        .progress-bar.error {
            background-color: var(--vscode-errorForeground);
        }
        .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            border-radius: 6px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        .stat-label {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            margin-top: 4px;
        }
        .section {
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .file-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            border-bottom: 1px solid var(--vscode-panel-border);
            cursor: pointer;
            transition: background-color 0.15s;
        }
        .file-item:last-child {
            border-bottom: none;
        }
        .file-item:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        .file-item.generating {
            background-color: var(--vscode-editor-selectionBackground);
        }
        .file-icon {
            margin-right: 8px;
            font-size: 14px;
        }
        .file-path {
            flex: 1;
            font-size: 13px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-lines {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            margin-right: 8px;
        }
        .file-status {
            font-size: 14px;
        }
        .quality-gates {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .gate-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 6px;
            border-left: 3px solid var(--vscode-panel-border);
        }
        .gate-item.passed {
            border-left-color: var(--vscode-charts-green);
        }
        .gate-item.failed {
            border-left-color: var(--vscode-errorForeground);
        }
        .gate-item.running {
            border-left-color: var(--vscode-charts-blue);
            animation: pulse 1s infinite;
        }
        .gate-icon {
            margin-right: 10px;
            font-size: 16px;
        }
        .gate-info {
            flex: 1;
        }
        .gate-name {
            font-weight: 500;
            font-size: 13px;
        }
        .gate-detail {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            margin-top: 2px;
        }
        .gate-duration {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
        }
        .error-box {
            padding: 16px;
            background-color: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
            border-radius: 6px;
            margin-bottom: 16px;
        }
        .error-title {
            font-weight: bold;
            color: var(--vscode-errorForeground);
            margin-bottom: 8px;
        }
        .error-message {
            font-size: 13px;
            margin-bottom: 12px;
        }
        .actions {
            display: flex;
            gap: 8px;
            margin-top: 16px;
        }
        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        button.secondary {
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        button.danger {
            background-color: var(--vscode-errorForeground);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--vscode-descriptionForeground);
        }
        .empty-state h2 {
            margin-bottom: 8px;
            font-size: 16px;
        }
        .current-file {
            padding: 12px;
            background-color: var(--vscode-textBlockQuote-background);
            border-radius: 6px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .current-file .spinner {
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div id="app">
        <div id="empty-state" class="empty-state">
            <h2>🚀 Code Generation</h2>
            <p>No generation in progress. Use the App Builder to start generating code.</p>
        </div>

        <div id="generation-view" style="display: none;">
            <div class="header">
                <h1>
                    <span>🚀</span>
                    <span id="blueprint-name">Code Generation</span>
                </h1>
                <span id="status-badge" class="status">Idle</span>
            </div>

            <div id="error-section" class="error-box" style="display: none;">
                <div class="error-title">⚠️ Generation Error</div>
                <div class="error-message" id="error-message"></div>
                <div class="actions">
                    <button id="btn-retry">🔄 Retry</button>
                    <button id="btn-dismiss" class="secondary">Dismiss</button>
                </div>
            </div>

            <div class="progress-section">
                <div class="progress-bar-container">
                    <div id="progress-bar" class="progress-bar" style="width: 0%"></div>
                </div>
                <div class="progress-info">
                    <span id="progress-text">Initializing...</span>
                    <span id="progress-percent">0%</span>
                </div>
            </div>

            <div id="current-file-section" class="current-file" style="display: none;">
                <span class="spinner">⚙️</span>
                <span>Generating: <strong id="current-file-name"></strong></span>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="stat-files">0</div>
                    <div class="stat-label">Files Generated</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="stat-lines">0</div>
                    <div class="stat-label">Lines of Code</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="stat-gates">0/4</div>
                    <div class="stat-label">Quality Gates</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">📁 Generated Files</div>
                <div class="file-list" id="file-list">
                    <div class="empty-state" style="padding: 20px;">
                        <p>Files will appear here as they are generated...</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">🔍 Quality Gates</div>
                <div class="quality-gates" id="quality-gates">
                    <div class="gate-item">
                        <span class="gate-icon">⏳</span>
                        <div class="gate-info">
                            <div class="gate-name">Waiting for file generation...</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="actions" id="action-buttons">
                <button id="btn-cancel" class="danger" style="display: none;">
                    ✕ Cancel Generation
                </button>
            </div>
        </div>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        // State
        let state = null;

        // DOM elements
        const emptyState = document.getElementById('empty-state');
        const generationView = document.getElementById('generation-view');
        const blueprintName = document.getElementById('blueprint-name');
        const statusBadge = document.getElementById('status-badge');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const progressPercent = document.getElementById('progress-percent');
        const currentFileSection = document.getElementById('current-file-section');
        const currentFileName = document.getElementById('current-file-name');
        const statFiles = document.getElementById('stat-files');
        const statLines = document.getElementById('stat-lines');
        const statGates = document.getElementById('stat-gates');
        const fileList = document.getElementById('file-list');
        const qualityGates = document.getElementById('quality-gates');
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');
        const btnCancel = document.getElementById('btn-cancel');
        const btnRetry = document.getElementById('btn-retry');
        const btnDismiss = document.getElementById('btn-dismiss');

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            vscode.postMessage({ command: 'ready' });
        });

        // Button handlers
        btnCancel.addEventListener('click', () => {
            vscode.postMessage({ command: 'cancel' });
        });

        btnRetry.addEventListener('click', () => {
            vscode.postMessage({ command: 'retry' });
        });

        btnDismiss.addEventListener('click', () => {
            errorSection.style.display = 'none';
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'initialState':
                    handleInitialState(message.payload);
                    break;
                case 'stateUpdated':
                    updateState(message.payload);
                    break;
                case 'fileGenerating':
                    showCurrentFile(message.payload.path);
                    break;
                case 'fileGenerated':
                    addFile(message.payload);
                    break;
                case 'qualityStarted':
                    showQualityGates();
                    break;
                case 'qualityGate':
                    updateQualityGate(message.payload);
                    break;
                case 'completed':
                    handleCompleted(message.payload);
                    break;
                case 'error':
                    handleError(message.payload);
                    break;
                case 'checkpoint':
                    handleCheckpoint(message.payload);
                    break;
            }
        });

        function handleInitialState(newState) {
            state = newState;
            render();
        }

        function updateState(newState) {
            state = newState;
            render();
        }

        function render() {
            if (!state) {
                emptyState.style.display = 'block';
                generationView.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            generationView.style.display = 'block';

            // Blueprint name
            blueprintName.textContent = state.blueprint?.name || 'Code Generation';

            // Status badge
            statusBadge.textContent = formatStatus(state.status);
            statusBadge.className = 'status ' + state.status;

            // Progress
            progressBar.style.width = state.progress + '%';
            progressBar.className = 'progress-bar ' + getProgressClass(state.status);
            progressPercent.textContent = Math.round(state.progress) + '%';
            progressText.textContent = getProgressText(state.status, state.currentFile);

            // Stats
            statFiles.textContent = state.totalFiles;
            statLines.textContent = formatNumber(state.totalLines);
            statGates.textContent = state.qualityGates.length + '/4';

            // Cancel button
            btnCancel.style.display = state.status === 'generating' || state.status === 'quality_check'
                ? 'inline-flex'
                : 'none';

            // Error section
            if (state.status === 'failed' && state.errorMessage) {
                errorSection.style.display = 'block';
                errorMessage.textContent = state.errorMessage;
            } else {
                errorSection.style.display = 'none';
            }

            // Render files
            renderFiles(state.files);

            // Render quality gates
            renderQualityGates(state.qualityGates, state.status);
        }

        function showCurrentFile(path) {
            currentFileSection.style.display = 'flex';
            currentFileName.textContent = path;
        }

        function addFile(file) {
            if (state) {
                state.files.push(file);
                state.totalFiles = state.files.length;
                state.totalLines += file.lines;
                renderFiles(state.files);
                statFiles.textContent = state.totalFiles;
                statLines.textContent = formatNumber(state.totalLines);
            }
            currentFileSection.style.display = 'none';
        }

        function showQualityGates() {
            if (state) {
                state.status = 'quality_check';
                render();
            }
        }

        function updateQualityGate(gate) {
            if (state) {
                const existingIndex = state.qualityGates.findIndex(g => g.gate_number === gate.gate_number);
                if (existingIndex >= 0) {
                    state.qualityGates[existingIndex] = gate;
                } else {
                    state.qualityGates.push(gate);
                }
                renderQualityGates(state.qualityGates, state.status);
                statGates.textContent = state.qualityGates.length + '/4';
            }
        }

        function handleCompleted(data) {
            if (state) {
                state.status = 'completed';
                state.progress = 100;
                state.totalFiles = data.totalFiles;
                state.totalLines = data.totalLines;
                render();
            }
        }

        function handleError(data) {
            if (state) {
                state.status = 'failed';
                state.errorMessage = data.message;
                state.recoveryId = data.recoveryId;
                render();
            }
        }

        function handleCheckpoint(data) {
            progressText.textContent = 'Checkpoint: ' + data.lastFilePath;
        }

        function renderFiles(files) {
            if (files.length === 0) {
                fileList.innerHTML = '<div class="empty-state" style="padding: 20px;"><p>Files will appear here...</p></div>';
                return;
            }

            fileList.innerHTML = files.map(file => {
                const icon = getFileIcon(file.path);
                const statusIcon = file.syntax_valid ? '✅' : '❌';
                return \`
                    <div class="file-item" onclick="openFile('\${file.path}')">
                        <span class="file-icon">\${icon}</span>
                        <span class="file-path">\${file.path}</span>
                        <span class="file-lines">\${file.lines} lines</span>
                        <span class="file-status">\${statusIcon}</span>
                    </div>
                \`;
            }).join('');
        }

        function renderQualityGates(gates, status) {
            if (status === 'generating') {
                qualityGates.innerHTML = \`
                    <div class="gate-item">
                        <span class="gate-icon">⏳</span>
                        <div class="gate-info">
                            <div class="gate-name">Waiting for file generation...</div>
                        </div>
                    </div>
                \`;
                return;
            }

            const allGates = [
                { gate_number: 1, gate_name: 'Syntax Validation', status: 'pending' },
                { gate_number: 2, gate_name: 'Security Scan (SAST)', status: 'pending' },
                { gate_number: 3, gate_name: 'Context Validation', status: 'pending' },
                { gate_number: 4, gate_name: 'Test Generation', status: 'pending' },
            ];

            gates.forEach(gate => {
                const idx = allGates.findIndex(g => g.gate_number === gate.gate_number);
                if (idx >= 0) {
                    allGates[idx] = gate;
                }
            });

            qualityGates.innerHTML = allGates.map(gate => {
                const statusClass = gate.status || 'pending';
                const icon = gate.status === 'passed' ? '✅' :
                            gate.status === 'failed' ? '❌' :
                            gate.status === 'running' ? '🔄' : '⏳';
                const duration = gate.duration_ms ? \`\${(gate.duration_ms / 1000).toFixed(1)}s\` : '';

                return \`
                    <div class="gate-item \${statusClass}">
                        <span class="gate-icon">\${icon}</span>
                        <div class="gate-info">
                            <div class="gate-name">Gate \${gate.gate_number}: \${gate.gate_name}</div>
                            \${gate.details ? \`<div class="gate-detail">\${gate.details}</div>\` : ''}
                        </div>
                        \${duration ? \`<span class="gate-duration">\${duration}</span>\` : ''}
                    </div>
                \`;
            }).join('');
        }

        function openFile(path) {
            vscode.postMessage({ command: 'openFile', payload: path });
        }

        function formatStatus(status) {
            const statusMap = {
                'idle': 'Idle',
                'generating': 'Generating...',
                'quality_check': 'Quality Check',
                'completed': 'Completed',
                'failed': 'Failed',
                'cancelled': 'Cancelled',
            };
            return statusMap[status] || status;
        }

        function getProgressClass(status) {
            switch (status) {
                case 'generating':
                case 'quality_check':
                    return 'active';
                case 'completed':
                    return 'complete';
                case 'failed':
                    return 'error';
                default:
                    return '';
            }
        }

        function getProgressText(status, currentFile) {
            switch (status) {
                case 'generating':
                    return currentFile ? \`Generating: \${currentFile}\` : 'Generating files...';
                case 'quality_check':
                    return 'Running quality gates...';
                case 'completed':
                    return 'Generation completed successfully!';
                case 'failed':
                    return 'Generation failed';
                case 'cancelled':
                    return 'Generation cancelled';
                default:
                    return 'Initializing...';
            }
        }

        function getFileIcon(path) {
            const ext = path.split('.').pop();
            const icons = {
                'py': '🐍',
                'ts': '📘',
                'tsx': '⚛️',
                'js': '📒',
                'jsx': '⚛️',
                'json': '📋',
                'md': '📝',
                'yaml': '⚙️',
                'yml': '⚙️',
                'html': '🌐',
                'css': '🎨',
                'sql': '🗃️',
            };
            return icons[ext] || '📄';
        }

        function formatNumber(num) {
            if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return num.toString();
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
exports.GenerationPanel = GenerationPanel;
/**
 * Register generation panel command
 */
function registerGenerationPanelCommand(context, codegenApi) {
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.showGenerationPanel', () => {
        GenerationPanel.createOrShow(context.extensionUri, codegenApi);
    }));
    logger_1.Logger.info('Generation panel command registered');
}
//# sourceMappingURL=generationPanel.js.map