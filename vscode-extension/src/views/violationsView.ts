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
import { CacheService, CacheKeys, CacheTTL } from '../services/cacheService';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { classifyError, ErrorCode, SDLCError } from '../utils/errors';

/**
 * Severity order for sorting
 */
const SEVERITY_ORDER: Record<string, number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
};

/**
 * Tree item representing a violation or group
 */
export class ViolationTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly violation?: Violation,
        public readonly itemType: 'violation' | 'group' | 'detail' = 'violation',
        public readonly groupKey?: string
    ) {
        super(label, collapsibleState);
        this.contextValue = itemType;

        if (violation && itemType === 'violation') {
            this.setupViolationItem(violation);
        }
    }

    /**
     * Configures the tree item for a violation
     */
    private setupViolationItem(violation: Violation): void {
        // Set description
        this.description = violation.severity;

        // Set icon based on severity
        this.iconPath = this.getSeverityIcon(violation.severity);

        // Set tooltip
        this.tooltip = new vscode.MarkdownString();
        this.tooltip.appendMarkdown(`### ${violation.violation_type}\n\n`);
        this.tooltip.appendMarkdown(`**Severity:** ${violation.severity}\n\n`);
        this.tooltip.appendMarkdown(`**Description:** ${violation.description}\n\n`);
        if (violation.file_path) {
            this.tooltip.appendMarkdown(`**File:** \`${violation.file_path}\`\n\n`);
        }
        if (violation.gate_type) {
            this.tooltip.appendMarkdown(`**Gate:** ${violation.gate_type}`);
        }

        // Set command for clicking
        this.command = {
            command: 'sdlc.showViolationDetails',
            title: 'Show Violation Details',
            arguments: [violation.id],
        };
    }

    /**
     * Gets icon based on violation severity
     */
    private getSeverityIcon(severity: string): vscode.ThemeIcon {
        switch (severity) {
            case 'critical':
                return new vscode.ThemeIcon(
                    'error',
                    new vscode.ThemeColor('sdlc.gateRejected')
                );
            case 'high':
                return new vscode.ThemeIcon(
                    'warning',
                    new vscode.ThemeColor('charts.orange')
                );
            case 'medium':
                return new vscode.ThemeIcon(
                    'warning',
                    new vscode.ThemeColor('sdlc.gatePending')
                );
            case 'low':
            default:
                return new vscode.ThemeIcon(
                    'info',
                    new vscode.ThemeColor('charts.blue')
                );
        }
    }
}

/**
 * Tree data provider for violations sidebar
 */
