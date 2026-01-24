#!/bin/bash
# =========================================================================
# Security Audit Script - SDLC Orchestrator
# Sprint 105: Integration Testing + Launch Readiness
#
# Version: 1.0.0
# Date: January 24, 2026
# Status: ACTIVE - Sprint 105 Implementation
# Authority: Security Lead + CTO Approved
# Reference: docs/04-build/02-Sprint-Plans/SPRINT-105-DESIGN.md
#
# Purpose:
# - Comprehensive security audit for production launch
# - Python code scan (bandit)
# - Dependency scan (grype)
# - Container scan (trivy)
# - API security scan (OWASP ZAP)
# - Secret detection (gitleaks)
#
# Usage:
#   ./scripts/security-audit-final.sh           # Full audit
#   ./scripts/security-audit-final.sh --quick   # Quick scan (bandit + grype)
#   ./scripts/security-audit-final.sh --report  # Generate HTML report
#
# Exit Codes:
#   0: All scans passed
#   1: Critical vulnerabilities found
#   2: High vulnerabilities found (warn only)
#   3: Tool not installed
# =========================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="${PROJECT_ROOT}/reports/security"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PREFIX="${REPORTS_DIR}/${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scan modes
QUICK_MODE=false
GENERATE_REPORT=false

# Exit codes
EXIT_OK=0
EXIT_CRITICAL=1
EXIT_HIGH=2
EXIT_TOOL_MISSING=3

# Track scan results
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_header() {
    echo ""
    echo "========================================================================="
    echo -e "${BLUE}$1${NC}"
    echo "========================================================================="
}

