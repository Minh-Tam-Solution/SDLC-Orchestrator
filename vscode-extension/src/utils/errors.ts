/**
 * SDLC Orchestrator Error Utilities
 *
 * Provides centralized error handling, classification, and user-friendly
 * error messages for the VS Code extension.
 *
 * Sprint 27 Day 2 - Error Handling
 * @version 0.1.0
 */

import * as vscode from 'vscode';
import { Logger } from './logger';

/**
 * Error codes for classification
 */
export enum ErrorCode {
    // Network errors (1xx)
    NETWORK_ERROR = 100,
    TIMEOUT = 101,
    CONNECTION_REFUSED = 102,

    // Authentication errors (2xx)
    UNAUTHORIZED = 200,
    TOKEN_EXPIRED = 201,
    TOKEN_INVALID = 202,
    FORBIDDEN = 203,

    // API errors (3xx)
    NOT_FOUND = 300,
    BAD_REQUEST = 301,
    CONFLICT = 302,
    RATE_LIMITED = 303,
    SERVER_ERROR = 304,

    // Client errors (4xx)
    VALIDATION_ERROR = 400,
    CONFIGURATION_ERROR = 401,
    NO_PROJECT_SELECTED = 402,

    // Unknown (9xx)
    UNKNOWN = 999,
}

/**
 * Base error class for SDLC extension
 */
export class SDLCError extends Error {
    constructor(
        public readonly code: ErrorCode,
        message: string,
        public readonly originalError?: Error,
        public readonly context?: Record<string, unknown>
    ) {
        super(message);
        this.name = 'SDLCError';
    }

    /**
     * Gets user-friendly error message
     */
    getUserMessage(): string {
        return getErrorMessage(this.code, this.message);
    }

    /**
     * Checks if error is retryable
     */
    isRetryable(): boolean {
        return isRetryableError(this.code);
    }

    /**
     * Gets suggested action for the error
     */
    getSuggestedAction(): string {
        return getSuggestedAction(this.code);
    }
}

/**
 * Network-related error
 */
export class NetworkError extends SDLCError {
    constructor(message: string, originalError?: Error) {
        super(ErrorCode.NETWORK_ERROR, message, originalError);
        this.name = 'NetworkError';
    }
}

/**
 * Authentication-related error
 */
export class AuthError extends SDLCError {
    constructor(code: ErrorCode, message: string, originalError?: Error) {
        super(code, message, originalError);
        this.name = 'AuthError';
    }
}

/**
 * API-related error
 */
export class ApiError extends SDLCError {
    constructor(
        public readonly statusCode: number,
        message: string,
        public readonly responseData?: unknown
    ) {
        super(httpStatusToErrorCode(statusCode), message, undefined, { statusCode, responseData });
        this.name = 'ApiError';
    }
}

/**
 * Validation error
 */
export class ValidationError extends SDLCError {
    constructor(
        message: string,
        public readonly fieldErrors?: Record<string, string>
    ) {
        super(ErrorCode.VALIDATION_ERROR, message, undefined, { fieldErrors });
        this.name = 'ValidationError';
    }
}

/**
 * Maps HTTP status code to error code
 */
