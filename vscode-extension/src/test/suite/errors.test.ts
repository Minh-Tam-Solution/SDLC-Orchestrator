/**
 * Error Utilities Unit Tests
 *
 * Sprint 27 Day 2 - Testing
 * @version 0.1.0
 */

import * as assert from 'assert';
import {
    SDLCError,
    ErrorCode,
    classifyError,
    createNetworkError,
    createAuthError,
    createApiError,
} from '../../utils/errors';

suite('SDLCError Test Suite', () => {
    test('SDLCError has correct properties', () => {
        const error = new SDLCError(
            ErrorCode.NETWORK_ERROR,
            'Test error message',
            undefined,
            { category: 'network' }
        );

        assert.strictEqual(error.message, 'Test error message');
        assert.strictEqual(error.code, ErrorCode.NETWORK_ERROR);
        assert.ok(error.isRetryable());
    });

    test('SDLCError is instance of Error', () => {
        const error = new SDLCError(ErrorCode.UNKNOWN, 'Test');
        assert.ok(error instanceof Error);
    });

    test('SDLCError has name property', () => {
        const error = new SDLCError(ErrorCode.UNKNOWN, 'Test');
        assert.strictEqual(error.name, 'SDLCError');
    });

    test('SDLCError getUserMessage returns user-friendly message', () => {
        const error = new SDLCError(
            ErrorCode.CONNECTION_REFUSED,
            'ECONNREFUSED 127.0.0.1:8000',
            undefined,
            { category: 'network' }
        );

        const userMessage = error.getUserMessage();
        assert.ok(userMessage);
        assert.ok(!userMessage.includes('ECONNREFUSED')); // Should be user-friendly
    });

    test('SDLCError stores original error', () => {
        const originalError = new Error('Original error');
        const error = new SDLCError(
            ErrorCode.UNKNOWN,
            'Wrapped error',
            originalError
        );

        assert.strictEqual(error.originalError, originalError);
    });
});

suite('ErrorCode Test Suite', () => {
    test('Network error codes are in 100 range', () => {
        const networkError = Number(ErrorCode.NETWORK_ERROR);
        const timeout = Number(ErrorCode.TIMEOUT);
        const connectionRefused = Number(ErrorCode.CONNECTION_REFUSED);
        assert.ok(networkError >= 100 && networkError < 200);
        assert.ok(timeout >= 100 && timeout < 200);
        assert.ok(connectionRefused >= 100 && connectionRefused < 200);
    });

    test('Auth error codes are in 200 range', () => {
        const unauthorized = Number(ErrorCode.UNAUTHORIZED);
        const tokenExpired = Number(ErrorCode.TOKEN_EXPIRED);
        const tokenInvalid = Number(ErrorCode.TOKEN_INVALID);
        const forbidden = Number(ErrorCode.FORBIDDEN);
        assert.ok(unauthorized >= 200 && unauthorized < 300);
        assert.ok(tokenExpired >= 200 && tokenExpired < 300);
        assert.ok(tokenInvalid >= 200 && tokenInvalid < 300);
        assert.ok(forbidden >= 200 && forbidden < 300);
    });

    test('API error codes are in 300 range', () => {
        const notFound = Number(ErrorCode.NOT_FOUND);
        const badRequest = Number(ErrorCode.BAD_REQUEST);
        const rateLimited = Number(ErrorCode.RATE_LIMITED);
        const serverError = Number(ErrorCode.SERVER_ERROR);
        assert.ok(notFound >= 300 && notFound < 400);
        assert.ok(badRequest >= 300 && badRequest < 400);
        assert.ok(rateLimited >= 300 && rateLimited < 400);
        assert.ok(serverError >= 300 && serverError < 400);
    });

    test('Client error codes are in 400 range', () => {
        const noProjectSelected = Number(ErrorCode.NO_PROJECT_SELECTED);
        assert.ok(noProjectSelected >= 400 && noProjectSelected < 500);
    });
});

