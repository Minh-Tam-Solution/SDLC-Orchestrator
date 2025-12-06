"use strict";
/**
 * SDLC Orchestrator Error Utilities
 *
 * Provides centralized error handling, classification, and user-friendly
 * error messages for the VS Code extension.
 *
 * Sprint 27 Day 2 - Error Handling
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
exports.ValidationError = exports.ApiError = exports.AuthError = exports.NetworkError = exports.SDLCError = exports.ErrorCode = void 0;
exports.handleError = handleError;
exports.withErrorHandling = withErrorHandling;
exports.withRetry = withRetry;
exports.classifyError = classifyError;
exports.createNetworkError = createNetworkError;
exports.createAuthError = createAuthError;
exports.createApiError = createApiError;
const vscode = __importStar(require("vscode"));
const logger_1 = require("./logger");
/**
 * Error codes for classification
 */
var ErrorCode;
(function (ErrorCode) {
    // Network errors (1xx)
    ErrorCode[ErrorCode["NETWORK_ERROR"] = 100] = "NETWORK_ERROR";
    ErrorCode[ErrorCode["TIMEOUT"] = 101] = "TIMEOUT";
    ErrorCode[ErrorCode["CONNECTION_REFUSED"] = 102] = "CONNECTION_REFUSED";
    // Authentication errors (2xx)
    ErrorCode[ErrorCode["UNAUTHORIZED"] = 200] = "UNAUTHORIZED";
    ErrorCode[ErrorCode["TOKEN_EXPIRED"] = 201] = "TOKEN_EXPIRED";
    ErrorCode[ErrorCode["TOKEN_INVALID"] = 202] = "TOKEN_INVALID";
    ErrorCode[ErrorCode["FORBIDDEN"] = 203] = "FORBIDDEN";
    // API errors (3xx)
    ErrorCode[ErrorCode["NOT_FOUND"] = 300] = "NOT_FOUND";
    ErrorCode[ErrorCode["BAD_REQUEST"] = 301] = "BAD_REQUEST";
    ErrorCode[ErrorCode["CONFLICT"] = 302] = "CONFLICT";
    ErrorCode[ErrorCode["RATE_LIMITED"] = 303] = "RATE_LIMITED";
    ErrorCode[ErrorCode["SERVER_ERROR"] = 304] = "SERVER_ERROR";
    // Client errors (4xx)
    ErrorCode[ErrorCode["VALIDATION_ERROR"] = 400] = "VALIDATION_ERROR";
    ErrorCode[ErrorCode["CONFIGURATION_ERROR"] = 401] = "CONFIGURATION_ERROR";
    ErrorCode[ErrorCode["NO_PROJECT_SELECTED"] = 402] = "NO_PROJECT_SELECTED";
    // Unknown (9xx)
    ErrorCode[ErrorCode["UNKNOWN"] = 999] = "UNKNOWN";
})(ErrorCode || (exports.ErrorCode = ErrorCode = {}));
/**
 * Base error class for SDLC extension
 */
class SDLCError extends Error {
    code;
    originalError;
    context;
    constructor(code, message, originalError, context) {
        super(message);
        this.code = code;
        this.originalError = originalError;
        this.context = context;
        this.name = 'SDLCError';
    }
    /**
     * Gets user-friendly error message
     */
    getUserMessage() {
        return getErrorMessage(this.code, this.message);
    }
    /**
     * Checks if error is retryable
     */
    isRetryable() {
        return isRetryableError(this.code);
    }
    /**
     * Gets suggested action for the error
     */
    getSuggestedAction() {
        return getSuggestedAction(this.code);
    }
}
exports.SDLCError = SDLCError;
/**
 * Network-related error
 */
class NetworkError extends SDLCError {
    constructor(message, originalError) {
        super(ErrorCode.NETWORK_ERROR, message, originalError);
        this.name = 'NetworkError';
    }
}
exports.NetworkError = NetworkError;
/**
 * Authentication-related error
 */
class AuthError extends SDLCError {
    constructor(code, message, originalError) {
        super(code, message, originalError);
        this.name = 'AuthError';
    }
}
exports.AuthError = AuthError;
/**
 * API-related error
 */
class ApiError extends SDLCError {
    statusCode;
    responseData;
    constructor(statusCode, message, responseData) {
        super(httpStatusToErrorCode(statusCode), message, undefined, { statusCode, responseData });
        this.statusCode = statusCode;
        this.responseData = responseData;
        this.name = 'ApiError';
    }
}
exports.ApiError = ApiError;
/**
 * Validation error
 */
