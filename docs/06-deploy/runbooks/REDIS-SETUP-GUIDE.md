# Redis Configuration Guide - Sprint 128 Rate Limiting

**Date**: January 31, 2026
**Purpose**: Configure Redis for invitation rate limiting
**Time Estimate**: 1 hour
**Reference**: Sprint 128 Infrastructure Setup

---

## Overview

Redis is used for rate limiting team invitations:
- **Team rate limit**: 50 invitations/hour per team
- **Email rate limit**: 3 invitations/day per email
- **Resend cooldown**: 5 minutes between resends

---

## Option 1: Use Existing Redis (Recommended)

**If you already have Redis running** (e.g., postgres-central):

### 1.1 Verify Existing Redis

```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG

# Or if using custom port:
redis-cli -h localhost -p 6395 ping
```

### 1.2 Update Configuration

Edit `backend/.env.local`:

```bash
# Use existing Redis
REDIS_URL="redis://localhost:6379/0"

# Or if using custom port:
REDIS_URL="redis://localhost:6395/0"

# Or with authentication:
REDIS_URL="redis://:password@localhost:6379/0"
```

### 1.3 Test Connection

```python
# backend/scripts/test_redis.py
import redis
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
client = redis.from_url(redis_url)

# Test ping
response = client.ping()
print(f"Redis PING: {response}")  # Should print: True

# Test set/get
client.set("test_key", "hello_redis")
value = client.get("test_key")
print(f"Redis GET: {value.decode()}")  # Should print: hello_redis

# Test expiry
client.setex("expiry_test", 5, "expires_in_5_seconds")
print(f"TTL: {client.ttl('expiry_test')} seconds")  # Should print: 5

print("✅ Redis connection successful!")
```

Run test:
```bash
cd backend
REDIS_URL="redis://localhost:6379/0" python scripts/test_redis.py
```

---

## Option 2: Docker Redis (New Instance)

**If you need a dedicated Redis for invitations**:

### 2.1 Docker Run (Quick Start)

```bash
docker run -d \
  --name redis-invitations \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7.2-alpine

# Verify running
docker ps | grep redis-invitations

# Test connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG
```

### 2.2 Docker Compose (Recommended)

Add to `docker-compose.yml`:

```yaml
services:
  redis-invitations:
    image: redis:7.2-alpine
    container_name: redis-invitations
    ports:
      - "6379:6379"
    volumes:
      - redis-invitations-data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  redis-invitations-data:
```

Start Redis:
```bash
docker-compose up -d redis-invitations

# Check logs
docker-compose logs -f redis-invitations
```

### 2.3 Redis with Password (Production)

```bash
docker run -d \
  --name redis-invitations \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7.2-alpine \
  redis-server --requirepass "your_strong_password_here"

# Update .env.local
REDIS_URL="redis://:your_strong_password_here@localhost:6379/0"
```

---

## Option 3: Managed Redis (Production)

### 3.1 AWS ElastiCache

```bash
# Create ElastiCache cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id sdlc-orchestrator-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --engine-version 7.0

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id sdlc-orchestrator-redis \
  --show-cache-node-info

# Update .env.local
REDIS_URL="redis://your-cluster.cache.amazonaws.com:6379/0"
```

### 3.2 Redis Cloud (Upstash/Redis Labs)

1. Go to https://upstash.com/ or https://redis.com/
2. Create free account
3. Create Redis database
4. Copy connection URL
5. Update `.env.local`:
   ```bash
   REDIS_URL="rediss://default:password@endpoint.upstash.io:6379"
   ```

---

## Step 3: Configure Backend (15 minutes)

### 3.1 Install Redis Client

```bash
cd backend
pip install redis
pip freeze | grep redis >> requirements.txt
```

### 3.2 Update Config Class

Edit `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_SOCKET_TIMEOUT: int = 5  # seconds

    # Rate Limiting
    MAX_INVITATIONS_PER_TEAM_PER_HOUR: int = 50
    MAX_INVITATIONS_PER_EMAIL_PER_DAY: int = 3
    MAX_INVITATION_RESENDS: int = 3
    INVITATION_RESEND_COOLDOWN_MINUTES: int = 5
```

### 3.3 Create Redis Client

Edit `backend/app/core/redis.py` (create if not exists):

```python
"""
Redis Client Configuration

Used for:
- Rate limiting (invitations, API calls)
- Session storage
- Token blacklist
"""
import os
import redis
from typing import Optional

from app.core.config import settings

# Global Redis client instance
redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client instance (singleton pattern).

    Returns:
        Redis client or None if connection fails
    """
    global redis_client

    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                decode_responses=True,  # Auto-decode bytes to strings
            )

            # Test connection
            redis_client.ping()

            print(f"✅ Redis connected: {settings.REDIS_URL}")

        except Exception as e:
            print(f"⚠️ Redis connection failed: {str(e)}")
            print("Rate limiting will be disabled (development only)")
            redis_client = None

    return redis_client


def close_redis_client():
    """Close Redis connection on app shutdown"""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None
```

### 3.4 Initialize Redis on Startup

Edit `backend/app/main.py`:

```python
from app.core.redis import get_redis_client, close_redis_client

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Initialize Redis
    get_redis_client()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Close Redis connection
    close_redis_client()
```

---

## Step 4: Test Rate Limiting (20 minutes)

