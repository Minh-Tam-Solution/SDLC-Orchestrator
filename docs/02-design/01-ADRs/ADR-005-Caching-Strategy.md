# ADR-005: Caching Strategy

**Status**: APPROVED
**Date**: November 13, 2025
**Decision Makers**: Tech Lead, Backend Lead, SRE Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0

---

## Context

SDLC Orchestrator requires aggressive caching to meet performance targets:
- API latency p95 <100ms (from Performance-Budget.md)
- 1,000+ concurrent users
- Complex queries (multi-table joins for dashboards)
- Expensive AI operations (2-6s for Ollama responses)

Current challenges:
- Database queries can take 20-50ms
- AI responses take 2-6 seconds
- Dashboard aggregations require multiple queries
- Session management for 100K+ users

---

## Decision

Implement a **multi-layer caching strategy** using Redis with:

1. **Session Cache**: JWT tokens, user sessions (30-day TTL)
2. **Query Cache**: Database query results (5-minute TTL)
3. **AI Response Cache**: LLM responses (1-hour TTL)
4. **Object Cache**: Frequently accessed entities (15-minute TTL)
5. **Edge Cache**: CDN for static assets (CloudFront)

---

## Rationale

### Why Redis?

**Performance**:
- Sub-millisecond response times
- 100K+ operations per second
- In-memory storage with optional persistence

**Features**:
- Data structures (strings, hashes, lists, sets, sorted sets)
- TTL support per key
- Pub/Sub for cache invalidation
- Clustering for horizontal scaling

**Battle-tested**:
- Used in BFlow Platform (200K users)
- NQH-Bot success with Redis caching
- AI-Platform: 86% test coverage with Redis

### Cache Patterns

We'll use three primary patterns:

1. **Cache-Aside (Lazy Loading)**
   - Read from cache first
   - On miss, fetch from source and populate cache
   - Best for: Read-heavy workloads

2. **Write-Through**
   - Write to cache and database simultaneously
   - Ensures cache consistency
   - Best for: Critical data (user permissions)

3. **Write-Behind (Async)**
   - Write to cache immediately
   - Write to database asynchronously
   - Best for: High-throughput writes (metrics, logs)

---

## Architecture Design

### 1. Cache Layers

```python
# cache/cache_manager.py
from typing import Optional, Any, Dict
import json
import hashlib
from redis import asyncio as aioredis
from datetime import timedelta

class CacheLayer(Enum):
    SESSION = "session"      # 30 days TTL
    QUERY = "query"         # 5 minutes TTL
    AI = "ai"              # 1 hour TTL
    OBJECT = "object"      # 15 minutes TTL
    PERMISSION = "perm"    # 15 minutes TTL

class CacheManager:
    """Unified cache management with multiple layers"""

    def __init__(self):
        self.redis = aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True,
            max_connections=100
        )

        # TTL configuration per layer
        self.ttl_config = {
            CacheLayer.SESSION: timedelta(days=30),
            CacheLayer.QUERY: timedelta(minutes=5),
            CacheLayer.AI: timedelta(hours=1),
            CacheLayer.OBJECT: timedelta(minutes=15),
            CacheLayer.PERMISSION: timedelta(minutes=15)
        }

    def _generate_key(
        self,
        layer: CacheLayer,
        identifier: str,
        params: Optional[Dict] = None
    ) -> str:
        """Generate cache key with namespace"""

        if params:
            # Sort params for consistent keys
            param_str = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            return f"{layer.value}:{identifier}:{param_hash}"

        return f"{layer.value}:{identifier}"

    async def get(
        self,
        layer: CacheLayer,
        identifier: str,
        params: Optional[Dict] = None
    ) -> Optional[Any]:
        """Get value from cache"""

        key = self._generate_key(layer, identifier, params)

        try:
            value = await self.redis.get(key)
            if value:
                # Track cache hit
                await self._increment_metric("cache_hits", layer.value)
                return json.loads(value) if value else None
            else:
                # Track cache miss
                await self._increment_metric("cache_misses", layer.value)
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        layer: CacheLayer,
        identifier: str,
        value: Any,
        params: Optional[Dict] = None,
        ttl_override: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""

        key = self._generate_key(layer, identifier, params)
        ttl = ttl_override or int(self.ttl_config[layer].total_seconds())

        try:
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate(
        self,
        layer: CacheLayer,
        pattern: str
    ) -> int:
        """Invalidate cache entries matching pattern"""

        # Use SCAN to avoid blocking
        count = 0
        async for key in self.redis.scan_iter(
            match=f"{layer.value}:{pattern}*",
            count=100
        ):
            await self.redis.delete(key)
            count += 1

        logger.info(f"Invalidated {count} cache entries for pattern {pattern}")
        return count

    async def _increment_metric(self, metric: str, label: str):
        """Track cache metrics for monitoring"""
        # Increment Prometheus counter
        cache_operations.labels(operation=metric, layer=label).inc()
```

