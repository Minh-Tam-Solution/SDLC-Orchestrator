# ADR-001: Database Choice (PostgreSQL vs MongoDB)

**Status**: ✅ ACCEPTED
**Date**: November 13, 2025
**Deciders**: CTO, Tech Lead, Backend Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 4.9

---

## Context

SDLC Orchestrator requires a primary database to store:
- **Structured data**: Users, teams, projects, gates, approvals (relational)
- **Semi-structured data**: Gate policies (YAML), evidence metadata (JSON)
- **Audit logs**: Immutable logs for compliance (SOC 2, ISO 27001)
- **Vector embeddings**: AI-powered semantic search (future)

**Scale Requirements**:
- MVP: 100 teams, ~10K records
- Year 3: 1,000 teams, ~167M rows (see Data Model ERD)
- Query patterns: OLTP (transactional), some OLAP (reporting)

**Alternatives Considered**:
1. **PostgreSQL 15.5** (SQL, ACID, JSONB support)
2. **MongoDB 7.0** (NoSQL, document store, flexible schema)
3. **MySQL 8.0** (SQL, ACID, but weaker JSON support)

---

## Decision

**We choose PostgreSQL 15.5 as the primary database.**

---

## Rationale

### Why PostgreSQL?

**1. ACID Compliance (Critical)**
```sql
-- Gate approval requires multi-row transaction (atomic)
BEGIN;
  INSERT INTO gate_approvals (gate_id, user_id, status) VALUES ('G1', 'user123', 'approved');
  UPDATE gates SET status = 'PASS' WHERE id = 'G1' AND (
    SELECT COUNT(*) FROM gate_approvals WHERE gate_id = 'G1' AND status = 'approved'
  ) >= 2;  -- Requires 2+ approvals
COMMIT;
```

**Why ACID matters**:
- Gate approvals MUST be atomic (either all succeed or all fail)
- MongoDB's multi-document transactions (since 4.0) are slower and more complex
- PostgreSQL: 20+ years of ACID battle-testing

**2. JSONB Support (Flexible Schema Where Needed)**
```sql
-- Store gate policy (YAML converted to JSON) in JSONB column
CREATE TABLE policies (
  id UUID PRIMARY KEY,
  gate_id VARCHAR(10),
  policy JSONB,  -- Flexible schema
  created_at TIMESTAMP
);

-- Query policy by nested field (fast with GIN index)
SELECT * FROM policies WHERE policy @> '{"requires": {"openapi_lint": "PASS"}}';
```

**Why JSONB matters**:
- Best of both worlds: relational structure + flexible schema
- MongoDB-like queries (`@>`, `?`, `?&` operators)
- GIN index makes JSONB queries fast (not table scan)

**3. Full-Text Search + Vector Embeddings (pgvector)**
```sql
-- Install pgvector extension (AI-powered semantic search)
CREATE EXTENSION vector;

-- Store evidence embeddings (OpenAI Ada-002, 1536 dimensions)
CREATE TABLE evidence (
  id UUID PRIMARY KEY,
  title TEXT,
  description TEXT,
  embedding vector(1536),  -- Vector embedding
  created_at TIMESTAMP
);

-- Semantic search (find similar evidence)
SELECT id, title, 1 - (embedding <=> query_embedding) AS similarity
FROM evidence
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

**Why pgvector matters**:
- No separate vector database (Pinecone, Weaviate) needed
- Lower operational complexity (one database vs two)
- Cost savings ($0 vs $70/month for Pinecone starter)

**4. Battle-Tested (20+ Years)**
- PostgreSQL: Released 1996, used by: Apple, Netflix, Instagram, Spotify
- MongoDB: Released 2009, known issues: data loss (2013), replica lag
- MySQL: JSON support weaker than PostgreSQL (no GIN index for JSON)

**5. Horizontal Scalability (Citus Extension)**
```sql
-- Future: Shard PostgreSQL across multiple nodes (if >10M rows)
CREATE EXTENSION citus;

