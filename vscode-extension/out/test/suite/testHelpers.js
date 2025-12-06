"use strict";
/**
 * Test Helper Utilities
 *
 * Provides common mock objects and helper functions for testing.
 *
 * Sprint 27 Day 5 - Test Fixes
 * @version 0.1.0
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
exports.simpleMockContext = exports.MockSecretStorage = exports.MockGlobalState = void 0;
exports.createMockExtensionContext = createMockExtensionContext;
const vscode = __importStar(require("vscode"));
/**
 * Mock GlobalState implementation
 */
class MockGlobalState {
    storage = new Map();
    get(key, defaultValue) {
        const value = this.storage.get(key);
        return value !== undefined ? value : defaultValue;
    }
    update(key, value) {
        if (value === undefined) {
            this.storage.delete(key);
        }
        else {
            this.storage.set(key, value);
        }
        return Promise.resolve();
    }
    keys() {
        return Array.from(this.storage.keys());
    }
    setKeysForSync(_keys) {
        // No-op for testing
    }
    // Helper for testing
    clear() {
        this.storage.clear();
    }
}
exports.MockGlobalState = MockGlobalState;
/**
 * Mock SecretStorage implementation
 */
class MockSecretStorage {
    secrets = new Map();
    _onDidChange = new vscode.EventEmitter();
    onDidChange = this._onDidChange.event;
    get(key) {
        return Promise.resolve(this.secrets.get(key));
    }
    store(key, value) {
        this.secrets.set(key, value);
        this._onDidChange.fire({ key });
        return Promise.resolve();
    }
    delete(key) {
        this.secrets.delete(key);
        this._onDidChange.fire({ key });
        return Promise.resolve();
    }
    keys() {
        return Promise.resolve(Array.from(this.secrets.keys()));
    }
    // Helper for testing
    clear() {
        this.secrets.clear();
    }
}
exports.MockSecretStorage = MockSecretStorage;
/**
 * Creates a complete mock VS Code extension context
 */
function createMockExtensionContext(options) {
    const globalState = options?.globalState ?? new MockGlobalState();
    const secrets = options?.secrets ?? new MockSecretStorage();
    return {
        subscriptions: [],
        globalState,
        workspaceState: new MockGlobalState(),
        secrets,
        extensionUri: vscode.Uri.parse('file:///test'),
        extensionPath: '/test',
        environmentVariableCollection: {},
        storagePath: '/test/storage',
        globalStoragePath: '/test/global-storage',
        logPath: '/test/logs',
        extensionMode: vscode.ExtensionMode.Test,
        storageUri: vscode.Uri.parse('file:///test/storage'),
        globalStorageUri: vscode.Uri.parse('file:///test/global-storage'),
        logUri: vscode.Uri.parse('file:///test/logs'),
        extension: {},
        languageModelAccessInformation: {},
        asAbsolutePath: (relativePath) => `/test/${relativePath}`,
    };
}
/**
 * Simple mock context for basic tests (inline object)
 */
exports.simpleMockContext = {
    subscriptions: [],
    globalState: {
        get: () => undefined,
        update: () => Promise.resolve(),
        keys: () => [],
        setKeysForSync: () => undefined,
    },
    workspaceState: {
        get: () => undefined,
        update: () => Promise.resolve(),
        keys: () => [],
        setKeysForSync: () => undefined,
    },
    secrets: {
        get: () => Promise.resolve(undefined),
        store: () => Promise.resolve(),
        delete: () => Promise.resolve(),
        keys: () => Promise.resolve([]),
        onDidChange: new vscode.EventEmitter().event,
    },
    extensionUri: vscode.Uri.parse('file:///test'),
    extensionPath: '/test',
    environmentVariableCollection: {},
    storagePath: '/test/storage',
    globalStoragePath: '/test/global-storage',
    logPath: '/test/logs',
    extensionMode: vscode.ExtensionMode.Test,
    storageUri: vscode.Uri.parse('file:///test/storage'),
    globalStorageUri: vscode.Uri.parse('file:///test/global-storage'),
    logUri: vscode.Uri.parse('file:///test/logs'),
    extension: {},
    languageModelAccessInformation: {},
    asAbsolutePath: (relativePath) => `/test/${relativePath}`,
};
//# sourceMappingURL=testHelpers.js.map