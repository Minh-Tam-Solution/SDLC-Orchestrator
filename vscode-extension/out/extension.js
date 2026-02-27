"use strict";
/**
 * SDLC Orchestrator VS Code Extension
 *
 * Main entry point for the VS Code extension providing:
 * - Gate status sidebar (G0-G5 progress monitoring)
 * - Inline AI chat (Copilot-style @gate commands)
 * - Compliance violation tracking
 * - App Builder with code generation (Sprint 53)
 * - Integration with SDLC Orchestrator backend
 *
 * Sprint 53 - App Builder + Contract Lock
 * @version 0.2.0
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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const apiClient_1 = require("./services/apiClient");
const authService_1 = require("./services/authService");
const cacheService_1 = require("./services/cacheService");
const codegenApi_1 = require("./services/codegenApi");
const gateStatusView_1 = require("./views/gateStatusView");
const violationsView_1 = require("./views/violationsView");
const projectsView_1 = require("./views/projectsView");
const complianceChat_1 = require("./views/complianceChat");
const contextPanel_1 = require("./views/contextPanel");
const logger_1 = require("./utils/logger");
const config_1 = require("./utils/config");
const errors_1 = require("./utils/errors");
const initCommand_1 = require("./commands/initCommand");
const generateCommand_1 = require("./commands/generateCommand");
const magicCommand_1 = require("./commands/magicCommand");
const lockCommand_1 = require("./commands/lockCommand");
const previewCommand_1 = require("./commands/previewCommand");
const resumeCommand_1 = require("./commands/resumeCommand");
const specValidationCommand_1 = require("./commands/specValidationCommand");
const connectGithubCommand_1 = require("./commands/connectGithubCommand");
const e2eValidateCommand_1 = require("./commands/e2eValidateCommand");
const e2eCrossRefCommand_1 = require("./commands/e2eCrossRefCommand");
const ssotValidator_1 = require("./validation/ssotValidator");
const sdlcStructureService_1 = require("./services/sdlcStructureService");
const blueprintProvider_1 = require("./providers/blueprintProvider");
const appBuilderPanel_1 = require("./panels/appBuilderPanel");
const generationPanel_1 = require("./panels/generationPanel");
const projectDetector_1 = require("./services/projectDetector");
const gateApprovalCommand_1 = require("./commands/gateApprovalCommand");
const evidenceSubmissionCommand_1 = require("./commands/evidenceSubmissionCommand");
const state = {
    apiClient: undefined,
    authService: undefined,
    cacheService: undefined,
    codegenApi: undefined,
    projectDetector: undefined,
    gateStatusProvider: undefined,
    violationsProvider: undefined,
    projectsProvider: undefined,
    blueprintProvider: undefined,
    contextPanelProvider: undefined,
    contextStatusBar: undefined,
    chatParticipant: undefined,
    ssotValidator: undefined,
    refreshInterval: undefined,
};
/**
 * Activates the SDLC Orchestrator extension
 *
 * This function is called when the extension is activated, which happens
 * on VS Code startup (onStartupFinished activation event).
 *
 * @param context - VS Code extension context for managing subscriptions
 */
