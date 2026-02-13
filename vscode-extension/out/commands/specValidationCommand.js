"use strict";
/**
 * Specification Validation Command for SDLC Orchestrator VS Code Extension
 *
 * Sprint 126 - S126-06: Add spec validation to Extension
 * Implements SDLC 6.0.0 SPEC-0002 specification validation in IDE.
 *
 * Features:
 * - Validate current file against SPEC-0002 standard
 * - YAML frontmatter validation
 * - BDD requirements format checking
 * - Tier-specific section validation
 * - Cross-reference validation
 * - Results displayed in Problems panel and Output channel
 *
 * @version 1.0.0
 * @since Sprint 126
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
exports.registerSpecValidationCommand = registerSpecValidationCommand;
const vscode = __importStar(require("vscode"));
const logger_1 = require("../utils/logger");
const telemetryService_1 = require("../services/telemetryService");
// Diagnostic collection for showing validation errors in Problems panel
let diagnosticCollection;
/**
 * Register spec validation commands
 *
 * @param context - VS Code extension context
 * @param codegenApi - CodegenApiService instance
 */
function registerSpecValidationCommand(context, codegenApi) {
    // Create diagnostic collection for spec validation
    diagnosticCollection = vscode.languages.createDiagnosticCollection('sdlc-spec');
    context.subscriptions.push(diagnosticCollection);
    // Register validate spec command
    const validateCommand = vscode.commands.registerCommand('sdlc.validateSpec', async () => {
        await executeValidateSpec(codegenApi);
    });
    context.subscriptions.push(validateCommand);
    logger_1.Logger.info('Spec validation command registered');
    // Register validate spec on save (optional, configurable)
    const onSaveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
        // Only validate markdown files that look like specs
        if (document.languageId === 'markdown' && isSpecFile(document)) {
            const config = vscode.workspace.getConfiguration('sdlc');
            const validateOnSave = config.get('validateSpecOnSave', false);
            if (validateOnSave) {
                await validateDocument(document, codegenApi);
            }
        }
    });
    context.subscriptions.push(onSaveDisposable);
    // Register command to show spec validation results
    const showResultsCommand = vscode.commands.registerCommand('sdlc.showSpecValidationResults', async (result) => {
        if (!result) {
            // No cached result - run validation on current file first
            const editor = vscode.window.activeTextEditor;
            if (editor && editor.document.languageId === 'markdown') {
                await executeValidateSpec(codegenApi);
            }
            else {
                void vscode.window.showWarningMessage('No spec validation results available. Open a spec file and run "SDLC: Validate Spec" first.');
            }
            return;
        }
        showValidationResultsPanel(result);
    });
    context.subscriptions.push(showResultsCommand);
    // Register tier-specific validation command
    const validateWithTierCommand = vscode.commands.registerCommand('sdlc.validateSpecWithTier', async () => {
        await executeValidateSpecWithTier(codegenApi);
    });
    context.subscriptions.push(validateWithTierCommand);
    logger_1.Logger.info('All spec validation commands registered');
}
/**
 * Check if a document is likely a specification file
 */
function isSpecFile(document) {
    const content = document.getText();
    const fileName = document.fileName.toLowerCase();
    // Check filename patterns
    if (fileName.includes('spec-') || fileName.includes('specification')) {
        return true;
    }
    // Check content patterns (YAML frontmatter with spec_id)
    if (content.includes('spec_id:') || content.includes('SPEC-')) {
        return true;
    }
    // Check if in specs directory
    if (fileName.includes('/specs/') || fileName.includes('\\specs\\')) {
        return true;
    }
    // Check if in Technical-Specs directory
    if (fileName.includes('technical-specs') || fileName.includes('Technical-Specs')) {
        return true;
    }
    return false;
}
/**
 * Execute spec validation for current active file
 */
async function executeValidateSpec(codegenApi) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        void vscode.window.showWarningMessage('No active file to validate. Open a specification file first.');
        return;
    }
    const document = editor.document;
    // Check if it's a markdown file
    if (document.languageId !== 'markdown') {
        const proceed = await vscode.window.showWarningMessage('The current file is not a Markdown file. Validate anyway?', 'Yes', 'No');
        if (proceed !== 'Yes') {
            return;
        }
    }
    await validateDocument(document, codegenApi);
}
/**
 * Execute spec validation with tier selection
 */
