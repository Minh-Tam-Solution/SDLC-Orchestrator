"use strict";
/**
 * SSE (Server-Sent Events) Client for SDLC Orchestrator
 *
 * Handles real-time streaming from code generation endpoints.
 * Sprint 53 Day 1 - SSE Client Implementation
 *
 * @version 1.0.0
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.SSEClient = void 0;
exports.createCodegenSSEClient = createCodegenSSEClient;
const logger_1 = require("../utils/logger");
/**
 * SSE Client for streaming code generation events
 *
 * Uses native fetch with ReadableStream for SSE parsing.
 * Provides automatic reconnection and event dispatching.
 */
class SSEClient {
    options;
    state = 'disconnected';
    abortController = null;
    eventHandlers = new Map();
    errorHandlers = [];
    stateChangeHandlers = [];
    retryCount = 0;
    maxRetries;
    retryDelay;
    timeout;
    constructor(options) {
        this.options = options;
        this.maxRetries = options.retryAttempts ?? 3;
        this.retryDelay = options.retryDelay ?? 1000;
        this.timeout = options.timeout ?? 120000; // 2 minutes default
    }
    /**
     * Current connection state
     */
    getState() {
        return this.state;
    }
    /**
     * Register an event handler for specific event type or all events
     */
    on(eventType, handler) {
        const handlers = this.eventHandlers.get(eventType) || [];
        handlers.push(handler);
        this.eventHandlers.set(eventType, handlers);
    }
    /**
     * Remove an event handler
     */
    off(eventType, handler) {
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
    onError(handler) {
        this.errorHandlers.push(handler);
    }
    /**
     * Register a state change handler
     */
    onStateChange(handler) {
        this.stateChangeHandlers.push(handler);
    }
    /**
     * Connect to SSE endpoint and start streaming
     */
    async connect() {
        if (this.state === 'connected' || this.state === 'connecting') {
            logger_1.Logger.warn('SSE client already connected or connecting');
            return;
        }
        this.setState('connecting');
        this.retryCount = 0;
        await this.establishConnection();
    }
    /**
     * Disconnect from SSE endpoint
     */
    disconnect() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.setState('disconnected');
        logger_1.Logger.info('SSE client disconnected');
    }
    /**
     * Dispose of the SSE client
     */
    dispose() {
        this.disconnect();
        this.eventHandlers.clear();
        this.errorHandlers = [];
        this.stateChangeHandlers = [];
    }
    /**
     * Establish SSE connection with retry logic
     */
    async establishConnection() {
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
            logger_1.Logger.info(`SSE connected to ${this.options.url}`);
            await this.processStream(response.body);
        }
        catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                logger_1.Logger.info('SSE connection aborted');
                return;
            }
            this.handleConnectionError(error);
        }
    }
    /**
     * Process the SSE stream
     */
    async processStream(body) {
        const reader = body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    logger_1.Logger.info('SSE stream ended');
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
        }
        catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                return;
            }
            this.handleConnectionError(error);
        }
        finally {
            reader.releaseLock();
        }
    }
    /**
     * Parse SSE buffer into events
     */
    parseSSEBuffer(buffer) {
        const events = [];
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
            }
            else if (line === '' && currentData) {
                // Empty line signals end of event
                try {
                    const parsed = JSON.parse(currentData);
                    events.push(parsed);
                }
                catch {
                    logger_1.Logger.warn(`Failed to parse SSE event: ${currentData}`);
                }
                currentData = '';
            }
        }
        return { parsed: events, remaining };
    }
    /**
     * Dispatch event to registered handlers
     */
    dispatchEvent(event) {
        // Dispatch to specific event type handlers
        const typeHandlers = this.eventHandlers.get(event.type);
        if (typeHandlers) {
            for (const handler of typeHandlers) {
                try {
                    handler(event);
                }
                catch (error) {
                    logger_1.Logger.error(`SSE event handler error: ${error}`);
                }
            }
        }
        // Dispatch to wildcard handlers
        const wildcardHandlers = this.eventHandlers.get('*');
        if (wildcardHandlers) {
            for (const handler of wildcardHandlers) {
                try {
                    handler(event);
                }
                catch (error) {
                    logger_1.Logger.error(`SSE wildcard handler error: ${error}`);
                }
            }
        }
    }
    /**
     * Handle connection errors with retry logic
     */
    handleConnectionError(error) {
        logger_1.Logger.error(`SSE connection error: ${error.message}`);
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            logger_1.Logger.info(`SSE retry attempt ${this.retryCount}/${this.maxRetries}`);
            setTimeout(() => {
                void this.establishConnection();
            }, this.retryDelay * this.retryCount);
        }
        else {
            this.setState('error');
            for (const handler of this.errorHandlers) {
                try {
                    handler(error);
                }
                catch (handlerError) {
                    logger_1.Logger.error(`SSE error handler error: ${handlerError}`);
                }
            }
        }
    }
    /**
     * Update connection state and notify handlers
     */
    setState(newState) {
        if (this.state !== newState) {
            this.state = newState;
            for (const handler of this.stateChangeHandlers) {
                try {
                    handler(newState);
                }
                catch (error) {
                    logger_1.Logger.error(`SSE state change handler error: ${error}`);
                }
            }
        }
    }
}
exports.SSEClient = SSEClient;
/**
 * Create an SSE client for code generation streaming
 */
function createCodegenSSEClient(baseUrl, sessionId, token) {
    const url = `${baseUrl}/api/v1/codegen/stream/${sessionId}`;
    return new SSEClient({
        url,
        token,
        timeout: 300000, // 5 minutes for code generation
        retryAttempts: 3,
        retryDelay: 2000,
    });
}
//# sourceMappingURL=sseClient.js.map