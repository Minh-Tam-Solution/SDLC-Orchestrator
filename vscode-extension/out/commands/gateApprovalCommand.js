"use strict";
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
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerGateApprovalCommands = registerGateApprovalCommands;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
/**
 * Register gate approval and rejection commands.
 */
function registerGateApprovalCommands(context, apiClient) {
    const approveCmd = vscode.commands.registerCommand('sdlc.approveGate', async (gateItem) => {
        await executeApproveGate(apiClient, gateItem?.gateId);
    });
    const rejectCmd = vscode.commands.registerCommand('sdlc.rejectGate', async (gateItem) => {
        await executeRejectGate(apiClient, gateItem?.gateId);
    });
    context.subscriptions.push(approveCmd, rejectCmd);
    logger_1.Logger.info('Gate approval/rejection commands registered (Sprint 173)');
}
/**
 * Execute gate approval with server-driven permission check.
 */
async function executeApproveGate(apiClient, gateId) {
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
        const result = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Approving gate...',
            cancellable: false,
        }, async () => {
            return apiClient.approveGate(resolvedGateId, comment.trim());
        });
        vscode.window.showInformationMessage(`Gate approved: ${result.gate_name || resolvedGateId}`);
        // Refresh gate status view
        await vscode.commands.executeCommand('sdlc.refreshGates');
    }
    catch (error) {
        handleGateError(error, 'approve');
    }
}
/**
 * Execute gate rejection with server-driven permission check.
 */
async function executeRejectGate(apiClient, gateId) {
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
        const result = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Rejecting gate...',
            cancellable: false,
        }, async () => {
            return apiClient.rejectGate(resolvedGateId, comment.trim());
        });
        vscode.window.showWarningMessage(`Gate rejected: ${result.gate_name || resolvedGateId}`);
        // Refresh gate status view
        await vscode.commands.executeCommand('sdlc.refreshGates');
    }
    catch (error) {
        handleGateError(error, 'reject');
    }
}
/**
 * Prompt user for gate ID if not provided via context menu.
 */
async function promptForGateId() {
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
function handleGateError(error, action) {
    const apiError = error;
    if (apiError?.statusCode === 403) {
        vscode.window.showErrorMessage('Missing scope: governance:approve. Please re-login with full permissions.', 'Re-login').then(choice => {
            if (choice === 'Re-login') {
                vscode.commands.executeCommand('sdlc.login');
            }
        });
        return;
    }
    if (apiError?.statusCode === 409) {
        vscode.window.showWarningMessage(`Cannot ${action}: ${apiError.message || 'State conflict'}`);
        return;
    }
    if (apiError?.statusCode === 401) {
        vscode.window.showErrorMessage('Authentication expired. Please log in again.', 'Login').then(choice => {
            if (choice === 'Login') {
                vscode.commands.executeCommand('sdlc.login');
            }
        });
        return;
    }
    const message = error instanceof Error ? error.message : String(error);
    logger_1.Logger.error(`Gate ${action} error: ${message}`);
    vscode.window.showErrorMessage(`Failed to ${action} gate: ${message}`);
}
//# sourceMappingURL=gateApprovalCommand.js.map