/**
 * VS Code Extension Test Runner
 *
 * Launches VS Code with extension tests.
 * Sprint 27 Day 2 - Testing Infrastructure
 * @version 0.1.0
 */

import * as path from 'path';
import { runTests } from '@vscode/test-electron';

async function main(): Promise<void> {
    try {
        // The folder containing the Extension Manifest package.json
        const extensionDevelopmentPath = path.resolve(__dirname, '../../');

        // The path to test runner
        const extensionTestsPath = path.resolve(__dirname, './suite/index');

        // Run VS Code tests with specific version for compatibility
        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            version: '1.85.0',
            launchArgs: [
                '--disable-extensions',
                '--disable-gpu',
            ],
        });
    } catch (err) {
        console.error('Failed to run tests:', err);
        process.exit(1);
    }
}

void main();
