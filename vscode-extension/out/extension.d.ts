/**
 * SDLC Orchestrator VS Code Extension
 *
 * Main entry point for the VS Code extension providing:
 * - Gate status sidebar (G0-G5 progress monitoring)
 * - Inline AI chat (Copilot-style @gate commands)
 * - Compliance violation tracking
 * - App Builder with code generation (Sprint 53)
 * - Integration with SDLC Orchestrator backend
 *
 * Sprint 53 - App Builder + Contract Lock
 * @version 0.2.0
 */
import * as vscode from 'vscode';
/**
 * Activates the SDLC Orchestrator extension
 *
 * This function is called when the extension is activated, which happens
 * on VS Code startup (onStartupFinished activation event).
 *
 * @param context - VS Code extension context for managing subscriptions
 */
export declare function activate(context: vscode.ExtensionContext): Promise<void>;
/**
 * Deactivates the extension and cleans up resources
 */
export declare function deactivate(): void;
//# sourceMappingURL=extension.d.ts.map