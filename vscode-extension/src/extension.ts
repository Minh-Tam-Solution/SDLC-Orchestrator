/**
 * SDLC Orchestrator VS Code Extension
 *
 * Main entry point for the VS Code extension providing:
 * - Gate status sidebar (G0-G5 progress monitoring)
 * - Inline AI chat (Copilot-style @gate commands)
 * - Compliance violation tracking
 * - Integration with SDLC Orchestrator backend
 *
 * Sprint 27 Day 1 - Extension Foundation
 * @version 0.1.0
 */

import * as vscode from 'vscode';
import { ApiClient } from './services/apiClient';
import { AuthService } from './services/authService';
import { CacheService } from './services/cacheService';
import { GateStatusProvider } from './views/gateStatusView';
import { ViolationsProvider } from './views/violationsView';
import { ProjectsProvider } from './views/projectsView';
import { ComplianceChatParticipant } from './views/complianceChat';
import { Logger } from './utils/logger';
import { ConfigManager } from './utils/config';
import { handleError } from './utils/errors';

/**
 * Extension state management
 */
interface ExtensionState {
    apiClient: ApiClient | undefined;
    authService: AuthService | undefined;
    cacheService: CacheService | undefined;
    gateStatusProvider: GateStatusProvider | undefined;
    violationsProvider: ViolationsProvider | undefined;
    projectsProvider: ProjectsProvider | undefined;
    chatParticipant: ComplianceChatParticipant | undefined;
    refreshInterval: ReturnType<typeof setInterval> | undefined;
}

const state: ExtensionState = {
    apiClient: undefined,
    authService: undefined,
    cacheService: undefined,
    gateStatusProvider: undefined,
    violationsProvider: undefined,
    projectsProvider: undefined,
    chatParticipant: undefined,
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
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    Logger.info('SDLC Orchestrator extension activating...');

    try {
        // Initialize configuration manager
        const config = ConfigManager.getInstance();

        // Initialize services
        state.authService = new AuthService(context);
        state.apiClient = new ApiClient(context, state.authService);
        state.cacheService = new CacheService(context);

        // Check authentication status
        const isAuthenticated = await state.authService.isAuthenticated();
        await vscode.commands.executeCommand(
            'setContext',
            'sdlc.isAuthenticated',
            isAuthenticated
        );

        // Initialize view providers with cache support
        state.gateStatusProvider = new GateStatusProvider(
            state.apiClient,
            state.cacheService
        );
        state.violationsProvider = new ViolationsProvider(
            state.apiClient,
            state.cacheService
        );
        state.projectsProvider = new ProjectsProvider(
            state.apiClient,
            state.cacheService
        );

        // Register tree data providers
        context.subscriptions.push(
            vscode.window.registerTreeDataProvider(
                'sdlc-gate-status',
                state.gateStatusProvider
            ),
            vscode.window.registerTreeDataProvider(
                'sdlc-violations',
                state.violationsProvider
            ),
            vscode.window.registerTreeDataProvider(
                'sdlc-projects',
                state.projectsProvider
            )
        );

        // Register chat participant for Copilot-style @gate commands
        state.chatParticipant = new ComplianceChatParticipant(state.apiClient);
        const chatParticipantDisposable = vscode.chat.createChatParticipant(
            'sdlc-orchestrator.gate',
            state.chatParticipant.handleChatRequest.bind(state.chatParticipant)
        );
        chatParticipantDisposable.iconPath = vscode.Uri.joinPath(
            context.extensionUri,
            'media',
            'sdlc-icon.svg'
        );
        context.subscriptions.push(chatParticipantDisposable);

        // Register commands
        registerCommands(context);

        // Setup auto-refresh
        setupAutoRefresh(config.autoRefreshInterval);

        // Listen for configuration changes
        context.subscriptions.push(
            vscode.workspace.onDidChangeConfiguration((e) => {
                if (e.affectsConfiguration('sdlc')) {
                    handleConfigurationChange();
                }
            })
        );

        // Show welcome message on first activation
        const hasShownWelcome = context.globalState.get<boolean>('sdlc.hasShownWelcome');
        if (!hasShownWelcome) {
            await showWelcomeMessage();
            await context.globalState.update('sdlc.hasShownWelcome', true);
        }

        // Initial data load if authenticated
        if (isAuthenticated) {
            await refreshAllViews();
        }

        Logger.info('SDLC Orchestrator extension activated successfully');
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        Logger.error(`Extension activation failed: ${errorMessage}`);
        void vscode.window.showErrorMessage(
            `SDLC Orchestrator activation failed: ${errorMessage}`
        );
    }
}

/**
 * Deactivates the extension and cleans up resources
 */
export function deactivate(): void {
    Logger.info('SDLC Orchestrator extension deactivating...');

    // Clear refresh interval
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
        state.refreshInterval = undefined;
    }

    // Cleanup services
    state.apiClient = undefined;
    state.authService = undefined;
    state.cacheService = undefined;
    state.gateStatusProvider = undefined;
    state.violationsProvider = undefined;
    state.projectsProvider = undefined;
    state.chatParticipant = undefined;

    Logger.info('SDLC Orchestrator extension deactivated');
}

/**
 * Registers all extension commands
 */
