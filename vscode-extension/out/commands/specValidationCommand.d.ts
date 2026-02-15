/**
 * Specification Validation Command for SDLC Orchestrator VS Code Extension
 *
 * Sprint 126 - S126-06: Add spec validation to Extension
 * Implements SDLC 6.0.5 SPEC-0002 specification validation in IDE.
 *
 * Features:
 * - Validate current file against SPEC-0002 standard
 * - YAML frontmatter validation
 * - BDD requirements format checking
 * - Tier-specific section validation
 * - Cross-reference validation
 * - Results displayed in Problems panel and Output channel
 *
 * @version 1.0.0
 * @since Sprint 126
 */
import * as vscode from 'vscode';
import type { CodegenApiService } from '../services/codegenApi';
/**
 * Register spec validation commands
 *
 * @param context - VS Code extension context
 * @param codegenApi - CodegenApiService instance
 */
export declare function registerSpecValidationCommand(context: vscode.ExtensionContext, codegenApi: CodegenApiService): void;
//# sourceMappingURL=specValidationCommand.d.ts.map