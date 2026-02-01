/**
 * SDLC Context Panel Provider
 *
 * Displays dynamic SDLC context overlay in VS Code sidebar.
 * Shows current stage, gate status, sprint info, and constraints.
 *
 * Sprint 81 - Context Panel Implementation
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
import { CacheService } from '../services/cacheService';
import { ProjectDetector } from '../services/projectDetector';
/**
 * Constraint from SDLC context overlay
 */
export interface SDLCConstraint {
    type: string;
    severity: 'info' | 'warning' | 'error';
    message: string;
    affected_files?: string[];
}
/**
 * Sprint information from context overlay
 */
export interface SprintInfo {
    number: number;
    goal: string;
    days_remaining: number;
    start_date?: string;
    end_date?: string;
}
/**
 * SDLC Context Overlay response
 */
export interface SDLCContextOverlay {
    project_id: string;
    stage_name: string;
    gate_status: string;
    strict_mode: boolean;
    sprint?: SprintInfo;
    constraints: SDLCConstraint[];
    generated_at: string;
    formatted?: {
        pr_comment?: string;
        cli?: string;
    };
}
/**
 * Context Panel tree item types
 */
type ContextItemType = 'header' | 'stage' | 'gate' | 'sprint' | 'constraint' | 'warning' | 'error' | 'info';
/**
 * Tree item for Context Panel
 */
export declare class ContextTreeItem extends vscode.TreeItem {
    readonly itemType: ContextItemType;
    readonly children: ContextTreeItem[];
    constructor(label: string, collapsibleState: vscode.TreeItemCollapsibleState, itemType: ContextItemType, itemDescription?: string, children?: ContextTreeItem[], itemTooltip?: string, itemCommand?: vscode.Command);
    private getIcon;
}
/**
 * Context Panel Provider - displays SDLC context in sidebar
 */
export declare class ContextPanelProvider implements vscode.TreeDataProvider<ContextTreeItem> {
    private readonly apiClient;
    private readonly cacheService;
    private readonly projectDetector?;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<ContextTreeItem | undefined | null | void>;
    private context;
    private isLoading;
    private lastError;
    private refreshInterval;
    constructor(apiClient: ApiClient, cacheService: CacheService, projectDetector?: ProjectDetector | undefined);
    /**
     * Setup auto-refresh interval
     */
    private setupAutoRefresh;
    /**
     * Refresh context data
     */
    refresh(): Promise<void>;
    /**
     * Clear context data
     */
    clear(): void;
    /**
     * Dispose resources
     */
    dispose(): void;
    /**
     * Get tree item for display
     */
    getTreeItem(element: ContextTreeItem): vscode.TreeItem;
    /**
     * Get children for tree view
     */
    getChildren(element?: ContextTreeItem): Thenable<ContextTreeItem[]>;
    /**
     * Build root level tree items
     */
    private buildRootItems;
    /**
     * Build context tree items from overlay data
     */
    private buildContextItems;
    /**
     * Format constraint type for display
     */
    private formatConstraintType;
    /**
     * Map severity to tree item type
     */
    private mapSeverityToType;
    /**
     * Format timestamp for display
     */
    private formatTimestamp;
}
/**
 * Context Status Bar Item
 *
 * Shows quick context info in VS Code status bar
 */
export declare class ContextStatusBarItem {
    private statusBarItem;
    constructor();
    /**
     * Update status bar with context
     */
    update(context: SDLCContextOverlay | null): void;
    /**
     * Show loading state
     */
    showLoading(): void;
    /**
     * Show error state
     */
    showError(message: string): void;
    /**
     * Dispose status bar item
     */
    dispose(): void;
}
/**
 * Register context panel commands
 */
export declare function registerContextCommands(context: vscode.ExtensionContext, contextPanel: ContextPanelProvider, statusBar: ContextStatusBarItem): void;
export {};
//# sourceMappingURL=contextPanel.d.ts.map