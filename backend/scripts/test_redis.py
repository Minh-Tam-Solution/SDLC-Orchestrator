"""
Redis Connection Test Script

Tests Redis connectivity and basic operations.

Usage:
    REDIS_URL="redis://localhost:6379/0" python scripts/test_redis.py

Reference: Sprint 128 Infrastructure Setup
"""
import os
import sys
import redis
from datetime import datetime


def test_redis():
    """Test Redis connection and operations"""

    # Get Redis URL from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    print(f"📍 Redis URL: {redis_url}")
    print(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")
    print("\n" + "="*60)

    try:
        # Create Redis client
        print("\n1️⃣ Connecting to Redis...")
        client = redis.from_url(
            redis_url,
            socket_timeout=5,
            decode_responses=True
        )

        # Test 1: PING
        print("\n2️⃣ Testing PING command...")
        response = client.ping()
        if response:
            print(f"   ✅ PING successful: {response}")
        else:
            print(f"   ❌ PING failed")
            return False

        # Test 2: SET/GET
        print("\n3️⃣ Testing SET/GET commands...")
        test_key = "test_key_sprint128"
        test_value = f"hello_redis_{datetime.utcnow().timestamp()}"

        client.set(test_key, test_value)
        retrieved_value = client.get(test_key)

        if retrieved_value == test_value:
            print(f"   ✅ SET/GET successful")
            print(f"      Key: {test_key}")
            print(f"      Value: {retrieved_value}")
        else:
            print(f"   ❌ SET/GET failed")
            print(f"      Expected: {test_value}")
            print(f"      Got: {retrieved_value}")
            return False

        # Test 3: SETEX (with expiry)
        print("\n4️⃣ Testing SETEX (expiry) command...")
        expiry_key = "expiry_test_sprint128"
        expiry_value = "expires_in_5_seconds"

        client.setex(expiry_key, 5, expiry_value)
        ttl = client.ttl(expiry_key)

        if 0 < ttl <= 5:
            print(f"   ✅ SETEX successful")
            print(f"      Key: {expiry_key}")
            print(f"      TTL: {ttl} seconds")
        else:
            print(f"   ❌ SETEX failed (TTL: {ttl})")
            return False

        # Test 4: INCR (for rate limiting)
        print("\n5️⃣ Testing INCR command (rate limiting)...")
        counter_key = "counter_test_sprint128"

        # Delete key first (cleanup)
        client.delete(counter_key)

        # Increment 5 times
        for i in range(5):
            count = client.incr(counter_key)
            if count != i + 1:
                print(f"   ❌ INCR failed at iteration {i+1}")
                return False

        final_count = client.get(counter_key)
        if int(final_count) == 5:
            print(f"   ✅ INCR successful (final count: {final_count})")
        else:
            print(f"   ❌ INCR failed (expected 5, got {final_count})")
            return False

        # Test 5: DELETE
        print("\n6️⃣ Cleanup (DELETE commands)...")
        deleted = client.delete(test_key, expiry_key, counter_key)
        print(f"   ✅ Deleted {deleted} keys")

        # Test 6: INFO (server info)
        print("\n7️⃣ Redis Server Info:")
        info = client.info("server")
        print(f"   Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"   OS: {info.get('os', 'Unknown')}")
        print(f"   Uptime: {info.get('uptime_in_seconds', 0)} seconds")

        info_memory = client.info("memory")
        print(f"   Memory Used: {info_memory.get('used_memory_human', 'Unknown')}")

        info_stats = client.info("stats")
        print(f"   Total Connections: {info_stats.get('total_connections_received', 0)}")
        print(f"   Total Commands: {info_stats.get('total_commands_processed', 0)}")

        return True

    except redis.ConnectionError as e:
        print(f"\n❌ Connection Error: {str(e)}")
        print(f"\nTroubleshooting:")
        print(f"  - Check Redis is running: docker ps | grep redis")
        print(f"  - Verify Redis URL is correct: {redis_url}")
        print(f"  - Test with redis-cli: redis-cli -h localhost -p 6379 ping")
        return False

    except redis.AuthenticationError as e:
        print(f"\n❌ Authentication Error: {str(e)}")
        print(f"\nTroubleshooting:")
        print(f"  - Check Redis password in REDIS_URL")
        print(f"  - Format: redis://:password@host:port/db")
        return False

    except redis.TimeoutError as e:
        print(f"\n❌ Timeout Error: {str(e)}")
        print(f"\nTroubleshooting:")
        print(f"  - Redis server may be slow or unresponsive")
        print(f"  - Check server load: redis-cli INFO")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("REDIS CONNECTION TEST")
    print("Sprint 128 - Team Invitation System")
    print("="*60)

    success = test_redis()

    print("\n" + "="*60)

    if success:
        print("✅ ALL TESTS PASSED - Redis configuration is correct!")
        print("\nNext Steps:")
        print("  1. ✅ Redis connection verified")
        print("  2. ⏭️  Test rate limiting functions")
        print("  3. ⏭️  Run integration tests")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Please fix Redis configuration")
        print("\nTroubleshooting:")
        print("  - Review REDIS-SETUP-GUIDE.md")
        print("  - Check Redis server status")
        print("  - Verify network connectivity")
        sys.exit(1)
