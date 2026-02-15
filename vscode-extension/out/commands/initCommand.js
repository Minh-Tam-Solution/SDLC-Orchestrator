"use strict";
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
exports.InitCommandHandler = void 0;
exports.registerInitCommand = registerInitCommand;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const sdlcStructureService_1 = require("../services/sdlcStructureService");
const logger_1 = require("../utils/logger");
const telemetryService_1 = require("../services/telemetryService");
/**
 * SDLC Init Command Handler
 */
class InitCommandHandler {
    structureService;
    apiClient;
    authService;
    constructor(apiClient, authService) {
        this.structureService = new sdlcStructureService_1.SDLCStructureService();
        this.apiClient = apiClient;
        this.authService = authService;
    }
    /**
     * Execute the /init command
     */
    async execute(options = {}) {
        logger_1.Logger.info('Executing SDLC init command');
        // Get workspace root
        const workspaceRoot = this.getWorkspaceRoot();
        if (!workspaceRoot) {
            void vscode.window.showErrorMessage('No workspace folder open. Please open a folder first.');
            return false;
        }
        // Auth pre-check: warn user if not authenticated (server sync will fail)
        if (!options.offline && this.authService) {
            const isAuth = await this.authService.isAuthenticated();
            if (!isAuth) {
                const action = await vscode.window.showWarningMessage('You are not logged in to SDLC Orchestrator.\n\nProject will be created locally but cannot be registered with the backend until you log in.', { modal: true }, 'Login First', 'Continue Offline');
                if (action === 'Login First') {
                    await vscode.commands.executeCommand('sdlc.login');
                    // Re-check after login
                    const nowAuth = await this.authService.isAuthenticated();
                    if (!nowAuth) {
                        logger_1.Logger.warn('User cancelled login, continuing offline');
                        options.offline = true;
                    }
                }
                else if (action === 'Continue Offline') {
                    options.offline = true;
                }
                else {
                    return false; // User dismissed the dialog
                }
            }
        }
        // Check if already initialized
        if (this.structureService.hasSDLCConfig(workspaceRoot) && !options.force) {
            const action = await vscode.window.showWarningMessage('This project already has an SDLC configuration (.sdlc-config.json).', 'View Config', 'Reinitialize', 'Cancel');
            if (action === 'View Config') {
                await this.openConfig(workspaceRoot);
                return true;
            }
            else if (action !== 'Reinitialize') {
                return false;
            }
        }
        // Check for existing files and perform gap analysis
        const isEmptyFolder = this.structureService.isEmptyOrMinimalFolder(workspaceRoot);
        if (!isEmptyFolder) {
            // Existing project - show gap analysis
            return await this.handleExistingProject(workspaceRoot, options);
        }
        else {
            // Empty folder - create new structure
            return await this.handleNewProject(workspaceRoot, options);
        }
    }
    /**
     * Handle initialization for new (empty) projects
     */
    async handleNewProject(workspaceRoot, options) {
        logger_1.Logger.info('Initializing new SDLC project');
        // Step 1: Get project name
        const folderName = path.basename(workspaceRoot);
        const projectName = await vscode.window.showInputBox({
            prompt: 'Enter project name',
            value: this.formatProjectName(folderName),
            placeHolder: 'My Awesome Project',
            validateInput: (value) => {
                if (!value || value.trim().length < 2) {
                    return 'Project name must be at least 2 characters';
                }
                return null;
            },
        });
        if (!projectName) {
            return false;
        }
        // Step 2: Select tier
        const tier = await this.selectTier();
        if (!tier) {
            return false;
        }
        // Step 3: Confirm and create
        const createTemplates = await this.confirmCreateTemplates();
        // Step 4: Generate structure with progress
        const result = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Creating SDLC 6.0.5 structure...',
            cancellable: false,
        }, async (progress) => {
            progress.report({ increment: 0, message: 'Preparing...' });
            const serverUrl = this.getServerUrl(options.offline);
            progress.report({ increment: 30, message: 'Creating folders...' });
            const result = this.structureService.generateStructure(workspaceRoot, projectName, tier, {
                createTemplates: createTemplates,
                ...(serverUrl ? { serverUrl } : {}),
            });
            progress.report({ increment: 60, message: 'Finalizing...' });
            // Try to sync with server if online
            if (!options.offline && this.apiClient) {
                progress.report({ increment: 80, message: 'Registering with server...' });
                await this.syncWithServer(workspaceRoot, projectName, tier);
            }
            progress.report({ increment: 100, message: 'Done!' });
            return result;
        });
        if (result.success) {
            await this.showSuccessMessage(result.createdFolders, result.createdFiles, tier);
            await this.openGettingStarted(workspaceRoot);
            // Track telemetry (Sprint 147 - Product Truth Layer)
            void (0, telemetryService_1.trackProjectCreated)(`vscode-${path.basename(workspaceRoot)}`, tier);
            void (0, telemetryService_1.trackCommand)('sdlc.init', true);
            return true;
        }
        else {
            void vscode.window.showErrorMessage('Failed to create SDLC structure');
            void (0, telemetryService_1.trackCommand)('sdlc.init', false);
            return false;
        }
    }
    /**
     * Handle initialization for existing projects (gap analysis)
     */
    async handleExistingProject(workspaceRoot, options) {
        logger_1.Logger.info('Analyzing existing project for SDLC compliance');
        // Step 1: Select target tier
        const tier = await this.selectTier('Select the governance tier for gap analysis');
        if (!tier) {
            return false;
        }
        // Step 2: Perform gap analysis
        const analysis = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Analyzing project structure...',
            cancellable: false,
        }, () => {
            return Promise.resolve(this.structureService.analyzeExistingStructure(workspaceRoot, tier));
        });
        // Step 3: Show gap analysis results
        const action = await this.showGapAnalysisResults(analysis, tier);
        if (action === 'create') {
            // Create missing folders only
            const projectName = await this.getProjectName(workspaceRoot);
            if (!projectName) {
                return false;
            }
            const result = this.structureService.generateStructure(workspaceRoot, projectName, tier, { createTemplates: false });
            if (result.success) {
                // Sprint 172: Sync with server to register project in backend
                if (!options.offline && this.apiClient) {
                    await this.syncWithServer(workspaceRoot, projectName, tier);
                }
                void vscode.window.showInformationMessage(`Created ${result.createdFolders.length} folders and ${result.createdFiles.length} files`);
                // Track telemetry (Sprint 147 - Product Truth Layer)
                void (0, telemetryService_1.trackProjectCreated)(`vscode-${path.basename(workspaceRoot)}`, tier);
                void (0, telemetryService_1.trackCommand)('sdlc.init', true);
                return true;
            }
        }
        else if (action === 'config-only') {
            // Create only .sdlc-config.json
            const projectName = await this.getProjectName(workspaceRoot);
            if (!projectName) {
                return false;
            }
            const config = this.structureService.generateConfig(projectName, tier);
            const configPath = path.join(workspaceRoot, '.sdlc-config.json');
            const fs = await import('fs');
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
            // Sprint 172: Sync with server to register project in backend
            if (!options.offline && this.apiClient) {
                await this.syncWithServer(workspaceRoot, projectName, tier);
            }
            void vscode.window.showInformationMessage('Created .sdlc-config.json');
            // Track telemetry (Sprint 147 - Product Truth Layer)
            void (0, telemetryService_1.trackProjectCreated)(`vscode-${path.basename(workspaceRoot)}`, tier);
            void (0, telemetryService_1.trackCommand)('sdlc.init', true);
            return true;
        }
        return false;
    }
    /**
     * Select SDLC tier via quick pick
     */
    async selectTier(placeholder) {
        const items = Object.entries(sdlcStructureService_1.TIER_DESCRIPTIONS).map(([tier, info]) => ({
            label: info.label,
            description: info.teamSize,
            detail: info.description,
            tier: tier,
        }));
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: placeholder || 'Select SDLC governance tier',
            matchOnDescription: true,
            matchOnDetail: true,
        });
        return selected?.tier;
    }
    /**
     * Confirm whether to create template files
     */
    async confirmCreateTemplates() {
        const selection = await vscode.window.showQuickPick([
            {
                label: '$(file-add) Yes, create starter templates',
                description: 'Recommended for new projects',
                value: true,
            },
            {
                label: '$(folder) No, create folders only',
                description: 'I will add my own files',
                value: false,
            },
        ], {
            placeHolder: 'Create starter template files?',
        });
        return selection?.value ?? true;
    }
    /**
     * Show gap analysis results
     */
    async showGapAnalysisResults(analysis, tier) {
        // Create markdown content for webview
        const panel = vscode.window.createWebviewPanel('sdlc.gapAnalysis', 'SDLC 6.0.5 Gap Analysis', vscode.ViewColumn.One, { enableScripts: true });
        panel.webview.html = this.generateGapAnalysisHtml(analysis, tier);
        // Show quick pick for action
        const action = await vscode.window.showQuickPick([
            {
                label: '$(add) Create missing folders + config',
                description: `${analysis.missingFolders.length} folders to create`,
                value: 'create',
            },
            {
                label: '$(gear) Create .sdlc-config.json only',
                description: 'Keep existing structure',
                value: 'config-only',
            },
            {
                label: '$(close) Cancel',
                description: 'No changes',
                value: 'cancel',
            },
        ], {
            placeHolder: 'What would you like to do?',
        });
        panel.dispose();
        return action?.value ?? 'cancel';
    }
    /**
     * Generate HTML for gap analysis results
     */
    generateGapAnalysisHtml(analysis, tier) {
        const existingCount = analysis.existingFolders.length;
        const missingCount = analysis.missingFolders.length;
        const totalCount = existingCount + missingCount;
        const compliancePercent = Math.round((existingCount / totalCount) * 100);
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SDLC 6.0.5 Gap Analysis</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        h1 { color: var(--vscode-textLink-foreground); }
        .tier-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            font-weight: bold;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: var(--vscode-input-background);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background-color: ${compliancePercent >= 80 ? '#22c55e' : compliancePercent >= 50 ? '#eab308' : '#ef4444'};
            width: ${compliancePercent}%;
            transition: width 0.3s;
        }
        .section { margin: 20px 0; }
        .folder-list { list-style: none; padding: 0; }
        .folder-list li {
            padding: 8px;
            margin: 4px 0;
            border-radius: 4px;
            background-color: var(--vscode-input-background);
        }
        .existing { border-left: 3px solid #22c55e; }
        .missing { border-left: 3px solid #ef4444; }
        .suggestion { border-left: 3px solid #eab308; }
        .recommendation {
            padding: 12px;
            margin: 8px 0;
            background-color: var(--vscode-textBlockQuote-background);
            border-left: 3px solid var(--vscode-textLink-foreground);
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>SDLC 6.0.5 Gap Analysis</h1>
    <p>Target Tier: <span class="tier-badge">${tier}</span></p>

    <div class="section">
        <h2>Compliance Score: ${compliancePercent}%</h2>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <p>${existingCount} of ${totalCount} required folders found</p>
    </div>

    ${analysis.existingFolders.length > 0 ? `
    <div class="section">
        <h2>✅ Existing Folders (${existingCount})</h2>
        <ul class="folder-list">
            ${analysis.existingFolders.map(f => `<li class="existing">📁 ${f}</li>`).join('')}
        </ul>
    </div>
    ` : ''}

    ${analysis.missingFolders.length > 0 ? `
    <div class="section">
        <h2>❌ Missing Folders (${missingCount})</h2>
        <ul class="folder-list">
            ${analysis.missingFolders.map(f => `<li class="missing">📁 ${f}</li>`).join('')}
        </ul>
    </div>
    ` : ''}

    ${Object.keys(analysis.suggestedMappings).length > 0 ? `
    <div class="section">
        <h2>💡 Suggested Mappings</h2>
        <ul class="folder-list">
            ${Object.entries(analysis.suggestedMappings).map(([from, to]) => `<li class="suggestion">📁 ${from} → ${to}</li>`).join('')}
        </ul>
    </div>
    ` : ''}

    ${analysis.recommendations.length > 0 ? `
    <div class="section">
        <h2>📋 Recommendations</h2>
        ${analysis.recommendations.map(r => `<div class="recommendation">${r}</div>`).join('')}
    </div>
    ` : ''}
</body>
</html>`;
    }
    /**
     * Show success message with summary
     */
    async showSuccessMessage(folders, files, tier) {
        const message = `SDLC 6.0.5 project initialized! (${tier} tier)\n` +
            `Created ${folders.length} folders and ${files.length} files.`;
        const action = await vscode.window.showInformationMessage(message, 'Open Getting Started', 'View Gate Status');
        if (action === 'View Gate Status') {
            await vscode.commands.executeCommand('sdlc-gate-status.focus');
        }
    }
    /**
     * Open the Getting Started guide
     */
    async openGettingStarted(workspaceRoot) {
        const readmePath = path.join(workspaceRoot, 'README.md');
        const fs = await import('fs');
        if (fs.existsSync(readmePath)) {
            const doc = await vscode.workspace.openTextDocument(readmePath);
            await vscode.window.showTextDocument(doc, {
                preview: false,
                viewColumn: vscode.ViewColumn.One,
            });
        }
    }
    /**
     * Open the SDLC config file
     */
    async openConfig(workspaceRoot) {
        const configPath = path.join(workspaceRoot, '.sdlc-config.json');
        const doc = await vscode.workspace.openTextDocument(configPath);
        await vscode.window.showTextDocument(doc);
    }
    /**
     * Get workspace root folder
     */
    getWorkspaceRoot() {
        const folders = vscode.workspace.workspaceFolders;
        if (folders && folders.length > 0 && folders[0]) {
            return folders[0].uri.fsPath;
        }
        return undefined;
    }
    /**
     * Get project name from folder or user input
     */
    async getProjectName(workspaceRoot) {
        const config = this.structureService.readConfig(workspaceRoot);
        if (config?.project?.name) {
            return config.project.name;
        }
        const folderName = path.basename(workspaceRoot);
        return await vscode.window.showInputBox({
            prompt: 'Enter project name',
            value: this.formatProjectName(folderName),
        });
    }
    /**
     * Format folder name to project name
     */
    formatProjectName(folderName) {
        return folderName
            .replace(/[-_]/g, ' ')
            .replace(/\b\w/g, (c) => c.toUpperCase());
    }
    /**
     * Get server URL based on offline mode
     */
    getServerUrl(offline) {
        if (offline) {
            return undefined;
        }
        const config = vscode.workspace.getConfiguration('sdlc');
        return config.get('apiUrl');
    }
    /**
     * Sync project with SDLC Orchestrator server
     *
     * Returns true if sync succeeded, false otherwise.
     * Shows user-facing error messages on failure instead of silently swallowing.
     */
    async syncWithServer(workspaceRoot, projectName, tier) {
        if (!this.apiClient) {
            return false;
        }
        try {
            // Call server API to register project
            const response = await this.apiClient.initProject({
                name: projectName,
                tier: tier,
                source: 'vscode',
            });
            // Update local config with server-assigned ID
            if (response?.project_id) {
                this.structureService.updateConfig(workspaceRoot, {
                    project: {
                        id: response.project_id,
                        name: projectName,
                        slug: projectName.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
                    },
                    server: {
                        url: this.apiClient.getBaseUrl(),
                        connected: true,
                    },
                });
                logger_1.Logger.info(`Project synced with server: ${response.project_id}`);
                return true;
            }
            return false;
        }
        catch (error) {
            const statusCode = error?.statusCode ?? error?.response?.status ?? 0;
            const errorMsg = error instanceof Error ? error.message : String(error);
            logger_1.Logger.warn(`Failed to sync with server: [${statusCode}] ${errorMsg}`);
            if (statusCode === 401 || statusCode === 403) {
                const action = await vscode.window.showWarningMessage('Authentication failed. Please log in to register this project with the backend.', 'Login Now');
                if (action === 'Login Now') {
                    await vscode.commands.executeCommand('sdlc.login');
                }
            }
            else if (statusCode === 409) {
                // Project already exists - not really an error
                void vscode.window.showInformationMessage(`Project "${projectName}" is already registered in the backend.`);
                return true;
            }
            else if (statusCode === 0 || statusCode >= 500) {
                void vscode.window.showWarningMessage(`Cannot reach SDLC backend server. Project created locally. Error: ${errorMsg}`);
            }
            else {
                void vscode.window.showWarningMessage(`Failed to register project with backend (${statusCode}): ${errorMsg}`);
            }
            return false;
        }
    }
    /**
     * Run standalone gap analysis
     */
    async runGapAnalysis() {
        const workspaceRoot = this.getWorkspaceRoot();
        if (!workspaceRoot) {
            void vscode.window.showErrorMessage('No workspace folder open');
            return;
        }
        // Select tier for analysis
        const tier = await this.selectTier('Select tier to analyze compliance');
        if (!tier) {
            return;
        }
        // Run analysis
        const analysis = this.structureService.analyzeExistingStructure(workspaceRoot, tier);
        // Show results
        await this.showGapAnalysisResults(analysis, tier);
    }
}
exports.InitCommandHandler = InitCommandHandler;
/**
 * Register the init command
 */
function registerInitCommand(context, apiClient, authService) {
    const handler = new InitCommandHandler(apiClient, authService);
    // Main init command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.init', async () => {
        await handler.execute();
    }));
    // Init with offline mode
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.initOffline', async () => {
        await handler.execute({ offline: true });
    }));
    // Force reinitialize
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.reinit', async () => {
        await handler.execute({ force: true });
    }));
    // Gap analysis command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.gapAnalysis', async () => {
        await handler.runGapAnalysis();
    }));
    logger_1.Logger.info('SDLC init commands registered');
}
//# sourceMappingURL=initCommand.js.map