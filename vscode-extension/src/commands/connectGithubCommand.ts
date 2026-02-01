/**
 * GitHub Repository Connection Command Handler
 *
 * Implements the "SDLC: Connect GitHub Repository" command for linking
 * GitHub repositories to SDLC Orchestrator projects.
 *
 * Features:
 * - List user's GitHub App installations
 * - List accessible repositories
 * - Link repository to current project
 * - Trigger clone and gap analysis
 *
 * Sprint 129 Day 3 - Extension Integration
 * Reference: ADR-044-GitHub-Integration-Strategy.md
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
import { Logger } from '../utils/logger';
import {
    handleError,
    ErrorCode,
    GitHubError,
    parseGitHubApiError,
} from '../utils/errors';

/**
 * GitHub Installation from API
 */
export interface GitHubInstallation {
    id: string;
    installation_id: number;
    account_type: string;
    account_login: string;
    account_avatar_url?: string;
    status: string;
    installed_at: string;
}

/**
 * GitHub Repository from API
 */
export interface GitHubRepository {
    id: number;
    name: string;
    full_name: string;
    owner: string;
    private: boolean;
    html_url: string;
    default_branch: string;
    description?: string;
}

/**
 * Linked repository info
 */
export interface LinkedRepository {
    id: string;
    github_repo_id: number;
    owner: string;
    name: string;
    full_name: string;
    clone_status: string;
    local_path?: string;
    html_url?: string;
}

/**
 * GitHub Connect Command Handler
 */
export class ConnectGithubCommandHandler {
    private readonly apiClient: ApiClient;

    constructor(apiClient: ApiClient) {
        this.apiClient = apiClient;
    }

    /**
     * Execute the connect GitHub repository command
     */
    async execute(): Promise<boolean> {
        Logger.info('Executing Connect GitHub Repository command');

        try {
            // Get current project ID
            const projectId = this.apiClient.getCurrentProjectId();
            if (!projectId) {
                const action = await vscode.window.showWarningMessage(
                    'No project selected. Please select a project first.',
                    'Select Project'
                );
                if (action === 'Select Project') {
                    await vscode.commands.executeCommand('sdlc.selectProject');
                }
                return false;
            }

            // Check if project already has a linked repo
            const existingRepo = await this.getLinkedRepository(projectId);
            if (existingRepo) {
                const action = await vscode.window.showWarningMessage(
                    `This project is already linked to ${existingRepo.full_name}`,
                    'View Repository',
                    'Unlink',
                    'Cancel'
                );

                if (action === 'View Repository' && existingRepo.html_url) {
                    await vscode.env.openExternal(vscode.Uri.parse(existingRepo.html_url));
                    return true;
                } else if (action === 'Unlink') {
                    return await this.unlinkRepository(projectId);
                }
                return false;
            }

            // Get installations
            const installations = await this.getInstallations();
            if (installations.length === 0) {
                const action = await vscode.window.showInformationMessage(
                    'No GitHub App installations found. Please install the SDLC Orchestrator GitHub App.',
                    'Install GitHub App',
                    'Cancel'
                );
                if (action === 'Install GitHub App') {
                    await this.openGitHubAppInstallation();
                }
                return false;
            }

            // Select installation
            const selectedInstallation = await this.selectInstallation(installations);
            if (!selectedInstallation) {
                return false;
            }

            // Get repositories for installation
            const repositories = await this.getRepositoriesForInstallation(selectedInstallation.id);
            if (repositories.length === 0) {
                void vscode.window.showInformationMessage(
                    'No repositories found for this installation. The GitHub App may need more permissions.'
                );
                return false;
            }

            // Select repository
            const selectedRepo = await this.selectRepository(repositories);
            if (!selectedRepo) {
                return false;
            }

            // Link repository to project
            return await this.linkRepository(projectId, selectedInstallation.id, selectedRepo);

        } catch (error) {
            // Parse GitHub-specific errors for better user feedback
            const sdlcError = parseGitHubApiError(error);

            // Add context-specific custom actions based on error type
            const customActions = [];

            if (sdlcError.code === ErrorCode.GITHUB_APP_NOT_INSTALLED) {
                customActions.push({
                    title: 'Install GitHub App',
                    command: 'vscode.open',
                    args: [vscode.Uri.parse('https://github.com/apps/sdlc-orchestrator/installations/new')],
                });
            }

            if (sdlcError.code === ErrorCode.GITHUB_REPO_ACCESS_DENIED) {
                customActions.push({
                    title: 'View Repository',
                    command: 'vscode.open',
                    args: [vscode.Uri.parse('https://github.com/settings/installations')],
                });
            }

            const errorOptions: Parameters<typeof handleError>[1] = {
                showNotification: true,
                notificationType: 'error',
                includeActions: true,
            };
            if (customActions.length > 0) {
                errorOptions.customActions = customActions;
            }
            await handleError(sdlcError, errorOptions);
            return false;
        }
    }

