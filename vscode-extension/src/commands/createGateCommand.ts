/**
 * Gate Creation Command
 * Cross-Interface Parity — Web App + CLI + OTT + Extension
 *
 * Multi-step wizard to create a new quality gate for a project.
 * Uses GATE_PRESETS matching backend GATE_PRESETS (backend/app/api/routes/gates.py).
 *
 * Commands:
 * - sdlc.createGate: Create a new quality gate
 */

import * as vscode from 'vscode';
import { ApiClient, ApiError } from '../services/apiClient';
import { Logger } from '../utils/logger';

/**
 * Gate presets matching backend GATE_PRESETS (see backend/app/api/routes/gates.py).
 * Each entry maps a user-friendly label to the backend gate_name, gate_type, and stage.
 */
const GATE_PRESETS: Array<{
    label: string;
    gate_name: string;
    gate_type: string;
    stage: string;
}> = [
    { label: 'G0.1 — Foundation Ready', gate_name: 'G0.1', gate_type: 'FOUNDATION_READY', stage: 'WHY' },
    { label: 'G0.2 — Solution Diversity', gate_name: 'G0.2', gate_type: 'SOLUTION_DIVERSITY', stage: 'WHY' },
    { label: 'G1 — Consultation', gate_name: 'G1', gate_type: 'G1_CONSULTATION', stage: 'WHAT' },
    { label: 'G2 — Design Review', gate_name: 'G2', gate_type: 'DESIGN_REVIEW', stage: 'HOW' },
    { label: 'G3 — Ship Ready', gate_name: 'G3', gate_type: 'SHIP_READY', stage: 'BUILD' },
    { label: 'G4 — Launch Ready', gate_name: 'G4', gate_type: 'LAUNCH_READY', stage: 'DEPLOY' },
];

/**
 * Register the gate creation command.
 */
export function registerCreateGateCommand(
    context: vscode.ExtensionContext,
    apiClient: ApiClient
): void {
    const disposable = vscode.commands.registerCommand(
        'sdlc.createGate',
        async () => {
            await executeCreateGate(apiClient);
        }
    );

    context.subscriptions.push(disposable);
    Logger.info('Gate creation command registered');
}

/**
 * Execute the multi-step gate creation wizard.
 *
 * Flow:
 * 1. Resolve project (workspace state or QuickPick)
 * 2. Pick gate type from GATE_PRESETS
 * 3. Optional description
 * 4. Optional exit criteria (loop)
 * 5. Create gate with progress indicator
 * 6. Refresh gate status view
 */
async function executeCreateGate(apiClient: ApiClient): Promise<void> {
    try {
        // Step 1: Resolve project ID
        const projectId = await resolveProjectId(apiClient);
        if (!projectId) {
            return;
        }

        // Step 2: Pick gate type from presets
        const selectedPreset = await vscode.window.showQuickPick(
            GATE_PRESETS.map((preset) => ({
                label: preset.label,
                description: `Stage: ${preset.stage}`,
                detail: `Type: ${preset.gate_type}`,
                preset,
            })),
            {
                placeHolder: 'Select gate type',
                title: 'Create Quality Gate',
            }
        );

        if (!selectedPreset) {
            return;
        }

        const { gate_name, gate_type, stage } = selectedPreset.preset;

        // Step 3: Optional description
        const description = await vscode.window.showInputBox({
            prompt: 'Gate description (optional — press Enter to skip)',
            placeHolder: 'Brief description of this gate...',
        });

        // User pressed Escape
        if (description === undefined) {
            return;
        }

        // Step 4: Optional exit criteria
        const exitCriteria = await collectExitCriteria();

        // User pressed Escape during criteria collection
        if (exitCriteria === undefined) {
            return;
        }

        // Step 5: Create the gate with progress indicator
        const result = await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: `Creating gate ${gate_name}...`,
                cancellable: false,
            },
            async () => {
                const payload: {
                    gate_name: string;
                    gate_type: string;
                    stage: string;
                    description?: string;
                    exit_criteria?: Array<{ criterion: string; status?: string }>;
                } = {
                    gate_name,
                    gate_type,
                    stage,
                };

                if (description) {
                    payload.description = description.trim();
                }

                if (exitCriteria.length > 0) {
                    payload.exit_criteria = exitCriteria;
                }

                return apiClient.createGate(projectId, payload);
            }
        );

        // Step 6: Show success and refresh
        vscode.window.showInformationMessage(
            `Gate created: ${result.gate_name || gate_name} (${result.status})`
        );

        await vscode.commands.executeCommand('sdlc.refreshGates');

    } catch (error) {
        handleCreateGateError(error);
    }
}

/**
 * Resolve the project ID from workspace configuration or prompt the user.
 *
 * Checks sdlc.defaultProjectId first; if not set, fetches project list
 * and shows a QuickPick.
 */
async function resolveProjectId(apiClient: ApiClient): Promise<string | undefined> {
    // Try workspace-configured project first
    const currentProjectId = apiClient.getCurrentProjectId();
    if (currentProjectId) {
        return currentProjectId;
    }

    // Fall back to project selection QuickPick
    const projects = await apiClient.getProjects();

    if (projects.length === 0) {
        vscode.window.showWarningMessage(
            'No projects found. Create a project first with "SDLC: Initialize Project".'
        );
        return undefined;
    }

    const selected = await vscode.window.showQuickPick(
        projects.map((p) => ({
            label: p.name,
            description: p.description,
            detail: `ID: ${p.id} | Status: ${p.status}`,
            projectId: p.id,
        })),
        {
            placeHolder: 'Select a project to create the gate in',
            title: 'Select Project',
        }
    );

    return selected?.projectId;
}

/**
 * Collect optional exit criteria via a loop of InputBox prompts.
 *
 * Returns an array of criteria objects (may be empty if user declines).
 * Returns undefined if user pressed Escape (cancellation).
 */
async function collectExitCriteria(): Promise<
    Array<{ criterion: string; status?: string }> | undefined
> {
    const addCriteria = await vscode.window.showQuickPick(
        [
            { label: 'Yes', description: 'Add exit criteria for this gate' },
            { label: 'No', description: 'Skip exit criteria' },
        ],
        {
            placeHolder: 'Add exit criteria?',
            title: 'Exit Criteria',
        }
    );

    // User pressed Escape
    if (!addCriteria) {
        return undefined;
    }

    if (addCriteria.label === 'No') {
        return [];
    }

    const criteria: Array<{ criterion: string; status?: string }> = [];

    while (true) {
        const criterion = await vscode.window.showInputBox({
            prompt: `Exit criterion #${criteria.length + 1} (leave empty to finish)`,
            placeHolder: 'e.g., All unit tests pass with 95%+ coverage',
        });

        // User pressed Escape
        if (criterion === undefined) {
            return undefined;
        }

        // Empty string means done
        if (!criterion.trim()) {
            break;
        }

        criteria.push({ criterion: criterion.trim(), status: 'pending' });
    }

    return criteria;
}

/**
 * Handle gate creation errors with auth-aware messaging.
 */
function handleCreateGateError(error: unknown): void {
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

    if (apiError?.statusCode === 409) {
        vscode.window.showWarningMessage(
            `Cannot create gate: ${apiError.message || 'A gate of this type already exists for the project'}`
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
    Logger.error(`Gate creation error: ${message}`);
    vscode.window.showErrorMessage(`Failed to create gate: ${message}`);
}
