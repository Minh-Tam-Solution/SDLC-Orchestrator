/**
 * Close Sprint Command — Sprint 214 Track C
 *
 * Multi-step wizard: project → sprint select → summary → confirm → close
 * Calls sprint close endpoint via apiClient
 * Refreshes gate views after close
 *
 * @sdlc SDLC 6.1.1 — Sprint 214 (Cross-Interface Parity)
 * @status Active
 */

import * as vscode from 'vscode';
import { ApiClient, ApiError } from '../services/apiClient';
import { Logger } from '../utils/logger';

/**
 * Sprint list item from backend.
 */
interface SprintItem {
    id: string;
    sprint_number: number;
    goal: string;
    status: string;
    start_date: string;
    end_date: string;
}

/**
 * Registers the sdlc.closeSprint command.
 */
export function registerCloseSprintCommand(
    context: vscode.ExtensionContext,
    apiClient: ApiClient
): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.closeSprint', async () => {
            try {
                await executeCloseSprint(apiClient);
            } catch (error) {
                handleCloseSprintError(error);
            }
        })
    );
    Logger.info('Registered command: sdlc.closeSprint');
}

/**
 * Executes the sprint close wizard.
 */
async function executeCloseSprint(apiClient: ApiClient): Promise<void> {
    // Step 1: Resolve project ID
    const projectId = apiClient.getCurrentProjectId();
    if (!projectId) {
        const projects = await apiClient.getProjects();
        if (projects.length === 0) {
            void vscode.window.showWarningMessage('No projects found.');
            return;
        }
        const pick = await vscode.window.showQuickPick(
            projects.map((p) => ({
                label: p.name,
                description: p.status,
                detail: `ID: ${p.id}`,
                projectId: p.id,
            })),
            { placeHolder: 'Select project to close sprint for' }
        );
        if (!pick) {
            return;
        }
        // Use the selected project for this flow
        return await executeCloseSprintForProject(apiClient, pick.projectId);
    }

    await executeCloseSprintForProject(apiClient, projectId);
}

async function executeCloseSprintForProject(
    apiClient: ApiClient,
    projectId: string
): Promise<void> {
    // Step 2: Fetch sprints
    const sprints = await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Loading sprints...',
            cancellable: false,
        },
        async () => apiClient.getProjectSprints(projectId)
    );

    const activeSprints = sprints.filter(
        (s: SprintItem) => s.status === 'active' || s.status === 'in_progress'
    );

    if (activeSprints.length === 0) {
        void vscode.window.showInformationMessage('No active sprints found for this project.');
        return;
    }

    // Step 3: Pick sprint
    const sprintPick = await vscode.window.showQuickPick(
        activeSprints.map((s: SprintItem) => ({
            label: `Sprint ${s.sprint_number}`,
            description: s.goal,
            detail: `${s.start_date} → ${s.end_date} | Status: ${s.status}`,
            sprintId: s.id,
            sprintNumber: s.sprint_number,
        })),
        { placeHolder: 'Select sprint to close' }
    );

    if (!sprintPick) {
        return;
    }

    // Step 4: Optional summary
    const summary = await vscode.window.showInputBox({
        prompt: `Sprint ${sprintPick.sprintNumber} close summary (optional)`,
        placeHolder: 'Brief summary of sprint outcomes...',
    });

    // User pressed Escape
    if (summary === undefined) {
        return;
    }

    // Step 5: Confirm
    const confirm = await vscode.window.showWarningMessage(
        `Close Sprint ${sprintPick.sprintNumber}? This will trigger G-Sprint-Close evaluation.`,
        { modal: true },
        'Close Sprint'
    );

    if (confirm !== 'Close Sprint') {
        return;
    }

    // Step 6: Execute close
    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: `Closing Sprint ${sprintPick.sprintNumber}...`,
            cancellable: false,
        },
        async () => {
            await apiClient.closeSprintGate(sprintPick.sprintId, summary || undefined);
        }
    );

    // Step 7: Refresh gate views
    await vscode.commands.executeCommand('sdlc.refreshGates');

    void vscode.window.showInformationMessage(
        `Sprint ${sprintPick.sprintNumber} closed successfully. Gate views refreshed.`
    );
}

/**
 * Handles close sprint errors with user-friendly messages.
 */
function handleCloseSprintError(error: unknown): void {
    const apiError = error as ApiError;
    if (apiError?.statusCode === 401) {
        void vscode.window.showErrorMessage('Authentication required. Please log in first.', 'Login')
            .then((action) => {
                if (action === 'Login') {
                    void vscode.commands.executeCommand('sdlc.login');
                }
            });
    } else if (apiError?.statusCode === 403) {
        void vscode.window.showErrorMessage('You do not have permission to close sprints for this project.');
    } else if (apiError?.statusCode === 404) {
        void vscode.window.showErrorMessage('Sprint not found. It may have been already closed.');
    } else if (apiError?.statusCode === 409) {
        void vscode.window.showErrorMessage('Sprint cannot be closed in its current state. Check gate requirements.');
    } else {
        const msg = error instanceof Error ? error.message : String(error);
        Logger.error(`Close sprint error: ${msg}`);
        void vscode.window.showErrorMessage(`Close sprint failed: ${msg}`);
    }
}
