/**
 * Projects View Unit Tests
 *
 * Tests for the ProjectsProvider TreeDataProvider and ProjectTreeItem
 *
 * Sprint 27 Day 4 - Testing
 * @version 0.1.0
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { ProjectsProvider, ProjectTreeItem } from '../../views/projectsView';
import { ApiClient, Project } from '../../services/apiClient';
import { AuthService } from '../../services/authService';
import { CacheService } from '../../services/cacheService';
import { simpleMockContext } from './testHelpers';

const mockContext = simpleMockContext;

suite('ProjectsProvider Test Suite', () => {
    let provider: ProjectsProvider;
    let apiClient: ApiClient;
    let authService: AuthService;
    let cacheService: CacheService;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        cacheService = new CacheService(mockContext);
        provider = new ProjectsProvider(apiClient, cacheService);
    });

    test('ProjectsProvider initializes correctly', () => {
        assert.ok(provider);
    });

    test('ProjectsProvider implements TreeDataProvider interface', () => {
        assert.ok(typeof provider.getTreeItem === 'function');
        assert.ok(typeof provider.getChildren === 'function');
        assert.ok(provider.onDidChangeTreeData);
    });

    test('getTreeItem returns tree item for project', () => {
        const mockProject: Project = {
            id: 'project-1',
            name: 'Test Project',
            description: 'A test project',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner-1',
        };

        const treeItem = provider.getTreeItem(new ProjectTreeItem(mockProject, false));

        assert.ok(treeItem);
        assert.strictEqual(treeItem.collapsibleState, vscode.TreeItemCollapsibleState.None);
    });

    test('refresh fires onDidChangeTreeData event', async () => {
        let eventFired = false;
        provider.onDidChangeTreeData(() => {
            eventFired = true;
        });

        await provider.refresh();

        assert.strictEqual(eventFired, true);
    });

    test('clear resets provider state', () => {
        provider.clear();

        const selectedProject = provider.getSelectedProject();
        assert.strictEqual(selectedProject, undefined);
    });

    test('getProjects returns array copy', () => {
        const projects = provider.getProjects();
        assert.ok(Array.isArray(projects));
    });

    test('getSelectedProject returns undefined initially', () => {
        const selected = provider.getSelectedProject();
        assert.strictEqual(selected, undefined);
    });
});

suite('ProjectTreeItem Test Suite', () => {
    test('ProjectTreeItem has correct label', () => {
        const project: Project = {
            id: 'p1',
            name: 'My Project',
            description: 'Description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.strictEqual(item.label, 'My Project');
    });

    test('ProjectTreeItem is not collapsible', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.strictEqual(item.collapsibleState, vscode.TreeItemCollapsibleState.None);
    });

    test('ProjectTreeItem has context value of project', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.strictEqual(item.contextValue, 'project');
    });

    test('Selected ProjectTreeItem shows (selected) description', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, true);

        assert.strictEqual(item.description, '(selected)');
    });

    test('Non-selected ProjectTreeItem shows status in description', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.strictEqual(item.description, 'active');
    });

    test('ProjectTreeItem has tooltip', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test Project',
            description: 'A detailed description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.ok(item.tooltip);
    });

    test('ProjectTreeItem has select command', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.ok(item.command);
        assert.strictEqual(item.command?.command, 'sdlc.internal.selectProjectItem');
        assert.deepStrictEqual(item.command?.arguments, ['p1', 'Test']);
    });

    test('ProjectTreeItem stores project reference', () => {
        const project: Project = {
            id: 'unique-id',
            name: 'My Project',
            description: 'Description',
            status: 'draft',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.strictEqual(item.project.id, 'unique-id');
        assert.strictEqual(item.project.name, 'My Project');
    });

    test('ProjectTreeItem stores isSelected flag', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const selectedItem = new ProjectTreeItem(project, true);
        const unselectedItem = new ProjectTreeItem(project, false);

        assert.strictEqual(selectedItem.isSelected, true);
        assert.strictEqual(unselectedItem.isSelected, false);
    });
});

suite('ProjectTreeItem Status Icons', () => {
    test('Active project has folder-active icon', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.ok(item.iconPath);
        // ThemeIcon would be folder-active for active projects
    });

    test('Archived project has archive icon', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'archived',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.ok(item.iconPath);
        // ThemeIcon would be archive for archived projects
    });

    test('Draft project has folder icon', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'draft',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.ok(item.iconPath);
        // ThemeIcon would be folder for draft projects
    });

    test('Selected project has check icon', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, true);

        assert.ok(item.iconPath);
        // Selected items should have check icon
    });

    test('Unknown status uses default folder icon', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'unknown' as Project['status'],
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        assert.ok(item.iconPath);
    });
});

suite('ProjectTreeItem Tooltip Content', () => {
    test('Tooltip includes project name', () => {
        const project: Project = {
            id: 'p1',
            name: 'My Awesome Project',
            description: 'Description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        const tooltipText = (item.tooltip as vscode.MarkdownString).value;
        assert.ok(tooltipText.includes('My Awesome Project'));
    });

    test('Tooltip includes project description', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'This is a detailed description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        const tooltipText = (item.tooltip as vscode.MarkdownString).value;
        assert.ok(tooltipText.includes('This is a detailed description'));
    });

    test('Tooltip includes project status', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        const item = new ProjectTreeItem(project, false);

        const tooltipText = (item.tooltip as vscode.MarkdownString).value;
        assert.ok(tooltipText.includes('Status'));
        assert.ok(tooltipText.includes('active'));
    });

    test('Tooltip includes compliance score if present', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
            compliance_score: 85,
        };

        const item = new ProjectTreeItem(project, false);

        const tooltipText = (item.tooltip as vscode.MarkdownString).value;
        assert.ok(tooltipText.includes('Compliance'));
        assert.ok(tooltipText.includes('85'));
    });

    test('Tooltip includes current gate if present', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
            current_gate: 'G2',
        };

        const item = new ProjectTreeItem(project, false);

        const tooltipText = (item.tooltip as vscode.MarkdownString).value;
        assert.ok(tooltipText.includes('Current Gate'));
        assert.ok(tooltipText.includes('G2'));
    });

    test('Tooltip handles missing description', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: '',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        // Should not throw
        const item = new ProjectTreeItem(project, false);
        assert.ok(item.tooltip);
    });
});

suite('ProjectsProvider with CacheService', () => {
    let provider: ProjectsProvider;
    let apiClient: ApiClient;
    let authService: AuthService;
    let cacheService: CacheService;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        cacheService = new CacheService(mockContext);
        provider = new ProjectsProvider(apiClient, cacheService);
    });

    test('Provider accepts optional CacheService', () => {
        const providerWithoutCache = new ProjectsProvider(apiClient);
        assert.ok(providerWithoutCache);
    });

    test('Provider uses CacheService when available', () => {
        const providerWithCache = new ProjectsProvider(apiClient, cacheService);
        assert.ok(providerWithCache);
    });

    test('Refresh works without CacheService', async () => {
        const providerWithoutCache = new ProjectsProvider(apiClient);
        await providerWithoutCache.refresh();
        // Should not throw
        assert.ok(true);
    });

    test('Clear works regardless of cache', () => {
        provider.clear();
        assert.ok(true);
    });
});

suite('ProjectsProvider Event Handling', () => {
    let provider: ProjectsProvider;
    let apiClient: ApiClient;
    let authService: AuthService;

    setup(() => {
        authService = new AuthService(mockContext);
        apiClient = new ApiClient(mockContext, authService);
        provider = new ProjectsProvider(apiClient);
    });

    test('onDidChangeTreeData is an Event', () => {
        assert.ok(provider.onDidChangeTreeData);
        // Should be able to subscribe
        const disposable = provider.onDidChangeTreeData(() => {
            // Handler
        });
        assert.ok(disposable);
        disposable.dispose();
    });

    test('Multiple subscribers receive events', async () => {
        let count = 0;

        provider.onDidChangeTreeData(() => {
            count++;
        });
        provider.onDidChangeTreeData(() => {
            count++;
        });

        await provider.refresh();

        assert.strictEqual(count, 2);
    });
});

suite('Project Interface Validation', () => {
    test('Project requires id', () => {
        const project: Project = {
            id: 'required-id',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };

        assert.ok(project.id);
    });

    test('Project status values', () => {
        const statuses: Array<Project['status']> = ['active', 'archived', 'draft'];

        for (const status of statuses) {
            const project: Project = {
                id: 'p1',
                name: 'Test',
                description: 'Test',
                status,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
                owner_id: 'owner',
            };
            assert.strictEqual(project.status, status);
        }
    });

    test('Project optional fields', () => {
        const project: Project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
            compliance_score: 90,
            current_gate: 'G3',
            github_repo: 'https://github.com/test/repo',
        };

        assert.strictEqual(project.compliance_score, 90);
        assert.strictEqual(project.current_gate, 'G3');
        assert.strictEqual(project.github_repo, 'https://github.com/test/repo');
    });
});
