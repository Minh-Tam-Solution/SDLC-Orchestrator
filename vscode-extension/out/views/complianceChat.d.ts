/**
 * SDLC Orchestrator Compliance Chat Participant
 *
 * Implements VS Code Chat Participant API for Copilot-style @gate commands.
 * Provides compliance assistance, gate status queries, and AI recommendations.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
 */
import * as vscode from 'vscode';
import { ApiClient } from '../services/apiClient';
/**
 * Chat result metadata (used for tracking command execution context)
 */
type ChatResultMetadata = {
    command?: string;
    projectId?: string;
    violationId?: string;
    councilMode?: boolean;
};
export type { ChatResultMetadata };
/**
 * Compliance Chat Participant for @gate commands
 */
export declare class ComplianceChatParticipant {
    private apiClient;
    constructor(apiClient: ApiClient);
    /**
     * Handles incoming chat requests
     *
     * @param request - The chat request from the user
     * @param context - The chat context with history
     * @param stream - Response stream for sending output
     * @param token - Cancellation token
     */
    handleChatRequest(request: vscode.ChatRequest, _context: vscode.ChatContext, stream: vscode.ChatResponseStream, token: vscode.CancellationToken): Promise<vscode.ChatResult>;
    /**
     * Handles /status command - shows current gate status
     */
    private handleStatusCommand;
    /**
     * Handles /evaluate command - shows current violations
     */
    private handleEvaluateCommand;
    /**
     * Handles /fix command - gets AI recommendation for a violation
     */
    private handleFixCommand;
    /**
     * Handles /council command - uses full AI Council deliberation
     */
    private handleCouncilCommand;
    /**
     * Handles general questions without a specific command
     */
    private handleGeneralQuestion;
    /**
     * Gets emoji for gate status
     */
    private getStatusEmoji;
    /**
     * Renders a list of violations
     */
    private renderViolationList;
    /**
     * Gets emoji for severity
     */
    private getSeverityEmoji;
}
//# sourceMappingURL=complianceChat.d.ts.map