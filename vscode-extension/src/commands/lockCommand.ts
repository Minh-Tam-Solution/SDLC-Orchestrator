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
import { Logger } from '../utils/logger';
import { handleError } from '../utils/errors';
import type { CodegenApiService } from '../services/codegenApi';

/**
 * Register the lock command
 */
export function registerLockCommand(
    context: vscode.ExtensionContext,
    codegenApi: CodegenApiService
): void {
    const lockCommand = vscode.commands.registerCommand(
        'sdlc.lock',
        async (sessionId?: string) => {
            await executeLockCommand(codegenApi, sessionId);
        }
    );

    const unlockCommand = vscode.commands.registerCommand(
        'sdlc.unlock',
        async (sessionId?: string) => {
            await executeUnlockCommand(codegenApi, sessionId);
        }
    );

    context.subscriptions.push(lockCommand, unlockCommand);
    Logger.info('Lock/Unlock commands registered');
}

/**
 * Execute the lock command
 */
async function executeLockCommand(
    codegenApi: CodegenApiService,
    providedSessionId?: string
): Promise<void> {
    try {
        // Get session ID if not provided
        const sessionId = providedSessionId || await getSessionId(codegenApi);
        if (!sessionId) {
            return; // User cancelled
        }

        // Check current lock status
        const status = await codegenApi.getContractStatus(sessionId);

        if (status.is_locked) {
            void vscode.window.showWarningMessage(
                `Contract is already locked since ${formatDate(status.locked_at)} by ${status.locked_by}`
            );
            return;
        }

        // Ask for lock reason
        const reason = await vscode.window.showInputBox({
            prompt: 'Reason for locking (optional)',
            placeHolder: 'e.g., Ready for production deployment',
        });

        // Lock the contract
        const result = await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Locking contract...',
                cancellable: false,
            },
            async () => {
                return await codegenApi.lockContract(sessionId, reason);
            }
        );

        if (result.success) {
            const action = await vscode.window.showInformationMessage(
                `🔒 Contract locked successfully!\n\nSpec Hash: ${result.spec_hash.substring(0, 16)}...\nVersion: ${result.version}`,
                'Copy Hash',
                'View Status'
            );

            if (action === 'Copy Hash') {
                await vscode.env.clipboard.writeText(result.spec_hash);
                void vscode.window.showInformationMessage('Hash copied to clipboard');
            } else if (action === 'View Status') {
                await showLockStatus(codegenApi, sessionId);
            }
        } else {
            void vscode.window.showErrorMessage(`Failed to lock: ${result.message}`);
        }

    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Execute the unlock command
 */
async function executeUnlockCommand(
    codegenApi: CodegenApiService,
    providedSessionId?: string
): Promise<void> {
    try {
        // Get session ID if not provided
        const sessionId = providedSessionId || await getSessionId(codegenApi);
        if (!sessionId) {
            return; // User cancelled
        }

        // Check current lock status
        const status = await codegenApi.getContractStatus(sessionId);

        if (!status.is_locked) {
            void vscode.window.showInformationMessage('Contract is not locked');
            return;
        }

        // Confirm unlock
        const confirm = await vscode.window.showWarningMessage(
            `Are you sure you want to unlock this contract?\n\nLocked by: ${status.locked_by}\nLocked at: ${formatDate(status.locked_at)}\nSpec Hash: ${status.spec_hash?.substring(0, 16)}...`,
            { modal: true },
            'Unlock',
            'Cancel'
        );

        if (confirm !== 'Unlock') {
            return;
        }

        // Ask for unlock reason
        const reasonOptions = [
            { label: 'Need to modify specification', reason: 'modification_needed' as const },
            { label: 'Generation failed, need to retry', reason: 'generation_failed' as const },
        ];

        const selectedReason = await vscode.window.showQuickPick(reasonOptions, {
            placeHolder: 'Select reason for unlocking',
            title: 'Unlock Reason',
        });

        if (!selectedReason) {
            return; // User cancelled
        }

        // Unlock the contract
        const result = await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Unlocking contract...',
                cancellable: false,
            },
            async () => {
                return await codegenApi.unlockContract(sessionId, selectedReason.reason);
            }
        );

        if (result.success) {
            void vscode.window.showInformationMessage(
                `🔓 Contract unlocked successfully!\n\n${result.message}`
            );
        } else {
            void vscode.window.showErrorMessage(`Failed to unlock: ${result.message}`);
        }

    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Register additional lock-related commands
 */
export function registerLockStatusCommand(
    context: vscode.ExtensionContext,
    codegenApi: CodegenApiService
): void {
    // Status command
    const statusCommand = vscode.commands.registerCommand(
        'sdlc.lockStatus',
        async (sessionId?: string) => {
            const id = sessionId || await getSessionId(codegenApi);
            if (id) {
                await showLockStatus(codegenApi, id);
            }
        }
    );

    // Verify hash command
    const verifyCommand = vscode.commands.registerCommand(
        'sdlc.verifyHash',
        async (sessionId?: string) => {
            await executeVerifyHashCommand(codegenApi, sessionId);
        }
    );

    context.subscriptions.push(statusCommand, verifyCommand);
    Logger.info('Lock status commands registered');
}