class ValidationError extends SDLCError {
    fieldErrors;
    constructor(message, fieldErrors) {
        super(ErrorCode.VALIDATION_ERROR, message, undefined, { fieldErrors });
        this.fieldErrors = fieldErrors;
        this.name = 'ValidationError';
    }
}
exports.ValidationError = ValidationError;
/**
 * Maps HTTP status code to error code
 */
function httpStatusToErrorCode(status) {
    switch (status) {
        case 400:
            return ErrorCode.BAD_REQUEST;
        case 401:
            return ErrorCode.UNAUTHORIZED;
        case 403:
            return ErrorCode.FORBIDDEN;
        case 404:
            return ErrorCode.NOT_FOUND;
        case 409:
            return ErrorCode.CONFLICT;
        case 429:
            return ErrorCode.RATE_LIMITED;
        case 500:
        case 502:
        case 503:
        case 504:
            return ErrorCode.SERVER_ERROR;
        default:
            return ErrorCode.UNKNOWN;
    }
}
/**
 * Gets user-friendly error message
 */
function getErrorMessage(code, technicalMessage) {
    switch (code) {
        case ErrorCode.NETWORK_ERROR:
            return 'Unable to connect to SDLC Orchestrator. Please check your network connection.';
        case ErrorCode.TIMEOUT:
            return 'Request timed out. The server may be experiencing high load.';
        case ErrorCode.CONNECTION_REFUSED:
            return 'Connection refused. Please ensure the SDLC Orchestrator backend is running.';
        case ErrorCode.UNAUTHORIZED:
            return 'Authentication required. Please log in to continue.';
        case ErrorCode.TOKEN_EXPIRED:
            return 'Your session has expired. Please log in again.';
        case ErrorCode.TOKEN_INVALID:
            return 'Invalid authentication token. Please log in again.';
        case ErrorCode.FORBIDDEN:
            return 'Access denied. You do not have permission to perform this action.';
        case ErrorCode.NOT_FOUND:
            return 'The requested resource was not found.';
        case ErrorCode.BAD_REQUEST:
            return `Invalid request: ${technicalMessage}`;
        case ErrorCode.CONFLICT:
            return 'A conflict occurred. The resource may have been modified.';
        case ErrorCode.RATE_LIMITED:
            return 'Too many requests. Please wait a moment and try again.';
        case ErrorCode.SERVER_ERROR:
            return 'Server error. The SDLC Orchestrator service is experiencing issues.';
        case ErrorCode.VALIDATION_ERROR:
            return `Validation error: ${technicalMessage}`;
        case ErrorCode.CONFIGURATION_ERROR:
            return `Configuration error: ${technicalMessage}`;
        case ErrorCode.NO_PROJECT_SELECTED:
            return 'No project selected. Please select a project first.';
        default:
            return technicalMessage || 'An unexpected error occurred.';
    }
}
/**
 * Checks if an error is retryable
 */
function isRetryableError(code) {
    return [
        ErrorCode.NETWORK_ERROR,
        ErrorCode.TIMEOUT,
        ErrorCode.CONNECTION_REFUSED,
        ErrorCode.SERVER_ERROR,
        ErrorCode.RATE_LIMITED,
    ].includes(code);
}
/**
 * Gets suggested action for an error
 */
function getSuggestedAction(code) {
    switch (code) {
        case ErrorCode.NETWORK_ERROR:
        case ErrorCode.CONNECTION_REFUSED:
            return 'Check your network connection and ensure the backend is running.';
        case ErrorCode.TIMEOUT:
            return 'Try again in a few seconds.';
        case ErrorCode.UNAUTHORIZED:
        case ErrorCode.TOKEN_EXPIRED:
        case ErrorCode.TOKEN_INVALID:
            return 'Run "SDLC: Login" to authenticate.';
        case ErrorCode.FORBIDDEN:
            return 'Contact your administrator for access.';
        case ErrorCode.NOT_FOUND:
            return 'Verify the resource exists and refresh the view.';
        case ErrorCode.RATE_LIMITED:
            return 'Wait 30 seconds before trying again.';
        case ErrorCode.SERVER_ERROR:
            return 'Wait a few minutes and try again. If the problem persists, check the backend logs.';
        case ErrorCode.NO_PROJECT_SELECTED:
            return 'Run "SDLC: Select Project" to choose a project.';
        case ErrorCode.CONFIGURATION_ERROR:
            return 'Check your extension settings.';
        default:
            return 'Try again or check the logs for more details.';
    }
}
/**
 * Default error handler options
 */
const DEFAULT_OPTIONS = {
    showNotification: true,
    notificationType: 'error',
    logError: true,
    includeActions: true,
};
/**
 * Handles an error with appropriate user feedback
 *
 * @param error - The error to handle
 * @param options - Handler options
 */
