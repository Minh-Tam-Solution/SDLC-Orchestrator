/**
 * SDLC Orchestrator Projects View
 *
 * TreeDataProvider for displaying and selecting projects in the sidebar.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ApiClient, Project } from '../services/apiClient';
import { CacheService, CacheKeys, CacheTTL } from '../services/cacheService';
import { ProjectDetector } from '../services/projectDetector';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { classifyError, ErrorCode, SDLCError } from '../utils/errors';

/**
 * Local SDLC config file schema (from sdlcctl CLI)
 */
interface LocalSDLCConfig {
    version?: string;
    project?: {
        id?: string;
        name?: string;
        description?: string;
        slug?: string;
        repository?: string;
    };
    tier?: string;
    sdlc?: {
        frameworkVersion?: string;
        tier?: string;
        stages?: Record<string, string>;
    };
    server?: {
        url?: string;
        connected?: boolean;
    };
}

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
    private shouldShowPanel = true; // Sprint 127: Hide panel when auto-detect works

    constructor(
        private apiClient: ApiClient,
        private cacheService?: CacheService,
        private projectDetector?: ProjectDetector
    ) {
        // Register internal command for project selection
        vscode.commands.registerCommand(
            'sdlc.internal.selectProjectItem',
            this.handleProjectSelect.bind(this)
        );

        // Load selected project from config
        const config = ConfigManager.getInstance();
        this.selectedProjectId = config.defaultProjectId || undefined;

        // Sprint 127: Check if panel should be shown
        this.updatePanelVisibility();
    }

    /**
     * Update panel visibility based on auto-detect and user settings (Sprint 127)
     */
    private async updatePanelVisibility(): Promise<void> {
        if (!this.projectDetector) {
            this.shouldShowPanel = true;
            await this.setVisibilityContext(true);
            return;
        }

        // Check user setting (opt-in to show panel)
        const config = vscode.workspace.getConfiguration('sdlc');
        const showPanel = config.get<boolean>('showProjectsPanel', false);
        if (showPanel) {
            this.shouldShowPanel = true;
            await this.setVisibilityContext(true);
            return;
        }

        // Check for monorepo (multiple .sdlc/config.yaml)
        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (!workspace) {
            this.shouldShowPanel = false;
            await this.setVisibilityContext(false);
            return;
        }

        const pattern = new vscode.RelativePattern(workspace, '**/.sdlc/config.yaml');
        try {
            const files = await vscode.workspace.findFiles(pattern, null, 2);
            const shouldShow = files.length > 1; // Show for monorepo
            this.shouldShowPanel = shouldShow;
            await this.setVisibilityContext(shouldShow);
        } catch {
            this.shouldShowPanel = false;
            await this.setVisibilityContext(false);
        }
    }

    /**
     * Set VS Code context key for panel visibility
     */
    private async setVisibilityContext(visible: boolean): Promise<void> {
        await vscode.commands.executeCommand(
            'setContext',
            'sdlc.projectsPanelVisible',
            visible
        );
        Logger.debug(`Projects panel visibility context set to: ${visible}`);
    }

    /**
     * Load local project from .sdlc-config.json in workspace
     */
    private loadLocalProject(): Project | null {
        const folders = vscode.workspace.workspaceFolders;
        if (!folders || folders.length === 0) {
            return null;
        }

        const workspaceRoot = folders[0]?.uri.fsPath;
        if (!workspaceRoot) {
            return null;
        }

        const configPath = path.join(workspaceRoot, '.sdlc-config.json');
        if (!fs.existsSync(configPath)) {
            return null;
        }

        try {
            const content = fs.readFileSync(configPath, 'utf-8');
            const config: LocalSDLCConfig = JSON.parse(content);

            // Extract project info from either schema format
            const projectName = config.project?.name || path.basename(workspaceRoot);
            const projectId = config.project?.id || `local-${projectName.toLowerCase().replace(/[^a-z0-9]/g, '-')}`;
            const tier = config.tier || config.sdlc?.tier || 'STANDARD';

            const repoUrl = config.project?.repository;
            const localProject: Project = {
                id: projectId,
                name: projectName,
                description: config.project?.description || `Local project: ${projectName}`,
                status: 'active',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                owner_id: 'local',
                current_gate: 'G0.1',
            };
            // Add optional properties only if they have values
            if (repoUrl) {
                localProject.github_repo = repoUrl;
            }

            Logger.info(`Loaded local project: ${projectName} (tier: ${tier})`);
            return localProject;
        } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            Logger.warn(`Failed to load local .sdlc-config.json: ${msg}`);
            return null;
        }
    }

    /**
     * Refreshes the projects data
     */
    async refresh(): Promise<void> {
        if (this.isLoading) {
            return;
        }

        // Sprint 127: Update panel visibility before refresh
        await this.updatePanelVisibility();

        this.isLoading = true;
        this.hasError = false;
        this.errorMessage = '';
        this.lastError = undefined;

        try {
            // Local-First approach: Load local project from .sdlc-config.json
            const localProject = this.loadLocalProject();

            // Try to fetch from server (for sync purposes, not required)
            let serverProjects: Project[] = [];
            try {
                if (this.cacheService) {
                    const cacheKey = CacheKeys.PROJECTS;
                    const result = await this.cacheService.getOrFetch<Project[]>(
                        cacheKey,
                        () => this.apiClient.getProjects(),
                        CacheTTL.PROJECTS
                    );
                    serverProjects = result.data;
                } else {
                    serverProjects = await this.apiClient.getProjects();
                }
            } catch (apiError) {
                // API failed - local project still works (Local-First approach)
                const classified = classifyError(apiError);
                if (classified.code === ErrorCode.UNAUTHORIZED) {
                    Logger.info('Not authenticated, using local project');
                } else {
                    Logger.warn(`API error: ${classified.getUserMessage()}`);
                }
            }

            // Merge local project with server projects
            this.projects = [];

            // Add local project first if exists
            if (localProject) {
                // Check if local project already exists in server projects
                const existsOnServer = serverProjects.some(
                    p => p.name === localProject.name || p.id === localProject.id
                );
                if (!existsOnServer) {
                    // Mark as local project
                    localProject.description = `📁 ${localProject.description}`;
                    this.projects.push(localProject);
                }
            }

            // Add server projects
            this.projects.push(...serverProjects);

            // Sort by name
            this.projects.sort((a, b) => a.name.localeCompare(b.name));

            Logger.info(
                `Loaded ${this.projects.length} projects` +
                    (localProject ? ' (includes local)' : '')
            );

            // Update selected project ID from config
            const config = ConfigManager.getInstance();
            this.selectedProjectId = config.defaultProjectId || undefined;

            // Auto-select local project if no project selected
            if (!this.selectedProjectId && localProject) {
                this.selectedProjectId = localProject.id;
                await vscode.workspace
                    .getConfiguration('sdlc')
                    .update('defaultProjectId', localProject.id, vscode.ConfigurationTarget.Workspace);
                Logger.info(`Auto-selected local project: ${localProject.name}`);
            }

        } catch (error) {
            this.lastError = classifyError(error);
            this.hasError = true;
            this.errorMessage = this.lastError.getUserMessage();
            Logger.error(`Failed to refresh projects: ${this.errorMessage}`);

            // Handle 401 Unauthorized - prompt re-login
            if (this.lastError.code === ErrorCode.UNAUTHORIZED) {
                // Still try to load local project
                const localProject = this.loadLocalProject();
                if (localProject) {
                    this.projects = [localProject];
                    this.hasError = false;
                    this.errorMessage = '';
                } else {
                    this.projects = [];
                    void vscode.window.showErrorMessage(
                        'Authentication expired. Please log in again.',
                        'Login'
                    ).then(selection => {
                        if (selection === 'Login') {
                            void vscode.commands.executeCommand('sdlc.login');
                        }
                    });
                }
            } else {
                // Try to get cached data on error
                if (this.cacheService) {
                    const cached = this.cacheService.get<Project[]>(CacheKeys.PROJECTS);
                    if (cached) {
                        this.projects = cached.data;
                        this.hasError = false;
                    } else {
                        this.projects = [];
                    }
                } else {
                    this.projects = [];
                }
            }

            // Defensive: ensure projects is always an array
            if (!Array.isArray(this.projects)) {
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
        // Sprint 127: Hide panel if auto-detect is working
        if (!this.shouldShowPanel) {
            Logger.debug('Projects panel hidden (auto-detect enabled)');
            return [];
        }

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

        // Local-First Mode: No status indicators needed
        // Extension works with local .sdlc-config.json, server sync is automatic
        // No "offline" or "cached" messages - just show projects

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
