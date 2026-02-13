/**
 * E2E API Testing Validation Command for SDLC Orchestrator VS Code Extension
 *
 * Sprint 139 - Task 1: E2E Validate Command
 * Implements RFC-SDLC-602 E2E API Testing validation in IDE.
 *
 * Features:
 * - Validate E2E testing compliance (SDLC 6.0.2)
 * - Calls real CLI `sdlcctl e2e validate` (Zero Mock Policy)
 * - Display results in Output channel and Problems panel
 * - Optional --init for folder structure setup
 *
 * Reference:
 * - RFC-SDLC-602-E2E-API-TESTING
 * - SDLC Framework 6.0.2
 * - Skill: e2e-api-testing (6-phase workflow)
 *
 * CTO Requirements (Non-Negotiable):
 * - No placeholder code
 * - Real CLI integration (not mocked data)
 * - Error handling required
 * - Dogfooding mandatory
 *
 * @version 1.0.0
 * @since Sprint 139
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';
import { Logger } from '../utils/logger';
import { trackCommand, trackValidationRun } from '../services/telemetryService';
import type {
    E2EValidationResult,
    E2ETestingReport,
} from '../types/evidence';

const execAsync = promisify(exec);

// Diagnostic collection for E2E validation errors
let e2eDiagnosticCollection: vscode.DiagnosticCollection;

/**
 * E2E Validation configuration
 */
interface E2EValidationConfig {
    minPassRate: number;
    strict: boolean;
    init: boolean;
}

/**
 * Register E2E validation commands
 *
 * @param context - VS Code extension context
 */
export function registerE2EValidateCommand(
    context: vscode.ExtensionContext
): void {
    // Create diagnostic collection for E2E validation
    e2eDiagnosticCollection = vscode.languages.createDiagnosticCollection('sdlc-e2e');
    context.subscriptions.push(e2eDiagnosticCollection);

    // Register main E2E validate command
    const validateCommand = vscode.commands.registerCommand(
        'sdlc.e2eValidate',
        async () => {
            await executeE2EValidate({ minPassRate: 80, strict: false, init: false });
        }
    );
    context.subscriptions.push(validateCommand);
    Logger.info('E2E validate command registered');

    // Register E2E validate with options command
    const validateWithOptionsCommand = vscode.commands.registerCommand(
        'sdlc.e2eValidateWithOptions',
        async () => {
            await executeE2EValidateWithOptions();
        }
    );
    context.subscriptions.push(validateWithOptionsCommand);

    // Register E2E init command (creates folder structure)
    const initCommand = vscode.commands.registerCommand(
        'sdlc.e2eInit',
        async () => {
            await executeE2EInit();
        }
    );
    context.subscriptions.push(initCommand);

    // Register show E2E results command
    const showResultsCommand = vscode.commands.registerCommand(
        'sdlc.showE2EResults',
        (result?: E2EValidationResult) => {
            if (!result) {
                void vscode.window.showWarningMessage(
                    'No E2E validation results available. Run "SDLC: E2E Validate" first.'
                );
                return;
            }
            showE2EResultsPanel(result);
        }
    );
    context.subscriptions.push(showResultsCommand);

    Logger.info('All E2E validation commands registered');
}

/**
 * Execute E2E validation with user options
 */
async function executeE2EValidateWithOptions(): Promise<void> {
    // Prompt for minimum pass rate
    const passRateInput = await vscode.window.showInputBox({
        prompt: 'Minimum pass rate percentage (0-100)',
        value: '80',
        validateInput: (value) => {
            const num = parseInt(value, 10);
            if (isNaN(num) || num < 0 || num > 100) {
                return 'Please enter a number between 0 and 100';
            }
            return null;
        },
    });

    if (!passRateInput) {
        return;
    }

    // Prompt for strict mode
    const strictMode = await vscode.window.showQuickPick(
        [
            { label: 'Normal', value: false, description: 'Allow warnings, fail only on errors' },
            { label: 'Strict', value: true, description: 'Fail on any warning or error' },
        ],
        { placeHolder: 'Select validation mode' }
    );

    if (!strictMode) {
        return;
    }

    await executeE2EValidate({
        minPassRate: parseInt(passRateInput, 10),
        strict: strictMode.value,
        init: false,
    });
}