-- Distribute table by tenant_id (multi-tenant SaaS pattern)
SELECT create_distributed_table('projects', 'tenant_id');
```

**Why Citus matters**:
- Scales to billions of rows (same query API)
- No application code changes (transparent sharding)
- MongoDB sharding: complex, requires manual key management

---

### Why NOT MongoDB?

**Cons of MongoDB**:
1. ❌ **Weak ACID guarantees**: Multi-document transactions slower, more complex
2. ❌ **No vector search**: Requires separate Atlas Vector Search ($$$) or Pinecone
3. ❌ **Schema-less pain**: Easy to write, hard to maintain (data quality degrades over time)
4. ❌ **Vendor lock-in**: MongoDB Atlas pricing increases 10x after free tier
5. ❌ **Operational complexity**: Replica set configuration, sharding key management

**When MongoDB makes sense**:
- ✅ Pure document store (no relations, no transactions)
- ✅ Highly variable schema (different documents, different fields)
- ✅ Write-heavy workload (logs, events, time-series)

**SDLC Orchestrator is NOT a good fit**:
- We have clear relations (users → teams → projects → gates)
- We need ACID transactions (gate approvals, evidence linking)
- We need vector search (AI semantic search)

---

### Why NOT MySQL?

**Cons of MySQL**:
1. ❌ **Weaker JSON support**: No GIN index for JSON queries (table scan)
2. ❌ **No vector extension**: No pgvector equivalent
3. ❌ **Less PostgreSQL ecosystem**: Fewer extensions, tools, SaaS integrations

**When MySQL makes sense**:
- ✅ Simple CRUD (WordPress, Drupal)
- ✅ Read-heavy (replicas, no complex queries)
- ✅ Legacy systems (already using MySQL)

**SDLC Orchestrator needs**:
- Complex queries (joins, subqueries, CTEs)
- JSONB queries (gate policies, evidence metadata)
- Vector search (AI-powered semantic search)

---

## Consequences

### Positive

**1. Data Integrity (ACID)**
- ✅ Gate approvals are atomic (no partial approvals)
- ✅ Audit logs are consistent (no missing entries)
- ✅ Foreign keys enforce referential integrity (no orphaned records)

**2. Performance**
- ✅ JSONB queries fast (GIN index, not table scan)
- ✅ Vector search fast (pgvector index, not brute-force)
- ✅ Query planner mature (20+ years optimization)

**3. Cost Savings**
- ✅ No separate vector database ($0 vs $70/month Pinecone)
- ✅ No separate search engine ($0 vs $45/month Algolia)
- ✅ Self-hosted PostgreSQL = $20/month AWS RDS (vs $100+ MongoDB Atlas)

**4. Developer Experience**
- ✅ SQL is universal (easier to hire, easier to debug)
- ✅ Rich ecosystem (pgAdmin, DBeaver, Postico, DataGrip)
- ✅ ORM support (SQLAlchemy, Prisma, TypeORM)

**5. Future-Proof**
- ✅ Horizontal scaling (Citus extension)
- ✅ Read replicas (load balancing, HA)
- ✅ Partitioning (time-series data, audit logs)

### Negative

**1. Learning Curve (SQL)**
- ❌ Junior engineers may struggle with complex joins, CTEs
- **Mitigation**: ORM abstracts SQL (SQLAlchemy, Alembic migrations)

**2. Schema Migrations**
- ❌ Schema changes require migrations (ALTER TABLE, downtime)
- **Mitigation**: Alembic migrations (idempotent, backward-compatible)

**3. Write Scalability (Vertical Limit)**
- ❌ Single-node write limit (~10K TPS on AWS RDS db.r5.4xlarge)
- **Mitigation**: Defer sharding (Citus) until >10M rows (Year 5+)

**4. No Geo-Replication (Without Extension)**
- ❌ PostgreSQL native replication is async (eventual consistency)
- **Mitigation**: Use AWS Aurora Global Database (sync replication, 5 regions)

---

## Implementation Plan

### Phase 1: MVP (100 Teams) - Week 5-12
```yaml
Infrastructure:
  - AWS RDS PostgreSQL 15.5 (db.t3.medium, 2 vCPU, 4GB RAM)
  - Storage: 100GB SSD (gp3)
  - Backups: Automated daily snapshots (7-day retention)