async function activate(context) {
    logger_1.Logger.info('SDLC Orchestrator extension activating...');
    try {
        // Initialize configuration manager
        const config = config_1.ConfigManager.getInstance();
        // Initialize services (synchronous - won't fail)
        state.authService = new authService_1.AuthService(context);
        state.apiClient = new apiClient_1.ApiClient(context, state.authService);
        state.cacheService = new cacheService_1.CacheService(context);
        state.codegenApi = new codegenApi_1.CodegenApiService(context, state.authService);
        // Initialize Project Detector (Sprint 127 - Auto-Detect Project)
        state.projectDetector = projectDetector_1.ProjectDetector.getInstance(state.apiClient);
        // CRITICAL FIX (Sprint 136): Register TreeDataProviders BEFORE any async operations
        // This prevents "There is no data provider registered" errors when:
        // - Backend is unavailable
        // - Authentication check fails
        // - Network timeout occurs
        // Initialize view providers with cache support
        state.gateStatusProvider = new gateStatusView_1.GateStatusProvider(state.apiClient, state.cacheService);
        state.violationsProvider = new violationsView_1.ViolationsProvider(state.apiClient, state.cacheService);
        state.projectsProvider = new projectsView_1.ProjectsProvider(state.apiClient, state.cacheService, state.projectDetector);
        // Initialize Blueprint Provider (Sprint 53 Day 2)
        state.blueprintProvider = new blueprintProvider_1.BlueprintProvider();
        // Initialize Context Panel Provider (Sprint 81 + Sprint 127 Auto-Detect)
        state.contextPanelProvider = new contextPanel_1.ContextPanelProvider(state.apiClient, state.cacheService, state.projectDetector);
        state.contextStatusBar = new contextPanel_1.ContextStatusBarItem();
        // Register tree data providers IMMEDIATELY (before async operations)
        // This ensures views always have a provider, even if later steps fail
        context.subscriptions.push(vscode.window.registerTreeDataProvider('sdlc-context', state.contextPanelProvider), vscode.window.registerTreeDataProvider('sdlc-gate-status', state.gateStatusProvider), vscode.window.registerTreeDataProvider('sdlc-violations', state.violationsProvider), vscode.window.registerTreeDataProvider('sdlc-projects', state.projectsProvider), vscode.window.registerTreeDataProvider('sdlc-blueprint', state.blueprintProvider));
        logger_1.Logger.info('TreeDataProviders registered successfully');
        // NOW check authentication status (async - may fail)
        let isAuthenticated = false;
        try {
            isAuthenticated = await state.authService.isAuthenticated();
        }
        catch (authError) {
            logger_1.Logger.warn(`Authentication check failed (offline mode): ${authError instanceof Error ? authError.message : String(authError)}`);
            // Continue with unauthenticated state - views will show appropriate messages
        }
        await vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', isAuthenticated);
        // Register ALL commands first (must succeed even if optional features fail)
        // Context Panel commands (Sprint 81)
        (0, contextPanel_1.registerContextCommands)(context, state.contextPanelProvider, state.contextStatusBar);
        // Core commands
        registerCommands(context);
        // Init commands (SDLC 6.0.6 project initialization)
        (0, initCommand_1.registerInitCommand)(context, state.apiClient, state.authService);
        // App Builder commands (Sprint 53)
        (0, generateCommand_1.registerGenerateCommand)(context, state.codegenApi);
        (0, magicCommand_1.registerMagicCommand)(context, state.codegenApi);
        (0, lockCommand_1.registerLockCommand)(context, state.codegenApi);
        (0, lockCommand_1.registerLockStatusCommand)(context, state.codegenApi);
        (0, previewCommand_1.registerPreviewCommand)(context, state.codegenApi);
        (0, resumeCommand_1.registerResumeCommand)(context, state.codegenApi);
        // Specification Validation commands (Sprint 126 - S126-06)
        (0, specValidationCommand_1.registerSpecValidationCommand)(context, state.codegenApi);
        // GitHub Integration commands (Sprint 129 Day 3)
        (0, connectGithubCommand_1.registerGithubCommands)(context, state.apiClient);
        // E2E Testing commands (Sprint 139 - RFC-SDLC-602)
        (0, e2eValidateCommand_1.registerE2EValidateCommand)(context);
        (0, e2eCrossRefCommand_1.registerE2ECrossRefCommand)(context);
        // SSOT Validation commands (Sprint 141 - RFC-SDLC-602)
        state.ssotValidator = (0, ssotValidator_1.registerSSOTCommands)(context);
        // Gate Governance commands (Sprint 173 - ADR-053 Governance Loop)
        (0, gateApprovalCommand_1.registerGateApprovalCommands)(context, state.apiClient);
        (0, evidenceSubmissionCommand_1.registerEvidenceSubmissionCommand)(context, state.apiClient);
        // Blueprint commands (Sprint 53 Day 2)
        (0, blueprintProvider_1.registerBlueprintCommands)(context, state.blueprintProvider);
        // App Builder Panel command (Sprint 53 Day 2)
        context.subscriptions.push(vscode.commands.registerCommand('sdlc.openAppBuilder', () => {
            if (state.codegenApi && state.blueprintProvider) {
                appBuilderPanel_1.AppBuilderPanel.createOrShow(context.extensionUri, state.codegenApi, state.blueprintProvider);
            }
            else {
                void vscode.window.showErrorMessage('Services not initialized');
            }
        }));
        // Generation Panel command (Sprint 53 Day 3)
        (0, generationPanel_1.registerGenerationPanelCommand)(context, state.codegenApi);
        logger_1.Logger.info('All commands registered successfully');
        // Register chat participant (optional — requires VSCode 1.93+ Chat API)
        try {
            state.chatParticipant = new complianceChat_1.ComplianceChatParticipant(state.apiClient);
            const chatParticipantDisposable = vscode.chat.createChatParticipant('sdlc-orchestrator.gate', state.chatParticipant.handleChatRequest.bind(state.chatParticipant));
            chatParticipantDisposable.iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'sdlc-icon.svg');
            context.subscriptions.push(chatParticipantDisposable);
        }
        catch (chatError) {
            logger_1.Logger.warn(`Chat participant registration failed (requires VSCode 1.93+): ${chatError instanceof Error ? chatError.message : String(chatError)}`);
        }
        // Check for empty folder and prompt for initialization
        await checkAndPromptForInit(context);
        // Setup auto-refresh
        setupAutoRefresh(config.autoRefreshInterval);
        // Listen for configuration changes
        context.subscriptions.push(vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration('sdlc')) {
                handleConfigurationChange();
            }
        }));
        // Show welcome message on first activation
        const hasShownWelcome = context.globalState.get('sdlc.hasShownWelcome');
        if (!hasShownWelcome) {
            await showWelcomeMessage();
            await context.globalState.update('sdlc.hasShownWelcome', true);
        }
        // Auto-detect project on activation (Sprint 127)
        if (state.projectDetector) {
            const project = await state.projectDetector.getCurrentProject();
            if (project) {
                logger_1.Logger.info(`Auto-detected project: ${project.name} (${project.uuid}) from ${project.source}`);
            }
            else {
                logger_1.Logger.warn('No project auto-detected from workspace');
            }
        }
        // Listen for workspace folder changes to invalidate project cache
        context.subscriptions.push(vscode.workspace.onDidChangeWorkspaceFolders(() => {
            if (state.projectDetector) {
                state.projectDetector.invalidateCache();
                logger_1.Logger.info('Project cache invalidated due to workspace folder change');
            }
        }));
        // Initial data load if authenticated
        if (isAuthenticated) {
            await refreshAllViews();
        }
        logger_1.Logger.info('SDLC Orchestrator extension activated successfully');
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger_1.Logger.error(`Extension activation failed: ${errorMessage}`);
        void vscode.window.showErrorMessage(`SDLC Orchestrator activation failed: ${errorMessage}`);
    }
}
/**
 * Deactivates the extension and cleans up resources
 */
