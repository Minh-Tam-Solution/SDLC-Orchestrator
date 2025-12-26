/**
 * Resume Command - Resume Failed Generation
 *
 * Implements the sdlc.resume command for resuming
 * failed or interrupted code generation sessions.
 *
 * Sprint 53 Day 1 - Resume Command Implementation
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';
import { handleError } from '../utils/errors';
import type { CodegenApiService } from '../services/codegenApi';
import { SSEClient, createCodegenSSEClient } from '../services/sseClient';
import type {
    SSEEvent,
    SSEFileGeneratedEvent,
    SSEQualityGateEvent,
    SSECompletedEvent,
    SSEErrorEvent,
    GeneratedFile,
    CodegenSession,
} from '../types/codegen';
import { ConfigManager } from '../utils/config';

/**
 * Register the resume command
 */
export function registerResumeCommand(
    context: vscode.ExtensionContext,
    codegenApi: CodegenApiService
): void {
    const command = vscode.commands.registerCommand(
        'sdlc.resume',
        async (sessionId?: string) => {
            await executeResumeCommand(codegenApi, sessionId);
        }
    );
    context.subscriptions.push(command);
    Logger.info('Resume command registered');
}

/**
 * Execute the resume command
 */
async function executeResumeCommand(
    codegenApi: CodegenApiService,
    providedSessionId?: string
): Promise<void> {
    try {
        // Get session ID if not provided
        const sessionId = providedSessionId || await getFailedSessionId(codegenApi);
        if (!sessionId) {
            return;
        }

        // Get session status to verify it can be resumed
        const session = await codegenApi.getGenerationStatus(sessionId);

        if (session.status === 'completed') {
            void vscode.window.showInformationMessage(
                'This session is already completed. Use Preview to view generated files.'
            );
            return;
        }

        if (session.status === 'generating' || session.status === 'validating') {
            void vscode.window.showWarningMessage(
                'This session is still in progress. Please wait or cancel it first.'
            );
            return;
        }

        // Confirm resume
        const confirm = await vscode.window.showInformationMessage(
            `Resume generation for session ${sessionId.substring(0, 8)}?\n\nStatus: ${session.status}\nFiles generated: ${session.files?.length || 0}`,
            { modal: true },
            'Resume',
            'Cancel'
        );

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

    } catch (error) {
        await handleError(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}

/**
 * Get failed session ID from user
 */
async function getFailedSessionId(codegenApi: CodegenApiService): Promise<string | undefined> {
    const config = vscode.workspace.getConfiguration('sdlc');
    const projectId = config.get<string>('defaultProjectId');

    if (projectId) {
        try {
            const sessions = await codegenApi.listSessions(projectId);
            const failedSessions = sessions.filter(
                s => s.status === 'failed' || s.status === 'in_progress'
            );

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
        } catch (error) {
            Logger.warn(`Failed to list sessions: ${error}`);
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
async function selectOutputDirectory(): Promise<string | undefined> {
    const workspaceFolders = vscode.workspace.workspaceFolders;

    const options: vscode.OpenDialogOptions = {
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
async function resumeGenerationWithStreaming(
    codegenApi: CodegenApiService,
    sessionId: string,
    previousSession: CodegenSession,
    outputPath: string
): Promise<void> {
    const config = ConfigManager.getInstance();
    let sseClient: SSEClient | null = null;

    const existingFiles: GeneratedFile[] = previousSession.files || [];
    const newFiles: GeneratedFile[] = [];

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: '🔄 Resuming generation...',
            cancellable: true,
        },
        async (progressReporter, cancellationToken) => {
            return new Promise<void>(async (resolve, reject) => {
                try {
                    // Resume generation
                    progressReporter.report({
                        message: `Resuming from ${existingFiles.length} files...`,
                    });

                    const result = await codegenApi.resumeGeneration(sessionId);
                    const newSessionId = result.session_id;

                    // Get auth token and create SSE client
                    const token = await codegenApi.getAuthToken();
                    sseClient = createCodegenSSEClient(
                        config.apiUrl,
                        newSessionId,
                        token
                    );

                    // Handle cancellation
                    cancellationToken.onCancellationRequested(() => {
                        if (sseClient) {
                            sseClient.disconnect();
                        }
                        void codegenApi.cancelGeneration(newSessionId);
                        resolve();
                    });

                    // Set up event handlers
                    sseClient.on('file_generating', (event: SSEEvent) => {
                        const e = event as SSEEvent & { path: string };
                        progressReporter.report({
                            message: `Generating: ${e.path}`,
                        });
                    });

                    sseClient.on('file_generated', (event: SSEEvent) => {
                        const e = event as SSEFileGeneratedEvent;
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

                    sseClient.on('quality_gate', (event: SSEEvent) => {
                        const e = event as SSEQualityGateEvent;
                        const icon = e.status === 'passed' ? '✅' : '❌';
                        progressReporter.report({
                            message: `${icon} Gate ${e.gate_number}: ${e.gate_name}`,
                            increment: 10,
                        });
                    });

                    sseClient.on('completed', async (event: SSEEvent) => {
                        const e = event as SSECompletedEvent;

                        // Combine existing and new files
                        const allFiles = [...existingFiles, ...newFiles];

                        // Write all files to disk
                        await writeGeneratedFiles(outputPath, allFiles);

                        void vscode.window.showInformationMessage(
                            `🔄 Resume completed! ${e.total_files} total files (${newFiles.length} new)`
                        );

                        if (sseClient) {
                            sseClient.disconnect();
                        }
                        resolve();
                    });

                    sseClient.on('error', (event: SSEEvent) => {
                        const e = event as SSEErrorEvent;

                        void vscode.window.showErrorMessage(
                            `Resume failed: ${e.message}`
                        );

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

                } catch (error) {
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    reject(error);
                }
            });
        }
    );
}

/**
 * Write generated files to disk
 */
async function writeGeneratedFiles(
    outputPath: string,
    files: GeneratedFile[]
): Promise<void> {
    for (const file of files) {
        const fullPath = vscode.Uri.file(`${outputPath}/${file.path}`);

        // Ensure directory exists
        const dirPath = vscode.Uri.file(fullPath.fsPath.substring(0, fullPath.fsPath.lastIndexOf('/')));
        try {
            await vscode.workspace.fs.createDirectory(dirPath);
        } catch {
            // Directory may already exist
        }

        // Write file
        const content = Buffer.from(file.content, 'utf-8');
        await vscode.workspace.fs.writeFile(fullPath, content);
    }

    Logger.info(`Resume: Wrote ${files.length} files to ${outputPath}`);
}

/**
 * Format date string
 */
function formatDate(dateString?: string): string {
    if (!dateString) return 'Unknown';
    try {
        return new Date(dateString).toLocaleString();
    } catch {
        return dateString;
    }
}
