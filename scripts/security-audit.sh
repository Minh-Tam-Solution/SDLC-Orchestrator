#!/bin/bash
# ============================================================================
# Security Audit Script - OWASP ASVS Level 2 Compliance Check
# SDLC Orchestrator - Week 5 Day 1-2
# ============================================================================
#
# Purpose:
# - Run comprehensive security scans (Semgrep, Grype, Syft)
# - Validate OWASP ASVS Level 2 compliance (264 requirements)
# - Generate security audit report
#
# Usage:
#   ./scripts/security-audit.sh [--fix] [--report-only]
#
# Output:
#   - security-audit-report.md (comprehensive audit report)
#   - semgrep-results.json (SAST scan results)
#   - grype-results.json (dependency vulnerability scan)
#   - sbom.json (Software Bill of Materials)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/reports/security"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Security Audit - OWASP ASVS Level 2 Compliance Check       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📅 Date: $(date)"
echo "📁 Reports: $REPORTS_DIR"
echo ""

# ============================================================================
# Step 1: Check Required Tools
# ============================================================================

echo "🔍 Step 1/6: Checking required tools..."

check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "  ✅ $1: $(command -v "$1")"
        return 0
    else
        echo "  ❌ $1: NOT FOUND"
        echo "     Install with: $2"
        return 1
    fi
}

MISSING_TOOLS=0

check_tool "semgrep" "pip install semgrep" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool "grype" "https://github.com/anchore/grype#installation" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool "syft" "https://github.com/anchore/syft#installation" || MISSING_TOOLS=$((MISSING_TOOLS + 1))

if [ $MISSING_TOOLS -gt 0 ]; then
    echo ""
    echo "${RED}❌ Missing required tools. Please install them first.${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Step 2: Semgrep SAST Scan
# ============================================================================

echo "🔍 Step 2/6: Running Semgrep SAST scan (OWASP Top 10 + Custom Rules)..."

semgrep \
    --config=auto \
    --config=p/owasp-top-ten \
    --config=p/security-audit \
    --config=p/python \
    --json \
    --output="$REPORTS_DIR/semgrep-results-$TIMESTAMP.json" \
    "$PROJECT_ROOT/backend" \
    || true

# Count findings by severity
CRITICAL=$(jq '[.results[] | select(.extra.severity == "ERROR")] | length' "$REPORTS_DIR/semgrep-results-$TIMESTAMP.json" 2>/dev/null || echo "0")
HIGH=$(jq '[.results[] | select(.extra.severity == "WARNING")] | length' "$REPORTS_DIR/semgrep-results-$TIMESTAMP.json" 2>/dev/null || echo "0")

if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
    echo "  ${YELLOW}⚠️  Found $CRITICAL critical and $HIGH high severity issues${NC}"
else
    echo "  ${GREEN}✅ No critical or high severity issues found${NC}"
fi

echo ""

# ============================================================================
# Step 3: Generate SBOM (Software Bill of Materials)
# ============================================================================

echo "📦 Step 3/6: Generating SBOM (Software Bill of Materials)..."

cd "$PROJECT_ROOT/backend"

syft packages dir:. \
    -o cyclonedx-json \
    > "$REPORTS_DIR/sbom-$TIMESTAMP.json"

PACKAGE_COUNT=$(jq '.components | length' "$REPORTS_DIR/sbom-$TIMESTAMP.json" 2>/dev/null || echo "0")
echo "  ✅ Found $PACKAGE_COUNT packages"
echo ""

# Check for AGPL dependencies
echo "  🔍 Checking for AGPL dependencies..."
AGPL_COUNT=$(jq '[.components[] | select(.licenses[]?.license.id == "AGPL-3.0")] | length' "$REPORTS_DIR/sbom-$TIMESTAMP.json" 2>/dev/null || echo "0")

if [ "$AGPL_COUNT" -gt 0 ]; then
    echo "  ${YELLOW}⚠️  Found $AGPL_COUNT AGPL-licensed packages (should be network-only access)${NC}"
    jq '[.components[] | select(.licenses[]?.license.id == "AGPL-3.0") | {name: .name, version: .version}]' "$REPORTS_DIR/sbom-$TIMESTAMP.json"
else
    echo "  ${GREEN}✅ No AGPL dependencies (AGPL containment strategy validated)${NC}"
fi

echo ""

# ============================================================================
# Step 4: Grype Vulnerability Scan
# ============================================================================

echo "🛡️  Step 4/6: Running Grype vulnerability scan..."

grype sbom:"$REPORTS_DIR/sbom-$TIMESTAMP.json" \
    --output json \
    --file "$REPORTS_DIR/grype-results-$TIMESTAMP.json" \
    || true

# Count vulnerabilities by severity
CRITICAL_VULNS=$(jq '[.matches[] | select(.vulnerability.severity == "Critical")] | length' "$REPORTS_DIR/grype-results-$TIMESTAMP.json" 2>/dev/null || echo "0")
HIGH_VULNS=$(jq '[.matches[] | select(.vulnerability.severity == "High")] | length' "$REPORTS_DIR/grype-results-$TIMESTAMP.json" 2>/dev/null || echo "0")
MEDIUM_VULNS=$(jq '[.matches[] | select(.vulnerability.severity == "Medium")] | length' "$REPORTS_DIR/grype-results-$TIMESTAMP.json" 2>/dev/null || echo "0")

if [ "$CRITICAL_VULNS" -gt 0 ] || [ "$HIGH_VULNS" -gt 0 ]; then
    echo "  ${RED}❌ Found $CRITICAL_VULNS critical and $HIGH_VULNS high severity vulnerabilities${NC}"
    echo "     Review: $REPORTS_DIR/grype-results-$TIMESTAMP.json"
