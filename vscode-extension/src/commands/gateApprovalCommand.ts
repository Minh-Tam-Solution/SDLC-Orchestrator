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
import { ApiClient, ApiError } from '../services/apiClient';
import { Logger } from '../utils/logger';

/**
 * Register gate approval and rejection commands.
 */
export function registerGateApprovalCommands(
    context: vscode.ExtensionContext,
    apiClient: ApiClient
): void {
    const approveCmd = vscode.commands.registerCommand(
        'sdlc.approveGate',
        async (gateItem?: { gateId?: string }) => {
            await executeApproveGate(apiClient, gateItem?.gateId);
        }
    );

    const rejectCmd = vscode.commands.registerCommand(
        'sdlc.rejectGate',
        async (gateItem?: { gateId?: string }) => {
            await executeRejectGate(apiClient, gateItem?.gateId);
        }
    );

    context.subscriptions.push(approveCmd, rejectCmd);
    Logger.info('Gate approval/rejection commands registered (Sprint 173)');
}

/**
 * Execute gate approval with server-driven permission check.
 */
async function executeApproveGate(
    apiClient: ApiClient,
    gateId?: string
): Promise<void> {
    try {
        // Get gate ID from argument or prompt
        const resolvedGateId = gateId || await promptForGateId();
        if (!resolvedGateId) {
            return;
        }

        // Server-driven permission check (SDLC Expert v2 — no client-side logic)
        const actions = await apiClient.getGateActions(resolvedGateId);

        if (!actions.actions.can_approve) {
            const reason = actions.reasons.can_approve || 'Action not permitted';
            vscode.window.showWarningMessage(`Cannot approve gate: ${reason}`);
            return;
        }

        // Prompt for mandatory comment
        const comment = await vscode.window.showInputBox({
            prompt: 'Approval comment (required)',
            placeHolder: 'Enter reason for approval...',
            validateInput: (value) => {
                if (!value || !value.trim()) {
                    return 'Comment is required for approval';
                }
                return undefined;
            },
        });

        if (!comment) {
            return;
        }

        // Execute with progress indicator
        const result = await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Approving gate...',
                cancellable: false,
            },
            async () => {
                return apiClient.approveGate(resolvedGateId, comment.trim());
            }
        );

        vscode.window.showInformationMessage(
            `Gate approved: ${result.gate_name || resolvedGateId}`
        );

        // Refresh gate status view
        await vscode.commands.executeCommand('sdlc.refreshGates');

    } catch (error) {
        handleGateError(error, 'approve');
    }
}

/**
 * Execute gate rejection with server-driven permission check.
 */
async function executeRejectGate(
    apiClient: ApiClient,
    gateId?: string
): Promise<void> {
    try {
        // Get gate ID from argument or prompt
        const resolvedGateId = gateId || await promptForGateId();
        if (!resolvedGateId) {
            return;
        }

        // Server-driven permission check
        const actions = await apiClient.getGateActions(resolvedGateId);

        if (!actions.actions.can_reject) {
            const reason = actions.reasons.can_reject || 'Action not permitted';
            vscode.window.showWarningMessage(`Cannot reject gate: ${reason}`);
            return;
        }

        // Prompt for mandatory rejection comment (supports multiline)
        const comment = await vscode.window.showInputBox({
            prompt: 'Rejection reason (required)',
            placeHolder: 'Enter detailed reason for rejection...',
            validateInput: (value) => {
                if (!value || !value.trim()) {
                    return 'Comment is required for rejection';
                }
                return undefined;
            },
        });

        if (!comment) {
            return;
        }

        // Execute with progress indicator
        const result = await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Rejecting gate...',
                cancellable: false,
            },
            async () => {
                return apiClient.rejectGate(resolvedGateId, comment.trim());
            }
        );

        vscode.window.showWarningMessage(
            `Gate rejected: ${result.gate_name || resolvedGateId}`
        );

        // Refresh gate status view
        await vscode.commands.executeCommand('sdlc.refreshGates');

    } catch (error) {
        handleGateError(error, 'reject');
    }
}

/**
 * Prompt user for gate ID if not provided via context menu.
 */
async function promptForGateId(): Promise<string | undefined> {
    return vscode.window.showInputBox({
        prompt: 'Enter Gate ID',
        placeHolder: 'Gate UUID...',
        validateInput: (value) => {
            if (!value || !value.trim()) {
                return 'Gate ID is required';
            }
            return undefined;
        },
    });
}

/**
 * Handle gate operation errors with auth-aware messaging.
 */
function handleGateError(error: unknown, action: string): void {
    const apiError = error as ApiError;

    if (apiError?.statusCode === 403) {
        vscode.window.showErrorMessage(
            'Missing scope: governance:approve. Please re-login with full permissions.',
            'Re-login'
        ).then(choice => {
            if (choice === 'Re-login') {
                vscode.commands.executeCommand('sdlc.login');
            }
        });
        return;
    }

    if (apiError?.statusCode === 409) {
        vscode.window.showWarningMessage(
            `Cannot ${action}: ${apiError.message || 'State conflict'}`
        );
        return;
    }

    if (apiError?.statusCode === 401) {
        vscode.window.showErrorMessage(
            'Authentication expired. Please log in again.',
            'Login'
        ).then(choice => {
            if (choice === 'Login') {
                vscode.commands.executeCommand('sdlc.login');
            }
        });
        return;
    }

    const message = error instanceof Error ? error.message : String(error);
    Logger.error(`Gate ${action} error: ${message}`);
    vscode.window.showErrorMessage(`Failed to ${action} gate: ${message}`);
}
