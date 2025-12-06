/**
 * SDLC Orchestrator Logger Utility
 *
 * Provides centralized logging with VS Code Output Channel integration.
 *
 * Sprint 27 Day 1 - Utilities
 * @version 0.1.0
 */
/**
 * Log levels
 */
type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
/**
 * Logger class for SDLC Orchestrator extension
 */
export declare class Logger {
    private static outputChannel;
    private static minLevel;
    /**
     * Initializes the output channel
     */
    private static ensureChannel;
    /**
     * Sets the minimum log level
     */
    static setLevel(level: LogLevel): void;
    /**
     * Gets numeric priority for log level
     */
    private static getLevelPriority;
    /**
     * Checks if message should be logged based on level
     */
    private static shouldLog;
    /**
     * Formats a log message
     */
    private static formatMessage;
    /**
     * Logs a message at the specified level
     */
    private static log;
    /**
     * Logs a debug message
     */
    static debug(message: string): void;
    /**
     * Logs an info message
     */
    static info(message: string): void;
    /**
     * Logs a warning message
     */
    static warn(message: string): void;
    /**
     * Logs an error message
     */
    static error(message: string): void;
    /**
     * Shows the output channel
     */
    static show(): void;
    /**
     * Disposes the output channel
     */
    static dispose(): void;
}
export {};
//# sourceMappingURL=logger.d.ts.map