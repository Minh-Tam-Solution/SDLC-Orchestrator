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
export declare class ConnectGithubCommandHandler {
    private readonly apiClient;
    constructor(apiClient: ApiClient);
    /**
     * Execute the connect GitHub repository command
     */
    execute(): Promise<boolean>;
    /**
     * Get user's GitHub installations
     */
    private getInstallations;
    /**
     * Get repositories for an installation
     */
    private getRepositoriesForInstallation;
    /**
     * Get linked repository for a project
     */
    private getLinkedRepository;
    /**
     * Show installation selection quick pick
     */
    private selectInstallation;
    /**
     * Show repository selection quick pick
     */
    private selectRepository;
    /**
     * Link repository to project
     */
    private linkRepository;
    /**
     * Unlink repository from project
     */
    private unlinkRepository;
    /**
     * Open GitHub App installation page
     */
    private openGitHubAppInstallation;
}
/**
 * Status bar item for GitHub connection status
 */
export declare class GitHubStatusBarItem {
    private statusBarItem;
    constructor();
    /**
     * Update status bar with repository info
     */
    update(repo: LinkedRepository | null): void;
    /**
     * Hide status bar item
     */
    hide(): void;
    /**
     * Dispose status bar item
     */
    dispose(): void;
}
/**
 * Register GitHub commands
 */
export declare function registerGithubCommands(context: vscode.ExtensionContext, apiClient: ApiClient): void;
//# sourceMappingURL=connectGithubCommand.d.ts.map