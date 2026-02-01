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
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';

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
export class ContextTreeItem extends vscode.TreeItem {
    public readonly children: ContextTreeItem[];

    constructor(
        label: string,
        collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly itemType: ContextItemType,
        itemDescription?: string,
        children?: ContextTreeItem[],
        itemTooltip?: string,
        itemCommand?: vscode.Command,
    ) {
        super(label, collapsibleState);
        this.contextValue = itemType;
        // Force convert to string to handle edge cases where objects are passed
        this.description = itemDescription ? String(itemDescription) : '';
        this.tooltip = itemTooltip;
        this.children = children ?? [];

        // Set command if provided
        if (itemCommand) {
            this.command = itemCommand;
        }

        // Set icons based on item type
        this.iconPath = this.getIcon();
    }

    private getIcon(): vscode.ThemeIcon {
        switch (this.itemType) {
            case 'header':
                return new vscode.ThemeIcon('dashboard');
            case 'stage':
                return new vscode.ThemeIcon('layers');
            case 'gate':
                return new vscode.ThemeIcon('shield');
            case 'sprint':
                return new vscode.ThemeIcon('calendar');
            case 'constraint':
                return new vscode.ThemeIcon('list-unordered');
            case 'warning':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('editorWarning.foreground'));
            case 'error':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('editorError.foreground'));
            case 'info':
                return new vscode.ThemeIcon('info', new vscode.ThemeColor('editorInfo.foreground'));
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }
}

/**
 * Context Panel Provider - displays SDLC context in sidebar
 */