function deactivate() {
    logger_1.Logger.info('SDLC Orchestrator extension deactivating...');
    // Clear refresh interval
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
        state.refreshInterval = undefined;
    }
    // Cleanup services
    state.apiClient = undefined;
    state.authService = undefined;
    state.cacheService = undefined;
    state.codegenApi = undefined;
    state.gateStatusProvider = undefined;
    state.violationsProvider = undefined;
    state.projectsProvider = undefined;
    state.chatParticipant = undefined;
    // Cleanup Context Panel (Sprint 81)
    if (state.contextPanelProvider) {
        state.contextPanelProvider.dispose();
        state.contextPanelProvider = undefined;
    }
    if (state.contextStatusBar) {
        state.contextStatusBar.dispose();
        state.contextStatusBar = undefined;
    }
    // Cleanup SSOT Validator (Sprint 141)
    if (state.ssotValidator) {
        state.ssotValidator.dispose();
        state.ssotValidator = undefined;
    }
    logger_1.Logger.info('SDLC Orchestrator extension deactivated');
}
/**
 * Registers all extension commands
 */
function registerCommands(context) {
    // Refresh gates command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.refreshGates', async () => {
        await refreshAllViews();
        void vscode.window.showInformationMessage('Gate status refreshed');
    }));
    // Open gate in browser command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.openGate', (gateId) => {
        const config = config_1.ConfigManager.getInstance();
        const url = `${config.apiUrl.replace('/api', '')}/app/gates/${gateId}`;
        void vscode.env.openExternal(vscode.Uri.parse(url));
    }));
    // Select project command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.selectProject', async () => {
        await selectProject();
    }));
    // Login command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.login', async () => {
        await handleLogin();
    }));
    // Logout command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.logout', async () => {
        await handleLogout();
    }));
    // Show violation details command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.showViolationDetails', (violationId) => {
        void showViolationDetails(violationId);
    }));
    // Fix violation command
    context.subscriptions.push(vscode.commands.registerCommand('sdlc.fixViolation', async (violationId) => {
        await fixViolation(violationId);
    }));
}
/**
 * Sets up automatic refresh interval for gate status
 */
