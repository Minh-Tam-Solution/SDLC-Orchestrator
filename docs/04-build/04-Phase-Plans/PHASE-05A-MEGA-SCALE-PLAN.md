# PHASE-05A-MEGA-SCALE-PLAN

## SOP Generator - Phase 5A Mega-Scale Implementation Plan

**Version**: 1.0.0
**Created**: 2026-07-07
**Status**: DRAFT
**Duration**: 16 weeks (Jul 7 - Oct 23, 2026)
**Budget**: $80,000
**Target**: 50 teams, 500 developers, Multi-Region HA, SOC 2 Certified

---

## Executive Summary

Phase 5A represents the transformational leap from enterprise (20 teams) to **organizational-wide deployment** (50 teams, 500 developers). Building on Phase 4's exceptional success (5/5 VCR, 782% ROI, 9.73/10 sprint quality), this phase introduces:

| Capability | Phase 4 | Phase 5A |
|------------|---------|----------|
| Teams | 20 | 50 (2.5x) |
| Developers | 180 | 500 (2.8x) |
| Regions | 1 (US-East) | 3 (US-East + US-West + EU-West) |
| Uptime SLA | 99.9% | 99.99% |
| Load Tested | 100K users | 500K users |
| SOC 2 | Ready | **Certified** |
| Team Structure | Flat | Hierarchy (4 levels) |
| Template Sharing | None | Marketplace |
| AI Recommendations | None | Context-aware suggestions |

---

## 16-Week Timeline Overview

```
Week 1-4:   Multi-Region Foundation
Week 5-8:   Hierarchy & Marketplace
Week 9-12:  AI & Integrations
Week 13-16: Scale & Certification
```

### Milestone Summary

| Week | Milestone | Key Deliverables | Success Criteria |
|------|-----------|------------------|------------------|
| 4 | Multi-Region Live | 3 regions, CockroachDB, GeoDNS | <50ms intra-region latency |
| 8 | Marketplace Launch | Hierarchy, Marketplace, Search | 50% teams in hierarchy |
| 12 | AI Features Complete | Recommendations, Bulk Import | ≥30% CTR on recommendations |
| 16 | Phase Complete | SOC 2 Certified, 500K load test | 5/5 VCR, 4 LPS proofs |

---

## Phase 5A - Weeks 1-4: Multi-Region Foundation

### Week 1: CockroachDB Migration & Region Setup

**Theme**: Database Foundation for Multi-Region

**Day 1-2: CockroachDB Cluster Deployment**

```yaml
tasks:
  - task: "Deploy CockroachDB 3-node cluster (US-East)"
    owner: "DevOps Lead"
    deliverables:
      - Kubernetes StatefulSet for CockroachDB
      - 3 nodes with NVMe storage
      - Automated backup to S3
    code_sample: |
      # cockroachdb-cluster.yaml
      apiVersion: crdb.cockroachlabs.com/v1alpha1
      kind: CrdbCluster
      metadata:
        name: sop-generator-crdb
        namespace: sop-generator
      spec:
        nodes: 3
        image:
          name: cockroachdb/cockroach:v23.1.8
        resources:
          requests:
            cpu: "4"
            memory: "16Gi"
          limits:
            cpu: "8"
            memory: "32Gi"
        dataStore:
          pvc:
            spec:
              storageClassName: premium-nvme
              resources:
                requests:
                  storage: "500Gi"
        localities:
          - region: us-east-1
            zone: us-east-1a
          - region: us-east-1
            zone: us-east-1b
          - region: us-east-1
            zone: us-east-1c

  - task: "Create geo-partitioned schema"
    owner: "Backend Lead"
    deliverables:
      - Tables with locality constraints
      - EU data residency for PII
    code_sample: |
      -- Geo-partitioned users table
      CREATE TABLE users (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          email STRING NOT NULL,
          data_region STRING NOT NULL DEFAULT 'us-east',
          created_at TIMESTAMPTZ DEFAULT now(),
          INDEX idx_users_region (data_region)
      ) PARTITION BY LIST (data_region) (
          PARTITION us_east VALUES IN ('us-east'),
          PARTITION us_west VALUES IN ('us-west'),
          PARTITION eu_west VALUES IN ('eu-west')
      );

      -- Configure zone for EU data residency (GDPR)
      ALTER PARTITION eu_west OF TABLE users
      CONFIGURE ZONE USING constraints = '[+region=eu-west-1]';
```

**Day 3-4: PostgreSQL → CockroachDB Migration**

```yaml
tasks:
  - task: "Dual-write migration strategy"
    owner: "Backend Lead"
    deliverables:
      - Migration script with rollback
      - Data validation checksums
    code_sample: |
      # migration_service.py
      from typing import Dict, Any
      import hashlib
      import asyncio
      from sqlalchemy.ext.asyncio import create_async_engine

      class DualWriteMigration:
          """
          Dual-write strategy: Write to both PostgreSQL and CockroachDB
          during migration period. Validate consistency before cutover.
          """

          def __init__(self, pg_url: str, crdb_url: str):
              self.pg_engine = create_async_engine(pg_url)
              self.crdb_engine = create_async_engine(crdb_url)
              self.validation_errors: list[str] = []

          async def migrate_table(self, table_name: str, batch_size: int = 1000) -> Dict[str, Any]:
              """Migrate single table with checksum validation."""
              stats = {"rows_migrated": 0, "checksum_match": False}

              # Read from PostgreSQL in batches
              async with self.pg_engine.connect() as pg_conn:
                  offset = 0
                  while True:
                      result = await pg_conn.execute(
                          f"SELECT * FROM {table_name} ORDER BY id LIMIT {batch_size} OFFSET {offset}"
                      )
                      rows = result.fetchall()
                      if not rows:
                          break

                      # Write to CockroachDB
                      async with self.crdb_engine.connect() as crdb_conn:
                          for row in rows:
                              await crdb_conn.execute(
                                  f"UPSERT INTO {table_name} VALUES ({','.join(['$' + str(i+1) for i in range(len(row))])})",
                                  *row
                              )
                          await crdb_conn.commit()

                      stats["rows_migrated"] += len(rows)
                      offset += batch_size

              # Validate checksum
              pg_checksum = await self._table_checksum(self.pg_engine, table_name)
              crdb_checksum = await self._table_checksum(self.crdb_engine, table_name)
              stats["checksum_match"] = pg_checksum == crdb_checksum

              if not stats["checksum_match"]:
                  self.validation_errors.append(f"{table_name}: checksum mismatch")

              return stats

          async def _table_checksum(self, engine, table_name: str) -> str:
              """Calculate MD5 checksum of table data."""
              async with engine.connect() as conn:
                  result = await conn.execute(
                      f"SELECT MD5(STRING_AGG(CAST(t.* AS TEXT), '')) FROM {table_name} t"
                  )
                  return result.scalar()

          async def validate_migration(self) -> bool:
              """Final validation before cutover."""
              return len(self.validation_errors) == 0
```

**Day 5: Region 2 (US-West) Deployment**

```yaml
tasks:
  - task: "Deploy US-West Kubernetes cluster"
    owner: "DevOps Lead"
    deliverables:
      - EKS cluster in us-west-2
      - CockroachDB nodes joined to cluster
      - Cross-region networking (VPC peering)
    verification:
      - "kubectl get nodes --context=us-west-2"
      - "cockroach node status --host=crdb-us-west:26257"
```

**Success Criteria Week 1:**
- CockroachDB cluster operational (3 regions planned, 2 deployed)
- Migration script tested on staging
- <10ms read latency intra-region
- Data checksums validated

---

### Week 2: Multi-Region Networking & Early Load Test