/**
 * Execute E2E validation using real CLI (Zero Mock Policy)
 *
 * CTO Mandate: Call real sdlcctl e2e validate, not simulated data
 */
async function executeE2EValidate(config: E2EValidationConfig): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    if (!workspaceRoot) {
        void vscode.window.showErrorMessage('No workspace folder open. Please open a project folder.');
        return;
    }

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Validating E2E Testing Compliance...',
            cancellable: false,
        },
        async (progress) => {
            try {
                progress.report({ increment: 10, message: 'Checking CLI availability...' });

                // Check if sdlcctl is available
                const cliAvailable = await checkCLIAvailable();

                if (cliAvailable) {
                    // Use real CLI (preferred - Zero Mock Policy)
                    progress.report({ increment: 30, message: 'Running sdlcctl e2e validate...' });
                    const result = await executeCLIValidation(workspaceRoot, config);

                    progress.report({ increment: 40, message: 'Processing results...' });
                    updateE2EDiagnostics(result);

                    progress.report({ increment: 20, message: 'Done!' });
                    await showValidationSummary(result, config);

                    Logger.info(`E2E validation complete: ${result.passRate}% pass rate, ${result.errors.length} errors`);

                    // Track telemetry (Sprint 147 - Product Truth Layer)
                    void trackValidationRun('extension', 'e2e', result.valid ? 'pass' : 'fail', result.errors.length);
                    void trackCommand('sdlc.e2eValidate', result.valid);
                } else {
                    // Fallback to local validation (when CLI not installed)
                    Logger.warn('sdlcctl not found, using local validation');
                    progress.report({ increment: 20, message: 'CLI not found, using local validation...' });

                    const stage05Path = findStage05Path(workspaceRoot);
                    if (!stage05Path) {
                        const initAction = await vscode.window.showWarningMessage(
                            'Stage 05 (Testing) folder not found. Would you like to initialize E2E testing structure?',
                            'Initialize',
                            'Cancel'
                        );
                        if (initAction === 'Initialize') {
                            await executeE2EInit();
                        }
                        return;
                    }

                    progress.report({ increment: 30, message: 'Loading test artifacts...' });
                    const testResults = await loadTestResults(workspaceRoot, stage05Path);

                    progress.report({ increment: 20, message: 'Validating compliance...' });
                    const result = validateE2ECompliance(workspaceRoot, stage05Path, testResults, config);

                    progress.report({ increment: 10, message: 'Done!' });
                    updateE2EDiagnostics(result);
                    await showValidationSummary(result, config);

                    Logger.info(`E2E validation (local) complete: ${result.passRate}% pass rate`);

                    // Track telemetry (Sprint 147 - Product Truth Layer)
                    void trackValidationRun('extension', 'e2e', result.valid ? 'pass' : 'fail', result.errors.length);
                    void trackCommand('sdlc.e2eValidate', result.valid);
                }

            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                Logger.error(`E2E validation failed: ${errorMessage}`);
                void vscode.window.showErrorMessage(
                    `E2E validation failed: ${errorMessage}\n` +
                    `Check Output → SDLC Orchestrator for details.`
                );

                // Track telemetry for failed validation (Sprint 147)
                void trackCommand('sdlc.e2eValidate', false);
            }
        }
    );
}

/**
 * Check if sdlcctl CLI is available
 */
async function checkCLIAvailable(): Promise<boolean> {
    try {
        await execAsync('sdlcctl --version');
        return true;
    } catch {
        return false;
    }
}

/**
 * Execute E2E validation using real CLI
 *
 * Calls: sdlcctl e2e validate --format json
 */
