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
import { CacheService, CacheKeys, CacheTTL } from '../services/cacheService';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { classifyError, ErrorCode, SDLCError } from '../utils/errors';

/**
 * Gate stage definitions with metadata
 */
interface GateStageInfo {
    id: string;
    name: string;
    description: string;
    stage: number;
}

/**
 * SDLC 4.9.1 Gate stages
 */
const GATE_STAGES: GateStageInfo[] = [
    { id: 'G0.1', name: 'Problem Definition', description: 'Define the problem to solve', stage: 0 },
    { id: 'G0.2', name: 'Solution Diversity', description: 'Explore multiple solutions', stage: 0 },
    { id: 'G1', name: 'Market Validation', description: 'Validate market need', stage: 1 },
    { id: 'G2', name: 'Design Ready', description: 'Complete technical design', stage: 2 },
    { id: 'G3', name: 'Ship Ready', description: 'Ready for production deployment', stage: 3 },
    { id: 'G4', name: 'Launch Ready', description: 'Ready for public launch', stage: 4 },
    { id: 'G5', name: 'Scale Ready', description: 'Ready to scale operations', stage: 5 },
];

/**
 * Tree item representing a gate or gate detail
 */
export class GateTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly gate?: Gate,
        public readonly itemType: 'gate' | 'detail' = 'gate',
        public readonly detailKey?: string
    ) {
        super(label, collapsibleState);
        this.contextValue = itemType;

        if (gate && itemType === 'gate') {
            this.setupGateItem(gate);
        }
    }

    /**
     * Configures the tree item for a gate
     */
    private setupGateItem(gate: Gate): void {
        const stageInfo = GATE_STAGES.find((s) => gate.gate_type.startsWith(s.id));

        // Set description
        this.description = this.getStatusText(gate.status);

        // Set icon based on status
        this.iconPath = this.getStatusIcon(gate.status);

        // Set tooltip
        this.tooltip = new vscode.MarkdownString();
        this.tooltip.appendMarkdown(`### ${stageInfo?.name ?? gate.gate_type}\n\n`);
        this.tooltip.appendMarkdown(`**Status:** ${gate.status}\n\n`);
        this.tooltip.appendMarkdown(
            `**Evidence:** ${gate.evidence_count}/${gate.required_evidence_count}\n\n`
        );
        if (stageInfo?.description) {
            this.tooltip.appendMarkdown(`_${stageInfo.description}_`);
        }

        // Set command for clicking
        this.command = {
            command: 'sdlc.openGate',
            title: 'Open Gate',
            arguments: [gate.id],
        };
    }

    /**
     * Gets status display text
     */
    private getStatusText(status: string): string {
        switch (status) {
            case 'approved':
                return 'Approved';
            case 'pending_approval':
                return 'Pending Approval';
            case 'in_progress':
                return 'In Progress';
            case 'rejected':
                return 'Rejected';
            case 'not_started':
            default:
                return 'Not Started';
        }
    }

    /**
     * Gets icon based on gate status
     */
    private getStatusIcon(status: string): vscode.ThemeIcon {
        switch (status) {
            case 'approved':
                return new vscode.ThemeIcon(
                    'check',
                    new vscode.ThemeColor('sdlc.gateApproved')
                );
            case 'pending_approval':
                return new vscode.ThemeIcon(
                    'clock',
                    new vscode.ThemeColor('sdlc.gatePending')
                );
            case 'in_progress':
                return new vscode.ThemeIcon(
                    'sync~spin',
                    new vscode.ThemeColor('sdlc.gatePending')
                );
            case 'rejected':
                return new vscode.ThemeIcon(
                    'x',
                    new vscode.ThemeColor('sdlc.gateRejected')
                );
            case 'not_started':
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }
}

/**
 * Tree data provider for gate status sidebar
 */
