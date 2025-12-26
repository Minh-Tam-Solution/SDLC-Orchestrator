"use strict";
/**
 * Preview Command - Preview Generated Code
 *
 * Implements the sdlc.preview command for previewing
 * generated code before writing to disk.
 *
 * Sprint 53 Day 1 - Preview Command Implementation
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
exports.registerPreviewCommand = registerPreviewCommand;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const errors_1 = require("../utils/errors");
/**
 * Preview panel manager
 */
class PreviewPanelManager {
    static panels = new Map();
    static getOrCreatePanel(sessionId, context) {
        let panel = this.panels.get(sessionId);
        if (panel) {
            panel.reveal(vscode.ViewColumn.Two);
            return panel;
        }
        panel = vscode.window.createWebviewPanel('sdlc.codePreview', `Code Preview: ${sessionId.substring(0, 8)}`, vscode.ViewColumn.Two, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [context.extensionUri],
        });
        panel.onDidDispose(() => {
            this.panels.delete(sessionId);
        });
        this.panels.set(sessionId, panel);
        return panel;
    }
    static disposePanel(sessionId) {
        const panel = this.panels.get(sessionId);
        if (panel) {
            panel.dispose();
            this.panels.delete(sessionId);
        }
    }
}
/**
 * Register the preview command
 */
function registerPreviewCommand(context, codegenApi) {
    const command = vscode.commands.registerCommand('sdlc.preview', async (sessionId) => {
        await executePreviewCommand(context, codegenApi, sessionId);
    });
    context.subscriptions.push(command);
    logger_1.Logger.info('Preview command registered');
}
/**
 * Execute the preview command
 */
async function executePreviewCommand(context, codegenApi, providedSessionId) {
    try {
        // Get session ID if not provided
        const sessionId = providedSessionId || await getSessionId(codegenApi);
        if (!sessionId) {
            return;
        }
        // Get session status
        const session = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Loading preview...',
            cancellable: false,
        }, async () => {
            return await codegenApi.getGenerationStatus(sessionId);
        });
        if (!session.files || session.files.length === 0) {
            void vscode.window.showInformationMessage('No generated files to preview');
            return;
        }
        // Create or update preview panel
        const panel = PreviewPanelManager.getOrCreatePanel(sessionId, context);
        // Set panel content
        panel.webview.html = generatePreviewHtml(session, panel.webview, context.extensionUri);
        // Handle messages from webview
        panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'openFile':
                    if (message.path && message.content) {
                        await openFileInEditor(message.path, message.content);
                    }
                    break;
                case 'saveFile':
                    if (message.path && message.content) {
                        await saveFile(message.path, message.content);
                    }
                    break;
                case 'saveAll':
                    await saveAllFiles(session.files);
                    break;
            }
        }, undefined, context.subscriptions);
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}
/**
 * Get session ID from user
 */
async function getSessionId(codegenApi) {
    const config = vscode.workspace.getConfiguration('sdlc');
    const projectId = config.get('defaultProjectId');
    if (projectId) {
        try {
            const sessions = await codegenApi.listSessions(projectId);
            const completedSessions = sessions.filter(s => s.status === 'completed' && s.generated_files && s.generated_files.length > 0);
            if (completedSessions.length === 0) {
                void vscode.window.showInformationMessage('No completed sessions with generated files found');
                return undefined;
            }
            const firstSession = completedSessions[0];
            if (completedSessions.length === 1 && firstSession) {
                return firstSession.id;
            }
            const items = completedSessions.map(s => ({
                label: s.id.substring(0, 8),
                description: `${s.generated_files?.length || 0} files`,
                detail: `Created: ${formatDate(s.created_at)}`,
                sessionId: s.id,
            }));
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a session to preview',
            });
            return selected?.sessionId;
        }
        catch (error) {
            logger_1.Logger.warn(`Failed to list sessions: ${error}`);
        }
    }
    return await vscode.window.showInputBox({
        prompt: 'Enter the session ID to preview',
        placeHolder: 'e.g., abc12345-1234-1234-1234-123456789abc',
    });
}
/**
 * Open file content in a new editor
 */
