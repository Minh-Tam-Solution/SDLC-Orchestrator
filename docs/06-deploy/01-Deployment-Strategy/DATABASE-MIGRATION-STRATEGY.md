# Database Migration Strategy
## SDLC Orchestrator - Safe Schema Evolution

**Version**: 1.0.0
**Date**: November 18, 2025
**Status**: ACTIVE - Week 4 Day 1 (Architecture Documentation)
**Authority**: Backend Lead + Database Architect + CTO Approved
**Foundation**: Week 2 Data Model v0.1 (21 tables), Alembic Setup
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Document Purpose

This guide provides **comprehensive database migration strategies** for safely evolving the SDLC Orchestrator schema.

**Key Sections**:
- **Alembic Migration Workflow** - Creating, testing, and deploying migrations
- **Zero-Downtime Migrations** - Backward-compatible schema changes
- **Rollback Strategies** - Automatic and manual rollback procedures
- **Data Integrity Checks** - Pre/post-migration validation
- **Best Practices** - Review process, scheduling, monitoring
- **Troubleshooting** - Common issues, debugging, emergency procedures

**Audience**:
- Backend developers (creating migrations)
- Database administrators (production deployments)
- DevOps engineers (CI/CD integration)
- QA engineers (migration testing)

---

## Table of Contents