    /**
     * Get user's GitHub installations
     */
    private async getInstallations(): Promise<GitHubInstallation[]> {
        return await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Loading GitHub installations...',
                cancellable: false,
            },
            async () => {
                const response = await this.apiClient.get<{ installations: GitHubInstallation[] }>(
                    '/github/installations'
                );
                return response.installations || [];
            }
        );
    }

    /**
     * Get repositories for an installation
     */
    private async getRepositoriesForInstallation(installationId: string): Promise<GitHubRepository[]> {
        return await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Loading repositories...',
                cancellable: false,
            },
            async () => {
                const response = await this.apiClient.get<{
                    total_count: number;
                    repositories: GitHubRepository[];
                }>(`/github/installations/${installationId}/repositories`);
                return response.repositories || [];
            }
        );
    }

    /**
     * Get linked repository for a project
     */
    private async getLinkedRepository(projectId: string): Promise<LinkedRepository | null> {
        try {
            return await this.apiClient.get<LinkedRepository>(
                `/github/projects/${projectId}/repository`
            );
        } catch (error: any) {
            // 404 means no repo linked
            if (error?.statusCode === 404) {
                return null;
            }
            throw error;
        }
    }

    /**
     * Show installation selection quick pick
     */
    private async selectInstallation(
        installations: GitHubInstallation[]
    ): Promise<GitHubInstallation | undefined> {
        const items = installations.map((inst) => ({
            label: `$(${inst.account_type === 'Organization' ? 'organization' : 'person'}) ${inst.account_login}`,
            description: inst.account_type,
            detail: `Installation ID: ${inst.installation_id} | Status: ${inst.status}`,
            installation: inst,
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select GitHub account or organization',
            title: 'Connect GitHub Repository',
        });

        return selected?.installation;
    }

    /**
     * Show repository selection quick pick
     */
    private async selectRepository(
        repositories: GitHubRepository[]
    ): Promise<GitHubRepository | undefined> {
        const items = repositories.map((repo) => ({
            label: `$(repo) ${repo.name}`,
            description: repo.private ? '$(lock) Private' : '$(globe) Public',
            detail: repo.description || `${repo.full_name} (${repo.default_branch})`,
            repository: repo,
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select repository to connect',
            title: 'Connect GitHub Repository',
            matchOnDescription: true,
            matchOnDetail: true,
        });

        return selected?.repository;
    }

    /**
     * Link repository to project
     */
    private async linkRepository(
        projectId: string,
        installationId: string,
        repo: GitHubRepository
    ): Promise<boolean> {
        return await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `Linking ${repo.full_name}...`,
                cancellable: false,
            },
            async (progress) => {
                // Link repository
                progress.report({ message: 'Connecting repository...' });
                await this.apiClient.post(`/github/projects/${projectId}/link`, {
                    installation_id: installationId,
                    owner: repo.owner,
                    repo: repo.name,
                });

                // Trigger clone
                progress.report({ message: 'Starting repository clone...' });
                try {
                    await this.apiClient.post(`/github/projects/${projectId}/clone`, {
                        shallow: true,
                    });

                    void vscode.window.showInformationMessage(
                        `Successfully connected ${repo.full_name}. Cloning in background...`
                    );
                } catch (cloneError) {
                    // Clone failure is non-fatal
                    Logger.warn(`Clone failed for ${repo.full_name}: ${cloneError}`);
                    void vscode.window.showWarningMessage(
                        `Connected ${repo.full_name} but clone failed. You can retry later.`
                    );
                }

                return true;
            }
        );
    }

    /**
     * Unlink repository from project
     */
    private async unlinkRepository(projectId: string): Promise<boolean> {
        const confirm = await vscode.window.showWarningMessage(
            'Are you sure you want to unlink this repository?',
            { modal: true },
            'Unlink'
        );

        if (confirm !== 'Unlink') {
            return false;
        }

        return await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Unlinking repository...',
                cancellable: false,
            },
            async () => {
                await this.apiClient.delete(`/github/projects/${projectId}/unlink`);
                void vscode.window.showInformationMessage('Repository unlinked successfully');
                return true;
            }
        );
    }

    /**
     * Open GitHub App installation page
     */
    private async openGitHubAppInstallation(): Promise<void> {
        // GitHub App installation URL
        const installUrl = 'https://github.com/apps/sdlc-orchestrator/installations/new';
        await vscode.env.openExternal(vscode.Uri.parse(installUrl));
    }
}

/**
 * Status bar item for GitHub connection status
 */
