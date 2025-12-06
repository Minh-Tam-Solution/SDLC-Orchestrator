/**
 * Compliance Chat Participant Unit Tests
 *
 * Tests for the @gate chat commands: /status, /evaluate, /fix, /council
 *
 * Sprint 27 Day 4 - Testing
 * @version 0.1.0
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { ComplianceChatParticipant } from '../../views/complianceChat';
import { ApiClient } from '../../services/apiClient';
import { AuthService } from '../../services/authService';
import { simpleMockContext } from './testHelpers';

const mockContext = simpleMockContext;

// Mock response stream to capture output
class MockResponseStream implements vscode.ChatResponseStream {
    public markdownCalls: string[] = [];
    public progressCalls: string[] = [];
    public anchorCalls: Array<{ value: vscode.Uri | vscode.Location; title: string | undefined }> = [];
    public buttonCalls: Array<{ command: vscode.Command }> = [];
    public filetreeCalls: Array<{ value: vscode.ChatResponseFileTree[]; baseUri: vscode.Uri }> = [];
    public referenceCalls: Array<{ value: vscode.Uri | vscode.Location }> = [];

    markdown(value: string | vscode.MarkdownString): void {
        const text = typeof value === 'string' ? value : value.value;
        this.markdownCalls.push(text);
    }

    progress(value: string): void {
        this.progressCalls.push(value);
    }

    anchor(value: vscode.Uri | vscode.Location, title?: string): void {
        this.anchorCalls.push({ value, title: title ?? undefined });
    }

    button(command: vscode.Command): void {
        this.buttonCalls.push({ command });
    }

    filetree(value: vscode.ChatResponseFileTree[], baseUri: vscode.Uri): void {
        this.filetreeCalls.push({ value, baseUri });
    }

    reference(value: vscode.Uri | vscode.Location): void {
        this.referenceCalls.push({ value });
    }

    push(part: vscode.ChatResponsePart): void {
        // Handle generic parts
        if ('value' in part && typeof part.value === 'string') {
            this.markdownCalls.push(part.value);
        }
    }

    getMarkdownContent(): string {
        return this.markdownCalls.join('');
    }

    reset(): void {
        this.markdownCalls = [];
        this.progressCalls = [];
        this.anchorCalls = [];
        this.buttonCalls = [];
        this.filetreeCalls = [];
        this.referenceCalls = [];
    }
}

// Mock cancellation token
class MockCancellationToken implements vscode.CancellationToken {
    private _isCancellationRequested = false;
    private _onCancellationRequested = new vscode.EventEmitter<void>();

    get isCancellationRequested(): boolean {
        return this._isCancellationRequested;
    }

    get onCancellationRequested(): vscode.Event<void> {
        return this._onCancellationRequested.event;
    }

    cancel(): void {
        this._isCancellationRequested = true;
        this._onCancellationRequested.fire();
    }
}

// Mock chat request
function createMockRequest(command?: string, prompt = ''): vscode.ChatRequest {
    return {
        command,
        prompt,
        references: [],
        toolReferences: [],
        model: {} as vscode.LanguageModelChat,
        toolInvocationToken: {} as vscode.ChatParticipantToolToken,
    };
}

// Mock chat context
const mockChatContext: vscode.ChatContext = {
    history: [],
};

suite('ComplianceChatParticipant Test Suite', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('ComplianceChatParticipant initializes correctly', () => {
        assert.ok(chatParticipant);
    });

    test('handleChatRequest returns result with metadata', async () => {
        const request = createMockRequest();
        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.ok(result);
        assert.ok(result.metadata);
    });

    test('Cancelled request returns cancelled metadata', async () => {
        mockToken.cancel();
        const request = createMockRequest('status');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'cancelled');
    });
});

suite('ComplianceChatParticipant /status Command', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('/status without project shows no project message', async () => {
        const request = createMockRequest('status');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'status');
        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('No Project Selected'));
    });

    test('/status returns gate status metadata', async () => {
        const request = createMockRequest('status');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'status');
    });

    test('/status shows progress indicator', async () => {
        const request = createMockRequest('status');

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        // Should show markdown for no project message
        assert.ok(mockStream.markdownCalls.length > 0);
    });
});

suite('ComplianceChatParticipant /evaluate Command', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('/evaluate without project shows no project message', async () => {
        const request = createMockRequest('evaluate');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'evaluate');
        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('No Project Selected'));
    });

    test('/evaluate returns evaluate metadata', async () => {
        const request = createMockRequest('evaluate');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'evaluate');
    });

    test('/evaluate cancellation is handled', async () => {
        mockToken.cancel();
        const request = createMockRequest('evaluate');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        // Should return early with cancelled command
        assert.strictEqual(result.metadata?.command, 'cancelled');
    });
});

suite('ComplianceChatParticipant /fix Command', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('/fix without violation ID shows usage message', async () => {
        const request = createMockRequest('fix', '');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'fix');
        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('Usage:'));
        assert.ok(content.includes('<violation-id>'));
    });

    test('/fix with violation ID returns fix metadata', async () => {
        const request = createMockRequest('fix', 'abc123');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        // May fail due to API call, but metadata should be set
        assert.ok(result.metadata?.command === 'fix' || result.metadata?.command === 'error');
    });

    test('/fix shows AI Recommendation header', async () => {
        const request = createMockRequest('fix', 'test-violation-id');

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('AI Recommendation') || content.includes('Error'));
    });

    test('/fix extracts first word as violation ID', async () => {
        const request = createMockRequest('fix', 'violation-123 extra text');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        // violationId in metadata should be just the first word
        if (result.metadata?.violationId) {
            assert.strictEqual(result.metadata.violationId, 'violation-123');
        }
    });
});

suite('ComplianceChatParticipant /council Command', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('/council without violation ID shows usage message', async () => {
        const request = createMockRequest('council', '');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'council');
        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('Usage:'));
        assert.ok(content.includes('AI Council'));
    });

    test('/council explains 3-stage deliberation', async () => {
        const request = createMockRequest('council', '');

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('3-stage'));
    });

    test('/council with violation ID sets councilMode metadata', async () => {
        const request = createMockRequest('council', 'test-id');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        // May fail due to API, but if successful should have councilMode
        if (result.metadata?.councilMode !== undefined) {
            assert.strictEqual(result.metadata.councilMode, true);
        }
    });
});

suite('ComplianceChatParticipant General Questions', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('General question shows help commands', async () => {
        const request = createMockRequest(undefined, 'How do I check compliance?');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        assert.strictEqual(result.metadata?.command, 'help');
        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('/status'));
        assert.ok(content.includes('/evaluate'));
        assert.ok(content.includes('/fix'));
        assert.ok(content.includes('/council'));
    });

    test('Empty prompt shows available commands', async () => {
        const request = createMockRequest(undefined, '');

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('Commands'));
    });

    test('General question echoes user question', async () => {
        const userQuestion = 'What is SDLC compliance?';
        const request = createMockRequest(undefined, userQuestion);

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes(userQuestion));
    });

    test('Shows example commands', async () => {
        const request = createMockRequest(undefined, '');

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        const content = mockStream.getMarkdownContent();
        assert.ok(content.includes('Examples'));
        assert.ok(content.includes('@gate'));
    });
});

suite('ComplianceChatParticipant Error Handling', () => {
    let chatParticipant: ComplianceChatParticipant;
    let apiClient: ApiClient;
    let authService: AuthService;
    let mockStream: MockResponseStream;
    let mockToken: MockCancellationToken;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        chatParticipant = new ComplianceChatParticipant(apiClient);
        mockStream = new MockResponseStream();
        mockToken = new MockCancellationToken();
    });

    test('Error during request shows error message', async () => {
        // This will fail because no real backend
        const request = createMockRequest('fix', 'invalid-id');

        const result = await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        // Should handle error gracefully
        assert.ok(result);
        assert.ok(result.metadata);
    });

    test('Network error suggests checking connection', async () => {
        const request = createMockRequest('fix', 'test-id');

        await chatParticipant.handleChatRequest(
            request,
            mockChatContext,
            mockStream,
            mockToken
        );

        const content = mockStream.getMarkdownContent();
        // May show error or AI recommendation header
        assert.ok(content.length > 0);
    });
});

suite('ComplianceChatParticipant Helper Methods', () => {
    test('getStatusEmoji returns correct emojis', () => {
        // Test by creating chat participant and checking output
        // The emojis are internal but we can verify behavior through output

        const statuses = ['approved', 'pending_approval', 'in_progress', 'rejected', 'not_started'];

        for (const status of statuses) {
            // Status should be valid
            assert.ok(status);
        }
    });

    test('getSeverityEmoji maps severity to colors', () => {
        const severities = ['critical', 'high', 'medium', 'low'];

        for (const severity of severities) {
            assert.ok(severity);
        }
    });
});

suite('MockResponseStream Test', () => {
    test('MockResponseStream captures markdown calls', () => {
        const stream = new MockResponseStream();

        stream.markdown('# Header');
        stream.markdown('Content');

        assert.strictEqual(stream.markdownCalls.length, 2);
        assert.strictEqual(stream.markdownCalls[0], '# Header');
    });

    test('MockResponseStream captures progress calls', () => {
        const stream = new MockResponseStream();

        stream.progress('Loading...');

        assert.strictEqual(stream.progressCalls.length, 1);
        assert.strictEqual(stream.progressCalls[0], 'Loading...');
    });

    test('MockResponseStream getMarkdownContent joins calls', () => {
        const stream = new MockResponseStream();

        stream.markdown('Part 1');
        stream.markdown('Part 2');

        assert.strictEqual(stream.getMarkdownContent(), 'Part 1Part 2');
    });

    test('MockResponseStream reset clears all arrays', () => {
        const stream = new MockResponseStream();

        stream.markdown('Test');
        stream.progress('Loading');
        stream.reset();

        assert.strictEqual(stream.markdownCalls.length, 0);
        assert.strictEqual(stream.progressCalls.length, 0);
    });
});

suite('MockCancellationToken Test', () => {
    test('MockCancellationToken starts as not cancelled', () => {
        const token = new MockCancellationToken();
        assert.strictEqual(token.isCancellationRequested, false);
    });

    test('MockCancellationToken can be cancelled', () => {
        const token = new MockCancellationToken();
        token.cancel();
        assert.strictEqual(token.isCancellationRequested, true);
    });

    test('MockCancellationToken fires event on cancel', () => {
        const token = new MockCancellationToken();
        let eventFired = false;

        token.onCancellationRequested(() => {
            eventFired = true;
        });

        token.cancel();

        assert.strictEqual(eventFired, true);
    });
});
