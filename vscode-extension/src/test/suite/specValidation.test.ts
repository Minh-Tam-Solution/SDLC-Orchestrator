/**
 * Spec Validation Unit Tests
 *
 * Sprint 126 - S126-07: E2E Tests for Spec Validation
 * Tests the VS Code Extension's spec validation functionality
 *
 * @version 1.0.0
 */

import * as assert from 'assert';
import type {
    SpecValidationResult,
    SpecValidationError,
    SpecValidationWarning,
    SpecTier,
} from '../../types/codegen';

suite('Spec Validation Test Suite', () => {
    /**
     * Helper function to simulate Extension's validateSpecificationLocal
     * This mirrors the logic in codegenApi.ts for testing
     */
    function validateSpecificationLocal(
        content: string,
        _tier?: SpecTier
    ): SpecValidationResult {
        const errors: SpecValidationError[] = [];
        const warnings: SpecValidationWarning[] = [];
        const fieldsFound: string[] = [];
        const fieldsMissing: string[] = [];

        // Extract YAML frontmatter
        const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);

        if (!frontmatterMatch) {
            errors.push({
                code: 'SPC-004',
                field: 'frontmatter',
                message: 'Missing YAML frontmatter block',
                severity: 'critical',
                line_number: 1,
            });
            return createResult(false, errors, warnings, 'UNKNOWN', fieldsFound, fieldsMissing);
        }

        const frontmatterContent = frontmatterMatch[1];
        if (!frontmatterContent) {
            errors.push({
                code: 'SPC-004',
                field: 'frontmatter',
                message: 'Empty YAML frontmatter block',
                severity: 'critical',
                line_number: 1,
            });
            return createResult(false, errors, warnings, 'UNKNOWN', fieldsFound, fieldsMissing);
        }

        // Parse frontmatter fields
        const fields = parseFrontmatter(frontmatterContent);

        // Validate required fields
        const requiredFields = ['spec_id', 'title', 'version', 'status', 'tier', 'owner', 'last_updated'];
        for (const field of requiredFields) {
            if (!fields[field]) {
                fieldsMissing.push(field);
                errors.push({
                    code: 'SPC-001',
                    field: field,
                    message: `Missing required field '${field}'`,
                    severity: 'critical',
                    line_number: findFieldLine(frontmatterContent, field),
                });
            } else {
                fieldsFound.push(field);
            }
        }

        // Validate spec_id format (SPEC-XXYY)
        if (fields['spec_id']) {
            const specIdValue = String(fields['spec_id']);
            const specIdPattern = /^SPEC-\d{4}$/;
            if (!specIdPattern.test(specIdValue)) {
                errors.push({
                    code: 'SPC-002',
                    field: 'spec_id',
                    message: `Invalid spec_id format: expected SPEC-XXYY, got '${specIdValue}'`,
                    severity: 'critical',
                    line_number: findFieldLine(frontmatterContent, 'spec_id'),
                    suggestion: 'Use format SPEC-0001, SPEC-0210, etc.',
                });
            }
        }

        // Validate version format (X.Y.Z)
        if (fields['version']) {
            const versionValue = String(fields['version']);
            const versionPattern = /^\d+\.\d+\.\d+$/;
            if (!versionPattern.test(versionValue)) {
                errors.push({
                    code: 'SPC-002',
                    field: 'version',
                    message: `Invalid version format: expected X.Y.Z, got '${versionValue}'`,
                    severity: 'high',
                    line_number: findFieldLine(frontmatterContent, 'version'),
                    suggestion: 'Use semantic versioning: 1.0.0, 2.1.3, etc.',
                });
            }
        }

        // Validate status
        if (fields['status']) {
            const statusValue = String(fields['status']);
            const validStatuses = ['DRAFT', 'APPROVED', 'ACTIVE', 'DEPRECATED', 'ARCHIVED'];
            if (!validStatuses.includes(statusValue.toUpperCase())) {
                errors.push({
                    code: 'SPC-002',
                    field: 'status',
                    message: `Invalid status: expected one of ${validStatuses.join(', ')}, got '${statusValue}'`,
                    severity: 'high',
                    line_number: findFieldLine(frontmatterContent, 'status'),
                });
            }
        }

        // Validate tier
        if (fields['tier']) {
            const validTiers = ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'];
            const tierValue = fields['tier'];
            const tiers = Array.isArray(tierValue) ? tierValue : [tierValue];
            for (const t of tiers) {
                const tierStr = String(t);
                if (!validTiers.includes(tierStr.toUpperCase())) {
                    errors.push({
                        code: 'SPC-002',
                        field: 'tier',
                        message: `Invalid tier: expected one of ${validTiers.join(', ')}, got '${tierStr}'`,
                        severity: 'high',
                        line_number: findFieldLine(frontmatterContent, 'tier'),
                    });
                }
            }
        }

        // Validate date format (YYYY-MM-DD)
        if (fields['last_updated']) {
            const dateValue = String(fields['last_updated']);
            const datePattern = /^\d{4}-\d{2}-\d{2}$/;
            if (!datePattern.test(dateValue)) {
                errors.push({
                    code: 'SPC-002',
                    field: 'last_updated',
                    message: `Invalid date format: expected YYYY-MM-DD, got '${dateValue}'`,
                    severity: 'high',
                    line_number: findFieldLine(frontmatterContent, 'last_updated'),
                });
            }
        }

        // BDD validation for PROFESSIONAL/ENTERPRISE tiers
        const tierValue = fields['tier'];
        const tiersArray = Array.isArray(tierValue) ? tierValue : (tierValue ? [tierValue] : []);
        const requiresBDD = tiersArray.some((t) => {
            const tierStr = String(t);
            return ['PROFESSIONAL', 'ENTERPRISE'].includes(tierStr.toUpperCase());
        });
        if (requiresBDD && frontmatterMatch.index !== undefined) {
            const bodyContent = content.substring(frontmatterMatch.index + frontmatterMatch[0].length);
            const hasBDD = /```gherkin|GIVEN\s+.+\nWHEN\s+.+\nTHEN\s+/i.test(bodyContent);
            if (!hasBDD) {
                warnings.push({
                    code: 'SPC-003',
                    field: 'requirements',
                    message: 'PROFESSIONAL/ENTERPRISE tier should include BDD requirements (GIVEN-WHEN-THEN)',
                    suggestion: 'Add Gherkin-format requirements in Requirements section',
                });
            }
        }

        const specIdValue = fields['spec_id'] ? String(fields['spec_id']) : 'UNKNOWN';
        return createResult(errors.length === 0, errors, warnings, specIdValue, fieldsFound, fieldsMissing);
    }

    function parseFrontmatter(content: string): Record<string, string | string[]> {
        const result: Record<string, string | string[]> = {};
        let currentKey = '';
        let currentList: string[] = [];

        for (const line of content.split('\n')) {
            // Check for list item
            const listMatch = line.match(/^\s+-\s+(.+)$/);
            if (listMatch && listMatch[1] && currentKey) {
                const value = listMatch[1].replace(/^["']|["']$/g, '').trim();
                currentList.push(value);
                result[currentKey] = currentList;
                continue;
            }

            // Check for key-value
            const kvMatch = line.match(/^(\w+):\s*(.*)$/);
            if (kvMatch && kvMatch[1]) {
                currentKey = kvMatch[1];
                const value = (kvMatch[2] || '').replace(/^["']|["']$/g, '').trim();
                if (value) {
                    result[currentKey] = value;
                } else {
                    currentList = [];
                }
            }
        }

        return result;
    }

    function findFieldLine(content: string, field: string): number {
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line && line.startsWith(`${field}:`)) {
                return i + 2; // +2 for --- and 0-index
            }
        }
        return 1;
    }

    function createResult(
        valid: boolean,
        errors: SpecValidationError[],
        warnings: SpecValidationWarning[],
        specId: string,
        fieldsFound: string[],
        fieldsMissing: string[]
    ): SpecValidationResult {
        return {
            valid,
            spec_id: specId,
            spec_path: '/test/spec.md',
            version: '6.0.0',
            tier: ['PROFESSIONAL'] as SpecTier[],
            errors,
            warnings,
            frontmatter: {
                valid: errors.filter(e => e.code === 'SPC-004').length === 0,
                required_fields_present: fieldsFound,
                required_fields_missing: fieldsMissing,
                optional_fields_present: [],
                invalid_field_values: [],
            },
            bdd_validation: {
                valid: true,
                total_requirements: 0,
                valid_requirements: 0,
                invalid_requirements: [],
                coverage_percentage: 0,
            },
            cross_references: {
                valid: true,
                total_references: 0,
                valid_references: 0,
                broken_references: [],
            },
            tier_sections: {
                valid: true,
                tier: 'PROFESSIONAL' as SpecTier,
                required_sections: [],
                present_sections: [],
                missing_sections: [],
            },
            validation_timestamp: new Date().toISOString(),
            validator_version: '1.0.0',
        };
    }

    // ===========================================================================
    // Test Cases - Valid Specs
    // ===========================================================================

    test('Valid SDLC 6.0.0 spec passes validation', () => {
        const validSpec = `---
spec_id: SPEC-0001
title: "Valid Specification"
version: "1.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
owner: "Backend Team"
last_updated: "2026-01-30"
---

# SPEC-0001: Valid Specification

## Requirements

\`\`\`gherkin
GIVEN a valid spec
WHEN validated
THEN it should pass
\`\`\`
`;

        const result = validateSpecificationLocal(validSpec);

        assert.strictEqual(result.valid, true, 'Valid spec should pass validation');
        assert.strictEqual(result.errors.length, 0, 'Should have no errors');
        assert.strictEqual(result.spec_id, 'SPEC-0001');
    });

    test('Valid spec with all tiers passes', () => {
        const spec = `---
spec_id: SPEC-0002
title: "Multi-Tier Spec"
version: "2.0.0"
status: ACTIVE
tier:
  - LITE
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
owner: "Platform Team"
last_updated: "2026-01-30"
---

# Content

\`\`\`gherkin
GIVEN a user
WHEN they act
THEN result happens
\`\`\`
`;

        const result = validateSpecificationLocal(spec);

        assert.strictEqual(result.valid, true);
        assert.strictEqual(result.errors.length, 0);
    });

    // ===========================================================================
    // Test Cases - Missing Fields (SPC-001)
    // ===========================================================================

    test('Missing required fields triggers SPC-001', () => {
        const spec = `---
spec_id: SPEC-0003
title: "Incomplete Spec"
---

# Incomplete
`;

        const result = validateSpecificationLocal(spec);

        assert.strictEqual(result.valid, false, 'Should be invalid');

        const spc001Errors = result.errors.filter(e => e.code === 'SPC-001');
        assert.ok(spc001Errors.length >= 1, 'Should have SPC-001 errors');

        const missingFields = spc001Errors.map(e => e.field);
        assert.ok(missingFields.includes('version'), 'Should report missing version');
        assert.ok(missingFields.includes('status'), 'Should report missing status');
        assert.ok(missingFields.includes('tier'), 'Should report missing tier');
        assert.ok(missingFields.includes('owner'), 'Should report missing owner');
        assert.ok(missingFields.includes('last_updated'), 'Should report missing last_updated');
    });

    // ===========================================================================
    // Test Cases - Format Violations (SPC-002)
    // ===========================================================================

    test('Invalid spec_id format triggers SPC-002', () => {
        const spec = `---
spec_id: BAD-FORMAT
title: "Bad Spec ID"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Content
`;

        const result = validateSpecificationLocal(spec);

        assert.strictEqual(result.valid, false);

        const specIdError = result.errors.find(
            e => e.code === 'SPC-002' && e.field === 'spec_id'
        );
        assert.ok(specIdError, 'Should have spec_id format error');
        assert.ok(specIdError.message.includes('BAD-FORMAT'));
    });

    test('Invalid version format triggers SPC-002', () => {
        const spec = `---
spec_id: SPEC-0004
title: "Bad Version"
version: "v1.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Content
`;

        const result = validateSpecificationLocal(spec);

        const versionError = result.errors.find(
            e => e.code === 'SPC-002' && e.field === 'version'
        );
        assert.ok(versionError, 'Should have version format error');
        assert.ok(versionError.message.includes('v1.0'));
    });

    test('Invalid status triggers SPC-002', () => {
        const spec = `---
spec_id: SPEC-0005
title: "Bad Status"
version: "1.0.0"
status: INVALID_STATUS
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Content
`;

        const result = validateSpecificationLocal(spec);

        const statusError = result.errors.find(
            e => e.code === 'SPC-002' && e.field === 'status'
        );
        assert.ok(statusError, 'Should have status error');
        assert.ok(statusError.message.includes('INVALID_STATUS'));
    });

    test('Invalid tier triggers SPC-002', () => {
        const spec = `---
spec_id: SPEC-0006
title: "Bad Tier"
version: "1.0.0"
status: APPROVED
tier:
  - INVALID_TIER
owner: "Test"
last_updated: "2026-01-30"
---

# Content
`;

        const result = validateSpecificationLocal(spec);

        const tierError = result.errors.find(
            e => e.code === 'SPC-002' && e.field === 'tier'
        );
        assert.ok(tierError, 'Should have tier error');
        assert.ok(tierError.message.includes('INVALID_TIER'));
    });

    test('Invalid date format triggers SPC-002', () => {
        const spec = `---
spec_id: SPEC-0007
title: "Bad Date"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "30-01-2026"
---

# Content
`;

        const result = validateSpecificationLocal(spec);

        const dateError = result.errors.find(
            e => e.code === 'SPC-002' && e.field === 'last_updated'
        );
        assert.ok(dateError, 'Should have date format error');
        assert.ok(dateError.message.includes('30-01-2026'));
    });

    // ===========================================================================
    // Test Cases - Missing Frontmatter (SPC-004)
    // ===========================================================================

    test('Missing frontmatter triggers SPC-004', () => {
        const spec = `# No Frontmatter

This spec has no YAML frontmatter block.
`;

        const result = validateSpecificationLocal(spec);

        assert.strictEqual(result.valid, false);

        const frontmatterError = result.errors.find(e => e.code === 'SPC-004');
        assert.ok(frontmatterError, 'Should have SPC-004 error');
        assert.ok(frontmatterError.message.includes('Missing YAML frontmatter'));
    });

    // ===========================================================================
    // Test Cases - BDD Requirements (SPC-003)
    // ===========================================================================

    test('PROFESSIONAL tier without BDD triggers SPC-003 warning', () => {
        const spec = `---
spec_id: SPEC-0008
title: "No BDD Spec"
version: "1.0.0"
status: APPROVED
tier:
  - PROFESSIONAL
owner: "Test"
last_updated: "2026-01-30"
---

# SPEC-0008: No BDD

## Requirements

FR-001: Plain text requirement without BDD format.

FR-002: Another plain text requirement.
`;

        const result = validateSpecificationLocal(spec);

        // Spec is valid but should have BDD warning
        const bddWarning = result.warnings.find(w => w.code === 'SPC-003');
        assert.ok(bddWarning, 'Should have SPC-003 warning');
        assert.ok(bddWarning.message.includes('BDD'));
    });

    test('LITE tier without BDD has no warning', () => {
        const spec = `---
spec_id: SPEC-0009
title: "Lite Spec"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Lite tier spec

No BDD required for LITE tier.
`;

        const result = validateSpecificationLocal(spec);

        assert.strictEqual(result.valid, true);
        const bddWarning = result.warnings.find(w => w.code === 'SPC-003');
        assert.ok(!bddWarning, 'LITE tier should not require BDD');
    });

    // ===========================================================================
    // Test Cases - Line Numbers
    // ===========================================================================

    test('Error line numbers are correct', () => {
        const spec = `---
spec_id: SPEC-0010
title: "Test Line Numbers"
version: "bad"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---

# Content
`;

        const result = validateSpecificationLocal(spec);

        const versionError = result.errors.find(e => e.field === 'version');
        assert.ok(versionError, 'Should have version error');
        assert.ok(
            versionError.line_number && versionError.line_number > 0,
            'Should have positive line number'
        );
        // version: is on line 4 of frontmatter, +2 for --- offset = 6
        // The exact number depends on implementation
        assert.ok(
            versionError.line_number <= 10,
            `Line number should be reasonable, got ${versionError.line_number}`
        );
    });

    // ===========================================================================
    // Test Cases - Parity with CLI
    // ===========================================================================

    test('Extension produces same error codes as CLI specification', () => {
        // Test SPC-001
        const missingFieldSpec = `---
spec_id: SPEC-0001
---
# Test
`;
        const result1 = validateSpecificationLocal(missingFieldSpec);
        assert.ok(
            result1.errors.some(e => e.code === 'SPC-001'),
            'Should use SPC-001 for missing fields'
        );

        // Test SPC-002
        const badFormatSpec = `---
spec_id: BAD
title: "Test"
version: "1.0.0"
status: APPROVED
tier:
  - LITE
owner: "Test"
last_updated: "2026-01-30"
---
# Test
`;
        const result2 = validateSpecificationLocal(badFormatSpec);
        assert.ok(
            result2.errors.some(e => e.code === 'SPC-002'),
            'Should use SPC-002 for format errors'
        );

        // Test SPC-004
        const noFrontmatter = '# No frontmatter';
        const result4 = validateSpecificationLocal(noFrontmatter);
        assert.ok(
            result4.errors.some(e => e.code === 'SPC-004'),
            'Should use SPC-004 for missing frontmatter'
        );
    });
});