export class GateStatusProvider implements vscode.TreeDataProvider<GateTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<GateTreeItem | undefined | null>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private gates: Gate[] = [];
    private isLoading = false;
    private hasError = false;
    private errorMessage = '';
    private lastError: SDLCError | undefined;
    private isUsingCachedData = false;

    constructor(
        private apiClient: ApiClient,
        private cacheService?: CacheService
    ) {}

    /**
     * Refreshes the gate status data
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
                this.gates = [];
                Logger.info('No project selected for gate status');
            } else {
                // Use cache service if available for offline support
                if (this.cacheService) {
                    const cacheKey = CacheKeys.GATES(projectId);
                    const result = await this.cacheService.getOrFetch<Gate[]>(
                        cacheKey,
                        () => this.apiClient.getGates(projectId),
                        CacheTTL.GATES
                    );

                    this.gates = result.data;
                    this.isUsingCachedData = result.isCached;

                    if (result.isStale) {
                        Logger.info(`Using stale cached gates for project ${projectId}`);
                    }
                } else {
                    this.gates = await this.apiClient.getGates(projectId);
                }

                Logger.info(
                    `Loaded ${this.gates.length} gates for project ${projectId}` +
                        (this.isUsingCachedData ? ' (from cache)' : '')
                );

                // Check for notifications
                this.checkForNotifications();
            }
        } catch (error) {
            this.lastError = classifyError(error);
            this.hasError = true;
            this.errorMessage = this.lastError.getUserMessage();
            Logger.error(`Failed to refresh gates: ${this.errorMessage}`);

            // Try to get cached data on error (offline mode)
            const projectId = this.apiClient.getCurrentProjectId();
            if (projectId && this.cacheService) {
                const cached = this.cacheService.get<Gate[]>(CacheKeys.GATES(projectId));
                if (cached) {
                    this.gates = cached.data;
                    this.isUsingCachedData = true;
                    this.hasError = false;
                    Logger.info('Using cached gates due to network error');
                } else {
                    this.gates = [];
                }
            } else {
                this.gates = [];
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
        this.gates = [];
        this.hasError = false;
        this.errorMessage = '';
        this._onDidChangeTreeData.fire(undefined);
    }

    /**
     * Gets tree item for element
     */
    getTreeItem(element: GateTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Gets children for tree item
     */
    getChildren(element?: GateTreeItem): GateTreeItem[] {
        // Root level - show loading/error state or gates
        if (!element) {
            return this.getRootItems();
        }

        // Gate level - show details
        if (element.gate && element.itemType === 'gate') {
            return this.getGateDetails(element.gate);
        }

        return [];
    }

    /**
     * Gets root level items (gate stages)
     */
    private getRootItems(): GateTreeItem[] {
        const items: GateTreeItem[] = [];

        // Loading state
        if (this.isLoading) {
            const item = new GateTreeItem(
                'Loading gates...',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('loading~spin');
            return [item];
        }

        // Error state with enhanced error handling
        if (this.hasError) {
            const item = new GateTreeItem(
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
            const item = new GateTreeItem(
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
            const offlineItem = new GateTreeItem(
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

        // No gates found
        if (this.gates.length === 0) {
            const item = new GateTreeItem(
                'No gates found',
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('info');
            items.push(item);
            return items;
        }

        // Map gates to stage items
        const gateItems = GATE_STAGES.map((stageInfo) => {
            const gate = this.gates.find((g) => g.gate_type.startsWith(stageInfo.id));

            if (gate) {
                return new GateTreeItem(
                    stageInfo.id,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    gate
                );
            }

            // Gate not started
            const item = new GateTreeItem(
                stageInfo.id,
                vscode.TreeItemCollapsibleState.None
            );
            item.description = 'Not Started';
            item.iconPath = new vscode.ThemeIcon('circle-outline');
            item.tooltip = new vscode.MarkdownString(
                `### ${stageInfo.name}\n\n_${stageInfo.description}_`
            );
            return item;
        });

        return [...items, ...gateItems];
    }

    /**
     * Gets detail items for a gate
     */
    private getGateDetails(gate: Gate): GateTreeItem[] {
        const details: GateTreeItem[] = [];

        // Status detail
        const statusItem = new GateTreeItem(
            `Status: ${gate.status}`,
            vscode.TreeItemCollapsibleState.None,
            undefined,
            'detail',
            'status'
        );
        statusItem.iconPath = new vscode.ThemeIcon('info');
        details.push(statusItem);

        // Evidence count
        const evidenceItem = new GateTreeItem(
            `Evidence: ${gate.evidence_count}/${gate.required_evidence_count}`,
            vscode.TreeItemCollapsibleState.None,
            undefined,
            'detail',
            'evidence'
        );
        const evidencePercentage =
            gate.required_evidence_count > 0
                ? Math.round((gate.evidence_count / gate.required_evidence_count) * 100)
                : 0;
        evidenceItem.description = `${evidencePercentage}%`;
        evidenceItem.iconPath = new vscode.ThemeIcon('file');
        details.push(evidenceItem);

        // Approver info (if approved)
        if (gate.approved_at && gate.approver_id) {
            const approverItem = new GateTreeItem(
                `Approved: ${new Date(gate.approved_at).toLocaleDateString()}`,
                vscode.TreeItemCollapsibleState.None,
                undefined,
                'detail',
                'approver'
            );
            approverItem.iconPath = new vscode.ThemeIcon('person');
            details.push(approverItem);
        }

        // Updated timestamp
        const updatedItem = new GateTreeItem(
            `Updated: ${new Date(gate.updated_at).toLocaleDateString()}`,
            vscode.TreeItemCollapsibleState.None,
            undefined,
            'detail',
            'updated'
        );
        updatedItem.iconPath = new vscode.ThemeIcon('history');
        details.push(updatedItem);

        return details;
    }

    /**
     * Checks for gate status changes and shows notifications
     */
    private checkForNotifications(): void {
        const config = ConfigManager.getInstance();
        if (!config.enableNotifications) {
            return;
        }

        // Find gates pending approval
        const pendingGates = this.gates.filter(
            (g) => g.status === 'pending_approval'
        );

        if (pendingGates.length > 0) {
            const names = pendingGates
                .map((g) => g.gate_type)
                .join(', ');

            void vscode.window.showInformationMessage(
                `${pendingGates.length} gate(s) pending approval: ${names}`,
                'View Gates'
            ).then((selection) => {
                if (selection === 'View Gates') {
                    void vscode.commands.executeCommand(
                        'sdlc-gate-status.focus'
                    );
                }
            });
        }
    }

    /**
     * Gets current gate status summary
     */
    getStatusSummary(): {
        total: number;
        approved: number;
        pending: number;
        inProgress: number;
    } {
        return {
            total: GATE_STAGES.length,
            approved: this.gates.filter((g) => g.status === 'approved').length,
            pending: this.gates.filter((g) => g.status === 'pending_approval').length,
            inProgress: this.gates.filter((g) => g.status === 'in_progress').length,
        };
    }
}
