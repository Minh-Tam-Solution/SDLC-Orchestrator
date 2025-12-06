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
import { CacheService } from '../services/cacheService';
/**
 * Tree item representing a project
 */
export declare class ProjectTreeItem extends vscode.TreeItem {
    readonly project: Project;
    readonly isSelected: boolean;
    constructor(project: Project, isSelected: boolean);
    /**
     * Gets icon based on project status
     */
    private getStatusIcon;
}
/**
 * Tree data provider for projects sidebar
 */
export declare class ProjectsProvider implements vscode.TreeDataProvider<ProjectTreeItem> {
    private apiClient;
    private cacheService?;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<ProjectTreeItem | null | undefined>;
    private projects;
    private selectedProjectId;
    private isLoading;
    private hasError;
    private errorMessage;
    private lastError;
    private isUsingCachedData;
    constructor(apiClient: ApiClient, cacheService?: CacheService | undefined);
    /**
     * Refreshes the projects data
     */
    refresh(): Promise<void>;
    /**
     * Clears the view data
     */
    clear(): void;
    /**
     * Gets tree item for element
     */
    getTreeItem(element: ProjectTreeItem): vscode.TreeItem;
    /**
     * Gets children for tree item
     */
    getChildren(_element?: ProjectTreeItem): ProjectTreeItem[];
    /**
     * Gets root level items (projects)
     */
    private getRootItems;
    /**
     * Handles project selection from tree view
     */
    private handleProjectSelect;
    /**
     * Gets the currently selected project
     */
    getSelectedProject(): Project | undefined;
    /**
     * Gets all loaded projects
     */
    getProjects(): Project[];
}
//# sourceMappingURL=projectsView.d.ts.map