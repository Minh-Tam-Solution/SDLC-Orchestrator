/**
 * SDLC Orchestrator Logger Utility
 *
 * Provides centralized logging with VS Code Output Channel integration.
 *
 * Sprint 27 Day 1 - Utilities
 * @version 0.1.0
 */

import * as vscode from 'vscode';

/**
 * Log levels
 */
type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

/**
 * Logger class for SDLC Orchestrator extension
 */
export class Logger {
    private static outputChannel: vscode.OutputChannel | undefined;
    private static minLevel: LogLevel = 'INFO';

    /**
     * Initializes the output channel
     */
    private static ensureChannel(): vscode.OutputChannel {
        if (!this.outputChannel) {
            this.outputChannel = vscode.window.createOutputChannel('SDLC Orchestrator');
        }
        return this.outputChannel;
    }

    /**
     * Sets the minimum log level
     */
    static setLevel(level: LogLevel): void {
        this.minLevel = level;
    }

    /**
     * Gets numeric priority for log level
     */
    private static getLevelPriority(level: LogLevel): number {
        const priorities: Record<LogLevel, number> = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3,
        };
        return priorities[level];
    }

    /**
     * Checks if message should be logged based on level
     */
    private static shouldLog(level: LogLevel): boolean {
        return this.getLevelPriority(level) >= this.getLevelPriority(this.minLevel);
    }

    /**
     * Formats a log message
     */
    private static formatMessage(level: LogLevel, message: string): string {
        const timestamp = new Date().toISOString();
        return `[${timestamp}] [${level}] ${message}`;
    }

    /**
     * Logs a message at the specified level
     */
    private static log(level: LogLevel, message: string): void {
        if (!this.shouldLog(level)) {
            return;
        }

        const channel = this.ensureChannel();
        const formattedMessage = this.formatMessage(level, message);
        channel.appendLine(formattedMessage);

        // Also log to console for debugging
        if (level === 'ERROR') {
            console.error(formattedMessage);
        } else if (level === 'WARN') {
            console.warn(formattedMessage);
        }
    }

    /**
     * Logs a debug message
     */
    static debug(message: string): void {
        this.log('DEBUG', message);
    }

    /**
     * Logs an info message
     */
    static info(message: string): void {
        this.log('INFO', message);
    }

    /**
     * Logs a warning message
     */
    static warn(message: string): void {
        this.log('WARN', message);
    }

    /**
     * Logs an error message
     */
    static error(message: string): void {
        this.log('ERROR', message);
    }

    /**
     * Shows the output channel
     */
    static show(): void {
        this.ensureChannel().show();
    }

    /**
     * Disposes the output channel
     */
    static dispose(): void {
        if (this.outputChannel) {
            this.outputChannel.dispose();
            this.outputChannel = undefined;
        }
    }
}