**Theme**: Global Infrastructure & Performance Validation

**Day 1-2: EU-West Region Deployment**

```yaml
tasks:
  - task: "Deploy EU-West Kubernetes cluster"
    owner: "DevOps Lead"
    deliverables:
      - EKS cluster in eu-west-1
      - CockroachDB nodes with EU locality
      - GDPR-compliant configuration
    code_sample: |
      # EU region specific constraints
      ALTER DATABASE sop_generator
      CONFIGURE ZONE USING constraints = '{"+region=eu-west-1": 1}';

      -- EU user data stays in EU
      ALTER PARTITION eu_west OF TABLE users
      CONFIGURE ZONE USING
        constraints = '[+region=eu-west-1]',
        lease_preferences = '[[+region=eu-west-1]]';

  - task: "Cross-region VPC peering"
    owner: "DevOps Lead"
    deliverables:
      - VPC peering: US-East ↔ US-West ↔ EU-West
      - Private DNS resolution
      - Security groups for CockroachDB traffic
```

**Day 3-4: GeoDNS & CDN Setup**

```yaml
tasks:
  - task: "Configure Route 53 GeoDNS"
    owner: "DevOps Lead"
    deliverables:
      - Geolocation routing policy
      - Health checks per region
      - Failover configuration
    code_sample: |
      # terraform/route53.tf
      resource "aws_route53_health_check" "us_east" {
        fqdn              = "api-us-east.sop-generator.internal"
        port              = 443
        type              = "HTTPS"
        resource_path     = "/health"
        failure_threshold = "3"
        request_interval  = "30"
      }

      resource "aws_route53_record" "api_geo" {
        zone_id = aws_route53_zone.main.zone_id
        name    = "api.sop-generator.com"
        type    = "A"

        set_identifier = "us-east"
        geolocation_routing_policy {
          continent = "NA"
        }

        alias {
          name                   = aws_lb.us_east.dns_name
          zone_id                = aws_lb.us_east.zone_id
          evaluate_target_health = true
        }
      }

      resource "aws_route53_record" "api_geo_eu" {
        zone_id = aws_route53_zone.main.zone_id
        name    = "api.sop-generator.com"
        type    = "A"

        set_identifier = "eu-west"
        geolocation_routing_policy {
          continent = "EU"
        }

        alias {
          name                   = aws_lb.eu_west.dns_name
          zone_id                = aws_lb.eu_west.zone_id
          evaluate_target_health = true
        }
      }

  - task: "CloudFront CDN configuration"
    owner: "DevOps Lead"
    deliverables:
      - CloudFront distribution for static assets
      - Edge caching (1 hour TTL)
      - Origin failover
```

**Day 5: Early Load Test (500K Baseline)**

```yaml
tasks:
  - task: "500K load test - baseline"
    owner: "QA Lead"
    deliverables:
      - Locust test scenarios
      - Baseline performance metrics
      - Bottleneck identification
    code_sample: |
      # locustfile.py
      from locust import HttpUser, task, between
      import random

      class SOPGeneratorUser(HttpUser):
          wait_time = between(1, 3)
          host = "https://api.sop-generator.com"

          def on_start(self):
              # Authenticate
              response = self.client.post("/api/v1/auth/login", json={
                  "username": f"loadtest_user_{random.randint(1, 10000)}",
                  "password": "loadtest_password"
              })
              self.token = response.json().get("access_token")
              self.headers = {"Authorization": f"Bearer {self.token}"}

          @task(10)
          def browse_sops(self):
              """Most common: Browse SOPs (read-heavy)"""
              self.client.get("/api/v1/sops", headers=self.headers)

          @task(5)
          def search_sops(self):
              """Search SOPs"""
              queries = ["deployment", "rollback", "database", "api", "security"]
              self.client.get(
                  f"/api/v1/sops/search?q={random.choice(queries)}",
                  headers=self.headers
              )

          @task(2)
          def view_sop(self):
              """View single SOP"""
              sop_id = random.randint(1, 700)
              self.client.get(f"/api/v1/sops/{sop_id}", headers=self.headers)

          @task(1)
          def create_sop(self):
              """Create SOP (write-heavy)"""
              self.client.post("/api/v1/sops", headers=self.headers, json={
                  "title": f"Load Test SOP {random.randint(1, 100000)}",
                  "type": "DEPLOYMENT",
                  "content": "This is a load test SOP content..."
              })

      # Run: locust -f locustfile.py --users 500000 --spawn-rate 1000 --run-time 30m
    results_expected:
      - "Identify bottlenecks (target: p95 <100ms)"
      - "Document scaling requirements"
      - "Create optimization backlog"
```

**Success Criteria Week 2:**
- 3 regions operational (US-East, US-West, EU-West)
- GeoDNS routing validated
- 500K load test baseline completed
- Cross-region latency measured (<150ms target)

---

### Week 3: Multi-Region API & Application Deployment

**Theme**: Application Layer Multi-Region

**Day 1-2: Multi-Region Backend Deployment**

```yaml
tasks:
  - task: "Deploy backend to all 3 regions"
    owner: "Backend Lead"
    deliverables:
      - Kubernetes Deployments per region
      - Region-aware configuration
      - Cross-region service mesh
    code_sample: |
      # backend/config/multi_region.py
      from pydantic_settings import BaseSettings
      from enum import Enum

      class Region(str, Enum):
          US_EAST = "us-east-1"
          US_WEST = "us-west-2"
          EU_WEST = "eu-west-1"

      class MultiRegionSettings(BaseSettings):
          """Region-aware application settings."""

          current_region: Region = Region.US_EAST
          crdb_connection_string: str
          redis_cluster_nodes: list[str]

          # Cross-region configuration
          peer_regions: list[Region] = []
          replication_lag_threshold_ms: int = 1000

          @property
          def is_primary_region(self) -> bool:
              return self.current_region == Region.US_EAST

          @property
          def local_cache_prefix(self) -> str:
              return f"cache:{self.current_region.value}:"

          class Config:
              env_prefix = "SOP_"

      # Region-aware database router
      class RegionAwareDBRouter:
          """Route queries to appropriate database based on data locality."""

          def __init__(self, settings: MultiRegionSettings):
              self.settings = settings
              self.region = settings.current_region

          async def get_connection(self, data_region: Region | None = None):
              """Get connection with optional data locality preference."""
              if data_region and data_region != self.region:
                  # Cross-region read - use follower read for freshness
                  return await self._get_follower_read_connection(data_region)
              return await self._get_local_connection()

          async def _get_local_connection(self):
              """Get connection to local region."""
              return await asyncpg.connect(self.settings.crdb_connection_string)

          async def _get_follower_read_connection(self, target_region: Region):
              """Get connection with follower read for cross-region queries."""
              conn = await self._get_local_connection()
              # CockroachDB follower read with bounded staleness
              await conn.execute(
                  "SET CLUSTER SETTING kv.follower_read.target_duration = '1s'"
              )
              return conn

  - task: "Region health endpoint"
    owner: "Backend Lead"
    deliverables:
      - /health/region endpoint
      - Cross-region health aggregation
    code_sample: |
      # backend/routers/health.py
      from fastapi import APIRouter, HTTPException
      from datetime import datetime
      import asyncio

      router = APIRouter(prefix="/health", tags=["Health"])

      @router.get("/region")
      async def region_health():
          """Health check with region-specific information."""
          settings = get_settings()
          health_data = {
              "region": settings.current_region.value,
              "timestamp": datetime.utcnow().isoformat(),
              "status": "healthy",
              "checks": {}
          }

          # Check local database
          try:
              start = datetime.utcnow()
              async with get_db_connection() as conn:
                  await conn.execute("SELECT 1")
              latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
              health_data["checks"]["database"] = {
                  "status": "healthy",
                  "latency_ms": round(latency_ms, 2)
              }
          except Exception as e:
              health_data["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
              health_data["status"] = "degraded"

          # Check local Redis
          try:
              start = datetime.utcnow()
              redis = await get_redis()
              await redis.ping()
              latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
              health_data["checks"]["redis"] = {
                  "status": "healthy",
                  "latency_ms": round(latency_ms, 2)
              }
          except Exception as e:
              health_data["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
              health_data["status"] = "degraded"

          # Check peer regions (async, non-blocking)
          if settings.peer_regions:
              health_data["peer_regions"] = await check_peer_regions(settings.peer_regions)

          return health_data

      async def check_peer_regions(peer_regions: list) -> dict:
          """Check health of peer regions (with timeout)."""
          results = {}
          async def check_region(region):
              try:
                  async with httpx.AsyncClient(timeout=2.0) as client:
                      resp = await client.get(
                          f"https://api-{region.value}.sop-generator.internal/health"
                      )
                      return region.value, {"status": "reachable", "latency_ms": resp.elapsed.total_seconds() * 1000}
              except Exception as e:
                  return region.value, {"status": "unreachable", "error": str(e)}

          checks = await asyncio.gather(*[check_region(r) for r in peer_regions])
          return dict(checks)
```

