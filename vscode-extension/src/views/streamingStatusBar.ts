/**
 * Streaming Status Bar - Generation Progress Indicator
 *
 * Displays real-time generation status in the VS Code status bar:
 * - Current status (generating, quality check, complete)
 * - File count and progress
 * - Click to open Generation Panel
 *
 * Sprint 53 Day 3 - Streaming Integration
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';

/**
 * Generation status types
 */
export type GenerationStatus =
    | 'idle'
    | 'connecting'
    | 'generating'
    | 'quality_check'
    | 'completed'
    | 'failed'
    | 'cancelled';

/**
 * Status bar configuration
 */
interface StatusBarConfig {
    text: string;
    tooltip: string;
    icon: string;
    backgroundColor?: vscode.ThemeColor;
}

/**
 * Status configurations for each state
 */
const STATUS_CONFIGS: Record<GenerationStatus, StatusBarConfig> = {
    idle: {
        text: 'SDLC Ready',
        tooltip: 'SDLC Orchestrator - Ready for code generation',
        icon: '$(circle-outline)',
    },
    connecting: {
        text: 'Connecting...',
        tooltip: 'Connecting to code generation stream...',
        icon: '$(sync~spin)',
    },
    generating: {
        text: 'Generating',
        tooltip: 'Code generation in progress',
        icon: '$(sync~spin)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.warningBackground'),
    },
    quality_check: {
        text: 'Quality Gates',
        tooltip: 'Running quality validation gates',
        icon: '$(beaker)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.warningBackground'),
    },
    completed: {
        text: 'Complete',
        tooltip: 'Code generation completed successfully',
        icon: '$(check)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.prominentBackground'),
    },
    failed: {
        text: 'Failed',
        tooltip: 'Code generation failed',
        icon: '$(error)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.errorBackground'),
    },
    cancelled: {
        text: 'Cancelled',
        tooltip: 'Code generation was cancelled',
        icon: '$(circle-slash)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.warningBackground'),
    },
};

/**
 * Streaming Status Bar Manager
 *
 * Manages the status bar item for code generation progress.
 */
export class StreamingStatusBar implements vscode.Disposable {
    private static instance: StreamingStatusBar | undefined;

    private readonly statusBarItem: vscode.StatusBarItem;
    private currentStatus: GenerationStatus = 'idle';
    private fileCount = 0;
    private totalLines = 0;
    private currentFile: string | undefined;
    private hideTimeout: ReturnType<typeof setTimeout> | undefined;

    private constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.command = 'sdlc.showGenerationPanel';
        this.updateDisplay();
        Logger.info('StreamingStatusBar initialized');
    }

    /**
     * Get singleton instance
     */
    public static getInstance(): StreamingStatusBar {
        if (!StreamingStatusBar.instance) {
            StreamingStatusBar.instance = new StreamingStatusBar();
        }
        return StreamingStatusBar.instance;
    }

    /**
     * Update the status
     */
    public setStatus(status: GenerationStatus): void {
        this.currentStatus = status;
        this.clearHideTimeout();
        this.updateDisplay();

        // Auto-hide after completion
        if (status === 'completed' || status === 'cancelled') {
            this.hideTimeout = setTimeout(() => {
                this.setStatus('idle');
            }, 5000);
        }
    }

    /**
     * Update file count
     */
    public setFileCount(count: number): void {
        this.fileCount = count;
        this.updateDisplay();
    }

    /**
     * Update total lines
     */
    public setTotalLines(lines: number): void {
        this.totalLines = lines;
        this.updateDisplay();
    }

    /**
     * Set current file being generated
     */
    public setCurrentFile(file: string | undefined): void {
        this.currentFile = file;
        this.updateDisplay();
    }

    /**
     * Update all metrics
     */
    public updateMetrics(
        fileCount: number,
        totalLines: number,
        currentFile?: string
    ): void {
        this.fileCount = fileCount;
        this.totalLines = totalLines;
        this.currentFile = currentFile;
        this.updateDisplay();
    }

    /**
     * Reset to idle state
     */
    public reset(): void {
        this.currentStatus = 'idle';
        this.fileCount = 0;
        this.totalLines = 0;
        this.currentFile = undefined;
        this.clearHideTimeout();
        this.updateDisplay();
    }

    /**
     * Show the status bar item
     */
    public show(): void {
        this.statusBarItem.show();
    }

    /**
     * Hide the status bar item
     */
    public hide(): void {
        this.statusBarItem.hide();
    }

    /**
     * Dispose the status bar item
     */
    public dispose(): void {
        this.clearHideTimeout();
        this.statusBarItem.dispose();
        StreamingStatusBar.instance = undefined;
        Logger.info('StreamingStatusBar disposed');
    }

    /**
     * Update the display
     */
    private updateDisplay(): void {
        const config = STATUS_CONFIGS[this.currentStatus];

        // Build text
        let text = `${config.icon} ${config.text}`;

        if (this.currentStatus === 'generating' || this.currentStatus === 'quality_check') {
            if (this.fileCount > 0) {
                text += ` (${this.fileCount} files)`;
            }
        } else if (this.currentStatus === 'completed') {
            text = `${config.icon} ${this.fileCount} files (${this.formatLines(this.totalLines)} lines)`;
        }

        // Build tooltip
        let tooltip = config.tooltip;

        if (this.currentFile && this.currentStatus === 'generating') {
            tooltip += `\n\nCurrently generating: ${this.currentFile}`;
        }

        if (this.fileCount > 0) {
            tooltip += `\n\nFiles: ${this.fileCount}`;
            tooltip += `\nLines: ${this.totalLines.toLocaleString()}`;
        }

        tooltip += '\n\nClick to open Generation Panel';

        // Update status bar
        this.statusBarItem.text = text;
        this.statusBarItem.tooltip = tooltip;
        this.statusBarItem.backgroundColor = config.backgroundColor;

        // Show/hide based on status
        if (this.currentStatus === 'idle') {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * Format line count
     */
    private formatLines(lines: number): string {
        if (lines >= 1000) {
            return `${(lines / 1000).toFixed(1)}K`;
        }
        return lines.toString();
    }

    /**
     * Clear hide timeout
     */
    private clearHideTimeout(): void {
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = undefined;
        }
    }
}

/**
 * Get StreamingStatusBar singleton
 */
export function getStreamingStatusBar(): StreamingStatusBar {
    return StreamingStatusBar.getInstance();
}

/**
 * Register streaming status bar
 */
export function registerStreamingStatusBar(
    context: vscode.ExtensionContext
): StreamingStatusBar {
    const statusBar = StreamingStatusBar.getInstance();
    context.subscriptions.push(statusBar);
    return statusBar;
}
