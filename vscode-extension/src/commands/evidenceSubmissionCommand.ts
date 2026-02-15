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
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { ApiClient, ApiError } from '../services/apiClient';
import { Logger } from '../utils/logger';

const EVIDENCE_TYPES = [
    { label: 'test-results', description: 'Test execution results (JUnit, pytest, etc.)' },
    { label: 'api-docs', description: 'API documentation / OpenAPI specs' },
    { label: 'design-doc', description: 'Design documents / ADRs' },
    { label: 'security-scan', description: 'Security scan results (Semgrep, SAST)' },
    { label: 'code-review', description: 'Code review artifacts' },
    { label: 'manual', description: 'Manual / other evidence' },
];

/**
 * Register evidence submission command.
 */
export function registerEvidenceSubmissionCommand(
    context: vscode.ExtensionContext,
    apiClient: ApiClient
): void {
    const command = vscode.commands.registerCommand(
        'sdlc.submitEvidence',
        async (gateItem?: { gateId?: string }) => {
            await executeSubmitEvidence(apiClient, gateItem?.gateId);
        }
    );

    context.subscriptions.push(command);
    Logger.info('Evidence submission command registered (Sprint 173)');
}

/**
 * Execute evidence file upload with SHA256 verification.
 */
async function executeSubmitEvidence(
    apiClient: ApiClient,
    gateId?: string
): Promise<void> {
    try {
        // Get gate ID from argument or prompt
        const resolvedGateId = gateId || await vscode.window.showInputBox({
            prompt: 'Enter Gate ID to attach evidence to',
            placeHolder: 'Gate UUID...',
            validateInput: (value) => {
                if (!value || !value.trim()) {
                    return 'Gate ID is required';
                }
                return undefined;
            },
        });

        if (!resolvedGateId) {
            return;
        }

        // Check server-driven actions
        const actions = await apiClient.getGateActions(resolvedGateId);
        if (!actions.actions.can_upload_evidence) {
            const reason = actions.reasons.can_upload_evidence || 'Evidence upload not permitted';
            vscode.window.showWarningMessage(`Cannot upload evidence: ${reason}`);
            return;
        }

        // Select evidence type
        const selectedType = await vscode.window.showQuickPick(EVIDENCE_TYPES, {
            placeHolder: 'Select evidence type',
            title: 'Evidence Type',
        });

        if (!selectedType) {
            return;
        }

        // Select file(s) via dialog
        const fileUris = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: true,
            title: 'Select Evidence File(s)',
            filters: {
                'All Files': ['*'],
                'JSON': ['json'],
                'Markdown': ['md'],
                'PDF': ['pdf'],
                'XML': ['xml'],
                'HTML': ['html'],
            },
        });

        if (!fileUris || fileUris.length === 0) {
            return;
        }

        // Upload each file with progress
        const results: Array<{ name: string; success: boolean; message: string }> = [];

        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Uploading evidence',
                cancellable: false,
            },
            async (progress) => {
                for (let i = 0; i < fileUris.length; i++) {
                    const fileUri = fileUris[i]!;
                    const fileName = path.basename(fileUri.fsPath);

                    progress.report({
                        message: `${fileName} (${i + 1}/${fileUris.length})`,
                        increment: (100 / fileUris.length),
                    });

                    try {
                        const result = await uploadSingleFile(
                            apiClient,
                            resolvedGateId,
                            selectedType.label,
                            fileUri.fsPath
                        );

                        results.push({
                            name: fileName,
                            success: true,
                            message: result.integrity_verified
                                ? 'Uploaded (integrity verified)'
                                : 'Uploaded (integrity unverified)',
                        });

                        if (result.gate_status_changed) {
                            Logger.info(
                                `Gate ${resolvedGateId} status changed to EVALUATED_STALE after evidence upload`
                            );
                        }
                    } catch (uploadError) {
                        const message = uploadError instanceof Error
                            ? uploadError.message
                            : String(uploadError);
                        results.push({ name: fileName, success: false, message });
                    }
                }
            }
        );

        // Show results
        const successCount = results.filter(r => r.success).length;
        const failCount = results.filter(r => !r.success).length;

        if (failCount === 0) {
            vscode.window.showInformationMessage(
                `${successCount} evidence file(s) uploaded successfully.`
            );
        } else if (successCount === 0) {
            vscode.window.showErrorMessage(
                `All ${failCount} file(s) failed to upload.`
            );
        } else {
            vscode.window.showWarningMessage(
                `${successCount} uploaded, ${failCount} failed.`
            );
        }

        // Refresh gate status view
        await vscode.commands.executeCommand('sdlc.refreshGates');

    } catch (error) {
        const apiError = error as ApiError;

        if (apiError?.statusCode === 403) {
            vscode.window.showErrorMessage(
                'Missing scope: governance:write. Please re-login with full permissions.',
                'Re-login'
            ).then(choice => {
                if (choice === 'Re-login') {
                    vscode.commands.executeCommand('sdlc.login');
                }
            });
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
        Logger.error(`Evidence submission error: ${message}`);
        vscode.window.showErrorMessage(`Failed to submit evidence: ${message}`);
    }
}

/**
 * Upload a single evidence file with SHA256 hash computation.
 */
async function uploadSingleFile(
    apiClient: ApiClient,
    gateId: string,
    evidenceType: string,
    filePath: string
): Promise<{
    evidence_id: string;
    integrity_verified: boolean;
    gate_status_changed: boolean;
}> {
    // Read file
    const fileBuffer = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);
    const fileSize = fileBuffer.length;

    // Compute SHA256 client-side
    const hash = crypto.createHash('sha256');
    hash.update(fileBuffer);
    const sha256Client = hash.digest('hex');

    // Detect MIME type
    const ext = path.extname(filePath).toLowerCase();
    const mimeMap: Record<string, string> = {
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.md': 'text/markdown',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.yaml': 'application/x-yaml',
        '.yml': 'application/x-yaml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
    };
    const mimeType = mimeMap[ext] || 'application/octet-stream';

    Logger.info(
        `Uploading evidence: ${fileName} (${fileSize} bytes, SHA256: ${sha256Client.substring(0, 16)}...)`
    );

    return apiClient.submitEvidence(gateId, evidenceType, {
        buffer: fileBuffer,
        name: fileName,
        mimeType,
        sha256Client,
        sizeBytes: fileSize,
    });
}
