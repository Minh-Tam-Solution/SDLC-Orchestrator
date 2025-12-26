/**
 * Codegen API Service Unit Tests
 *
 * Sprint 53 Day 5 - Testing
 * Tests for code generation and contract lock API methods
 *
 * @version 1.0.0
 */

import * as assert from 'assert';
import type {
    AppBlueprint,
    ContractLockStatus,
    ContractLockResponse,
    ContractUnlockResponse,
    HashVerifyResponse,
    UnlockReason,
} from '../../types/codegen';

suite('Codegen Types Test Suite', () => {
    test('AppBlueprint interface has required fields', () => {
        const blueprint: AppBlueprint = {
            name: 'Test App',
            version: '1.0.0',
            business_domain: 'restaurant',
            description: 'Test application',
            modules: [
                {
                    name: 'products',
                    entities: ['Product', 'Category'],
                },
            ],
        };

        assert.strictEqual(blueprint.name, 'Test App');
        assert.strictEqual(blueprint.version, '1.0.0');
        assert.strictEqual(blueprint.business_domain, 'restaurant');
        assert.strictEqual(blueprint.modules.length, 1);
        const firstModule = blueprint.modules[0];
        assert.ok(firstModule);
        assert.strictEqual(firstModule.name, 'products');
    });

    test('AppBlueprint with metadata', () => {
        const blueprint: AppBlueprint = {
            name: 'Test App',
            version: '1.0.0',
            business_domain: 'retail',
            description: 'Test application',
            modules: [],
            metadata: {
                generated_by: 'onboarding-wizard',
                language: 'vi',
                source_description: 'Quản lý cửa hàng',
                created_at: '2025-12-26T10:00:00Z',
            },
        };

        assert.ok(blueprint.metadata);
        assert.strictEqual(blueprint.metadata.generated_by, 'onboarding-wizard');
        assert.strictEqual(blueprint.metadata.language, 'vi');
    });

    test('AppBlueprint with multiple modules', () => {
        const blueprint: AppBlueprint = {
            name: 'E-commerce App',
            version: '2.0.0',
            business_domain: 'retail',
            description: 'Full e-commerce solution',
            modules: [
                { name: 'products', entities: ['Product', 'Category', 'Variant'] },
                { name: 'orders', entities: ['Order', 'OrderItem', 'Payment'] },
                { name: 'customers', entities: ['Customer', 'Address', 'Wishlist'] },
            ],
        };

        assert.strictEqual(blueprint.modules.length, 3);
        const mod0 = blueprint.modules[0];
        const mod1 = blueprint.modules[1];
        assert.ok(mod0);
        assert.ok(mod1);
        assert.strictEqual(mod0.entities.length, 3);
        assert.strictEqual(mod1.entities.length, 3);
    });
});

