/**
 * SDLC Orchestrator Violations View
 *
 * TreeDataProvider for displaying compliance violations in the sidebar.
 * Shows severity, status, and quick actions for each violation.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
 */
import * as vscode from 'vscode';
import { ApiClient, Violation } from '../services/apiClient';
import { CacheService } from '../services/cacheService';
/**
 * Tree item representing a violation or group
 */
export declare class ViolationTreeItem extends vscode.TreeItem {
    readonly label: string;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    readonly violation?: Violation | undefined;
    readonly itemType: 'violation' | 'group' | 'detail';
    readonly groupKey?: string | undefined;
    constructor(label: string, collapsibleState: vscode.TreeItemCollapsibleState, violation?: Violation | undefined, itemType?: 'violation' | 'group' | 'detail', groupKey?: string | undefined);
    /**
     * Configures the tree item for a violation
     */
    private setupViolationItem;
    /**
     * Gets icon based on violation severity
     */
    private getSeverityIcon;
}
/**
 * Tree data provider for violations sidebar
 */
export declare class ViolationsProvider implements vscode.TreeDataProvider<ViolationTreeItem> {
    private apiClient;
    private cacheService?;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<ViolationTreeItem | null | undefined>;
    private violations;
    private isLoading;
    private hasError;
    private errorMessage;
    private lastError;
    private isUsingCachedData;
    private groupBy;
    constructor(apiClient: ApiClient, cacheService?: CacheService | undefined);
    /**
     * Refreshes the violations data
     */
    refresh(): Promise<void>;
    /**
     * Clears the view data
     */
    clear(): void;
    /**
     * Sets the grouping method
     */
    setGroupBy(groupBy: 'severity' | 'gate' | 'type'): void;
    /**
     * Gets tree item for element
     */
    getTreeItem(element: ViolationTreeItem): vscode.TreeItem;
    /**
     * Gets children for tree item
     */
    getChildren(element?: ViolationTreeItem): ViolationTreeItem[];
    /**
     * Gets root level items (groups or violations)
     */
    private getRootItems;
    /**
     * Gets grouped items based on current groupBy setting
     */
    private getGroupedItems;
    /**
     * Gets violations for a specific group
     */
    private getGroupItems;
    /**
     * Gets detail items for a violation
     */
    private getViolationDetails;
    /**
     * Gets icon for severity group
     */
    private getSeverityGroupIcon;
    /**
     * Updates the violations badge in activity bar
     */
    private updateBadge;
    /**
     * Gets violation count summary
     */
    getViolationSummary(): {
        total: number;
        critical: number;
        high: number;
        medium: number;
        low: number;
    };
}
//# sourceMappingURL=violationsView.d.ts.map