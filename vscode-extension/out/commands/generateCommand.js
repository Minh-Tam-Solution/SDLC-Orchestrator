"use strict";
/**
 * Generate Command - Code Generation from Blueprint
 *
 * Implements the sdlc.generate command for generating code
 * from an App Blueprint specification.
 *
 * Sprint 53 Day 1 - Generate Command Implementation
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
exports.registerGenerateCommand = registerGenerateCommand;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const errors_1 = require("../utils/errors");
const sseClient_1 = require("../services/sseClient");
const config_1 = require("../utils/config");
/**
 * Register the generate command
 */
function registerGenerateCommand(context, codegenApi) {
    const command = vscode.commands.registerCommand('sdlc.generate', async () => {
        await executeGenerateCommand(codegenApi);
    });
    context.subscriptions.push(command);
    logger_1.Logger.info('Generate command registered');
}
/**
 * Execute the generate command
 */
async function executeGenerateCommand(codegenApi) {
    try {
        // Step 1: Get blueprint from user
        const blueprint = await getBlueprintFromUser();
        if (!blueprint) {
            return; // User cancelled
        }
        // Step 2: Validate blueprint
        const validation = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Validating blueprint...',
            cancellable: false,
        }, async () => {
            return await codegenApi.validateBlueprint(blueprint);
        });
        if (!validation.valid) {
            const errorMessage = validation.errors.join('\n');
            void vscode.window.showErrorMessage(`Blueprint validation failed:\n${errorMessage}`);
            return;
        }
        if (validation.warnings.length > 0) {
            const warningMessage = validation.warnings.join('\n');
            const proceed = await vscode.window.showWarningMessage(`Blueprint has warnings:\n${warningMessage}`, 'Continue', 'Cancel');
            if (proceed !== 'Continue') {
                return;
            }
        }
        // Step 3: Select output directory
        const outputPath = await selectOutputDirectory();
        if (!outputPath) {
            return; // User cancelled
        }
        // Step 4: Start generation with streaming
        await startGenerationWithStreaming(codegenApi, blueprint, outputPath);
    }
    catch (error) {
        await (0, errors_1.handleError)(error, {
            showNotification: true,
            notificationType: 'error',
        });
    }
}
/**
 * Get blueprint from user input
 */
async function getBlueprintFromUser() {
    // Option 1: Select from file
    // Option 2: Use current editor content
    // Option 3: Use template
    const options = [
        {
            label: '$(file-code) From File',
            description: 'Load blueprint from JSON file',
            value: 'file',
        },
        {
            label: '$(edit) From Editor',
            description: 'Use current editor content as blueprint',
            value: 'editor',
        },
        {
            label: '$(package) From Template',
            description: 'Start from a domain template',
            value: 'template',
        },
    ];
    const selected = await vscode.window.showQuickPick(options, {
        placeHolder: 'How would you like to provide the blueprint?',
    });
    if (!selected) {
        return undefined;
    }
    switch (selected.value) {
        case 'file':
            return await loadBlueprintFromFile();
        case 'editor':
            return await loadBlueprintFromEditor();
        case 'template':
            return await loadBlueprintFromTemplate();
        default:
            return undefined;
    }
}
/**
 * Load blueprint from a JSON file
 */
async function loadBlueprintFromFile() {
    const fileUri = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: {
            'Blueprint Files': ['json'],
        },
        title: 'Select Blueprint File',
    });
    if (!fileUri || fileUri.length === 0) {
        return undefined;
    }
    const selectedFile = fileUri[0];
    if (!selectedFile) {
        return undefined;
    }
    try {
        const content = await vscode.workspace.fs.readFile(selectedFile);
        const blueprint = JSON.parse(Buffer.from(content).toString('utf-8'));
        return blueprint;
    }
    catch (error) {
        void vscode.window.showErrorMessage(`Failed to load blueprint: ${error instanceof Error ? error.message : 'Unknown error'}`);
        return undefined;
    }
}
/**
 * Load blueprint from current editor
 */
async function loadBlueprintFromEditor() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        void vscode.window.showErrorMessage('No active editor');
        return undefined;
    }
    try {
        const content = editor.document.getText();
        const blueprint = JSON.parse(content);
        return blueprint;
    }
    catch (error) {
        void vscode.window.showErrorMessage(`Failed to parse blueprint from editor: ${error instanceof Error ? error.message : 'Invalid JSON'}`);
        return undefined;
    }
}
/**
 * Load blueprint from a domain template
 */
async function loadBlueprintFromTemplate() {
    // Show available templates (hardcoded for now, will be fetched from API)
    const templates = [
        {
            label: '$(globe) E-commerce',
            description: 'Online store with products, orders, payments',
            value: 'ecommerce',
        },
        {
            label: '$(person) HRM',
            description: 'Human Resource Management system',
            value: 'hrm',
        },
        {
            label: '$(graph) CRM',
            description: 'Customer Relationship Management',
            value: 'crm',
        },
        {
            label: '$(book) LMS',
            description: 'Learning Management System',
            value: 'lms',
        },
    ];
    const selected = await vscode.window.showQuickPick(templates, {
        placeHolder: 'Select a domain template',
    });
    if (!selected) {
        return undefined;
    }
    // Return a basic template structure (will be replaced by API call)
    const blueprint = {
        name: `My ${selected.label.replace(/\$\([^)]+\)\s*/, '')} App`,
        version: '1.0.0',
        business_domain: selected.value,
        description: selected.description,
        modules: getTemplateModules(selected.value),
    };
    // Allow user to edit the name
    const name = await vscode.window.showInputBox({
        prompt: 'Enter application name',
        value: blueprint.name,
        validateInput: (value) => {
            if (!value || value.trim().length === 0) {
                return 'Application name is required';
            }
            return null;
        },
    });
    if (!name) {
        return undefined;
    }
    blueprint.name = name;
    return blueprint;
}
/**
 * Get template modules for a domain
 */