**Day 3-4: Frontend Multi-Region Deployment**

```yaml
tasks:
  - task: "Deploy frontend to CloudFront"
    owner: "Frontend Lead"
    deliverables:
      - Static assets on S3 (per region)
      - CloudFront distribution
      - Region-aware API client
    code_sample: |
      // frontend/src/lib/api-client.ts
      import { Region } from '@/types/region';

      interface RegionConfig {
        apiUrl: string;
        wsUrl: string;
      }

      const REGION_CONFIGS: Record<Region, RegionConfig> = {
        'us-east-1': {
          apiUrl: 'https://api-us-east.sop-generator.com',
          wsUrl: 'wss://ws-us-east.sop-generator.com',
        },
        'us-west-2': {
          apiUrl: 'https://api-us-west.sop-generator.com',
          wsUrl: 'wss://ws-us-west.sop-generator.com',
        },
        'eu-west-1': {
          apiUrl: 'https://api-eu-west.sop-generator.com',
          wsUrl: 'wss://ws-eu-west.sop-generator.com',
        },
      };

      export class RegionAwareApiClient {
        private region: Region;
        private config: RegionConfig;

        constructor() {
          this.region = this.detectRegion();
          this.config = REGION_CONFIGS[this.region];
        }

        private detectRegion(): Region {
          // Check user preference first
          const savedRegion = localStorage.getItem('preferred_region');
          if (savedRegion && savedRegion in REGION_CONFIGS) {
            return savedRegion as Region;
          }

          // Auto-detect based on timezone
          const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
          if (timezone.startsWith('Europe/')) return 'eu-west-1';
          if (timezone.startsWith('America/Los_Angeles') || timezone.startsWith('America/Denver')) {
            return 'us-west-2';
          }
          return 'us-east-1'; // Default
        }

        async fetch<T>(path: string, options?: RequestInit): Promise<T> {
          const url = `${this.config.apiUrl}${path}`;
          const response = await fetch(url, {
            ...options,
            headers: {
              'Content-Type': 'application/json',
              'X-Client-Region': this.region,
              ...options?.headers,
            },
          });

          if (!response.ok) {
            throw new ApiError(response.status, await response.text());
          }

          return response.json();
        }

        getWebSocketUrl(path: string): string {
          return `${this.config.wsUrl}${path}`;
        }

        getCurrentRegion(): Region {
          return this.region;
        }

        setRegion(region: Region): void {
          this.region = region;
          this.config = REGION_CONFIGS[region];
          localStorage.setItem('preferred_region', region);
        }
      }

      export const apiClient = new RegionAwareApiClient();
```

**Day 5: Region Failover Testing**

```yaml
tasks:
  - task: "Chaos engineering - region failover"
    owner: "DevOps Lead"
    deliverables:
      - Failover runbook
      - Recovery time validation (<30s)
      - Data consistency validation
    test_scenarios:
      - scenario: "Kill US-East region"
        steps:
          - "Scale down US-East pods to 0"
          - "Verify Route 53 health check fails"
          - "Verify traffic routes to US-West"
          - "Measure failover time"
        expected_result: "Failover <30s, 0 requests lost"

      - scenario: "Database primary failover"
        steps:
          - "Kill CockroachDB leader node"
          - "Verify automatic leader election"
          - "Verify write availability"
        expected_result: "Failover <10s, 0 data loss"
```

**Success Criteria Week 3:**
- Backend deployed to 3 regions
- Frontend on CloudFront (global edge)
- Region failover tested (<30s)
- Health endpoints operational

---

### Week 4: Production Cutover & Week 1-4 Review

**Theme**: Production Migration & Validation

**Day 1-2: Production Database Cutover**

```yaml
tasks:
  - task: "PostgreSQL → CockroachDB production cutover"
    owner: "Backend Lead + DevOps Lead"
    deliverables:
      - Zero-downtime migration
      - Rollback validation
      - Performance comparison
    procedure:
      - step: 1
        action: "Enable dual-write (PostgreSQL + CockroachDB)"
        validation: "Both databases receiving writes"
      - step: 2
        action: "Switch reads to CockroachDB"
        validation: "All reads from CockroachDB, writes dual"
      - step: 3
        action: "Disable PostgreSQL writes"
        validation: "CockroachDB only"
      - step: 4
        action: "Monitor for 24 hours"
        validation: "No errors, latency within budget"
      - step: 5
        action: "Decommission PostgreSQL (Week 8)"
        validation: "PostgreSQL kept as backup for 4 weeks"
```

**Day 3-4: Multi-Region Production Validation**

```yaml
tasks:
  - task: "Production smoke tests - all regions"
    owner: "QA Lead"
    deliverables:
      - E2E tests from each region
      - Cross-region data consistency test
      - Latency validation
    tests:
      - name: "Create SOP in US-East, read in EU-West"
        expected: "Visible in <1s (eventual consistency)"
      - name: "User in EU creates account"
        expected: "Data stored in EU-West region"
      - name: "Cross-region collaboration"
        expected: "Real-time edits visible <500ms"
```

**Day 5: Week 1-4 Review & MRP Evidence Collection**

```yaml
review:
  sprint_rating_target: "9.5/10"
  deliverables_checklist:
    - "3 Kubernetes clusters operational"
    - "CockroachDB multi-region cluster"
    - "GeoDNS routing validated"
    - "500K load test baseline"
    - "Region failover <30s"
    - "Production cutover complete"

  metrics_collected:
    - "Intra-region latency: <50ms"
    - "Cross-region latency: <150ms"
    - "Database migration: 0 data loss"
    - "Failover time: <30s"

  evidence_for_mrp:
    - "Load test report (500K baseline)"
    - "CockroachDB cluster status"
    - "Failover test recordings"
    - "Latency measurements (Prometheus)"
```

---

## Phase 5A - Weeks 5-8: Hierarchy & Marketplace

### Week 5: Team Hierarchy Implementation

**Theme**: Organizational Structure at Scale

**Day 1-3: Hierarchy Backend**