async function executeCLIValidation(
    workspaceRoot: string,
    config: E2EValidationConfig
): Promise<E2EValidationResult> {
    const args = [
        'e2e',
        'validate',
        '--project-path', workspaceRoot,
        '--min-pass-rate', config.minPassRate.toString(),
        '--format', 'json',
    ];

    if (config.strict) {
        args.push('--strict');
    }

    const command = `sdlcctl ${args.join(' ')}`;
    Logger.info(`Executing: ${command}`);

    try {
        const { stdout, stderr } = await execAsync(command, {
            cwd: workspaceRoot,
            timeout: 60000, // 60 second timeout
        });

        if (stderr) {
            Logger.warn(`CLI stderr: ${stderr}`);
        }

        // Parse JSON output from CLI
        const cliResult = JSON.parse(stdout);

        // Transform CLI result to Extension result format
        return transformCLIResult(cliResult, workspaceRoot);

    } catch (error) {
        // Handle CLI execution error
        if (error instanceof Error && 'code' in error) {
            const execError = error as Error & { code: number; stdout?: string; stderr?: string };

            // CLI exited with non-zero code (validation failed)
            if (execError.stdout) {
                try {
                    const cliResult = JSON.parse(execError.stdout);
                    return transformCLIResult(cliResult, workspaceRoot);
                } catch {
                    // JSON parse failed
                }
            }

            throw new Error(
                `CLI execution failed (code ${execError.code}): ${execError.stderr || execError.message}`
            );
        }
        throw error;
    }
}

/**
 * Transform CLI result to Extension result format
 */
function transformCLIResult(cliResult: {
    has_e2e_report?: boolean;
    has_api_documentation?: boolean;
    e2e_pass_rate?: number;
    total_endpoints?: number;
    failed_endpoints?: number;
    min_pass_rate_threshold?: number;
    violations?: string[];
    allow_transition?: boolean;
}, workspaceRoot: string): E2EValidationResult {
    const violations = cliResult.violations || [];
    const errors: Array<{ code: string; message: string; path?: string }> = [];
    const warnings: Array<{ code: string; message: string; path?: string }> = [];

    // Parse violations into errors/warnings
    for (const violation of violations) {
        if (violation.includes('E2E_PASS_RATE_LOW') || violation.includes('MISSING')) {
            const match = violation.match(/^([A-Z_]+):\s*(.+)$/);
            if (match) {
                errors.push({
                    code: match[1] || 'E2E-ERROR',
                    message: match[2] || violation,
                });
            } else {
                errors.push({
                    code: 'E2E-ERROR',
                    message: violation,
                });
            }
        } else {
            warnings.push({
                code: 'E2E-WARN',
                message: violation,
            });
        }
    }

    // Build checklist from CLI result
    const checklist: Array<{ item: string; passed: boolean; details?: string }> = [
        {
            item: 'E2E Test Report',
            passed: cliResult.has_e2e_report === true,
            details: cliResult.has_e2e_report ? 'Found' : 'Not found',
        },
        {
            item: 'API Documentation Reference',
            passed: cliResult.has_api_documentation === true,
            details: cliResult.has_api_documentation ? 'Found' : 'Not found',
        },
        {
            item: `Pass Rate >= ${cliResult.min_pass_rate_threshold || 80}%`,
            passed: (cliResult.e2e_pass_rate || 0) >= (cliResult.min_pass_rate_threshold || 80),
            details: `Actual: ${(cliResult.e2e_pass_rate || 0).toFixed(1)}%`,
        },
    ];

    return {
        valid: cliResult.allow_transition === true,
        passRate: cliResult.e2e_pass_rate || 0,
        totalEndpoints: cliResult.total_endpoints || 0,
        testedEndpoints: cliResult.total_endpoints || 0,
        passedEndpoints: (cliResult.total_endpoints || 0) - (cliResult.failed_endpoints || 0),
        failedEndpoints: cliResult.failed_endpoints || 0,
        errors,
        warnings,
        checklist,
        testResults: null,
        stage05Path: path.join(workspaceRoot, 'docs', '05-Testing-Quality'),
        validationTimestamp: new Date().toISOString(),
    };
}

/**
 * Execute E2E initialization (create folder structure)
 */