function setupAutoRefresh(intervalSeconds) {
    // Clear existing interval
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
    }
    // Setup new interval (convert seconds to milliseconds)
    const intervalMs = intervalSeconds * 1000;
    state.refreshInterval = setInterval(() => {
        void refreshAllViews();
    }, intervalMs);
    logger_1.Logger.info(`Auto-refresh set to ${intervalSeconds} seconds`);
}
/**
 * Handles configuration changes
 */
function handleConfigurationChange() {
    const config = config_1.ConfigManager.getInstance();
    // Update auto-refresh interval
    setupAutoRefresh(config.autoRefreshInterval);
    // Update API client base URL
    if (state.apiClient) {
        state.apiClient.updateBaseUrl(config.apiUrl);
    }
    logger_1.Logger.info('Configuration updated');
}
/**
 * Refreshes all view providers
 */
async function refreshAllViews() {
    // Don't attempt to refresh if not authenticated
    if (state.authService) {
        const isAuthenticated = await state.authService.isAuthenticated();
        if (!isAuthenticated) {
            logger_1.Logger.debug('Skipping refresh - not authenticated');
            return;
        }
    }
    try {
        const promises = [];
        // Refresh Context Panel first (Sprint 81)
        if (state.contextPanelProvider) {
            promises.push(state.contextPanelProvider.refresh());
        }
        if (state.gateStatusProvider) {
            promises.push(state.gateStatusProvider.refresh());
        }
        if (state.violationsProvider) {
            promises.push(state.violationsProvider.refresh());
        }
        if (state.projectsProvider) {
            promises.push(state.projectsProvider.refresh());
        }
        await Promise.all(promises);
        // Update status bar after refresh (Sprint 81)
        if (state.contextStatusBar && state.apiClient) {
            const projectId = state.apiClient.getCurrentProjectId();
            if (projectId) {
                try {
                    const overlay = await state.apiClient.getContextOverlay(projectId);
                    state.contextStatusBar.update(overlay);
                }
                catch {
                    // Status bar will show error state via contextPanelProvider
                }
            }
        }
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logger_1.Logger.error(`Failed to refresh views: ${errorMessage}`);
    }
}
/**
 * Handles user login flow
 */
async function handleLogin() {
    if (!state.authService) {
        void vscode.window.showErrorMessage('Auth service not initialized');
        return;
    }
    try {
        // Show login options
        const loginMethod = await vscode.window.showQuickPick([
            { label: '$(key) API Token', description: 'Never expires - Recommended for VS Code (sdlc_live_*)', value: 'token' },
            { label: '$(mail) Email & Password', description: 'Login with email and password (JWT expires in 8 hours)', value: 'email' },
            { label: '$(github) GitHub OAuth', description: 'Login with GitHub', value: 'github' },
        ], { placeHolder: 'Select login method' });
        if (!loginMethod) {
            return;
        }
        if (loginMethod.value === 'email') {
            // Email/Password login
            const email = await vscode.window.showInputBox({
                prompt: 'Enter your email address',
                placeHolder: 'admin@sdlc-orchestrator.io',
                validateInput: (value) => {
                    if (!value || !value.includes('@')) {
                        return 'Please enter a valid email address';
                    }
                    return null;
                },
            });
            if (!email) {
                return;
            }
            const password = await vscode.window.showInputBox({
                prompt: 'Enter your password',
                password: true,
                placeHolder: 'Your password',
                validateInput: (value) => {
                    if (!value || value.length < 6) {
                        return 'Password must be at least 6 characters';
                    }
                    return null;
                },
            });
            if (!password) {
                return;
            }
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Logging in...',
                cancellable: false,
            }, async () => {
                await state.authService.loginWithEmailPassword(email, password);
            });
            await vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', true);
            await refreshAllViews();
            void vscode.window.showInformationMessage(`Successfully logged in as ${email}`);
        }
        else if (loginMethod.value === 'token') {
            const token = await vscode.window.showInputBox({
                prompt: 'Enter your SDLC Orchestrator API token (JWT)',
                password: true,
                placeHolder: 'Paste your API token here',
                validateInput: (value) => {
                    if (!value || value.length < 10) {
                        return 'Please enter a valid API token';
                    }
                    return null;
                },
            });
            if (token) {
                await state.authService.setToken(token);
                await vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', true);
                await refreshAllViews();
                void vscode.window.showInformationMessage('Successfully logged in to SDLC Orchestrator');
            }
        }
        else if (loginMethod.value === 'github') {
            // GitHub OAuth device flow
            await state.authService.loginWithGitHub();
            await vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', true);
            await refreshAllViews();
            void vscode.window.showInformationMessage('Successfully logged in via GitHub');
        }
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
            includeActions: true,
        });
    }
}
/**
 * Handles user logout
 */
