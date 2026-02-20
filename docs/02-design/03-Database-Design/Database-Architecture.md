# Database Architecture (PostgreSQL 15.5)

**Version**: v1.1
**Date**: February 15, 2026
**Owner**: Tech Lead, Database Architect
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Status**: ✅ APPROVED

**Changelog v1.1** (Feb 15, 2026):
- Sprint 173 Governance Loop schema changes (ADR-053):
  - `gates` table: Added `evaluated_at`, `exit_criteria_version` columns; status values updated (PENDING_APPROVAL→SUBMITTED, added EVALUATED/EVALUATED_STALE)
  - `gate_evidence` table: Renamed `sha256_hash`→`sha256_client`; added `sha256_server`, `criteria_snapshot_id`, `source` columns
  - Alembic migration required for data migration (status value rename)

---

## 1. Overview

This document defines the **database architecture** for SDLC Orchestrator, built on **PostgreSQL 15.5**.

**Design Principles**:
- **ACID compliance** (critical for gate approvals, evidence linking)
- **Hybrid schema** (relational tables + JSONB for flexible data)
- **Performance** (indexing strategy, partitioning, connection pooling)
- **Scalability** (read replicas, Citus sharding for Year 5+)
- **Security** (encryption at rest/transit, RLS, audit logging)

**Related Documents**:
- [ADR-001-Database-Choice.md](../02-System-Architecture/Architecture-Decisions/ADR-001-Database-Choice.md) - Why PostgreSQL
- [Schema-Optimization.md](./Schema-Optimization.md) - Indexing strategy
- [Migration-Strategy.md](./Migration-Strategy.md) - Alembic migrations

---

## 2. Database Schema (16 Tables)

### 2.1 Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────────────────────────────────┐
│ ORGANIZATIONS (Multi-Tenant)                                    │
└─────────────────────────────────────────────────────────────────┘
  ↓ 1:N
┌─────────────────────────────────────────────────────────────────┐
│ TEAMS                                                           │
└─────────────────────────────────────────────────────────────────┘
  ↓ 1:N
┌─────────────────────────────────────────────────────────────────┐
│ USERS                    PROJECTS                               │
│   ↓ 1:N                    ↓ 1:N                                │
│ USER_ROLES              GATES                                   │
│                            ↓ 1:N                                │
│                         GATE_APPROVALS                          │
│                         GATE_POLICIES (YAML/JSON)               │
│                            ↓ M:N                                │
│                         EVIDENCE_VAULT                          │
│                            ↓ 1:N                                │
│                         EVIDENCE_LINKS                          │
└─────────────────────────────────────────────────────────────────┘
  ↓ All tables
┌─────────────────────────────────────────────────────────────────┐
│ AUDIT_LOG (Immutable, Append-Only)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Table Definitions

#### **organizations** (Multi-Tenant Root)

```sql
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,  -- techcorp, startup-xyz
  tier VARCHAR(20) NOT NULL,  -- lite, standard, enterprise
  settings JSONB DEFAULT '{}',  -- {logo_url, custom_gates, etc}
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for tenant isolation (RLS)
CREATE INDEX idx_organizations_slug ON organizations(slug);
```

**Scale**: 1,000 organizations (Year 3)

---

#### **teams** (Engineering Teams)

```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) NOT NULL,  -- backend-team, mobile-team
  description TEXT,
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  UNIQUE(organization_id, slug)
);

-- Index for queries: "Get all teams in organization"
CREATE INDEX idx_teams_organization_id ON teams(organization_id);
```

**Scale**: 10,000 teams (Year 3)

---

#### **users** (User Accounts)

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  avatar_url VARCHAR(500),
  password_hash VARCHAR(255),  -- bcrypt (12 rounds), NULL if OAuth-only
  role VARCHAR(20) NOT NULL,  -- ceo, cto, em, se, e, je, qa, pm, designer...
  team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- MFA fields
  mfa_enabled BOOLEAN DEFAULT FALSE,
  mfa_secret VARCHAR(255),  -- TOTP secret (encrypted)
  backup_codes JSONB DEFAULT '[]',  -- Array of backup codes (hashed)

  -- OAuth fields
  oauth_provider VARCHAR(50),  -- github, google, microsoft
  oauth_id VARCHAR(255),  -- GitHub user ID, Google sub

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_oauth_provider_id ON users(oauth_provider, oauth_id);
```

**Scale**: 100,000 users (Year 3)

---

#### **api_keys** (API Keys for CI/CD)

```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,  -- "GitHub Actions CI/CD"
  key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash
  scopes JSONB DEFAULT '["read"]',  -- ["read", "write", "approve"]
  last_used_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP,  -- NULL = never expires
  revoked_at TIMESTAMP
);

