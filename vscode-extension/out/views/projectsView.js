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
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    projects = [];
    selectedProjectId;
    isLoading = false;
    hasError = false;
    errorMessage = '';
    lastError;
    isUsingCachedData = false;
    constructor(apiClient, cacheService) {
        this.apiClient = apiClient;
        this.cacheService = cacheService;
        // Register internal command for project selection
        vscode.commands.registerCommand('sdlc.internal.selectProjectItem', this.handleProjectSelect.bind(this));
        // Load selected project from config
        const config = config_1.ConfigManager.getInstance();
        this.selectedProjectId = config.defaultProjectId || undefined;
    }
    /**
     * Refreshes the projects data
     */
    async refresh() {
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
                const cacheKey = cacheService_1.CacheKeys.PROJECTS;
                const result = await this.cacheService.getOrFetch(cacheKey, () => this.apiClient.getProjects(), cacheService_1.CacheTTL.PROJECTS);
                this.projects = result.data;
                this.isUsingCachedData = result.isCached;
                if (result.isStale) {
                    logger_1.Logger.info('Using stale cached projects');
                }
            }
            else {
                this.projects = await this.apiClient.getProjects();
            }
            // Sort by name
            this.projects.sort((a, b) => a.name.localeCompare(b.name));
            logger_1.Logger.info(`Loaded ${this.projects.length} projects` +
                (this.isUsingCachedData ? ' (from cache)' : ''));
            // Update selected project ID from config
            const config = config_1.ConfigManager.getInstance();
            this.selectedProjectId = config.defaultProjectId || undefined;
        }
        catch (error) {
            this.lastError = (0, errors_1.classifyError)(error);
            this.hasError = true;
            this.errorMessage = this.lastError.getUserMessage();
            logger_1.Logger.error(`Failed to refresh projects: ${this.errorMessage}`);
            // Try to get cached data on error (offline mode)
            if (this.cacheService) {
                const cached = this.cacheService.get(cacheService_1.CacheKeys.PROJECTS);
                if (cached) {
                    this.projects = cached.data;
                    this.isUsingCachedData = true;
                    this.hasError = false;
                    logger_1.Logger.info('Using cached projects due to network error');
                }
                else {
                    this.projects = [];
                }
            }
            else {
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
        // Offline mode indicator
        if (this.isUsingCachedData) {
            const offlineItem = new vscode.TreeItem('Offline mode (cached data)', vscode.TreeItemCollapsibleState.None);
            offlineItem.iconPath = new vscode.ThemeIcon('cloud-offline', new vscode.ThemeColor('editorWarning.foreground'));
            offlineItem.tooltip = 'Data may be outdated. Click refresh when online.';
            offlineItem.command = {
                command: 'sdlc.refreshGates',
                title: 'Refresh',
            };
            items.push(offlineItem);
        }
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