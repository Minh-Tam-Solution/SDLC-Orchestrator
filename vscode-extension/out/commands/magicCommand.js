"use strict";
/**
 * Magic Command - Natural Language Code Generation
 *
 * Implements the sdlc.magic command for generating code
 * from natural language descriptions (Vietnamese/English).
 *
 * Sprint 53 Day 1 - Magic Mode Command Implementation
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
exports.registerMagicCommand = registerMagicCommand;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const errors_1 = require("../utils/errors");
const sseClient_1 = require("../services/sseClient");
const config_1 = require("../utils/config");
/**
 * Register the magic mode command
 */
function registerMagicCommand(context, codegenApi) {
    const command = vscode.commands.registerCommand('sdlc.magic', async () => {
        await executeMagicCommand(codegenApi);
    });
    context.subscriptions.push(command);
    logger_1.Logger.info('Magic command registered');
}
/**
 * Execute the magic mode command
 */
async function executeMagicCommand(codegenApi) {
    try {
        // Step 1: Get natural language description
        const description = await getDescriptionFromUser();
        if (!description) {
            return; // User cancelled
        }
        // Step 2: Parse description and detect domain
        const parseResult = await parseDescription(codegenApi, description);
        if (!parseResult) {
            return; // Parsing failed
        }
        // Step 3: Confirm with user
        const confirmed = await confirmGeneration(parseResult);
        if (!confirmed) {
            return; // User cancelled
        }
        // Step 4: Select output directory
        const outputPath = await selectOutputDirectory();
        if (!outputPath) {
            return; // User cancelled
        }
        // Step 5: Start magic generation with streaming
        await startMagicGeneration(codegenApi, description, outputPath);
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}
/**
 * Get natural language description from user
 */
async function getDescriptionFromUser() {
    // Show input options
    const inputMethod = await vscode.window.showQuickPick([
        {
            label: '$(edit) Quick Input',
            description: 'Type a short description',
            value: 'quick',
        },
        {
            label: '$(note) Multi-line Input',
            description: 'Write a detailed description',
            value: 'multiline',
        },
        {
            label: '$(file-text) From File',
            description: 'Load description from a text file',
            value: 'file',
        },
    ], {
        placeHolder: 'How would you like to describe your application?',
    });
    if (!inputMethod) {
        return undefined;
    }
    switch (inputMethod.value) {
        case 'quick':
            return await getQuickInput();
        case 'multiline':
            return await getMultilineInput();
        case 'file':
            return await getDescriptionFromFile();
        default:
            return undefined;
    }
}
/**
 * Get quick single-line input
 */
async function getQuickInput() {
    const description = await vscode.window.showInputBox({
        prompt: 'Describe your application (Vietnamese or English)',
        placeHolder: 'Ví dụ: Hệ thống quản lý bán hàng cho cửa hàng điện thoại',
        validateInput: (value) => {
            if (!value || value.trim().length < 10) {
                return 'Please enter a more detailed description (at least 10 characters)';
            }
            return null;
        },
    });
    return description?.trim();
}
/**
 * Get multi-line input via temporary document
 */
async function getMultilineInput() {
    // Create a temporary untitled document
    const doc = await vscode.workspace.openTextDocument({
        content: `# Describe your application (Vietnamese or English)
# Delete these comment lines and write your description below
# Example:
# Hệ thống quản lý bán hàng online gồm:
# - Quản lý sản phẩm (thêm, sửa, xóa, tìm kiếm)
# - Quản lý đơn hàng
# - Quản lý khách hàng
# - Báo cáo doanh thu

`,
        language: 'markdown',
    });
    await vscode.window.showTextDocument(doc);
    // Wait for user to save or close
    const result = await vscode.window.showInformationMessage('Write your application description, then click "Done" when finished', { modal: true }, 'Done', 'Cancel');
    if (result !== 'Done') {
        return undefined;
    }
    // Get content, removing comment lines
    const content = doc.getText();
    const lines = content.split('\n');
    const descriptionLines = lines.filter(line => !line.trim().startsWith('#'));
    const description = descriptionLines.join('\n').trim();
    if (description.length < 10) {
        void vscode.window.showErrorMessage('Description is too short. Please provide more details.');
        return undefined;
    }
    return description;
}
/**
 * Load description from a text file
 */
async function getDescriptionFromFile() {
    const fileUri = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: {
            'Text Files': ['txt', 'md'],
        },
        title: 'Select Description File',
    });
    const selectedFile = fileUri?.[0];
    if (!selectedFile) {
        return undefined;
    }
    try {
        const content = await vscode.workspace.fs.readFile(selectedFile);
        const description = Buffer.from(content).toString('utf-8').trim();
        if (description.length < 10) {
            void vscode.window.showErrorMessage('Description file is too short. Please provide more details.');
            return undefined;
        }
        return description;
    }
    catch (error) {
        void vscode.window.showErrorMessage(`Failed to read file: ${error instanceof Error ? error.message : 'Unknown error'}`);
        return undefined;
    }
}
/**
 * Parse description and detect domain
 */