---

### 2. Session Cache Implementation

```python
# cache/session_cache.py
class SessionCache:
    """JWT token and session management"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def store_session(
        self,
        user_id: str,
        session_data: Dict[str, Any],
        access_token: str,
        refresh_token: str
    ) -> None:
        """Store user session with tokens"""

        # Store session data
        await self.cache.set(
            layer=CacheLayer.SESSION,
            identifier=f"user:{user_id}",
            value={
                "session": session_data,
                "access_token": access_token,
                "refresh_token_hash": hashlib.sha256(refresh_token.encode()).hexdigest(),
                "created_at": datetime.utcnow().isoformat()
            }
        )

        # Store reverse lookup for token validation
        await self.cache.set(
            layer=CacheLayer.SESSION,
            identifier=f"token:{access_token}",
            value={"user_id": user_id, "type": "access"},
            ttl_override=3600  # 1 hour for access token
        )

    async def validate_token(self, token: str) -> Optional[Dict]:
        """Fast token validation without database hit"""

        cached = await self.cache.get(
            layer=CacheLayer.SESSION,
            identifier=f"token:{token}"
        )

        if cached:
            return cached

        # Cache miss - validate against database
        user = await self._validate_from_database(token)
        if user:
            # Populate cache for next time
            await self.cache.set(
                layer=CacheLayer.SESSION,
                identifier=f"token:{token}",
                value={"user_id": user.id, "type": "access"},
                ttl_override=300  # 5 min for database-validated tokens
            )

        return user

    async def blacklist_token(self, token: str, reason: str) -> None:
        """Add token to blacklist (logout, security issue)"""

        await self.cache.set(
            layer=CacheLayer.SESSION,
            identifier=f"blacklist:{token}",
            value={"reason": reason, "blacklisted_at": datetime.utcnow().isoformat()},
            ttl_override=86400  # 24 hours (longer than token expiry)
        )

    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""

        return await self.cache.get(
            layer=CacheLayer.SESSION,
            identifier=f"blacklist:{token}"
        ) is not None
```

---

### 3. Query Cache Implementation

```python
# cache/query_cache.py
class QueryCache:
    """Database query result caching"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def cache_key_from_query(self, query: str, params: Dict) -> str:
        """Generate cache key from SQL query and parameters"""

        # Normalize query (remove whitespace, lowercase)
        normalized = " ".join(query.lower().split())

        # Hash query + params
        content = f"{normalized}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_or_fetch(
        self,
        query: str,
        params: Dict,
        fetch_func,
        ttl: int = 300
    ) -> Any:
        """Cache-aside pattern for queries"""

        cache_key = self.cache_key_from_query(query, params)

        # Try cache first
        cached = await self.cache.get(
            layer=CacheLayer.QUERY,
            identifier=cache_key
        )

        if cached is not None:
            return cached

        # Cache miss - fetch from database
        result = await fetch_func(query, params)

        # Store in cache
        await self.cache.set(
            layer=CacheLayer.QUERY,
            identifier=cache_key,
            value=result,
            ttl_override=ttl
        )

        return result

    async def invalidate_table(self, table_name: str) -> None:
        """Invalidate all queries touching a table"""

        # This is complex - we track query-table mappings
        query_keys = await self.cache.get(
            layer=CacheLayer.QUERY,
            identifier=f"table_queries:{table_name}"
        )

        if query_keys:
            for key in query_keys:
                await self.cache.invalidate(
                    layer=CacheLayer.QUERY,
                    pattern=key
                )

# Usage in repository layer
class ProjectRepository:
    def __init__(self, db: Database, cache: QueryCache):
        self.db = db
        self.cache = cache

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project with caching"""

        query = "SELECT * FROM projects WHERE id = :id"
        params = {"id": project_id}

        result = await self.cache.get_or_fetch(
            query=query,
            params=params,
            fetch_func=lambda q, p: self.db.fetch_one(q, p),
            ttl=900  # 15 minutes for individual objects
        )

        return Project(**result) if result else None

    async def list_projects(
        self,
        organization_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Project]:
        """List projects with caching"""

        query = """
            SELECT * FROM projects
            WHERE organization_id = :org_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        params = {"org_id": organization_id, "limit": limit, "offset": offset}

        results = await self.cache.get_or_fetch(
            query=query,
            params=params,
            fetch_func=lambda q, p: self.db.fetch_all(q, p),
            ttl=300  # 5 minutes for lists
        )

        return [Project(**r) for r in results]
```