export class ContextPanelProvider implements vscode.TreeDataProvider<ContextTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ContextTreeItem | undefined | null | void> =
        new vscode.EventEmitter<ContextTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ContextTreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private context: SDLCContextOverlay | null = null;
    private isLoading: boolean = false;
    private lastError: string | null = null;
    private refreshInterval: ReturnType<typeof setInterval> | undefined;

    constructor(
        private readonly apiClient: ApiClient,
        private readonly cacheService: CacheService,
        private readonly projectDetector?: ProjectDetector,
    ) {
        // Start auto-refresh
        this.setupAutoRefresh();
    }

    /**
     * Setup auto-refresh interval
     */
    private setupAutoRefresh(): void {
        const config = ConfigManager.getInstance();
        const intervalMs = config.autoRefreshInterval * 1000;

        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        this.refreshInterval = setInterval(() => {
            void this.refresh();
        }, intervalMs);
    }

    /**
     * Refresh context data
     */
    async refresh(): Promise<void> {
        // Sprint 127: Use ProjectDetector if available, fallback to manual config
        let projectId: string | undefined;
        let projectName: string | undefined;

        Logger.info('Context Overlay refresh started');

        if (this.projectDetector) {
            Logger.debug('Attempting auto-detect project...');
            try {
                const detected = await this.projectDetector.getCurrentProject();
                if (detected) {
                    projectId = detected.uuid;
                    projectName = detected.name;
                    Logger.info(`✅ Auto-detected project: ${projectName} (${projectId}) from ${detected.source}`);
                } else {
                    // UUID resolution failed, but try to get just the name for better error message
                    const nameOnly = this.projectDetector.detectProjectName();
                    if (nameOnly) {
                        projectName = nameOnly.name;
                        Logger.warn(`❌ Project "${projectName}" detected but not registered in backend`);
                    } else {
                        Logger.warn('❌ Auto-detect returned null');
                    }
                }
            } catch (error) {
                Logger.error(`❌ Auto-detect failed: ${error instanceof Error ? error.message : String(error)}`);
            }
        } else {
            Logger.debug('ProjectDetector not available');
        }

        // Fallback to manual config if auto-detect fails
        if (!projectId) {
            projectId = this.apiClient.getCurrentProjectId();
            Logger.debug(`Fallback to manual config: ${projectId || 'NOT SET'}`);
        }

        if (!projectId) {
            this.context = null;
            // Show project name if detected but not registered
            if (projectName) {
                this.lastError = `Project "${projectName}" not registered yet. Click to register with backend.`;
                Logger.warn(`❌ Project "${projectName}" detected but no UUID - needs registration`);
            } else {
                this.lastError = 'No project detected. Please configure sdlc.defaultProjectId in settings.';
                Logger.error('❌ No project ID available - showing error');
            }
            this._onDidChangeTreeData.fire();
            return;
        }

        Logger.info(`Fetching context overlay for project: ${projectId}`);

        this.isLoading = true;
        this._onDidChangeTreeData.fire();

        try {
            // Try cache first
            const cacheKey = `context_overlay_${projectId}`;
            const cached = this.cacheService.get<SDLCContextOverlay>(cacheKey);

            if (cached && cached.data) {
                this.context = cached.data;
                this.lastError = null;
                this.isLoading = false;
                this._onDidChangeTreeData.fire();
            }

            // Fetch fresh data
            Logger.debug(`Calling API: getContextOverlay(${projectId})`);
            const overlay = await this.apiClient.getContextOverlay(projectId);
            Logger.info(`✅ Context overlay received successfully`);

            this.context = overlay;
            this.lastError = null;

            // Update cache (5 minute TTL)
            void this.cacheService.set(cacheKey, overlay, 300000);

            Logger.info(`Context overlay refreshed successfully for project ${projectId}`);
        } catch (error: any) {
            // Sprint 127: Auto-register project if not found in backend
            const statusCode = error?.response?.status || error?.statusCode;

            if (statusCode === 422 || statusCode === 404) {
                // Project not found in backend - prompt to register
                Logger.warn(`Project "${projectName}" not found in backend (${statusCode})`);

                // Show friendly message with action
                this.context = null;
                this.lastError = `Project "${projectName || 'Unknown'}" not registered yet. Click to register with backend.`;

                // TODO: Add "Register Project" command that creates project in backend
                // For now, show helpful error message
            } else {
                // Other errors - extract meaningful error message
                let message = 'Unknown error';

                if (error?.response?.data?.detail) {
                    // FastAPI error format: {detail: "message"}
                    message = error.response.data.detail;
                } else if (error?.response?.data?.message) {
                    // Alternative error format: {message: "message"}
                    message = error.response.data.message;
                } else if (error?.message) {
                    // Standard Error object
                    message = error.message;
                } else if (typeof error === 'string') {
                    // String error
                    message = error;
                } else {
                    // Fallback: stringify the error
                    try {
                        message = JSON.stringify(error);
                    } catch {
                        message = String(error);
                    }
                }

                Logger.error(`Failed to fetch context overlay: ${message}`);
                this.lastError = `Offline mode: ${message}`;
            }
        } finally {
            this.isLoading = false;
            this._onDidChangeTreeData.fire();
        }
    }

    /**
     * Clear context data
     */
    clear(): void {
        this.context = null;
        this.lastError = null;
        this._onDidChangeTreeData.fire();
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    /**
     * Get tree item for display
     */
    getTreeItem(element: ContextTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Get children for tree view
     */
    getChildren(element?: ContextTreeItem): Thenable<ContextTreeItem[]> {
        if (element) {
            return Promise.resolve(element.children);
        }

        // Root level
        return Promise.resolve(this.buildRootItems());
    }

    /**
     * Build root level tree items
     */
    private buildRootItems(): ContextTreeItem[] {
        const items: ContextTreeItem[] = [];

        // Loading state
        if (this.isLoading && !this.context) {
            items.push(
                new ContextTreeItem(
                    'Loading...',
                    vscode.TreeItemCollapsibleState.None,
                    'info',
                    'Fetching context overlay',
                )
            );
            return items;
        }

        // Error state
        if (this.lastError && !this.context) {
            // Check if this is a "not registered" error - make it actionable
            const isNotRegistered = this.lastError.includes('not registered');
            items.push(
                new ContextTreeItem(
                    isNotRegistered ? 'Project Not Registered' : 'Error',
                    vscode.TreeItemCollapsibleState.None,
                    'error',
                    isNotRegistered ? 'Click to initialize project' : this.lastError,
                    undefined,
                    this.lastError,
                    isNotRegistered ? {
                        command: 'sdlc.init',
                        title: 'Initialize SDLC Project',
                    } : undefined,
                )
            );
            return items;
        }

        // No project selected
        if (!this.context) {
            items.push(
                new ContextTreeItem(
                    'No Project Selected',
                    vscode.TreeItemCollapsibleState.None,
                    'info',
                    'Select a project to view context',
                )
            );
            return items;
        }

        // Build context items
        items.push(...this.buildContextItems());

        return items;
    }

    /**
     * Build context tree items from overlay data
     */
    private buildContextItems(): ContextTreeItem[] {
        if (!this.context) {
            return [];
        }

        const items: ContextTreeItem[] = [];

        // Stage & Gate header
        const stageGateItem = new ContextTreeItem(
            'Stage & Gate',
            vscode.TreeItemCollapsibleState.Expanded,
            'header',
            undefined,
            [
                new ContextTreeItem(
                    `Stage: ${this.context.stage_name}`,
                    vscode.TreeItemCollapsibleState.None,
                    'stage',
                    this.context.strict_mode ? '🔒 STRICT MODE' : undefined,
                    undefined,
                    this.context.strict_mode
                        ? 'Strict mode is active. Only bug fixes allowed.'
                        : `Current SDLC stage: ${this.context.stage_name}`,
                ),
                new ContextTreeItem(
                    `Gate: ${this.context.gate_status}`,
                    vscode.TreeItemCollapsibleState.None,
                    'gate',
                    undefined,
                    undefined,
                    `Current gate status: ${this.context.gate_status}`,
                ),
            ],
        );
        items.push(stageGateItem);

        // Strict mode warning
        if (this.context.strict_mode) {
            items.push(
                new ContextTreeItem(
                    '⚠️ STRICT MODE ACTIVE',
                    vscode.TreeItemCollapsibleState.None,
                    'warning',
                    'Only bug fixes allowed',
                    undefined,
                    'Project is in strict mode. New features will be blocked by gate evaluation.',
                )
            );
        }

        // Sprint info
        if (this.context.sprint) {
            const sprint = this.context.sprint;
            const sprintItem = new ContextTreeItem(
                'Current Sprint',
                vscode.TreeItemCollapsibleState.Expanded,
                'header',
                undefined,
                [
                    new ContextTreeItem(
                        `Sprint ${sprint.number}`,
                        vscode.TreeItemCollapsibleState.None,
                        'sprint',
                        sprint.goal,
                        undefined,
                        `Sprint goal: ${sprint.goal}`,
                    ),
                    new ContextTreeItem(
                        `${sprint.days_remaining} days remaining`,
                        vscode.TreeItemCollapsibleState.None,
                        'info',
                        sprint.end_date ? `Ends: ${sprint.end_date}` : undefined,
                    ),
                ],
            );
            items.push(sprintItem);
        }

        // Constraints
        if (this.context.constraints && this.context.constraints.length > 0) {
            const constraintItems = this.context.constraints.map((c) =>
                new ContextTreeItem(
                    this.formatConstraintType(c.type),
                    vscode.TreeItemCollapsibleState.None,
                    this.mapSeverityToType(c.severity),
                    c.message,
                    undefined,
                    c.affected_files?.length
                        ? `Affects: ${c.affected_files.join(', ')}`
                        : c.message,
                )
            );

            const constraintsHeader = new ContextTreeItem(
                'Active Constraints',
                vscode.TreeItemCollapsibleState.Expanded,
                'header',
                `${this.context.constraints.length} items`,
                constraintItems,
            );
            items.push(constraintsHeader);
        }

        // Last updated
        items.push(
            new ContextTreeItem(
                'Last Updated',
                vscode.TreeItemCollapsibleState.None,
                'info',
                this.formatTimestamp(this.context.generated_at),
            )
        );

        return items;
    }

    /**
     * Format constraint type for display
     */
    private formatConstraintType(type: string): string {
        return type
            .replace(/_/g, ' ')
            .replace(/\b\w/g, (c) => c.toUpperCase());
    }

    /**
     * Map severity to tree item type
     */
    private mapSeverityToType(severity: string): ContextItemType {
        switch (severity) {
            case 'error':
                return 'error';
            case 'warning':
                return 'warning';
            default:
                return 'info';
        }
    }

    /**
     * Format timestamp for display
     */
    private formatTimestamp(isoString: string): string {
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString();
        } catch {
            return isoString;
        }
    }
}