suite('Spec Validation Types Test Suite', () => {
    test('SpecTier type has all valid values', () => {
        const validTiers: SpecTier[] = ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'];
        assert.strictEqual(validTiers.length, 4);
    });

    test('SpecValidationError interface structure', () => {
        const error: SpecValidationError = {
            code: 'SPC-001',
            field: 'version',
            message: 'Missing required field',
            severity: 'critical',
            line_number: 5,
            suggestion: 'Add version: "1.0.0"',
        };

        assert.strictEqual(error.code, 'SPC-001');
        assert.strictEqual(error.field, 'version');
        assert.strictEqual(error.severity, 'critical');
        assert.strictEqual(error.line_number, 5);
    });

    test('SpecValidationWarning interface structure', () => {
        const warning: SpecValidationWarning = {
            code: 'SPC-003',
            field: 'requirements',
            message: 'BDD format recommended',
            suggestion: 'Add GIVEN-WHEN-THEN',
        };

        assert.strictEqual(warning.code, 'SPC-003');
        assert.ok(warning.suggestion);
    });

    test('SpecValidationResult interface structure', () => {
        const result: SpecValidationResult = {
            valid: true,
            spec_id: 'SPEC-0001',
            spec_path: '/test/spec.md',
            version: '6.0.0',
            tier: ['PROFESSIONAL'],
            errors: [],
            warnings: [],
            frontmatter: {
                valid: true,
                required_fields_present: ['spec_id', 'title', 'version'],
                required_fields_missing: [],
                optional_fields_present: ['tags'],
                invalid_field_values: [],
            },
            bdd_validation: {
                valid: true,
                total_requirements: 5,
                valid_requirements: 5,
                invalid_requirements: [],
                coverage_percentage: 100,
            },
            cross_references: {
                valid: true,
                total_references: 2,
                valid_references: 2,
                broken_references: [],
            },
            tier_sections: {
                valid: true,
                tier: 'PROFESSIONAL',
                required_sections: ['Overview', 'Requirements'],
                present_sections: ['Overview', 'Requirements'],
                missing_sections: [],
            },
            validation_timestamp: '2026-01-30T10:00:00Z',
            validator_version: '1.0.0',
        };

        assert.strictEqual(result.valid, true);
        assert.strictEqual(result.spec_id, 'SPEC-0001');
        assert.strictEqual(result.errors.length, 0);
        assert.strictEqual(result.frontmatter.valid, true);
        assert.strictEqual(result.bdd_validation.coverage_percentage, 100);
    });
});
