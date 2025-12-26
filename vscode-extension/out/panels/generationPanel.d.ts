/**
 * Generation Panel - Real-time Code Generation View
 *
 * Displays live streaming progress of code generation with:
 * - Real-time file tree updates
 * - Quality gate status
 * - Progress indicators
 * - Error display with retry options
 *
 * Sprint 53 Day 3 - Streaming Integration
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import type { CodegenApiService } from '../services/codegenApi';
import type { GeneratedFile, QualityGateResult, AppBlueprint } from '../types/codegen';
/**
 * Generation state
 */
interface GenerationState {
    sessionId: string;
    status: 'idle' | 'generating' | 'quality_check' | 'completed' | 'failed' | 'cancelled';
    startedAt: Date;
    blueprint: AppBlueprint;
    files: GeneratedFile[];
    qualityGates: QualityGateResult[];
    currentFile?: string;
    progress: number;
    totalFiles: number;
    totalLines: number;
    errorMessage?: string;
    recoveryId?: string;
}
/**
 * Generation Panel Manager
 *
 * Manages real-time code generation display with SSE streaming.
 */
export declare class GenerationPanel {
    private readonly codegenApi;
    static currentPanel: GenerationPanel | undefined;
    private static readonly viewType;
    private readonly _panel;
    private _disposables;
    private _sseClient;
    private _state;
    private _statusBarItem;
    private constructor();
    /**
     * Create or show the generation panel
     */
    static createOrShow(_extensionUri: vscode.Uri, codegenApi: CodegenApiService): GenerationPanel;
    /**
     * Start generation with streaming
     */
    startGeneration(blueprint: AppBlueprint, outputPath: string): Promise<void>;
    /**
     * Resume failed generation
     */
    resumeGeneration(sessionId: string, outputPath: string): Promise<void>;
    /**
     * Cancel current generation
     */
    cancelGeneration(): Promise<void>;
    /**
     * Get current generation state
     */
    getState(): GenerationState | null;
    /**
     * Dispose the panel
     */
    dispose(): void;
    /**
     * Connect to SSE stream
     */
    private _connectToStream;
    /**
     * Write generated files to disk
     */
    private _writeFilesToDisk;
    /**
     * Handle messages from webview
     */
    private _handleMessage;
    /**
     * Send initial state to webview
     */
    private _sendInitialState;
    /**
     * Select output directory
     */
    private _selectOutputDirectory;
    /**
     * Open a file in editor
     */
    private _openFile;
    /**
     * Copy file content to clipboard
     */
    private _copyFileContent;
    /**
     * Update status bar
     */
    private _updateStatusBar;
    /**
     * Post message to webview
     */
    private _postMessage;
    /**
     * Update webview HTML
     */
    private _update;
    /**
     * Get HTML content for webview
     */
    private _getHtmlForWebview;
    /**
     * Generate nonce for CSP
     */
    private _getNonce;
}
/**
 * Register generation panel command
 */
export declare function registerGenerationPanelCommand(context: vscode.ExtensionContext, codegenApi: CodegenApiService): void;
export {};
//# sourceMappingURL=generationPanel.d.ts.map