/**
 * Context Status Bar Item
 *
 * Shows quick context info in VS Code status bar
 */
export class ContextStatusBarItem {
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.command = 'sdlc.refreshContext';
        this.statusBarItem.show();
        this.update(null);
    }

    /**
     * Update status bar with context
     */
    update(context: SDLCContextOverlay | null): void {

        if (!context) {
            this.statusBarItem.text = '$(shield) SDLC: No Project';
            this.statusBarItem.tooltip = 'Click to select a project';
            this.statusBarItem.backgroundColor = undefined;
            return;
        }

        // Build status text
        const stageShort = context.stage_name.substring(0, 8);
        const gateShort = context.gate_status.split(' ')[0] || 'N/A';

        let text = `$(shield) ${stageShort} | ${gateShort}`;

        if (context.strict_mode) {
            text += ' 🔒';
        }

        const errorCount = context.constraints.filter((c) => c.severity === 'error').length;
        const warningCount = context.constraints.filter((c) => c.severity === 'warning').length;

        if (errorCount > 0) {
            text += ` $(error) ${errorCount}`;
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        } else if (warningCount > 0) {
            text += ` $(warning) ${warningCount}`;
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        } else {
            this.statusBarItem.backgroundColor = undefined;
        }

        this.statusBarItem.text = text;

        // Build tooltip
        const tooltipLines = [
            `Stage: ${context.stage_name}`,
            `Gate: ${context.gate_status}`,
            context.strict_mode ? '⚠️ Strict Mode Active' : '',
            context.sprint ? `Sprint ${context.sprint.number}: ${context.sprint.goal}` : '',
            context.constraints.length > 0
                ? `Constraints: ${context.constraints.length} active`
                : '',
            '',
            'Click to refresh context',
        ].filter(Boolean);

        this.statusBarItem.tooltip = tooltipLines.join('\n');
    }

    /**
     * Show loading state
     */
    showLoading(): void {
        this.statusBarItem.text = '$(sync~spin) SDLC: Loading...';
    }

    /**
     * Show error state
     */
    showError(message: string): void {
        this.statusBarItem.text = '$(error) SDLC: Error';
        this.statusBarItem.tooltip = `Error: ${message}\nClick to retry`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    }

    /**
     * Dispose status bar item
     */
    dispose(): void {
        this.statusBarItem.dispose();
    }
}