-- Index for lookups: "Verify API key"
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
```

**Scale**: 10,000 API keys (Year 3)

---

#### **projects** (Projects)

```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL,  -- planning, active, paused, completed, archived
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Metadata
  github_repo VARCHAR(500),  -- github.com/techcorp/sdlc-orchestrator
  jira_project_key VARCHAR(50),  -- SDLC
  metadata JSONB DEFAULT '{}',  -- {start_date, end_date, tech_stack, etc}

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  UNIQUE(organization_id, slug)
);

-- Indexes
CREATE INDEX idx_projects_organization_id ON projects(organization_id);
CREATE INDEX idx_projects_team_id ON projects(team_id);
CREATE INDEX idx_projects_status ON projects(status);
```

**Scale**: 100,000 projects (Year 3)

---

#### **gates** (SDLC Gates: G0.1, G0.2, G1-G9)

```sql
CREATE TABLE gates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_name VARCHAR(255) NOT NULL,
  gate_type VARCHAR(50) NOT NULL,  -- 'G1_DESIGN_READY', 'G2_SHIP_READY', etc.
  stage VARCHAR(20) NOT NULL,  -- 'WHY', 'WHAT', 'BUILD', 'TEST', etc.
  description TEXT,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  -- Sprint 173 State Machine (ADR-053):
  -- Valid: DRAFT, EVALUATED, EVALUATED_STALE, SUBMITTED, APPROVED, REJECTED, ARCHIVED
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
  exit_criteria JSONB NOT NULL DEFAULT '[]',
  exit_criteria_version UUID DEFAULT gen_random_uuid(),  -- Sprint 173: snapshot binding
  evaluated_at TIMESTAMP,  -- Sprint 173: last evaluation timestamp
  approved_at TIMESTAMP,
  rejected_at TIMESTAMP,
  archived_at TIMESTAMP,

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMP,  -- Soft delete

  UNIQUE(project_id, gate_type)
);

-- Indexes
CREATE INDEX idx_gates_project_id ON gates(project_id);
CREATE INDEX idx_gates_status ON gates(status);
CREATE INDEX idx_gates_gate_type ON gates(gate_type);
CREATE INDEX idx_gates_stage ON gates(stage);
CREATE INDEX idx_gates_created_by ON gates(created_by);
CREATE INDEX idx_gates_created_at ON gates(created_at);
```

**Scale**: 1.1M gates (100K projects × 11 gates)

---

#### **gate_approvals** (Gate Approvals)

```sql
CREATE TABLE gate_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_id UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL,  -- approved, rejected
  comment TEXT,
  metadata JSONB DEFAULT '{}',  -- {ip_address, user_agent}

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Constraint: One approval per user per gate
  UNIQUE(gate_id, user_id)
);

-- Indexes
CREATE INDEX idx_gate_approvals_gate_id ON gate_approvals(gate_id);
CREATE INDEX idx_gate_approvals_user_id ON gate_approvals(user_id);
CREATE INDEX idx_gate_approvals_status ON gate_approvals(status);
```

**Scale**: 2.2M approvals (1.1M gates × 2 approvals)

---

#### **gate_policies** (Gate Policies - YAML/JSON)

```sql
CREATE TABLE gate_policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_id VARCHAR(10) NOT NULL,  -- G0.1, G0.2, G1, ..., G9
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  policy JSONB NOT NULL,  -- YAML converted to JSON
  version INT DEFAULT 1,

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  UNIQUE(organization_id, gate_id, version)
);