async function executeE2EInit(): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    if (!workspaceRoot) {
        void vscode.window.showErrorMessage('No workspace folder open.');
        return;
    }

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Initializing E2E Testing Structure...',
            cancellable: false,
        },
        async (progress) => {
            try {
                progress.report({ increment: 20, message: 'Creating folders...' });

                // Create SDLC 6.0.2 E2E folder structure
                const stage05Base = path.join(workspaceRoot, 'docs', '05-deploy');
                const e2eFolders = [
                    path.join(stage05Base, '03-E2E-Testing'),
                    path.join(stage05Base, '03-E2E-Testing', 'reports'),
                    path.join(stage05Base, '03-E2E-Testing', 'scripts'),
                    path.join(stage05Base, '03-E2E-Testing', 'artifacts'),
                ];

                // Also check for alternate stage structure
                const altStage05 = path.join(workspaceRoot, 'docs', '05-Testing-Quality');
                if (fs.existsSync(path.dirname(altStage05))) {
                    e2eFolders.push(
                        path.join(altStage05, '03-E2E-Testing'),
                        path.join(altStage05, '03-E2E-Testing', 'reports'),
                        path.join(altStage05, '03-E2E-Testing', 'scripts'),
                        path.join(altStage05, '03-E2E-Testing', 'artifacts'),
                    );
                }

                for (const folder of e2eFolders) {
                    if (!fs.existsSync(folder)) {
                        fs.mkdirSync(folder, { recursive: true });
                        Logger.info(`Created folder: ${folder}`);
                    }
                }

                progress.report({ increment: 40, message: 'Creating template files...' });

                // Create template test script
                const e2eTestingPath = e2eFolders[0];
                if (e2eTestingPath && fs.existsSync(e2eTestingPath)) {
                    await createTemplateFiles(e2eTestingPath);
                }

                progress.report({ increment: 40, message: 'Done!' });

                void vscode.window.showInformationMessage(
                    '✅ E2E Testing structure initialized. Check docs/05-*/03-E2E-Testing/'
                );

            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                Logger.error(`E2E init failed: ${errorMessage}`);
                void vscode.window.showErrorMessage(`E2E initialization failed: ${errorMessage}`);
            }
        }
    );
}

/**
 * Create template files for E2E testing
 */