Schema:
  - 16 tables (see Data Model ERD)
  - JSONB columns: policies.policy, evidence.metadata
  - Indexes: B-tree (primary keys), GIN (JSONB), BRIN (timestamps)

ORM:
  - SQLAlchemy 2.0 (async support)
  - Alembic (migrations, idempotent, backward-compatible)
```

### Phase 2: Scale (1,000 Teams) - Year 2-3
```yaml
Infrastructure:
  - AWS RDS PostgreSQL (db.r5.xlarge, 4 vCPU, 32GB RAM)
  - Storage: 1TB SSD (gp3)
  - Read replicas: 2x (load balancing, HA)

Optimizations:
  - Partitioning: audit_logs by month (BRIN index)
  - Caching: Redis (session, token blacklist, frequent queries)
  - Connection pooling: PgBouncer (1K connections → 100 DB connections)
```

### Phase 3: Enterprise (10K+ Teams) - Year 5+
```yaml
Infrastructure:
  - Citus (horizontal sharding by tenant_id)
  - 5 nodes (1 coordinator, 4 workers)
  - AWS Aurora Global Database (multi-region)

Optimizations:
  - TimescaleDB extension (time-series data, audit logs)
  - PgBouncer + PgPool-II (connection pooling + load balancing)
```

---

## Monitoring & Observability

**Metrics to Track**:
```yaml
Performance:
  - Query latency (p50, p95, p99): Target <50ms (p95)
  - Connection pool usage: Target <80% capacity
  - Cache hit ratio: Target >90%

Reliability:
  - Database availability: Target 99.9% uptime
  - Replication lag: Target <1 second
  - Backup success rate: Target 100%

Capacity:
  - Disk usage: Alert at 70% full
  - CPU usage: Alert at 80%
  - Connection count: Alert at 90% of max
```

**Tools**:
- **Prometheus**: Scrape PostgreSQL metrics (pg_exporter)
- **Grafana**: Dashboard (query latency, connection pool, cache hit ratio)
- **pgBadger**: Log analyzer (slow queries, connection errors)

---

## Alternatives Revisited

### Could We Switch Later?

**PostgreSQL → MongoDB** (Possible, Painful)
- Effort: 4-8 weeks (rewrite ORM, migrations, queries)
- Risk: Data migration errors, downtime
- **Mitigation**: Don't switch unless MongoDB solves a real problem (not hypothetical)

**PostgreSQL → MySQL** (Easy, But Why?)
- Effort: 1-2 weeks (SQL compatible, minor syntax changes)
- Risk: Lose JSONB, pgvector, Citus
- **Mitigation**: Don't switch (no benefit, only downsides)

**PostgreSQL + MongoDB** (Polyglot Persistence)
- Use PostgreSQL: Transactional data (users, teams, gates)
- Use MongoDB: Logs, events (high write volume)
- **Trade-off**: Operational complexity (2 databases vs 1)
- **Decision**: Defer until proven need (not premature optimization)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Write scalability limit** | Medium (Year 5+) | High | Citus sharding (proven at 1B+ rows) |
| **Complex query performance** | Low | Medium | Query optimization, indexes, EXPLAIN ANALYZE |
| **Data migration errors** | Low | Critical | Dry-run migrations, rollback plan, backups |
| **Vendor lock-in (AWS RDS)** | Low | Medium | PostgreSQL is open-source (portable) |

---

## References

- [PostgreSQL 15.5 Documentation](https://www.postgresql.org/docs/15/)
- [pgvector Extension](https://github.com/pgvector/pgvector) - Vector similarity search
- [Citus Extension](https://www.citusdata.com/) - Horizontal scaling
- [Data Model ERD v1.0](../../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md)
- [AWS RDS PostgreSQL Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

---

## Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **CTO** | [CTO Name] | ✅ APPROVED | Nov 13, 2025 |
| **Tech Lead** | [Tech Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Backend Lead** | [Backend Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Last Updated**: November 13, 2025
**Status**: ✅ ACCEPTED - Binding decision
**Next Review**: Year 2 (if scaling >1,000 teams)