-- Index for JSONB queries
CREATE INDEX idx_gate_policies_policy ON gate_policies USING GIN(policy);
CREATE INDEX idx_gate_policies_organization_gate ON gate_policies(organization_id, gate_id);
```

**Example JSONB**:
```json
{
  "gate_id": "G1",
  "stage": "WHAT",
  "requires": {
    "openapi_lint": "PASS",
    "legal_review": "APPROVED",
    "agpl_containment": "VERIFIED"
  },
  "approvals": ["TechLead", "SecurityLead"],
  "waiver": {
    "allowed": true,
    "max_items": 2,
    "expires_in_days": 21
  }
}
```

**Scale**: 11,000 policies (1,000 orgs × 11 gates)

---

#### **evidence_vault** (Evidence Storage Metadata)

```sql
CREATE TABLE evidence_vault (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(500) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL,  -- document, screenshot, test_report, sbom, etc
  file_path VARCHAR(1000) NOT NULL,  -- s3://bucket/org_id/proj_id/evidence_id
  file_size_bytes BIGINT NOT NULL,
  file_hash_sha256 VARCHAR(64) NOT NULL,  -- Integrity check
  mime_type VARCHAR(100),

  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
  metadata JSONB DEFAULT '{}',  -- {tags, compliance_framework, etc}

  -- AI Semantic Search (pgvector)
  embedding vector(1536),  -- OpenAI Ada-002 embeddings (1536 dimensions)

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_evidence_vault_project_id ON evidence_vault(project_id);
CREATE INDEX idx_evidence_vault_uploaded_by ON evidence_vault(uploaded_by);
CREATE INDEX idx_evidence_vault_type ON evidence_vault(type);
CREATE INDEX idx_evidence_vault_file_hash ON evidence_vault(file_hash_sha256);

-- Vector similarity search index (HNSW - faster than IVFFlat)
CREATE INDEX idx_evidence_vault_embedding ON evidence_vault
  USING hnsw (embedding vector_cosine_ops);
```

**Scale**: 10M evidence files (Year 3)

---

#### **evidence_links** (Evidence → Gate Linkage)

```sql
CREATE TABLE evidence_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_id UUID NOT NULL REFERENCES evidence_vault(id) ON DELETE CASCADE,
  gate_id UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
  link_type VARCHAR(50) DEFAULT 'supports',  -- supports, blocks, related
  comment TEXT,

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),

  UNIQUE(evidence_id, gate_id)
);

-- Indexes
CREATE INDEX idx_evidence_links_evidence_id ON evidence_links(evidence_id);
CREATE INDEX idx_evidence_links_gate_id ON evidence_links(gate_id);
```

**Scale**: 20M links (10M evidence × 2 gates average)

---

#### **audit_log** (Immutable Audit Log)

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id VARCHAR(50) UNIQUE NOT NULL,  -- evt_789
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  user_email VARCHAR(255),  -- Denormalized (in case user deleted)
  action VARCHAR(100) NOT NULL,  -- gate_approved, evidence_uploaded, etc
  resource_type VARCHAR(50) NOT NULL,  -- gate, evidence, project
  resource_id UUID NOT NULL,
  metadata JSONB DEFAULT '{}',  -- {ip_address, user_agent, comment}
  signature VARCHAR(255),  -- HMAC-SHA256 (for non-repudiation)

  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE
);

-- Partition by month (for compliance + performance)
CREATE TABLE audit_log_2025_11 PARTITION OF audit_log
  FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE audit_log_2025_12 PARTITION OF audit_log
  FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Indexes (on each partition)
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_organization_id ON audit_log(organization_id);

-- BRIN index (for timestamp range queries, 100x smaller than B-tree)
CREATE INDEX idx_audit_log_timestamp_brin ON audit_log USING BRIN(timestamp);
```

**Scale**: 50M events (Year 3), partitioned by month (60 partitions × 833K rows/month)

---

#### **refresh_tokens** (JWT Refresh Tokens)

```sql
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  metadata JSONB DEFAULT '{}',  -- {ip_address, user_agent, device_fingerprint}

  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Auto-delete expired tokens (pg_cron extension)
-- Runs daily at 2 AM
SELECT cron.schedule('delete-expired-tokens', '0 2 * * *',
  'DELETE FROM refresh_tokens WHERE expires_at < NOW()');
```

**Scale**: 100K active tokens (1 per user, 30-day TTL)