```yaml
tasks:
  - task: "Implement team hierarchy (FR27)"
    owner: "Backend Lead"
    deliverables:
      - team_hierarchy table with ltree
      - Permission inheritance logic
      - Hierarchy API endpoints
    code_sample: |
      # backend/models/team_hierarchy.py
      from sqlalchemy import Column, String, ForeignKey, Index
      from sqlalchemy.dialects.postgresql import LTREE
      from sqlalchemy.orm import relationship
      import uuid

      class TeamHierarchy(Base):
          """
          Team hierarchy with closure table pattern.
          Path format: engineering.platform.api.auth
          """
          __tablename__ = "team_hierarchy"

          id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
          name = Column(String(100), nullable=False)
          parent_id = Column(String, ForeignKey("team_hierarchy.id"), nullable=True)
          path = Column(LTREE, nullable=False)  # e.g., 'engineering.platform.api'
          level = Column(Integer, nullable=False)  # 1=BU, 2=Dept, 3=Team, 4=Sub-team
          metadata_ = Column(JSONB, default={})

          # Relationships
          parent = relationship("TeamHierarchy", remote_side=[id], backref="children")
          permissions = relationship("TeamPermission", back_populates="team")

          __table_args__ = (
              Index("idx_team_path_gist", path, postgresql_using="gist"),
              Index("idx_team_parent", parent_id),
          )

          @classmethod
          async def get_ancestors(cls, session, team_id: str) -> list["TeamHierarchy"]:
              """Get all ancestor teams (for permission inheritance)."""
              team = await session.get(cls, team_id)
              if not team:
                  return []

              # Use ltree @> operator for ancestor query
              result = await session.execute(
                  select(cls).where(text(f"path @> '{team.path}'")).order_by(cls.level)
              )
              return result.scalars().all()

          @classmethod
          async def get_descendants(cls, session, team_id: str) -> list["TeamHierarchy"]:
              """Get all descendant teams."""
              team = await session.get(cls, team_id)
              if not team:
                  return []

              result = await session.execute(
                  select(cls).where(text(f"'{team.path}' @> path")).order_by(cls.level)
              )
              return result.scalars().all()

      class TeamPermission(Base):
          """Permission assignment with inheritance support."""
          __tablename__ = "team_permissions"

          id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
          team_id = Column(String, ForeignKey("team_hierarchy.id"), nullable=False)
          permission = Column(String(50), nullable=False)  # e.g., 'sops.write'
          inherited_from = Column(String, ForeignKey("team_hierarchy.id"), nullable=True)
          is_override = Column(Boolean, default=False)
          granted_at = Column(DateTime, default=datetime.utcnow)
          granted_by = Column(String, ForeignKey("users.id"), nullable=False)

          team = relationship("TeamHierarchy", foreign_keys=[team_id])

      # Permission inheritance service
      class PermissionInheritanceService:
          """Calculate effective permissions with inheritance."""

          async def get_effective_permissions(
              self, session, team_id: str, user_id: str
          ) -> set[str]:
              """Get all permissions for user in team (including inherited)."""
              permissions = set()

              # Get team ancestors (for inheritance)
              ancestors = await TeamHierarchy.get_ancestors(session, team_id)

              for ancestor in ancestors:
                  # Get permissions for this level
                  result = await session.execute(
                      select(TeamPermission)
                      .where(TeamPermission.team_id == ancestor.id)
                      .where(TeamPermission.is_override == False)
                  )
                  for perm in result.scalars():
                      permissions.add(perm.permission)

              # Get override permissions for target team
              result = await session.execute(
                  select(TeamPermission)
                  .where(TeamPermission.team_id == team_id)
                  .where(TeamPermission.is_override == True)
              )
              for perm in result.scalars():
                  if perm.permission.startswith("-"):
                      # Negative override (remove permission)
                      permissions.discard(perm.permission[1:])
                  else:
                      permissions.add(perm.permission)

              return permissions
```

**Day 4-5: Hierarchy Frontend**

```yaml
tasks:
  - task: "Team hierarchy UI"
    owner: "Frontend Lead"
    deliverables:
      - Tree view component (react-arborist)
      - Drag-and-drop reorganization
      - Permission management modal
    code_sample: |
      // frontend/src/components/TeamHierarchy/TeamTree.tsx
      import { Tree, NodeApi } from 'react-arborist';
      import { TeamNode } from '@/types/team';
      import { useTeamHierarchy, useMoveTeam } from '@/hooks/useTeams';

      interface TeamTreeProps {
        onSelectTeam: (team: TeamNode) => void;
      }

      export function TeamTree({ onSelectTeam }: TeamTreeProps) {
        const { data: hierarchy, isLoading } = useTeamHierarchy();
        const moveTeam = useMoveTeam();

        const handleMove = async ({
          dragIds,
          parentId,
          index,
        }: {
          dragIds: string[];
          parentId: string | null;
          index: number;
        }) => {
          const teamId = dragIds[0];
          await moveTeam.mutateAsync({
            teamId,
            newParentId: parentId,
            position: index,
          });
        };

        if (isLoading) return <TreeSkeleton />;

        return (
          <div className="h-full overflow-auto">
            <Tree
              data={hierarchy}
              openByDefault={true}
              width="100%"
              height={600}
              indent={24}
              rowHeight={36}
              onMove={handleMove}
              onSelect={(nodes) => {
                if (nodes.length > 0) {
                  onSelectTeam(nodes[0].data);
                }
              }}
            >
              {Node}
            </Tree>
          </div>
        );
      }

      function Node({ node, style, dragHandle }: NodeRendererProps<TeamNode>) {
        const levelIcons = ['building', 'folder', 'users', 'user'];
        const levelColors = ['text-blue-600', 'text-green-600', 'text-purple-600', 'text-gray-600'];

        return (
          <div
            ref={dragHandle}
            style={style}
            className={cn(
              'flex items-center gap-2 px-2 py-1 rounded cursor-pointer',
              node.isSelected && 'bg-blue-100',
              'hover:bg-gray-100'
            )}
            onClick={() => node.select()}
          >
            <button onClick={() => node.toggle()}>
              {node.isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
            <Icon
              name={levelIcons[node.data.level - 1] || 'users'}
              className={levelColors[node.data.level - 1]}
              size={16}
            />
            <span className="flex-1 truncate">{node.data.name}</span>
            <Badge variant="outline">{node.data.memberCount} members</Badge>
          </div>
        );
      }
```

---

### Week 6: Template Marketplace Foundation

**Theme**: Knowledge Sharing at Scale

**Day 1-3: Marketplace Backend**

