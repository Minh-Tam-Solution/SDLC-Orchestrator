"use strict";
/**
 * SDLC Orchestrator Projects View
 *
 * TreeDataProvider for displaying and selecting projects in the sidebar.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
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
exports.ProjectsProvider = exports.ProjectTreeItem = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const cacheService_1 = require("../services/cacheService");
const logger_1 = require("../utils/logger");
const config_1 = require("../utils/config");
const errors_1 = require("../utils/errors");
/**
 * Tree item representing a project
 */
class ProjectTreeItem extends vscode.TreeItem {
    project;
    isSelected;
    constructor(project, isSelected) {
        super(project.name, vscode.TreeItemCollapsibleState.None);
        this.project = project;
        this.isSelected = isSelected;
        this.contextValue = 'project';
        // Set description
        this.description = isSelected ? '(selected)' : project.status;
        // Set icon based on status and selection
        if (isSelected) {
            this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('sdlc.gateApproved'));
        }
        else {
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
            this.tooltip.appendMarkdown(`**Compliance:** ${project.compliance_score}%\n\n`);
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
    getStatusIcon(status) {
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
exports.ProjectTreeItem = ProjectTreeItem;
/**
 * Tree data provider for projects sidebar
 */
class ProjectsProvider {
    apiClient;
    cacheService;
    projectDetector;
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    projects = [];
    selectedProjectId;
    isLoading = false;
    hasError = false;
    errorMessage = '';
    lastError;
    shouldShowPanel = true; // Sprint 127: Hide panel when auto-detect works
    constructor(apiClient, cacheService, projectDetector) {
        this.apiClient = apiClient;
        this.cacheService = cacheService;
        this.projectDetector = projectDetector;
        // Register internal command for project selection
        vscode.commands.registerCommand('sdlc.internal.selectProjectItem', this.handleProjectSelect.bind(this));
        // Load selected project from config
        const config = config_1.ConfigManager.getInstance();
        this.selectedProjectId = config.defaultProjectId || undefined;
        // Sprint 127: Check if panel should be shown
        this.updatePanelVisibility();
    }
    /**
     * Update panel visibility based on auto-detect and user settings (Sprint 127)
     */
    async updatePanelVisibility() {
        if (!this.projectDetector) {
            this.shouldShowPanel = true;
            await this.setVisibilityContext(true);
            return;
        }
        // Check user setting (opt-in to show panel)
        const config = vscode.workspace.getConfiguration('sdlc');
        const showPanel = config.get('showProjectsPanel', false);
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
        }
        catch {
            this.shouldShowPanel = false;
            await this.setVisibilityContext(false);
        }
    }
    /**
     * Set VS Code context key for panel visibility
     */
    async setVisibilityContext(visible) {
        await vscode.commands.executeCommand('setContext', 'sdlc.projectsPanelVisible', visible);
        logger_1.Logger.debug(`Projects panel visibility context set to: ${visible}`);
    }
    /**
     * Load local project from .sdlc-config.json in workspace
     */
    loadLocalProject() {
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
            const config = JSON.parse(content);
            // Extract project info from either schema format
            const projectName = config.project?.name || path.basename(workspaceRoot);
            const projectId = config.project?.id || `local-${projectName.toLowerCase().replace(/[^a-z0-9]/g, '-')}`;
            const tier = config.tier || config.sdlc?.tier || 'STANDARD';
            const repoUrl = config.project?.repository;
            const localProject = {
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
            logger_1.Logger.info(`Loaded local project: ${projectName} (tier: ${tier})`);
            return localProject;
        }
        catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            logger_1.Logger.warn(`Failed to load local .sdlc-config.json: ${msg}`);
            return null;
        }
    }
    /**
     * Refreshes the projects data
     */
    async refresh() {
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
            let serverProjects = [];
            try {
                if (this.cacheService) {
                    const cacheKey = cacheService_1.CacheKeys.PROJECTS;
                    const result = await this.cacheService.getOrFetch(cacheKey, () => this.apiClient.getProjects(), cacheService_1.CacheTTL.PROJECTS);
                    serverProjects = result.data;
                }
                else {
                    serverProjects = await this.apiClient.getProjects();
                }
            }
            catch (apiError) {
                // API failed - local project still works (Local-First approach)
                const classified = (0, errors_1.classifyError)(apiError);
                if (classified.code === errors_1.ErrorCode.UNAUTHORIZED) {
                    logger_1.Logger.info('Not authenticated, using local project');
                }
                else {
                    logger_1.Logger.warn(`API error: ${classified.getUserMessage()}`);
                }
            }
            // Merge local project with server projects
            this.projects = [];
            // Add local project first if exists
            if (localProject) {
                // Check if local project already exists in server projects
                const existsOnServer = serverProjects.some(p => p.name === localProject.name || p.id === localProject.id);
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
            logger_1.Logger.info(`Loaded ${this.projects.length} projects` +
                (localProject ? ' (includes local)' : ''));
            // Update selected project ID from config
            const config = config_1.ConfigManager.getInstance();
            this.selectedProjectId = config.defaultProjectId || undefined;
            // Auto-select local project if no project selected
            if (!this.selectedProjectId && localProject) {
                this.selectedProjectId = localProject.id;
                await vscode.workspace
                    .getConfiguration('sdlc')
                    .update('defaultProjectId', localProject.id, vscode.ConfigurationTarget.Workspace);
                logger_1.Logger.info(`Auto-selected local project: ${localProject.name}`);
            }
        }
        catch (error) {
            this.lastError = (0, errors_1.classifyError)(error);
            this.hasError = true;
            this.errorMessage = this.lastError.getUserMessage();
            logger_1.Logger.error(`Failed to refresh projects: ${this.errorMessage}`);
            // Handle 401 Unauthorized - prompt re-login
            if (this.lastError.code === errors_1.ErrorCode.UNAUTHORIZED) {
                // Still try to load local project
                const localProject = this.loadLocalProject();
                if (localProject) {
                    this.projects = [localProject];
                    this.hasError = false;
                    this.errorMessage = '';
                }
                else {
                    this.projects = [];
                    void vscode.window.showErrorMessage('Authentication expired. Please log in again.', 'Login').then(selection => {
                        if (selection === 'Login') {
                            void vscode.commands.executeCommand('sdlc.login');
                        }
                    });
                }
            }
            else {
                // Try to get cached data on error
                if (this.cacheService) {
                    const cached = this.cacheService.get(cacheService_1.CacheKeys.PROJECTS);
                    if (cached) {
                        this.projects = cached.data;
                        this.hasError = false;
                    }
                    else {
                        this.projects = [];
                    }
                }
                else {
                    this.projects = [];
                }
            }
            // Defensive: ensure projects is always an array
            if (!Array.isArray(this.projects)) {
                this.projects = [];
            }
        }
        finally {
            this.isLoading = false;
            this._onDidChangeTreeData.fire(undefined);
        }
    }
    /**
     * Clears the view data
     */
    clear() {
        this.projects = [];
        this.selectedProjectId = undefined;
        this.hasError = false;
        this.errorMessage = '';
        this._onDidChangeTreeData.fire(undefined);
    }
    /**
     * Gets tree item for element
     */
    getTreeItem(element) {
        return element;
    }
    /**
     * Gets children for tree item
     */
    getChildren(_element) {
        // Sprint 127: Hide panel if auto-detect is working
        if (!this.shouldShowPanel) {
            logger_1.Logger.debug('Projects panel hidden (auto-detect enabled)');
            return [];
        }
        // Projects view is flat - only root level
        return this.getRootItems();
    }
    /**
     * Gets root level items (projects)
     */
    getRootItems() {
        const items = [];
        // Loading state
        if (this.isLoading) {
            const item = new vscode.TreeItem('Loading projects...', vscode.TreeItemCollapsibleState.None);
            item.iconPath = new vscode.ThemeIcon('loading~spin');
            return [item];
        }
        // Error state with enhanced error handling
        if (this.hasError) {
            const item = new vscode.TreeItem(this.errorMessage, vscode.TreeItemCollapsibleState.None);
            item.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
            // Add suggested action to tooltip
            if (this.lastError) {
                const tooltip = new vscode.MarkdownString();
                tooltip.appendMarkdown('### Error\n\n');
                tooltip.appendMarkdown(`${this.errorMessage}\n\n`);
                tooltip.appendMarkdown(`**Suggested Action:** ${this.lastError.getSuggestedAction()}`);
                item.tooltip = tooltip;
                // Set command based on error type
                if (this.lastError.code === errors_1.ErrorCode.UNAUTHORIZED ||
                    this.lastError.code === errors_1.ErrorCode.TOKEN_EXPIRED) {
                    item.command = {
                        command: 'sdlc.login',
                        title: 'Login',
                    };
                }
                else if (this.lastError.isRetryable()) {
                    item.command = {
                        command: 'sdlc.refreshGates',
                        title: 'Retry',
                    };
                }
            }
            return [item];
        }
        // Local-First Mode: No status indicators needed
        // Extension works with local .sdlc-config.json, server sync is automatic
        // No "offline" or "cached" messages - just show projects
        // No projects found
        if (this.projects.length === 0) {
            const item = new vscode.TreeItem('No projects found', vscode.TreeItemCollapsibleState.None);
            item.iconPath = new vscode.ThemeIcon('info');
            items.push(item);
            return items;
        }
        // Map projects to tree items
        const projectItems = this.projects.map((project) => new ProjectTreeItem(project, project.id === this.selectedProjectId));
        return [...items, ...projectItems];
    }
    /**
     * Handles project selection from tree view
     */
    async handleProjectSelect(projectId, projectName) {
        try {
            // Update configuration
            await vscode.workspace
                .getConfiguration('sdlc')
                .update('defaultProjectId', projectId, vscode.ConfigurationTarget.Workspace);
            // Update local state
            this.selectedProjectId = projectId;
            // Refresh tree to update selection indicator
            this._onDidChangeTreeData.fire(undefined);
            // Show confirmation
            void vscode.window.showInformationMessage(`Selected project: ${projectName}`);
            // Trigger refresh of other views
            await vscode.commands.executeCommand('sdlc.refreshGates');
            logger_1.Logger.info(`Selected project: ${projectId} (${projectName})`);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            logger_1.Logger.error(`Failed to select project: ${message}`);
            void vscode.window.showErrorMessage(`Failed to select project: ${message}`);
        }
    }
    /**
     * Gets the currently selected project
     */
    getSelectedProject() {
        return this.projects.find((p) => p.id === this.selectedProjectId);
    }
    /**
     * Gets all loaded projects
     */
    getProjects() {
        return [...this.projects];
    }
}
exports.ProjectsProvider = ProjectsProvider;
//# sourceMappingURL=projectsView.js.map