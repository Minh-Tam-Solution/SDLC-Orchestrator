/**
 * SSE (Server-Sent Events) Client for SDLC Orchestrator
 *
 * Handles real-time streaming from code generation endpoints.
 * Sprint 53 Day 1 - SSE Client Implementation
 *
 * @version 1.0.0
 */

import * as vscode from 'vscode';
import { Logger } from '../utils/logger';
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
export class SSEClient implements vscode.Disposable {
    private state: SSEConnectionState = 'disconnected';
    private abortController: AbortController | null = null;
    private eventHandlers: Map<SSEEventType | '*', SSEEventHandler[]> = new Map();
    private errorHandlers: SSEErrorHandler[] = [];
    private stateChangeHandlers: ((state: SSEConnectionState) => void)[] = [];
    private retryCount = 0;
    private readonly maxRetries: number;
    private readonly retryDelay: number;
    private readonly timeout: number;

    constructor(
        private readonly options: SSEConnectionOptions
    ) {
        this.maxRetries = options.retryAttempts ?? 3;
        this.retryDelay = options.retryDelay ?? 1000;
        this.timeout = options.timeout ?? 120000; // 2 minutes default
    }

    /**
     * Current connection state
     */
    public getState(): SSEConnectionState {
        return this.state;
    }

    /**
     * Register an event handler for specific event type or all events
     */
    public on(eventType: SSEEventType | '*', handler: SSEEventHandler): void {
        const handlers = this.eventHandlers.get(eventType) || [];
        handlers.push(handler);
        this.eventHandlers.set(eventType, handlers);
    }

    /**
     * Remove an event handler
     */
    public off(eventType: SSEEventType | '*', handler: SSEEventHandler): void {
        const handlers = this.eventHandlers.get(eventType);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Register an error handler
     */
    public onError(handler: SSEErrorHandler): void {
        this.errorHandlers.push(handler);
    }

    /**
     * Register a state change handler
     */
    public onStateChange(handler: (state: SSEConnectionState) => void): void {
        this.stateChangeHandlers.push(handler);
    }

    /**
     * Connect to SSE endpoint and start streaming
     */
    public async connect(): Promise<void> {
        if (this.state === 'connected' || this.state === 'connecting') {
            Logger.warn('SSE client already connected or connecting');
            return;
        }

        this.setState('connecting');
        this.retryCount = 0;

        await this.establishConnection();
    }

    /**
     * Disconnect from SSE endpoint
     */
    public disconnect(): void {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.setState('disconnected');
        Logger.info('SSE client disconnected');
    }

    /**
     * Dispose of the SSE client
     */
    public dispose(): void {
        this.disconnect();
        this.eventHandlers.clear();
        this.errorHandlers = [];
        this.stateChangeHandlers = [];
    }

    /**
     * Establish SSE connection with retry logic
     */
    private async establishConnection(): Promise<void> {
        try {
            this.abortController = new AbortController();

            const timeoutId = setTimeout(() => {
                if (this.abortController) {
                    this.abortController.abort();
                }
            }, this.timeout);

            const response = await fetch(this.options.url, {
                method: 'GET',
                headers: {
                    'Accept': 'text/event-stream',
                    'Authorization': `Bearer ${this.options.token}`,
                    'Cache-Control': 'no-cache',
                },
                signal: this.abortController.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`SSE connection failed: ${response.status} ${response.statusText}`);
            }

            if (!response.body) {
                throw new Error('SSE response has no body');
            }

            this.setState('connected');
            Logger.info(`SSE connected to ${this.options.url}`);

            await this.processStream(response.body);

        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                Logger.info('SSE connection aborted');
                return;
            }

            this.handleConnectionError(error as Error);
        }
    }

    /**
     * Process the SSE stream
     */
    private async processStream(body: ReadableStream<Uint8Array>): Promise<void> {
        const reader = body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    Logger.info('SSE stream ended');
                    this.setState('disconnected');
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                // Process complete events in buffer
                const events = this.parseSSEBuffer(buffer);
                buffer = events.remaining;

                for (const event of events.parsed) {
                    this.dispatchEvent(event);
                }
            }
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }
            this.handleConnectionError(error as Error);
        } finally {
            reader.releaseLock();
        }
    }

    /**
     * Parse SSE buffer into events
     */
    private parseSSEBuffer(buffer: string): { parsed: SSEEvent[]; remaining: string } {
        const events: SSEEvent[] = [];
        const lines = buffer.split('\n');
        let currentData = '';
        let remaining = '';

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i] ?? '';

            // Check if this is the last incomplete line
            if (i === lines.length - 1 && !buffer.endsWith('\n')) {
                remaining = line;
                break;
            }

            if (line.startsWith('data: ')) {
                currentData = line.slice(6);
            } else if (line === '' && currentData) {
                // Empty line signals end of event
                try {
                    const parsed = JSON.parse(currentData) as SSEEvent;
                    events.push(parsed);
                } catch {
                    Logger.warn(`Failed to parse SSE event: ${currentData}`);
                }
                currentData = '';
            }
        }

        return { parsed: events, remaining };
    }

    /**
     * Dispatch event to registered handlers
     */
    private dispatchEvent(event: SSEEvent): void {
        // Dispatch to specific event type handlers
        const typeHandlers = this.eventHandlers.get(event.type);
        if (typeHandlers) {
            for (const handler of typeHandlers) {
                try {
                    handler(event);
                } catch (error) {
                    Logger.error(`SSE event handler error: ${error}`);
                }
            }
        }

        // Dispatch to wildcard handlers
        const wildcardHandlers = this.eventHandlers.get('*');
        if (wildcardHandlers) {
            for (const handler of wildcardHandlers) {
                try {
                    handler(event);
                } catch (error) {
                    Logger.error(`SSE wildcard handler error: ${error}`);
                }
            }
        }
    }

    /**
     * Handle connection errors with retry logic
     */
    private handleConnectionError(error: Error): void {
        Logger.error(`SSE connection error: ${error.message}`);

        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            Logger.info(`SSE retry attempt ${this.retryCount}/${this.maxRetries}`);

            setTimeout(() => {
                void this.establishConnection();
            }, this.retryDelay * this.retryCount);
        } else {
            this.setState('error');
            for (const handler of this.errorHandlers) {
                try {
                    handler(error);
                } catch (handlerError) {
                    Logger.error(`SSE error handler error: ${handlerError}`);
                }
            }
        }
    }

    /**
     * Update connection state and notify handlers
     */
    private setState(newState: SSEConnectionState): void {
        if (this.state !== newState) {
            this.state = newState;
            for (const handler of this.stateChangeHandlers) {
                try {
                    handler(newState);
                } catch (error) {
                    Logger.error(`SSE state change handler error: ${error}`);
                }
            }
        }
    }
}

/**
 * Create an SSE client for code generation streaming
 */
export function createCodegenSSEClient(
    baseUrl: string,
    sessionId: string,
    token: string
): SSEClient {
    const url = `${baseUrl}/api/v1/codegen/stream/${sessionId}`;
    return new SSEClient({
        url,
        token,
        timeout: 300000, // 5 minutes for code generation
        retryAttempts: 3,
        retryDelay: 2000,
    });
}