```yaml
tasks:
  - task: "Implement marketplace (FR28)"
    owner: "Backend Lead"
    deliverables:
      - marketplace_templates table
      - Publishing workflow
      - Search with PostgreSQL FTS
    code_sample: |
      # backend/services/marketplace_service.py
      from sqlalchemy import select, func
      from sqlalchemy.dialects.postgresql import TSVECTOR

      class MarketplaceService:
          """Service for SOP template marketplace."""

          async def publish_template(
              self,
              session,
              sop_id: str,
              author_id: str,
              title: str,
              description: str,
              tags: list[str],
              category: str,
          ) -> MarketplaceTemplate:
              """Publish SOP as marketplace template."""
              # Get original SOP
              sop = await session.get(SOP, sop_id)
              if not sop:
                  raise NotFoundException(f"SOP {sop_id} not found")

              # Create marketplace entry
              template = MarketplaceTemplate(
                  sop_id=sop_id,
                  title=title,
                  description=description,
                  tags=tags,
                  category=category,
                  author_id=author_id,
                  author_team_id=sop.team_id,
                  version="1.0.0",
                  content_snapshot=sop.content,  # Snapshot at publish time
                  search_vector=func.to_tsvector(
                      'english',
                      f"{title} {description} {' '.join(tags)}"
                  ),
              )

              session.add(template)
              await session.commit()
              return template

          async def search_templates(
              self,
              session,
              query: str | None = None,
              category: str | None = None,
              tags: list[str] | None = None,
              sort_by: str = "downloads",
              limit: int = 20,
              offset: int = 0,
          ) -> tuple[list[MarketplaceTemplate], int]:
              """Search marketplace templates with filters."""
              stmt = select(MarketplaceTemplate)

              # Full-text search
              if query:
                  stmt = stmt.where(
                      MarketplaceTemplate.search_vector.match(query)
                  )

              # Category filter
              if category:
                  stmt = stmt.where(MarketplaceTemplate.category == category)

              # Tags filter (ANY match)
              if tags:
                  stmt = stmt.where(
                      MarketplaceTemplate.tags.overlap(tags)
                  )

              # Count total
              count_stmt = select(func.count()).select_from(stmt.subquery())
              total = await session.scalar(count_stmt)

              # Sort
              if sort_by == "downloads":
                  stmt = stmt.order_by(MarketplaceTemplate.downloads.desc())
              elif sort_by == "rating":
                  stmt = stmt.order_by(MarketplaceTemplate.avg_rating.desc())
              elif sort_by == "recent":
                  stmt = stmt.order_by(MarketplaceTemplate.published_at.desc())

              # Pagination
              stmt = stmt.limit(limit).offset(offset)

              result = await session.execute(stmt)
              return result.scalars().all(), total

          async def install_template(
              self,
              session,
              template_id: str,
              team_id: str,
              installed_by: str,
          ) -> SOP:
              """Fork template to team's SOPs."""
              template = await session.get(MarketplaceTemplate, template_id)
              if not template:
                  raise NotFoundException(f"Template {template_id} not found")

              # Create SOP from template
              sop = SOP(
                  title=f"{template.title} (from Marketplace)",
                  content=template.content_snapshot,
                  type=template.original_type,
                  team_id=team_id,
                  created_by=installed_by,
                  metadata_={
                      "forked_from": {
                          "template_id": template_id,
                          "template_version": template.version,
                          "original_author": template.author_id,
                      }
                  },
              )
              session.add(sop)

              # Record install
              install = MarketplaceInstall(
                  template_id=template_id,
                  team_id=team_id,
                  installed_by=installed_by,
                  synced_version=template.version,
              )
              session.add(install)

              # Increment download count
              template.downloads += 1

              await session.commit()
              return sop
```

**Day 4-5: Marketplace Frontend**

```yaml
tasks:
  - task: "Marketplace UI"
    owner: "Frontend Lead"
    deliverables:
      - Marketplace browse page
      - Template detail modal
      - Publish workflow
    code_sample: |
      // frontend/src/pages/Marketplace/MarketplacePage.tsx
      import { useState } from 'react';
      import { useMarketplaceTemplates, useInstallTemplate } from '@/hooks/useMarketplace';
      import { TemplateCard } from './TemplateCard';
      import { MarketplaceFilters } from './MarketplaceFilters';

      const CATEGORIES = [
        { value: 'deployment', label: 'Deployment' },
        { value: 'troubleshooting', label: 'Troubleshooting' },
        { value: 'security', label: 'Security' },
        { value: 'database', label: 'Database' },
        { value: 'monitoring', label: 'Monitoring' },
      ];

      export function MarketplacePage() {
        const [filters, setFilters] = useState({
          query: '',
          category: null,
          tags: [],
          sortBy: 'downloads',
        });

        const { data, isLoading, fetchNextPage, hasNextPage } = useMarketplaceTemplates(filters);
        const installTemplate = useInstallTemplate();

        const handleInstall = async (templateId: string) => {
          await installTemplate.mutateAsync({
            templateId,
            teamId: currentTeam.id,
          });
          toast.success('Template installed successfully!');
        };

        return (
          <div className="container mx-auto py-8">
            <div className="mb-8">
              <h1 className="text-3xl font-bold mb-2">Template Marketplace</h1>
              <p className="text-muted-foreground">
                Discover and install SOP templates shared by teams across the organization.
              </p>
            </div>

            <div className="flex gap-8">
              {/* Filters Sidebar */}
              <div className="w-64 flex-shrink-0">
                <MarketplaceFilters
                  filters={filters}
                  onChange={setFilters}
                  categories={CATEGORIES}
                />
              </div>

              {/* Template Grid */}
              <div className="flex-1">
                {isLoading ? (
                  <TemplateGridSkeleton />
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {data?.pages.flatMap((page) =>
                        page.templates.map((template) => (
                          <TemplateCard
                            key={template.id}
                            template={template}
                            onInstall={() => handleInstall(template.id)}
                          />
                        ))
                      )}
                    </div>

                    {hasNextPage && (
                      <Button
                        variant="outline"
                        className="mt-8 w-full"
                        onClick={() => fetchNextPage()}
                      >
                        Load More
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        );
      }
```

---

### Week 7: Advanced Search & Rate Limiting

**Theme**: Performance at Scale

**Day 1-3: Advanced Search (FR31)**

```yaml
tasks:
  - task: "Implement advanced search"
    owner: "Backend Lead"
    deliverables:
      - Full-text search with highlights
      - Faceted search
      - Saved searches
    code_sample: |
      # backend/services/search_service.py
      class SOPSearchService:
          """Advanced SOP search with facets and highlights."""

          async def search(
              self,
              session,
              query: str,
              filters: SearchFilters,
              user: User,
              limit: int = 20,
              offset: int = 0,
          ) -> SearchResult:
              """Full-text search with facets and highlights."""

              # Build base query
              stmt = select(SOP)

              # Apply hierarchy filter (user's accessible teams)
              accessible_teams = await self._get_accessible_teams(session, user)
              stmt = stmt.where(SOP.team_id.in_(accessible_teams))

              # Full-text search
              if query:
                  stmt = stmt.where(
                      SOP.search_vector.match(query)
                  ).order_by(
                      func.ts_rank(SOP.search_vector, func.plainto_tsquery(query)).desc()
                  )

              # Apply filters
              if filters.team_ids:
                  stmt = stmt.where(SOP.team_id.in_(filters.team_ids))
              if filters.types:
                  stmt = stmt.where(SOP.type.in_(filters.types))
              if filters.authors:
                  stmt = stmt.where(SOP.created_by.in_(filters.authors))
              if filters.date_from:
                  stmt = stmt.where(SOP.created_at >= filters.date_from)
              if filters.date_to:
                  stmt = stmt.where(SOP.created_at <= filters.date_to)

              # Get results with highlights
              results = await self._execute_with_highlights(session, stmt, query, limit, offset)

              # Get facets (parallel queries)
              facets = await self._get_facets(session, stmt)

              return SearchResult(
                  results=results,
                  facets=facets,
                  total=len(results),
                  query=query,
                  filters=filters,
              )

          async def _execute_with_highlights(
              self, session, stmt, query: str, limit: int, offset: int
          ) -> list[SOPSearchResult]:
              """Execute search with highlighted snippets."""
              stmt = stmt.add_columns(
                  func.ts_headline(
                      'english',
                      SOP.content,
                      func.plainto_tsquery(query),
                      'StartSel=<mark>, StopSel=</mark>, MaxWords=50'
                  ).label('highlight')
              ).limit(limit).offset(offset)

              result = await session.execute(stmt)
              return [
                  SOPSearchResult(sop=row.SOP, highlight=row.highlight)
                  for row in result
              ]

          async def _get_facets(self, session, base_stmt) -> dict:
              """Get facet counts for filters."""
              facets = {}

              # Type facets
              type_stmt = select(
                  SOP.type, func.count(SOP.id)
              ).select_from(base_stmt.subquery()).group_by(SOP.type)
              type_result = await session.execute(type_stmt)
              facets['types'] = {row[0]: row[1] for row in type_result}

              # Team facets
              team_stmt = select(
                  SOP.team_id, func.count(SOP.id)
              ).select_from(base_stmt.subquery()).group_by(SOP.team_id)
              team_result = await session.execute(team_stmt)
              facets['teams'] = {row[0]: row[1] for row in team_result}

              return facets
```