suite('classifyError Test Suite', () => {
    test('classifyError handles network errors', () => {
        const error = { code: 'ECONNREFUSED' };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.CONNECTION_REFUSED);
        // Check category through context
        assert.ok(classified.context);
        assert.strictEqual((classified.context).category, 'network');
    });

    test('classifyError handles timeout errors', () => {
        const error = { code: 'ETIMEDOUT' };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.TIMEOUT);
    });

    test('classifyError handles 401 status', () => {
        const error = { response: { status: 401 } };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.UNAUTHORIZED);
        assert.ok(classified.context);
        assert.strictEqual((classified.context).category, 'auth');
    });

    test('classifyError handles 403 status', () => {
        const error = { response: { status: 403 } };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.FORBIDDEN);
    });

    test('classifyError handles 404 status', () => {
        const error = { response: { status: 404 } };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.NOT_FOUND);
        assert.ok(classified.context);
        assert.strictEqual((classified.context).category, 'api');
    });

    test('classifyError handles 429 status (rate limited)', () => {
        const error = { response: { status: 429 } };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.RATE_LIMITED);
    });

    test('classifyError handles 500 status', () => {
        const error = { response: { status: 500 } };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.SERVER_ERROR);
    });

    test('classifyError handles unknown errors', () => {
        const error = { message: 'Unknown error' };
        const classified = classifyError(error);

        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('classifyError handles string errors', () => {
        const classified = classifyError('Some error string');

        assert.strictEqual(classified.code, ErrorCode.UNKNOWN);
    });

    test('classifyError handles null/undefined', () => {
        const classified1 = classifyError(null);
        const classified2 = classifyError(undefined);

        assert.strictEqual(classified1.code, ErrorCode.UNKNOWN);
        assert.strictEqual(classified2.code, ErrorCode.UNKNOWN);
    });
});

suite('Error Factory Functions', () => {
    test('createNetworkError creates network category error', () => {
        const error = createNetworkError('Connection failed');

        assert.ok(error.context);
        assert.strictEqual((error.context).category, 'network');
        assert.ok(error.isRetryable());
    });

    test('createAuthError creates auth category error', () => {
        const error = createAuthError('Token expired', ErrorCode.TOKEN_EXPIRED);

        assert.ok(error.context);
        assert.strictEqual((error.context).category, 'auth');
        assert.strictEqual(error.code, ErrorCode.TOKEN_EXPIRED);
    });

    test('createApiError creates api category error', () => {
        const error = createApiError('Not found', 404);

        assert.ok(error.context);
        assert.strictEqual((error.context).category, 'api');
        assert.strictEqual(error.code, ErrorCode.NOT_FOUND);
    });

    test('createApiError handles 500 errors', () => {
        const error = createApiError('Server error', 500);

        assert.strictEqual(error.code, ErrorCode.SERVER_ERROR);
        assert.ok(error.isRetryable());
    });

    test('createApiError handles 400 errors', () => {
        const error = createApiError('Bad request', 400);

        assert.strictEqual(error.code, ErrorCode.BAD_REQUEST);
        assert.ok(!error.isRetryable());
    });
});

suite('Error Retryability', () => {
    test('Network errors are retryable', () => {
        const error = new SDLCError(ErrorCode.NETWORK_ERROR, 'Network');
        assert.ok(error.isRetryable());
    });

    test('Timeout errors are retryable', () => {
        const error = new SDLCError(ErrorCode.TIMEOUT, 'Timeout');
        assert.ok(error.isRetryable());
    });

    test('Server errors are retryable', () => {
        const error = new SDLCError(ErrorCode.SERVER_ERROR, 'Server error');
        assert.ok(error.isRetryable());
    });

    test('Rate limit errors are retryable', () => {
        const error = new SDLCError(ErrorCode.RATE_LIMITED, 'Rate limited');
        assert.ok(error.isRetryable());
    });

    test('Auth errors are not retryable', () => {
        const error = new SDLCError(ErrorCode.UNAUTHORIZED, 'Unauthorized');
        assert.ok(!error.isRetryable());
    });

    test('Bad request errors are not retryable', () => {
        const error = new SDLCError(ErrorCode.BAD_REQUEST, 'Bad request');
        assert.ok(!error.isRetryable());
    });

    test('Not found errors are not retryable', () => {
        const error = new SDLCError(ErrorCode.NOT_FOUND, 'Not found');
        assert.ok(!error.isRetryable());
    });
});

suite('Suggested Actions', () => {
    test('Connection refused suggests checking server', () => {
        const error = classifyError({ code: 'ECONNREFUSED' });
        const action = error.getSuggestedAction();

        assert.ok(action.toLowerCase().includes('backend') || action.toLowerCase().includes('running'));
    });

    test('Unauthorized suggests login', () => {
        const error = classifyError({ response: { status: 401 } });
        const action = error.getSuggestedAction();

        assert.ok(action.toLowerCase().includes('login') || action.toLowerCase().includes('authenticate'));
    });

    test('Rate limited suggests waiting', () => {
        const error = classifyError({ response: { status: 429 } });
        const action = error.getSuggestedAction();

        assert.ok(action.toLowerCase().includes('wait') || action.toLowerCase().includes('seconds'));
    });
});
