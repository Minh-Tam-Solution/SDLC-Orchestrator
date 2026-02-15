/**
 * E2E Cross-Reference Validation Command for SDLC Orchestrator VS Code Extension
 *
 * Sprint 139 - Task 2: Cross-Reference Command
 * Validates Stage 03 ↔ Stage 05 bidirectional cross-references.
 *
 * Features:
 * - Validate API documentation links to test reports
 * - Validate test reports link back to API docs
 * - Check SSOT compliance (no duplicate openapi.json)
 * - Display results in tree view and output channel
 * - Optional --fix to generate test stubs for uncovered endpoints
 *
 * Reference:
 * - RFC-SDLC-602-E2E-API-TESTING
 * - SDLC Framework 6.0.5
 * - Skill: e2e-api-testing (6-phase workflow)
 *
 * CTO Requirements (Non-Negotiable):
 * - No placeholder code
 * - Real CLI integration (not mocked data)
 * - Error handling required
 * - Dogfooding mandatory
 *
 * @version 1.0.0
 * @since Sprint 139
 */
import * as vscode from 'vscode';
/**
 * Register cross-reference validation commands
 *
 * @param context - VS Code extension context
 */
export declare function registerE2ECrossRefCommand(context: vscode.ExtensionContext): void;
//# sourceMappingURL=e2eCrossRefCommand.d.ts.map