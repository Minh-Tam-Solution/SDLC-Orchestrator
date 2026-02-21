#!/usr/bin/env bash
# =============================================================================
# Sprint 190 Pre-Deletion Dependency Audit Script
# SDLC Orchestrator — Conversation-First Cleanup
#
# Purpose: Validate that all files scheduled for deletion have ZERO active
#          imports from surviving code. Run BEFORE any deletions.
#
# Usage:   bash scripts/sprint190_audit_deps.sh
# Exit:    0 = safe to proceed, 1 = blockers found
#
# Authority: Expert Panel (9/9 APPROVE), CEO APPROVED (Feb 21, 2026)
# Reference: SPRINT-190-AGGRESSIVE-CLEANUP.md, ADR-064
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_DIR="backend/app"
BLOCKERS=0
WARNINGS=0

echo "============================================="
echo " Sprint 190 — Pre-Deletion Dependency Audit"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================="
echo ""

# -----------------------------------------------
# Tier 1: Service files scheduled for deletion
# -----------------------------------------------
TIER1_SERVICES=(
    "nist_govern_service"
    "nist_manage_service"
    "nist_map_service"
    "nist_measure_service"
    "ai_council_service"
    "feedback_learning_service"
    "sop_generator_service"
    "pilot_tracking_service"
    "analytics_service"
)

# Tier 1 directories scheduled for deletion
TIER1_DIRS=(
    "spec_converter"
)

# Context Authority v1 (separate — v2 must survive)
TIER1_V1_MODULES=(
    "context_authority"
)

# -----------------------------------------------
# Tier 2: Route files scheduled for deletion
# -----------------------------------------------
TIER2_ROUTES=(
    "nist_govern"
    "nist_manage"
    "nist_map"
    "nist_measure"
    "council"
    "feedback"
    "learnings"
    "sop"
    "pilot"
    "spec_converter"
    "dogfooding"
)

# -----------------------------------------------
# Collateral: Jobs that import deleted services
# -----------------------------------------------
COLLATERAL_JOBS=(
    "learning_aggregation"
)

# -----------------------------------------------
# SASE BLOCKER: Must NOT be in deletion list
# -----------------------------------------------
SASE_PROTECTED=(
    "sase_generation_service"
    "sase_sprint_integration"
)

echo "=== TIER 1: Service File Import Audit ==="
echo ""

for module in "${TIER1_SERVICES[@]}"; do
    echo -n "  Checking imports of '${module}'... "
    # Search for imports, excluding the file itself and test files
    hits=$(grep -rn "import.*${module}\|from.*${module}" "${BACKEND_DIR}/" \
        --include="*.py" \
        | grep -v "/${module}.py:" \
        | grep -v "/test_" \
        | grep -v "__pycache__" \
        | grep -v "alembic/versions/" \
        || true)

    if [ -z "$hits" ]; then
        echo -e "${GREEN}CLEAN${NC}"
    else
        echo -e "${RED}BLOCKER${NC}"
        echo "$hits" | while IFS= read -r line; do
            echo "    → $line"
        done
        BLOCKERS=$((BLOCKERS + 1))
    fi
done

echo ""
echo "=== TIER 1: Directory Import Audit ==="
echo ""

for dir in "${TIER1_DIRS[@]}"; do
    echo -n "  Checking imports of '${dir}'... "
    hits=$(grep -rn "import.*${dir}\|from.*${dir}" "${BACKEND_DIR}/" \
        --include="*.py" \
        | grep -v "/${dir}/" \
        | grep -v "/test_" \
        | grep -v "__pycache__" \
        | grep -v "alembic/versions/" \
        || true)

    if [ -z "$hits" ]; then
        echo -e "${GREEN}CLEAN${NC}"
    else
        echo -e "${RED}BLOCKER${NC}"
        echo "$hits" | while IFS= read -r line; do
            echo "    → $line"
        done
        BLOCKERS=$((BLOCKERS + 1))
    fi
done

echo ""
echo "=== TIER 1: V1 Module Audit (v2 must survive) ==="
echo ""

for module in "${TIER1_V1_MODULES[@]}"; do
    echo -n "  Checking imports of '${module}' (excluding v2)... "
    # Look for imports of context_authority that are NOT context_authority_v2
    hits=$(grep -rn "import.*${module}\|from.*${module}" "${BACKEND_DIR}/" \
        --include="*.py" \
        | grep -v "${module}_v2" \
        | grep -v "/${module}.py:" \
        | grep -v "/test_" \
        | grep -v "__pycache__" \
        | grep -v "alembic/versions/" \
        | grep -v "analytics_v2" \
        || true)

    if [ -z "$hits" ]; then
        echo -e "${GREEN}CLEAN${NC}"
    else
        echo -e "${YELLOW}WARNING — verify these are v1 references${NC}"
        echo "$hits" | while IFS= read -r line; do
            echo "    → $line"
        done
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "=== TIER 2: Route File Import Audit ==="
echo ""

