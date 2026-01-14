#!/bin/bash
# =============================================================================
# BE-W6-005: Smoke Test All 8 SOP Endpoints
# SASE Phase 2-Pilot - Week 6 Iteration 1
# Date: January 2026
# =============================================================================

# Note: Don't use set -e as we want to continue on failures
# set -e

BASE_URL="${BASE_URL:-http://localhost:8300}"
API_PREFIX="/api/v1/sop"

echo "============================================================"
echo "BE-W6-005: SOP Generator Smoke Test"
echo "Base URL: $BASE_URL"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Function to run test
run_test() {
    local test_num=$1
    local name=$2
    local method=$3
    local endpoint=$4
    local data=$5
    local expected_code=$6

    echo -n "[$test_num/8] $name... "

    start_time=$(date +%s%N)

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi

    end_time=$(date +%s%N)
    elapsed=$(( (end_time - start_time) / 1000000 ))

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}PASS${NC} (${elapsed}ms, HTTP $http_code)"
        ((PASS_COUNT++))
        echo "$body" | head -c 200
        echo ""
    else
        echo -e "${RED}FAIL${NC} (${elapsed}ms, HTTP $http_code, expected $expected_code)"
        ((FAIL_COUNT++))
        echo "$body" | head -c 300
        echo ""
    fi
    echo ""
}

# =============================================================================
# Test 1: GET /api/sop/types
# =============================================================================
run_test 1 "GET /api/sop/types (list 5 SOP types)" "GET" "$API_PREFIX/types" "" "200"

# =============================================================================
# Test 2: GET /api/sop/health
# =============================================================================
run_test 2 "GET /api/sop/health (service health)" "GET" "$API_PREFIX/health" "" "200"

# =============================================================================
# Test 3: POST /api/sop/generate (create SOP)
# =============================================================================
echo "[3/8] POST /api/sop/generate (generate SOP)..."
echo "      This may take 15-30 seconds..."

start_time=$(date +%s%N)
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$API_PREFIX/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "sop_type": "deployment",
        "workflow_description": "Deploy FastAPI application to Kubernetes cluster with zero-downtime. Include health checks, database migrations, and rollback procedure if deployment fails."
    }' \
    --max-time 35 2>/dev/null)
end_time=$(date +%s%N)
elapsed=$(( (end_time - start_time) / 1000000 ))

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "201" ]; then
    echo -e "      ${GREEN}PASS${NC} (${elapsed}ms, HTTP $http_code)"
    ((PASS_COUNT++))

    # Extract sop_id and mrp_id for subsequent tests
    SOP_ID=$(echo "$body" | grep -o '"sop_id":"[^"]*"' | cut -d'"' -f4)
    MRP_ID=$(echo "$body" | grep -o '"mrp_id":"[^"]*"' | cut -d'"' -f4)
    GEN_TIME=$(echo "$body" | grep -o '"generation_time_ms":[0-9.]*' | cut -d':' -f2)

    echo "      sop_id: $SOP_ID"
    echo "      mrp_id: $MRP_ID"
    echo "      generation_time_ms: $GEN_TIME"

    # Check if under 30s target
    if [ ! -z "$GEN_TIME" ]; then
        gen_int=${GEN_TIME%.*}
        if [ "$gen_int" -lt 30000 ]; then
            echo -e "      ${GREEN}✓ Under 30s target${NC}"
        else
            echo -e "      ${YELLOW}⚠ Over 30s target${NC}"
        fi
    fi
else
    echo -e "      ${RED}FAIL${NC} (${elapsed}ms, HTTP $http_code)"
    ((FAIL_COUNT++))
    echo "$body" | head -c 300
    SOP_ID=""
    MRP_ID=""
fi
echo ""

# If generate failed, skip dependent tests
if [ -z "$SOP_ID" ]; then
    echo -e "${YELLOW}⚠ Skipping tests 4-7 (no SOP_ID from generate)${NC}"
    echo ""
    FAIL_COUNT=$((FAIL_COUNT + 4))
else
    # =============================================================================
    # Test 4: GET /api/sop/{sop_id}
    # =============================================================================
    run_test 4 "GET /api/sop/$SOP_ID (get SOP details)" "GET" "$API_PREFIX/$SOP_ID" "" "200"

    # =============================================================================
    # Test 5: GET /api/sop/{sop_id}/mrp
    # =============================================================================
    run_test 5 "GET /api/sop/$SOP_ID/mrp (get MRP evidence)" "GET" "$API_PREFIX/$SOP_ID/mrp" "" "200"

    # =============================================================================
    # Test 6: POST /api/sop/{sop_id}/vcr (submit VCR)
    # =============================================================================
    echo "[6/8] POST /api/sop/$SOP_ID/vcr (submit VCR)..."

    start_time=$(date +%s%N)
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$API_PREFIX/$SOP_ID/vcr" \
        -H "Content-Type: application/json" \
        -d '{
            "decision": "approved",
            "reviewer": "Tech Lead",
            "comments": "SOP meets all quality criteria",
            "quality_rating": 5
        }' 2>/dev/null)
    end_time=$(date +%s%N)
    elapsed=$(( (end_time - start_time) / 1000000 ))

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "201" ]; then
        echo -e "      ${GREEN}PASS${NC} (${elapsed}ms, HTTP $http_code)"
        ((PASS_COUNT++))
        VCR_ID=$(echo "$body" | grep -o '"vcr_id":"[^"]*"' | cut -d'"' -f4)
        echo "      vcr_id: $VCR_ID"
    else
        echo -e "      ${RED}FAIL${NC} (${elapsed}ms, HTTP $http_code)"
        ((FAIL_COUNT++))
        echo "$body" | head -c 200
    fi
    echo ""

    # =============================================================================
    # Test 7: GET /api/sop/{sop_id}/vcr (get VCR status)
    # =============================================================================
    run_test 7 "GET /api/sop/$SOP_ID/vcr (get VCR status)" "GET" "$API_PREFIX/$SOP_ID/vcr" "" "200"
fi

# =============================================================================
# Test 8: GET /api/sop/list
# =============================================================================
run_test 8 "GET /api/sop/list (list SOPs)" "GET" "$API_PREFIX/list" "" "200"

# =============================================================================
# Summary
# =============================================================================
echo "============================================================"
echo "SMOKE TEST SUMMARY"
echo "============================================================"
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}/8"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}/8"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