function registerCommands(context: vscode.ExtensionContext): void {
    // Refresh gates command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.refreshGates', async () => {
            await refreshAllViews();
            void vscode.window.showInformationMessage('Gate status refreshed');
        })
    );

    // Open gate in browser command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.openGate', (gateId: string) => {
            const config = ConfigManager.getInstance();
            const url = `${config.apiUrl.replace('/api', '')}/gates/${gateId}`;
            void vscode.env.openExternal(vscode.Uri.parse(url));
        })
    );

    // Select project command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.selectProject', async () => {
            await selectProject();
        })
    );

    // Login command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.login', async () => {
            await handleLogin();
        })
    );

    // Logout command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.logout', async () => {
            await handleLogout();
        })
    );

    // Show violation details command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'sdlc.showViolationDetails',
            (violationId: string) => {
                void showViolationDetails(violationId);
            }
        )
    );

    // Fix violation command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'sdlc.fixViolation',
            async (violationId: string) => {
                await fixViolation(violationId);
            }
        )
    );
}

/**
 * Sets up automatic refresh interval for gate status
 */
function setupAutoRefresh(intervalSeconds: number): void {
    // Clear existing interval
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
    }

    // Setup new interval (convert seconds to milliseconds)
    const intervalMs = intervalSeconds * 1000;
    state.refreshInterval = setInterval(() => {
        void refreshAllViews();
    }, intervalMs);

    Logger.info(`Auto-refresh set to ${intervalSeconds} seconds`);
}

/**
 * Handles configuration changes
 */
function handleConfigurationChange(): void {
    const config = ConfigManager.getInstance();

    // Update auto-refresh interval
    setupAutoRefresh(config.autoRefreshInterval);

    // Update API client base URL
    if (state.apiClient) {
        state.apiClient.updateBaseUrl(config.apiUrl);
    }

    Logger.info('Configuration updated');
}

/**
 * Refreshes all view providers
 */
async function refreshAllViews(): Promise<void> {
    try {
        const promises: Promise<void>[] = [];

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
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        Logger.error(`Failed to refresh views: ${errorMessage}`);
    }
}

/**
 * Handles user login flow
 */
async function handleLogin(): Promise<void> {
    if (!state.authService) {
        void vscode.window.showErrorMessage('Auth service not initialized');
        return;
    }

    try {
        // Show login options
        const loginMethod = await vscode.window.showQuickPick(
            [
                { label: '$(key) API Token', description: 'Login with API token', value: 'token' },
                { label: '$(github) GitHub OAuth', description: 'Login with GitHub', value: 'github' },
            ],
            { placeHolder: 'Select login method' }
        );

        if (!loginMethod) {
            return;
        }

        if (loginMethod.value === 'token') {
            const token = await vscode.window.showInputBox({
                prompt: 'Enter your SDLC Orchestrator API token',
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
        } else if (loginMethod.value === 'github') {
            // GitHub OAuth device flow
            await state.authService.loginWithGitHub();
            await vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', true);
            await refreshAllViews();
            void vscode.window.showInformationMessage('Successfully logged in via GitHub');
        }
    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
            includeActions: true,
        });
    }
}

/**
 * Handles user logout
 */
async function handleLogout(): Promise<void> {
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
    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Shows project selection quick pick
 */
async function selectProject(): Promise<void> {
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
    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
            includeActions: true,
        });
    }
}

/**
 * Shows violation details in a webview panel
 */
async function showViolationDetails(violationId: string): Promise<void> {
    if (!state.apiClient) {
        return;
    }

    try {
        const violation = await state.apiClient.getViolation(violationId);

        const panel = vscode.window.createWebviewPanel(
            'sdlc.violationDetails',
            `Violation: ${violation.violation_type}`,
            vscode.ViewColumn.One,
            { enableScripts: false }
        );

        panel.webview.html = generateViolationDetailsHtml(violation);
    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Requests AI fix for a violation
 */
async function fixViolation(violationId: string): Promise<void> {
    if (!state.apiClient) {
        return;
    }

    try {
        const config = ConfigManager.getInstance();
        const councilMode = config.aiCouncilEnabled;

        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Getting AI recommendation...',
                cancellable: false,
            },
            async () => {
                const recommendation = await state.apiClient!.getAIRecommendation(
                    violationId,
                    councilMode
                );

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
            }
        );
    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
            includeActions: true,
        });
    }
}

/**
 * Shows welcome message for first-time users
 */
async function showWelcomeMessage(): Promise<void> {
    const selection = await vscode.window.showInformationMessage(
        'Welcome to SDLC Orchestrator! Monitor gate status, get compliance assistance, and use @gate in chat.',
        'Get Started',
        'Learn More'
    );

    if (selection === 'Get Started') {
        await vscode.commands.executeCommand('sdlc.login');
    } else if (selection === 'Learn More') {
        void vscode.env.openExternal(
            vscode.Uri.parse('https://docs.sdlc-orchestrator.dev/vscode-extension')
        );
    }
}

/**
 * Generates HTML for violation details webview
 */
function generateViolationDetailsHtml(violation: {
    id: string;
    violation_type: string;
    severity: string;
    description: string;
    created_at: string;
    gate_type?: string;
    remediation?: string;
}): string {
    const severityColor =
        violation.severity === 'critical'
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
