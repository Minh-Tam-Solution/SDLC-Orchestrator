#!/bin/bash
###############################################################################
# AI Council Test Runner Script
# Sprint 26 Day 4 - Tests + Performance
#
# Purpose:
#   Automated test execution for AI Council Service
#   - Unit tests (95%+ coverage target)
#   - Integration tests (API endpoints)
#   - Performance benchmarks (<3s single, <8s council)
#
# Usage:
#   ./scripts/run_council_tests.sh [unit|integration|performance|all]
#
# Examples:
#   ./scripts/run_council_tests.sh unit          # Run unit tests only
#   ./scripts/run_council_tests.sh performance   # Run performance benchmarks
#   ./scripts/run_council_tests.sh all           # Run all tests
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test mode (default: all)
MODE=${1:-all}

echo -e "${BLUE}=========================================================================${NC}"
echo -e "${BLUE}AI Council Service - Test Suite${NC}"
echo -e "${BLUE}Sprint 26 Day 4 - Tests + Performance${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
fi

# Check if dependencies are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing test dependencies...${NC}"
    pip install -r requirements.txt
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"

# Check if Docker services are running
echo -e "${BLUE}🐳 Checking Docker services...${NC}"
if ! docker compose ps | grep -q "postgres.*Up"; then
    echo -e "${YELLOW}⚠️  PostgreSQL not running. Starting Docker services...${NC}"
    docker compose up -d postgres redis
    sleep 5
    echo -e "${GREEN}✅ Docker services started${NC}"
else
    echo -e "${GREEN}✅ Docker services running${NC}"
fi

echo ""

# Function to run unit tests
run_unit_tests() {
    echo -e "${BLUE}=========================================================================${NC}"
    echo -e "${BLUE}🧪 Running Unit Tests${NC}"
    echo -e "${BLUE}=========================================================================${NC}"
    echo ""

    pytest tests/unit/test_ai_council_service.py \
        -v \
        --tb=short \
        --cov=app/services/ai_council_service \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/council_unit \
        --cov-fail-under=95 \
        -m "unit or not (integration or performance)" \
        || {
            echo -e "${RED}❌ Unit tests failed${NC}"
            return 1
        }

    echo ""
    echo -e "${GREEN}✅ Unit tests passed${NC}"
    echo -e "${YELLOW}📊 Coverage report: htmlcov/council_unit/index.html${NC}"
    return 0
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${BLUE}=========================================================================${NC}"
    echo -e "${BLUE}🔗 Running Integration Tests${NC}"
    echo -e "${BLUE}=========================================================================${NC}"
    echo ""

    pytest tests/integration/test_council_api.py \
        -v \
        --tb=short \
        --cov=app/api/routes/council \
        --cov-report=term-missing \
        --cov-report=html:htmlcov/council_integration \
        -m "integration or not (unit or performance)" \
        || {
            echo -e "${RED}❌ Integration tests failed${NC}"
            return 1
        }

    echo ""
    echo -e "${GREEN}✅ Integration tests passed${NC}"
    echo -e "${YELLOW}📊 Coverage report: htmlcov/council_integration/index.html${NC}"
    return 0
}

# Function to run performance tests
run_performance_tests() {
    echo -e "${BLUE}=========================================================================${NC}"
    echo -e "${BLUE}⚡ Running Performance Benchmarks${NC}"
    echo -e "${BLUE}=========================================================================${NC}"
    echo ""
    echo -e "${YELLOW}Performance Targets:${NC}"
    echo -e "  - Single mode:  <3s p95 latency"
    echo -e "  - Council mode: <8s p95 latency"
    echo -e "  - Success rate: >95%"
    echo -e "  - Throughput:   >3 req/s"
    echo ""

    pytest tests/performance/test_council_benchmarks.py \
        -v \
        --tb=short \
        -m performance \
        || {
            echo -e "${RED}❌ Performance tests failed${NC}"
            return 1
        }

    echo ""
    echo -e "${GREEN}✅ Performance tests passed${NC}"
    return 0
}

# Function to run all tests
run_all_tests() {
    local failed=0

    run_unit_tests || failed=1
    echo ""

    run_integration_tests || failed=1
    echo ""

    run_performance_tests || failed=1
    echo ""

    if [ $failed -eq 0 ]; then
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${GREEN}Sprint 26 Day 4: Tests + Performance - COMPLETE${NC}"
        echo ""
        echo -e "${YELLOW}Summary:${NC}"
        echo -e "  ✅ Unit tests (95%+ coverage)"
        echo -e "  ✅ Integration tests (API endpoints)"
        echo -e "  ✅ Performance benchmarks (targets met)"
        echo ""
        echo -e "${YELLOW}Next Steps:${NC}"
        echo -e "  1. Review coverage reports in htmlcov/"
        echo -e "  2. Document performance results"
        echo -e "  3. Proceed to Sprint 26 Day 5 (Documentation + CTO Sign-off)"
        echo -e "${BLUE}=========================================================================${NC}"
        return 0
    else
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${YELLOW}Check test output above for details${NC}"
        return 1
    fi
}

# Execute based on mode
case "$MODE" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    performance)
        run_performance_tests
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo -e "${RED}❌ Invalid mode: $MODE${NC}"
        echo -e "${YELLOW}Usage: $0 [unit|integration|performance|all]${NC}"
        exit 1
        ;;
esac

exit $?
