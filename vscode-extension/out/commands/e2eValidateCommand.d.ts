/**
 * E2E API Testing Validation Command for SDLC Orchestrator VS Code Extension
 *
 * Sprint 139 - Task 1: E2E Validate Command
 * Implements RFC-SDLC-602 E2E API Testing validation in IDE.
 *
 * Features:
 * - Validate E2E testing compliance (SDLC 6.0.5)
 * - Calls real CLI `sdlcctl e2e validate` (Zero Mock Policy)
 * - Display results in Output channel and Problems panel
 * - Optional --init for folder structure setup
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
 * Register E2E validation commands
 *
 * @param context - VS Code extension context
 */
export declare function registerE2EValidateCommand(context: vscode.ExtensionContext): void;
//# sourceMappingURL=e2eValidateCommand.d.ts.map