---

#### **sessions** (Active Sessions - Optional)

```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_token_hash VARCHAR(64) UNIQUE NOT NULL,
  ip_address INET,
  user_agent TEXT,
  device_fingerprint VARCHAR(255),
  last_activity_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,

  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_session_token_hash ON sessions(session_token_hash);
CREATE INDEX idx_sessions_last_activity_at ON sessions(last_activity_at);
```

**Scale**: 10K active sessions (concurrent users)

---

#### **notifications** (In-App Notifications)

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,  -- gate_approved, evidence_uploaded, mention
  title VARCHAR(500) NOT NULL,
  message TEXT,
  link VARCHAR(500),  -- /projects/proj_123/gates/G1
  read_at TIMESTAMP,

  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read_at ON notifications(read_at);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

**Scale**: 1M notifications (Year 3)

---

#### **webhooks** (Outbound Webhooks)

```sql
CREATE TABLE webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  url VARCHAR(1000) NOT NULL,
  events JSONB NOT NULL,  -- ["gate.approved", "evidence.uploaded"]
  secret VARCHAR(255),  -- HMAC secret (for signature verification)
  enabled BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_webhooks_organization_id ON webhooks(organization_id);
CREATE INDEX idx_webhooks_enabled ON webhooks(enabled);
```

**Scale**: 1,000 webhooks (Year 3)

---

#### **webhook_deliveries** (Webhook Delivery Log)

```sql
CREATE TABLE webhook_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
  event_type VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL,
  response_status_code INT,
  response_body TEXT,
  delivered_at TIMESTAMP,
  failed_at TIMESTAMP,
  retry_count INT DEFAULT 0,

  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_event_type ON webhook_deliveries(event_type);
CREATE INDEX idx_webhook_deliveries_created_at ON webhook_deliveries(created_at DESC);
```

**Scale**: 10M deliveries (Year 3)

---

## 3. Indexing Strategy

### 3.1 Index Types

| Index Type | Use Case | Example |
|------------|----------|---------|
| **B-tree** (default) | Primary keys, foreign keys, equality/range queries | `CREATE INDEX idx_users_email ON users(email)` |
| **GIN** (Generalized Inverted Index) | JSONB, array, full-text search | `CREATE INDEX idx_gate_policies_policy ON gate_policies USING GIN(policy)` |
| **HNSW** (Hierarchical Navigable Small World) | Vector similarity search (pgvector) | `CREATE INDEX idx_evidence_vault_embedding ON evidence_vault USING hnsw(embedding vector_cosine_ops)` |
| **BRIN** (Block Range Index) | Timestamp range queries (100x smaller than B-tree) | `CREATE INDEX idx_audit_log_timestamp_brin ON audit_log USING BRIN(timestamp)` |

**Index Size Comparison** (audit_log table, 50M rows):
- B-tree on `timestamp`: ~2GB
- BRIN on `timestamp`: ~20MB (100x smaller)
- Trade-off: BRIN is slower for point queries, but faster for range queries

---

### 3.2 Query Performance Targets

| Query | Target (p95) | Index Strategy |
|-------|--------------|----------------|
| GET /projects (list) | <50ms | `idx_projects_organization_id` (B-tree) |
| GET /projects/:id (detail) | <50ms | Primary key (B-tree) |
| GET /gates/:id/approvals | <50ms | `idx_gate_approvals_gate_id` (B-tree) |
| POST /gates/:id/approve | <100ms | Transaction (ACID), `idx_gate_approvals_gate_id` |
| GET /evidence (semantic search) | <200ms | `idx_evidence_vault_embedding` (HNSW) |
| GET /audit-log (range query) | <100ms | `idx_audit_log_timestamp_brin` (BRIN) |

---

## 4. Partitioning Strategy

### 4.1 Audit Log (Time-Series Partitioning)

**Problem**: 50M rows (Year 3) → slow queries, large indexes

**Solution**: Partition by month (60 partitions × 833K rows/month)

```sql
-- Parent table (partitioned)
CREATE TABLE audit_log (
  id UUID NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  ...
) PARTITION BY RANGE (timestamp);

-- Child partitions (one per month)
CREATE TABLE audit_log_2025_11 PARTITION OF audit_log
  FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE audit_log_2025_12 PARTITION OF audit_log
  FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
```

