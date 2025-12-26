"use strict";
/**
 * Resume Command - Resume Failed Generation
 *
 * Implements the sdlc.resume command for resuming
 * failed or interrupted code generation sessions.
 *
 * Sprint 53 Day 1 - Resume Command Implementation
 * @version 1.0.0
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
exports.registerResumeCommand = registerResumeCommand;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const errors_1 = require("../utils/errors");
const sseClient_1 = require("../services/sseClient");
const config_1 = require("../utils/config");
/**
 * Register the resume command
 */
function registerResumeCommand(context, codegenApi) {
    const command = vscode.commands.registerCommand('sdlc.resume', async (sessionId) => {
        await executeResumeCommand(codegenApi, sessionId);
    });
    context.subscriptions.push(command);
    logger_1.Logger.info('Resume command registered');
}
/**
 * Execute the resume command
 */
async function executeResumeCommand(codegenApi, providedSessionId) {
    try {
        // Get session ID if not provided
        const sessionId = providedSessionId || await getFailedSessionId(codegenApi);
        if (!sessionId) {
            return;
        }
        // Get session status to verify it can be resumed
        const session = await codegenApi.getGenerationStatus(sessionId);
        if (session.status === 'completed') {
            void vscode.window.showInformationMessage('This session is already completed. Use Preview to view generated files.');
            return;
        }
        if (session.status === 'generating' || session.status === 'validating') {
            void vscode.window.showWarningMessage('This session is still in progress. Please wait or cancel it first.');
            return;
        }
        // Confirm resume
        const confirm = await vscode.window.showInformationMessage(`Resume generation for session ${sessionId.substring(0, 8)}?\n\nStatus: ${session.status}\nFiles generated: ${session.files?.length || 0}`, { modal: true }, 'Resume', 'Cancel');
        if (confirm !== 'Resume') {
            return;
        }
        // Select output directory
        const outputPath = await selectOutputDirectory();
        if (!outputPath) {
            return;
        }
        // Resume generation with streaming
        await resumeGenerationWithStreaming(codegenApi, sessionId, session, outputPath);
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}
/**
 * Get failed session ID from user
 */
async function getFailedSessionId(codegenApi) {
    const config = vscode.workspace.getConfiguration('sdlc');
    const projectId = config.get('defaultProjectId');
    if (projectId) {
        try {
            const sessions = await codegenApi.listSessions(projectId);
            const failedSessions = sessions.filter(s => s.status === 'failed' || s.status === 'in_progress');
            if (failedSessions.length === 0) {
                void vscode.window.showInformationMessage('No failed or interrupted sessions found');
                return undefined;
            }
            const items = failedSessions.map(s => ({
                label: `${s.id.substring(0, 8)}...`,
                description: s.status,
                detail: `Created: ${formatDate(s.created_at)} | Files: ${s.generated_files?.length || 0}`,
                sessionId: s.id,
            }));
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a session to resume',
            });
            return selected?.sessionId;
        }
        catch (error) {
            logger_1.Logger.warn(`Failed to list sessions: ${error}`);
        }
    }
    // Fallback to manual input
    return await vscode.window.showInputBox({
        prompt: 'Enter the session ID to resume',
        placeHolder: 'e.g., abc12345-1234-1234-1234-123456789abc',
    });
}
/**
 * Select output directory
 */
async function selectOutputDirectory() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const options = {
        canSelectFiles: false,
        canSelectFolders: true,
        canSelectMany: false,
        title: 'Select Output Directory',
        openLabel: 'Select',
    };
    const firstWorkspace = workspaceFolders?.[0];
    if (firstWorkspace) {
        options.defaultUri = firstWorkspace.uri;
    }
    const folderUri = await vscode.window.showOpenDialog(options);
    const selectedFolder = folderUri?.[0];
    if (!selectedFolder) {
        return undefined;
    }
    return selectedFolder.fsPath;
}
/**
 * Resume generation with SSE streaming
 */
