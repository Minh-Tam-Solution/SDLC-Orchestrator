/**
 * Gate Approval & Rejection Commands
 * Sprint 173 - Governance Loop (ADR-053)
 *
 * Server-driven actions: All permission checks via GET /gates/{id}/actions.
 * No client-side permission computation.
 *
 * Commands:
 * - sdlc.approveGate: Approve a submitted gate
 * - sdlc.rejectGate: Reject a submitted gate
 */
import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
/**
 * Register gate approval and rejection commands.
 */
export declare function registerGateApprovalCommands(context: vscode.ExtensionContext, apiClient: ApiClient): void;
//# sourceMappingURL=gateApprovalCommand.d.ts.map