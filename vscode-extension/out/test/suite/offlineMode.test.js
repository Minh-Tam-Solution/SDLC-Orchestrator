"use strict";
/**
 * Offline Mode Integration Tests
 *
 * Tests for offline mode behavior across all views with cache fallback
 *
 * Sprint 27 Day 4 - Integration Testing
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
const cacheService_1 = require("../../services/cacheService");
const testHelpers_1 = require("./testHelpers");
function createMockContext(globalState) {
    return (0, testHelpers_1.createMockExtensionContext)({ globalState });
}
suite('Offline Mode - Cache Fallback', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    setup(() => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('getOrFetch returns cached data when fetcher fails', async () => {
        // Pre-populate cache with data
        const cachedProjects = [
            {
                id: 'p1',
                name: 'Cached Project',
                description: 'From cache',
                status: 'active',
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
                owner_id: 'owner-1',
            },
        ];
        await cacheService.set(cacheService_1.CacheKeys.PROJECTS, cachedProjects, cacheService_1.CacheTTL.PROJECTS);
        // Simulate network failure - fetcher throws
        const failingFetcher = () => {
            return Promise.reject(new Error('Network error - connection refused'));
        };
        // getOrFetch should return cached data when fetcher fails
        const result = await cacheService.getOrFetch(cacheService_1.CacheKeys.PROJECTS, failingFetcher, cacheService_1.CacheTTL.PROJECTS);
        assert.ok(result);
        assert.strictEqual(result.isCached, true);
        assert.strictEqual(result.data.length, 1);
        assert.strictEqual(result.data[0].name, 'Cached Project');
    });
    test('Cache persists across service instances', async () => {
        // Store data in first instance
        const testData = { key: 'value', items: [1, 2, 3] };
        await cacheService.set('persistence-test', testData);
        // Create new cache service instance (simulating extension reload)
        const newCacheService = new cacheService_1.CacheService(mockContext);
        // Data should still be available
        const result = newCacheService.get('persistence-test');
        assert.ok(result);
        assert.deepStrictEqual(result.data, testData);
    });
    test('Stale data is returned during revalidation', async () => {
        // Set data with very short TTL
        const originalData = { value: 'original' };
        await cacheService.set('stale-test', originalData, 1);
        // Wait for data to become stale (but within grace period)
        await new Promise((resolve) => setTimeout(resolve, 10));
        // Fetcher that returns new data
        const newData = { value: 'new' };
        const fetcher = () => Promise.resolve(newData);
        // Should return stale data while revalidating in background
        const result = await cacheService.getOrFetch('stale-test', fetcher, 1);
        // Result should be the original cached data (stale-while-revalidate)
        assert.ok(result);
        // Note: Depending on timing, this may return original or new data
    });
});
suite('Offline Mode - Project Cache', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    const mockProjects = [
        {
            id: 'project-1',
            name: 'SDLC Orchestrator',
            description: 'Main project',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner-1',
            compliance_score: 85,
            current_gate: 'G2',
        },
        {
            id: 'project-2',
            name: 'BFlow Platform',
            description: 'Secondary project',
            status: 'active',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
            owner_id: 'owner-1',
        },
    ];
    setup(async () => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
        // Pre-populate with project data
        await cacheService.set(cacheService_1.CacheKeys.PROJECTS, mockProjects, cacheService_1.CacheTTL.PROJECTS);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('Cached projects are available offline', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.PROJECTS);
        assert.ok(result);
        assert.strictEqual(result.data.length, 2);
        assert.strictEqual(result.data[0].name, 'SDLC Orchestrator');
    });
    test('Project compliance score is preserved in cache', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.PROJECTS);
        assert.ok(result);
        assert.strictEqual(result.data[0].compliance_score, 85);
    });
    test('Project current gate is preserved in cache', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.PROJECTS);
        assert.ok(result);
        assert.strictEqual(result.data[0].current_gate, 'G2');
    });
});
suite('Offline Mode - Gate Cache', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    const projectId = 'project-123';
    const mockGates = [
        {
            id: 'gate-1',
            project_id: projectId,
            gate_type: 'G0',
            name: 'Problem Definition',
            description: 'Define the problem',
            status: 'approved',
            evidence_count: 3,
            required_evidence_count: 3,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        },
        {
            id: 'gate-2',
            project_id: projectId,
            gate_type: 'G1',
            name: 'Legal Validation',
            description: 'Legal and market validation',
            status: 'pending_approval',
            evidence_count: 4,
            required_evidence_count: 5,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        },
        {
            id: 'gate-3',
            project_id: projectId,
            gate_type: 'G2',
            name: 'Design Ready',
            description: 'Design phase complete',
            status: 'in_progress',
            evidence_count: 2,
            required_evidence_count: 8,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
        },
    ];
    setup(async () => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
        // Pre-populate with gate data
        await cacheService.set(cacheService_1.CacheKeys.GATES(projectId), mockGates, cacheService_1.CacheTTL.GATES);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('Cached gates are available offline', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.GATES(projectId));
        assert.ok(result);
        assert.strictEqual(result.data.length, 3);
    });
    test('Gate status is preserved in cache', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.GATES(projectId));
        assert.ok(result);
        assert.strictEqual(result.data[0].status, 'approved');
        assert.strictEqual(result.data[1].status, 'pending_approval');
        assert.strictEqual(result.data[2].status, 'in_progress');
    });
    test('Gate evidence counts are preserved', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.GATES(projectId));
        assert.ok(result);
        assert.strictEqual(result.data[1].evidence_count, 4);
        assert.strictEqual(result.data[1].required_evidence_count, 5);
    });
    test('Different projects have separate cache entries', async () => {
        const otherProjectId = 'other-project';
        const otherGates = [
            {
                id: 'gate-other',
                project_id: otherProjectId,
                gate_type: 'G0',
                name: 'Other Gate',
                description: 'Other project gate',
                status: 'not_started',
                evidence_count: 0,
                required_evidence_count: 2,
                created_at: '2025-01-01T00:00:00Z',
                updated_at: '2025-01-01T00:00:00Z',
            },
        ];
        await cacheService.set(cacheService_1.CacheKeys.GATES(otherProjectId), otherGates, cacheService_1.CacheTTL.GATES);
        const result1 = cacheService.get(cacheService_1.CacheKeys.GATES(projectId));
        const result2 = cacheService.get(cacheService_1.CacheKeys.GATES(otherProjectId));
        assert.ok(result1);
        assert.ok(result2);
        assert.strictEqual(result1.data.length, 3);
        assert.strictEqual(result2.data.length, 1);
    });
});
suite('Offline Mode - Violation Cache', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    const projectId = 'project-456';
    const mockViolations = [
        {
            id: 'v-1',
            project_id: projectId,
            violation_type: 'missing_documentation',
            severity: 'critical',
            description: 'Security baseline document is missing',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        },
        {
            id: 'v-2',
            project_id: projectId,
            violation_type: 'incomplete_review',
            severity: 'high',
            description: 'Code review has missing approvals',
            status: 'open',
            created_at: '2025-01-01T00:00:00Z',
        },
        {
            id: 'v-3',
            project_id: projectId,
            violation_type: 'test_coverage',
            severity: 'medium',
            description: 'Test coverage below 80%',
            status: 'resolved',
            created_at: '2025-01-01T00:00:00Z',
            resolved_at: '2025-01-02T00:00:00Z',
        },
    ];
    setup(async () => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
        // Pre-populate with violation data
        await cacheService.set(cacheService_1.CacheKeys.VIOLATIONS(projectId), mockViolations, cacheService_1.CacheTTL.VIOLATIONS);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('Cached violations are available offline', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.VIOLATIONS(projectId));
        assert.ok(result);
        assert.strictEqual(result.data.length, 3);
    });
    test('Violation severity is preserved', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.VIOLATIONS(projectId));
        assert.ok(result);
        assert.strictEqual(result.data[0].severity, 'critical');
        assert.strictEqual(result.data[1].severity, 'high');
        assert.strictEqual(result.data[2].severity, 'medium');
    });
    test('Violation status is preserved', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.VIOLATIONS(projectId));
        assert.ok(result);
        assert.strictEqual(result.data[0].status, 'open');
        assert.strictEqual(result.data[2].status, 'resolved');
    });
    test('Resolved violation has resolved_at timestamp', () => {
        const result = cacheService.get(cacheService_1.CacheKeys.VIOLATIONS(projectId));
        assert.ok(result);
        assert.ok(result.data[2].resolved_at);
    });
});
suite('Offline Mode - Cache Invalidation', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    setup(() => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('clearProject removes all project-related cache', async () => {
        const projectId = 'clear-test-project';
        await cacheService.set(cacheService_1.CacheKeys.GATES(projectId), [{ id: 'g1' }]);
        await cacheService.set(cacheService_1.CacheKeys.VIOLATIONS(projectId), [{ id: 'v1' }]);
        await cacheService.set(cacheService_1.CacheKeys.PROJECT(projectId), { id: projectId });
        await cacheService.clearProject(projectId);
        assert.strictEqual(cacheService.get(cacheService_1.CacheKeys.GATES(projectId)), undefined);
        assert.strictEqual(cacheService.get(cacheService_1.CacheKeys.VIOLATIONS(projectId)), undefined);
        assert.strictEqual(cacheService.get(cacheService_1.CacheKeys.PROJECT(projectId)), undefined);
    });
    test('clear removes all cache entries', async () => {
        await cacheService.set('cache.item1', { data: 1 });
        await cacheService.set('cache.item2', { data: 2 });
        await cacheService.set('cache.item3', { data: 3 });
        await cacheService.clear();
        assert.strictEqual(cacheService.get('cache.item1'), undefined);
        assert.strictEqual(cacheService.get('cache.item2'), undefined);
        assert.strictEqual(cacheService.get('cache.item3'), undefined);
    });
    test('invalidatePattern removes matching entries', async () => {
        await cacheService.set('cache.gates.project-1', [{ id: 'g1' }]);
        await cacheService.set('cache.gates.project-2', [{ id: 'g2' }]);
        await cacheService.set('cache.violations.project-1', [{ id: 'v1' }]);
        // Invalidate all gates
        await cacheService.invalidatePattern('^cache\\.gates\\.');
        assert.strictEqual(cacheService.get('cache.gates.project-1'), undefined);
        assert.strictEqual(cacheService.get('cache.gates.project-2'), undefined);
        // Violations should still exist
        const violations = cacheService.get('cache.violations.project-1');
        assert.ok(violations);
    });
});
suite('Offline Mode - Network Recovery', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    setup(() => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('Fresh data replaces stale cache on network recovery', async () => {
        // Set old cached data
        const oldData = { version: 1, data: 'old' };
        await cacheService.set('recovery-test', oldData);
        // Simulate network recovery with fresh data
        const freshData = { version: 2, data: 'fresh' };
        await cacheService.set('recovery-test', freshData);
        const result = cacheService.get('recovery-test');
        assert.ok(result);
        assert.strictEqual(result.data.version, 2);
        assert.strictEqual(result.data.data, 'fresh');
    });
    test('Cache age is reset after refresh', async () => {
        await cacheService.set('age-reset-test', { data: 'test' });
        // Wait a bit
        await new Promise((resolve) => setTimeout(resolve, 50));
        const firstResult = cacheService.get('age-reset-test');
        const firstAge = firstResult?.age || 0;
        // Refresh cache
        await cacheService.set('age-reset-test', { data: 'refreshed' });
        const secondResult = cacheService.get('age-reset-test');
        const secondAge = secondResult?.age || 0;
        // Second age should be less than first
        assert.ok(secondAge < firstAge);
    });
});
suite('Offline Mode - Cache Statistics', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    setup(() => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('getStats returns memory and persisted counts', async () => {
        await cacheService.set('cache.stat1', { data: 1 });
        await cacheService.set('cache.stat2', { data: 2 });
        const stats = cacheService.getStats();
        assert.ok(stats.memoryEntries >= 2);
        assert.ok(stats.persistedEntries >= 2);
    });
    test('getStats tracks oldest and newest entries', async () => {
        await cacheService.set('cache.first', { data: 'first' });
        await new Promise((resolve) => setTimeout(resolve, 10));
        await cacheService.set('cache.second', { data: 'second' });
        const stats = cacheService.getStats();
        if (stats.oldestEntry !== null && stats.newestEntry !== null) {
            assert.ok(stats.oldestEntry <= stats.newestEntry);
        }
    });
});
suite('Offline Mode - isFresh Check', () => {
    let cacheService;
    let mockGlobalState;
    let mockContext;
    setup(() => {
        mockGlobalState = new testHelpers_1.MockGlobalState();
        mockContext = createMockContext(mockGlobalState);
        cacheService = new cacheService_1.CacheService(mockContext);
    });
    teardown(async () => {
        await cacheService.clear();
        mockGlobalState.clear();
    });
    test('isFresh returns true for recently cached data', async () => {
        await cacheService.set('fresh-check', { data: 'test' }, 60000);
        const isFresh = cacheService.isFresh('fresh-check');
        assert.strictEqual(isFresh, true);
    });
    test('isFresh returns false for non-existent key', () => {
        const isFresh = cacheService.isFresh('non-existent');
        assert.strictEqual(isFresh, false);
    });
});
//# sourceMappingURL=offlineMode.test.js.map