async function createTemplateFiles(e2eTestingPath: string): Promise<void> {
    // Create README
    const readmePath = path.join(e2eTestingPath, 'README.md');
    if (!fs.existsSync(readmePath)) {
        const readmeContent = `# E2E API Testing

## SDLC 6.0.2 - RFC-SDLC-602 E2E API Testing

This folder contains E2E API testing artifacts following the RFC-SDLC-602 specification.

## Folder Structure

\`\`\`
03-E2E-Testing/
├── README.md              # This file
├── reports/               # Test execution reports
│   └── E2E-API-REPORT-YYYY-MM-DD.md
├── scripts/               # Test scripts
│   └── test_all_endpoints.py
└── artifacts/             # Test artifacts
    └── auth_token.txt     # Authentication tokens
\`\`\`

## 6-Phase Workflow

1. **Phase 0**: Check Stage 03 documentation (OpenAPI spec)
2. **Phase 1**: Setup & Authentication
3. **Phase 2**: Test execution
4. **Phase 3**: Report generation
5. **Phase 4**: Update Stage 03 documentation
6. **Phase 5**: Cross-reference validation

## Commands

- \`sdlcctl e2e validate\` - Validate E2E testing compliance
- \`sdlcctl e2e cross-reference\` - Validate Stage 03 ↔ 05 links
- \`sdlcctl e2e generate-report\` - Generate test report

## References

- [RFC-SDLC-602](../../01-planning/02-RFCs/RFC-SDLC-602-E2E-API-TESTING.md)
- [Stage 03 OpenAPI](../../03-integrate/01-api-contracts/openapi.json)
`;
        fs.writeFileSync(readmePath, readmeContent);
        Logger.info(`Created template: ${readmePath}`);
    }

    // Create example test script
    const scriptPath = path.join(e2eTestingPath, 'scripts', 'test_all_endpoints.py');
    if (!fs.existsSync(scriptPath)) {
        const scriptContent = `#!/usr/bin/env python3
"""
E2E API Test Script - SDLC 6.0.2

This script tests all API endpoints defined in Stage 03 OpenAPI specification.
Reference: RFC-SDLC-602-E2E-API-TESTING

Usage:
    python test_all_endpoints.py --base-url http://localhost:8000 --auth-token $TOKEN
"""

import argparse
import json
import requests
from datetime import datetime
from pathlib import Path


def load_openapi_spec(spec_path: str) -> dict:
    """Load OpenAPI specification from Stage 03."""
    with open(spec_path, "r") as f:
        return json.load(f)


def test_endpoint(base_url: str, method: str, path: str, auth_token: str | None) -> dict:
    """Test a single endpoint."""
    url = f"{base_url}{path}"
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        response = requests.request(method, url, headers=headers, timeout=30)
        return {
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response_time_ms": response.elapsed.total_seconds() * 1000,
        }
    except Exception as e:
        return {
            "method": method,
            "path": path,
            "status_code": 0,
            "success": False,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="E2E API Test Script")
    parser.add_argument("--base-url", required=True, help="API base URL")
    parser.add_argument("--auth-token", help="Bearer token for authentication")
    parser.add_argument("--openapi", default="../../03-integrate/01-api-contracts/openapi.json")
    parser.add_argument("--output", default="../reports/test_results.json")
    args = parser.parse_args()

    print(f"E2E API Testing - {datetime.now().isoformat()}")
    print(f"Base URL: {args.base_url}")

    # Load OpenAPI spec
    spec = load_openapi_spec(args.openapi)

    results = []
    passed = 0
    failed = 0

    # Test each endpoint
    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post", "put", "patch", "delete"]:
            if method in methods:
                result = test_endpoint(args.base_url, method.upper(), path, args.auth_token)
                results.append(result)
                if result["success"]:
                    passed += 1
                    print(f"  ✅ {method.upper()} {path}")
                else:
                    failed += 1
                    print(f"  ❌ {method.upper()} {path}")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "base_url": args.base_url,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / len(results) * 100) if results else 0,
        "results": results,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\\nResults: {passed}/{len(results)} passed ({output['pass_rate']:.1f}%)")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
`;
        fs.mkdirSync(path.dirname(scriptPath), { recursive: true });
        fs.writeFileSync(scriptPath, scriptContent);
        Logger.info(`Created template: ${scriptPath}`);
    }
}

/**
 * Get workspace root path
 */
function getWorkspaceRoot(): string | undefined {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        return undefined;
    }
    return folders[0]?.uri.fsPath;
}

/**
 * Find Stage 05 path (supports multiple naming conventions)
 */
function findStage05Path(workspaceRoot: string): string | undefined {
    const possiblePaths = [
        path.join(workspaceRoot, 'docs', '05-deploy'),
        path.join(workspaceRoot, 'docs', '05-Testing-Quality'),
        path.join(workspaceRoot, 'docs', '05-test'),
        path.join(workspaceRoot, 'docs', '05-TEST'),
        path.join(workspaceRoot, 'Stage-05'),
    ];

    for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }

    return undefined;
}

/**
 * Load test results from Stage 05
 */
async function loadTestResults(
    workspaceRoot: string,
    stage05Path: string
): Promise<E2ETestingReport | null> {
    // Look for test results JSON file
    const possibleResultFiles = [
        path.join(stage05Path, '03-E2E-Testing', 'reports', 'test_results.json'),
        path.join(stage05Path, 'E2E-Testing', 'reports', 'test_results.json'),
        path.join(stage05Path, 'test_results.json'),
        path.join(workspaceRoot, 'test_results.json'),
    ];

    for (const resultFile of possibleResultFiles) {
        if (fs.existsSync(resultFile)) {
            try {
                const content = fs.readFileSync(resultFile, 'utf-8');
                const data = JSON.parse(content);
                return {
                    timestamp: data.timestamp || new Date().toISOString(),
                    totalEndpoints: data.total || 0,
                    testedEndpoints: data.passed + data.failed || 0,
                    passedEndpoints: data.passed || 0,
                    failedEndpoints: data.failed || 0,
                    passRate: data.pass_rate || 0,
                    coverage: (data.results || []).map((r: { method: string; path: string; success: boolean; status_code: number }) => ({
                        method: r.method,
                        path: r.path,
                        tested: true,
                        passed: r.success,
                        statusCode: r.status_code,
                    })),
                    reportPath: resultFile,
                };
            } catch (e) {
                Logger.warn(`Failed to parse test results from ${resultFile}: ${e}`);
            }
        }
    }

    return null;
}