**Benefits**:
- ✅ Query only relevant partition (10x faster for range queries)
- ✅ Drop old partitions (DELETE is instant, not row-by-row)
- ✅ Smaller indexes (index per partition, not global)

**Automation** (Create partitions automatically):
```python
# Alembic migration: create next 12 months of partitions
from datetime import datetime, timedelta

def create_audit_log_partitions():
    now = datetime.utcnow()
    for i in range(12):
        start = (now + timedelta(days=30 * i)).replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        partition_name = f"audit_log_{start.strftime('%Y_%m')}"

        op.execute(f"""
          CREATE TABLE IF NOT EXISTS {partition_name}
          PARTITION OF audit_log
          FOR VALUES FROM ('{start.strftime('%Y-%m-%d')}')
                      TO ('{end.strftime('%Y-%m-%d')}')
        """)
```

---

### 4.2 Webhook Deliveries (Time-Series Partitioning)

**Same strategy as audit_log** (10M rows, partition by month)

---

## 5. Connection Pooling (PgBouncer)

**Problem**: 1,000 concurrent users → 1,000 DB connections → PostgreSQL limit (100-500)

**Solution**: PgBouncer (connection pooler)

```
┌─────────────────────────────────────────────────────────────────┐
│ Application (FastAPI) - 1,000 concurrent requests               │
└─────────────────────────────────────────────────────────────────┘
                       ↓ 1,000 connections
┌─────────────────────────────────────────────────────────────────┐
│ PgBouncer (Connection Pooler)                                   │
│   - Mode: Transaction pooling                                   │
│   - Max client connections: 10,000                              │
│   - Pool size (per database): 100                               │
└─────────────────────────────────────────────────────────────────┘
                       ↓ 100 connections
┌─────────────────────────────────────────────────────────────────┐
│ PostgreSQL 15.5 (AWS RDS)                                       │
│   - Max connections: 100                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Configuration**:
```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
sdlc_orchestrator = host=postgres.sdlc-orchestrator.com port=5432 dbname=sdlc_orchestrator

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Transaction pooling (recommended for web apps)
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 100
reserve_pool_size = 10
reserve_pool_timeout = 5
```

**Benefits**:
- ✅ 1,000 clients → 100 DB connections (10x reduction)
- ✅ Faster connection (reuse existing, not create new)
- ✅ Protects DB from connection exhaustion

---

## 6. Scalability Plan

### Phase 1: MVP (100 Teams) - Week 5-12
```yaml
Infrastructure:
  - AWS RDS PostgreSQL 15.5 (db.t3.medium, 2 vCPU, 4GB RAM)
  - Storage: 100GB SSD (gp3)
  - Backups: Automated daily snapshots (7-day retention)

Schema:
  - 16 tables, ~10K rows total
  - Indexes: B-tree (primary keys), GIN (JSONB), HNSW (vector)

ORM:
  - SQLAlchemy 2.0 (async support)
  - Alembic (migrations, idempotent, backward-compatible)
```

---

### Phase 2: Scale (1,000 Teams) - Year 2-3
```yaml
Infrastructure:
  - AWS RDS PostgreSQL (db.r5.xlarge, 4 vCPU, 32GB RAM)
  - Storage: 1TB SSD (gp3)
  - Read replicas: 2x (load balancing, HA)

Optimizations:
  - Partitioning: audit_log, webhook_deliveries by month
  - Caching: Redis (session, token blacklist, frequent queries)
  - Connection pooling: PgBouncer (1K connections → 100 DB connections)
```

---

### Phase 3: Enterprise (10K+ Teams) - Year 5+
```yaml
Infrastructure:
  - Citus (horizontal sharding by organization_id)
  - 5 nodes (1 coordinator, 4 workers)
  - AWS Aurora Global Database (multi-region)

Optimizations:
  - TimescaleDB extension (time-series data, hypertables)
  - PgBouncer + PgPool-II (connection pooling + load balancing)
  - Distributed tables (projects, gates, evidence_vault)
