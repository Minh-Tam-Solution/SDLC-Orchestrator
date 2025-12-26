"use strict";
/**
 * Streaming Status Bar - Generation Progress Indicator
 *
 * Displays real-time generation status in the VS Code status bar:
 * - Current status (generating, quality check, complete)
 * - File count and progress
 * - Click to open Generation Panel
 *
 * Sprint 53 Day 3 - Streaming Integration
 * @version 1.0.0
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
exports.StreamingStatusBar = void 0;
exports.getStreamingStatusBar = getStreamingStatusBar;
exports.registerStreamingStatusBar = registerStreamingStatusBar;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
/**
 * Status configurations for each state
 */
const STATUS_CONFIGS = {
    idle: {
        text: 'SDLC Ready',
        tooltip: 'SDLC Orchestrator - Ready for code generation',
        icon: '$(circle-outline)',
    },
    connecting: {
        text: 'Connecting...',
        tooltip: 'Connecting to code generation stream...',
        icon: '$(sync~spin)',
    },
    generating: {
        text: 'Generating',
        tooltip: 'Code generation in progress',
        icon: '$(sync~spin)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.warningBackground'),
    },
    quality_check: {
        text: 'Quality Gates',
        tooltip: 'Running quality validation gates',
        icon: '$(beaker)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.warningBackground'),
    },
    completed: {
        text: 'Complete',
        tooltip: 'Code generation completed successfully',
        icon: '$(check)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.prominentBackground'),
    },
    failed: {
        text: 'Failed',
        tooltip: 'Code generation failed',
        icon: '$(error)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.errorBackground'),
    },
    cancelled: {
        text: 'Cancelled',
        tooltip: 'Code generation was cancelled',
        icon: '$(circle-slash)',
        backgroundColor: new vscode.ThemeColor('statusBarItem.warningBackground'),
    },
};
/**
 * Streaming Status Bar Manager
 *
 * Manages the status bar item for code generation progress.
 */
class StreamingStatusBar {
    static instance;
    statusBarItem;
    currentStatus = 'idle';
    fileCount = 0;
    totalLines = 0;
    currentFile;
    hideTimeout;
    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.statusBarItem.command = 'sdlc.showGenerationPanel';
        this.updateDisplay();
        logger_1.Logger.info('StreamingStatusBar initialized');
    }
    /**
     * Get singleton instance
     */
    static getInstance() {
        if (!StreamingStatusBar.instance) {
            StreamingStatusBar.instance = new StreamingStatusBar();
        }
        return StreamingStatusBar.instance;
    }
    /**
     * Update the status
     */
    setStatus(status) {
        this.currentStatus = status;
        this.clearHideTimeout();
        this.updateDisplay();
        // Auto-hide after completion
        if (status === 'completed' || status === 'cancelled') {
            this.hideTimeout = setTimeout(() => {
                this.setStatus('idle');
            }, 5000);
        }
    }
    /**
     * Update file count
     */
    setFileCount(count) {
        this.fileCount = count;
        this.updateDisplay();
    }
    /**
     * Update total lines
     */
    setTotalLines(lines) {
        this.totalLines = lines;
        this.updateDisplay();
    }
    /**
     * Set current file being generated
     */
    setCurrentFile(file) {
        this.currentFile = file;
        this.updateDisplay();
    }
    /**
     * Update all metrics
     */
    updateMetrics(fileCount, totalLines, currentFile) {
        this.fileCount = fileCount;
        this.totalLines = totalLines;
        this.currentFile = currentFile;
        this.updateDisplay();
    }
    /**
     * Reset to idle state
     */
    reset() {
        this.currentStatus = 'idle';
        this.fileCount = 0;
        this.totalLines = 0;
        this.currentFile = undefined;
        this.clearHideTimeout();
        this.updateDisplay();
    }
    /**
     * Show the status bar item
     */
    show() {
        this.statusBarItem.show();
    }
    /**
     * Hide the status bar item
     */
    hide() {
        this.statusBarItem.hide();
    }
    /**
     * Dispose the status bar item
     */
    dispose() {
        this.clearHideTimeout();
        this.statusBarItem.dispose();
        StreamingStatusBar.instance = undefined;
        logger_1.Logger.info('StreamingStatusBar disposed');
    }
    /**
     * Update the display
     */
    updateDisplay() {
        const config = STATUS_CONFIGS[this.currentStatus];
        // Build text
        let text = `${config.icon} ${config.text}`;
        if (this.currentStatus === 'generating' || this.currentStatus === 'quality_check') {
            if (this.fileCount > 0) {
                text += ` (${this.fileCount} files)`;
            }
        }
        else if (this.currentStatus === 'completed') {
            text = `${config.icon} ${this.fileCount} files (${this.formatLines(this.totalLines)} lines)`;
        }
        // Build tooltip
        let tooltip = config.tooltip;
        if (this.currentFile && this.currentStatus === 'generating') {
            tooltip += `\n\nCurrently generating: ${this.currentFile}`;
        }
        if (this.fileCount > 0) {
            tooltip += `\n\nFiles: ${this.fileCount}`;
            tooltip += `\nLines: ${this.totalLines.toLocaleString()}`;
        }
        tooltip += '\n\nClick to open Generation Panel';
        // Update status bar
        this.statusBarItem.text = text;
        this.statusBarItem.tooltip = tooltip;
        this.statusBarItem.backgroundColor = config.backgroundColor;
        // Show/hide based on status
        if (this.currentStatus === 'idle') {
            this.hide();
        }
        else {
            this.show();
        }
    }
    /**
     * Format line count
     */
    formatLines(lines) {
        if (lines >= 1000) {
            return `${(lines / 1000).toFixed(1)}K`;
        }
        return lines.toString();
    }
    /**
     * Clear hide timeout
     */
    clearHideTimeout() {
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = undefined;
        }
    }
}
exports.StreamingStatusBar = StreamingStatusBar;
/**
 * Get StreamingStatusBar singleton
 */
function getStreamingStatusBar() {
    return StreamingStatusBar.getInstance();
}
/**
 * Register streaming status bar
 */
function registerStreamingStatusBar(context) {
    const statusBar = StreamingStatusBar.getInstance();
    context.subscriptions.push(statusBar);
    return statusBar;
}
//# sourceMappingURL=streamingStatusBar.js.map