export class ViolationsProvider implements vscode.TreeDataProvider<ViolationTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ViolationTreeItem | undefined | null>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private violations: Violation[] = [];
    private isLoading = false;
    private hasError = false;
    private errorMessage = '';
    private lastError: SDLCError | undefined;
    private isUsingCachedData = false;
    private groupBy: 'severity' | 'gate' | 'type' = 'severity';

    constructor(
        private apiClient: ApiClient,
        private cacheService?: CacheService
    ) {}

    /**
     * Refreshes the violations data
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
            const projectId = this.apiClient.getCurrentProjectId();

            if (!projectId) {
                this.violations = [];
                Logger.info('No project selected for violations');
            } else {
                // Use cache service if available for offline support
                if (this.cacheService) {
                    const cacheKey = CacheKeys.VIOLATIONS(projectId);
                    const result = await this.cacheService.getOrFetch<Violation[]>(
                        cacheKey,
                        () => this.apiClient.getViolations(projectId, 'open'),
                        CacheTTL.VIOLATIONS
                    );

                    this.violations = result.data;
                    this.isUsingCachedData = result.isCached;

                    if (result.isStale) {
                        Logger.info(`Using stale cached violations for project ${projectId}`);
                    }
                } else {
                    this.violations = await this.apiClient.getViolations(
                        projectId,
                        'open'
                    );
                }

                // Sort by severity
                this.violations.sort(
                    (a, b) =>
                        (SEVERITY_ORDER[a.severity] ?? 4) -
                        (SEVERITY_ORDER[b.severity] ?? 4)
                );

                Logger.info(
                    `Loaded ${this.violations.length} violations for project ${projectId}` +
                        (this.isUsingCachedData ? ' (from cache)' : '')
                );

                // Update badge
                this.updateBadge();
            }
        } catch (error) {
            this.lastError = classifyError(error);
            this.hasError = true;
            this.errorMessage = this.lastError.getUserMessage();
            Logger.error(`Failed to refresh violations: ${this.errorMessage}`);

            // Try to get cached data on error (offline mode)
            const projectId = this.apiClient.getCurrentProjectId();
            if (projectId && this.cacheService) {
                const cached = this.cacheService.get<Violation[]>(
                    CacheKeys.VIOLATIONS(projectId)
                );
                if (cached) {
                    this.violations = cached.data;
                    this.isUsingCachedData = true;
                    this.hasError = false;
                    Logger.info('Using cached violations due to network error');
                } else {
                    this.violations = [];
                }
            } else {
                this.violations = [];
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
        this.violations = [];
        this.hasError = false;
        this.errorMessage = '';
        this._onDidChangeTreeData.fire(undefined);
    }

    /**
     * Sets the grouping method
     */
    setGroupBy(groupBy: 'severity' | 'gate' | 'type'): void {
        this.groupBy = groupBy;
        this._onDidChangeTreeData.fire(undefined);
    }

    /**
     * Gets tree item for element
     */
    getTreeItem(element: ViolationTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Gets children for tree item
     */
    getChildren(element?: ViolationTreeItem): ViolationTreeItem[] {
        // Root level
        if (!element) {
            return this.getRootItems();
        }

        // Group level - show violations in group
        if (element.itemType === 'group' && element.groupKey) {
            return this.getGroupItems(element.groupKey);
        }

        // Violation level - show details
        if (element.violation && element.itemType === 'violation') {
            return this.getViolationDetails(element.violation);
        }

        return [];
    }

    /**
     * Gets root level items (groups or violations)
     */
    private getRootItems(): ViolationTreeItem[] {
        const items: ViolationTreeItem[] = [];

        // Loading state
        if (this.isLoading) {
            const item = new ViolationTreeItem(
                'Loading violations...',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('loading~spin');
            return [item];
        }

        // Error state with enhanced error handling
        if (this.hasError) {
            const item = new ViolationTreeItem(
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

            return [item];
        }

        // No project selected
        if (!this.apiClient.getCurrentProjectId()) {
            const item = new ViolationTreeItem(
                'No project selected',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('info');
            item.command = {
                command: 'sdlc.selectProject',
                title: 'Select Project',
            };
            item.tooltip = 'Click to select a project to monitor';
            return [item];
        }

        // Offline mode indicator
        if (this.isUsingCachedData) {
            const offlineItem = new ViolationTreeItem(
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

        // No violations
        if (this.violations.length === 0) {
            const item = new ViolationTreeItem(
                'No violations found',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon(
                'check',
                new vscode.ThemeColor('sdlc.gateApproved')
            );
            items.push(item);
            return items;
        }

        // Group violations and append to items
        return [...items, ...this.getGroupedItems()];
    }

    /**
     * Gets grouped items based on current groupBy setting
     */
    private getGroupedItems(): ViolationTreeItem[] {
        const groups = new Map<string, Violation[]>();

        for (const violation of this.violations) {
            let key: string;

            switch (this.groupBy) {
                case 'gate':
                    key = violation.gate_type ?? 'No Gate';
                    break;
                case 'type':
                    key = violation.violation_type;
                    break;
                case 'severity':
                default:
                    key = violation.severity;
                    break;
            }

            const existing = groups.get(key) ?? [];
            existing.push(violation);
            groups.set(key, existing);
        }

        // Sort groups
        const sortedKeys = Array.from(groups.keys()).sort((a, b) => {
            if (this.groupBy === 'severity') {
                return (
                    (SEVERITY_ORDER[a] ?? 4) - (SEVERITY_ORDER[b] ?? 4)
                );
            }
            return a.localeCompare(b);
        });

        return sortedKeys.map((key) => {
            const count = groups.get(key)?.length ?? 0;
            const item = new ViolationTreeItem(
                `${key} (${count})`,
                vscode.TreeItemCollapsibleState.Expanded,
                undefined,
                'group',
                key
            );

            // Set icon based on group type
            if (this.groupBy === 'severity') {
                item.iconPath = this.getSeverityGroupIcon(key);
            } else {
                item.iconPath = new vscode.ThemeIcon('folder');
            }

            return item;
        });
    }

    /**
     * Gets violations for a specific group
     */
    private getGroupItems(groupKey: string): ViolationTreeItem[] {
        const filtered = this.violations.filter((v) => {
            switch (this.groupBy) {
                case 'gate':
                    return (v.gate_type ?? 'No Gate') === groupKey;
                case 'type':
                    return v.violation_type === groupKey;
                case 'severity':
                default:
                    return v.severity === groupKey;
            }
        });

        return filtered.map(
            (v) =>
                new ViolationTreeItem(
                    v.violation_type,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    v
                )
        );
    }

    /**
     * Gets detail items for a violation
     */
    private getViolationDetails(violation: Violation): ViolationTreeItem[] {
        const details: ViolationTreeItem[] = [];

        // Description
        const descItem = new ViolationTreeItem(
            violation.description.substring(0, 50) +
                (violation.description.length > 50 ? '...' : ''),
            vscode.TreeItemCollapsibleState.None,
            undefined,
            'detail'
        );
        descItem.iconPath = new vscode.ThemeIcon('note');
        descItem.tooltip = violation.description;
        details.push(descItem);

        // File path if exists
        if (violation.file_path) {
            const fileItem = new ViolationTreeItem(
                violation.file_path,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'detail'
            );
            fileItem.iconPath = new vscode.ThemeIcon('file-code');
            if (violation.line_number) {
                fileItem.description = `Line ${violation.line_number}`;
            }
            details.push(fileItem);
        }

        // AI Fix button
        const fixItem = new ViolationTreeItem(
            'Get AI Fix',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            'detail'
        );
        fixItem.iconPath = new vscode.ThemeIcon('lightbulb');
        fixItem.command = {
            command: 'sdlc.fixViolation',
            title: 'Get AI Fix',
            arguments: [violation.id],
        };
        details.push(fixItem);

        return details;
    }

    /**
     * Gets icon for severity group
     */
    private getSeverityGroupIcon(severity: string): vscode.ThemeIcon {
        switch (severity) {
            case 'critical':
                return new vscode.ThemeIcon(
                    'error',
                    new vscode.ThemeColor('sdlc.gateRejected')
                );
            case 'high':
                return new vscode.ThemeIcon(
                    'warning',
                    new vscode.ThemeColor('charts.orange')
                );
            case 'medium':
                return new vscode.ThemeIcon(
                    'warning',
                    new vscode.ThemeColor('sdlc.gatePending')
                );
            case 'low':
            default:
                return new vscode.ThemeIcon(
                    'info',
                    new vscode.ThemeColor('charts.blue')
                );
        }
    }

    /**
     * Updates the violations badge in activity bar
     */
    private updateBadge(): void {
        const config = ConfigManager.getInstance();
        if (!config.showViolationBadge) {
            return;
        }

        // Count critical/high violations
        const criticalCount = this.violations.filter(
            (v) => v.severity === 'critical' || v.severity === 'high'
        ).length;

        // Would need to store badge view reference to update
        // This is a placeholder for the badge update logic
        Logger.debug(`Violation badge count: ${criticalCount}`);
    }

    /**
     * Gets violation count summary
     */
    getViolationSummary(): {
        total: number;
        critical: number;
        high: number;
        medium: number;
        low: number;
    } {
        return {
            total: this.violations.length,
            critical: this.violations.filter((v) => v.severity === 'critical').length,
            high: this.violations.filter((v) => v.severity === 'high').length,
            medium: this.violations.filter((v) => v.severity === 'medium').length,
            low: this.violations.filter((v) => v.severity === 'low').length,
        };
    }
}