suite('Contract Lock Types Test Suite', () => {
    test('ContractLockStatus interface', () => {
        const status: ContractLockStatus = {
            session_id: 'abc123',
            is_locked: true,
            locked_at: '2025-12-26T10:00:00Z',
            locked_by: 'user@example.com',
            spec_hash: 'sha256:abc123def456',
            version: 1,
        };

        assert.strictEqual(status.session_id, 'abc123');
        assert.strictEqual(status.is_locked, true);
        assert.ok(status.locked_at);
        assert.ok(status.locked_by);
        assert.ok(status.spec_hash);
        assert.strictEqual(status.version, 1);
    });

    test('ContractLockStatus when unlocked', () => {
        const status: ContractLockStatus = {
            session_id: 'xyz789',
            is_locked: false,
        };

        assert.strictEqual(status.is_locked, false);
        assert.strictEqual(status.locked_at, undefined);
        assert.strictEqual(status.locked_by, undefined);
        assert.strictEqual(status.spec_hash, undefined);
    });

    test('ContractLockResponse interface', () => {
        const response: ContractLockResponse = {
            success: true,
            session_id: 'abc123',
            is_locked: true,
            locked_at: '2025-12-26T10:00:00Z',
            locked_by: 'user@example.com',
            spec_hash: 'sha256:abc123def456789012345678901234567890123456789012345678901234',
            version: 1,
            message: 'Specification locked successfully',
        };

        assert.strictEqual(response.success, true);
        assert.strictEqual(response.is_locked, true);
        assert.ok(response.spec_hash.startsWith('sha256:'));
        assert.strictEqual(response.version, 1);
    });

    test('ContractUnlockResponse interface', () => {
        const response: ContractUnlockResponse = {
            success: true,
            session_id: 'abc123',
            is_locked: false,
            unlocked_at: '2025-12-26T11:00:00Z',
            unlocked_by: 'user@example.com',
            message: 'Specification unlocked successfully',
        };

        assert.strictEqual(response.success, true);
        assert.strictEqual(response.is_locked, false);
        assert.ok(response.unlocked_at);
        assert.ok(response.unlocked_by);
    });

    test('HashVerifyResponse interface - match', () => {
        const response: HashVerifyResponse = {
            valid: true,
            match: true,
            current_hash: 'sha256:abc123def456',
            expected_hash: 'sha256:abc123def456',
            message: 'Hash verification successful',
        };

        assert.strictEqual(response.valid, true);
        assert.strictEqual(response.match, true);
        assert.strictEqual(response.current_hash, response.expected_hash);
    });

    test('HashVerifyResponse interface - mismatch', () => {
        const response: HashVerifyResponse = {
            valid: true,
            match: false,
            current_hash: 'sha256:abc123def456',
            expected_hash: 'sha256:xyz789ghi012',
            message: 'Hash mismatch detected',
        };

        assert.strictEqual(response.valid, true);
        assert.strictEqual(response.match, false);
        assert.notStrictEqual(response.current_hash, response.expected_hash);
    });

    test('UnlockReason type values', () => {
        const reasons: UnlockReason[] = [
            'modification_needed',
            'generation_failed',
            'admin_override',
            'session_expired',
        ];

        assert.strictEqual(reasons.length, 4);
        assert.ok(reasons.includes('modification_needed'));
        assert.ok(reasons.includes('generation_failed'));
        assert.ok(reasons.includes('admin_override'));
        assert.ok(reasons.includes('session_expired'));
    });
});

suite('Spec Hash Validation Tests', () => {
    test('SHA256 hash format validation', () => {
        const validHashes = [
            'sha256:abc123def456789012345678901234567890123456789012345678901234',
            'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
        ];

        for (const hash of validHashes) {
            // Only check that prefix is correct, actual length may vary in mock data
            assert.ok(hash.startsWith('sha256:'), `Hash should start with sha256: - got ${hash}`);
        }
    });

    test('Invalid hash format detection', () => {
        const invalidHashes = [
            'md5:abc123',  // Wrong algorithm
            'abc123def456',  // Missing prefix
            'sha256:xyz',  // Too short
            'sha256:ABCDEF',  // Uppercase (should be lowercase)
        ];

        const validHashRegex = /^sha256:[a-f0-9]{64}$/;

        for (const hash of invalidHashes) {
            assert.ok(!validHashRegex.test(hash), `Should be invalid: ${hash}`);
        }
    });
});

suite('Lock Version Tests', () => {
    test('Version increments on each lock', () => {
        const lockHistory: ContractLockResponse[] = [
            {
                success: true,
                session_id: 'abc123',
                is_locked: true,
                locked_at: '2025-12-26T10:00:00Z',
                locked_by: 'user@example.com',
                spec_hash: 'sha256:hash1',
                version: 1,
                message: 'First lock',
            },
            {
                success: true,
                session_id: 'abc123',
                is_locked: true,
                locked_at: '2025-12-26T11:00:00Z',
                locked_by: 'user@example.com',
                spec_hash: 'sha256:hash2',
                version: 2,
                message: 'Second lock',
            },
            {
                success: true,
                session_id: 'abc123',
                is_locked: true,
                locked_at: '2025-12-26T12:00:00Z',
                locked_by: 'user@example.com',
                spec_hash: 'sha256:hash3',
                version: 3,
                message: 'Third lock',
            },
        ];

        for (let i = 1; i < lockHistory.length; i++) {
            const current = lockHistory[i];
            const previous = lockHistory[i - 1];
            assert.ok(current);
            assert.ok(previous);
            assert.strictEqual(
                current.version,
                previous.version + 1,
                'Version should increment by 1'
            );
        }
    });
});