for route in "${TIER2_ROUTES[@]}"; do
    echo -n "  Checking imports of route '${route}'... "
    hits=$(grep -rn "import.*routes\.${route}\|from.*routes.*import.*${route}" "${BACKEND_DIR}/" \
        --include="*.py" \
        | grep -v "/routes/${route}.py:" \
        | grep -v "/test_" \
        | grep -v "__pycache__" \
        | grep -v "main.py:" \
        || true)

    if [ -z "$hits" ]; then
        echo -e "${GREEN}CLEAN (only main.py)${NC}"
    else
        echo -e "${RED}BLOCKER — imported outside main.py${NC}"
        echo "$hits" | while IFS= read -r line; do
            echo "    → $line"
        done
        BLOCKERS=$((BLOCKERS + 1))
    fi
done

echo ""
echo "=== COLLATERAL: Jobs Import Audit ==="
echo ""

for job in "${COLLATERAL_JOBS[@]}"; do
    echo -n "  Checking imports of job '${job}'... "
    hits=$(grep -rn "import.*${job}\|from.*${job}" "${BACKEND_DIR}/" \
        --include="*.py" \
        | grep -v "/${job}.py:" \
        | grep -v "/test_" \
        | grep -v "__pycache__" \
        || true)

    if [ -z "$hits" ]; then
        echo -e "${GREEN}CLEAN${NC}"
    else
        echo -e "${YELLOW}WARNING — verify no active caller${NC}"
        echo "$hits" | while IFS= read -r line; do
            echo "    → $line"
        done
        WARNINGS=$((WARNINGS + 1))
    fi
done

echo ""
echo "=== SASE PROTECTION CHECK ==="
echo ""

for protected in "${SASE_PROTECTED[@]}"; do
    echo -n "  Checking active imports of '${protected}'... "
    hits=$(grep -rn "import.*${protected}\|from.*${protected}" "${BACKEND_DIR}/" \
        --include="*.py" \
        | grep -v "/${protected}.py:" \
        | grep -v "/test_" \
        | grep -v "__pycache__" \
        || true)

    if [ -z "$hits" ]; then
        echo -e "${GREEN}No active imports — SAFE to delete (but verify)${NC}"
    else
        echo -e "${RED}ACTIVE IMPORTS — DO NOT DELETE (deferred to Sprint 191+)${NC}"
        echo "$hits" | while IFS= read -r line; do
            echo "    → $line"
        done
    fi
done

echo ""
echo "=== ROUTER REGISTRATION CHECK (main.py) ==="
echo ""

echo "  Routers scheduled for removal from main.py:"
ROUTERS_TO_REMOVE=(
    "nist_govern.router"
    "nist_manage.router"
    "nist_map.router"
    "nist_measure.router"
    "council.router"
    "feedback.router"
    "learnings.router"
    "sop.router"
    "pilot.router"
    "spec_converter.router"
    "analytics.router"
    "context_authority.router"
    "dogfooding.router"
)

for router in "${ROUTERS_TO_REMOVE[@]}"; do
    echo -n "    ${router}... "
    if grep -q "${router}" "${BACKEND_DIR}/main.py" 2>/dev/null; then
        echo -e "${YELLOW}FOUND — will be removed${NC}"
    else
        echo -e "${GREEN}ALREADY REMOVED${NC}"
    fi
done

echo ""
echo "  Routers that MUST survive:"
ROUTERS_TO_KEEP=(
    "analytics_v2.router"
    "context_authority_v2.router"
    "agent_team.router"
    "ott_gateway.router"
    "enterprise_sso.router"
    "jira_integration.router"
    "audit_trail.router"
    "data_residency.router"
    "gdpr.router"
)

for router in "${ROUTERS_TO_KEEP[@]}"; do
    echo -n "    ${router}... "
    if grep -q "${router}" "${BACKEND_DIR}/main.py" 2>/dev/null; then
        echo -e "${GREEN}PRESENT${NC}"
    else
        echo -e "${RED}MISSING — CRITICAL${NC}"
        BLOCKERS=$((BLOCKERS + 1))
    fi
done

echo ""
echo "============================================="
echo " AUDIT SUMMARY"
echo "============================================="
echo ""
echo -e "  Blockers: ${RED}${BLOCKERS}${NC}"
echo -e "  Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ "$BLOCKERS" -gt 0 ]; then
    echo -e "${RED}RESULT: BLOCKED — Fix ${BLOCKERS} blocker(s) before proceeding with deletions${NC}"
    echo ""
    echo "  Action: Investigate each BLOCKER above. Either:"
    echo "  1. Remove the import from the surviving file, OR"
    echo "  2. Defer the deletion to Sprint 191+"
    exit 1
else
    echo -e "${GREEN}RESULT: SAFE TO PROCEED — All deletion targets have clean imports${NC}"
    if [ "$WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}  (${WARNINGS} warning(s) — verify manually before deletion)${NC}"
    fi
    exit 0
fi
