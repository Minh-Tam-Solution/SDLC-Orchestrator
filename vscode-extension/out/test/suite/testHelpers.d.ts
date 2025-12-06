/**
 * Test Helper Utilities
 *
 * Provides common mock objects and helper functions for testing.
 *
 * Sprint 27 Day 5 - Test Fixes
 * @version 0.1.0
 */
import * as vscode from 'vscode';
/**
 * Mock GlobalState implementation
 */
export declare class MockGlobalState implements vscode.Memento {
    private storage;
    get<T>(key: string): T | undefined;
    get<T>(key: string, defaultValue: T): T;
    update(key: string, value: unknown): Promise<void>;
    keys(): readonly string[];
    setKeysForSync(_keys: readonly string[]): void;
    clear(): void;
}
/**
 * Mock SecretStorage implementation
 */
export declare class MockSecretStorage implements vscode.SecretStorage {
    private secrets;
    private _onDidChange;
    onDidChange: vscode.Event<vscode.SecretStorageChangeEvent>;
    get(key: string): Promise<string | undefined>;
    store(key: string, value: string): Promise<void>;
    delete(key: string): Promise<void>;
    keys(): Thenable<string[]>;
    clear(): void;
}
/**
 * Creates a complete mock VS Code extension context
 */
export declare function createMockExtensionContext(options?: {
    globalState?: MockGlobalState;
    secrets?: MockSecretStorage;
}): vscode.ExtensionContext;
/**
 * Simple mock context for basic tests (inline object)
 */
export declare const simpleMockContext: vscode.ExtensionContext;
//# sourceMappingURL=testHelpers.d.ts.map