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
/**
 * Evidence type enumeration - SDLC 6.0.5 compliant
 */
export declare enum EvidenceType {
    REQUIREMENTS_DOCUMENT = "requirements_document",
    DESIGN_DOCUMENT = "design_document",
    CODE_REVIEW = "code_review",
    TEST_RESULTS = "test_results",
    DEPLOYMENT_LOG = "deployment_log",
    AUDIT_TRAIL = "audit_trail",
    E2E_TESTING_REPORT = "e2e_testing_report",
    API_DOCUMENTATION_REFERENCE = "api_documentation_reference",
    SECURITY_TESTING_RESULTS = "security_testing_results",
    STAGE_CROSS_REFERENCE = "stage_cross_reference"
}
/**
 * Base evidence metadata
 */
export interface EvidenceMetadata {
    id: string;
    type: EvidenceType;
    projectId: string;
    createdAt: string;
    createdBy: string;
    version: string;
    sdlcStage: string;
    tags?: string[];
}
/**
 * Endpoint coverage information
 */
export interface EndpointCoverage {
    method: string;
    path: string;
    tested: boolean;
    passed: boolean;
    statusCode?: number;
    responseTime?: number;
    errorMessage?: string;
}
/**
 * E2E Testing Report evidence
 * Phase 3: Report generation output
 */
export interface E2ETestingReport {
    timestamp: string;
    totalEndpoints: number;
    testedEndpoints: number;
    passedEndpoints: number;
    failedEndpoints: number;
    passRate: number;
    coverage: EndpointCoverage[];
    reportPath?: string;
    testRunner?: 'newman' | 'pytest' | 'rest-assured' | 'custom';
    environment?: string;
    baseUrl?: string;
}
/**
 * E2E Testing Report with full evidence metadata
 */
export interface E2ETestingReportEvidence extends EvidenceMetadata {
    type: EvidenceType.E2E_TESTING_REPORT;
    report: E2ETestingReport;
}
/**
 * API Documentation Reference evidence
 * Links to Stage 03 OpenAPI spec
 */
export interface APIDocumentationReference {
    openapiPath: string;
    openapiVersion: string;
    totalEndpoints: number;
    endpointsByMethod: Record<string, number>;
    lastUpdated: string;
    specHash?: string;
}
/**
 * API Documentation Reference with full evidence metadata
 */
export interface APIDocumentationReferenceEvidence extends EvidenceMetadata {
    type: EvidenceType.API_DOCUMENTATION_REFERENCE;
    reference: APIDocumentationReference;
}
/**
 * Security Testing Results evidence
 * OWASP/security scan results
 */
export interface SecurityTestingResults {
    scanType: 'owasp' | 'penetration' | 'vulnerability' | 'compliance';
    timestamp: string;
    totalTests: number;
    passedTests: number;
    failedTests: number;
    criticalIssues: number;
    highIssues: number;
    mediumIssues: number;
    lowIssues: number;
    scannerTool?: string;
    reportPath?: string;
}
/**
 * Security Testing Results with full evidence metadata
 */
export interface SecurityTestingResultsEvidence extends EvidenceMetadata {
    type: EvidenceType.SECURITY_TESTING_RESULTS;
    results: SecurityTestingResults;
}
/**
 * Stage Cross-Reference link
 */
export interface CrossReferenceLink {
    sourceStage: string;
    sourcePath: string;
    sourceType: 'openapi' | 'spec' | 'adr' | 'code' | 'test';
    targetStage: string;
    targetPath: string;
    targetType: 'openapi' | 'spec' | 'adr' | 'code' | 'test';
    linkType: 'implements' | 'tests' | 'documents' | 'references';
    valid: boolean;
    validatedAt?: string;
}
/**
 * Stage Cross-Reference evidence
 * Bidirectional links between Stage 03 ↔ Stage 05
 */
export interface StageCrossReference {
    sourceStage: string;
    targetStage: string;
    totalLinks: number;
    validLinks: number;
    brokenLinks: number;
    links: CrossReferenceLink[];
    validationTimestamp: string;
}
/**
 * Stage Cross-Reference with full evidence metadata
 */
export interface StageCrossReferenceEvidence extends EvidenceMetadata {
    type: EvidenceType.STAGE_CROSS_REFERENCE;
    crossReference: StageCrossReference;
}
/**
 * E2E Validation error
 */
export interface E2EValidationError {
    code: string;
    message: string;
    path?: string;
    line?: number;
}
/**
 * E2E Validation warning
 */
export interface E2EValidationWarning {
    code: string;
    message: string;
    path?: string;
}
/**
 * E2E Compliance checklist item
 */
export interface E2EChecklistItem {
    item: string;
    passed: boolean;
    details?: string;
}
/**
 * Complete E2E Validation result
 * Output of sdlc.e2eValidate command
 */
export interface E2EValidationResult {
    valid: boolean;
    passRate: number;
    totalEndpoints: number;
    testedEndpoints: number;
    passedEndpoints: number;
    failedEndpoints: number;
    errors: E2EValidationError[];
    warnings: E2EValidationWarning[];
    checklist: E2EChecklistItem[];
    testResults: E2ETestingReport | null;
    stage05Path?: string;
    openapiPath?: string;
    validationTimestamp: string;
}
/**
 * Cross-reference validation result
 * Output of sdlc.e2eCrossReference command
 */
export interface CrossReferenceValidationResult {
    valid: boolean;
    stage03Path: string;
    stage05Path: string;
    totalEndpoints: number;
    coveredEndpoints: number;
    uncoveredEndpoints: number;
    coveragePercentage: number;
    links: CrossReferenceLink[];
    errors: E2EValidationError[];
    warnings: E2EValidationWarning[];
    validationTimestamp: string;
}
/**
 * E2E Validate request options
 */
export interface E2EValidateRequest {
    projectPath: string;
    minPassRate?: number;
    strict?: boolean;
    init?: boolean;
}
/**
 * E2E Cross-Reference request options
 */
export interface E2ECrossReferenceRequest {
    projectPath: string;
    stage03Path?: string;
    stage05Path?: string;
    strict?: boolean;
    fix?: boolean;
}
/**
 * E2E Report generation request
 */
export interface E2EReportRequest {
    projectPath: string;
    testResultsPath?: string;
    outputPath?: string;
    format?: 'markdown' | 'json' | 'html';
}
/**
 * Cross-reference validation API response
 * From: POST /api/v1/cross-reference/validate
 */
export interface CrossReferenceAPIResponse {
    success: boolean;
    project_id: string;
    stage_03_path: string;
    stage_05_path: string;
    api_endpoints: Array<{
        method: string;
        path: string;
        operation_id?: string;
    }>;
    test_files: Array<{
        path: string;
        endpoints_tested: string[];
    }>;
    coverage: {
        total: number;
        covered: number;
        percentage: number;
    };
    missing_tests: Array<{
        method: string;
        path: string;
    }>;
    validation_timestamp: string;
}
/**
 * E2E execution API response
 * From: POST /api/v1/e2e/execute
 */
export interface E2EExecuteAPIResponse {
    execution_id: string;
    status: 'queued' | 'running' | 'completed' | 'failed';
    message: string;
    started_at?: string;
    completed_at?: string;
    results?: E2ETestingReport;
}
/**
 * E2E results API response
 * From: GET /api/v1/e2e/results/{execution_id}
 */
export interface E2EResultsAPIResponse {
    execution_id: string;
    status: 'queued' | 'running' | 'completed' | 'failed';
    test_results?: E2ETestingReport;
    error_message?: string;
    duration_ms?: number;
}
//# sourceMappingURL=evidence.d.ts.map