function httpStatusToErrorCode(status: number): ErrorCode {
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
function getErrorMessage(code: ErrorCode, technicalMessage: string): string {
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
function isRetryableError(code: ErrorCode): boolean {
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
function getSuggestedAction(code: ErrorCode): string {
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
 * Error handler options
 */
interface ErrorHandlerOptions {
    /** Show VS Code notification */
    showNotification?: boolean;
    /** Notification type */
    notificationType?: 'error' | 'warning' | 'info';
    /** Log the error */
    logError?: boolean;
    /** Include action buttons in notification */
    includeActions?: boolean;
    /** Custom actions */
    customActions?: Array<{
        title: string;
        command: string;
        args?: unknown[];
    }>;
}

/**
 * Default error handler options
 */
const DEFAULT_OPTIONS: ErrorHandlerOptions = {
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
export async function handleError(
    error: unknown,
    options: ErrorHandlerOptions = {}
): Promise<void> {
    const opts = { ...DEFAULT_OPTIONS, ...options };
    const sdlcError = normalizeError(error);

    // Log the error
    if (opts.logError) {
        Logger.error(
            `[${ErrorCode[sdlcError.code]}] ${sdlcError.message}` +
                (sdlcError.originalError
                    ? ` | Original: ${sdlcError.originalError.message}`
                    : '')
        );
    }

    // Show notification
    if (opts.showNotification) {
        const userMessage = sdlcError.getUserMessage();
        const actions = buildActions(sdlcError, opts);

        let selection: string | undefined;

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
function normalizeError(error: unknown): SDLCError {
    if (error instanceof SDLCError) {
        return error;
    }

    if (error instanceof Error) {
        // Check for network errors
        if (
            error.message.includes('ECONNREFUSED') ||
            error.message.includes('ENOTFOUND')
        ) {
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
function buildActions(error: SDLCError, options: ErrorHandlerOptions): string[] {
    const actions: string[] = [];

    if (!options.includeActions) {
        return actions;
    }

    // Add suggested action
    if (error.isRetryable()) {
        actions.push('Retry');
    }

    // Add login action for auth errors
    if (
        [ErrorCode.UNAUTHORIZED, ErrorCode.TOKEN_EXPIRED, ErrorCode.TOKEN_INVALID].includes(
            error.code
        )
    ) {
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
async function handleActionSelection(
    selection: string,
    error: SDLCError,
    options: ErrorHandlerOptions
): Promise<void> {
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
                await vscode.commands.executeCommand(
                    customAction.command,
                    ...(customAction.args ?? [])
                );
            }
            break;
        }
    }
}

/**
 * Shows detailed error information
 */
function showErrorDetails(error: SDLCError): void {
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
export function withErrorHandling<T extends unknown[], R>(
    fn: (...args: T) => Promise<R>,
    options?: ErrorHandlerOptions
): (...args: T) => Promise<R | undefined> {
    return async (...args: T): Promise<R | undefined> => {
        try {
            return await fn(...args);
        } catch (error) {
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
export function withRetry<T extends unknown[], R>(
    fn: (...args: T) => Promise<R>,
    maxRetries: number = 3,
    delayMs: number = 1000
): (...args: T) => Promise<R> {
    return async (...args: T): Promise<R> => {
        let lastError: Error | undefined;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await fn(...args);
            } catch (error) {
                lastError = error instanceof Error ? error : new Error(String(error));
                const sdlcError = normalizeError(error);

                if (!sdlcError.isRetryable() || attempt === maxRetries) {
                    throw error;
                }

                Logger.warn(
                    `Attempt ${attempt}/${maxRetries} failed, retrying in ${delayMs}ms...`
                );
                await sleep(delayMs * attempt); // Exponential backoff
            }
        }

        throw lastError;
    };
}

/**
 * Sleep helper
 */
function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Classifies an error and returns an SDLCError
 *
 * @param error - The error to classify
 */
export function classifyError(error: unknown): SDLCError {
    if (error === null || error === undefined) {
        return new SDLCError(ErrorCode.UNKNOWN, 'Unknown error occurred');
    }

    if (error instanceof SDLCError) {
        return error;
    }

    // Handle axios-like errors with response
    if (typeof error === 'object' && error !== null) {
        const err = error as Record<string, unknown>;

        // Check for network error codes
        if (err.code === 'ECONNREFUSED') {
            return new SDLCError(
                ErrorCode.CONNECTION_REFUSED,
                'Connection refused',
                undefined,
                { category: 'network' }
            );
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
        const response = err.response as Record<string, unknown> | undefined;
        if (response && typeof response.status === 'number') {
            const status = response.status;
            const code = httpStatusToErrorCode(status);
            const category =
                status === 401 || status === 403
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
    get: function (this: SDLCError) {
        const ctx = this.context;
        if (ctx && typeof ctx === 'object' && 'category' in ctx) {
            const ctxObj = ctx as { category?: string };
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
export function createNetworkError(
    message: string,
    code: ErrorCode = ErrorCode.NETWORK_ERROR
): SDLCError {
    const error = new SDLCError(code, message, undefined, { category: 'network' });
    return error;
}

/**
 * Factory function to create an auth error
 *
 * @param message - Error message
 * @param code - Error code
 */
export function createAuthError(message: string, code: ErrorCode): SDLCError {
    return new SDLCError(code, message, undefined, { category: 'auth' });
}

/**
 * Factory function to create an API error
 *
 * @param message - Error message
 * @param statusCode - HTTP status code
 */
export function createApiError(message: string, statusCode: number): SDLCError {
    const code = httpStatusToErrorCode(statusCode);
    const retryable = statusCode >= 500 || statusCode === 429;
    return new SDLCError(code, message, undefined, { category: 'api', retryable });
}