1. [Overview](#overview)
2. [Alembic Migration Workflow](#alembic-migration-workflow)
3. [Zero-Downtime Migrations](#zero-downtime-migrations)
4. [Rollback Strategies](#rollback-strategies)
5. [Data Integrity Checks](#data-integrity-checks)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Alembic?

**Alembic** is a lightweight database migration tool for SQLAlchemy.

**Key Features**:
- ✅ Auto-generate migrations from SQLAlchemy models
- ✅ Version control for database schema
- ✅ Upgrade and downgrade capabilities (forward/rollback)
- ✅ Support for multiple database branches
- ✅ Production-ready (used by Dropbox, Reddit, etc.)

**Why Alembic over alternatives**:
- **Django Migrations**: Tied to Django ORM (not SQLAlchemy)
- **Flask-Migrate**: Wrapper around Alembic (unnecessary abstraction)
- **SQLAlchemy-Migrate**: Deprecated (no longer maintained)
- **Alembic**: ✅ Industry standard for SQLAlchemy projects

### Migration Principles

**1. Backward Compatibility** (Zero-Downtime):
- New code must work with old schema
- Old code must work with new schema (during deployment)
- Use multi-step migrations for breaking changes

**2. Rollback Safety**:
- Every migration must have a downgrade path
- Rollbacks should preserve data (no data loss)
- Test rollbacks in staging before production

**3. Data Integrity**:
- Validate data before and after migration
- Use transactions for atomic migrations
- Backup critical data before large migrations

**4. Performance**:
- Avoid long-running migrations (use background jobs)
- Use concurrent index creation (PostgreSQL CONCURRENTLY)
- Schedule migrations during off-peak hours

### Alembic Setup

**Project Structure**:
```
backend/
├── alembic/
│   ├── versions/           # Migration files
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_user_roles.py
│   │   └── 003_add_gate_approvals.py
│   ├── env.py              # Alembic environment configuration
│   ├── script.py.mako      # Migration template
│   └── README
├── alembic.ini             # Alembic configuration
├── app/
│   ├── models/             # SQLAlchemy models
│   └── db/
│       └── base_class.py   # Base SQLAlchemy model
└── requirements.txt
```

**Configuration** (alembic.ini):
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Database URL (override with environment variable)
sqlalchemy.url = postgresql://sdlc_user:password@localhost:5432/sdlc_orchestrator

[loggers]
keys = root,sqlalchemy,alembic

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

**Environment Configuration** (alembic/env.py):
```python
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import all SQLAlchemy models
from app.db.base_class import Base
from app.models.user import User, Role
from app.models.gate import Gate, GateApproval
from app.models.evidence import GateEvidence
from app.models.policy import Policy

# Alembic Config object
config = context.config

# Override database URL from environment variable
if os.getenv("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Configure logging
fileConfig(config.config_file_name)

# Target metadata (all SQLAlchemy models)
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode (with database connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

---

## Alembic Migration Workflow

### Creating Migrations

#### Autogenerate (Recommended for Schema Changes)

**Use Case**: Adding/removing columns, tables, indexes, constraints

**Command**:
```bash
# Generate migration from SQLAlchemy models
cd backend
alembic revision --autogenerate -m "Add user email index"

# Expected output:
# Generating /path/to/backend/alembic/versions/a1b2c3d4e5f6_add_user_email_index.py ... done
```

**Generated Migration**:
```python
"""Add user email index

Revision ID: a1b2c3d4e5f6
Revises: previous_revision
Create Date: 2025-11-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'a1b2c3d4e5f6'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    """Apply migration: Add email index."""
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade():
    """Rollback migration: Remove email index."""
    op.drop_index('ix_users_email', table_name='users')
```

**Review Generated Migration**:
```bash
# ALWAYS review autogenerated migrations before applying!
cat alembic/versions/a1b2c3d4e5f6_add_user_email_index.py

# Common issues to check:
# ✅ Verify column types are correct (e.g., String vs Text)
# ✅ Verify nullable constraints are correct
# ✅ Verify foreign key relationships are correct
# ✅ Add custom data migrations if needed
```

#### Manual Migration (For Data Migrations)

**Use Case**: Data transformations, ETL scripts, custom SQL

**Command**:
```bash
# Create empty migration template
alembic revision -m "Migrate user_roles_to_jsonb"

# Expected output:
# Generating /path/to/backend/alembic/versions/b2c3d4e5f6g7_migrate_user_roles_to_jsonb.py ... done
```

**Manual Migration Example**:
```python
"""Migrate user_roles to JSONB format

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-18 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'

def upgrade():
    """Migrate user_roles from String to JSONB."""
    # Step 1: Add new JSONB column (nullable)
    op.add_column('users', sa.Column('roles_jsonb', postgresql.JSONB, nullable=True))

    # Step 2: Migrate data (String → JSONB)
    connection = op.get_bind()
    connection.execute("""
        UPDATE users
        SET roles_jsonb = ARRAY[roles]::JSONB
        WHERE roles IS NOT NULL;
    """)

    # Step 3: Make new column NOT NULL
    op.alter_column('users', 'roles_jsonb', nullable=False)

    # Step 4: Drop old column
    op.drop_column('users', 'roles')

    # Step 5: Rename new column
    op.alter_column('users', 'roles_jsonb', new_column_name='roles')

def downgrade():
    """Rollback: JSONB → String."""
    # Step 1: Rename column
    op.alter_column('users', 'roles', new_column_name='roles_jsonb')

    # Step 2: Add old String column
    op.add_column('users', sa.Column('roles', sa.String(50), nullable=True))

    # Step 3: Migrate data (JSONB → String)
    connection = op.get_bind()
    connection.execute("""
        UPDATE users
        SET roles = roles_jsonb->>0
        WHERE roles_jsonb IS NOT NULL;
    """)

    # Step 4: Make old column NOT NULL
    op.alter_column('users', 'roles', nullable=False)

    # Step 5: Drop JSONB column
    op.drop_column('users', 'roles_jsonb')
```

### Migration Commands

#### Upgrade (Apply Migrations)

```bash
# Apply all pending migrations
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, Add user email index
# INFO  [alembic.runtime.migration] Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6g7, Migrate user_roles_to_jsonb

# Apply specific migration
alembic upgrade <revision>

# Apply next migration only
alembic upgrade +1

# Apply next 3 migrations
alembic upgrade +3
```

#### Downgrade (Rollback)

```bash
# Rollback last migration
alembic downgrade -1

# Expected output:
# INFO  [alembic.runtime.migration] Running downgrade b2c3d4e5f6g7 -> a1b2c3d4e5f6, Migrate user_roles_to_jsonb

# Rollback to specific revision
alembic downgrade <revision>

# Rollback all migrations (DESTRUCTIVE!)
alembic downgrade base
```

#### History & Current Version

```bash
# Show migration history
alembic history

# Expected output:
# a1b2c3d4e5f6 -> b2c3d4e5f6g7 (head), Migrate user_roles_to_jsonb
# <base> -> a1b2c3d4e5f6, Add user email index

# Show current migration version
alembic current

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# b2c3d4e5f6g7 (head)

# Show pending migrations
alembic heads

# Show SQL without executing
alembic upgrade head --sql
```

### Migration Testing

#### Development Environment

```bash
# 1. Create test database
createdb sdlc_orchestrator_test

# 2. Set test database URL
export DATABASE_URL="postgresql://sdlc_user:password@localhost:5432/sdlc_orchestrator_test"

# 3. Run migrations
cd backend
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, Add user email index
# INFO  [alembic.runtime.migration] Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6g7, Migrate user_roles_to_jsonb

# 4. Run integration tests
pytest tests/integration/test_migrations.py

# 5. Test rollback
alembic downgrade -1

# Expected output:
# INFO  [alembic.runtime.migration] Running downgrade b2c3d4e5f6g7 -> a1b2c3d4e5f6

# 6. Verify rollback
alembic current

# 7. Re-apply migration
alembic upgrade head

# 8. Drop test database
dropdb sdlc_orchestrator_test
```

#### Staging Environment

**Staging Migration Checklist**:
- ✅ Backup database before migration
- ✅ Run migration during off-peak hours
- ✅ Monitor application logs for errors
- ✅ Validate data integrity post-migration
- ✅ Test rollback procedure
- ✅ Document any issues encountered

**Staging Migration Script**:
```bash
#!/bin/bash
# File: deploy_migration_staging.sh

set -e  # Exit on error

ENVIRONMENT="staging"
DATABASE_URL="postgresql://sdlc_user:${POSTGRES_PASSWORD}@staging-db:5432/sdlc_orchestrator"
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Staging Migration Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $TIMESTAMP"

# Step 1: Backup database
echo "Step 1/5: Backing up database..."
pg_dump -U sdlc_user sdlc_orchestrator | gzip > "$BACKUP_DIR/sdlc_orchestrator_pre_migration_$TIMESTAMP.sql.gz"
echo "✅ Backup complete: $BACKUP_DIR/sdlc_orchestrator_pre_migration_$TIMESTAMP.sql.gz"

# Step 2: Show pending migrations
echo "Step 2/5: Showing pending migrations..."
cd backend
alembic heads
alembic current

# Step 3: Apply migrations
echo "Step 3/5: Applying migrations..."
alembic upgrade head

# Step 4: Validate data integrity
echo "Step 4/5: Validating data integrity..."
python scripts/validate_migration.py

# Step 5: Test application
echo "Step 5/5: Testing application..."
curl -f http://staging-api:8000/health || (echo "❌ Health check failed!" && exit 1)

echo "✅ Staging migration complete!"
```

#### Production Environment

**Production Migration Checklist**:
- ✅ Migration tested in staging (same database version)
- ✅ Rollback procedure documented and tested
- ✅ Maintenance window scheduled (or zero-downtime strategy)
- ✅ Database backup completed
- ✅ Monitoring alerts configured
- ✅ Team on standby (DBA, backend dev, DevOps)

**Production Migration Script**:
```bash
#!/bin/bash
# File: deploy_migration_production.sh

set -e

ENVIRONMENT="production"
DATABASE_URL="postgresql://sdlc_user:${POSTGRES_PASSWORD}@prod-db:5432/sdlc_orchestrator"
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "⚠️  WARNING: Production Migration Deployment ⚠️"
echo "Environment: $ENVIRONMENT"
echo "Timestamp: $TIMESTAMP"
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Migration aborted."
    exit 1
fi

# Step 1: Backup database
echo "Step 1/6: Backing up database..."
pg_dump -U sdlc_user sdlc_orchestrator | gzip > "$BACKUP_DIR/sdlc_orchestrator_pre_migration_$TIMESTAMP.sql.gz"
echo "✅ Backup complete: $BACKUP_DIR/sdlc_orchestrator_pre_migration_$TIMESTAMP.sql.gz"

# Step 2: Enable maintenance mode (optional)
# echo "Step 2/6: Enabling maintenance mode..."
# curl -X POST http://prod-api:8000/admin/maintenance/enable

# Step 3: Show pending migrations
echo "Step 3/6: Showing pending migrations..."
cd backend
alembic heads
alembic current

# Step 4: Apply migrations
echo "Step 4/6: Applying migrations..."
alembic upgrade head

# Step 5: Validate data integrity
echo "Step 5/6: Validating data integrity..."
python scripts/validate_migration.py

# Step 6: Test application
echo "Step 6/6: Testing application..."
curl -f http://prod-api:8000/health || (echo "❌ Health check failed! Rolling back..." && alembic downgrade -1 && exit 1)

# Step 7: Disable maintenance mode (optional)
# echo "Step 7/6: Disabling maintenance mode..."
# curl -X POST http://prod-api:8000/admin/maintenance/disable

echo "✅ Production migration complete!"
```

---

## Zero-Downtime Migrations

### Principles

**Zero-Downtime Migration** = Database schema changes without application downtime.

**Key Strategies**:
1. **Backward Compatibility**: New code works with old schema
2. **Forward Compatibility**: Old code works with new schema
3. **Multi-Step Deployment**: Deploy code before/after schema changes
4. **Blue-Green Deployment**: Run old and new versions simultaneously

### Backward-Compatible Changes (Safe for Zero-Downtime)

#### Add Column (NULLABLE)

**Strategy**: Add column as NULLABLE, populate data, make NOT NULL later

**Migration**:
```python
def upgrade():
    """Add phone_number column (nullable)."""
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade():
    """Remove phone_number column."""
    op.drop_column('users', 'phone_number')
```

**Deployment Steps**:
1. ✅ **Deploy Migration**: Add `phone_number` column (NULLABLE)
2. ✅ **Deploy Application**: Update code to handle NULL `phone_number`
3. ✅ **Populate Data**: Backfill `phone_number` for existing users (background job)
4. ✅ **Deploy Migration**: Make `phone_number` NOT NULL (optional)

**Application Code** (backward-compatible):
```python
# Handle NULL phone_number
class UserResponse(BaseModel):
    id: UUID
    email: str
    phone_number: Optional[str] = None  # Allow NULL during migration
```

#### Add Index (CONCURRENTLY)

**Strategy**: Use PostgreSQL CONCURRENTLY to avoid table locks

**Migration**:
```python
def upgrade():
    """Add email index (concurrent, zero-downtime)."""
    # Use raw SQL for CONCURRENTLY (not supported by Alembic op.create_index)
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_email ON users(email)")

def downgrade():
    """Remove email index."""
    op.execute("DROP INDEX IF EXISTS ix_users_email")
```

**Benefits**:
- ✅ No table lock (reads/writes continue)
- ✅ Zero downtime
- ✅ Safe for production

**Caveats**:
- ⚠️ CONCURRENTLY cannot run inside a transaction (use `op.execute()`)
- ⚠️ Slower than regular index creation
- ⚠️ May fail if table is under heavy write load

#### Add Table

**Strategy**: Add new table, deploy code, populate data

**Migration**:
```python
def upgrade():
    """Add audit_logs table."""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])

def downgrade():
    """Remove audit_logs table."""
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
```

**Deployment Steps**:
1. ✅ **Deploy Migration**: Create `audit_logs` table
2. ✅ **Deploy Application**: Update code to write to `audit_logs`
3. ✅ **Zero Downtime**: Old code ignores new table, new code writes to it

### Forward-Compatible Changes (Requires Multi-Step)

#### Remove Column (3-Step Process)

**Problem**: Removing column breaks old code (if old code reads that column)

**Solution**: Multi-step deployment

**Step 1**: Remove column from application code (deploy first)
```python
# OLD CODE (reads phone_number)
class User:
    email: str
    phone_number: str  # ❌ Remove this field

# NEW CODE (doesn't read phone_number)
class User:
    email: str
    # phone_number removed
```

**Step 2**: Deploy application (old code no longer uses `phone_number`)

**Step 3**: Remove column from database (after application deploy)
```python
def upgrade():
    """Remove phone_number column."""
    op.drop_column('users', 'phone_number')

def downgrade():
    """Re-add phone_number column."""
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
```

**Timeline**:
- Day 1: Deploy application (remove `phone_number` usage)
- Day 2-7: Monitor for errors (ensure old code not using `phone_number`)
- Day 8: Deploy migration (remove `phone_number` column)

#### Change Column Type (4-Step Process)

**Problem**: Changing column type breaks old/new code

**Solution**: Add new column, migrate data, remove old column

**Step 1**: Add new column (NULLABLE)
```python
def upgrade():
    """Add status_new column (String → Enum)."""
    op.add_column('gates', sa.Column('status_new', sa.Enum('PENDING', 'PASSED', 'BLOCKED', name='gate_status_enum'), nullable=True))

def downgrade():
    """Remove status_new column."""
    op.drop_column('gates', 'status_new')
    op.execute("DROP TYPE gate_status_enum")
```

**Step 2**: Migrate data (application code or background job)
```python
# Application code (copy old_column → new_column)
from app.models.gate import Gate, GateStatus

def migrate_gate_status():
    """Migrate status (String) → status_new (Enum)."""
    gates = db.query(Gate).filter(Gate.status_new == None).all()
    for gate in gates:
        if gate.status == "pending":
            gate.status_new = GateStatus.PENDING
        elif gate.status == "passed":
            gate.status_new = GateStatus.PASSED
        elif gate.status == "blocked":
            gate.status_new = GateStatus.BLOCKED
    db.commit()
```

**Step 3**: Make new column NOT NULL, update application code
```python
def upgrade():
    """Make status_new NOT NULL."""
    # Ensure all rows have status_new populated
    connection = op.get_bind()
    result = connection.execute("SELECT COUNT(*) FROM gates WHERE status_new IS NULL")
    count = result.scalar()
    if count > 0:
        raise ValueError(f"Cannot make status_new NOT NULL: {count} rows have NULL values")

    op.alter_column('gates', 'status_new', nullable=False)

def downgrade():
    """Make status_new NULLABLE."""
    op.alter_column('gates', 'status_new', nullable=True)
```

**Step 4**: Remove old column, rename new column
```python
def upgrade():
    """Remove old status column, rename status_new → status."""
    op.drop_column('gates', 'status')
    op.alter_column('gates', 'status_new', new_column_name='status')

def downgrade():
    """Rename status → status_new, re-add old status column."""
    op.alter_column('gates', 'status', new_column_name='status_new')
    op.add_column('gates', sa.Column('status', sa.String(20), nullable=True))
```

**Timeline**:
- Week 1: Deploy Step 1 (add `status_new` column)
- Week 2: Migrate data (copy `status` → `status_new`)
- Week 3: Deploy Step 3 (make `status_new` NOT NULL)
- Week 4: Deploy Step 4 (remove `status`, rename `status_new`)

### Blue-Green Deployment Pattern

**Strategy**: Run old (Blue) and new (Green) environments simultaneously

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer                           │
│                  (Traffic Switching)                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   ┌────▼────┐         ┌────▼────┐
   │  Blue   │         │  Green  │
   │ (Old)   │         │  (New)  │
   │ v1.0.0  │         │ v1.1.0  │
   └────┬────┘         └────┬────┘
        │                   │
   ┌────▼────────────────────▼────┐
   │      Database (Shared)        │
   │  (Schema compatible with      │
   │   both Blue and Green)        │
   └───────────────────────────────┘
```

**Deployment Steps**:
1. ✅ **Blue Environment** (Current Production)
   - Run migration on Blue database
   - Ensure Blue application still works

2. ✅ **Green Environment** (New Production)
   - Deploy new application version to Green
   - Run migrations on Green database (same database, compatible schema)
   - Validate Green environment

3. ✅ **Traffic Switch**
   - Gradually shift traffic from Blue to Green (10% → 50% → 100%)
   - Monitor metrics (errors, latency, CPU)

4. ✅ **Rollback** (If Issues)
   - Switch traffic back to Blue (instant rollback)
   - Fix issues in Green
   - Retry deployment

**Example** (Kubernetes):
```yaml
# Blue Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdlc-backend-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sdlc-backend
      version: blue
  template:
    metadata:
      labels:
        app: sdlc-backend
        version: blue
    spec:
      containers:
      - name: backend
        image: sdlc-backend:v1.0.0

---
# Green Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdlc-backend-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sdlc-backend
      version: green
  template:
    metadata:
      labels:
        app: sdlc-backend
        version: green
    spec:
      containers:
      - name: backend
        image: sdlc-backend:v1.1.0

---
# Service (Traffic Splitting)
apiVersion: v1
kind: Service
metadata:
  name: sdlc-backend
spec:
  selector:
    app: sdlc-backend
    version: blue  # Change to 'green' for traffic switch
  ports:
  - port: 8000
    targetPort: 8000
```

---

## Rollback Strategies

### Automatic Rollback (Alembic Downgrade)

**Command**:
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>

# Rollback all migrations (DESTRUCTIVE!)
alembic downgrade base
```

**Example Rollback**:
```python
# Migration: Add user_email_index
def upgrade():
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade():
    op.drop_index('ix_users_email', table_name='users')
```

**Rollback Steps**:
1. ✅ Stop application (if necessary)
2. ✅ Run `alembic downgrade -1`
3. ✅ Verify schema rollback (`alembic current`)
4. ✅ Restart application (old version)
5. ✅ Validate application functionality

### Manual Rollback Procedures

**When Automatic Rollback Fails**:
- ❌ Migration partially applied (constraint violation)
- ❌ Data already migrated (rollback would lose data)
- ❌ Alembic version table corrupted

**Manual Rollback Steps**:

**Step 1**: Backup current database state
```bash
pg_dump -U sdlc_user sdlc_orchestrator | gzip > rollback_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Step 2**: Manually reverse schema changes
```sql
-- Example: Manually drop index
DROP INDEX IF EXISTS ix_users_email;

-- Example: Manually drop column
ALTER TABLE users DROP COLUMN phone_number;

-- Example: Manually restore old column type
ALTER TABLE gates ADD COLUMN status_old VARCHAR(20);
UPDATE gates SET status_old = status::TEXT;
ALTER TABLE gates DROP COLUMN status;
ALTER TABLE gates RENAME COLUMN status_old TO status;
```

**Step 3**: Update Alembic version table
```sql
-- Manually update Alembic version (DANGEROUS!)
UPDATE alembic_version SET version_num = '<previous_revision>';
```

**Step 4**: Verify rollback
```bash
# Verify Alembic version
alembic current

# Expected: <previous_revision>

# Verify schema
psql -U sdlc_user -d sdlc_orchestrator -c "\d users"
```

### Data Preservation During Rollback

**Strategy**: Backup critical data before migration

**Pre-Migration Backup**:
```python
# Migration: backup_user_roles.py
def upgrade():
    """Backup user_roles before migration."""
    connection = op.get_bind()

    # Export data to temporary table
    connection.execute("""
        CREATE TABLE user_roles_backup AS
        SELECT id, roles FROM users;
    """)

    # Proceed with migration
    # ...

def downgrade():
    """Restore user_roles from backup."""
    connection = op.get_bind()

    # Restore data from backup
    connection.execute("""
        UPDATE users
        SET roles = user_roles_backup.roles
        FROM user_roles_backup
        WHERE users.id = user_roles_backup.id;
    """)

    # Drop backup table
    connection.execute("DROP TABLE user_roles_backup;")
```

### Rollback Decision Criteria

**When to Rollback** ✅:
- ✅ Migration fails (syntax errors, constraint violations)
- ✅ Data integrity issues (data loss, corruption, foreign key violations)
- ✅ Performance degradation (>50% slower queries, table locks)
- ✅ Application errors (API failures, crashes, 500 errors)
- ✅ Monitoring alerts (high error rate, low throughput)

**When NOT to Rollback** ⚠️:
- ⚠️ Migration partially applied (requires manual fix, not automatic rollback)
- ⚠️ Data already migrated (rollback would lose new data)
- ⚠️ Application already deployed (requires coordinated rollback of code + schema)
- ⚠️ Minor performance impact (<10% slower, acceptable)

**Rollback SLA**:
- **Critical Issues**: Rollback within 15 minutes (data loss, application down)
- **Major Issues**: Rollback within 1 hour (performance degradation, errors)
- **Minor Issues**: Fix forward (no rollback, apply fix migration)

---

## Data Integrity Checks

### Pre-Migration Validation

**Purpose**: Ensure database is in a consistent state before migration

**Validation Script**:
```python
# File: scripts/validate_pre_migration.py
import sys
from sqlalchemy import create_engine, inspect
from app.core.config import settings

def validate_pre_migration():
    """Validate database before migration."""
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)

    errors = []

    # Check 1: Verify all required tables exist
    required_tables = ['users', 'roles', 'gates', 'gate_evidence', 'policies']
    existing_tables = inspector.get_table_names()

    for table in required_tables:
        if table not in existing_tables:
            errors.append(f"Missing table: {table}")

    # Check 2: Verify foreign key integrity
    with engine.connect() as conn:
        result = conn.execute("""
            SELECT conname, conrelid::regclass, confrelid::regclass
            FROM pg_constraint
            WHERE contype = 'f'
            AND NOT EXISTS (
                SELECT 1
                FROM pg_class c1
                JOIN pg_class c2 ON c1.oid = conrelid AND c2.oid = confrelid
            );
        """)
        for row in result:
            errors.append(f"Invalid foreign key: {row[0]}")

    # Check 3: Verify no NULL values in NOT NULL columns
    for table in existing_tables:
        columns = inspector.get_columns(table)
        for column in columns:
            if not column['nullable']:
                result = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column['name']} IS NULL")
                count = result.scalar()
                if count > 0:
                    errors.append(f"NULL values in NOT NULL column: {table}.{column['name']} ({count} rows)")

    # Report errors
    if errors:
        print("❌ Pre-migration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Pre-migration validation passed")

if __name__ == "__main__":
    validate_pre_migration()
```

### Post-Migration Validation

**Purpose**: Ensure migration succeeded and data integrity maintained

**Validation Script**:
```python
# File: scripts/validate_post_migration.py
import sys
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings

def validate_post_migration():
    """Validate database after migration."""
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)

    errors = []

    # Check 1: Verify expected schema changes
    # Example: Verify email index exists
    indexes = inspector.get_indexes('users')
    if 'ix_users_email' not in [idx['name'] for idx in indexes]:
        errors.append("Missing index: ix_users_email")

    # Check 2: Verify data integrity (row counts)
    with engine.connect() as conn:
        # Example: Verify no users lost during migration
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        expected_count = 1000  # Known value before migration
        if user_count < expected_count:
            errors.append(f"User count mismatch: expected {expected_count}, got {user_count}")

    # Check 3: Verify foreign key integrity
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM gates
            WHERE created_by NOT IN (SELECT id FROM users);
        """))
        orphaned_gates = result.scalar()
        if orphaned_gates > 0:
            errors.append(f"Orphaned gates: {orphaned_gates} gates reference non-existent users")

    # Report errors
    if errors:
        print("❌ Post-migration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Post-migration validation passed")

if __name__ == "__main__":
    validate_post_migration()
```

### Migration Testing

#### Unit Tests

**Test Migration Logic**:
```python
# File: tests/integration/test_migrations.py
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

@pytest.fixture
def alembic_config():
    """Alembic configuration for testing."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", "postgresql://sdlc_user:password@localhost:5432/sdlc_test")
    return config

def test_migration_upgrade(alembic_config):
    """Test migration upgrade."""
    # Apply all migrations
    command.upgrade(alembic_config, "head")

    # Verify schema changes
    engine = create_engine(alembic_config.get_main_option("sqlalchemy.url"))
    inspector = inspect(engine)

    # Example: Verify email index exists
    indexes = inspector.get_indexes('users')
    assert 'ix_users_email' in [idx['name'] for idx in indexes]

def test_migration_downgrade(alembic_config):
    """Test migration rollback."""
    # Apply all migrations
    command.upgrade(alembic_config, "head")

    # Rollback last migration
    command.downgrade(alembic_config, "-1")

    # Verify schema changes reverted
    engine = create_engine(alembic_config.get_main_option("sqlalchemy.url"))
    inspector = inspect(engine)

    # Example: Verify email index removed
    indexes = inspector.get_indexes('users')
    assert 'ix_users_email' not in [idx['name'] for idx in indexes]

def test_migration_idempotent(alembic_config):
    """Test migration idempotency (can run multiple times)."""
    # Apply migration twice
    command.upgrade(alembic_config, "head")
    command.upgrade(alembic_config, "head")  # Should not fail

    # Verify schema unchanged
    # ...
```

---

## Best Practices

### 1. Migration Review Process

**Code Review Checklist**:
- ✅ Migration has clear description (what it does, why)
- ✅ Migration has downgrade path (rollback logic)
- ✅ Migration tested in development and staging
- ✅ Migration performance reviewed (no long-running operations)
- ✅ Migration data integrity validated (pre/post checks)
- ✅ Migration backward-compatible (zero-downtime strategy)

**Review Template**:
```markdown
## Migration Review: Add user_email_index

**Author**: @backend-dev
**Reviewers**: @dba, @senior-backend-dev
**Jira**: SDLC-123

### Summary
Add unique index on `users.email` to improve login query performance.

### Testing
- ✅ Tested in development (local PostgreSQL 15.5)
- ✅ Tested in staging (10K users, <5s migration time)
- ✅ Rollback tested in staging

### Performance Impact
- **Estimated Migration Time**: 5 seconds (10K users)
- **Estimated Index Size**: 1 MB
- **Query Performance Improvement**: 50ms → 5ms (10x faster)

### Risks
- ⚠️ Migration requires brief table lock (CONCURRENTLY not used)
- ⚠️ Mitigation: Run during off-peak hours (2 AM UTC)

### Rollback Plan
- Automatic rollback: `alembic downgrade -1`
- Manual rollback: `DROP INDEX ix_users_email;`

### Approval
- ✅ DBA: Approved (performance looks good)
- ✅ Senior Backend Dev: Approved (migration tested)
```

### 2. Migration Scheduling

**Best Practices**:
- ✅ Schedule migrations during off-peak hours (minimize user impact)
- ✅ Communicate maintenance windows to users (email, status page)
- ✅ Use zero-downtime strategies when possible (no maintenance window needed)
- ✅ Have team on standby during migration (DBA, backend dev, DevOps)

**Maintenance Window Schedule**:
```markdown
## Maintenance Window: Database Migration

**Date**: Saturday, December 10, 2025
**Time**: 2:00 AM - 4:00 AM UTC (off-peak hours)
**Duration**: Estimated 30 minutes (2-hour buffer)
**Impact**: API may be unavailable for 5-10 minutes

### Migration Plan
1. ✅ 2:00 AM: Backup database (10 minutes)
2. ✅ 2:10 AM: Enable maintenance mode (API returns 503)
3. ✅ 2:15 AM: Apply migrations (5-10 minutes)
4. ✅ 2:25 AM: Validate data integrity (5 minutes)
5. ✅ 2:30 AM: Disable maintenance mode (API live)
6. ✅ 2:35 AM: Monitor for errors (25 minutes)

### Rollback Plan
If errors detected:
1. ❌ 2:40 AM: Rollback migration (`alembic downgrade -1`)
2. ❌ 2:45 AM: Restore from backup (if needed)
3. ❌ 2:50 AM: Restart application (old version)

### Communication
- **Status Page**: https://status.sdlc-orchestrator.com
- **Email**: Sent to all users 48 hours in advance
- **Slack**: #engineering, #ops
```

### 3. Migration Monitoring

**Monitoring Metrics**:
- **Migration Duration**: Track how long migrations take
- **Application Errors**: Monitor 4xx/5xx error rates during migration
- **Database Connections**: Monitor active connections (should not spike)
- **Query Performance**: Monitor slow queries post-migration

**Monitoring Dashboard** (Grafana):
```yaml
# Prometheus metrics
- sdlc_migration_duration_seconds (histogram)
- sdlc_migration_errors_total (counter)
- sdlc_migration_last_run_timestamp (gauge)

# Alerting rules
- Alert: MigrationTooSlow
  Condition: sdlc_migration_duration_seconds > 300
  Action: Slack #ops

- Alert: MigrationFailed
  Condition: sdlc_migration_errors_total > 0
  Action: PagerDuty (wake up DBA)
```

### 4. Migration Documentation

**Changelog Template**:
```markdown
## Database Migration Changelog

### v1.2.0 (December 10, 2025)

**Migration**: `a1b2c3d4e5f6_add_user_email_index`

**Changes**:
- Added unique index on `users.email`

**Rationale**:
- Improve login query performance (50ms → 5ms)

**Impact**:
- **Estimated Duration**: 5 seconds (10K users)
- **Downtime**: None (zero-downtime migration)

**Rollback**:
```bash
alembic downgrade -1
```

**Validation**:
```bash
# Verify index exists
psql -c "\d users"
```
```

---

## Troubleshooting

### Common Migration Issues

#### Issue 1: Lock Timeout

**Error**:
```
sqlalchemy.exc.OperationalError: (psycopg2.errors.LockNotAvailable) could not obtain lock on relation "users"
```

**Cause**: Long-running migration holds table lock, blocking other queries

**Solution**:
1. Use CONCURRENTLY for index creation (no lock)
2. Break migration into smaller steps
3. Schedule migration during off-peak hours

```python
# ❌ BAD (holds lock)
op.create_index('ix_users_email', 'users', ['email'])

# ✅ GOOD (no lock)
op.execute("CREATE INDEX CONCURRENTLY ix_users_email ON users(email)")
```

#### Issue 2: Foreign Key Constraint Violation

**Error**:
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "gates" violates foreign key constraint "fk_gates_created_by_users"
```

**Cause**: Orphaned data (foreign key references non-existent row)

**Solution**:
1. Clean up orphaned data before migration
2. Use CASCADE on foreign keys (delete orphaned data automatically)

```python
# Migration: Clean up orphaned data
def upgrade():
    connection = op.get_bind()

    # Delete orphaned gates
    connection.execute("""
        DELETE FROM gates
        WHERE created_by NOT IN (SELECT id FROM users);
    """)

    # Proceed with migration
    # ...
```

#### Issue 3: Duplicate Key Violation

**Error**:
```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "users_email_key"
```

**Cause**: Duplicate data in column marked as UNIQUE

**Solution**:
1. Remove duplicates before adding UNIQUE constraint
2. Update application logic to prevent duplicates

```python
# Migration: Remove duplicates
def upgrade():
    connection = op.get_bind()

    # Keep oldest user, delete duplicates
    connection.execute("""
        DELETE FROM users a
        USING users b
        WHERE a.id > b.id
        AND a.email = b.email;
    """)

    # Add UNIQUE constraint
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
```

### Migration Debugging

**Enable SQL Logging**:
```python
# alembic/env.py
import logging

# Enable SQL echo
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        echo=True,  # Enable SQL logging
    )
    # ...
```

**Dry Run** (Show SQL without executing):
```bash
# Show SQL for upgrade
alembic upgrade head --sql > migration_upgrade.sql

# Review SQL before applying
cat migration_upgrade.sql
```

### Emergency Procedures

#### Data Recovery

**Scenario**: Migration deleted data accidentally

**Recovery Steps**:
1. ✅ Stop application immediately
2. ✅ Restore from last backup
3. ✅ Re-apply migrations (if needed)
4. ✅ Validate data integrity
5. ✅ Restart application

```bash
# Restore from backup
gunzip -c backup_20251118_020000.sql.gz | psql -U sdlc_user sdlc_orchestrator

# Verify data
psql -U sdlc_user -d sdlc_orchestrator -c "SELECT COUNT(*) FROM users;"

# Re-apply migrations (if needed)
cd backend
alembic upgrade head
```

---

## Additional Resources

### Documentation
- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **PostgreSQL Concurrent Indexes**: https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/

### Internal Documentation
- **Data Model v0.1**: [Data-Model-ERD.md](../../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md)
- **Docker Deployment Guide**: [DOCKER-DEPLOYMENT-GUIDE.md](./DOCKER-DEPLOYMENT-GUIDE.md)
- **Monitoring & Observability Guide**: [MONITORING-OBSERVABILITY-GUIDE.md](../02-Environment-Management/MONITORING-OBSERVABILITY-GUIDE.md)
- **C4 Architecture Diagrams**: [C4-ARCHITECTURE-DIAGRAMS.md](../../02-Design-Architecture/02-System-Architecture/C4-ARCHITECTURE-DIAGRAMS.md)
- **API Developer Guide**: [API-DEVELOPER-GUIDE.md](../../02-Design-Architecture/04-API-Design/API-DEVELOPER-GUIDE.md)

---

**Last Updated**: November 18, 2025
**Owner**: Backend Lead + Database Architect + CTO
**Status**: ✅ ACTIVE (Week 4 Day 1)

---

**End of Database Migration Strategy v1.0.0**