**Day 4-5: Rate Limiting (FR35)**

```yaml
tasks:
  - task: "Implement hierarchical rate limiting"
    owner: "Backend Lead"
    deliverables:
      - User/Team/Org rate limits
      - Redis token bucket
      - Rate limit headers
    code_sample: |
      # backend/middleware/rate_limit.py
      from fastapi import Request, HTTPException
      from redis.asyncio import Redis
      import time

      class HierarchicalRateLimiter:
          """
          Token bucket rate limiter with user → team → org hierarchy.
          """

          DEFAULT_LIMITS = {
              "user": {"requests": 100, "window_seconds": 60},
              "team": {"requests": 1000, "window_seconds": 60},
              "org": {"requests": 10000, "window_seconds": 60},
          }

          def __init__(self, redis: Redis):
              self.redis = redis

          async def check_rate_limit(
              self,
              user_id: str,
              team_id: str,
              org_id: str,
          ) -> RateLimitResult:
              """Check rate limits at all levels."""
              now = time.time()

              # Check user limit
              user_result = await self._check_limit(
                  f"ratelimit:user:{user_id}",
                  self.DEFAULT_LIMITS["user"],
                  now,
              )
              if not user_result.allowed:
                  return user_result

              # Check team limit
              team_result = await self._check_limit(
                  f"ratelimit:team:{team_id}",
                  self.DEFAULT_LIMITS["team"],
                  now,
              )
              if not team_result.allowed:
                  return team_result

              # Check org limit
              org_result = await self._check_limit(
                  f"ratelimit:org:{org_id}",
                  self.DEFAULT_LIMITS["org"],
                  now,
              )
              return org_result

          async def _check_limit(
              self,
              key: str,
              limit_config: dict,
              now: float,
          ) -> RateLimitResult:
              """Token bucket implementation with Lua script."""
              lua_script = """
              local key = KEYS[1]
              local limit = tonumber(ARGV[1])
              local window = tonumber(ARGV[2])
              local now = tonumber(ARGV[3])

              local bucket = redis.call('HGETALL', key)
              local tokens = limit
              local last_update = now

              if #bucket > 0 then
                  tokens = tonumber(bucket[2])
                  last_update = tonumber(bucket[4])
              end

              -- Refill tokens based on time elapsed
              local elapsed = now - last_update
              local refill = math.floor(elapsed * limit / window)
              tokens = math.min(limit, tokens + refill)

              if tokens > 0 then
                  tokens = tokens - 1
                  redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                  redis.call('EXPIRE', key, window)
                  return {1, tokens, limit}
              else
                  return {0, 0, limit}
              end
              """

              result = await self.redis.eval(
                  lua_script,
                  1,
                  key,
                  limit_config["requests"],
                  limit_config["window_seconds"],
                  now,
              )

              return RateLimitResult(
                  allowed=bool(result[0]),
                  remaining=result[1],
                  limit=result[2],
                  reset_at=now + limit_config["window_seconds"],
              )

      # FastAPI middleware
      @app.middleware("http")
      async def rate_limit_middleware(request: Request, call_next):
          if not request.state.user:
              return await call_next(request)

          limiter = HierarchicalRateLimiter(redis)
          result = await limiter.check_rate_limit(
              user_id=request.state.user.id,
              team_id=request.state.user.team_id,
              org_id=request.state.user.org_id,
          )

          if not result.allowed:
              raise HTTPException(
                  status_code=429,
                  detail="Rate limit exceeded",
                  headers={
                      "X-RateLimit-Limit": str(result.limit),
                      "X-RateLimit-Remaining": "0",
                      "X-RateLimit-Reset": str(int(result.reset_at)),
                      "Retry-After": str(int(result.reset_at - time.time())),
                  },
              )

          response = await call_next(request)
          response.headers["X-RateLimit-Limit"] = str(result.limit)
          response.headers["X-RateLimit-Remaining"] = str(result.remaining)
          response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))
          return response
```

---

### Week 8: Week 5-8 Review & Mid-Phase Checkpoint

**Theme**: Validate Hierarchy & Marketplace

**Day 1-4: Integration Testing & Bug Fixes**

```yaml
tasks:
  - task: "End-to-end testing of new features"
    owner: "QA Lead"
    test_scenarios:
      - "Create 4-level team hierarchy"
      - "Verify permission inheritance"
      - "Publish and install marketplace template"
      - "Search across 500+ SOPs"
      - "Rate limit enforcement"

  - task: "Performance optimization"
    owner: "Backend Lead"
    focus_areas:
      - "Search latency <200ms"
      - "Hierarchy queries <50ms"
      - "Marketplace browse <100ms"
```

**Day 5: Mid-Phase Review**

```yaml
review:
  sprint_rating_target: "9.5/10"
  metrics:
    - metric: "Teams in hierarchy"
      target: "50% (25/50)"
      actual: "TBD"
    - metric: "Marketplace templates published"
      target: "20+"
      actual: "TBD"
    - metric: "Search latency p95"
      target: "<200ms"
      actual: "TBD"

  go_no_go_decision:
    criteria:
      - "Hierarchy feature stable"
      - "Marketplace functional"
      - "No P0 bugs"
    decision: "Proceed to Week 9-12 (AI & Integrations)"
```

---

## Phase 5A - Weeks 9-12: AI & Integrations

### Week 9: AI-Powered Recommendations

**Theme**: Intelligent SOP Discovery

**Day 1-3: Recommendation Engine (FR29)**