/**
 * Get session ID from user
 */
async function getSessionId(codegenApi: CodegenApiService): Promise<string | undefined> {
    // Try to get current project's sessions
    const config = vscode.workspace.getConfiguration('sdlc');
    const projectId = config.get<string>('defaultProjectId');

    if (projectId) {
        try {
            const sessions = await codegenApi.listSessions(projectId);

            if (sessions.length === 0) {
                void vscode.window.showInformationMessage('No onboarding sessions found for this project');
                return undefined;
            }

            const firstSession = sessions[0];
            if (sessions.length === 1 && firstSession) {
                return firstSession.id;
            }

            // Let user pick a session
            const items = sessions.map(s => ({
                label: s.id.substring(0, 8),
                description: s.status,
                detail: `Created: ${formatDate(s.created_at)} | ${s.is_locked ? '🔒 Locked' : '🔓 Unlocked'}`,
                sessionId: s.id,
            } as const));

            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select an onboarding session',
            });

            return selected?.sessionId;
        } catch (error) {
            Logger.warn(`Failed to list sessions: ${error}`);
        }
    }

    // Fallback to manual input
    const sessionId = await vscode.window.showInputBox({
        prompt: 'Enter the onboarding session ID',
        placeHolder: 'e.g., abc12345-1234-1234-1234-123456789abc',
        validateInput: (value) => {
            if (!value || value.length < 8) {
                return 'Please enter a valid session ID';
            }
            return null;
        },
    });

    return sessionId;
}

/**
 * Show lock status in a webview or quick pick
 */
async function showLockStatus(
    codegenApi: CodegenApiService,
    sessionId: string
): Promise<void> {
    try {
        const status = await codegenApi.getContractStatus(sessionId);

        const statusItems: vscode.QuickPickItem[] = [
            {
                label: `$(${status.is_locked ? 'lock' : 'unlock'}) Status`,
                description: status.is_locked ? 'Locked' : 'Unlocked',
            },
            {
                label: '$(key) Session ID',
                description: sessionId,
            },
        ];

        if (status.is_locked) {
            statusItems.push(
                {
                    label: '$(calendar) Locked At',
                    description: formatDate(status.locked_at),
                },
                {
                    label: '$(person) Locked By',
                    description: status.locked_by || 'Unknown',
                },
                {
                    label: '$(file-binary) Spec Hash',
                    description: status.spec_hash?.substring(0, 32) + '...',
                },
                {
                    label: '$(versions) Version',
                    description: String(status.version),
                }
            );
        }

        const selected = await vscode.window.showQuickPick(statusItems, {
            title: 'Contract Lock Status',
            placeHolder: 'Select an item to copy its value',
        });

        if (selected && selected.description) {
            await vscode.env.clipboard.writeText(selected.description);
            void vscode.window.showInformationMessage('Copied to clipboard');
        }

    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Execute verify hash command
 */
async function executeVerifyHashCommand(
    codegenApi: CodegenApiService,
    providedSessionId?: string
): Promise<void> {
    try {
        // Get session ID if not provided
        const sessionId = providedSessionId || await getSessionId(codegenApi);
        if (!sessionId) {
            return;
        }

        // Get expected hash from user
        const expectedHash = await vscode.window.showInputBox({
            prompt: 'Enter the expected spec hash to verify',
            placeHolder: 'SHA256 hash (64 characters)',
            validateInput: (value) => {
                if (!value || value.length !== 64) {
                    return 'Please enter a valid SHA256 hash (64 characters)';
                }
                if (!/^[a-fA-F0-9]+$/.test(value)) {
                    return 'Hash must contain only hexadecimal characters';
                }
                return null;
            },
        });

        if (!expectedHash) {
            return;
        }

        // Verify hash
        const result = await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Verifying hash...',
                cancellable: false,
            },
            async () => {
                return await codegenApi.verifyContractHash(sessionId, expectedHash);
            }
        );

        if (result.match) {
            void vscode.window.showInformationMessage(
                '✅ Hash verification successful! The contract specification has not been modified.'
            );
        } else {
            void vscode.window.showWarningMessage(
                `❌ Hash mismatch!\n\nExpected: ${expectedHash.substring(0, 16)}...\nCurrent: ${result.current_hash.substring(0, 16)}...\n\nThe contract specification has been modified.`
            );
        }

    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Format date string for display
 */
function formatDate(dateString?: string): string {
    if (!dateString) {
        return 'Unknown';
    }
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch {
        return dateString;
    }
}
