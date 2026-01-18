#!/bin/bash
# Run Alembic migration - Sprint 74 Planning Hierarchy
# Execute from backend directory

echo "=== Sprint 74 Planning Hierarchy Migration ==="
echo "Date: $(date)"
echo "Running alembic upgrade head..."

cd /app
alembic upgrade head

echo "Migration completed. Checking current revision..."
alembic current

echo "=== Done ==="
