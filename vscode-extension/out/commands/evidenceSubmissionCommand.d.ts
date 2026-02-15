/**
 * Evidence Submission Command
 * Sprint 173 - Governance Loop (ADR-053)
 *
 * Upload evidence files to a gate with client-side SHA256 computation.
 * Server re-verifies hash on upload. If gate is EVALUATED, status
 * changes to EVALUATED_STALE (forces re-evaluation).
 *
 * Commands:
 * - sdlc.submitEvidence: Upload evidence file to gate
 */
import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
/**
 * Register evidence submission command.
 */
export declare function registerEvidenceSubmissionCommand(context: vscode.ExtensionContext, apiClient: ApiClient): void;
//# sourceMappingURL=evidenceSubmissionCommand.d.ts.map