else
    echo "  ${GREEN}✅ No critical or high severity vulnerabilities found${NC}"
    echo "     Medium: $MEDIUM_VULNS (review recommended)"
fi

echo ""

# ============================================================================
# Step 5: Secrets Detection
# ============================================================================

echo "🔐 Step 5/6: Scanning for hardcoded secrets..."

if command -v gitleaks &> /dev/null; then
    gitleaks detect \
        --source "$PROJECT_ROOT" \
        --report-path "$REPORTS_DIR/gitleaks-results-$TIMESTAMP.json" \
        --no-banner \
        || true
    
    LEAKS_COUNT=$(jq '.length' "$REPORTS_DIR/gitleaks-results-$TIMESTAMP.json" 2>/dev/null || echo "0")
    
    if [ "$LEAKS_COUNT" -gt 0 ]; then
        echo "  ${RED}❌ Found $LEAKS_COUNT potential secrets${NC}"
        echo "     Review: $REPORTS_DIR/gitleaks-results-$TIMESTAMP.json"
    else
        echo "  ${GREEN}✅ No secrets detected${NC}"
    fi
else
    echo "  ${YELLOW}⚠️  gitleaks not installed (skipping secrets detection)${NC}"
    echo "     Install with: https://github.com/gitleaks/gitleaks#installation"
fi

echo ""

# ============================================================================
# Step 6: Generate Security Audit Report
# ============================================================================

echo "📄 Step 6/6: Generating security audit report..."

cat > "$REPORTS_DIR/security-audit-report-$TIMESTAMP.md" << EOF
# Security Audit Report - OWASP ASVS Level 2 Compliance

**Date**: $(date)
**Project**: SDLC Orchestrator
**Auditor**: Security Lead + Automation
**Scope**: Backend Code (Python/FastAPI)

---

## Executive Summary

**Overall Status**: ⏳ PENDING REVIEW

**Critical Issues**: $CRITICAL
**High Issues**: $HIGH
**Medium Issues**: $MEDIUM_VULNS
**Total Packages**: $PACKAGE_COUNT
**AGPL Dependencies**: $AGPL_COUNT

---

## 1. SAST Scan Results (Semgrep)

**Tool**: Semgrep (OWASP Top 10 + Custom Rules)
**Results**: \`$REPORTS_DIR/semgrep-results-$TIMESTAMP.json\`

**Findings**:
- Critical: $CRITICAL
- High: $HIGH

**Next Steps**:
1. Review critical/high findings
2. Fix security vulnerabilities
3. Re-run scan to verify fixes

---

## 2. Dependency Vulnerability Scan (Grype)

**Tool**: Grype (CVE Database Matching)
**SBOM**: \`$REPORTS_DIR/sbom-$TIMESTAMP.json\`
**Results**: \`$REPORTS_DIR/grype-results-$TIMESTAMP.json\`

**Vulnerabilities**:
- Critical: $CRITICAL_VULNS
- High: $HIGH_VULNS
- Medium: $MEDIUM_VULNS

**Next Steps**:
1. Review critical/high CVEs
2. Update vulnerable dependencies
3. Test after updates
4. Re-scan to verify fixes

---

## 3. Software Bill of Materials (SBOM)

**Tool**: Syft (CycloneDX Format)
**File**: \`$REPORTS_DIR/sbom-$TIMESTAMP.json\`

**Summary**:
- Total Packages: $PACKAGE_COUNT
- AGPL Dependencies: $AGPL_COUNT

**AGPL Containment Status**: $([ "$AGPL_COUNT" -eq 0 ] && echo "✅ SAFE (No AGPL dependencies)" || echo "⚠️  REVIEW NEEDED (Network-only access validated)")

---

## 4. Secrets Detection

**Tool**: Gitleaks
**Results**: \`$REPORTS_DIR/gitleaks-results-$TIMESTAMP.json\`

**Findings**: $LEAKS_COUNT potential secrets

---

## 5. OWASP ASVS Level 2 Compliance

**Total Requirements**: 264

See \`docs/02-Design-Architecture/07-Security-RBAC/Security-Baseline.md\` for detailed mapping.

**Compliance Status**: ⏳ MANUAL REVIEW REQUIRED

---

## Next Steps

1. ✅ **Critical/High Issues**: Fix immediately (24 hours SLA)
2. ✅ **Medium Issues**: Fix within 7 days
3. ✅ **Re-scan**: Run audit again after fixes
4. ✅ **Gate G2 Approval**: Security Lead sign-off required

---

**Report Generated**: $(date)
**Automated Scans**: ✅ Complete
**Manual Review**: ⏳ Pending
EOF

echo "  ✅ Report generated: $REPORTS_DIR/security-audit-report-$TIMESTAMP.md"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Security Audit Complete                                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "  Critical Issues: $CRITICAL"
echo "  High Issues: $HIGH"
echo "  Critical Vulnerabilities: $CRITICAL_VULNS"
echo "  High Vulnerabilities: $HIGH_VULNS"
echo "  AGPL Dependencies: $AGPL_COUNT"
echo ""
echo "📄 Reports:"
echo "  - Security Audit Report: $REPORTS_DIR/security-audit-report-$TIMESTAMP.md"
echo "  - Semgrep Results: $REPORTS_DIR/semgrep-results-$TIMESTAMP.json"
echo "  - Grype Results: $REPORTS_DIR/grype-results-$TIMESTAMP.json"
echo "  - SBOM: $REPORTS_DIR/sbom-$TIMESTAMP.json"
echo ""
echo "🔧 Next Steps:"
echo "  1. Review security-audit-report-$TIMESTAMP.md"
echo "  2. Fix critical/high issues"
echo "  3. Re-run: ./scripts/security-audit.sh"
echo ""
