/**
 * SDLC Orchestrator Projects View
 *
 * TreeDataProvider for displaying and selecting projects in the sidebar.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
 */

import * as vscode from 'vscode';
import { ApiClient, Project } from '../services/apiClient';
import { CacheService, CacheKeys, CacheTTL } from '../services/cacheService';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { classifyError, ErrorCode, SDLCError } from '../utils/errors';

/**
 * Tree item representing a project
 */
export class ProjectTreeItem extends vscode.TreeItem {
    constructor(
        public readonly project: Project,
        public readonly isSelected: boolean
    ) {
        super(project.name, vscode.TreeItemCollapsibleState.None);

        this.contextValue = 'project';

        // Set description
        this.description = isSelected ? '(selected)' : project.status;

        // Set icon based on status and selection
        if (isSelected) {
            this.iconPath = new vscode.ThemeIcon(
                'check',
                new vscode.ThemeColor('sdlc.gateApproved')
            );
        } else {
            this.iconPath = this.getStatusIcon(project.status);
        }

        // Set tooltip
        this.tooltip = new vscode.MarkdownString();
        this.tooltip.appendMarkdown(`### ${project.name}\n\n`);
        if (project.description) {
            this.tooltip.appendMarkdown(`${project.description}\n\n`);
        }
        this.tooltip.appendMarkdown(`**Status:** ${project.status}\n\n`);
        if (project.compliance_score !== undefined) {
            this.tooltip.appendMarkdown(
                `**Compliance:** ${project.compliance_score}%\n\n`
            );
        }
        if (project.current_gate) {
            this.tooltip.appendMarkdown(`**Current Gate:** ${project.current_gate}`);
        }

        // Set command for clicking
        this.command = {
            command: 'sdlc.internal.selectProjectItem',
            title: 'Select Project',
            arguments: [project.id, project.name],
        };
    }

    /**
     * Gets icon based on project status
     */
    private getStatusIcon(status: string): vscode.ThemeIcon {
        switch (status) {
            case 'active':
                return new vscode.ThemeIcon('folder-active');
            case 'archived':
                return new vscode.ThemeIcon('archive');
            case 'draft':
            default:
                return new vscode.ThemeIcon('folder');
        }
    }
}

/**
 * Tree data provider for projects sidebar
 */
