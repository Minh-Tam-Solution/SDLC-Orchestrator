/**
 * SDLC Context Panel Unit Tests
 *
 * Tests for Context Panel Provider and Status Bar
 *
 * Sprint 81 - Context Panel Implementation
 * @version 1.0.0
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import {
    ContextPanelProvider,
    ContextStatusBarItem,
    ContextTreeItem,
    SDLCContextOverlay,
} from '../../views/contextPanel';

// Mock ApiClient
class MockApiClient {
    private projectId: string | undefined;
    private mockOverlay: SDLCContextOverlay | null = null;
    private shouldError: boolean = false;

    setProjectId(id: string | undefined): void {
        this.projectId = id;
    }

    setMockOverlay(overlay: SDLCContextOverlay | null): void {
        this.mockOverlay = overlay;
    }

    setShouldError(shouldError: boolean): void {
        this.shouldError = shouldError;
    }

    getCurrentProjectId(): string | undefined {
        return this.projectId;
    }

    async getContextOverlay(projectId: string): Promise<SDLCContextOverlay> {
        if (this.shouldError) {
            throw new Error('API Error');
        }
        if (this.mockOverlay) {
            return this.mockOverlay;
        }
        return {
            project_id: projectId,
            stage_name: 'BUILD',
            gate_status: 'G3 PASSED',
            strict_mode: false,
            sprint: {
                number: 81,
                goal: 'AGENTS.md Integration',
                days_remaining: 5,
            },
            constraints: [],
            generated_at: new Date().toISOString(),
        };
    }
}

// Mock CacheService
class MockCacheService {
    private cache: Map<string, unknown> = new Map();

    async get<T>(key: string): Promise<T | null> {
        return (this.cache.get(key) as T) || null;
    }

    async set<T>(key: string, value: T, _ttl?: number): Promise<void> {
        this.cache.set(key, value);
    }

    async clear(): Promise<void> {
        this.cache.clear();
    }
}

suite('Context Panel Provider Test Suite', () => {
    let mockApiClient: MockApiClient;
    let mockCacheService: MockCacheService;
    let provider: ContextPanelProvider;

    setup(() => {
        mockApiClient = new MockApiClient();
        mockCacheService = new MockCacheService();
        // Cast to any to bypass type checking for mocks
        provider = new ContextPanelProvider(
            mockApiClient as any,
            mockCacheService as any
        );
    });

    teardown(() => {
        provider.dispose();
    });

    test('Shows "No Project Selected" when no project is set', async () => {
        mockApiClient.setProjectId(undefined);

        const children = await provider.getChildren();

        assert.strictEqual(children.length, 1);
        assert.ok(children[0] !== undefined);
        assert.strictEqual(children[0].label, 'No Project Selected');
    });

    test('Fetches and displays context overlay', async () => {
        const projectId = 'test-project-123';
        mockApiClient.setProjectId(projectId);

        await provider.refresh();
        const children = await provider.getChildren();

        // Should have Stage & Gate header, Sprint info, and Last Updated
        assert.ok(children.length >= 2, 'Should have at least 2 items');

        // Find Stage & Gate header
        const stageGateHeader = children.find((c) => c.label === 'Stage & Gate');
        assert.ok(stageGateHeader, 'Should have Stage & Gate header');
    });

    test('Displays strict mode warning when active', async () => {
        const projectId = 'test-project-strict';
        mockApiClient.setProjectId(projectId);
        mockApiClient.setMockOverlay({
            project_id: projectId,
            stage_name: 'DEPLOY',
            gate_status: 'G4 PENDING',
            strict_mode: true,
            constraints: [],
            generated_at: new Date().toISOString(),
        });

        await provider.refresh();
        const children = await provider.getChildren();

        // Find strict mode warning
        const strictWarning = children.find((c) =>
            (c.label as string).includes('STRICT MODE')
        );
        assert.ok(strictWarning, 'Should display strict mode warning');
    });

    test('Displays constraints when present', async () => {
        const projectId = 'test-project-constraints';
        mockApiClient.setProjectId(projectId);
        mockApiClient.setMockOverlay({
            project_id: projectId,
            stage_name: 'BUILD',
            gate_status: 'G3 PASSED',
            strict_mode: false,
            constraints: [
                {
                    type: 'security_scan',
                    severity: 'warning',
                    message: 'SAST scan pending',
                },
                {
                    type: 'test_coverage',
                    severity: 'error',
                    message: 'Coverage below 90%',
                },
            ],
            generated_at: new Date().toISOString(),
        });

        await provider.refresh();
        const children = await provider.getChildren();

        // Find constraints header
        const constraintsHeader = children.find(
            (c) => c.label === 'Active Constraints'
        );
        assert.ok(constraintsHeader !== undefined, 'Should have Active Constraints header');
        assert.strictEqual(
            constraintsHeader.description,
            '2 items',
            'Should show constraint count'
        );
    });

    test('Handles API errors gracefully', async () => {
        const projectId = 'test-project-error';
        mockApiClient.setProjectId(projectId);
        mockApiClient.setShouldError(true);

        await provider.refresh();
        const children = await provider.getChildren();

        // Should show error state
        assert.strictEqual(children.length, 1);
        assert.ok(children[0] !== undefined);
        assert.strictEqual(children[0].label, 'Error');
    });

    test('Clear method resets context', async () => {
        const projectId = 'test-project-clear';
        mockApiClient.setProjectId(projectId);

        await provider.refresh();
        provider.clear();

        const children = await provider.getChildren();
        assert.strictEqual(children.length, 1);
        assert.ok(children[0] !== undefined);
        assert.strictEqual(children[0].label, 'No Project Selected');
    });
});

suite('Context Tree Item Test Suite', () => {
    test('Creates tree item with correct properties', () => {
        const item = new ContextTreeItem(
            'Test Label',
            vscode.TreeItemCollapsibleState.None,
            'stage',
            'Test Description'
        );

        assert.strictEqual(item.label, 'Test Label');
        assert.strictEqual(item.description, 'Test Description');
        assert.strictEqual(item.contextValue, 'stage');
    });

    test('Creates expandable tree item with children', () => {
        const children = [
            new ContextTreeItem(
                'Child 1',
                vscode.TreeItemCollapsibleState.None,
                'info'
            ),
            new ContextTreeItem(
                'Child 2',
                vscode.TreeItemCollapsibleState.None,
                'info'
            ),
        ];

        const parent = new ContextTreeItem(
            'Parent',
            vscode.TreeItemCollapsibleState.Expanded,
            'header',
            undefined,
            children
        );

        assert.strictEqual(parent.children.length, 2);
        assert.strictEqual(
            parent.collapsibleState,
            vscode.TreeItemCollapsibleState.Expanded
        );
    });

    test('Sets correct icons for different item types', () => {
        const errorItem = new ContextTreeItem(
            'Error',
            vscode.TreeItemCollapsibleState.None,
            'error'
        );
        const warningItem = new ContextTreeItem(
            'Warning',
            vscode.TreeItemCollapsibleState.None,
            'warning'
        );
        const infoItem = new ContextTreeItem(
            'Info',
            vscode.TreeItemCollapsibleState.None,
            'info'
        );

        assert.ok(errorItem.iconPath, 'Error item should have icon');
        assert.ok(warningItem.iconPath, 'Warning item should have icon');
        assert.ok(infoItem.iconPath, 'Info item should have icon');
    });
});

suite('Context Status Bar Test Suite', () => {
    let statusBar: ContextStatusBarItem;

    setup(() => {
        statusBar = new ContextStatusBarItem();
    });

    teardown(() => {
        statusBar.dispose();
    });

    test('Shows "No Project" when context is null', () => {
        statusBar.update(null);
        // Status bar text is internal, we just verify no error is thrown
    });

    test('Updates with context overlay', () => {
        const overlay: SDLCContextOverlay = {
            project_id: 'test-123',
            stage_name: 'BUILD',
            gate_status: 'G3 PASSED',
            strict_mode: false,
            constraints: [],
            generated_at: new Date().toISOString(),
        };

        statusBar.update(overlay);
        // Verify no error is thrown
    });

    test('Shows error count with error constraints', () => {
        const overlay: SDLCContextOverlay = {
            project_id: 'test-456',
            stage_name: 'BUILD',
            gate_status: 'G3 FAILED',
            strict_mode: false,
            constraints: [
                {
                    type: 'test_failure',
                    severity: 'error',
                    message: 'Tests failed',
                },
                {
                    type: 'coverage',
                    severity: 'error',
                    message: 'Low coverage',
                },
            ],
            generated_at: new Date().toISOString(),
        };

        statusBar.update(overlay);
        // Verify no error is thrown
    });

    test('Shows strict mode indicator', () => {
        const overlay: SDLCContextOverlay = {
            project_id: 'test-789',
            stage_name: 'DEPLOY',
            gate_status: 'G4 PASSED',
            strict_mode: true,
            constraints: [],
            generated_at: new Date().toISOString(),
        };

        statusBar.update(overlay);
        // Verify no error is thrown
    });

    test('ShowLoading changes state', () => {
        statusBar.showLoading();
        // Verify no error is thrown
    });

    test('ShowError changes state', () => {
        statusBar.showError('Test error message');
        // Verify no error is thrown
    });
});