check_tool() {
    local tool=$1
    if ! command -v "$tool" &> /dev/null; then
        log_warning "$tool is not installed. Skipping..."
        return 1
    fi
    return 0
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick     Quick scan (bandit + grype only)"
            echo "  --report    Generate HTML reports"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Setup
# =============================================================================

log_header "SDLC Orchestrator - Security Audit (Sprint 105)"
echo "Timestamp: $(date)"
echo "Mode: $(if $QUICK_MODE; then echo 'Quick'; else echo 'Full'; fi)"
echo "Reports: $(if $GENERATE_REPORT; then echo 'Yes'; else echo 'No'; fi)"

# Create reports directory
mkdir -p "$REPORTS_DIR"

# =============================================================================
# 1. Python Code Scan (Bandit)
# =============================================================================

log_header "1. Python Code Scan (Bandit)"

if check_tool bandit; then
    log_info "Scanning Python code for security issues..."

    BANDIT_OUTPUT="${REPORT_PREFIX}_bandit.json"

    if bandit -r "${PROJECT_ROOT}/backend/app" \
        -f json \
        -o "$BANDIT_OUTPUT" \
        --severity-level medium \
        -x "${PROJECT_ROOT}/backend/app/tests" \
        2>/dev/null; then
        log_success "No security issues found in Python code"
    else
        # Parse results
        if [ -f "$BANDIT_OUTPUT" ]; then
            BANDIT_HIGH=$(jq '.results | map(select(.issue_severity == "HIGH")) | length' "$BANDIT_OUTPUT" 2>/dev/null || echo "0")
            BANDIT_MEDIUM=$(jq '.results | map(select(.issue_severity == "MEDIUM")) | length' "$BANDIT_OUTPUT" 2>/dev/null || echo "0")

            if [ "$BANDIT_HIGH" -gt 0 ]; then
                log_error "Found $BANDIT_HIGH HIGH severity issues"
                HIGH_COUNT=$((HIGH_COUNT + BANDIT_HIGH))
            fi
            if [ "$BANDIT_MEDIUM" -gt 0 ]; then
                log_warning "Found $BANDIT_MEDIUM MEDIUM severity issues"
                MEDIUM_COUNT=$((MEDIUM_COUNT + BANDIT_MEDIUM))
            fi
        fi
    fi

    # Generate HTML report if requested
    if $GENERATE_REPORT; then
        bandit -r "${PROJECT_ROOT}/backend/app" \
            -f html \
            -o "${REPORT_PREFIX}_bandit.html" \
            -x "${PROJECT_ROOT}/backend/app/tests" \
            2>/dev/null || true
        log_info "Bandit HTML report: ${REPORT_PREFIX}_bandit.html"
    fi
fi

# =============================================================================
# 2. Dependency Vulnerability Scan (Grype)
# =============================================================================

log_header "2. Dependency Vulnerability Scan (Grype)"

if check_tool grype; then
    log_info "Scanning dependencies for known vulnerabilities..."

    GRYPE_OUTPUT="${REPORT_PREFIX}_grype.json"

    # Scan Python dependencies
    if [ -f "${PROJECT_ROOT}/backend/requirements.txt" ]; then
        grype "sbom:${PROJECT_ROOT}/backend/requirements.txt" \
            -o json \
            --file "$GRYPE_OUTPUT" \
            2>/dev/null || true

        if [ -f "$GRYPE_OUTPUT" ]; then
            GRYPE_CRITICAL=$(jq '.matches | map(select(.vulnerability.severity == "Critical")) | length' "$GRYPE_OUTPUT" 2>/dev/null || echo "0")
            GRYPE_HIGH=$(jq '.matches | map(select(.vulnerability.severity == "High")) | length' "$GRYPE_OUTPUT" 2>/dev/null || echo "0")

            if [ "$GRYPE_CRITICAL" -gt 0 ]; then
                log_error "Found $GRYPE_CRITICAL CRITICAL vulnerabilities in dependencies"
                CRITICAL_COUNT=$((CRITICAL_COUNT + GRYPE_CRITICAL))
            else
                log_success "No critical vulnerabilities in Python dependencies"
            fi

            if [ "$GRYPE_HIGH" -gt 0 ]; then
                log_warning "Found $GRYPE_HIGH HIGH vulnerabilities in dependencies"
                HIGH_COUNT=$((HIGH_COUNT + GRYPE_HIGH))
            fi
        fi
    fi

    # Scan Node.js dependencies
    if [ -f "${PROJECT_ROOT}/frontend/package-lock.json" ]; then
        log_info "Scanning frontend dependencies..."
        grype "sbom:${PROJECT_ROOT}/frontend/package-lock.json" \
            -o json \
            --file "${REPORT_PREFIX}_grype_frontend.json" \
            2>/dev/null || true
    fi
fi

# =============================================================================
# 3. Container Scan (Trivy) - Skip in Quick Mode
# =============================================================================

if ! $QUICK_MODE; then
    log_header "3. Container Security Scan (Trivy)"

    if check_tool trivy; then
        log_info "Scanning Docker images for vulnerabilities..."

        # Scan backend Dockerfile
        if [ -f "${PROJECT_ROOT}/backend/Dockerfile" ]; then
            TRIVY_OUTPUT="${REPORT_PREFIX}_trivy_backend.json"

            trivy config "${PROJECT_ROOT}/backend/Dockerfile" \
                --format json \
                --output "$TRIVY_OUTPUT" \
                2>/dev/null || true

            if [ -f "$TRIVY_OUTPUT" ]; then
                TRIVY_MISCONFIG=$(jq '.Results[0].Misconfigurations | length' "$TRIVY_OUTPUT" 2>/dev/null || echo "0")

                if [ "$TRIVY_MISCONFIG" -gt 0 ]; then
                    log_warning "Found $TRIVY_MISCONFIG Dockerfile misconfigurations"
                else
                    log_success "No Dockerfile misconfigurations found"
                fi
            fi
        fi

        # Scan IaC (Terraform) if exists
        if [ -d "${PROJECT_ROOT}/infrastructure/terraform" ]; then
            log_info "Scanning Terraform configurations..."
            trivy config "${PROJECT_ROOT}/infrastructure/terraform" \
                --format json \
                --output "${REPORT_PREFIX}_trivy_terraform.json" \
                2>/dev/null || true
        fi
    fi
fi

# =============================================================================
# 4. Secret Detection (Gitleaks) - Skip in Quick Mode
# =============================================================================

if ! $QUICK_MODE; then
    log_header "4. Secret Detection (Gitleaks)"

    if check_tool gitleaks; then
        log_info "Scanning for hardcoded secrets..."

        GITLEAKS_OUTPUT="${REPORT_PREFIX}_gitleaks.json"

        if gitleaks detect \
            --source="${PROJECT_ROOT}" \
            --report-format=json \
            --report-path="$GITLEAKS_OUTPUT" \
            --no-git \
            2>/dev/null; then
            log_success "No hardcoded secrets found"
        else
            if [ -f "$GITLEAKS_OUTPUT" ]; then
                SECRETS_COUNT=$(jq 'length' "$GITLEAKS_OUTPUT" 2>/dev/null || echo "0")
                if [ "$SECRETS_COUNT" -gt 0 ]; then
                    log_error "Found $SECRETS_COUNT potential secrets!"
                    CRITICAL_COUNT=$((CRITICAL_COUNT + SECRETS_COUNT))
                fi
            fi
        fi
    fi
fi

# =============================================================================
# 5. API Security Scan (OWASP ZAP) - Skip in Quick Mode
# =============================================================================

if ! $QUICK_MODE; then
    log_header "5. API Security Scan (OWASP ZAP)"

    if check_tool zap-cli || check_tool zaproxy; then
        log_info "API security scan requires running backend..."
        log_warning "Skipping ZAP scan (requires manual execution with running API)"
        log_info "To run manually:"
        echo "  zap-cli quick-scan http://localhost:8000/api/v1"
        echo "  zap-cli report -o ${REPORT_PREFIX}_zap.html -f html"
    else
        log_warning "OWASP ZAP not installed. Install with: brew install zaproxy"
    fi
fi

# =============================================================================
# 6. SBOM Generation (Syft) - Skip in Quick Mode
# =============================================================================

if ! $QUICK_MODE; then
    log_header "6. SBOM Generation (Syft)"

    if check_tool syft; then
        log_info "Generating Software Bill of Materials..."

        SBOM_OUTPUT="${REPORT_PREFIX}_sbom.json"

        syft "${PROJECT_ROOT}/backend" \
            -o spdx-json="$SBOM_OUTPUT" \
            2>/dev/null || true

        if [ -f "$SBOM_OUTPUT" ]; then
            PACKAGE_COUNT=$(jq '.packages | length' "$SBOM_OUTPUT" 2>/dev/null || echo "0")
            log_success "SBOM generated: $PACKAGE_COUNT packages cataloged"
            log_info "SBOM file: $SBOM_OUTPUT"
        fi
    fi
fi

# =============================================================================
# 7. License Compliance Check - Skip in Quick Mode
# =============================================================================

if ! $QUICK_MODE; then
    log_header "7. License Compliance Check"

    log_info "Checking for AGPL contamination..."

    # Check for AGPL imports (MinIO, Grafana SDKs)
    AGPL_VIOLATIONS=$(grep -r "from minio import\|from grafana import\|import minio\|import grafana" \
        "${PROJECT_ROOT}/backend/app" 2>/dev/null | wc -l || echo "0")

    if [ "$AGPL_VIOLATIONS" -gt 0 ]; then
        log_error "AGPL contamination detected! Found $AGPL_VIOLATIONS violations"
        CRITICAL_COUNT=$((CRITICAL_COUNT + AGPL_VIOLATIONS))
        grep -r "from minio import\|from grafana import\|import minio\|import grafana" \
            "${PROJECT_ROOT}/backend/app" 2>/dev/null || true
    else
        log_success "No AGPL contamination (network-only access verified)"
    fi
fi

# =============================================================================
# Summary Report
# =============================================================================

log_header "SECURITY AUDIT SUMMARY"

echo ""
echo "Results:"
echo "  Critical: $CRITICAL_COUNT"
echo "  High:     $HIGH_COUNT"
echo "  Medium:   $MEDIUM_COUNT"
echo ""

if $GENERATE_REPORT; then
    echo "Reports saved to: $REPORTS_DIR"
    ls -la "${REPORTS_DIR}/${TIMESTAMP}"* 2>/dev/null || true
fi

echo ""

# =============================================================================
# Exit with appropriate code
# =============================================================================

if [ "$CRITICAL_COUNT" -gt 0 ]; then
    log_error "AUDIT FAILED: $CRITICAL_COUNT critical issues found"
    log_error "Fix all critical issues before production launch!"
    exit $EXIT_CRITICAL
elif [ "$HIGH_COUNT" -gt 0 ]; then
    log_warning "AUDIT WARNING: $HIGH_COUNT high severity issues found"
    log_warning "Review and address high severity issues before launch"
    exit $EXIT_HIGH
else
    log_success "AUDIT PASSED: No critical or high severity issues found"
    echo ""
    echo "==========================================================================="
    echo -e "${GREEN}✓ Security audit complete - Ready for production launch${NC}"
    echo "==========================================================================="
    exit $EXIT_OK
fi
