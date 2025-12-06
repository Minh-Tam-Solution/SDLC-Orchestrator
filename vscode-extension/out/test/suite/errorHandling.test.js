"use strict";
/**
 * Error Handling Integration Tests
 *
 * Tests for error handling flows across views and services
 *
 * Sprint 27 Day 4 - Integration Testing
 * @version 0.1.0
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const assert = __importStar(require("assert"));
const errors_1 = require("../../utils/errors");
const cacheService_1 = require("../../services/cacheService");
const testHelpers_1 = require("./testHelpers");
function createMockContext(globalState) {
    return (0, testHelpers_1.createMockExtensionContext)({ globalState });
}
suite('Error Classification Integration', () => {
    test('Network errors from fetch failures', () => {
        // Simulate fetch error
        const fetchError = {
            code: 'ECONNREFUSED',
            message: 'connect ECONNREFUSED 127.0.0.1:8000',
        };
        const classified = (0, errors_1.classifyError)(fetchError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.CONNECTION_REFUSED);
        assert.ok(classified.isRetryable());
        assert.ok(classified.getUserMessage().toLowerCase().includes('backend'));
    });
    test('Timeout errors from slow network', () => {
        const timeoutError = {
            code: 'ETIMEDOUT',
            message: 'network timeout at: http://localhost:8000',
        };
        const classified = (0, errors_1.classifyError)(timeoutError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.TIMEOUT);
        assert.ok(classified.isRetryable());
    });
    test('DNS resolution failures', () => {
        const dnsError = {
            code: 'ENOTFOUND',
            message: 'getaddrinfo ENOTFOUND api.example.com',
        };
        const classified = (0, errors_1.classifyError)(dnsError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.NETWORK_ERROR);
    });
    test('401 from expired token', () => {
        const authError = {
            response: {
                status: 401,
                data: { detail: 'Token has expired' },
            },
        };
        const classified = (0, errors_1.classifyError)(authError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNAUTHORIZED);
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
        const classified = (0, errors_1.classifyError)(forbiddenError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.FORBIDDEN);
        assert.ok(!classified.isRetryable());
    });
    test('404 from missing resource', () => {
        const notFoundError = {
            response: {
                status: 404,
                data: { detail: 'Project not found' },
            },
        };
        const classified = (0, errors_1.classifyError)(notFoundError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.NOT_FOUND);
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
        const classified = (0, errors_1.classifyError)(validationError);
        // 422 is typically classified as BAD_REQUEST
        assert.ok(classified.code === errors_1.ErrorCode.BAD_REQUEST || classified.code === errors_1.ErrorCode.UNKNOWN);
    });
    test('429 rate limiting', () => {
        const rateLimitError = {
            response: {
                status: 429,
                data: { detail: 'Rate limit exceeded' },
                headers: { 'retry-after': '60' },
            },
        };
        const classified = (0, errors_1.classifyError)(rateLimitError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.RATE_LIMITED);
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
        const classified = (0, errors_1.classifyError)(serverError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.SERVER_ERROR);
        assert.ok(classified.isRetryable());
    });
    test('502 bad gateway', () => {
        const badGatewayError = {
            response: {
                status: 502,
                data: { message: 'Bad gateway' },
            },
        };
        const classified = (0, errors_1.classifyError)(badGatewayError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.SERVER_ERROR);
        assert.ok(classified.isRetryable());
    });
    test('503 service unavailable', () => {
        const unavailableError = {
            response: {
                status: 503,
                data: { message: 'Service temporarily unavailable' },
            },
        };
        const classified = (0, errors_1.classifyError)(unavailableError);
        assert.strictEqual(classified.code, errors_1.ErrorCode.SERVER_ERROR);
        assert.ok(classified.isRetryable());
    });
});
suite('Error User Messages', () => {
    test('Network error has friendly message', () => {
        const error = (0, errors_1.createNetworkError)('ECONNREFUSED 127.0.0.1:8000');
        const message = error.getUserMessage();
        // Should not contain technical details
        assert.ok(!message.includes('ECONNREFUSED'));
        assert.ok(!message.includes('127.0.0.1'));
    });
    test('Auth error has friendly message', () => {
        const error = (0, errors_1.createAuthError)('JWT token validation failed', errors_1.ErrorCode.TOKEN_INVALID);
        const message = error.getUserMessage();
        // Should not contain JWT details
        assert.ok(!message.includes('JWT'));
    });
    test('Server error has friendly message', () => {
        const error = (0, errors_1.createApiError)('NullPointerException at line 42', 500);
        const message = error.getUserMessage();
        // Should not contain stack trace
        assert.ok(!message.includes('NullPointerException'));
        assert.ok(!message.includes('line 42'));
    });
    test('User messages are actionable', () => {
        const networkError = (0, errors_1.createNetworkError)('Connection failed');
        const authError = (0, errors_1.createAuthError)('Unauthorized', errors_1.ErrorCode.UNAUTHORIZED);
        const serverError = (0, errors_1.createApiError)('Internal error', 500);
        // Each error type should have a suggested action
        assert.ok(networkError.getSuggestedAction().length > 0);
        assert.ok(authError.getSuggestedAction().length > 0);
        assert.ok(serverError.getSuggestedAction().length > 0);
    });
});
suite('Error with Cache Fallback Integration', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    setup(() => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
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
        const networkError = (0, errors_1.createNetworkError)('Connection refused');
        // In real scenario, view would:
        // 1. Catch the error
        // 2. Classify it
        // 3. Check if it's retryable
        // 4. Fall back to cache
        const classified = (0, errors_1.classifyError)(networkError);
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
        const authError = (0, errors_1.createAuthError)('Token expired', errors_1.ErrorCode.TOKEN_EXPIRED);
        const classified = (0, errors_1.classifyError)(authError);
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
        const error = (0, errors_1.classifyError)({ code: 'ECONNREFUSED' });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('backend') ||
            action.toLowerCase().includes('running') ||
            action.toLowerCase().includes('start'));
    });
    test('Timeout suggests retry', () => {
        const error = (0, errors_1.classifyError)({ code: 'ETIMEDOUT' });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('retry') ||
            action.toLowerCase().includes('try again') ||
            action.toLowerCase().includes('check'));
    });
    test('Unauthorized suggests login', () => {
        const error = (0, errors_1.classifyError)({ response: { status: 401 } });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('login') ||
            action.toLowerCase().includes('sign in') ||
            action.toLowerCase().includes('authenticate'));
    });
    test('Forbidden suggests permissions', () => {
        const error = (0, errors_1.classifyError)({ response: { status: 403 } });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('permission') ||
            action.toLowerCase().includes('access') ||
            action.toLowerCase().includes('admin'));
    });
    test('Not found suggests checking resource', () => {
        const error = (0, errors_1.classifyError)({ response: { status: 404 } });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('exist') ||
            action.toLowerCase().includes('check') ||
            action.toLowerCase().includes('resource'));
    });
    test('Server error suggests retry later', () => {
        const error = (0, errors_1.classifyError)({ response: { status: 500 } });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('retry') ||
            action.toLowerCase().includes('later') ||
            action.toLowerCase().includes('try again'));
    });
});
suite('Error Context Preservation', () => {
    test('SDLCError preserves error context', () => {
        const context = {
            category: 'network',
            endpoint: '/api/v1/projects',
            method: 'GET',
        };
        const error = new errors_1.SDLCError(errors_1.ErrorCode.NETWORK_ERROR, 'Request failed', undefined, context);
        assert.deepStrictEqual(error.context, context);
    });
    test('SDLCError preserves original error', () => {
        const original = new Error('Original error');
        original.name = 'OriginalError';
        const wrapped = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Wrapped error', original);
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
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.NOT_FOUND);
    });
});
suite('Error Type Guards', () => {
    test('isRetryable returns true for network errors', () => {
        const errors = [
            new errors_1.SDLCError(errors_1.ErrorCode.NETWORK_ERROR, 'Network'),
            new errors_1.SDLCError(errors_1.ErrorCode.TIMEOUT, 'Timeout'),
            new errors_1.SDLCError(errors_1.ErrorCode.CONNECTION_REFUSED, 'Refused'),
            new errors_1.SDLCError(errors_1.ErrorCode.SERVER_ERROR, 'Server'),
            new errors_1.SDLCError(errors_1.ErrorCode.RATE_LIMITED, 'Rate'),
        ];
        for (const error of errors) {
            assert.ok(error.isRetryable(), `${errors_1.ErrorCode[error.code]} should be retryable`);
        }
    });
    test('isRetryable returns false for client errors', () => {
        const errors = [
            new errors_1.SDLCError(errors_1.ErrorCode.UNAUTHORIZED, 'Unauth'),
            new errors_1.SDLCError(errors_1.ErrorCode.FORBIDDEN, 'Forbidden'),
            new errors_1.SDLCError(errors_1.ErrorCode.NOT_FOUND, 'Not found'),
            new errors_1.SDLCError(errors_1.ErrorCode.BAD_REQUEST, 'Bad req'),
            new errors_1.SDLCError(errors_1.ErrorCode.NO_PROJECT_SELECTED, 'No project'),
        ];
        for (const error of errors) {
            assert.ok(!error.isRetryable(), `${errors_1.ErrorCode[error.code]} should not be retryable`);
        }
    });
});
suite('Error Handling Edge Cases', () => {
    test('classifyError handles null', () => {
        const classified = (0, errors_1.classifyError)(null);
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('classifyError handles undefined', () => {
        const classified = (0, errors_1.classifyError)(undefined);
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('classifyError handles string', () => {
        const classified = (0, errors_1.classifyError)('Something went wrong');
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('classifyError handles number', () => {
        const classified = (0, errors_1.classifyError)(404);
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('classifyError handles empty object', () => {
        const classified = (0, errors_1.classifyError)({});
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('SDLCError without context', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Test');
        assert.strictEqual(error.context, undefined);
    });
    test('SDLCError getUserMessage never throws', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Test');
        let threw = false;
        try {
            error.getUserMessage();
        }
        catch {
            threw = true;
        }
        assert.ok(!threw);
    });
    test('SDLCError getSuggestedAction never throws', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Test');
        let threw = false;
        try {
            error.getSuggestedAction();
        }
        catch {
            threw = true;
        }
        assert.ok(!threw);
    });
});
suite('Error Factory Functions', () => {
    test('createNetworkError sets correct category', () => {
        const error = (0, errors_1.createNetworkError)('Failed');
        const context = error.context;
        assert.ok(context);
        assert.strictEqual(context.category, 'network');
    });
    test('createAuthError sets correct category', () => {
        const error = (0, errors_1.createAuthError)('Failed', errors_1.ErrorCode.UNAUTHORIZED);
        const context = error.context;
        assert.ok(context);
        assert.strictEqual(context.category, 'auth');
    });
    test('createApiError sets correct category', () => {
        const error = (0, errors_1.createApiError)('Failed', 404);
        const context = error.context;
        assert.ok(context);
        assert.strictEqual(context.category, 'api');
    });
    test('createApiError maps status codes correctly', () => {
        const statusMap = [
            [400, errors_1.ErrorCode.BAD_REQUEST],
            [401, errors_1.ErrorCode.UNAUTHORIZED],
            [403, errors_1.ErrorCode.FORBIDDEN],
            [404, errors_1.ErrorCode.NOT_FOUND],
            [429, errors_1.ErrorCode.RATE_LIMITED],
            [500, errors_1.ErrorCode.SERVER_ERROR],
            [502, errors_1.ErrorCode.SERVER_ERROR],
            [503, errors_1.ErrorCode.SERVER_ERROR],
        ];
        for (const [status, expectedCode] of statusMap) {
            const error = (0, errors_1.createApiError)(`Error ${status}`, status);
            assert.strictEqual(error.code, expectedCode, `Status ${status} should map to ${errors_1.ErrorCode[expectedCode]}`);
        }
    });
});
//# sourceMappingURL=errorHandling.test.js.map