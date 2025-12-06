/**
 * Error Handling Integration Tests
 *
 * Tests for error handling flows across views and services
 *
 * Sprint 27 Day 4 - Integration Testing
 * @version 0.1.0
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import {
    SDLCError,
    ErrorCode,
    classifyError,
    createNetworkError,
    createAuthError,
    createApiError,
} from '../../utils/errors';
import { CacheService } from '../../services/cacheService';
import { MockGlobalState, createMockExtensionContext } from './testHelpers';

function createMockContext(globalState: MockGlobalState): vscode.ExtensionContext {
    return createMockExtensionContext({ globalState });
}

suite('Error Classification Integration', () => {
    test('Network errors from fetch failures', () => {
        // Simulate fetch error
        const fetchError = {
            code: 'ECONNREFUSED',
            message: 'connect ECONNREFUSED 127.0.0.1:8000',
        };

        const classified = classifyError(fetchError);

        assert.strictEqual(classified.code, ErrorCode.CONNECTION_REFUSED);
        assert.ok(classified.isRetryable());
        assert.ok(classified.getUserMessage().toLowerCase().includes('backend'));
    });

    test('Timeout errors from slow network', () => {
        const timeoutError = {
            code: 'ETIMEDOUT',
            message: 'network timeout at: http://localhost:8000',
        };

        const classified = classifyError(timeoutError);

        assert.strictEqual(classified.code, ErrorCode.TIMEOUT);
        assert.ok(classified.isRetryable());
    });

    test('DNS resolution failures', () => {
        const dnsError = {
            code: 'ENOTFOUND',
            message: 'getaddrinfo ENOTFOUND api.example.com',
        };

        const classified = classifyError(dnsError);

        assert.strictEqual(classified.code, ErrorCode.NETWORK_ERROR);
    });

    test('401 from expired token', () => {
        const authError = {
            response: {
                status: 401,
                data: { detail: 'Token has expired' },
            },
        };

        const classified = classifyError(authError);

        assert.strictEqual(classified.code, ErrorCode.UNAUTHORIZED);
        assert.ok(!classified.isRetryable());
        assert.ok(classified.getSuggestedAction().toLowerCase().includes('login'));
    });

    test('403 from insufficient permissions', () => {
        const forbiddenError = {
            response: {
                status: 403,
                data: { detail: 'Insufficient permissions' },
            },
        };

        const classified = classifyError(forbiddenError);

        assert.strictEqual(classified.code, ErrorCode.FORBIDDEN);
        assert.ok(!classified.isRetryable());
    });

    test('404 from missing resource', () => {
        const notFoundError = {
            response: {
                status: 404,
                data: { detail: 'Project not found' },
            },
        };

        const classified = classifyError(notFoundError);

        assert.strictEqual(classified.code, ErrorCode.NOT_FOUND);
        assert.ok(!classified.isRetryable());
    });

    test('422 validation error', () => {
        const validationError = {
            response: {
                status: 422,
                data: {
                    detail: [
                        { loc: ['body', 'name'], msg: 'field required' },
                    ],
                },
            },
        };

        const classified = classifyError(validationError);

        // 422 is typically classified as BAD_REQUEST
        assert.ok(classified.code === ErrorCode.BAD_REQUEST || classified.code === ErrorCode.UNKNOWN);
    });

    test('429 rate limiting', () => {
        const rateLimitError = {
            response: {
                status: 429,
                data: { detail: 'Rate limit exceeded' },
                headers: { 'retry-after': '60' },
            },
        };

        const classified = classifyError(rateLimitError);

        assert.strictEqual(classified.code, ErrorCode.RATE_LIMITED);
        assert.ok(classified.isRetryable());
        assert.ok(classified.getSuggestedAction().toLowerCase().includes('wait'));
    });

    test('500 server error', () => {
        const serverError = {
            response: {
                status: 500,
                data: { detail: 'Internal server error' },
            },
        };

        const classified = classifyError(serverError);

        assert.strictEqual(classified.code, ErrorCode.SERVER_ERROR);
        assert.ok(classified.isRetryable());
    });

    test('502 bad gateway', () => {
        const badGatewayError = {
            response: {
                status: 502,
                data: { message: 'Bad gateway' },
            },
        };

        const classified = classifyError(badGatewayError);

        assert.strictEqual(classified.code, ErrorCode.SERVER_ERROR);
        assert.ok(classified.isRetryable());
    });

    test('503 service unavailable', () => {
        const unavailableError = {
            response: {
                status: 503,
                data: { message: 'Service temporarily unavailable' },
            },
        };

        const classified = classifyError(unavailableError);

        assert.strictEqual(classified.code, ErrorCode.SERVER_ERROR);
        assert.ok(classified.isRetryable());
    });
});

suite('Error User Messages', () => {
    test('Network error has friendly message', () => {
        const error = createNetworkError('ECONNREFUSED 127.0.0.1:8000');
        const message = error.getUserMessage();

        // Should not contain technical details
        assert.ok(!message.includes('ECONNREFUSED'));
        assert.ok(!message.includes('127.0.0.1'));
    });

    test('Auth error has friendly message', () => {
        const error = createAuthError('JWT token validation failed', ErrorCode.TOKEN_INVALID);
        const message = error.getUserMessage();

        // Should not contain JWT details
        assert.ok(!message.includes('JWT'));
    });

    test('Server error has friendly message', () => {
        const error = createApiError('NullPointerException at line 42', 500);
        const message = error.getUserMessage();

        // Should not contain stack trace
        assert.ok(!message.includes('NullPointerException'));
        assert.ok(!message.includes('line 42'));
    });

    test('User messages are actionable', () => {
        const networkError = createNetworkError('Connection failed');
        const authError = createAuthError('Unauthorized', ErrorCode.UNAUTHORIZED);
        const serverError = createApiError('Internal error', 500);

        // Each error type should have a suggested action
        assert.ok(networkError.getSuggestedAction().length > 0);
        assert.ok(authError.getSuggestedAction().length > 0);
        assert.ok(serverError.getSuggestedAction().length > 0);
    });
});

suite('Error with Cache Fallback Integration', () => {
    let cacheService: CacheService;
    let mockGlobalState: MockGlobalState;
    let mockContext: vscode.ExtensionContext;

    setup(() => {
        mockGlobalState = new MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new CacheService(mockContext);
    });

    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });

    test('Cache fallback on network error', async () => {
        // Pre-populate cache
        const cachedData = [{ id: '1', name: 'Cached Item' }];
        await cacheService.set('fallback-test', cachedData);

        // Simulate network error
        const networkError = createNetworkError('Connection refused');

        // In real scenario, view would:
        // 1. Catch the error
        // 2. Classify it
        // 3. Check if it's retryable
        // 4. Fall back to cache

        const classified = classifyError(networkError);
        assert.ok(classified.isRetryable());

        // Get cached data as fallback
        const cached = cacheService.get('fallback-test');
        assert.ok(cached);
        assert.deepStrictEqual(cached.data, cachedData);
    });

    test('No cache fallback on auth error', async () => {
        // Pre-populate cache
        const cachedData = [{ id: '1', name: 'Sensitive Item' }];
        await cacheService.set('auth-test', cachedData);

        // Auth errors should NOT use cache (user needs to re-authenticate)
        const authError = createAuthError('Token expired', ErrorCode.TOKEN_EXPIRED);
        const classified = classifyError(authError);

        assert.ok(!classified.isRetryable());
        // Application should redirect to login, not serve cached data
    });

    test('Cache provides offline indicator data', async () => {
        const cachedData = { offline: false, items: ['a', 'b'] };
        await cacheService.set('offline-indicator', cachedData);

        const result = cacheService.get('offline-indicator');
        assert.ok(result);
        assert.strictEqual(result.isCached, true);
        // View can use isCached to show offline indicator
    });
});

suite('Error Suggested Actions', () => {
    test('Connection refused suggests starting backend', () => {
        const error = classifyError({ code: 'ECONNREFUSED' });
        const action = error.getSuggestedAction();

        assert.ok(
            action.toLowerCase().includes('backend') ||
            action.toLowerCase().includes('running') ||
            action.toLowerCase().includes('start')
        );
    });

    test('Timeout suggests retry', () => {
        const error = classifyError({ code: 'ETIMEDOUT' });
        const action = error.getSuggestedAction();

        assert.ok(
            action.toLowerCase().includes('retry') ||
            action.toLowerCase().includes('try again') ||
            action.toLowerCase().includes('check')
        );
    });

    test('Unauthorized suggests login', () => {
        const error = classifyError({ response: { status: 401 } });
        const action = error.getSuggestedAction();

        assert.ok(
            action.toLowerCase().includes('login') ||
            action.toLowerCase().includes('sign in') ||
            action.toLowerCase().includes('authenticate')
        );
    });

    test('Forbidden suggests permissions', () => {
        const error = classifyError({ response: { status: 403 } });
        const action = error.getSuggestedAction();

        assert.ok(
            action.toLowerCase().includes('permission') ||
            action.toLowerCase().includes('access') ||
            action.toLowerCase().includes('admin')
        );
    });

    test('Not found suggests checking resource', () => {
        const error = classifyError({ response: { status: 404 } });
        const action = error.getSuggestedAction();

        assert.ok(
            action.toLowerCase().includes('exist') ||
            action.toLowerCase().includes('check') ||
            action.toLowerCase().includes('resource')
        );
    });

    test('Server error suggests retry later', () => {
        const error = classifyError({ response: { status: 500 } });
        const action = error.getSuggestedAction();

        assert.ok(
            action.toLowerCase().includes('retry') ||
            action.toLowerCase().includes('later') ||
            action.toLowerCase().includes('try again')
        );
    });
});

suite('Error Context Preservation', () => {
    test('SDLCError preserves error context', () => {
        const context = {
            category: 'network',
            endpoint: '/api/v1/projects',
            method: 'GET',
        };

        const error = new SDLCError(
            ErrorCode.NETWORK_ERROR,
            'Request failed',
            undefined,
            context
        );

        assert.deepStrictEqual(error.context, context);
    });

    test('SDLCError preserves original error', () => {
        const original = new Error('Original error');
        original.name = 'OriginalError';

        const wrapped = new SDLCError(
            ErrorCode.UNKNOWN,
            'Wrapped error',
            original
        );

        assert.strictEqual(wrapped.originalError, original);
        assert.strictEqual(wrapped.originalError?.name, 'OriginalError');
    });

    test('classifyError extracts HTTP status', () => {
        const error = {
            response: {
                status: 404,
                statusText: 'Not Found',
            },
        };

        const classified = classifyError(error);
        assert.strictEqual(classified.code, ErrorCode.NOT_FOUND);
    });
});

suite('Error Type Guards', () => {
    test('isRetryable returns true for network errors', () => {
        const errors = [
            new SDLCError(ErrorCode.NETWORK_ERROR, 'Network'),
            new SDLCError(ErrorCode.TIMEOUT, 'Timeout'),
            new SDLCError(ErrorCode.CONNECTION_REFUSED, 'Refused'),
            new SDLCError(ErrorCode.SERVER_ERROR, 'Server'),
            new SDLCError(ErrorCode.RATE_LIMITED, 'Rate'),
        ];

        for (const error of errors) {
            assert.ok(error.isRetryable(), `${ErrorCode[error.code]} should be retryable`);
        }
    });

    test('isRetryable returns false for client errors', () => {
        const errors = [
            new SDLCError(ErrorCode.UNAUTHORIZED, 'Unauth'),
            new SDLCError(ErrorCode.FORBIDDEN, 'Forbidden'),
            new SDLCError(ErrorCode.NOT_FOUND, 'Not found'),
            new SDLCError(ErrorCode.BAD_REQUEST, 'Bad req'),
            new SDLCError(ErrorCode.NO_PROJECT_SELECTED, 'No project'),
        ];

        for (const error of errors) {
            assert.ok(!error.isRetryable(), `${ErrorCode[error.code]} should not be retryable`);
        }
    });
});

suite('Error Handling Edge Cases', () => {
    test('classifyError handles null', () => {
        const classified = classifyError(null);
        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('classifyError handles undefined', () => {
        const classified = classifyError(undefined);
        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('classifyError handles string', () => {
        const classified = classifyError('Something went wrong');
        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('classifyError handles number', () => {
        const classified = classifyError(404);
        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('classifyError handles empty object', () => {
        const classified = classifyError({});
        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('SDLCError without context', () => {
        const error = new SDLCError(ErrorCode.UNKNOWN, 'Test');
        assert.strictEqual(error.context, undefined);
    });

    test('SDLCError getUserMessage never throws', () => {
        const error = new SDLCError(ErrorCode.UNKNOWN, 'Test');
        let threw = false;

        try {
            error.getUserMessage();
        } catch {
            threw = true;
        }

        assert.ok(!threw);
    });

    test('SDLCError getSuggestedAction never throws', () => {
        const error = new SDLCError(ErrorCode.UNKNOWN, 'Test');
        let threw = false;

        try {
            error.getSuggestedAction();
        } catch {
            threw = true;
        }

        assert.ok(!threw);
    });
});

suite('Error Factory Functions', () => {
    test('createNetworkError sets correct category', () => {
        const error = createNetworkError('Failed');
        const context = error.context as Record<string, unknown>;

        assert.ok(context);
        assert.strictEqual(context.category, 'network');
    });

    test('createAuthError sets correct category', () => {
        const error = createAuthError('Failed', ErrorCode.UNAUTHORIZED);
        const context = error.context as Record<string, unknown>;

        assert.ok(context);
        assert.strictEqual(context.category, 'auth');
    });

    test('createApiError sets correct category', () => {
        const error = createApiError('Failed', 404);
        const context = error.context as Record<string, unknown>;

        assert.ok(context);
        assert.strictEqual(context.category, 'api');
    });

    test('createApiError maps status codes correctly', () => {
        const statusMap: Array<[number, ErrorCode]> = [
            [400, ErrorCode.BAD_REQUEST],
            [401, ErrorCode.UNAUTHORIZED],
            [403, ErrorCode.FORBIDDEN],
            [404, ErrorCode.NOT_FOUND],
            [429, ErrorCode.RATE_LIMITED],
            [500, ErrorCode.SERVER_ERROR],
            [502, ErrorCode.SERVER_ERROR],
            [503, ErrorCode.SERVER_ERROR],
        ];

        for (const [status, expectedCode] of statusMap) {
            const error = createApiError(`Error ${status}`, status);
            assert.strictEqual(
                error.code,
                expectedCode,
                `Status ${status} should map to ${ErrorCode[expectedCode]}`
            );
        }
    });
});