```yaml
tasks:
  - task: "Build AI recommendation engine"
    owner: "Backend Lead + ML Engineer"
    deliverables:
      - Embedding pipeline (text-embedding-3-small)
      - pgvector similarity search
      - Context-aware recommendations
    code_sample: |
      # backend/services/recommendation_service.py
      import openai
      from pgvector.sqlalchemy import Vector
      import numpy as np

      class SOPRecommendationService:
          """AI-powered SOP recommendations using embeddings."""

          def __init__(self, openai_client, embedding_model: str = "text-embedding-3-small"):
              self.client = openai_client
              self.embedding_model = embedding_model
              self.embedding_dim = 1536

          async def get_recommendations(
              self,
              session,
              context: RecommendationContext,
              limit: int = 5,
          ) -> list[SOPRecommendation]:
              """Get SOP recommendations based on context."""

              # Build context string
              context_text = self._build_context_text(context)

              # Get embedding for context
              context_embedding = await self._get_embedding(context_text)

              # Find similar SOPs using pgvector
              similar_sops = await self._find_similar_sops(
                  session,
                  context_embedding,
                  context.accessible_teams,
                  limit,
              )

              # Calculate relevance scores
              recommendations = []
              for sop, similarity in similar_sops:
                  score = self._calculate_relevance_score(sop, context, similarity)
                  recommendations.append(SOPRecommendation(
                      sop=sop,
                      relevance_score=score,
                      reason=self._generate_reason(sop, context),
                  ))

              return sorted(recommendations, key=lambda r: r.relevance_score, reverse=True)

          def _build_context_text(self, context: RecommendationContext) -> str:
              """Build text representation of context for embedding."""
              parts = []

              if context.project_name:
                  parts.append(f"Project: {context.project_name}")
              if context.project_description:
                  parts.append(f"Description: {context.project_description}")
              if context.incident_title:
                  parts.append(f"Incident: {context.incident_title}")
              if context.code_context:
                  parts.append(f"Code: {context.code_context[:500]}")
              if context.tags:
                  parts.append(f"Tags: {', '.join(context.tags)}")

              return " ".join(parts)

          async def _get_embedding(self, text: str) -> list[float]:
              """Get embedding from OpenAI."""
              response = await self.client.embeddings.create(
                  model=self.embedding_model,
                  input=text,
              )
              return response.data[0].embedding

          async def _find_similar_sops(
              self,
              session,
              embedding: list[float],
              accessible_teams: list[str],
              limit: int,
          ) -> list[tuple[SOP, float]]:
              """Find SOPs with similar embeddings using pgvector."""
              stmt = select(
                  SOP,
                  (1 - SOP.embedding.cosine_distance(embedding)).label('similarity')
              ).where(
                  SOP.team_id.in_(accessible_teams)
              ).order_by(
                  SOP.embedding.cosine_distance(embedding)
              ).limit(limit)

              result = await session.execute(stmt)
              return [(row.SOP, row.similarity) for row in result]

          async def index_sop(self, session, sop_id: str) -> None:
              """Generate and store embedding for SOP."""
              sop = await session.get(SOP, sop_id)
              if not sop:
                  return

              # Build text for embedding
              text = f"{sop.title} {sop.content[:2000]} {' '.join(sop.tags or [])}"

              # Get embedding
              embedding = await self._get_embedding(text)

              # Update SOP
              sop.embedding = embedding
              await session.commit()

          async def record_feedback(
              self,
              session,
              recommendation_id: str,
              feedback_type: str,  # 'click', 'dismiss', 'helpful', 'not_helpful'
              user_id: str,
          ) -> None:
              """Record user feedback for model improvement."""
              feedback = RecommendationFeedback(
                  recommendation_id=recommendation_id,
                  feedback_type=feedback_type,
                  user_id=user_id,
              )
              session.add(feedback)
              await session.commit()
```

**Day 4-5: Recommendation UI**

```yaml
tasks:
  - task: "Recommendation UI components"
    owner: "Frontend Lead"
    deliverables:
      - Recommendation sidebar
      - Context-aware suggestions
      - Feedback buttons
    code_sample: |
      // frontend/src/components/Recommendations/RecommendationSidebar.tsx
      import { useRecommendations, useRecordFeedback } from '@/hooks/useRecommendations';
      import { useCurrentProject } from '@/hooks/useProjects';

      export function RecommendationSidebar() {
        const project = useCurrentProject();
        const { data: recommendations, isLoading } = useRecommendations({
          projectId: project?.id,
          projectName: project?.name,
          projectDescription: project?.description,
        });
        const recordFeedback = useRecordFeedback();

        const handleClick = (recommendation) => {
          recordFeedback.mutate({
            recommendationId: recommendation.id,
            feedbackType: 'click',
          });
        };

        const handleDismiss = (recommendation) => {
          recordFeedback.mutate({
            recommendationId: recommendation.id,
            feedbackType: 'dismiss',
          });
        };

        if (isLoading) return <RecommendationSkeleton />;
        if (!recommendations?.length) return null;

        return (
          <div className="w-80 border-l p-4 bg-muted/50">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Recommended SOPs</h3>
            </div>

            <div className="space-y-3">
              {recommendations.map((rec) => (
                <Card
                  key={rec.id}
                  className="cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => handleClick(rec)}
                >
                  <CardHeader className="p-3 pb-2">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-sm font-medium line-clamp-2">
                        {rec.sop.title}
                      </CardTitle>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDismiss(rec);
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-3 pt-0">
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {rec.reason}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="secondary" className="text-xs">
                        {Math.round(rec.relevance_score * 100)}% match
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {rec.sop.type}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );
      }
```

---

### Week 10: Bulk Operations

**Theme**: Legacy System Migration

**Day 1-3: Bulk Import (FR30)**

```yaml
tasks:
  - task: "Implement bulk import from Confluence/SharePoint"
    owner: "Backend Lead"
    deliverables:
      - Confluence API integration
      - SharePoint Graph API integration
      - CSV import with field mapping
    code_sample: |
      # backend/services/bulk_import_service.py
      from celery import Celery
      import httpx
      from html2text import html2text

      celery = Celery('sop-generator')

      class BulkImportService:
          """Service for bulk importing SOPs from external systems."""

          async def import_from_confluence(
              self,
              session,
              confluence_url: str,
              space_key: str,
              page_ids: list[str],
              team_id: str,
              imported_by: str,
          ) -> str:
              """Start async Confluence import job."""
              job = ImportJob(
                  source="confluence",
                  status="pending",
                  total_items=len(page_ids),
                  team_id=team_id,
                  created_by=imported_by,
                  metadata_={
                      "confluence_url": confluence_url,
                      "space_key": space_key,
                      "page_ids": page_ids,
                  },
              )
              session.add(job)
              await session.commit()

              # Start Celery task
              import_confluence_pages.delay(job.id)

              return job.id

      @celery.task(bind=True)
      def import_confluence_pages(self, job_id: str):
          """Celery task for Confluence import."""
          with get_db_session() as session:
              job = session.get(ImportJob, job_id)
              job.status = "processing"
              session.commit()

              try:
                  confluence_url = job.metadata_["confluence_url"]
                  page_ids = job.metadata_["page_ids"]

                  imported = 0
                  errors = []

                  for page_id in page_ids:
                      try:
                          # Fetch page from Confluence
                          page = fetch_confluence_page(confluence_url, page_id)

                          # Convert HTML to Markdown
                          content = html2text(page["body"]["storage"]["value"])

                          # Create SOP
                          sop = SOP(
                              title=page["title"],
                              content=content,
                              type="GENERAL",
                              team_id=job.team_id,
                              created_by=job.created_by,
                              metadata_={
                                  "imported_from": "confluence",
                                  "source_id": page_id,
                                  "source_url": page["_links"]["webui"],
                              },
                          )
                          session.add(sop)

                          imported += 1
                          job.processed_items = imported
                          session.commit()

                          # Update progress
                          self.update_state(
                              state='PROGRESS',
                              meta={'current': imported, 'total': len(page_ids)}
                          )

                      except Exception as e:
                          errors.append({"page_id": page_id, "error": str(e)})

                  job.status = "completed" if not errors else "completed_with_errors"
                  job.result = {"imported": imported, "errors": errors}
                  session.commit()

              except Exception as e:
                  job.status = "failed"
                  job.error = str(e)
                  session.commit()
                  raise

      def fetch_confluence_page(base_url: str, page_id: str) -> dict:
          """Fetch single page from Confluence API."""
          response = httpx.get(
              f"{base_url}/rest/api/content/{page_id}",
              params={"expand": "body.storage"},
              headers={"Authorization": f"Bearer {get_confluence_token()}"},
          )
          response.raise_for_status()
          return response.json()
```

**Day 4-5: Bulk Export & Scheduled Backups**

```yaml
tasks:
  - task: "Implement bulk export and scheduled backups"
    owner: "Backend Lead"
    deliverables:
      - Multi-format export (JSON, CSV, Markdown)
      - ZIP bundling
      - Scheduled backup to S3
```

---

### Week 11: Workflows & SOC 2 Prep

**Theme**: Governance & Compliance

**Day 1-3: SOP Workflows (FR32)**

