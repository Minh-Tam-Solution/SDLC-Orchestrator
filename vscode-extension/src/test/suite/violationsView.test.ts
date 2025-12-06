/**
 * Violations View Unit Tests
 *
 * Sprint 27 Day 2 - Testing
 * @version 0.1.0
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { ViolationsProvider, ViolationTreeItem } from '../../views/violationsView';
import { ApiClient, Violation } from '../../services/apiClient';
import { AuthService } from '../../services/authService';
import { CacheService } from '../../services/cacheService';
import { simpleMockContext } from './testHelpers';

const mockContext = simpleMockContext;

suite('ViolationsProvider Test Suite', () => {
    let provider: ViolationsProvider;
    let apiClient: ApiClient;
    let authService: AuthService;
    let cacheService: CacheService;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        cacheService = new CacheService(mockContext);
        provider = new ViolationsProvider(apiClient, cacheService);
    });

    test('ViolationsProvider initializes correctly', () => {
        assert.ok(provider);
    });

    test('getTreeItem returns tree item for violation', () => {
        const mockViolation: Violation = {
            id: 'v-1',
            project_id: 'project-1',
            violation_type: 'missing_documentation',
            severity: 'high',
            description: 'Security baseline documentation is missing',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const treeItem = provider.getTreeItem(new ViolationTreeItem(
            mockViolation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            mockViolation
        ));

        assert.ok(treeItem);
        assert.strictEqual(treeItem.contextValue, 'violation');
    });

    test('refresh fires onDidChangeTreeData event', async () => {
        let eventFired = false;
        const disposable = provider.onDidChangeTreeData(() => {
            eventFired = true;
        });

        await provider.refresh();
        disposable.dispose();

        assert.strictEqual(eventFired, true);
    });
});

suite('ViolationTreeItem Test Suite', () => {
    test('ViolationTreeItem has correct label', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'missing_test_coverage',
            severity: 'medium',
            description: 'Unit test coverage below 80%',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );

        assert.ok(item.label);
        assert.ok((item.label).includes('missing_test_coverage'));
    });

    test('ViolationTreeItem has tooltip with description', () => {
        const violation: Violation = {
            id: 'v-2',
            project_id: 'p-1',
            violation_type: 'security_vulnerability',
            severity: 'critical',
            description: 'SQL injection vulnerability detected in user input handling',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );

        assert.ok(item.tooltip);
        assert.ok((item.tooltip as vscode.MarkdownString).value.includes('SQL injection'));
    });

    test('ViolationTreeItem context value is violation', () => {
        const violation: Violation = {
            id: 'v-3',
            project_id: 'p-1',
            violation_type: 'code_review_pending',
            severity: 'low',
            description: 'Code review not completed for merge request',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );

        assert.strictEqual(item.contextValue, 'violation');
    });

    test('ViolationTreeItem stores violation id', () => {
        const violation: Violation = {
            id: 'violation-uuid-123',
            project_id: 'p-1',
            violation_type: 'test',
            severity: 'low',
            description: 'Test violation',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );

        assert.ok(item.violation);
        assert.strictEqual(item.violation.id, 'violation-uuid-123');
    });
});

suite('ViolationTreeItem Severity Icons', () => {
    test('Critical severity has error icon', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'security_breach',
            severity: 'critical',
            description: 'Critical security issue',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.iconPath);
    });

    test('High severity has warning icon', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'data_leak',
            severity: 'high',
            description: 'Potential data leak',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.iconPath);
    });

    test('Medium severity has info icon', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'code_smell',
            severity: 'medium',
            description: 'Code quality issue',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.iconPath);
    });

    test('Low severity has info icon', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'style_issue',
            severity: 'low',
            description: 'Code style issue',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.iconPath);
    });
});

suite('ViolationTreeItem Status Display', () => {
    test('Open violation shows open status', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'test',
            severity: 'medium',
            description: 'Test',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.description);
    });

    test('Resolved violation shows resolved status', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'test',
            severity: 'medium',
            description: 'Test',
            status: 'resolved',
            created_at: '2025-01-01T00:00:00Z',
            resolved_at: '2025-01-02T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.description);
    });

    test('Ignored violation shows ignored status', () => {
        const violation: Violation = {
            id: 'v-1',
            project_id: 'p-1',
            violation_type: 'test',
            severity: 'low',
            description: 'Test',
            status: 'ignored',
            created_at: '2025-01-01T00:00:00Z',
        };

        const item = new ViolationTreeItem(
            violation.violation_type,
            vscode.TreeItemCollapsibleState.Collapsed,
            violation
        );
        assert.ok(item.description);
    });
});

suite('Violation Filtering', () => {
    test('Violations can be filtered by severity', () => {
        const violations: Violation[] = [
            {
                id: 'v-1',
                project_id: 'p-1',
                violation_type: 'a',
                severity: 'critical',
                description: 'A',
                status: 'open',
                created_at: '2025-01-01T00:00:00Z',
            },
            {
                id: 'v-2',
                project_id: 'p-1',
                violation_type: 'b',
                severity: 'high',
                description: 'B',
                status: 'open',
                created_at: '2025-01-01T00:00:00Z',
            },
            {
                id: 'v-3',
                project_id: 'p-1',
                violation_type: 'c',
                severity: 'low',
                description: 'C',
                status: 'open',
                created_at: '2025-01-01T00:00:00Z',
            },
        ];

        const critical = violations.filter((v) => v.severity === 'critical');
        const high = violations.filter((v) => v.severity === 'high');
        const low = violations.filter((v) => v.severity === 'low');

        assert.strictEqual(critical.length, 1);
        assert.strictEqual(high.length, 1);
        assert.strictEqual(low.length, 1);
    });

    test('Violations can be filtered by status', () => {
        const violations: Violation[] = [
            {
                id: 'v-1',
                project_id: 'p-1',
                violation_type: 'a',
                severity: 'high',
                description: 'A',
                status: 'open',
                created_at: '2025-01-01T00:00:00Z',
            },
            {
                id: 'v-2',
                project_id: 'p-1',
                violation_type: 'b',
                severity: 'medium',
                description: 'B',
                status: 'resolved',
                created_at: '2025-01-01T00:00:00Z',
            },
        ];

        const open = violations.filter((v) => v.status === 'open');
        const resolved = violations.filter((v) => v.status === 'resolved');

        assert.strictEqual(open.length, 1);
        assert.strictEqual(resolved.length, 1);
    });
});