async function executeValidateSpecWithTier(codegenApi) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        void vscode.window.showWarningMessage('No active file to validate.');
        return;
    }
    // Prompt for tier selection
    const tierOptions = [
        { label: 'LITE', value: 'LITE', description: 'Minimal governance (1-2 people, 4 stages)' },
        { label: 'STANDARD', value: 'STANDARD', description: 'Basic governance (3-10 people, 6 stages)' },
        { label: 'PROFESSIONAL', value: 'PROFESSIONAL', description: 'Full governance (10-50 people, 10 stages)' },
        { label: 'ENTERPRISE', value: 'ENTERPRISE', description: 'Complete governance (50+ people, 11 stages)' },
    ];
    const selected = await vscode.window.showQuickPick(tierOptions, {
        placeHolder: 'Select tier for validation',
        title: 'SDLC 6.0.0 Tier Selection',
    });
    if (!selected) {
        return;
    }
    await validateDocument(editor.document, codegenApi, selected.value);
}
/**
 * Validate a document and show results
 */
async function validateDocument(document, codegenApi, tier) {
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Validating specification...',
        cancellable: false,
    }, async (progress) => {
        try {
            progress.report({ increment: 20, message: 'Reading file...' });
            const content = document.getText();
            const filePath = document.uri.fsPath;
            progress.report({ increment: 40, message: 'Running validation...' });
            // Use local validation (no backend required)
            const result = codegenApi.validateSpecificationLocal(content, tier);
            result.spec_path = filePath;
            progress.report({ increment: 30, message: 'Processing results...' });
            // Update diagnostics
            updateDiagnostics(document, result);
            progress.report({ increment: 10, message: 'Done!' });
            // Show summary notification
            const errorCount = result.errors.length;
            const warningCount = result.warnings.length;
            if (errorCount === 0 && warningCount === 0) {
                void vscode.window.showInformationMessage(`✅ Specification ${result.spec_id} is valid (SDLC 6.0.0)`);
            }
            else if (errorCount === 0) {
                const action = await vscode.window.showWarningMessage(`⚠️ Specification has ${warningCount} warning(s)`, 'Show Details', 'Dismiss');
                if (action === 'Show Details') {
                    showValidationResultsPanel(result);
                }
            }
            else {
                const action = await vscode.window.showErrorMessage(`❌ Specification has ${errorCount} error(s) and ${warningCount} warning(s)`, 'Show Details', 'Dismiss');
                if (action === 'Show Details') {
                    showValidationResultsPanel(result);
                }
            }
            logger_1.Logger.info(`Spec validation complete: ${result.spec_id} - ${errorCount} errors, ${warningCount} warnings`);
            // Track telemetry (Sprint 147 - Product Truth Layer)
            void (0, telemetryService_1.trackSpecValidation)(1, // spec_count
            errorCount === 0 ? 1 : 0, // valid_count
            errorCount > 0 ? 1 : 0);
            void (0, telemetryService_1.trackCommand)('sdlc.validateSpec', errorCount === 0);
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Spec validation failed: ${errorMessage}`);
            void vscode.window.showErrorMessage(`Specification validation failed: ${errorMessage}`);
            // Track telemetry for failed validation (Sprint 147)
            void (0, telemetryService_1.trackCommand)('sdlc.validateSpec', false);
        }
    });
}
/**
 * Update VS Code diagnostics (Problems panel) with validation results
 */
function updateDiagnostics(document, result) {
    const diagnostics = [];
    // Add errors
    for (const error of result.errors) {
        const line = error.line_number ? error.line_number - 1 : 0;
        const range = new vscode.Range(line, 0, line, Number.MAX_SAFE_INTEGER);
        const diagnostic = new vscode.Diagnostic(range, `[${error.code}] ${error.message}`, vscode.DiagnosticSeverity.Error);
        diagnostic.source = 'SDLC Spec Validator';
        diagnostic.code = error.code;
        if (error.suggestion) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(new vscode.Location(document.uri, range), `Suggestion: ${error.suggestion}`),
            ];
        }
        diagnostics.push(diagnostic);
    }
    // Add warnings
    for (const warning of result.warnings) {
        const line = warning.line_number ? warning.line_number - 1 : 0;
        const range = new vscode.Range(line, 0, line, Number.MAX_SAFE_INTEGER);
        const diagnostic = new vscode.Diagnostic(range, `[${warning.code}] ${warning.message}`, vscode.DiagnosticSeverity.Warning);
        diagnostic.source = 'SDLC Spec Validator';
        diagnostic.code = warning.code;
        if (warning.suggestion) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(new vscode.Location(document.uri, range), `Suggestion: ${warning.suggestion}`),
            ];
        }
        diagnostics.push(diagnostic);
    }
    diagnosticCollection.set(document.uri, diagnostics);
}
/**
 * Show validation results in an output channel
 */
function showValidationResultsPanel(result) {
    if (!result || !result.spec_id) {
        void vscode.window.showWarningMessage('No spec validation results available. Run "SDLC: Validate Spec" on a specification file first.');
        return;
    }
    const outputChannel = vscode.window.createOutputChannel('SDLC Spec Validation');
    outputChannel.clear();
    outputChannel.appendLine('═'.repeat(70));
    outputChannel.appendLine('  SDLC 6.0.0 SPECIFICATION VALIDATION REPORT');
    outputChannel.appendLine('═'.repeat(70));
    outputChannel.appendLine('');
    // Summary
    outputChannel.appendLine(`Spec ID:     ${result.spec_id}`);
    outputChannel.appendLine(`Version:     ${result.version}`);
    outputChannel.appendLine(`Tier:        ${result.tier.join(', ')}`);
    outputChannel.appendLine(`Path:        ${result.spec_path}`);
    outputChannel.appendLine(`Validated:   ${result.validation_timestamp}`);
    outputChannel.appendLine(`Validator:   v${result.validator_version}`);
    outputChannel.appendLine('');
    // Status
    const statusIcon = result.valid ? '✅' : '❌';
    outputChannel.appendLine(`Status:      ${statusIcon} ${result.valid ? 'VALID' : 'INVALID'}`);
    outputChannel.appendLine(`Errors:      ${result.errors.length}`);
    outputChannel.appendLine(`Warnings:    ${result.warnings.length}`);
    outputChannel.appendLine('');
    // Frontmatter Validation
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine('FRONTMATTER VALIDATION');
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine(`Valid:       ${result.frontmatter.valid ? '✅ Yes' : '❌ No'}`);
    if (result.frontmatter.required_fields_present.length > 0) {
        outputChannel.appendLine(`Present:     ${result.frontmatter.required_fields_present.join(', ')}`);
    }
    if (result.frontmatter.required_fields_missing.length > 0) {
        outputChannel.appendLine(`Missing:     ${result.frontmatter.required_fields_missing.join(', ')}`);
    }
    outputChannel.appendLine('');
    // BDD Validation
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine('BDD REQUIREMENTS VALIDATION');
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine(`Valid:       ${result.bdd_validation.valid ? '✅ Yes' : '⚠️ Check needed'}`);
    outputChannel.appendLine(`Total:       ${result.bdd_validation.total_requirements} requirement statements`);
    outputChannel.appendLine(`Coverage:    ${result.bdd_validation.coverage_percentage}%`);
    outputChannel.appendLine('');
    // Tier Sections
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine(`TIER-SPECIFIC SECTIONS (${result.tier_sections.tier})`);
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine(`Valid:       ${result.tier_sections.valid ? '✅ Yes' : '⚠️ Missing sections'}`);
    if (result.tier_sections.present_sections.length > 0) {
        outputChannel.appendLine(`Present:     ${result.tier_sections.present_sections.join(', ')}`);
    }
    if (result.tier_sections.missing_sections.length > 0) {
        outputChannel.appendLine(`Missing:     ${result.tier_sections.missing_sections.join(', ')}`);
    }
    outputChannel.appendLine('');
    // Cross References
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine('CROSS-REFERENCE VALIDATION');
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine(`Valid:       ${result.cross_references.valid ? '✅ Yes' : '❌ No'}`);
    outputChannel.appendLine(`Total refs:  ${result.cross_references.total_references}`);
    outputChannel.appendLine('');
    // Errors Detail
    if (result.errors.length > 0) {
        outputChannel.appendLine('─'.repeat(70));
        outputChannel.appendLine('ERRORS');
        outputChannel.appendLine('─'.repeat(70));
        for (const error of result.errors) {
            outputChannel.appendLine(`  ❌ [${error.code}] ${error.message}`);
            if (error.line_number) {
                outputChannel.appendLine(`     Line: ${error.line_number}`);
            }
            if (error.suggestion) {
                outputChannel.appendLine(`     💡 ${error.suggestion}`);
            }
            outputChannel.appendLine('');
        }
    }
    // Warnings Detail
    if (result.warnings.length > 0) {
        outputChannel.appendLine('─'.repeat(70));
        outputChannel.appendLine('WARNINGS');
        outputChannel.appendLine('─'.repeat(70));
        for (const warning of result.warnings) {
            outputChannel.appendLine(`  ⚠️ [${warning.code}] ${warning.message}`);
            if (warning.suggestion) {
                outputChannel.appendLine(`     💡 ${warning.suggestion}`);
            }
            outputChannel.appendLine('');
        }
    }
    outputChannel.appendLine('═'.repeat(70));
    outputChannel.appendLine('  END OF VALIDATION REPORT');
    outputChannel.appendLine('═'.repeat(70));
    outputChannel.show();
}
//# sourceMappingURL=specValidationCommand.js.map