/**
 * Register context panel commands
 */
export function registerContextCommands(
    context: vscode.ExtensionContext,
    contextPanel: ContextPanelProvider,
    statusBar: ContextStatusBarItem,
): void {
    // Refresh context command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.refreshContext', async () => {
            statusBar.showLoading();
            await contextPanel.refresh();

            // Update status bar after refresh
            const projectId = contextPanel['apiClient'].getCurrentProjectId();
            if (projectId) {
                try {
                    const overlay = await contextPanel['apiClient'].getContextOverlay(projectId);
                    statusBar.update(overlay);
                    void vscode.window.showInformationMessage('SDLC context refreshed');
                } catch (error) {
                    const message = error instanceof Error ? error.message : String(error);
                    statusBar.showError(message);
                }
            } else {
                statusBar.update(null);
            }
        })
    );

    // Show context details command
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.showContextDetails', () => {
            const overlay = contextPanel['context'];
            if (!overlay) {
                void vscode.window.showWarningMessage('No context available. Select a project first.');
                return;
            }

            // Show context in output channel
            const outputChannel = vscode.window.createOutputChannel('SDLC Context');
            outputChannel.clear();
            outputChannel.appendLine('='.repeat(60));
            outputChannel.appendLine('SDLC Context Overlay');
            outputChannel.appendLine('='.repeat(60));
            outputChannel.appendLine('');
            outputChannel.appendLine(`Stage: ${overlay.stage_name}`);
            outputChannel.appendLine(`Gate: ${overlay.gate_status}`);
            outputChannel.appendLine(`Strict Mode: ${overlay.strict_mode ? 'YES' : 'No'}`);
            outputChannel.appendLine('');

            if (overlay.sprint) {
                outputChannel.appendLine('-'.repeat(60));
                outputChannel.appendLine('SPRINT INFO');
                outputChannel.appendLine('-'.repeat(60));
                outputChannel.appendLine(`Sprint: ${overlay.sprint.number}`);
                outputChannel.appendLine(`Goal: ${overlay.sprint.goal}`);
                outputChannel.appendLine(`Days Remaining: ${overlay.sprint.days_remaining}`);
                outputChannel.appendLine('');
            }

            if (overlay.constraints.length > 0) {
                outputChannel.appendLine('-'.repeat(60));
                outputChannel.appendLine('ACTIVE CONSTRAINTS');
                outputChannel.appendLine('-'.repeat(60));
                for (const c of overlay.constraints) {
                    const icon =
                        c.severity === 'error'
                            ? '🔴'
                            : c.severity === 'warning'
                              ? '🟡'
                              : 'ℹ️';
                    outputChannel.appendLine(`${icon} [${c.type}] ${c.message}`);
                }
                outputChannel.appendLine('');
            }

            outputChannel.appendLine(`Generated: ${overlay.generated_at}`);
            outputChannel.show();
        })
    );

    // Copy context as PR comment
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.copyContextAsPRComment', async () => {
            const overlay = contextPanel['context'];
            if (!overlay) {
                void vscode.window.showWarningMessage('No context available. Select a project first.');
                return;
            }

            const prComment = overlay.formatted?.pr_comment || generatePRComment(overlay);
            await vscode.env.clipboard.writeText(prComment);
            void vscode.window.showInformationMessage('Context copied as PR comment');
        })
    );
}

