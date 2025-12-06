"use strict";
/**
 * Gate Status View Unit Tests
 *
 * Sprint 27 Day 2 - Testing
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
const gateStatusView_1 = require("../../views/gateStatusView");
const apiClient_1 = require("../../services/apiClient");
const authService_1 = require("../../services/authService");
const cacheService_1 = require("../../services/cacheService");
const testHelpers_1 = require("./testHelpers");
const mockContext = testHelpers_1.simpleMockContext;
suite('GateStatusProvider Test Suite', () => {
    let provider;
    let apiClient;
    let authService;
    let cacheService;
    setup(() => {
        authService = new authService_1.AuthService(mockContext);
        apiClient = new apiClient_1.ApiClient(mockContext, authService);
        cacheService = new cacheService_1.CacheService(mockContext);
        provider = new gateStatusView_1.GateStatusProvider(apiClient, cacheService);
    });
    test('GateStatusProvider initializes correctly', () => {
        assert.ok(provider);
    });
    test('getTreeItem returns tree item for gate', () => {
        const mockGate = {
            id: 'gate-1',
            project_id: 'project-1',
            gate_type: 'G1',
            name: 'Legal Validation',
            description: 'Legal and market validation',
            status: 'approved',
            evidence_count: 5,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const treeItem = provider.getTreeItem(new gateStatusView_1.GateTreeItem(`${mockGate.gate_type}: ${mockGate.name}`, vscode.TreeItemCollapsibleState.None, mockGate));
        assert.ok(treeItem);
        assert.strictEqual(treeItem.collapsibleState, vscode.TreeItemCollapsibleState.None);
    });
    test('GateTreeItem has correct label', () => {
        const mockGate = {
            id: 'gate-2',
            project_id: 'project-1',
            gate_type: 'G2',
            name: 'Design Ready',
            description: 'Design phase complete',
            status: 'pending_approval',
            evidence_count: 3,
            required_evidence_count: 8,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const label = `${mockGate.gate_type}: ${mockGate.name}`;
        const treeItem = new gateStatusView_1.GateTreeItem(label, vscode.TreeItemCollapsibleState.Collapsed, mockGate);
        assert.ok(treeItem.label);
        assert.ok((treeItem.label).includes('G2'));
    });
    test('GateTreeItem has tooltip with description', () => {
        const mockGate = {
            id: 'gate-3',
            project_id: 'project-1',
            gate_type: 'G3',
            name: 'Ship Ready',
            description: 'Ready for production release',
            status: 'in_progress',
            evidence_count: 10,
            required_evidence_count: 15,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const label = `${mockGate.gate_type}: ${mockGate.name}`;
        const treeItem = new gateStatusView_1.GateTreeItem(label, vscode.TreeItemCollapsibleState.Collapsed, mockGate);
        assert.ok(treeItem.tooltip);
        assert.ok(treeItem.tooltip.value.includes('Ship Ready'));
    });
    test('GateTreeItem context value is gate', () => {
        const mockGate = {
            id: 'gate-4',
            project_id: 'project-1',
            gate_type: 'G0',
            name: 'Problem Definition',
            description: 'Problem definition complete',
            status: 'not_started',
            evidence_count: 0,
            required_evidence_count: 3,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const label = `${mockGate.gate_type}: ${mockGate.name}`;
        const treeItem = new gateStatusView_1.GateTreeItem(label, vscode.TreeItemCollapsibleState.Collapsed, mockGate);
        assert.strictEqual(treeItem.contextValue, 'gate');
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
// Helper to create GateTreeItem from Gate
function createGateTreeItem(gate) {
    const label = `${gate.gate_type}: ${gate.name}`;
    return new gateStatusView_1.GateTreeItem(label, vscode.TreeItemCollapsibleState.Collapsed, gate);
}
suite('GateTreeItem Status Icons', () => {
    test('Approved gate has check icon', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G1',
            name: 'Test',
            description: 'Test',
            status: 'approved',
            evidence_count: 5,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        assert.ok(item.iconPath);
    });
    test('Rejected gate has error icon', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G1',
            name: 'Test',
            description: 'Test',
            status: 'rejected',
            evidence_count: 2,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        assert.ok(item.iconPath);
    });
    test('Pending gate has clock icon', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G1',
            name: 'Test',
            description: 'Test',
            status: 'pending_approval',
            evidence_count: 4,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        assert.ok(item.iconPath);
    });
    test('In progress gate has loading icon', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G1',
            name: 'Test',
            description: 'Test',
            status: 'in_progress',
            evidence_count: 3,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        assert.ok(item.iconPath);
    });
    test('Not started gate has circle icon', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G1',
            name: 'Test',
            description: 'Test',
            status: 'not_started',
            evidence_count: 0,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        assert.ok(item.iconPath);
    });
});
suite('GateTreeItem Progress Display', () => {
    test('Shows progress percentage in description', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G2',
            name: 'Design',
            description: 'Design gate',
            status: 'in_progress',
            evidence_count: 5,
            required_evidence_count: 10,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        // Description should show 50% or 5/10
        assert.ok(item.description);
        const desc = item.description;
        assert.ok(desc.includes('50%') || desc.includes('5/10'));
    });
    test('Shows 100% for fully complete gate', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G2',
            name: 'Design',
            description: 'Design gate',
            status: 'approved',
            evidence_count: 10,
            required_evidence_count: 10,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        const item = createGateTreeItem(gate);
        // Should show complete status
        assert.ok(item.description);
    });
    test('Handles zero required evidence', () => {
        const gate = {
            id: 'g1',
            project_id: 'p1',
            gate_type: 'G0',
            name: 'Init',
            description: 'Initial gate',
            status: 'not_started',
            evidence_count: 0,
            required_evidence_count: 0,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        };
        // Should not throw
        const item = createGateTreeItem(gate);
        assert.ok(item);
    });
});
//# sourceMappingURL=gateStatusView.test.js.map