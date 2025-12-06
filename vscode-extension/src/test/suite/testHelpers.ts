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
export class MockGlobalState implements vscode.Memento {
    private storage: Map<string, unknown> = new Map();

    get<T>(key: string): T | undefined;
    get<T>(key: string, defaultValue: T): T;
    get<T>(key: string, defaultValue?: T): T | undefined {
        const value = this.storage.get(key);
        return value !== undefined ? (value as T) : defaultValue;
    }

    update(key: string, value: unknown): Promise<void> {
        if (value === undefined) {
            this.storage.delete(key);
        } else {
            this.storage.set(key, value);
        }
        return Promise.resolve();
    }

    keys(): readonly string[] {
        return Array.from(this.storage.keys());
    }

    setKeysForSync(_keys: readonly string[]): void {
        // No-op for testing
    }

    // Helper for testing
    clear(): void {
        this.storage.clear();
    }
}

/**
 * Mock SecretStorage implementation
 */
export class MockSecretStorage implements vscode.SecretStorage {
    private secrets: Map<string, string> = new Map();
    private _onDidChange = new vscode.EventEmitter<vscode.SecretStorageChangeEvent>();

    onDidChange = this._onDidChange.event;

    get(key: string): Promise<string | undefined> {
        return Promise.resolve(this.secrets.get(key));
    }

    store(key: string, value: string): Promise<void> {
        this.secrets.set(key, value);
        this._onDidChange.fire({ key });
        return Promise.resolve();
    }

    delete(key: string): Promise<void> {
        this.secrets.delete(key);
        this._onDidChange.fire({ key });
        return Promise.resolve();
    }

    keys(): Thenable<string[]> {
        return Promise.resolve(Array.from(this.secrets.keys()));
    }

    // Helper for testing
    clear(): void {
        this.secrets.clear();
    }
}

/**
 * Creates a complete mock VS Code extension context
 */
export function createMockExtensionContext(
    options?: {
        globalState?: MockGlobalState;
        secrets?: MockSecretStorage;
    }
): vscode.ExtensionContext {
    const globalState = options?.globalState ?? new MockGlobalState();
    const secrets = options?.secrets ?? new MockSecretStorage();

    return {
        subscriptions: [],
        globalState,
        workspaceState: new MockGlobalState(),
        secrets,
        extensionUri: vscode.Uri.parse('file:///test'),
        extensionPath: '/test',
        environmentVariableCollection: {} as vscode.GlobalEnvironmentVariableCollection,
        storagePath: '/test/storage',
        globalStoragePath: '/test/global-storage',
        logPath: '/test/logs',
        extensionMode: vscode.ExtensionMode.Test,
        storageUri: vscode.Uri.parse('file:///test/storage'),
        globalStorageUri: vscode.Uri.parse('file:///test/global-storage'),
        logUri: vscode.Uri.parse('file:///test/logs'),
        extension: {} as vscode.Extension<unknown>,
        languageModelAccessInformation: {} as vscode.LanguageModelAccessInformation,
        asAbsolutePath: (relativePath: string) => `/test/${relativePath}`,
    } as vscode.ExtensionContext;
}

/**
 * Simple mock context for basic tests (inline object)
 */
export const simpleMockContext = {
    subscriptions: [],
    globalState: {
        get: () => undefined,
        update: (): Promise<void> => Promise.resolve(),
        keys: () => [],
        setKeysForSync: () => undefined,
    },
    workspaceState: {
        get: () => undefined,
        update: (): Promise<void> => Promise.resolve(),
        keys: () => [],
        setKeysForSync: () => undefined,
    },
    secrets: {
        get: (): Promise<string | undefined> => Promise.resolve(undefined),
        store: (): Promise<void> => Promise.resolve(),
        delete: (): Promise<void> => Promise.resolve(),
        keys: (): Promise<string[]> => Promise.resolve([]),
        onDidChange: new vscode.EventEmitter<vscode.SecretStorageChangeEvent>().event,
    },
    extensionUri: vscode.Uri.parse('file:///test'),
    extensionPath: '/test',
    environmentVariableCollection: {} as vscode.GlobalEnvironmentVariableCollection,
    storagePath: '/test/storage',
    globalStoragePath: '/test/global-storage',
    logPath: '/test/logs',
    extensionMode: vscode.ExtensionMode.Test,
    storageUri: vscode.Uri.parse('file:///test/storage'),
    globalStorageUri: vscode.Uri.parse('file:///test/global-storage'),
    logUri: vscode.Uri.parse('file:///test/logs'),
    extension: {} as vscode.Extension<unknown>,
    languageModelAccessInformation: {} as vscode.LanguageModelAccessInformation,
    asAbsolutePath: (relativePath: string) => `/test/${relativePath}`,
} as vscode.ExtensionContext;