```

---

## 7. Backup & Disaster Recovery

**Backup Strategy**:
| Type | Frequency | Retention | RTO | RPO |
|------|-----------|-----------|-----|-----|
| **Automated snapshots** | Daily (2 AM UTC) | 7 days | 4 hours | 24 hours |
| **Point-in-time recovery** | Continuous (WAL archiving) | 7 days | 1 hour | 5 minutes |
| **Manual backups** | Before major migrations | 30 days | 4 hours | N/A |
| **Offsite backups** (S3 Glacier) | Weekly | 7 years (compliance) | 24 hours | 7 days |

**Disaster Recovery Plan**:
```yaml
Scenario: Database Failure (AWS RDS outage)

1. Detection (5 min):
   - Alert: CloudWatch alarm (DB connection errors)
   - Verify: Attempt connection to read replica

2. Failover (10 min):
   - Promote read replica to primary (AWS RDS automatic failover)
   - Update DNS (CNAME: postgres.sdlc-orchestrator.com → replica endpoint)

3. Recovery (30 min):
   - Verify data integrity (row counts, hash checks)
   - Restore write traffic (application reconnects automatically)
   - Create new read replica (from promoted primary)

4. Post-Incident (1 week):
   - Postmortem: Why did primary fail?
   - Update runbook: Add automated failover test
   - Test restore from backup (quarterly drill)
```

---

## 8. Monitoring & Observability

**Metrics to Track**:
```yaml
Performance:
  - Query latency (p50, p95, p99): Target <50ms (p95)
  - Connection pool usage: Target <80% capacity
  - Cache hit ratio: Target >90%
  - Index usage: Target >80% (unused indexes = waste)

Reliability:
  - Database availability: Target 99.9% uptime
  - Replication lag: Target <1 second
  - Backup success rate: Target 100%

Capacity:
  - Disk usage: Alert at 70% full
  - CPU usage: Alert at 80%
  - Connection count: Alert at 90% of max
  - Row count growth: Forecast capacity needs
```

**Tools**:
- **Prometheus**: Scrape PostgreSQL metrics (postgres_exporter)
- **Grafana**: Dashboard (query latency, connection pool, cache hit ratio)
- **pgBadger**: Log analyzer (slow queries, connection errors)
- **pg_stat_statements**: Track query performance (built-in extension)

---

## 9. Security (Database Layer)

**Encryption**:
- ✅ **At rest**: AWS RDS encrypted volumes (AES-256)
- ✅ **In transit**: TLS 1.3 (mandatory, reject non-TLS connections)

**Row-Level Security (RLS)**:
```sql
-- Multi-tenant isolation (users can only see their org's data)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_tenant_isolation ON projects
  USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Application sets organization_id per request
-- SET LOCAL app.current_organization_id = 'org_123';
```

**Database Roles**:
```sql
-- Read-only role (for analytics, reporting)
CREATE ROLE readonly_user LOGIN PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE sdlc_orchestrator TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Application role (read-write, no DDL)
CREATE ROLE app_user LOGIN PASSWORD 'app_password';
GRANT CONNECT ON DATABASE sdlc_orchestrator TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Admin role (full access, migrations)
CREATE ROLE admin_user LOGIN PASSWORD 'admin_password';
GRANT ALL PRIVILEGES ON DATABASE sdlc_orchestrator TO admin_user;
```

---

## 10. References

- [ADR-001-Database-Choice.md](../02-System-Architecture/Architecture-Decisions/ADR-001-Database-Choice.md) - Why PostgreSQL
- [PostgreSQL 15.5 Documentation](https://www.postgresql.org/docs/15/)
- [pgvector Extension](https://github.com/pgvector/pgvector) - Vector similarity search
- [PgBouncer](https://www.pgbouncer.org/) - Connection pooling
- [Citus Extension](https://www.citusdata.com/) - Horizontal scaling
- [AWS RDS PostgreSQL Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

---

## 11. Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **Tech Lead** | [Tech Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Database Architect** | [DB Architect Name] | ✅ APPROVED | Nov 13, 2025 |
| **Backend Lead** | [Backend Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Last Updated**: November 13, 2025
**Status**: ✅ ACCEPTED - Binding database architecture
**Next Review**: Phase 2 (scaling to 1,000 teams, Year 2)
**Gate G2 Evidence**: `db_erd_link: present`
