/**
 * SSE (Server-Sent Events) Client for SDLC Orchestrator
 *
 * Handles real-time streaming from code generation endpoints.
 * Sprint 53 Day 1 - SSE Client Implementation
 *
 * @version 1.0.0
 */
import * as vscode from 'vscode';
import type { SSEEvent, SSEEventType } from '../types/codegen';
/**
 * SSE connection state
 */
export type SSEConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
/**
 * SSE event handler function type
 */
export type SSEEventHandler = (event: SSEEvent) => void;
/**
 * SSE error handler function type
 */
export type SSEErrorHandler = (error: Error) => void;
/**
 * SSE connection options
 */
export interface SSEConnectionOptions {
    /** Base URL for the SSE endpoint */
    url: string;
    /** Authorization token */
    token: string;
    /** Connection timeout in milliseconds */
    timeout?: number;
    /** Retry attempts on connection failure */
    retryAttempts?: number;
    /** Retry delay in milliseconds */
    retryDelay?: number;
}
/**
 * SSE Client for streaming code generation events
 *
 * Uses native fetch with ReadableStream for SSE parsing.
 * Provides automatic reconnection and event dispatching.
 */
export declare class SSEClient implements vscode.Disposable {
    private readonly options;
    private state;
    private abortController;
    private eventHandlers;
    private errorHandlers;
    private stateChangeHandlers;
    private retryCount;
    private readonly maxRetries;
    private readonly retryDelay;
    private readonly timeout;
    constructor(options: SSEConnectionOptions);
    /**
     * Current connection state
     */
    getState(): SSEConnectionState;
    /**
     * Register an event handler for specific event type or all events
     */
    on(eventType: SSEEventType | '*', handler: SSEEventHandler): void;
    /**
     * Remove an event handler
     */
    off(eventType: SSEEventType | '*', handler: SSEEventHandler): void;
    /**
     * Register an error handler
     */
    onError(handler: SSEErrorHandler): void;
    /**
     * Register a state change handler
     */
    onStateChange(handler: (state: SSEConnectionState) => void): void;
    /**
     * Connect to SSE endpoint and start streaming
     */
    connect(): Promise<void>;
    /**
     * Disconnect from SSE endpoint
     */
    disconnect(): void;
    /**
     * Dispose of the SSE client
     */
    dispose(): void;
    /**
     * Establish SSE connection with retry logic
     */
    private establishConnection;
    /**
     * Process the SSE stream
     */
    private processStream;
    /**
     * Parse SSE buffer into events
     */
    private parseSSEBuffer;
    /**
     * Dispatch event to registered handlers
     */
    private dispatchEvent;
    /**
     * Handle connection errors with retry logic
     */
    private handleConnectionError;
    /**
     * Update connection state and notify handlers
     */
    private setState;
}
/**
 * Create an SSE client for code generation streaming
 */
export declare function createCodegenSSEClient(baseUrl: string, sessionId: string, token: string): SSEClient;
//# sourceMappingURL=sseClient.d.ts.map