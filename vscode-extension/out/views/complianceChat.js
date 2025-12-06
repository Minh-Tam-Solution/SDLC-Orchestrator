"use strict";
/**
 * SDLC Orchestrator Compliance Chat Participant
 *
 * Implements VS Code Chat Participant API for Copilot-style @gate commands.
 * Provides compliance assistance, gate status queries, and AI recommendations.
 *
 * Sprint 27 Day 1 - Views
 * @version 0.1.0
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ComplianceChatParticipant = void 0;
const logger_1 = require("../utils/logger");
const config_1 = require("../utils/config");
/**
 * Compliance Chat Participant for @gate commands
 */
class ComplianceChatParticipant {
    apiClient;
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
    /**
     * Handles incoming chat requests
     *
     * @param request - The chat request from the user
     * @param context - The chat context with history
     * @param stream - Response stream for sending output
     * @param token - Cancellation token
     */
    async handleChatRequest(request, _context, stream, token) {
        logger_1.Logger.info(`Chat request: command=${request.command ?? 'none'}, prompt=${request.prompt}`);
        try {
            // Check for cancellation
            if (token.isCancellationRequested) {
                return { metadata: { command: 'cancelled' } };
            }
            // Handle slash commands
            switch (request.command) {
                case 'status':
                    return await this.handleStatusCommand(stream, token);
                case 'evaluate':
                    return await this.handleEvaluateCommand(stream, token);
                case 'fix':
                    return await this.handleFixCommand(request.prompt, stream, token);
                case 'council':
                    return await this.handleCouncilCommand(request.prompt, stream, token);
                default:
                    return this.handleGeneralQuestion(request.prompt, stream, token);
            }
        }
        catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            logger_1.Logger.error(`Chat request failed: ${message}`);
            stream.markdown(`\n\n**Error:** ${message}\n`);
            stream.markdown('\nPlease try again or check your connection to the SDLC Orchestrator backend.');
            return { metadata: { command: request.command ?? 'error' } };
        }
    }
    /**
     * Handles /status command - shows current gate status
     */
    async handleStatusCommand(stream, token) {
        const projectId = this.apiClient.getCurrentProjectId();
        if (!projectId) {
            stream.markdown('## No Project Selected\n\n');
            stream.markdown('Please select a project first using the **SDLC: Select Project** command.\n');
            return { metadata: { command: 'status' } };
        }
        stream.markdown('## Gate Status\n\n');
        stream.progress('Loading gate status...');
        if (token.isCancellationRequested) {
            return { metadata: { command: 'status' } };
        }
        const gates = await this.apiClient.getGates(projectId);
        if (gates.length === 0) {
            stream.markdown('No gates found for this project.\n');
            return { metadata: { command: 'status', projectId } };
        }
        // Display gate status
        for (const gate of gates) {
            const icon = this.getStatusEmoji(gate.status);
            const progress = gate.required_evidence_count > 0
                ? Math.round((gate.evidence_count / gate.required_evidence_count) * 100)
                : 0;
            stream.markdown(`${icon} **${gate.gate_type}**: ${gate.status}`);
            if (gate.status !== 'approved' && gate.status !== 'not_started') {
                stream.markdown(` (${gate.evidence_count}/${gate.required_evidence_count} evidence, ${progress}%)`);
            }
            stream.markdown('\n');
        }
        // Summary
        const approved = gates.filter((g) => g.status === 'approved').length;
        const pending = gates.filter((g) => g.status === 'pending_approval').length;
        stream.markdown('\n---\n');
        stream.markdown(`**Summary:** ${approved}/${gates.length} gates approved`);
        if (pending > 0) {
            stream.markdown(`, ${pending} pending approval`);
        }
        stream.markdown('\n');
        return { metadata: { command: 'status', projectId } };
    }
    /**
     * Handles /evaluate command - shows current violations
     */
    async handleEvaluateCommand(stream, token) {
        const projectId = this.apiClient.getCurrentProjectId();
        if (!projectId) {
            stream.markdown('## No Project Selected\n\n');
            stream.markdown('Please select a project first.\n');
            return { metadata: { command: 'evaluate' } };
        }
        stream.markdown('## Compliance Evaluation\n\n');
        stream.progress('Scanning for violations...');
        if (token.isCancellationRequested) {
            return { metadata: { command: 'evaluate' } };
        }
        const violations = await this.apiClient.getViolations(projectId, 'open');
        if (violations.length === 0) {
            stream.markdown('**No violations found.** Your project is compliant.\n');
            return { metadata: { command: 'evaluate', projectId } };
        }
        stream.markdown(`**${violations.length} violations found**\n\n`);
        // Group by severity
        const critical = violations.filter((v) => v.severity === 'critical');
        const high = violations.filter((v) => v.severity === 'high');
        const medium = violations.filter((v) => v.severity === 'medium');
        const low = violations.filter((v) => v.severity === 'low');
        if (critical.length > 0) {
            stream.markdown('### Critical\n');
            this.renderViolationList(critical.slice(0, 3), stream);
            if (critical.length > 3) {
                stream.markdown(`_...and ${critical.length - 3} more_\n`);
            }
            stream.markdown('\n');
        }
        if (high.length > 0) {
            stream.markdown('### High\n');
            this.renderViolationList(high.slice(0, 3), stream);
            if (high.length > 3) {
                stream.markdown(`_...and ${high.length - 3} more_\n`);
            }
            stream.markdown('\n');
        }
        if (medium.length > 0) {
            stream.markdown('### Medium\n');
            this.renderViolationList(medium.slice(0, 3), stream);
            if (medium.length > 3) {
                stream.markdown(`_...and ${medium.length - 3} more_\n`);
            }
            stream.markdown('\n');
        }
        if (low.length > 0) {
            stream.markdown('### Low\n');
            this.renderViolationList(low.slice(0, 3), stream);
            if (low.length > 3) {
                stream.markdown(`_...and ${low.length - 3} more_\n`);
            }
            stream.markdown('\n');
        }
        // Recommendation
        stream.markdown('---\n');
        stream.markdown('**Tip:** Use `/fix <violation-id>` to get AI recommendations for fixing violations.\n');
        return { metadata: { command: 'evaluate', projectId } };
    }
    /**
     * Handles /fix command - gets AI recommendation for a violation
     */
    async handleFixCommand(prompt, stream, token) {
        const violationId = prompt.trim().split(/\s+/)[0];
        if (!violationId) {
            stream.markdown('## Fix Violation\n\n');
            stream.markdown('**Usage:** `/fix <violation-id>`\n\n');
            stream.markdown('Please provide a violation ID to get AI recommendations.\n');
            return { metadata: { command: 'fix' } };
        }
        stream.markdown('## AI Recommendation\n\n');
        stream.markdown(`**Violation ID:** \`${violationId}\`\n\n`);
        stream.progress('Generating AI recommendation...');
        if (token.isCancellationRequested) {
            return { metadata: { command: 'fix', violationId } };
        }
        const config = config_1.ConfigManager.getInstance();
        const councilMode = false; // Use single mode for faster response
        const recommendation = await this.apiClient.getAIRecommendation(violationId, councilMode);
        // Display recommendation
        stream.markdown('### Recommendation\n\n');
        stream.markdown(recommendation.recommendation);
        stream.markdown('\n\n');
        // Metadata
        stream.markdown('---\n');
        stream.markdown(`**Confidence:** ${recommendation.confidence_score}/10\n\n`);
        stream.markdown(`**Provider:** ${recommendation.providers_used.join(', ')}\n\n`);
        if (recommendation.total_cost_usd !== undefined) {
            stream.markdown(`**Cost:** $${recommendation.total_cost_usd.toFixed(4)}\n\n`);
        }
        // Suggest council mode for better quality
        if (!councilMode && config.aiCouncilEnabled) {
            stream.markdown('_For higher confidence recommendations, use `/council <violation-id>` for AI Council deliberation._\n');
        }
        return {
            metadata: {
                command: 'fix',
                violationId,
                councilMode,
            },
        };
    }
    /**
     * Handles /council command - uses full AI Council deliberation
     */
    async handleCouncilCommand(prompt, stream, token) {
        const violationId = prompt.trim().split(/\s+/)[0];
        if (!violationId) {
            stream.markdown('## AI Council Deliberation\n\n');
            stream.markdown('**Usage:** `/council <violation-id>`\n\n');
            stream.markdown('AI Council uses 3-stage multi-LLM deliberation for high-confidence recommendations.\n');
            return { metadata: { command: 'council' } };
        }
        stream.markdown('## AI Council Deliberation\n\n');
        stream.markdown(`**Violation ID:** \`${violationId}\`\n\n`);
        stream.markdown('Starting 3-stage deliberation process...\n\n');
        // Stage 1
        stream.progress('Stage 1: Querying multiple AI providers...');
        if (token.isCancellationRequested) {
            return { metadata: { command: 'council', violationId } };
        }
        // Use council mode
        const recommendation = await this.apiClient.getAIRecommendation(violationId, true // council mode
        );
        // Display stages if available
        if (recommendation.stage1_responses && recommendation.stage1_responses.length > 0) {
            stream.markdown('### Stage 1: Provider Responses\n\n');
            for (const response of recommendation.stage1_responses) {
                if (response.error) {
                    stream.markdown(`- **${response.provider}:** _Error - ${response.error}_\n`);
                }
                else {
                    stream.markdown(`- **${response.provider}** (${response.duration_ms}ms): ${response.response.substring(0, 100)}...\n`);
                }
            }
            stream.markdown('\n');
        }
        // Stage 2 rankings
        if (recommendation.stage2_rankings && recommendation.stage2_rankings.length > 0) {
            stream.markdown('### Stage 2: Peer Review Rankings\n\n');
            for (const ranking of recommendation.stage2_rankings) {
                stream.markdown(`- **${ranking.ranker}:** ${ranking.rankings.join(' > ')}\n`);
            }
            stream.markdown('\n');
        }
        // Stage 3 synthesis
        stream.markdown('### Stage 3: Chairman Synthesis\n\n');
        stream.markdown(recommendation.recommendation);
        stream.markdown('\n\n');
        // Metadata
        stream.markdown('---\n');
        stream.markdown(`**Final Confidence:** ${recommendation.confidence_score}/10\n\n`);
        stream.markdown(`**Providers Used:** ${recommendation.providers_used.join(', ')}\n\n`);
        stream.markdown(`**Total Time:** ${recommendation.total_duration_ms}ms\n\n`);
        if (recommendation.total_cost_usd !== undefined) {
            stream.markdown(`**Total Cost:** $${recommendation.total_cost_usd.toFixed(4)}\n`);
        }
        return {
            metadata: {
                command: 'council',
                violationId,
                councilMode: true,
            },
        };
    }
    /**
     * Handles general questions without a specific command
     */
    handleGeneralQuestion(prompt, stream, _token) {
        stream.markdown('## SDLC Gate Assistant\n\n');
        // Provide contextual help
        stream.markdown('I can help you with SDLC compliance and gate management. Here are the available commands:\n\n');
        stream.markdown('### Commands\n\n');
        stream.markdown('- **/status** - Show current gate status (G0-G5)\n');
        stream.markdown('- **/evaluate** - Run compliance evaluation and show violations\n');
        stream.markdown('- **/fix `<violation-id>`** - Get AI recommendation to fix a violation\n');
        stream.markdown('- **/council `<violation-id>`** - Use AI Council for high-confidence recommendations\n');
        stream.markdown('\n### Examples\n\n');
        stream.markdown('```\n@gate /status\n@gate /evaluate\n@gate /fix abc123-def456\n@gate /council abc123-def456\n```\n\n');
        // If user provided a question, acknowledge it
        if (prompt.trim()) {
            stream.markdown('---\n');
            stream.markdown(`You asked: "${prompt}"\n\n`);
            stream.markdown('Please use one of the commands above, or rephrase your question.\n');
        }
        return { metadata: { command: 'help' } };
    }
    /**
     * Gets emoji for gate status
     */
    getStatusEmoji(status) {
        switch (status) {
            case 'approved':
                return '\u2705'; // green check
            case 'pending_approval':
                return '\uD83D\uDD04'; // refresh
            case 'in_progress':
                return '\u23F3'; // hourglass
            case 'rejected':
                return '\u274C'; // red X
            case 'not_started':
            default:
                return '\u26AA'; // white circle
        }
    }
    /**
     * Renders a list of violations
     */
    renderViolationList(violations, stream) {
        for (const v of violations) {
            const severityEmoji = this.getSeverityEmoji(v.severity);
            stream.markdown(`${severityEmoji} **${v.violation_type}**\n`);
            stream.markdown(`  _${v.description.substring(0, 80)}${v.description.length > 80 ? '...' : ''}_\n`);
            stream.markdown(`  ID: \`${v.id}\`\n\n`);
        }
    }
    /**
     * Gets emoji for severity
     */
    getSeverityEmoji(severity) {
        switch (severity) {
            case 'critical':
                return '\uD83D\uDD34'; // red circle
            case 'high':
                return '\uD83D\uDFE0'; // orange circle
            case 'medium':
                return '\uD83D\uDFE1'; // yellow circle
            case 'low':
            default:
                return '\uD83D\uDD35'; // blue circle
        }
    }
}
exports.ComplianceChatParticipant = ComplianceChatParticipant;
//# sourceMappingURL=complianceChat.js.map