async function openFileInEditor(path, content) {
    const doc = await vscode.workspace.openTextDocument({
        content,
        language: getLanguageId(path),
    });
    await vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
}
/**
 * Save file to disk
 */
async function saveFile(path, content) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const firstWorkspace = workspaceFolders?.[0];
    if (!firstWorkspace) {
        void vscode.window.showErrorMessage('No workspace folder open');
        return;
    }
    const targetPath = vscode.Uri.joinPath(firstWorkspace.uri, path);
    // Create directory if needed
    const dirPath = vscode.Uri.joinPath(targetPath, '..');
    try {
        await vscode.workspace.fs.createDirectory(dirPath);
    }
    catch {
        // Directory may exist
    }
    await vscode.workspace.fs.writeFile(targetPath, Buffer.from(content, 'utf-8'));
    void vscode.window.showInformationMessage(`Saved: ${path}`);
}
/**
 * Save all files to disk
 */
async function saveAllFiles(files) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const firstWorkspace = workspaceFolders?.[0];
    if (!firstWorkspace) {
        const folderUri = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            title: 'Select Output Directory',
        });
        const selectedFolder = folderUri?.[0];
        if (!selectedFolder) {
            return;
        }
        await writeFilesToDirectory(selectedFolder.fsPath, files);
    }
    else {
        await writeFilesToDirectory(firstWorkspace.uri.fsPath, files);
    }
}
/**
 * Write files to a directory
 */
async function writeFilesToDirectory(basePath, files) {
    let savedCount = 0;
    for (const file of files) {
        try {
            const targetPath = vscode.Uri.file(`${basePath}/${file.path}`);
            const dirPath = vscode.Uri.file(targetPath.fsPath.substring(0, targetPath.fsPath.lastIndexOf('/')));
            try {
                await vscode.workspace.fs.createDirectory(dirPath);
            }
            catch {
                // Directory may exist
            }
            await vscode.workspace.fs.writeFile(targetPath, Buffer.from(file.content, 'utf-8'));
            savedCount++;
        }
        catch (error) {
            logger_1.Logger.error(`Failed to save ${file.path}: ${error}`);
        }
    }
    void vscode.window.showInformationMessage(`Saved ${savedCount} of ${files.length} files`);
}
/**
 * Get VS Code language ID from file path
 */
function getLanguageId(path) {
    const ext = path.split('.').pop()?.toLowerCase();
    const langMap = {
        'py': 'python',
        'ts': 'typescript',
        'tsx': 'typescriptreact',
        'js': 'javascript',
        'jsx': 'javascriptreact',
        'json': 'json',
        'md': 'markdown',
        'yaml': 'yaml',
        'yml': 'yaml',
        'html': 'html',
        'css': 'css',
        'sql': 'sql',
    };
    return langMap[ext || ''] || 'plaintext';
}
/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString)
        return 'Unknown';
    try {
        return new Date(dateString).toLocaleString();
    }
    catch {
        return dateString;
    }
}
/**
 * Generate HTML for preview panel
 */
