"use strict";
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
exports.registerEvidenceSubmissionCommand = registerEvidenceSubmissionCommand;
const vscode = __importStar(require("vscode"));
const crypto = __importStar(require("crypto"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const logger_1 = require("../utils/logger");
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
function registerEvidenceSubmissionCommand(context, apiClient) {
    const command = vscode.commands.registerCommand('sdlc.submitEvidence', async (gateItem) => {
        await executeSubmitEvidence(apiClient, gateItem?.gateId);
    });
    context.subscriptions.push(command);
    logger_1.Logger.info('Evidence submission command registered (Sprint 173)');
}
/**
 * Execute evidence file upload with SHA256 verification.
 */
async function executeSubmitEvidence(apiClient, gateId) {
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
        const results = [];
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Uploading evidence',
            cancellable: false,
        }, async (progress) => {
            for (let i = 0; i < fileUris.length; i++) {
                const fileUri = fileUris[i];
                const fileName = path.basename(fileUri.fsPath);
                progress.report({
                    message: `${fileName} (${i + 1}/${fileUris.length})`,
                    increment: (100 / fileUris.length),
                });
                try {
                    const result = await uploadSingleFile(apiClient, resolvedGateId, selectedType.label, fileUri.fsPath);
                    results.push({
                        name: fileName,
                        success: true,
                        message: result.integrity_verified
                            ? 'Uploaded (integrity verified)'
                            : 'Uploaded (integrity unverified)',
                    });
                    if (result.gate_status_changed) {
                        logger_1.Logger.info(`Gate ${resolvedGateId} status changed to EVALUATED_STALE after evidence upload`);
                    }
                }
                catch (uploadError) {
                    const message = uploadError instanceof Error
                        ? uploadError.message
                        : String(uploadError);
                    results.push({ name: fileName, success: false, message });
                }
            }
        });
        // Show results
        const successCount = results.filter(r => r.success).length;
        const failCount = results.filter(r => !r.success).length;
        if (failCount === 0) {
            vscode.window.showInformationMessage(`${successCount} evidence file(s) uploaded successfully.`);
        }
        else if (successCount === 0) {
            vscode.window.showErrorMessage(`All ${failCount} file(s) failed to upload.`);
        }
        else {
            vscode.window.showWarningMessage(`${successCount} uploaded, ${failCount} failed.`);
        }
        // Refresh gate status view
        await vscode.commands.executeCommand('sdlc.refreshGates');
    }
    catch (error) {
        const apiError = error;
        if (apiError?.statusCode === 403) {
            vscode.window.showErrorMessage('Missing scope: governance:write. Please re-login with full permissions.', 'Re-login').then(choice => {
                if (choice === 'Re-login') {
                    vscode.commands.executeCommand('sdlc.login');
                }
            });
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
        logger_1.Logger.error(`Evidence submission error: ${message}`);
        vscode.window.showErrorMessage(`Failed to submit evidence: ${message}`);
    }
}
/**
 * Upload a single evidence file with SHA256 hash computation.
 */
async function uploadSingleFile(apiClient, gateId, evidenceType, filePath) {
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
    const mimeMap = {
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
    logger_1.Logger.info(`Uploading evidence: ${fileName} (${fileSize} bytes, SHA256: ${sha256Client.substring(0, 16)}...)`);
    return apiClient.submitEvidence(gateId, evidenceType, {
        buffer: fileBuffer,
        name: fileName,
        mimeType,
        sha256Client,
        sizeBytes: fileSize,
    });
}
//# sourceMappingURL=evidenceSubmissionCommand.js.map