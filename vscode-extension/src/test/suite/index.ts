/**
 * Test Suite Entry Point
 *
 * Discovers and runs all test files in the suite.
 * Sprint 27 Day 2 - Testing Infrastructure
 * @version 0.1.0
 */

import * as path from 'path';
import Mocha from 'mocha';
import { glob } from 'glob';

export async function run(): Promise<void> {
    // Create the mocha test runner
    const mocha = new Mocha({
        ui: 'tdd',
        color: true,
        timeout: 10000, // 10 second timeout for async tests
        reporter: 'spec',
    });

    const testsRoot = path.resolve(__dirname, '.');

    try {
        // Find all test files
        const files = await glob('**/*.test.js', { cwd: testsRoot });

        // Add files to the test suite
        for (const file of files) {
            mocha.addFile(path.resolve(testsRoot, file));
        }

        // Run the mocha tests
        return new Promise((resolve, reject) => {
            mocha.run((failures: number) => {
                if (failures > 0) {
                    reject(new Error(`${failures} tests failed.`));
                } else {
                    resolve();
                }
            });
        });
    } catch (err) {
        console.error('Error running tests:', err);
        throw err;
    }
}