### 4.1 Manual Rate Limit Test

Create test script:

```python
# backend/scripts/test_rate_limiting.py
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.redis import get_redis_client
from app.services.invitation_service import check_team_rate_limit, check_email_rate_limit

# Initialize Redis
redis_client = get_redis_client()

if not redis_client:
    print("❌ Redis not available!")
    sys.exit(1)

# Test 1: Team rate limiting
print("Test 1: Team rate limiting")
team_id = uuid4()

for i in range(52):  # Try 52 requests (limit is 50)
    try:
        check_team_rate_limit(team_id)
        print(f"  Request {i+1}: ✅ Allowed")
    except Exception as e:
        print(f"  Request {i+1}: ❌ Blocked - {str(e)}")
        break

# Test 2: Email rate limiting
print("\nTest 2: Email rate limiting")
email = "test@example.com"

for i in range(4):  # Try 4 requests (limit is 3)
    try:
        check_email_rate_limit(email)
        print(f"  Request {i+1}: ✅ Allowed")
    except Exception as e:
        print(f"  Request {i+1}: ❌ Blocked - {str(e)}")
        break

print("\n✅ Rate limiting test complete!")
```

Run test:
```bash
cd backend
REDIS_URL="redis://localhost:6379/0" python scripts/test_rate_limiting.py
```

Expected output:
```
Test 1: Team rate limiting
  Request 1: ✅ Allowed
  Request 2: ✅ Allowed
  ...
  Request 50: ✅ Allowed
  Request 51: ❌ Blocked - Rate limit exceeded

Test 2: Email rate limiting
  Request 1: ✅ Allowed
  Request 2: ✅ Allowed
  Request 3: ✅ Allowed
  Request 4: ❌ Blocked - Rate limit exceeded

✅ Rate limiting test complete!
```

### 4.2 Verify Redis Keys

```bash
# Connect to Redis CLI
redis-cli -h localhost -p 6379

# List all invitation rate limit keys
KEYS invitation_rate:*

# Example output:
# 1) "invitation_rate:550e8400-e29b-41d4-a716-446655440000:2026013112"

# Get value (invitation count)
GET invitation_rate:550e8400-e29b-41d4-a716-446655440000:2026013112

# Check TTL (time to live)
TTL invitation_rate:550e8400-e29b-41d4-a716-446655440000:2026013112
# Should return remaining seconds (up to 3600)

# List email rate limit keys
KEYS invitation_email:*

# Clear all test keys (cleanup)
DEL invitation_rate:550e8400-e29b-41d4-a716-446655440000:2026013112
```

---

## Step 5: Performance Monitoring (10 minutes)

### 5.1 Redis INFO Command

```bash
redis-cli -h localhost -p 6379 INFO

# Key metrics to monitor:
# - used_memory_human: Current memory usage
# - connected_clients: Number of active connections
# - total_commands_processed: Total commands executed
# - keyspace_hits: Cache hit rate
# - keyspace_misses: Cache miss rate
```

### 5.2 Monitor Real-Time Activity

```bash
# Monitor all commands in real-time
redis-cli -h localhost -p 6379 MONITOR

# Example output:
# 1643673600.123456 [0 127.0.0.1:12345] "INCR" "invitation_rate:uuid:2026013112"
# 1643673600.234567 [0 127.0.0.1:12345] "EXPIRE" "invitation_rate:uuid:2026013112" "3600"
```

### 5.3 Performance Benchmarks

```bash
# Benchmark Redis performance
redis-benchmark -h localhost -p 6379 -c 50 -n 10000

# Key metrics:
# - GET: ~50,000-100,000 requests/second
# - SET: ~50,000-100,000 requests/second
# - INCR: ~50,000-100,000 requests/second
```

---

## Troubleshooting

### Issue 1: Connection Refused

**Cause**: Redis not running

**Solutions**:
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis
docker start redis-invitations

# Or docker-compose
docker-compose up -d redis-invitations
```

### Issue 2: Authentication Failed

**Cause**: Wrong password or missing password

**Solutions**:
```bash
# Test connection with password
redis-cli -h localhost -p 6379 -a "your_password" ping

# Update REDIS_URL with password
REDIS_URL="redis://:your_password@localhost:6379/0"
```

### Issue 3: Too Many Connections

**Cause**: Connection pool exhausted

**Solutions**:
```python
# Increase max connections in config
REDIS_MAX_CONNECTIONS=20

# Or close unused connections
redis_client.connection_pool.disconnect()
```

---

## Success Criteria

- ✅ Redis running and accessible (PING → PONG)
- ✅ Backend can connect to Redis
- ✅ Rate limiting test passes (51st request blocked)
- ✅ Redis keys have correct TTL (3600s for team, 86400s for email)
- ✅ Performance benchmark >10,000 ops/second
- ✅ Memory usage <10MB (development)

---

## Next Steps

After Redis setup complete:
1. ✅ Update environment variables (.env.local)
2. ✅ Run integration tests (database + Redis + SendGrid)
3. ✅ Move to **Afternoon**: Code review session

---

**Status**: 🟡 **IN PROGRESS**
**Owner**: Backend Team
**Deadline**: January 31, 2026 (1 PM)
**Estimated Time**: 1 hour

---

**Last Updated**: January 31, 2026
**Next Review**: After successful rate limiting test