/**
 * Validate E2E compliance
 */
function validateE2ECompliance(
    workspaceRoot: string,
    stage05Path: string,
    testResults: E2ETestingReport | null,
    config: E2EValidationConfig
): E2EValidationResult {
    const errors: Array<{ code: string; message: string; path?: string; line?: number }> = [];
    const warnings: Array<{ code: string; message: string; path?: string }> = [];
    const checklist: Array<{ item: string; passed: boolean; details?: string }> = [];

    // Check 1: E2E Testing folder exists
    const e2eFolder = path.join(stage05Path, '03-E2E-Testing');
    const hasE2EFolder = fs.existsSync(e2eFolder);
    checklist.push({
        item: 'E2E Testing folder exists',
        passed: hasE2EFolder,
        details: hasE2EFolder ? e2eFolder : 'Missing docs/05-*/03-E2E-Testing/',
    });
    if (!hasE2EFolder) {
        errors.push({
            code: 'E2E-001',
            message: 'E2E Testing folder not found. Run "SDLC: Initialize E2E Testing" to create.',
            path: stage05Path,
        });
    }

    // Check 2: Test scripts exist
    const scriptsFolder = path.join(e2eFolder, 'scripts');
    const hasScripts = fs.existsSync(scriptsFolder) && fs.readdirSync(scriptsFolder).length > 0;
    checklist.push({
        item: 'Test scripts exist',
        passed: hasScripts,
        details: hasScripts ? 'Found in scripts/' : 'No test scripts found',
    });
    if (!hasScripts) {
        warnings.push({
            code: 'E2E-002',
            message: 'No test scripts found in scripts/ folder.',
            path: scriptsFolder,
        });
    }

    // Check 3: Test results exist
    const hasTestResults = testResults !== null;
    checklist.push({
        item: 'Test results available',
        passed: hasTestResults,
        details: hasTestResults ? `${testResults?.testedEndpoints} endpoints tested` : 'No test results found',
    });
    if (!hasTestResults) {
        warnings.push({
            code: 'E2E-003',
            message: 'No test results found. Run your E2E tests first.',
        });
    }

    // Check 4: Pass rate meets threshold
    const passRate = testResults?.passRate ?? 0;
    const meetsThreshold = passRate >= config.minPassRate;
    checklist.push({
        item: `Pass rate >= ${config.minPassRate}%`,
        passed: meetsThreshold,
        details: `Actual: ${passRate.toFixed(1)}%`,
    });
    if (!meetsThreshold && hasTestResults) {
        errors.push({
            code: 'E2E-004',
            message: `Pass rate ${passRate.toFixed(1)}% is below threshold ${config.minPassRate}%`,
        });
    }

    // Check 5: Reports folder exists
    const reportsFolder = path.join(e2eFolder, 'reports');
    const hasReports = fs.existsSync(reportsFolder);
    checklist.push({
        item: 'Reports folder exists',
        passed: hasReports,
        details: hasReports ? 'reports/ folder found' : 'Missing reports/ folder',
    });

    // Check 6: Stage 03 OpenAPI exists (cross-reference)
    const stage03Paths = [
        path.join(workspaceRoot, 'docs', '03-integrate', '01-api-contracts', 'openapi.json'),
        path.join(workspaceRoot, 'docs', '03-Integration-APIs', '02-API-Specifications', 'openapi.json'),
        path.join(workspaceRoot, 'openapi.json'),
    ];
    let openapiPath: string | undefined;
    for (const p of stage03Paths) {
        if (fs.existsSync(p)) {
            openapiPath = p;
            break;
        }
    }
    const hasOpenAPI = openapiPath !== undefined;
    checklist.push({
        item: 'Stage 03 OpenAPI spec exists',
        passed: hasOpenAPI,
        details: hasOpenAPI && openapiPath ? openapiPath : 'OpenAPI spec not found in Stage 03',
    });
    if (!hasOpenAPI) {
        warnings.push({
            code: 'E2E-005',
            message: 'OpenAPI spec not found in Stage 03. Cross-reference validation not possible.',
        });
    }

    // Calculate overall validity
    const isValid = errors.length === 0 && (!config.strict || warnings.length === 0);

    return {
        valid: isValid,
        passRate,
        totalEndpoints: testResults?.totalEndpoints ?? 0,
        testedEndpoints: testResults?.testedEndpoints ?? 0,
        passedEndpoints: testResults?.passedEndpoints ?? 0,
        failedEndpoints: testResults?.failedEndpoints ?? 0,
        errors,
        warnings,
        checklist,
        testResults,
        stage05Path,
        openapiPath: openapiPath ?? '',
        validationTimestamp: new Date().toISOString(),
    };
}