async function handleLogout() {
    if (!state.authService) {
        return;
    }
    try {
        await state.authService.logout();
        await vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', false);
        // Clear views
        if (state.gateStatusProvider) {
            state.gateStatusProvider.clear();
        }
        if (state.violationsProvider) {
            state.violationsProvider.clear();
        }
        if (state.projectsProvider) {
            state.projectsProvider.clear();
        }
        void vscode.window.showInformationMessage('Successfully logged out');
        // Clear cache on logout
        if (state.cacheService) {
            await state.cacheService.clear();
        }
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}
/**
 * Shows project selection quick pick
 */
async function selectProject() {
    if (!state.apiClient) {
        void vscode.window.showErrorMessage('API client not initialized');
        return;
    }
    try {
        const projects = await state.apiClient.getProjects();
        if (projects.length === 0) {
            void vscode.window.showInformationMessage('No projects found');
            return;
        }
        const items = projects.map((p) => ({
            label: p.name,
            description: p.description,
            detail: `ID: ${p.id} | Status: ${p.status}`,
            projectId: p.id,
        }));
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a project to monitor',
        });
        if (selected) {
            // Update configuration with selected project
            await vscode.workspace
                .getConfiguration('sdlc')
                .update('defaultProjectId', selected.projectId, vscode.ConfigurationTarget.Workspace);
            // Refresh views with new project
            await refreshAllViews();
            void vscode.window.showInformationMessage(`Selected project: ${selected.label}`);
        }
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
            includeActions: true,
        });
    }
}
/**
 * Shows violation details in a webview panel
 */
async function showViolationDetails(violationId) {
    if (!state.apiClient) {
        return;
    }
    try {
        const violation = await state.apiClient.getViolation(violationId);
        const panel = vscode.window.createWebviewPanel('sdlc.violationDetails', `Violation: ${violation.violation_type}`, vscode.ViewColumn.One, { enableScripts: false });
        panel.webview.html = generateViolationDetailsHtml(violation);
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}
/**
 * Requests AI fix for a violation
 */
async function fixViolation(violationId) {
    if (!state.apiClient) {
        return;
    }
    try {
        const config = config_1.ConfigManager.getInstance();
        const councilMode = config.aiCouncilEnabled;
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Getting AI recommendation...',
            cancellable: false,
        }, async () => {
            const recommendation = await state.apiClient.getAIRecommendation(violationId, councilMode);
            // Show recommendation in output channel
            const outputChannel = vscode.window.createOutputChannel('SDLC AI Recommendation');
            outputChannel.clear();
            outputChannel.appendLine('='.repeat(60));
            outputChannel.appendLine('SDLC Orchestrator - AI Recommendation');
            outputChannel.appendLine('='.repeat(60));
            outputChannel.appendLine('');
            outputChannel.appendLine(`Violation ID: ${violationId}`);
            outputChannel.appendLine(`Council Mode: ${councilMode ? 'Enabled' : 'Disabled'}`);
            outputChannel.appendLine(`Confidence: ${recommendation.confidence_score}/10`);
            outputChannel.appendLine(`Provider: ${recommendation.providers_used.join(', ')}`);
            outputChannel.appendLine('');
            outputChannel.appendLine('-'.repeat(60));
            outputChannel.appendLine('RECOMMENDATION:');
            outputChannel.appendLine('-'.repeat(60));
            outputChannel.appendLine('');
            outputChannel.appendLine(recommendation.recommendation);
            outputChannel.show();
        });
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
            includeActions: true,
        });
    }
}
/**
 * Shows welcome message for first-time users
 */