---

### 4. AI Response Cache

```python
# cache/ai_cache.py
class AIResponseCache:
    """Cache expensive AI operations"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def _generate_prompt_hash(self, prompt: str, context: Dict) -> str:
        """Generate hash from prompt + context"""

        # Include important context in hash
        cache_key_data = {
            "prompt": prompt,
            "stage": context.get("stage"),
            "model": context.get("model", "default"),
            "temperature": context.get("temperature", 0.7)
        }

        serialized = json.dumps(cache_key_data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    async def get_cached_response(
        self,
        prompt: str,
        context: Dict
    ) -> Optional[str]:
        """Get cached AI response"""

        prompt_hash = self._generate_prompt_hash(prompt, context)

        return await self.cache.get(
            layer=CacheLayer.AI,
            identifier=prompt_hash
        )

    async def cache_response(
        self,
        prompt: str,
        context: Dict,
        response: str,
        ttl: int = 3600
    ) -> None:
        """Cache AI response"""

        prompt_hash = self._generate_prompt_hash(prompt, context)

        await self.cache.set(
            layer=CacheLayer.AI,
            identifier=prompt_hash,
            value={
                "response": response,
                "prompt_preview": prompt[:100],
                "cached_at": datetime.utcnow().isoformat(),
                "model": context.get("model", "unknown")
            },
            ttl_override=ttl
        )

# Integration with AI Gateway
class AIGateway:
    def __init__(self):
        self.cache = AIResponseCache(cache_manager)

    async def complete(
        self,
        prompt: str,
        context: Dict,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """AI completion with caching"""

        # Check cache if enabled
        if use_cache:
            cached = await self.cache.get_cached_response(prompt, context)
            if cached:
                return {
                    "response": cached["response"],
                    "provider": "cache",
                    "latency_ms": 5,
                    "cached": True
                }

        # Cache miss - call AI provider
        response = await self._call_provider(prompt, context)

        # Cache successful response
        if use_cache and response.get("success"):
            await self.cache.cache_response(
                prompt=prompt,
                context=context,
                response=response["response"],
                ttl=3600 if context.get("stage") else 7200
            )

        return response
```

---

### 5. Permission Cache

```python
# cache/permission_cache.py
class PermissionCache:
    """Cache user permissions for fast authorization"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def get_user_permissions(self, user_id: str) -> Optional[Dict]:
        """Get cached user permissions"""

        return await self.cache.get(
            layer=CacheLayer.PERMISSION,
            identifier=f"user:{user_id}"
        )

    async def cache_user_permissions(
        self,
        user_id: str,
        permissions: Dict
    ) -> None:
        """Cache user permissions with write-through"""

        await self.cache.set(
            layer=CacheLayer.PERMISSION,
            identifier=f"user:{user_id}",
            value=permissions,
            ttl_override=900  # 15 minutes
        )

    async def invalidate_user(self, user_id: str) -> None:
        """Invalidate user's permission cache"""

        await self.cache.invalidate(
            layer=CacheLayer.PERMISSION,
            pattern=f"user:{user_id}"
        )

    async def invalidate_team(self, team_id: str) -> None:
        """Invalidate all team members' caches"""

        # Get team members
        members = await self.db.fetch_all(
            "SELECT user_id FROM users WHERE team_id = :team_id",
            {"team_id": team_id}
        )

        # Invalidate each member
        for member in members:
            await self.invalidate_user(member["user_id"])

# Usage in authorization
async def check_permission(
    user_id: str,
    resource: str,
    action: str
) -> bool:
    """Fast permission check with cache"""

    # Try cache first
    permissions = await permission_cache.get_user_permissions(user_id)

    if not permissions:
        # Cache miss - fetch from database
        permissions = await fetch_user_permissions_from_db(user_id)

        # Cache for next time
        await permission_cache.cache_user_permissions(user_id, permissions)

    # Check permission
    return permissions.get(resource, {}).get(action, False)
```

---

### 6. Cache Warming & Preloading

