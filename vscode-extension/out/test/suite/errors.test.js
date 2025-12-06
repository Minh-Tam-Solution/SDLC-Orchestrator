"use strict";
/**
 * Error Utilities Unit Tests
 *
 * Sprint 27 Day 2 - Testing
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
suite('SDLCError Test Suite', () => {
    test('SDLCError has correct properties', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.NETWORK_ERROR, 'Test error message', undefined, { category: 'network' });
        assert.strictEqual(error.message, 'Test error message');
        assert.strictEqual(error.code, errors_1.ErrorCode.NETWORK_ERROR);
        assert.ok(error.isRetryable());
    });
    test('SDLCError is instance of Error', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Test');
        assert.ok(error instanceof Error);
    });
    test('SDLCError has name property', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Test');
        assert.strictEqual(error.name, 'SDLCError');
    });
    test('SDLCError getUserMessage returns user-friendly message', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.CONNECTION_REFUSED, 'ECONNREFUSED 127.0.0.1:8000', undefined, { category: 'network' });
        const userMessage = error.getUserMessage();
        assert.ok(userMessage);
        assert.ok(!userMessage.includes('ECONNREFUSED')); // Should be user-friendly
    });
    test('SDLCError stores original error', () => {
        const originalError = new Error('Original error');
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNKNOWN, 'Wrapped error', originalError);
        assert.strictEqual(error.originalError, originalError);
    });
});
suite('ErrorCode Test Suite', () => {
    test('Network error codes are in 100 range', () => {
        const networkError = Number(errors_1.ErrorCode.NETWORK_ERROR);
        const timeout = Number(errors_1.ErrorCode.TIMEOUT);
        const connectionRefused = Number(errors_1.ErrorCode.CONNECTION_REFUSED);
        assert.ok(networkError >= 100 && networkError < 200);
        assert.ok(timeout >= 100 && timeout < 200);
        assert.ok(connectionRefused >= 100 && connectionRefused < 200);
    });
    test('Auth error codes are in 200 range', () => {
        const unauthorized = Number(errors_1.ErrorCode.UNAUTHORIZED);
        const tokenExpired = Number(errors_1.ErrorCode.TOKEN_EXPIRED);
        const tokenInvalid = Number(errors_1.ErrorCode.TOKEN_INVALID);
        const forbidden = Number(errors_1.ErrorCode.FORBIDDEN);
        assert.ok(unauthorized >= 200 && unauthorized < 300);
        assert.ok(tokenExpired >= 200 && tokenExpired < 300);
        assert.ok(tokenInvalid >= 200 && tokenInvalid < 300);
        assert.ok(forbidden >= 200 && forbidden < 300);
    });
    test('API error codes are in 300 range', () => {
        const notFound = Number(errors_1.ErrorCode.NOT_FOUND);
        const badRequest = Number(errors_1.ErrorCode.BAD_REQUEST);
        const rateLimited = Number(errors_1.ErrorCode.RATE_LIMITED);
        const serverError = Number(errors_1.ErrorCode.SERVER_ERROR);
        assert.ok(notFound >= 300 && notFound < 400);
        assert.ok(badRequest >= 300 && badRequest < 400);
        assert.ok(rateLimited >= 300 && rateLimited < 400);
        assert.ok(serverError >= 300 && serverError < 400);
    });
    test('Client error codes are in 400 range', () => {
        const noProjectSelected = Number(errors_1.ErrorCode.NO_PROJECT_SELECTED);
        assert.ok(noProjectSelected >= 400 && noProjectSelected < 500);
    });
});
suite('classifyError Test Suite', () => {
    test('classifyError handles network errors', () => {
        const error = { code: 'ECONNREFUSED' };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.CONNECTION_REFUSED);
        // Check category through context
        assert.ok(classified.context);
        assert.strictEqual((classified.context).category, 'network');
    });
    test('classifyError handles timeout errors', () => {
        const error = { code: 'ETIMEDOUT' };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.TIMEOUT);
    });
    test('classifyError handles 401 status', () => {
        const error = { response: { status: 401 } };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNAUTHORIZED);
        assert.ok(classified.context);
        assert.strictEqual((classified.context).category, 'auth');
    });
    test('classifyError handles 403 status', () => {
        const error = { response: { status: 403 } };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.FORBIDDEN);
    });
    test('classifyError handles 404 status', () => {
        const error = { response: { status: 404 } };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.NOT_FOUND);
        assert.ok(classified.context);
        assert.strictEqual((classified.context).category, 'api');
    });
    test('classifyError handles 429 status (rate limited)', () => {
        const error = { response: { status: 429 } };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.RATE_LIMITED);
    });
    test('classifyError handles 500 status', () => {
        const error = { response: { status: 500 } };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.SERVER_ERROR);
    });
    test('classifyError handles unknown errors', () => {
        const error = { message: 'Unknown error' };
        const classified = (0, errors_1.classifyError)(error);
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('classifyError handles string errors', () => {
        const classified = (0, errors_1.classifyError)('Some error string');
        assert.strictEqual(classified.code, errors_1.ErrorCode.UNKNOWN);
    });
    test('classifyError handles null/undefined', () => {
        const classified1 = (0, errors_1.classifyError)(null);
        const classified2 = (0, errors_1.classifyError)(undefined);
        assert.strictEqual(classified1.code, errors_1.ErrorCode.UNKNOWN);
        assert.strictEqual(classified2.code, errors_1.ErrorCode.UNKNOWN);
    });
});
suite('Error Factory Functions', () => {
    test('createNetworkError creates network category error', () => {
        const error = (0, errors_1.createNetworkError)('Connection failed');
        assert.ok(error.context);
        assert.strictEqual((error.context).category, 'network');
        assert.ok(error.isRetryable());
    });
    test('createAuthError creates auth category error', () => {
        const error = (0, errors_1.createAuthError)('Token expired', errors_1.ErrorCode.TOKEN_EXPIRED);
        assert.ok(error.context);
        assert.strictEqual((error.context).category, 'auth');
        assert.strictEqual(error.code, errors_1.ErrorCode.TOKEN_EXPIRED);
    });
    test('createApiError creates api category error', () => {
        const error = (0, errors_1.createApiError)('Not found', 404);
        assert.ok(error.context);
        assert.strictEqual((error.context).category, 'api');
        assert.strictEqual(error.code, errors_1.ErrorCode.NOT_FOUND);
    });
    test('createApiError handles 500 errors', () => {
        const error = (0, errors_1.createApiError)('Server error', 500);
        assert.strictEqual(error.code, errors_1.ErrorCode.SERVER_ERROR);
        assert.ok(error.isRetryable());
    });
    test('createApiError handles 400 errors', () => {
        const error = (0, errors_1.createApiError)('Bad request', 400);
        assert.strictEqual(error.code, errors_1.ErrorCode.BAD_REQUEST);
        assert.ok(!error.isRetryable());
    });
});
suite('Error Retryability', () => {
    test('Network errors are retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.NETWORK_ERROR, 'Network');
        assert.ok(error.isRetryable());
    });
    test('Timeout errors are retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.TIMEOUT, 'Timeout');
        assert.ok(error.isRetryable());
    });
    test('Server errors are retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.SERVER_ERROR, 'Server error');
        assert.ok(error.isRetryable());
    });
    test('Rate limit errors are retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.RATE_LIMITED, 'Rate limited');
        assert.ok(error.isRetryable());
    });
    test('Auth errors are not retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.UNAUTHORIZED, 'Unauthorized');
        assert.ok(!error.isRetryable());
    });
    test('Bad request errors are not retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.BAD_REQUEST, 'Bad request');
        assert.ok(!error.isRetryable());
    });
    test('Not found errors are not retryable', () => {
        const error = new errors_1.SDLCError(errors_1.ErrorCode.NOT_FOUND, 'Not found');
        assert.ok(!error.isRetryable());
    });
});
suite('Suggested Actions', () => {
    test('Connection refused suggests checking server', () => {
        const error = (0, errors_1.classifyError)({ code: 'ECONNREFUSED' });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('backend') || action.toLowerCase().includes('running'));
    });
    test('Unauthorized suggests login', () => {
        const error = (0, errors_1.classifyError)({ response: { status: 401 } });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('login') || action.toLowerCase().includes('authenticate'));
    });
    test('Rate limited suggests waiting', () => {
        const error = (0, errors_1.classifyError)({ response: { status: 429 } });
        const action = error.getSuggestedAction();
        assert.ok(action.toLowerCase().includes('wait') || action.toLowerCase().includes('seconds'));
    });
});
//# sourceMappingURL=errors.test.js.map