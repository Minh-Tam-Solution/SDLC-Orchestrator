#!/bin/bash
# =========================================================================
# Reset Database Script - SDLC Orchestrator
# =========================================================================
# Version: 1.0.1
# Date: December 29, 2025
#
# Usage:
#   ./scripts/reset-database.sh
#
# This script will:
# 1. Stop the backend container
# 2. Drop and recreate the database
# 3. Run all migrations
# 4. Truncate seeded data from migrations
# 5. Apply clean start seed data
# 6. Restart the backend container
#
# WARNING: This will DELETE ALL DATA in the database!
# =========================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SEED_FILE="$PROJECT_DIR/docs/05-test/07-E2E-Testing/CLEAN-START-SEED-DATA.sql"

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}SDLC Orchestrator - Database Reset${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""

# Confirm before proceeding
echo -e "${RED}WARNING: This will DELETE ALL DATA in the database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/6] Stopping backend container...${NC}"
docker compose stop backend || true

echo ""
echo -e "${YELLOW}[2/6] Dropping and recreating database...${NC}"
docker exec postgres-central psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'sdlc_orchestrator' AND pid <> pg_backend_pid();" > /dev/null 2>&1 || true
docker exec postgres-central psql -U postgres -c "DROP DATABASE IF EXISTS sdlc_orchestrator;"
docker exec postgres-central psql -U postgres -c "CREATE DATABASE sdlc_orchestrator OWNER sdlc_user;"
echo -e "${GREEN}Database recreated.${NC}"

echo ""
echo -e "${YELLOW}[3/6] Starting backend container...${NC}"
docker compose up -d backend
sleep 8  # Wait for backend to start and be healthy

echo ""
echo -e "${YELLOW}[4/6] Running database migrations...${NC}"
docker compose exec -T backend alembic upgrade head
echo -e "${GREEN}Migrations completed.${NC}"

echo ""
echo -e "${YELLOW}[5/6] Truncating migration seed data...${NC}"
docker exec postgres-central psql -U sdlc_user -d sdlc_orchestrator -c "
TRUNCATE TABLE users, roles, projects, project_members, gates, ai_providers, policies, audit_logs, api_keys, oauth_accounts, refresh_tokens CASCADE;
" > /dev/null 2>&1
echo -e "${GREEN}Data truncated.${NC}"

echo ""
echo -e "${YELLOW}[6/6] Applying clean start seed data...${NC}"
cat "$SEED_FILE" | docker exec -i postgres-central psql -U sdlc_user -d sdlc_orchestrator
echo -e "${GREEN}Seed data applied.${NC}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Database Reset Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Platform Admin Account:"
echo "  Email: admin@sdlc-orchestrator.io"
echo "  Password: Admin@123"
echo ""
echo "First Owner to Onboard:"
echo "  Email: dangtt1971@gmail.com"
echo "  Method: GitHub OAuth or Email Registration"
echo "  Project: Endior Translator"
echo ""