async function handleError(error, options = {}) {
    const opts = { ...DEFAULT_OPTIONS, ...options };
    const sdlcError = normalizeError(error);
    // Log the error
    if (opts.logError) {
        logger_1.Logger.error(`[${ErrorCode[sdlcError.code]}] ${sdlcError.message}` +
            (sdlcError.originalError
                ? ` | Original: ${sdlcError.originalError.message}`
                : ''));
    }
    // Show notification
    if (opts.showNotification) {
        const userMessage = sdlcError.getUserMessage();
        const actions = buildActions(sdlcError, opts);
        let selection;
        switch (opts.notificationType) {
            case 'warning':
                selection = await vscode.window.showWarningMessage(userMessage, ...actions);
                break;
            case 'info':
                selection = await vscode.window.showInformationMessage(userMessage, ...actions);
                break;
            case 'error':
            default:
                selection = await vscode.window.showErrorMessage(userMessage, ...actions);
        }
        // Handle action selection
        if (selection) {
            await handleActionSelection(selection, sdlcError, opts);
        }
    }
}
/**
 * Normalizes any error to SDLCError
 */
function normalizeError(error) {
    if (error instanceof SDLCError) {
        return error;
    }
    if (error instanceof Error) {
        // Check for network errors
        if (error.message.includes('ECONNREFUSED') ||
            error.message.includes('ENOTFOUND')) {
            return new NetworkError(error.message, error);
        }
        if (error.message.includes('ETIMEDOUT') || error.message.includes('timeout')) {
            return new SDLCError(ErrorCode.TIMEOUT, error.message, error);
        }
        return new SDLCError(ErrorCode.UNKNOWN, error.message, error);
    }
    return new SDLCError(ErrorCode.UNKNOWN, String(error));
}
/**
 * Builds action buttons for notification
 */
function buildActions(error, options) {
    const actions = [];
    if (!options.includeActions) {
        return actions;
    }
    // Add suggested action
    if (error.isRetryable()) {
        actions.push('Retry');
    }
    // Add login action for auth errors
    if ([ErrorCode.UNAUTHORIZED, ErrorCode.TOKEN_EXPIRED, ErrorCode.TOKEN_INVALID].includes(error.code)) {
        actions.push('Login');
    }
    // Add select project action
    if (error.code === ErrorCode.NO_PROJECT_SELECTED) {
        actions.push('Select Project');
    }
    // Add custom actions
    if (options.customActions) {
        actions.push(...options.customActions.map((a) => a.title));
    }
    // Always add "More Info" for detailed errors
    if (error.context || error.originalError) {
        actions.push('Show Details');
    }
    return actions;
}
/**
 * Handles action button selection
 */
async function handleActionSelection(selection, error, options) {
    switch (selection) {
        case 'Retry':
            // The caller should implement retry logic
            break;
        case 'Login':
            await vscode.commands.executeCommand('sdlc.login');
            break;
        case 'Select Project':
            await vscode.commands.executeCommand('sdlc.selectProject');
            break;
        case 'Show Details':
            showErrorDetails(error);
            break;
        default: {
            // Check custom actions
            const customAction = options.customActions?.find((a) => a.title === selection);
            if (customAction) {
                await vscode.commands.executeCommand(customAction.command, ...(customAction.args ?? []));
            }
            break;
        }
    }
}
/**
 * Shows detailed error information
 */
function showErrorDetails(error) {
    const outputChannel = vscode.window.createOutputChannel('SDLC Error Details');
    outputChannel.clear();
    outputChannel.appendLine('='.repeat(60));
    outputChannel.appendLine('SDLC Orchestrator - Error Details');
    outputChannel.appendLine('='.repeat(60));
    outputChannel.appendLine('');
    outputChannel.appendLine(`Error Code: ${error.code} (${ErrorCode[error.code]})`);
    outputChannel.appendLine(`Message: ${error.message}`);
    outputChannel.appendLine('');
    outputChannel.appendLine(`User Message: ${error.getUserMessage()}`);
    outputChannel.appendLine(`Suggested Action: ${error.getSuggestedAction()}`);
    outputChannel.appendLine(`Retryable: ${error.isRetryable() ? 'Yes' : 'No'}`);
    if (error.originalError) {
        outputChannel.appendLine('');
        outputChannel.appendLine('-'.repeat(60));
        outputChannel.appendLine('Original Error:');
        outputChannel.appendLine('-'.repeat(60));
        outputChannel.appendLine(`Name: ${error.originalError.name}`);
        outputChannel.appendLine(`Message: ${error.originalError.message}`);
        if (error.originalError.stack) {
            outputChannel.appendLine('');
            outputChannel.appendLine('Stack Trace:');
            outputChannel.appendLine(error.originalError.stack);
        }
    }
    if (error.context) {
        outputChannel.appendLine('');
        outputChannel.appendLine('-'.repeat(60));
        outputChannel.appendLine('Context:');
        outputChannel.appendLine('-'.repeat(60));
        outputChannel.appendLine(JSON.stringify(error.context, null, 2));
    }
    outputChannel.show();
}
/**
 * Wraps an async function with error handling
 *
 * @param fn - The async function to wrap
 * @param options - Error handler options
 */