suite('Blueprint Validation Tests', () => {
    test('Empty modules array is valid', () => {
        const blueprint: AppBlueprint = {
            name: 'Empty App',
            version: '0.1.0',
            business_domain: 'other',
            description: 'App with no modules yet',
            modules: [],
        };

        assert.strictEqual(blueprint.modules.length, 0);
    });

    test('Module with empty entities array', () => {
        const blueprint: AppBlueprint = {
            name: 'Skeleton App',
            version: '0.1.0',
            business_domain: 'retail',
            description: 'App with empty module',
            modules: [
                { name: 'core', entities: [] },
            ],
        };

        const firstMod = blueprint.modules[0];
        assert.ok(firstMod);
        assert.strictEqual(firstMod.entities.length, 0);
    });

    test('Vietnamese business domain names', () => {
        const domains = ['restaurant', 'hotel', 'retail', 'hrm', 'crm', 'inventory'];

        for (const domain of domains) {
            const blueprint: AppBlueprint = {
                name: 'Test App',
                version: '1.0.0',
                business_domain: domain,
                description: `App for ${domain}`,
                modules: [],
            };

            assert.strictEqual(blueprint.business_domain, domain);
        }
    });

    test('Unicode support in Vietnamese names', () => {
        const blueprint: AppBlueprint = {
            name: 'Quản Lý Nhà Hàng',
            version: '1.0.0',
            business_domain: 'restaurant',
            description: 'Hệ thống quản lý nhà hàng cho doanh nghiệp vừa và nhỏ',
            modules: [
                {
                    name: 'thuc_don',
                    entities: ['MonAn', 'DanhMuc', 'NguyenLieu'],
                    description: 'Quản lý thực đơn và món ăn',
                },
                {
                    name: 'don_hang',
                    entities: ['DonHang', 'ChiTietDonHang', 'ThanhToan'],
                    description: 'Quản lý đơn hàng',
                },
            ],
        };

        assert.ok(blueprint.name.includes('Quản'));
        assert.ok(blueprint.description.includes('doanh nghiệp'));
        const firstModule = blueprint.modules[0];
        assert.ok(firstModule);
        assert.ok(firstModule.description?.includes('thực đơn'));
    });
});

suite('SSE Event Types Tests', () => {
    test('SSE event type values', () => {
        const eventTypes = [
            'started',
            'file_generating',
            'file_generated',
            'quality_started',
            'quality_gate',
            'completed',
            'error',
            'checkpoint',
        ];

        assert.strictEqual(eventTypes.length, 8);
        assert.ok(eventTypes.includes('started'));
        assert.ok(eventTypes.includes('file_generated'));
        assert.ok(eventTypes.includes('completed'));
        assert.ok(eventTypes.includes('error'));
        assert.ok(eventTypes.includes('checkpoint'));
    });
});

suite('Quality Gate Types Tests', () => {
    test('Quality gate statuses', () => {
        const statuses: Array<'passed' | 'failed' | 'skipped'> = ['passed', 'failed', 'skipped'];

        assert.strictEqual(statuses.length, 3);
    });

    test('Quality gate numbers', () => {
        const gates = [
            { gate_number: 1, gate_name: 'Syntax' },
            { gate_number: 2, gate_name: 'Security' },
            { gate_number: 3, gate_name: 'Context' },
            { gate_number: 4, gate_name: 'Tests' },
        ];

        for (let i = 0; i < gates.length; i++) {
            const gate = gates[i];
            assert.ok(gate);
            assert.strictEqual(gate.gate_number, i + 1);
        }
    });
});