export class GitHubStatusBarItem {
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            99 // Priority (lower = more right)
        );
        this.statusBarItem.command = 'sdlc.connectGithub';
    }

    /**
     * Update status bar with repository info
     */
    update(repo: LinkedRepository | null): void {
        if (repo) {
            this.statusBarItem.text = `$(github) ${repo.full_name}`;
            this.statusBarItem.tooltip = `GitHub: ${repo.full_name}\nStatus: ${repo.clone_status}`;
            this.statusBarItem.backgroundColor = undefined;
        } else {
            this.statusBarItem.text = '$(github) Not Connected';
            this.statusBarItem.tooltip = 'Click to connect GitHub repository';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
        this.statusBarItem.show();
    }

    /**
     * Hide status bar item
     */
    hide(): void {
        this.statusBarItem.hide();
    }

    /**
     * Dispose status bar item
     */
    dispose(): void {
        this.statusBarItem.dispose();
    }
}

/**
 * Register GitHub commands
 */
export function registerGithubCommands(
    context: vscode.ExtensionContext,
    apiClient: ApiClient
): void {
    const handler = new ConnectGithubCommandHandler(apiClient);

    // Register connect command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.connectGithub', async () => {
            await handler.execute();
        })
    );

    // Register disconnect command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.disconnectGithub', async () => {
            const projectId = apiClient.getCurrentProjectId();
            if (projectId) {
                await handler.execute(); // Will show unlink option if connected
            } else {
                void vscode.window.showWarningMessage('No project selected');
            }
        })
    );

    // Register sync command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.syncGithub', async () => {
            const projectId = apiClient.getCurrentProjectId();
            if (!projectId) {
                void vscode.window.showWarningMessage('No project selected');
                return;
            }

            try {
                await vscode.window.withProgress(
                    {
                        location: vscode.ProgressLocation.Notification,
                        title: 'Syncing with GitHub...',
                        cancellable: false,
                    },
                    async () => {
                        await apiClient.post(`/github/projects/${projectId}/clone`, {
                            shallow: true,
                        });
                        void vscode.window.showInformationMessage('GitHub sync started');
                    }
                );
            } catch (error) {
                const sdlcError = parseGitHubApiError(error);

                // Provide helpful message for rate limit errors
                if (sdlcError instanceof GitHubError && sdlcError.code === ErrorCode.GITHUB_RATE_LIMIT) {
                    const retryMsg = sdlcError.getRetryMessage();
                    void vscode.window.showWarningMessage(
                        `GitHub rate limit exceeded. ${retryMsg}`
                    );
                    return;
                }

                await handleError(sdlcError, {
                    showNotification: true,
                    notificationType: 'error',
                    includeActions: true,
                });
            }
        })
    );

    // Register scan command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.scanGithubRepo', async () => {
            const projectId = apiClient.getCurrentProjectId();
            if (!projectId) {
                void vscode.window.showWarningMessage('No project selected');
                return;
            }

            try {
                const result = await vscode.window.withProgress(
                    {
                        location: vscode.ProgressLocation.Notification,
                        title: 'Scanning repository...',
                        cancellable: false,
                    },
                    async () => {
                        return await apiClient.get<{
                            folders: string[];
                            files: string[];
                            total_folders: number;
                            total_files: number;
                            sdlc_config_found: boolean;
                            docs_folder_exists: boolean;
                        }>(`/github/projects/${projectId}/scan`);
                    }
                );

                // Show result
                const outputChannel = vscode.window.createOutputChannel('SDLC GitHub Scan');
                outputChannel.clear();
                outputChannel.appendLine('='.repeat(60));
                outputChannel.appendLine('SDLC Orchestrator - Repository Scan Results');
                outputChannel.appendLine('='.repeat(60));
                outputChannel.appendLine('');
                outputChannel.appendLine(`Total Folders: ${result.total_folders}`);
                outputChannel.appendLine(`Total Files: ${result.total_files}`);
                outputChannel.appendLine(`SDLC Config Found: ${result.sdlc_config_found ? 'Yes' : 'No'}`);
                outputChannel.appendLine(`Docs Folder Exists: ${result.docs_folder_exists ? 'Yes' : 'No'}`);
                outputChannel.appendLine('');
                outputChannel.appendLine('-'.repeat(60));
                outputChannel.appendLine('FOLDERS:');
                outputChannel.appendLine('-'.repeat(60));
                result.folders.forEach(folder => outputChannel.appendLine(`  ${folder}`));
                outputChannel.show();

            } catch (error) {
                const sdlcError = parseGitHubApiError(error);

                // Provide specific guidance based on error type
                const scanErrorOptions: Parameters<typeof handleError>[1] = {
                    showNotification: true,
                    notificationType: 'error',
                    includeActions: true,
                };

                if (sdlcError.code === ErrorCode.GITHUB_CLONE_FAILED) {
                    scanErrorOptions.customActions = [{
                        title: 'Retry Sync',
                        command: 'sdlc.syncGithub',
                    }];
                }

                await handleError(sdlcError, scanErrorOptions);
            }
        })
    );

    Logger.info('GitHub commands registered');
}