export class ProjectsProvider implements vscode.TreeDataProvider<ProjectTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ProjectTreeItem | undefined | null>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private projects: Project[] = [];
    private selectedProjectId: string | undefined;
    private isLoading = false;
    private hasError = false;
    private errorMessage = '';
    private lastError: SDLCError | undefined;
    private isUsingCachedData = false;

    constructor(
        private apiClient: ApiClient,
        private cacheService?: CacheService
    ) {
        // Register internal command for project selection
        vscode.commands.registerCommand(
            'sdlc.internal.selectProjectItem',
            this.handleProjectSelect.bind(this)
        );

        // Load selected project from config
        const config = ConfigManager.getInstance();
        this.selectedProjectId = config.defaultProjectId || undefined;
    }

    /**
     * Refreshes the projects data
     */
    async refresh(): Promise<void> {
        if (this.isLoading) {
            return;
        }

        this.isLoading = true;
        this.hasError = false;
        this.errorMessage = '';
        this.lastError = undefined;
        this.isUsingCachedData = false;

        try {
            // Use cache service if available for offline support
            if (this.cacheService) {
                const cacheKey = CacheKeys.PROJECTS;
                const result = await this.cacheService.getOrFetch<Project[]>(
                    cacheKey,
                    () => this.apiClient.getProjects(),
                    CacheTTL.PROJECTS
                );

                this.projects = result.data;
                this.isUsingCachedData = result.isCached;

                if (result.isStale) {
                    Logger.info('Using stale cached projects');
                }
            } else {
                this.projects = await this.apiClient.getProjects();
            }

            // Sort by name
            this.projects.sort((a, b) => a.name.localeCompare(b.name));

            Logger.info(
                `Loaded ${this.projects.length} projects` +
                    (this.isUsingCachedData ? ' (from cache)' : '')
            );

            // Update selected project ID from config
            const config = ConfigManager.getInstance();
            this.selectedProjectId = config.defaultProjectId || undefined;
        } catch (error) {
            this.lastError = classifyError(error);
            this.hasError = true;
            this.errorMessage = this.lastError.getUserMessage();
            Logger.error(`Failed to refresh projects: ${this.errorMessage}`);

            // Try to get cached data on error (offline mode)
            if (this.cacheService) {
                const cached = this.cacheService.get<Project[]>(CacheKeys.PROJECTS);
                if (cached) {
                    this.projects = cached.data;
                    this.isUsingCachedData = true;
                    this.hasError = false;
                    Logger.info('Using cached projects due to network error');
                } else {
                    this.projects = [];
                }
            } else {
                this.projects = [];
            }
        } finally {
            this.isLoading = false;
            this._onDidChangeTreeData.fire(undefined);
        }
    }

    /**
     * Clears the view data
     */
    clear(): void {
        this.projects = [];
        this.selectedProjectId = undefined;
        this.hasError = false;
        this.errorMessage = '';
        this._onDidChangeTreeData.fire(undefined);
    }

    /**
     * Gets tree item for element
     */
    getTreeItem(element: ProjectTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Gets children for tree item
     */
    getChildren(_element?: ProjectTreeItem): ProjectTreeItem[] {
        // Projects view is flat - only root level
        return this.getRootItems();
    }

    /**
     * Gets root level items (projects)
     */
    private getRootItems(): ProjectTreeItem[] {
        const items: vscode.TreeItem[] = [];

        // Loading state
        if (this.isLoading) {
            const item = new vscode.TreeItem(
                'Loading projects...',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('loading~spin');
            return [item as ProjectTreeItem];
        }

        // Error state with enhanced error handling
        if (this.hasError) {
            const item = new vscode.TreeItem(
                this.errorMessage,
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon(
                'error',
                new vscode.ThemeColor('errorForeground')
            );

            // Add suggested action to tooltip
            if (this.lastError) {
                const tooltip = new vscode.MarkdownString();
                tooltip.appendMarkdown('### Error\n\n');
                tooltip.appendMarkdown(`${this.errorMessage}\n\n`);
                tooltip.appendMarkdown(`**Suggested Action:** ${this.lastError.getSuggestedAction()}`);
                item.tooltip = tooltip;

                // Set command based on error type
                if (this.lastError.code === ErrorCode.UNAUTHORIZED ||
                    this.lastError.code === ErrorCode.TOKEN_EXPIRED) {
                    item.command = {
                        command: 'sdlc.login',
                        title: 'Login',
                    };
                } else if (this.lastError.isRetryable()) {
                    item.command = {
                        command: 'sdlc.refreshGates',
                        title: 'Retry',
                    };
                }
            }

            return [item as ProjectTreeItem];
        }

        // Offline mode indicator
        if (this.isUsingCachedData) {
            const offlineItem = new vscode.TreeItem(
                'Offline mode (cached data)',
                vscode.TreeItemCollapsibleState.None
            );
            offlineItem.iconPath = new vscode.ThemeIcon(
                'cloud-offline',
                new vscode.ThemeColor('editorWarning.foreground')
            );
            offlineItem.tooltip = 'Data may be outdated. Click refresh when online.';
            offlineItem.command = {
                command: 'sdlc.refreshGates',
                title: 'Refresh',
            };
            items.push(offlineItem);
        }

        // No projects found
        if (this.projects.length === 0) {
            const item = new vscode.TreeItem(
                'No projects found',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('info');
            items.push(item);
            return items as ProjectTreeItem[];
        }

        // Map projects to tree items
        const projectItems = this.projects.map(
            (project) =>
                new ProjectTreeItem(
                    project,
                    project.id === this.selectedProjectId
                )
        );

        return [...items, ...projectItems] as ProjectTreeItem[];
    }

    /**
     * Handles project selection from tree view
     */
    private async handleProjectSelect(
        projectId: string,
        projectName: string
    ): Promise<void> {
        try {
            // Update configuration
            await vscode.workspace
                .getConfiguration('sdlc')
                .update(
                    'defaultProjectId',
                    projectId,
                    vscode.ConfigurationTarget.Workspace
                );

            // Update local state
            this.selectedProjectId = projectId;

            // Refresh tree to update selection indicator
            this._onDidChangeTreeData.fire(undefined);

            // Show confirmation
            void vscode.window.showInformationMessage(
                `Selected project: ${projectName}`
            );

            // Trigger refresh of other views
            await vscode.commands.executeCommand('sdlc.refreshGates');

            Logger.info(`Selected project: ${projectId} (${projectName})`);
        } catch (error) {
            const message =
                error instanceof Error ? error.message : 'Unknown error';
            Logger.error(`Failed to select project: ${message}`);
            void vscode.window.showErrorMessage(
                `Failed to select project: ${message}`
            );
        }
    }

    /**
     * Gets the currently selected project
     */
    getSelectedProject(): Project | undefined {
        return this.projects.find((p) => p.id === this.selectedProjectId);
    }

    /**
     * Gets all loaded projects
     */
    getProjects(): Project[] {
        return [...this.projects];
    }
}