function getTemplateModules(domain) {
    const templates = {
        ecommerce: [
            { name: 'catalog', entities: ['Product', 'Category', 'Brand'], description: 'Product catalog management' },
            { name: 'orders', entities: ['Order', 'OrderItem', 'Cart'], description: 'Order processing' },
            { name: 'customers', entities: ['Customer', 'Address'], description: 'Customer management' },
            { name: 'payments', entities: ['Payment', 'Invoice'], description: 'Payment processing' },
        ],
        hrm: [
            { name: 'employees', entities: ['Employee', 'Department', 'Position'], description: 'Employee management' },
            { name: 'attendance', entities: ['Attendance', 'Leave', 'Holiday'], description: 'Time tracking' },
            { name: 'payroll', entities: ['Salary', 'Payslip', 'Deduction'], description: 'Payroll processing' },
        ],
        crm: [
            { name: 'contacts', entities: ['Contact', 'Company', 'Lead'], description: 'Contact management' },
            { name: 'deals', entities: ['Deal', 'Pipeline', 'Stage'], description: 'Deal tracking' },
            { name: 'activities', entities: ['Activity', 'Task', 'Meeting'], description: 'Activity logging' },
        ],
        lms: [
            { name: 'courses', entities: ['Course', 'Lesson', 'Module'], description: 'Course management' },
            { name: 'students', entities: ['Student', 'Enrollment', 'Progress'], description: 'Student tracking' },
            { name: 'assessments', entities: ['Quiz', 'Assignment', 'Grade'], description: 'Assessment system' },
        ],
    };
    return templates[domain] || [];
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
 * Start code generation with SSE streaming
 */
async function startGenerationWithStreaming(codegenApi, blueprint, outputPath) {
    const config = config_1.ConfigManager.getInstance();
    let sseClient = null;
    const progress = {
        sessionId: '',
        status: 'connecting',
        filesGenerated: 0,
        totalLines: 0,
        gatesPassed: 0,
        totalGates: 4,
        files: [],
        errors: [],
    };
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Generating code...',
        cancellable: true,
    }, async (progressReporter, cancellationToken) => {
        return new Promise(async (resolve, reject) => {
            try {
                // Start generation and get session ID
                progressReporter.report({ message: 'Starting generation...' });
                const result = await codegenApi.startGeneration({
                    blueprint,
                    output_path: outputPath,
                });
                progress.sessionId = result.session_id;
                progress.status = 'generating';
                // Get auth token and create SSE client
                const token = await codegenApi.getAuthToken();
                sseClient = (0, sseClient_1.createCodegenSSEClient)(config.apiUrl, progress.sessionId, token);
                // Handle cancellation
                cancellationToken.onCancellationRequested(() => {
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    void codegenApi.cancelGeneration(progress.sessionId);
                    resolve();
                });
                // Set up event handlers
                sseClient.on('file_generating', (event) => {
                    const e = event;
                    progress.currentFile = e.path;
                    progressReporter.report({
                        message: `Generating: ${e.path}`,
                    });
                });
                sseClient.on('file_generated', (event) => {
                    const e = event;
                    progress.filesGenerated++;
                    progress.totalLines += e.lines;
                    const syntaxValid = e.syntax_valid ?? true;
                    progress.files.push({
                        path: e.path,
                        content: e.content,
                        lines: e.lines,
                        language: e.language,
                        syntax_valid: syntaxValid,
                        status: syntaxValid ? 'valid' : 'error',
                    });
                    progressReporter.report({
                        message: `Generated: ${e.path} (${e.lines} lines)`,
                        increment: 5,
                    });
                });
                sseClient.on('quality_started', () => {
                    progress.status = 'validating';
                    progressReporter.report({
                        message: 'Running quality gates...',
                    });
                });
                sseClient.on('quality_gate', (event) => {
                    const e = event;
                    if (e.status === 'passed') {
                        progress.gatesPassed++;
                    }
                    progressReporter.report({
                        message: `Gate ${e.gate_number}: ${e.gate_name} - ${e.status}`,
                        increment: 10,
                    });
                });
                sseClient.on('completed', async (event) => {
                    const e = event;
                    progress.status = 'completed';
                    // Write files to disk
                    await writeGeneratedFiles(outputPath, progress.files);
                    void vscode.window.showInformationMessage(`Code generation completed! ${e.total_files} files (${e.total_lines} lines) in ${(e.duration_ms / 1000).toFixed(1)}s`);
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    resolve();
                });
                sseClient.on('error', (event) => {
                    const e = event;
                    progress.status = 'error';
                    progress.errors.push(e.message);
                    void vscode.window.showErrorMessage(`Generation error: ${e.message}`);
                    if (sseClient) {
                        sseClient.disconnect();
                    }
                    reject(new Error(e.message));
                });
                sseClient.onError((error) => {
                    progress.status = 'error';
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
    logger_1.Logger.info(`Wrote ${files.length} files to ${outputPath}`);
}
//# sourceMappingURL=generateCommand.js.map