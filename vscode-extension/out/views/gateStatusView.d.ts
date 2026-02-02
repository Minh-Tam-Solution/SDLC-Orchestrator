/**
 * SDLC Orchestrator Gate Status View
 *
 * TreeDataProvider for displaying gate status (G0-G5) in the sidebar.
 * Shows progress, evidence count, and approval status for each gate.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
 */
import * as vscode from 'vscode';
import { ApiClient, Gate } from '../services/apiClient';
import { CacheService } from '../services/cacheService';
/**
 * Tree item representing a gate or gate detail
 */
export declare class GateTreeItem extends vscode.TreeItem {
    readonly label: string;
    readonly collapsibleState: vscode.TreeItemCollapsibleState;
    readonly gate?: Gate | undefined;
    readonly itemType: 'gate' | 'detail';
    readonly detailKey?: string | undefined;
    constructor(label: string, collapsibleState: vscode.TreeItemCollapsibleState, gate?: Gate | undefined, itemType?: 'gate' | 'detail', detailKey?: string | undefined);
    /**
     * Configures the tree item for a gate
     * Sprint 136: Use gate_name instead of gate_type
     */
    private setupGateItem;
    /**
     * Gets status display text
     * Sprint 136: Normalize to lowercase for case-insensitive comparison
     */
    private getStatusText;
    /**
     * Gets icon based on gate status
     * Sprint 136: Normalize to lowercase for case-insensitive comparison
     */
    private getStatusIcon;
}
/**
 * Tree data provider for gate status sidebar
 */
export declare class GateStatusProvider implements vscode.TreeDataProvider<GateTreeItem> {
    private apiClient;
    private cacheService?;
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<GateTreeItem | null | undefined>;
    private gates;
    private isLoading;
    private hasError;
    private errorMessage;
    private lastError;
    private isUsingCachedData;
    constructor(apiClient: ApiClient, cacheService?: CacheService | undefined);
    /**
     * Refreshes the gate status data
     */
    refresh(): Promise<void>;
    /**
     * Clears the view data
     */
    clear(): void;
    /**
     * Gets tree item for element
     */
    getTreeItem(element: GateTreeItem): vscode.TreeItem;
    /**
     * Gets children for tree item
     */
    getChildren(element?: GateTreeItem): GateTreeItem[];
    /**
     * Gets root level items (gate stages)
     */
    private getRootItems;
    /**
     * Gets detail items for a gate
     */
    private getGateDetails;
    /**
     * Checks for gate status changes and shows notifications
     * Sprint 136: Normalize to lowercase for case-insensitive comparison
     */
    private checkForNotifications;
    /**
     * Gets current gate status summary
     * Sprint 136: Normalize to lowercase for case-insensitive comparison
     */
    getStatusSummary(): {
        total: number;
        approved: number;
        pending: number;
        inProgress: number;
    };
}
//# sourceMappingURL=gateStatusView.d.ts.map