/**
 * Update VS Code diagnostics with E2E validation results
 */
function updateE2EDiagnostics(result: E2EValidationResult): void {
    // Clear previous diagnostics
    e2eDiagnosticCollection.clear();

    // We can't easily map E2E errors to specific files/lines
    // So we'll use the workspace root as a general location
    const workspaceRoot = getWorkspaceRoot();
    if (!workspaceRoot) {
        return;
    }

    // Create a pseudo-diagnostic for the Problems panel
    const diagnosticsMap = new Map<string, vscode.Diagnostic[]>();

    for (const error of result.errors) {
        const filePath = error.path || workspaceRoot;
        const range = new vscode.Range(0, 0, 0, 100);

        const diagnostic = new vscode.Diagnostic(
            range,
            `[${error.code}] ${error.message}`,
            vscode.DiagnosticSeverity.Error
        );
        diagnostic.source = 'SDLC E2E Validator';
        diagnostic.code = error.code;

        const existing = diagnosticsMap.get(filePath) || [];
        existing.push(diagnostic);
        diagnosticsMap.set(filePath, existing);
    }

    for (const warning of result.warnings) {
        const filePath = warning.path || workspaceRoot;
        const range = new vscode.Range(0, 0, 0, 100);

        const diagnostic = new vscode.Diagnostic(
            range,
            `[${warning.code}] ${warning.message}`,
            vscode.DiagnosticSeverity.Warning
        );
        diagnostic.source = 'SDLC E2E Validator';
        diagnostic.code = warning.code;

        const existing = diagnosticsMap.get(filePath) || [];
        existing.push(diagnostic);
        diagnosticsMap.set(filePath, existing);
    }

    for (const [filePath, diagnostics] of diagnosticsMap) {
        e2eDiagnosticCollection.set(vscode.Uri.file(filePath), diagnostics);
    }
}

/**
 * Show validation summary notification
 */
async function showValidationSummary(
    result: E2EValidationResult,
    _config: E2EValidationConfig
): Promise<void> {
    const errorCount = result.errors.length;
    const warningCount = result.warnings.length;

    if (result.valid) {
        void vscode.window.showInformationMessage(
            `✅ E2E Testing Compliance: PASSED (${result.passRate.toFixed(1)}% pass rate)`
        );
    } else if (errorCount > 0) {
        const action = await vscode.window.showErrorMessage(
            `❌ E2E Testing Compliance: FAILED (${errorCount} error(s), ${warningCount} warning(s))`,
            'Show Details',
            'Initialize E2E',
            'Dismiss'
        );
        if (action === 'Show Details') {
            showE2EResultsPanel(result);
        } else if (action === 'Initialize E2E') {
            await executeE2EInit();
        }
    } else {
        const action = await vscode.window.showWarningMessage(
            `⚠️ E2E Testing Compliance: ${warningCount} warning(s)`,
            'Show Details',
            'Dismiss'
        );
        if (action === 'Show Details') {
            showE2EResultsPanel(result);
        }
    }
}

