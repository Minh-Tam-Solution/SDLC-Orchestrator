#!/bin/bash

###############################################################################
# Reset Test Database
#
# File: scripts/reset_test_db.sh
# Version: 1.0.0
# Date: December 12, 2025
# Status: ACTIVE - Week 6 Day 1
# Authority: Backend Lead + QA Lead
# Framework: SDLC 4.9 Complete Lifecycle
#
# Description:
#   Resets the test database (sdlc_orchestrator_test) to a clean state.
#   Drops all tables and recreates schema using pytest fixtures.
#
# Usage:
#   ./scripts/reset_test_db.sh
#
# Prerequisites:
#   - PostgreSQL container running (docker-compose up postgres)
#   - Correct user: sdlc_user (from docker-compose.yml)
#
# Safety:
#   - Only affects sdlc_orchestrator_test (NOT production)
###############################################################################

set -e  # Exit on error

echo "🔄 Resetting test database..."

# Database configuration (use sdlc_user from docker-compose.yml)
DB_USER="${DB_USER:-sdlc_user}"
DB_PASSWORD="${DB_PASSWORD:-changeme_secure_password}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
TEST_DB_NAME="sdlc_orchestrator_test"

echo "📊 Dropping all tables in test database..."

# Drop all tables in test database (preserve the database itself)
docker exec sdlc-postgres psql -U "$DB_USER" -d "$TEST_DB_NAME" -c "
DO \$\$ DECLARE
    r RECORD;
BEGIN
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;

    -- Drop all sequences
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
    END LOOP;

    -- Drop all types (enums, etc)
    FOR r IN (SELECT typname FROM pg_type WHERE typnamespace = 'public'::regnamespace AND typtype = 'e') LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
    END LOOP;
END \$\$;
" 2>/dev/null || echo "Note: Some objects may not exist"

echo "✅ Test database reset complete: $TEST_DB_NAME"

# Note: Schema will be recreated by pytest fixtures
echo "ℹ️  Schema will be created by pytest fixtures (tests/conftest.py)"
echo "ℹ️  Run tests with: pytest tests/integration/ -v --cov"