function withErrorHandling(fn, options) {
    return async (...args) => {
        try {
            return await fn(...args);
        }
        catch (error) {
            await handleError(error, options);
            return undefined;
        }
    };
}
/**
 * Creates a retry wrapper for async functions
 *
 * @param fn - The async function to wrap
 * @param maxRetries - Maximum number of retries
 * @param delayMs - Delay between retries in milliseconds
 */
function withRetry(fn, maxRetries = 3, delayMs = 1000) {
    return async (...args) => {
        let lastError;
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await fn(...args);
            }
            catch (error) {
                lastError = error instanceof Error ? error : new Error(String(error));
                const sdlcError = normalizeError(error);
                if (!sdlcError.isRetryable() || attempt === maxRetries) {
                    throw error;
                }
                logger_1.Logger.warn(`Attempt ${attempt}/${maxRetries} failed, retrying in ${delayMs}ms...`);
                await sleep(delayMs * attempt); // Exponential backoff
            }
        }
        throw lastError;
    };
}
/**
 * Sleep helper
 */
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
/**
 * Classifies an error and returns an SDLCError
 *
 * @param error - The error to classify
 */
function classifyError(error) {
    if (error === null || error === undefined) {
        return new SDLCError(ErrorCode.UNKNOWN, 'Unknown error occurred');
    }
    if (error instanceof SDLCError) {
        return error;
    }
    // Handle axios-like errors with response
    if (typeof error === 'object' && error !== null) {
        const err = error;
        // Check for network error codes
        if (err.code === 'ECONNREFUSED') {
            return new SDLCError(ErrorCode.CONNECTION_REFUSED, 'Connection refused', undefined, { category: 'network' });
        }
        if (err.code === 'ETIMEDOUT' || err.code === 'TIMEOUT') {
            return new SDLCError(ErrorCode.TIMEOUT, 'Request timed out', undefined, {
                category: 'network',
            });
        }
        if (err.code === 'ENOTFOUND') {
            return new SDLCError(ErrorCode.NETWORK_ERROR, 'Network error', undefined, {
                category: 'network',
            });
        }
        // Check for HTTP response errors
        const response = err.response;
        if (response && typeof response.status === 'number') {
            const status = response.status;
            const code = httpStatusToErrorCode(status);
            const category = status === 401 || status === 403
                ? 'auth'
                : status >= 400 && status < 500
                    ? 'api'
                    : 'api';
            return new SDLCError(code, `HTTP ${status} error`, undefined, { category });
        }
    }
    // Handle string errors
    if (typeof error === 'string') {
        return new SDLCError(ErrorCode.UNKNOWN, error);
    }
    // Handle Error instances
    if (error instanceof Error) {
        return new SDLCError(ErrorCode.UNKNOWN, error.message, error);
    }
    return new SDLCError(ErrorCode.UNKNOWN, String(error));
}
// Extend SDLCError to support category
Object.defineProperty(SDLCError.prototype, 'category', {
    get: function () {
        const ctx = this.context;
        if (ctx && typeof ctx === 'object' && 'category' in ctx) {
            const ctxObj = ctx;
            return ctxObj.category ?? 'unknown';
        }
        return 'unknown';
    },
});
/**
 * Factory function to create a network error
 *
 * @param message - Error message
 * @param code - Error code (default: NETWORK_ERROR)
 */
function createNetworkError(message, code = ErrorCode.NETWORK_ERROR) {
    const error = new SDLCError(code, message, undefined, { category: 'network' });
    return error;
}
/**
 * Factory function to create an auth error
 *
 * @param message - Error message
 * @param code - Error code
 */
function createAuthError(message, code) {
    return new SDLCError(code, message, undefined, { category: 'auth' });
}
/**
 * Factory function to create an API error
 *
 * @param message - Error message
 * @param statusCode - HTTP status code
 */
function createApiError(message, statusCode) {
    const code = httpStatusToErrorCode(statusCode);
    const retryable = statusCode >= 500 || statusCode === 429;
    return new SDLCError(code, message, undefined, { category: 'api', retryable });
}
//# sourceMappingURL=errors.js.map