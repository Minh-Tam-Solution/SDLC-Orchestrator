/**
 * Export Audit Command — Sprint 214 Track C
 *
 * Multi-step wizard: project → format (CSV/PDF) → progress → save dialog
 * Calls GET /evidence/export?format=csv|pdf&project_id=UUID
 * Handles binary StreamingResponse → save to file
 *
 * @sdlc SDLC 6.1.1 — Sprint 214 (Cross-Interface Parity)
 * @status Active
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import { ApiClient, ApiError } from '../services/apiClient';
import { Logger } from '../utils/logger';

/**
 * Registers the sdlc.exportAudit command.
 */
export function registerExportAuditCommand(
    context: vscode.ExtensionContext,
    apiClient: ApiClient
): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.exportAudit', async () => {
            try {
                await executeExportAudit(apiClient);
            } catch (error) {
                handleExportError(error);
            }
        })
    );
    Logger.info('Registered command: sdlc.exportAudit');
}

/**
 * Executes the audit export wizard.
 */
async function executeExportAudit(apiClient: ApiClient): Promise<void> {
    // Step 1: Resolve project ID
    const projectId = await resolveProjectId(apiClient);
    if (!projectId) {
        return;
    }

    // Step 2: Pick format
    const formatPick = await vscode.window.showQuickPick(
        [
            { label: '$(file) CSV', description: 'Comma-separated values — spreadsheet compatible', value: 'csv' },
            { label: '$(file-pdf) PDF', description: 'Formatted audit report with metadata', value: 'pdf' },
        ],
        { placeHolder: 'Select export format' }
    );

    if (!formatPick) {
        return;
    }

    const format = formatPick.value;

    // Step 3: Export with progress
    const data = await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: `Exporting audit log as ${format.toUpperCase()}...`,
            cancellable: false,
        },
        async () => {
            return apiClient.exportAudit(projectId, format);
        }
    );

    // Step 4: Save dialog
    const today = new Date().toISOString().slice(0, 10);
    const defaultName = `evidence_export_${projectId.slice(0, 8)}_${today}.${format}`;

    const saveUri = await vscode.window.showSaveDialog({
        defaultUri: vscode.Uri.file(defaultName),
        filters: format === 'csv'
            ? { 'CSV files': ['csv'], 'All files': ['*'] }
            : { 'PDF files': ['pdf'], 'All files': ['*'] },
        title: 'Save Audit Export',
    });

    if (!saveUri) {
        void vscode.window.showInformationMessage('Export cancelled.');
        return;
    }

    // Step 5: Write to disk
    const buffer = Buffer.from(data);
    fs.writeFileSync(saveUri.fsPath, buffer);

    // Step 6: Offer to open
    const openAction = await vscode.window.showInformationMessage(
        `Audit export saved: ${saveUri.fsPath}`,
        'Open File',
        'Open Folder'
    );

    if (openAction === 'Open File') {
        await vscode.commands.executeCommand('vscode.open', saveUri);
    } else if (openAction === 'Open Folder') {
        const folderUri = vscode.Uri.file(
            saveUri.fsPath.substring(0, saveUri.fsPath.lastIndexOf('/'))
        );
        await vscode.commands.executeCommand('revealFileInOS', folderUri);
    }
}

/**
 * Resolves the project ID from config or QuickPick.
 */
async function resolveProjectId(apiClient: ApiClient): Promise<string | undefined> {
    const currentId = apiClient.getCurrentProjectId();
    if (currentId) {
        return currentId;
    }

    // Fallback: let user pick from project list
    const projects = await apiClient.getProjects();
    if (projects.length === 0) {
        void vscode.window.showWarningMessage('No projects found. Please create a project first.');
        return undefined;
    }

    const pick = await vscode.window.showQuickPick(
        projects.map((p) => ({
            label: p.name,
            description: p.status,
            detail: `ID: ${p.id}`,
            projectId: p.id,
        })),
        { placeHolder: 'Select project to export audit for' }
    );

    return pick?.projectId;
}

/**
 * Handles export errors with user-friendly messages.
 */
function handleExportError(error: unknown): void {
    const apiError = error as ApiError;
    if (apiError?.statusCode === 401) {
        void vscode.window.showErrorMessage('Authentication required. Please log in first.', 'Login')
            .then((action) => {
                if (action === 'Login') {
                    void vscode.commands.executeCommand('sdlc.login');
                }
            });
    } else if (apiError?.statusCode === 403) {
        void vscode.window.showErrorMessage('You do not have permission to export audit data for this project.');
    } else if (apiError?.statusCode === 501) {
        void vscode.window.showErrorMessage('PDF export requires reportlab on the server. Contact your administrator.');
    } else {
        const msg = error instanceof Error ? error.message : String(error);
        Logger.error(`Export audit error: ${msg}`);
        void vscode.window.showErrorMessage(`Export failed: ${msg}`);
    }
}
