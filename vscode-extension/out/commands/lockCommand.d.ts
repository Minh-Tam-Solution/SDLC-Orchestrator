/**
 * Lock/Unlock Commands - Contract Specification Immutability
 *
 * Implements the sdlc.lock and sdlc.unlock commands for
 * managing contract specification immutability.
 *
 * Sprint 53 Day 1 - Lock Command Implementation
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import type { CodegenApiService } from '../services/codegenApi';
/**
 * Register the lock command
 */
export declare function registerLockCommand(context: vscode.ExtensionContext, codegenApi: CodegenApiService): void;
/**
 * Register additional lock-related commands
 */
export declare function registerLockStatusCommand(context: vscode.ExtensionContext, codegenApi: CodegenApiService): void;
//# sourceMappingURL=lockCommand.d.ts.map