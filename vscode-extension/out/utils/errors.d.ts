/**
 * SDLC Orchestrator Error Utilities
 *
 * Provides centralized error handling, classification, and user-friendly
 * error messages for the VS Code extension.
 *
 * Sprint 27 Day 2 - Error Handling
 * @version 0.1.0
 */
/**
 * Error codes for classification
 */
export declare enum ErrorCode {
    NETWORK_ERROR = 100,
    TIMEOUT = 101,
    CONNECTION_REFUSED = 102,
    UNAUTHORIZED = 200,
    TOKEN_EXPIRED = 201,
    TOKEN_INVALID = 202,
    FORBIDDEN = 203,
    NOT_FOUND = 300,
    BAD_REQUEST = 301,
    CONFLICT = 302,
    RATE_LIMITED = 303,
    SERVER_ERROR = 304,
    VALIDATION_ERROR = 400,
    CONFIGURATION_ERROR = 401,
    NO_PROJECT_SELECTED = 402,
    UNKNOWN = 999
}
/**
 * Base error class for SDLC extension
 */
export declare class SDLCError extends Error {
    readonly code: ErrorCode;
    readonly originalError?: Error | undefined;
    readonly context?: Record<string, unknown> | undefined;
    constructor(code: ErrorCode, message: string, originalError?: Error | undefined, context?: Record<string, unknown> | undefined);
    /**
     * Gets user-friendly error message
     */
    getUserMessage(): string;
    /**
     * Checks if error is retryable
     */
    isRetryable(): boolean;
    /**
     * Gets suggested action for the error
     */
    getSuggestedAction(): string;
}
/**
 * Network-related error
 */
export declare class NetworkError extends SDLCError {
    constructor(message: string, originalError?: Error);
}
/**
 * Authentication-related error
 */
export declare class AuthError extends SDLCError {
    constructor(code: ErrorCode, message: string, originalError?: Error);
}
/**
 * API-related error
 */
export declare class ApiError extends SDLCError {
    readonly statusCode: number;
    readonly responseData?: unknown | undefined;
    constructor(statusCode: number, message: string, responseData?: unknown | undefined);
}
/**
 * Validation error
 */
export declare class ValidationError extends SDLCError {
    readonly fieldErrors?: Record<string, string> | undefined;
    constructor(message: string, fieldErrors?: Record<string, string> | undefined);
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
 * Handles an error with appropriate user feedback
 *
 * @param error - The error to handle
 * @param options - Handler options
 */
export declare function handleError(error: unknown, options?: ErrorHandlerOptions): Promise<void>;
/**
 * Wraps an async function with error handling
 *
 * @param fn - The async function to wrap
 * @param options - Error handler options
 */
export declare function withErrorHandling<T extends unknown[], R>(fn: (...args: T) => Promise<R>, options?: ErrorHandlerOptions): (...args: T) => Promise<R | undefined>;
/**
 * Creates a retry wrapper for async functions
 *
 * @param fn - The async function to wrap
 * @param maxRetries - Maximum number of retries
 * @param delayMs - Delay between retries in milliseconds
 */
export declare function withRetry<T extends unknown[], R>(fn: (...args: T) => Promise<R>, maxRetries?: number, delayMs?: number): (...args: T) => Promise<R>;
/**
 * Classifies an error and returns an SDLCError
 *
 * @param error - The error to classify
 */
export declare function classifyError(error: unknown): SDLCError;
/**
 * Factory function to create a network error
 *
 * @param message - Error message
 * @param code - Error code (default: NETWORK_ERROR)
 */
export declare function createNetworkError(message: string, code?: ErrorCode): SDLCError;
/**
 * Factory function to create an auth error
 *
 * @param message - Error message
 * @param code - Error code
 */
export declare function createAuthError(message: string, code: ErrorCode): SDLCError;
/**
 * Factory function to create an API error
 *
 * @param message - Error message
 * @param statusCode - HTTP status code
 */
export declare function createApiError(message: string, statusCode: number): SDLCError;
export {};
//# sourceMappingURL=errors.d.ts.map