async function resumeGenerationWithStreaming(codegenApi, sessionId, previousSession, outputPath) {
    const config = config_1.ConfigManager.getInstance();
    let sseClient = null;
    const existingFiles = previousSession.files || [];
    const newFiles = [];
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: '🔄 Resuming generation...',
        cancellable: true,
    }, async (progressReporter, cancellationToken) => {
        return new Promise(async (resolve, reject) => {
            try {
                // Resume generation
                progressReporter.report({
                    message: `Resuming from ${existingFiles.length} files...`,
                });
                const result = await codegenApi.resumeGeneration(sessionId);
                const newSessionId = result.session_id;
                // Get auth token and create SSE client
                const token = await codegenApi.getAuthToken();
                sseClient = (0, sseClient_1.createCodegenSSEClient)(config.apiUrl, newSessionId, token);
                // Handle cancellation
                cancellationToken.onCancellationRequested(() => {
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    void codegenApi.cancelGeneration(newSessionId);
                    resolve();
                });
                // Set up event handlers
                sseClient.on('file_generating', (event) => {
                    const e = event;
                    progressReporter.report({
                        message: `Generating: ${e.path}`,
                    });
                });
                sseClient.on('file_generated', (event) => {
                    const e = event;
                    const syntaxValid = e.syntax_valid ?? true;
                    newFiles.push({
                        path: e.path,
                        content: e.content,
                        lines: e.lines,
                        language: e.language,
                        syntax_valid: syntaxValid,
                        status: syntaxValid ? 'valid' : 'error',
                    });
                    progressReporter.report({
                        message: `Generated: ${e.path}`,
                        increment: 5,
                    });
                });
                sseClient.on('quality_started', () => {
                    progressReporter.report({
                        message: '🔍 Running quality gates...',
                    });
                });
                sseClient.on('quality_gate', (event) => {
                    const e = event;
                    const icon = e.status === 'passed' ? '✅' : '❌';
                    progressReporter.report({
                        message: `${icon} Gate ${e.gate_number}: ${e.gate_name}`,
                        increment: 10,
                    });
                });
                sseClient.on('completed', async (event) => {
                    const e = event;
                    // Combine existing and new files
                    const allFiles = [...existingFiles, ...newFiles];
                    // Write all files to disk
                    await writeGeneratedFiles(outputPath, allFiles);
                    void vscode.window.showInformationMessage(`🔄 Resume completed! ${e.total_files} total files (${newFiles.length} new)`);
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    resolve();
                });
                sseClient.on('error', (event) => {
                    const e = event;
                    void vscode.window.showErrorMessage(`Resume failed: ${e.message}`);
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    reject(new Error(e.message));
                });
                sseClient.onError((error) => {
                    reject(error);
                });
                // Connect to SSE stream
                await sseClient.connect();
            }
            catch (error) {
                if (sseClient) {
                    sseClient.disconnect();
                }
                reject(error);
            }
        });
    });
}
/**
 * Write generated files to disk
 */
async function writeGeneratedFiles(outputPath, files) {
    for (const file of files) {
        const fullPath = vscode.Uri.file(`${outputPath}/${file.path}`);
        // Ensure directory exists
        const dirPath = vscode.Uri.file(fullPath.fsPath.substring(0, fullPath.fsPath.lastIndexOf('/')));
        try {
            await vscode.workspace.fs.createDirectory(dirPath);
        }
        catch {
            // Directory may already exist
        }
        // Write file
        const content = Buffer.from(file.content, 'utf-8');
        await vscode.workspace.fs.writeFile(fullPath, content);
    }
    logger_1.Logger.info(`Resume: Wrote ${files.length} files to ${outputPath}`);
}
/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString)
        return 'Unknown';
    try {
        return new Date(dateString).toLocaleString();
    }
    catch {
        return dateString;
    }
}
//# sourceMappingURL=resumeCommand.js.map