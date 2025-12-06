"use strict";
/**
 * SDLC Orchestrator Logger Utility
 *
 * Provides centralized logging with VS Code Output Channel integration.
 *
 * Sprint 27 Day 1 - Utilities
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
exports.Logger = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Logger class for SDLC Orchestrator extension
 */
class Logger {
    static outputChannel;
    static minLevel = 'INFO';
    /**
     * Initializes the output channel
     */
    static ensureChannel() {
        if (!this.outputChannel) {
            this.outputChannel = vscode.window.createOutputChannel('SDLC Orchestrator');
        }
        return this.outputChannel;
    }
    /**
     * Sets the minimum log level
     */
    static setLevel(level) {
        this.minLevel = level;
    }
    /**
     * Gets numeric priority for log level
     */
    static getLevelPriority(level) {
        const priorities = {
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
    static shouldLog(level) {
        return this.getLevelPriority(level) >= this.getLevelPriority(this.minLevel);
    }
    /**
     * Formats a log message
     */
    static formatMessage(level, message) {
        const timestamp = new Date().toISOString();
        return `[${timestamp}] [${level}] ${message}`;
    }
    /**
     * Logs a message at the specified level
     */
    static log(level, message) {
        if (!this.shouldLog(level)) {
            return;
        }
        const channel = this.ensureChannel();
        const formattedMessage = this.formatMessage(level, message);
        channel.appendLine(formattedMessage);
        // Also log to console for debugging
        if (level === 'ERROR') {
            console.error(formattedMessage);
        }
        else if (level === 'WARN') {
            console.warn(formattedMessage);
        }
    }
    /**
     * Logs a debug message
     */
    static debug(message) {
        this.log('DEBUG', message);
    }
    /**
     * Logs an info message
     */
    static info(message) {
        this.log('INFO', message);
    }
    /**
     * Logs a warning message
     */
    static warn(message) {
        this.log('WARN', message);
    }
    /**
     * Logs an error message
     */
    static error(message) {
        this.log('ERROR', message);
    }
    /**
     * Shows the output channel
     */
    static show() {
        this.ensureChannel().show();
    }
    /**
     * Disposes the output channel
     */
    static dispose() {
        if (this.outputChannel) {
            this.outputChannel.dispose();
            this.outputChannel = undefined;
        }
    }
}
exports.Logger = Logger;
//# sourceMappingURL=logger.js.map