```python
# cache/cache_warmer.py
class CacheWarmer:
    """Preload cache with hot data"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def warm_cache_on_startup(self) -> None:
        """Warm cache when application starts"""

        logger.info("Starting cache warming...")

        # 1. Load active sessions
        await self._warm_active_sessions()

        # 2. Load popular projects
        await self._warm_popular_projects()

        # 3. Load recent AI responses
        await self._warm_ai_responses()

        logger.info("Cache warming completed")

    async def _warm_active_sessions(self) -> None:
        """Preload active user sessions"""

        active_users = await db.fetch_all("""
            SELECT u.*, s.session_token
            FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.expires_at > NOW()
            AND s.last_activity_at > NOW() - INTERVAL '1 hour'
            LIMIT 1000
        """)

        for user in active_users:
            await session_cache.store_session(
                user_id=user["id"],
                session_data=user,
                access_token=user["session_token"],
                refresh_token=""  # Not needed for warming
            )

        logger.info(f"Warmed {len(active_users)} active sessions")

    async def _warm_popular_projects(self) -> None:
        """Preload frequently accessed projects"""

        popular = await db.fetch_all("""
            SELECT p.*
            FROM projects p
            JOIN (
                SELECT project_id, COUNT(*) as access_count
                FROM audit_log
                WHERE action = 'project_accessed'
                AND timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY project_id
                ORDER BY access_count DESC
                LIMIT 100
            ) hot ON p.id = hot.project_id
        """)

        for project in popular:
            await self.cache.set(
                layer=CacheLayer.OBJECT,
                identifier=f"project:{project['id']}",
                value=project
            )

        logger.info(f"Warmed {len(popular)} popular projects")

# Schedule periodic cache warming
@app.on_event("startup")
async def startup_cache_warming():
    warmer = CacheWarmer(cache_manager)
    await warmer.warm_cache_on_startup()

    # Schedule periodic warming every hour
    scheduler.add_job(
        warmer.warm_cache_on_startup,
        'interval',
        hours=1,
        id='cache_warming'
    )
```

---

## Consequences

### Positive

1. **Performance**: Sub-millisecond cache hits reduce API latency
2. **Scalability**: Reduce database load by 70-80%
3. **Cost Savings**: Fewer database queries, smaller instance needed
4. **User Experience**: Fast response times, especially for dashboards
5. **AI Cost Reduction**: Cache expensive LLM responses

### Negative

1. **Complexity**: Cache invalidation logic
2. **Memory Cost**: Redis instances ($100-500/month)
3. **Stale Data Risk**: TTL tuning required
4. **Debugging Difficulty**: Cache-related bugs harder to reproduce

### Risks

1. **Cache Stampede**: Many clients fetching same expired key
   - **Mitigation**: Use lock pattern or probabilistic early expiration

2. **Memory Exhaustion**: Redis runs out of memory
   - **Mitigation**: Set maxmemory-policy to allkeys-lru

3. **Cache Inconsistency**: Stale data served
   - **Mitigation**: Event-driven invalidation, short TTLs

---

## Implementation Plan

### Phase 1: Foundation (Day 1-2)
- [ ] Setup Redis cluster with replication
- [ ] Implement CacheManager base class
- [ ] Add session cache layer
- [ ] Integrate with authentication

### Phase 2: Query Cache (Day 3-4)
- [ ] Implement query cache with invalidation
- [ ] Add to repository layer
- [ ] Cache warming for hot data

### Phase 3: AI Cache (Day 5)
- [ ] Cache AI responses
- [ ] Implement prompt hashing
- [ ] Add cache metrics

### Phase 4: Monitoring (Day 6-7)
- [ ] Prometheus metrics (hit rate, latency)
- [ ] Grafana dashboard
- [ ] Alert on low hit rate (<80%)

---

## Alternatives Considered

### Alternative 1: No Caching
- ❌ **Rejected**: Cannot meet <100ms p95 latency target

### Alternative 2: In-Memory Application Cache
- ❌ **Rejected**: Not shared across instances, memory limitations

### Alternative 3: Database Query Cache Only
- ❌ **Rejected**: Limited control, doesn't cache AI responses

### Alternative 4: Memcached
- ❌ **Rejected**: Fewer data structures, no persistence option

---

## References

- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
- [BFlow Platform Caching](../../../heritage/bflow-caching.md)
- [Performance Budget](../../10-Performance-Architecture/Performance-Budget.md)

---

## Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
| **Tech Lead** | [Tech Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Backend Lead** | [Backend Name] | ✅ APPROVED | Nov 13, 2025 |
| **SRE Lead** | [SRE Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Decision**: **APPROVED** - Multi-layer Redis caching strategy

**Priority**: **RECOMMENDED** - Critical for performance targets

**Timeline**: 1 week implementation in BUILD phase

**Success Metrics**:
- Cache hit rate >90% for sessions
- Cache hit rate >80% for queries
- API p95 latency <100ms achieved
- Database load reduced by 70%+

---

*"Cache aggressively, invalidate wisely"* 🚀