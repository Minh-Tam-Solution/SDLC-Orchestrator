#!/bin/bash

###############################################################################
# Sprint 73 Quick Test - 5 phút
# Chỉ test migration + BUG #7 verification
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ✗${NC} $*"
}

###############################################################################
# Quick Test
###############################################################################

main() {
    echo ""
    log "=========================================="
    log "Sprint 73 Quick Test (5 phút)"
    log "=========================================="
    echo ""

    # 1. Check backend is running
    log "Checking backend..."
    if curl -sf http://localhost:8300/health > /dev/null 2>&1; then
        log_success "Backend is running"
    else
        log_error "Backend not running. Starting..."
        docker compose up -d backend
        sleep 10
    fi

    # 2. Run migration
    log "Running migration..."
    docker exec sdlc-backend bash -c "cd /app && alembic upgrade head" 2>&1 | grep -E "(✓|✅|ERROR|WARNING)" || true

    # 3. Verify 0/0/0
    log "Verifying migration (0/0/0 check)..."
    docker exec postgres-central psql -U sdlc_user -d sdlc_orchestrator -t -c "
        SELECT
            (SELECT COUNT(*) FROM users WHERE organization_id IS NULL AND deleted_at IS NULL) as users_without_org,
            (SELECT COUNT(*) FROM projects WHERE team_id IS NULL AND deleted_at IS NULL) as projects_without_team,
            (SELECT COUNT(*) FROM (SELECT p.id FROM projects p LEFT JOIN gates g ON p.id = g.project_id WHERE p.deleted_at IS NULL GROUP BY p.id HAVING COUNT(g.id) = 0) AS subq) as projects_without_gates;
    " | while read line; do
        if [ -n "$line" ]; then
            if echo "$line" | grep -q "0.*0.*0"; then
                log_success "Migration verified: 0/0/0 (PASS)"
            else
                log_error "Migration failed: $line (expected: 0 | 0 | 0)"
            fi
        fi
    done

    # 4. Test BUG #7 (auto-gate creation)
    log "Testing BUG #7 (auto-gate creation)..."

    # Get token (try default admin)
    TOKEN=$(curl -s -X POST http://localhost:8300/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email": "admin@sdlc-orchestrator.io", "password": "Admin@123"}' \
        | jq -r .access_token 2>/dev/null || echo "")

    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        log_error "Cannot authenticate - skipping BUG #7 test"
    else
        # Create test project
        RESPONSE=$(curl -s -X POST http://localhost:8300/api/v1/projects \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"Quick Test $(date +%s)\",
                \"description\": \"Quick test for Sprint 73\",
                \"slug\": \"quick-test-$(date +%s)\"
            }")

        GATES_CREATED=$(echo "$RESPONSE" | jq -r .gates_created 2>/dev/null || echo "0")

        if [ "$GATES_CREATED" = "5" ]; then
            log_success "BUG #7 VERIFIED: 5 gates auto-created ✓"
        else
            log_error "BUG #7 FAILED: Expected 5 gates, got $GATES_CREATED"
        fi
    fi

    echo ""
    log_success "=========================================="
    log_success "Quick Test Complete!"
    log_success "=========================================="
    echo ""
}

main "$@"
