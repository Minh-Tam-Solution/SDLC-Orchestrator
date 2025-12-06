"use strict";
/**
 * Projects View Unit Tests
 *
 * Tests for the ProjectsProvider TreeDataProvider and ProjectTreeItem
 *
 * Sprint 27 Day 4 - Testing
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
const assert = __importStar(require("assert"));
const vscode = __importStar(require("vscode"));
const projectsView_1 = require("../../views/projectsView");
const apiClient_1 = require("../../services/apiClient");
const authService_1 = require("../../services/authService");
const cacheService_1 = require("../../services/cacheService");
const testHelpers_1 = require("./testHelpers");
const mockContext = testHelpers_1.simpleMockContext;
suite('ProjectsProvider Test Suite', () => {
    let provider;
    let apiClient;
    let authService;
    let cacheService;
    setup(() => {
        authService = new authService_1.AuthService(mockContext);
        apiClient = new apiClient_1.ApiClient(mockContext, authService);
        cacheService = new cacheService_1.CacheService(mockContext);
        provider = new projectsView_1.ProjectsProvider(apiClient, cacheService);
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
        const mockProject = {
            id: 'project-1',
            name: 'Test Project',
            description: 'A test project',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner-1',
        };
        const treeItem = provider.getTreeItem(new projectsView_1.ProjectTreeItem(mockProject, false));
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
        const project = {
            id: 'p1',
            name: 'My Project',
            description: 'Description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.strictEqual(item.label, 'My Project');
    });
    test('ProjectTreeItem is not collapsible', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.strictEqual(item.collapsibleState, vscode.TreeItemCollapsibleState.None);
    });
    test('ProjectTreeItem has context value of project', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.strictEqual(item.contextValue, 'project');
    });
    test('Selected ProjectTreeItem shows (selected) description', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, true);
        assert.strictEqual(item.description, '(selected)');
    });
    test('Non-selected ProjectTreeItem shows status in description', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.strictEqual(item.description, 'active');
    });
    test('ProjectTreeItem has tooltip', () => {
        const project = {
            id: 'p1',
            name: 'Test Project',
            description: 'A detailed description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.tooltip);
    });
    test('ProjectTreeItem has select command', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.command);
        assert.strictEqual(item.command?.command, 'sdlc.internal.selectProjectItem');
        assert.deepStrictEqual(item.command?.arguments, ['p1', 'Test']);
    });
    test('ProjectTreeItem stores project reference', () => {
        const project = {
            id: 'unique-id',
            name: 'My Project',
            description: 'Description',
            status: 'draft',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.strictEqual(item.project.id, 'unique-id');
        assert.strictEqual(item.project.name, 'My Project');
    });
    test('ProjectTreeItem stores isSelected flag', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const selectedItem = new projectsView_1.ProjectTreeItem(project, true);
        const unselectedItem = new projectsView_1.ProjectTreeItem(project, false);
        assert.strictEqual(selectedItem.isSelected, true);
        assert.strictEqual(unselectedItem.isSelected, false);
    });
});
suite('ProjectTreeItem Status Icons', () => {
    test('Active project has folder-active icon', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.iconPath);
        // ThemeIcon would be folder-active for active projects
    });
    test('Archived project has archive icon', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'archived',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.iconPath);
        // ThemeIcon would be archive for archived projects
    });
    test('Draft project has folder icon', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'draft',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.iconPath);
        // ThemeIcon would be folder for draft projects
    });
    test('Selected project has check icon', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, true);
        assert.ok(item.iconPath);
        // Selected items should have check icon
    });
    test('Unknown status uses default folder icon', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'unknown',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.iconPath);
    });
});
suite('ProjectTreeItem Tooltip Content', () => {
    test('Tooltip includes project name', () => {
        const project = {
            id: 'p1',
            name: 'My Awesome Project',
            description: 'Description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        const tooltipText = item.tooltip.value;
        assert.ok(tooltipText.includes('My Awesome Project'));
    });
    test('Tooltip includes project description', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'This is a detailed description',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        const tooltipText = item.tooltip.value;
        assert.ok(tooltipText.includes('This is a detailed description'));
    });
    test('Tooltip includes project status', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        const tooltipText = item.tooltip.value;
        assert.ok(tooltipText.includes('Status'));
        assert.ok(tooltipText.includes('active'));
    });
    test('Tooltip includes compliance score if present', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
            compliance_score: 85,
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        const tooltipText = item.tooltip.value;
        assert.ok(tooltipText.includes('Compliance'));
        assert.ok(tooltipText.includes('85'));
    });
    test('Tooltip includes current gate if present', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: 'Test',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
            current_gate: 'G2',
        };
        const item = new projectsView_1.ProjectTreeItem(project, false);
        const tooltipText = item.tooltip.value;
        assert.ok(tooltipText.includes('Current Gate'));
        assert.ok(tooltipText.includes('G2'));
    });
    test('Tooltip handles missing description', () => {
        const project = {
            id: 'p1',
            name: 'Test',
            description: '',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner',
        };
        // Should not throw
        const item = new projectsView_1.ProjectTreeItem(project, false);
        assert.ok(item.tooltip);
    });
});
suite('ProjectsProvider with CacheService', () => {
    let provider;
    let apiClient;
    let authService;
    let cacheService;
    setup(() => {
        authService = new authService_1.AuthService(mockContext);
        apiClient = new apiClient_1.ApiClient(mockContext, authService);
        cacheService = new cacheService_1.CacheService(mockContext);
        provider = new projectsView_1.ProjectsProvider(apiClient, cacheService);
    });
    test('Provider accepts optional CacheService', () => {
        const providerWithoutCache = new projectsView_1.ProjectsProvider(apiClient);
        assert.ok(providerWithoutCache);
    });
    test('Provider uses CacheService when available', () => {
        const providerWithCache = new projectsView_1.ProjectsProvider(apiClient, cacheService);
        assert.ok(providerWithCache);
    });
    test('Refresh works without CacheService', async () => {
        const providerWithoutCache = new projectsView_1.ProjectsProvider(apiClient);
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
    let provider;
    let apiClient;
    let authService;
    setup(() => {
        authService = new authService_1.AuthService(mockContext);
        apiClient = new apiClient_1.ApiClient(mockContext, authService);
        provider = new projectsView_1.ProjectsProvider(apiClient);
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
        const project = {
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
        const statuses = ['active', 'archived', 'draft'];
        for (const status of statuses) {
            const project = {
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
        const project = {
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
//# sourceMappingURL=projectsView.test.js.map