async function parseDescription(codegenApi, description) {
    return await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Analyzing description...',
        cancellable: false,
    }, async (progress) => {
        try {
            progress.report({ message: 'Detecting language and domain...' });
            const result = await codegenApi.parseMagicDescription({
                description,
                language: 'auto',
            });
            progress.report({ message: 'Building blueprint...' });
            return result;
        }
        catch (error) {
            void vscode.window.showErrorMessage(`Failed to parse description: ${error instanceof Error ? error.message : 'Unknown error'}`);
            return undefined;
        }
    });
}
/**
 * Confirm generation with user
 */
async function confirmGeneration(parseResult) {
    const { blueprint, domain_detection } = parseResult;
    // Build confirmation message
    const moduleList = blueprint.modules
        .map(m => `  • ${m.name}: ${m.entities.join(', ')}`)
        .join('\n');
    const confirmMessage = `
**Detected Domain**: ${domain_detection.domain} (${(domain_detection.confidence * 100).toFixed(0)}% confidence)

**Application**: ${blueprint.name}

**Modules**:
${moduleList}

Do you want to proceed with code generation?`;
    // Create a quick pick with the details
    const result = await vscode.window.showInformationMessage(`Detected: ${blueprint.name} (${domain_detection.domain})`, { modal: true, detail: confirmMessage }, 'Generate', 'Edit Blueprint', 'Cancel');
    if (result === 'Generate') {
        return true;
    }
    if (result === 'Edit Blueprint') {
        // Open blueprint in editor for editing
        const doc = await vscode.workspace.openTextDocument({
            content: JSON.stringify(blueprint, null, 2),
            language: 'json',
        });
        await vscode.window.showTextDocument(doc);
        void vscode.window.showInformationMessage('Edit the blueprint, save, then use "SDLC: Generate from Blueprint" command');
        return false;
    }
    return false;
}
/**
 * Select output directory for generated code
 */
async function selectOutputDirectory() {
    const options = {
        canSelectFiles: false,
        canSelectFolders: true,
        canSelectMany: false,
        title: 'Select Output Directory',
        openLabel: 'Select',
    };
    // Default to workspace folder if available
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const firstWorkspace = workspaceFolders?.[0];
    if (firstWorkspace) {
        options.defaultUri = firstWorkspace.uri;
    }
    const folderUri = await vscode.window.showOpenDialog(options);
    const selectedFolder = folderUri?.[0];
    if (!selectedFolder) {
        return undefined;
    }
    return selectedFolder.fsPath;
}
/**
 * Start magic mode generation with SSE streaming
 */