async function showWelcomeMessage() {
    const selection = await vscode.window.showInformationMessage('Welcome to SDLC Orchestrator! Monitor gate status, get compliance assistance, and use @gate in chat.', 'Get Started', 'Learn More');
    if (selection === 'Get Started') {
        await vscode.commands.executeCommand('sdlc.login');
    }
    else if (selection === 'Learn More') {
        void vscode.env.openExternal(vscode.Uri.parse('https://docs.sdlc-orchestrator.dev/vscode-extension'));
    }
}
/**
 * Check for empty folder or missing SDLC config and prompt for initialization
 */
async function checkAndPromptForInit(context) {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        return;
    }
    const firstFolder = folders[0];
    if (!firstFolder) {
        return;
    }
    const workspaceRoot = firstFolder.uri.fsPath;
    const structureService = new sdlcStructureService_1.SDLCStructureService();
    // Check if SDLC config exists
    if (structureService.hasSDLCConfig(workspaceRoot)) {
        // Config exists, no prompt needed
        logger_1.Logger.info('SDLC config found, skipping init prompt');
        return;
    }
    // Check if folder is empty or minimal
    const isEmptyOrMinimal = structureService.isEmptyOrMinimalFolder(workspaceRoot);
    // Check if we've already prompted for this workspace
    const hasPrompted = context.workspaceState.get('sdlc.hasPromptedInit');
    if (hasPrompted) {
        return;
    }
    // Show prompt based on folder state
    let message;
    let actions;
    if (isEmptyOrMinimal) {
        message = 'This folder is empty. Would you like to create an SDLC 6.0.6 project structure?';
        actions = ['Create SDLC Project', 'Not Now', "Don't Ask Again"];
    }
    else {
        message = 'This project doesn\'t have an SDLC configuration. Would you like to add SDLC 6.0.6 governance?';
        actions = ['Run Gap Analysis', 'Initialize', 'Not Now', "Don't Ask Again"];
    }
    const selection = await vscode.window.showInformationMessage(message, ...actions);
    if (selection === 'Create SDLC Project' || selection === 'Initialize') {
        await vscode.commands.executeCommand('sdlc.init');
    }
    else if (selection === 'Run Gap Analysis') {
        await vscode.commands.executeCommand('sdlc.gapAnalysis');
    }
    else if (selection === "Don't Ask Again") {
        await context.workspaceState.update('sdlc.hasPromptedInit', true);
    }
}
/**
 * Generates HTML for violation details webview
 */
function generateViolationDetailsHtml(violation) {
    const severityColor = violation.severity === 'critical'
        ? '#ef4444'
        : violation.severity === 'high'
            ? '#f97316'
            : violation.severity === 'medium'
                ? '#eab308'
                : '#22c55e';
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Violation Details</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        .severity-badge {
            background-color: ${severityColor};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .section {
            margin-bottom: 20px;
        }
        .section-title {
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
            margin-bottom: 8px;
        }
        .description {
            background-color: var(--vscode-textBlockQuote-background);
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid var(--vscode-textLink-foreground);
        }
        .meta {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>${violation.violation_type}</h1>
        <span class="severity-badge">${violation.severity}</span>
    </div>

    <div class="section">
        <div class="section-title">Description</div>
        <div class="description">${violation.description}</div>
    </div>

    ${violation.gate_type ? `
    <div class="section">
        <div class="section-title">Gate</div>
        <p>${violation.gate_type}</p>
    </div>
    ` : ''}

    ${violation.remediation ? `
    <div class="section">
        <div class="section-title">Remediation</div>
        <div class="description">${violation.remediation}</div>
    </div>
    ` : ''}

    <div class="meta">
        <p>ID: ${violation.id}</p>
        <p>Created: ${new Date(violation.created_at).toLocaleString()}</p>
    </div>
</body>
</html>`;
}
//# sourceMappingURL=extension.js.map