function generatePreviewHtml(session, _webview, _extensionUri) {
    const files = session.files || [];
    const gates = session.quality_gates || [];
    const fileListHtml = files.map((file, index) => {
        const statusIcon = file.syntax_valid ? '✅' : '❌';
        const statusClass = file.syntax_valid ? 'valid' : 'error';
        return `
            <div class="file-item ${statusClass}" data-index="${index}">
                <span class="file-icon">${getFileIcon(file.path)}</span>
                <span class="file-path">${file.path}</span>
                <span class="file-lines">${file.lines} lines</span>
                <span class="file-status">${statusIcon}</span>
            </div>
        `;
    }).join('');
    const gateListHtml = gates.map(gate => {
        const statusIcon = gate.status === 'passed' ? '✅' : gate.status === 'failed' ? '❌' : '⏭️';
        const statusClass = gate.status;
        return `
            <div class="gate-item ${statusClass}">
                <span class="gate-name">Gate ${gate.gate_number}: ${gate.gate_name}</span>
                <span class="gate-status">${statusIcon}</span>
                <span class="gate-duration">${gate.duration_ms}ms</span>
            </div>
        `;
    }).join('');
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Preview</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 0;
            margin: 0;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 300px;
            border-right: 1px solid var(--vscode-panel-border);
            overflow-y: auto;
            padding: 10px;
        }
        .main {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .toolbar {
            padding: 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            gap: 10px;
        }
        .code-view {
            flex: 1;
            overflow: auto;
            padding: 10px;
        }
        .section-title {
            font-weight: bold;
            margin: 10px 0;
            color: var(--vscode-textLink-foreground);
        }
        .file-item {
            padding: 8px;
            cursor: pointer;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .file-item:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        .file-item.selected {
            background-color: var(--vscode-list-activeSelectionBackground);
        }
        .file-path {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-lines {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
        }
        .gate-item {
            padding: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }
        .gate-name {
            flex: 1;
        }
        .gate-duration {
            color: var(--vscode-descriptionForeground);
        }
        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 14px;
            cursor: pointer;
            border-radius: 2px;
        }
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        pre {
            margin: 0;
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            background-color: var(--vscode-textCodeBlock-background);
            padding: 10px;
            border-radius: 4px;
            overflow: auto;
        }
        .summary {
            padding: 10px;
            background-color: var(--vscode-textBlockQuote-background);
            border-radius: 4px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="summary">
                <strong>Session:</strong> ${session.id.substring(0, 8)}...<br>
                <strong>Status:</strong> ${session.status}<br>
                <strong>Files:</strong> ${files.length}<br>
                <strong>Total Lines:</strong> ${files.reduce((sum, f) => sum + f.lines, 0)}
            </div>

            <div class="section-title">📁 Generated Files</div>
            <div id="file-list">
                ${fileListHtml}
            </div>

            <div class="section-title">🔍 Quality Gates</div>
            <div id="gate-list">
                ${gateListHtml}
            </div>
        </div>
        <div class="main">
            <div class="toolbar">
                <button id="btn-open">Open in Editor</button>
                <button id="btn-save">Save File</button>
                <button id="btn-save-all">Save All</button>
            </div>
            <div class="code-view">
                <pre id="code-content">Select a file to preview</pre>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const files = ${JSON.stringify(files)};
        let selectedIndex = -1;

        // File selection
        document.querySelectorAll('.file-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                // Update selection
                document.querySelectorAll('.file-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                selectedIndex = index;

                // Show code
                const file = files[index];
                document.getElementById('code-content').textContent = file.content;
            });
        });

        // Button handlers
        document.getElementById('btn-open').addEventListener('click', () => {
            if (selectedIndex >= 0) {
                const file = files[selectedIndex];
                vscode.postMessage({ command: 'openFile', path: file.path, content: file.content });
            }
        });

        document.getElementById('btn-save').addEventListener('click', () => {
            if (selectedIndex >= 0) {
                const file = files[selectedIndex];
                vscode.postMessage({ command: 'saveFile', path: file.path, content: file.content });
            }
        });

        document.getElementById('btn-save-all').addEventListener('click', () => {
            vscode.postMessage({ command: 'saveAll' });
        });

        // Auto-select first file
        if (files.length > 0) {
            document.querySelector('.file-item')?.click();
        }
    </script>
</body>
</html>`;
}
/**
 * Get file icon based on extension
 */
function getFileIcon(path) {
    const ext = path.split('.').pop()?.toLowerCase();
    const iconMap = {
        'py': '🐍',
        'ts': '📘',
        'tsx': '⚛️',
        'js': '📒',
        'jsx': '⚛️',
        'json': '📋',
        'md': '📝',
        'yaml': '⚙️',
        'yml': '⚙️',
        'html': '🌐',
        'css': '🎨',
        'sql': '🗃️',
    };
    return iconMap[ext || ''] || '📄';
}
//# sourceMappingURL=previewCommand.js.map