/**
 * Generate PR comment from overlay
 */
function generatePRComment(overlay: SDLCContextOverlay): string {
    const lines: string[] = [
        '## 🛡️ SDLC Context Overlay',
        '',
        `**Stage:** ${overlay.stage_name}`,
        `**Gate:** ${overlay.gate_status}`,
    ];

    if (overlay.strict_mode) {
        lines.push('');
        lines.push('> ⚠️ **STRICT MODE ACTIVE** - Only bug fixes allowed');
    }

    if (overlay.sprint) {
        lines.push('');
        lines.push(`### 📅 Sprint ${overlay.sprint.number}`);
        lines.push(`**Goal:** ${overlay.sprint.goal}`);
        lines.push(`**Days Remaining:** ${overlay.sprint.days_remaining}`);
    }

    if (overlay.constraints.length > 0) {
        lines.push('');
        lines.push('### 📋 Active Constraints');
        lines.push('');
        for (const c of overlay.constraints) {
            const icon =
                c.severity === 'error'
                    ? '🔴'
                    : c.severity === 'warning'
                      ? '🟡'
                      : 'ℹ️';
            lines.push(`- ${icon} **${c.type}**: ${c.message}`);
        }
    }

    lines.push('');
    lines.push('---');
    lines.push(`*Generated by SDLC Orchestrator at ${new Date(overlay.generated_at).toLocaleString()}*`);

    return lines.join('\n');
}