async function startMagicGeneration(codegenApi, description, outputPath) {
    const config = config_1.ConfigManager.getInstance();
    let sseClient = null;
    const state = {
        sessionId: '',
        description,
        status: 'generating',
        filesGenerated: 0,
        totalLines: 0,
        files: [],
        errors: [],
    };
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: '✨ Magic Mode: Generating code...',
        cancellable: true,
    }, async (progressReporter, cancellationToken) => {
        return new Promise(async (resolve, reject) => {
            try {
                // Start magic generation
                progressReporter.report({ message: 'Starting magic generation...' });
                const result = await codegenApi.startMagicGeneration({
                    description,
                    language: 'auto',
                    output_path: outputPath,
                });
                state.sessionId = result.session_id;
                // Get auth token and create SSE client
                const token = await codegenApi.getAuthToken();
                sseClient = (0, sseClient_1.createCodegenSSEClient)(config.apiUrl, state.sessionId, token);
                // Handle cancellation
                cancellationToken.onCancellationRequested(() => {
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    void codegenApi.cancelGeneration(state.sessionId);
                    resolve();
                });
                // Set up event handlers
                sseClient.on('file_generating', (event) => {
                    const e = event;
                    progressReporter.report({
                        message: `✨ Generating: ${e.path}`,
                    });
                });
                sseClient.on('file_generated', (event) => {
                    const e = event;
                    state.filesGenerated++;
                    state.totalLines += e.lines;
                    const syntaxValid = e.syntax_valid ?? true;
                    state.files.push({
                        path: e.path,
                        content: e.content,
                        lines: e.lines,
                        language: e.language,
                        syntax_valid: syntaxValid,
                        status: syntaxValid ? 'valid' : 'error',
                    });
                    progressReporter.report({
                        message: `✨ Generated: ${e.path}`,
                        increment: 5,
                    });
                });
                sseClient.on('quality_started', () => {
                    state.status = 'validating';
                    progressReporter.report({
                        message: '🔍 Running quality gates...',
                    });
                });
                sseClient.on('quality_gate', (event) => {
                    const e = event;
                    const icon = e.status === 'passed' ? '✅' : '❌';
                    progressReporter.report({
                        message: `${icon} Gate ${e.gate_number}: ${e.gate_name}`,
                        increment: 10,
                    });
                });
                sseClient.on('completed', async (event) => {
                    const e = event;
                    state.status = 'completed';
                    // Write files to disk
                    await writeGeneratedFiles(outputPath, state.files);
                    // Show success with summary
                    const action = await vscode.window.showInformationMessage(`✨ Magic complete! ${e.total_files} files (${e.total_lines} lines) in ${(e.duration_ms / 1000).toFixed(1)}s`, 'Open Folder', 'View Files');
                    if (action === 'Open Folder') {
                        const folderUri = vscode.Uri.file(outputPath);
                        await vscode.commands.executeCommand('vscode.openFolder', folderUri, { forceNewWindow: false });
                    }
                    else if (action === 'View Files') {
                        // Open the first generated file
                        const firstGeneratedFile = state.files[0];
                        if (firstGeneratedFile) {
                            const firstFile = vscode.Uri.file(`${outputPath}/${firstGeneratedFile.path}`);
                            await vscode.window.showTextDocument(firstFile);
                        }
                    }
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    resolve();
                });
                sseClient.on('error', (event) => {
                    const e = event;
                    state.status = 'error';
                    state.errors.push(e.message);
                    // Offer resume option if recovery ID is available
                    if (e.recovery_id) {
                        void vscode.window.showErrorMessage(`Generation error: ${e.message}`, 'Resume', 'Cancel').then(async (action) => {
                            if (action === 'Resume') {
                                await vscode.commands.executeCommand('sdlc.resume', e.recovery_id);
                            }
                        });
                    }
                    else {
                        void vscode.window.showErrorMessage(`Generation error: ${e.message}`);
                    }
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    reject(new Error(e.message));
                });
                sseClient.onError((error) => {
                    state.status = 'error';
                    reject(error);
                });
                // Connect to SSE stream
                await sseClient.connect();
            }
            catch (error) {
                if (sseClient) {
                    sseClient.disconnect();
                }
                reject(error);
            }
        });
    });
}
/**
 * Write generated files to disk
 */
async function writeGeneratedFiles(outputPath, files) {
    for (const file of files) {
        const fullPath = vscode.Uri.file(`${outputPath}/${file.path}`);
        // Ensure directory exists
        const dirPath = vscode.Uri.file(fullPath.fsPath.substring(0, fullPath.fsPath.lastIndexOf('/')));
        try {
            await vscode.workspace.fs.createDirectory(dirPath);
        }
        catch {
            // Directory may already exist
        }
        // Write file
        const content = Buffer.from(file.content, 'utf-8');
        await vscode.workspace.fs.writeFile(fullPath, content);
    }
    logger_1.Logger.info(`Magic mode: Wrote ${files.length} files to ${outputPath}`);
}
//# sourceMappingURL=magicCommand.js.map