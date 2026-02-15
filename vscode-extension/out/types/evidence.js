"use strict";
/**
 * Evidence Types for SDLC Orchestrator VS Code Extension
 *
 * Sprint 139 - Task 3: Evidence Type Definitions
 * Implements RFC-SDLC-602 E2E API Testing evidence types.
 *
 * Reference:
 * - RFC-SDLC-602-E2E-API-TESTING
 * - SPEC-0016 Implementation Evidence Schema
 * - SDLC Framework 6.0.5
 *
 * @version 1.0.0
 * @since Sprint 139
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.EvidenceType = void 0;
// ========================================
// Base Evidence Types (SPEC-0016)
// ========================================
/**
 * Evidence type enumeration - SDLC 6.0.5 compliant
 */
var EvidenceType;
(function (EvidenceType) {
    // Existing types (SPEC-0016)
    EvidenceType["REQUIREMENTS_DOCUMENT"] = "requirements_document";
    EvidenceType["DESIGN_DOCUMENT"] = "design_document";
    EvidenceType["CODE_REVIEW"] = "code_review";
    EvidenceType["TEST_RESULTS"] = "test_results";
    EvidenceType["DEPLOYMENT_LOG"] = "deployment_log";
    EvidenceType["AUDIT_TRAIL"] = "audit_trail";
    // NEW - RFC-SDLC-602 E2E API Testing Evidence Types
    EvidenceType["E2E_TESTING_REPORT"] = "e2e_testing_report";
    EvidenceType["API_DOCUMENTATION_REFERENCE"] = "api_documentation_reference";
    EvidenceType["SECURITY_TESTING_RESULTS"] = "security_testing_results";
    EvidenceType["STAGE_CROSS_REFERENCE"] = "stage_cross_reference";
})(EvidenceType || (exports.EvidenceType = EvidenceType = {}));
//# sourceMappingURL=evidence.js.map