```yaml
tasks:
  - task: "Implement approval workflows"
    owner: "Backend Lead"
    deliverables:
      - Workflow state machine
      - Reviewer assignment
      - Approval notifications
```

**Day 4-5: SOC 2 Audit Preparation**

```yaml
tasks:
  - task: "SOC 2 Type II controls validation"
    owner: "Security Lead"
    deliverables:
      - Control evidence collection
      - Audit log verification
      - Access control review
      - Pre-audit gap analysis
```

---

### Week 12: Week 9-12 Review

**Theme**: AI Features Complete

**Day 1-4: Integration Testing**

```yaml
tasks:
  - task: "Full feature integration testing"
    owner: "QA Lead"
    test_scenarios:
      - "AI recommendations accuracy (≥30% CTR)"
      - "Bulk import 200+ SOPs"
      - "Workflow approval chain"
      - "Cross-region data consistency"
```

**Day 5: Week 9-12 Review**

```yaml
review:
  sprint_rating_target: "9.5/10"
  metrics:
    - metric: "AI recommendation CTR"
      target: "≥30%"
    - metric: "SOPs imported via bulk"
      target: "≥200"
    - metric: "Workflows configured"
      target: "≥10 teams"
```

---

## Phase 5A - Weeks 13-16: Scale & Certification

### Week 13: 500K Load Test

**Theme**: Performance Validation at Scale

**Day 1-3: Full-Scale Load Test**

```yaml
tasks:
  - task: "Execute 500K concurrent user load test"
    owner: "DevOps Lead + QA Lead"
    deliverables:
      - Locust test execution (500K users)
      - Performance report
      - Bottleneck analysis
    test_scenarios:
      - scenario: "500K read-heavy (browse, search)"
        target: "p95 <100ms"
      - scenario: "50K write-heavy (create, edit)"
        target: "p95 <200ms"
      - scenario: "25K concurrent collaborations"
        target: "p95 <500ms"
```

**Day 4-5: Performance Optimization**

```yaml
tasks:
  - task: "Address load test findings"
    owner: "Backend Lead"
    potential_optimizations:
      - "Database query optimization"
      - "Redis cache tuning"
      - "Connection pool sizing"
      - "Kubernetes HPA adjustment"
```

---

### Week 14: SOC 2 Audit

**Theme**: Compliance Certification

**Day 1-5: External Audit**

```yaml
tasks:
  - task: "SOC 2 Type II audit execution"
    owner: "Security Lead + External Auditor"
    audit_areas:
      - "Security (access control, encryption)"
      - "Availability (uptime, failover)"
      - "Confidentiality (data protection)"
    expected_outcome: "0 critical, 0 high, ≤2 medium findings"
```

---

### Week 15: 50-Team Onboarding

**Theme**: Organizational Rollout

**Day 1-5: Batch Onboarding**

```yaml
tasks:
  - task: "Onboard 30 additional teams (20 existing + 30 new = 50)"
    owner: "PM Lead"
    onboarding_plan:
      - day: 1-2
        teams: 10
        method: "Self-service + office hours"
      - day: 3-4
        teams: 10
        method: "Self-service + office hours"
      - day: 5
        teams: 10
        method: "Self-service + office hours"
    success_criteria:
      - "50 teams active"
      - "500 developers with accounts"
      - "≥85% adoption by Week 16"
```

---

### Week 16: SASE Level 2 Completion & Phase Review

**Theme**: Documentation & Approval

**Day 1-3: MRP Evidence Compilation**

```yaml
tasks:
  - task: "Compile MRP-PHASE5A-MEGA-SCALE-001.md"
    owner: "QA Lead"
    evidence:
      - "500K load test report"
      - "SOC 2 audit report"
      - "Test coverage report"
      - "Uptime metrics"
      - "Adoption metrics"
```

**Day 4: VCR Approval**

```yaml
tasks:
  - task: "CTO review for VCR"
    owner: "CTO"
    rating_criteria:
      - "All FRs implemented (10/10)"
      - "All NFRs met (10/10)"
      - "500K load test passed"
      - "SOC 2 certified"
      - "≥85% adoption"
      - "≥4.5/5 satisfaction"
    target_rating: "5/5"
```

**Day 5: LPS Mathematical Proofs**

```yaml
tasks:
  - task: "Validate 4 LPS proofs"
    owner: "CTO + Tech Lead"
    proofs:
      - proof: 1
        title: "Multi-region eventual consistency (<1s)"
        validation: "CockroachDB replication lag measurements"
      - proof: 2
        title: "Federated RBAC correctness"
        validation: "Permission inheritance unit tests (100% pass)"
      - proof: 3
        title: "Marketplace template integrity"
        validation: "Version checksums + signature verification"
      - proof: 4
        title: "500K concurrent user scalability"
        validation: "Load test results (p95 <100ms)"
```

---

## Success Metrics Summary

| Category | Metric | Target | Measurement |
|----------|--------|--------|-------------|
| Adoption | Active developers | ≥85% (425/500) | User analytics |
| Volume | SOPs generated | ≥700 | Database count |
| Satisfaction | NPS score | ≥4.5/5 | Weekly survey |
| Marketplace | Template adoption | ≥50% teams | marketplace_installs |
| Hierarchy | Teams in hierarchy | ≥80% (40/50) | team_hierarchy |
| AI | Recommendation CTR | ≥30% | recommendation_clicks |
| Reliability | Uptime | ≥99.99% | Prometheus |
| Performance | API latency (p95) | <100ms intra-region | Prometheus |
| Compliance | SOC 2 Type II | Certified | Audit report |
| ROI | Year 1 | ≥900% | Calculation |
| Quality | Sprint average | ≥9.5/10 | Weekly reviews |
| SASE | VCR rating | 5/5 | CTO approval |

---

## Budget Breakdown

| Category | Amount | Allocation |
|----------|--------|------------|
| Backend Development | $24,000 | 3 FTE × 16 weeks |
| Frontend Development | $16,000 | 2 FTE × 16 weeks |
| DevOps/Infrastructure | $20,000 | 2 FTE × 16 weeks |
| QA Testing | $8,000 | 1 FTE × 16 weeks |
| SOC 2 Audit | $8,000 | External auditor |
| Cloud Infrastructure | $3,000 | Multi-region costs |
| Miscellaneous | $1,000 | Buffer |
| **Total** | **$80,000** | |

---

## Risk Management

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| CockroachDB migration issues | CRITICAL | LOW | Dual-write + 4-week rollback |
| 500K load test bottlenecks | HIGH | MEDIUM | Early testing (Week 2) |
| SOC 2 audit findings | HIGH | LOW | Pre-audit (Week 8) |
| Multi-region latency | MEDIUM | MEDIUM | Edge caching + CDN |
| 50-team onboarding | MEDIUM | MEDIUM | Self-service + champions |

---

## Phase 5A Completion Checklist

- [ ] Multi-region deployment (3 regions)
- [ ] CockroachDB migration complete
- [ ] Team hierarchy implemented
- [ ] Template marketplace launched
- [ ] AI recommendations live
- [ ] Bulk import/export functional
- [ ] 500K load test passed
- [ ] SOC 2 Type II certified
- [ ] 50 teams onboarded
- [ ] 500 developers active
- [ ] ≥85% adoption achieved
- [ ] ≥4.5/5 satisfaction maintained
- [ ] 99.99% uptime achieved
- [ ] MRP evidence compiled
- [ ] VCR 5/5 approved
- [ ] 4 LPS proofs validated

---

**Document Status**: DRAFT
**Next Review**: Week 4 checkpoint
**Owner**: PM Lead + CTO
**Approval Required**: CTO + CEO + CPO