/**
 * Show E2E validation results in output channel
 */
function showE2EResultsPanel(result: E2EValidationResult): void {
    const outputChannel = vscode.window.createOutputChannel('SDLC E2E Validation');
    outputChannel.clear();

    outputChannel.appendLine('═'.repeat(70));
    outputChannel.appendLine('  SDLC 6.0.2 E2E API TESTING VALIDATION REPORT');
    outputChannel.appendLine('═'.repeat(70));
    outputChannel.appendLine('');

    // Summary
    const statusIcon = result.valid ? '✅' : '❌';
    outputChannel.appendLine(`Status:      ${statusIcon} ${result.valid ? 'PASSED' : 'FAILED'}`);
    outputChannel.appendLine(`Pass Rate:   ${result.passRate.toFixed(1)}%`);
    outputChannel.appendLine(`Endpoints:   ${result.testedEndpoints}/${result.totalEndpoints} tested`);
    outputChannel.appendLine(`Passed:      ${result.passedEndpoints}`);
    outputChannel.appendLine(`Failed:      ${result.failedEndpoints}`);
    outputChannel.appendLine(`Errors:      ${result.errors.length}`);
    outputChannel.appendLine(`Warnings:    ${result.warnings.length}`);
    outputChannel.appendLine(`Validated:   ${result.validationTimestamp}`);
    outputChannel.appendLine('');

    // Checklist
    outputChannel.appendLine('─'.repeat(70));
    outputChannel.appendLine('COMPLIANCE CHECKLIST');
    outputChannel.appendLine('─'.repeat(70));
    for (const item of result.checklist) {
        const icon = item.passed ? '✅' : '❌';
        outputChannel.appendLine(`  ${icon} ${item.item}`);
        if (item.details) {
            outputChannel.appendLine(`     └─ ${item.details}`);
        }
    }
    outputChannel.appendLine('');

    // Errors
    if (result.errors.length > 0) {
        outputChannel.appendLine('─'.repeat(70));
        outputChannel.appendLine('ERRORS');
        outputChannel.appendLine('─'.repeat(70));
        for (const error of result.errors) {
            outputChannel.appendLine(`  ❌ [${error.code}] ${error.message}`);
            if (error.path) {
                outputChannel.appendLine(`     Path: ${error.path}`);
            }
        }
        outputChannel.appendLine('');
    }

    // Warnings
    if (result.warnings.length > 0) {
        outputChannel.appendLine('─'.repeat(70));
        outputChannel.appendLine('WARNINGS');
        outputChannel.appendLine('─'.repeat(70));
        for (const warning of result.warnings) {
            outputChannel.appendLine(`  ⚠️ [${warning.code}] ${warning.message}`);
            if (warning.path) {
                outputChannel.appendLine(`     Path: ${warning.path}`);
            }
        }
        outputChannel.appendLine('');
    }

    // Test Results
    if (result.testResults && result.testResults.coverage.length > 0) {
        outputChannel.appendLine('─'.repeat(70));
        outputChannel.appendLine('ENDPOINT TEST RESULTS');
        outputChannel.appendLine('─'.repeat(70));
        for (const endpoint of result.testResults.coverage.slice(0, 20)) {
            const icon = endpoint.passed ? '✅' : '❌';
            outputChannel.appendLine(`  ${icon} ${endpoint.method} ${endpoint.path} (${endpoint.statusCode})`);
        }
        if (result.testResults.coverage.length > 20) {
            outputChannel.appendLine(`  ... and ${result.testResults.coverage.length - 20} more endpoints`);
        }
        outputChannel.appendLine('');
    }

    outputChannel.appendLine('═'.repeat(70));
    outputChannel.appendLine('  END OF E2E VALIDATION REPORT');
    outputChannel.appendLine('═'.repeat(70));

    outputChannel.show();
}
