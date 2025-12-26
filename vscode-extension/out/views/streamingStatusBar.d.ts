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
/**
 * Generation status types
 */
export type GenerationStatus = 'idle' | 'connecting' | 'generating' | 'quality_check' | 'completed' | 'failed' | 'cancelled';
/**
 * Streaming Status Bar Manager
 *
 * Manages the status bar item for code generation progress.
 */
export declare class StreamingStatusBar implements vscode.Disposable {
    private static instance;
    private readonly statusBarItem;
    private currentStatus;
    private fileCount;
    private totalLines;
    private currentFile;
    private hideTimeout;
    private constructor();
    /**
     * Get singleton instance
     */
    static getInstance(): StreamingStatusBar;
    /**
     * Update the status
     */
    setStatus(status: GenerationStatus): void;
    /**
     * Update file count
     */
    setFileCount(count: number): void;
    /**
     * Update total lines
     */
    setTotalLines(lines: number): void;
    /**
     * Set current file being generated
     */
    setCurrentFile(file: string | undefined): void;
    /**
     * Update all metrics
     */
    updateMetrics(fileCount: number, totalLines: number, currentFile?: string): void;
    /**
     * Reset to idle state
     */
    reset(): void;
    /**
     * Show the status bar item
     */
    show(): void;
    /**
     * Hide the status bar item
     */
    hide(): void;
    /**
     * Dispose the status bar item
     */
    dispose(): void;
    /**
     * Update the display
     */
    private updateDisplay;
    /**
     * Format line count
     */
    private formatLines;
    /**
     * Clear hide timeout
     */
    private clearHideTimeout;
}
/**
 * Get StreamingStatusBar singleton
 */
export declare function getStreamingStatusBar(): StreamingStatusBar;
/**
 * Register streaming status bar
 */
export declare function registerStreamingStatusBar(context: vscode.ExtensionContext): StreamingStatusBar;
//# sourceMappingURL=streamingStatusBar.d.ts.map