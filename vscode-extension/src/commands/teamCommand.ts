/**
 * Team Invite Command — Sprint 212 Track C (Team Invite Parity)
 *
 * Provides sdlc.inviteTeamMember command:
 *   1. Prompts for email via showInputBox
 *   2. Prompts for role via showQuickPick (member/admin/viewer)
 *   3. POSTs to /api/v1/teams/{team_id}/invitations
 *   4. Shows success/error notification
 *
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
import { Logger } from '../utils/logger';

/**
 * Register the sdlc.inviteTeamMember command.
 */
export function registerTeamCommand(
    context: vscode.ExtensionContext,
    apiClient?: ApiClient
): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('sdlc.inviteTeamMember', async () => {
            if (!apiClient) {
                void vscode.window.showErrorMessage('API client not initialized. Please log in first.');
                return;
            }

            // Step 1: Prompt for email
            const email = await vscode.window.showInputBox({
                prompt: 'Enter the email address to invite',
                placeHolder: 'colleague@company.com',
                validateInput: (value) => {
                    if (!value || !value.includes('@') || !value.includes('.')) {
                        return 'Please enter a valid email address';
                    }
                    return null;
                },
            });

            if (!email) {
                return;
            }

            // Step 2: Select role
            const roleSelection = await vscode.window.showQuickPick(
                [
                    { label: 'Member', description: 'Standard team member', value: 'member' },
                    { label: 'Admin', description: 'Team administrator', value: 'admin' },
                    { label: 'Viewer', description: 'Read-only access', value: 'viewer' },
                ],
                { placeHolder: 'Select a role for the invited user' }
            );

            if (!roleSelection) {
                return;
            }

            // Step 3: Get team ID from workspace config
            const teamId = vscode.workspace.getConfiguration('sdlc').get<string>('defaultTeamId');
            if (!teamId) {
                void vscode.window.showErrorMessage(
                    'No team ID configured. Set sdlc.defaultTeamId in workspace settings.'
                );
                return;
            }

            // Step 4: Send invitation
            try {
                await apiClient.post(
                    `/api/v1/teams/${teamId}/invitations`,
                    { email, role: roleSelection.value }
                );
                void vscode.window.showInformationMessage(
                    `Invited ${email} as ${roleSelection.value}`
                );
                Logger.info(`Team invite sent: ${email} as ${roleSelection.value}`);
            } catch (error: unknown) {
                const msg = error instanceof Error ? error.message : String(error);
                Logger.error(`Team invite failed: ${msg}`);
                void vscode.window.showErrorMessage(`Failed to invite ${email}: ${msg}`);
            }
        })
    );

    Logger.info('Team command registered');
}
