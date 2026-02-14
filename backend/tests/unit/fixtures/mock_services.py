"""
=========================================================================
Mock Services for Unit Testing - RA-004 (Sprint 142)
SDLC Orchestrator - Stage 05 (TEST)

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 142 (Test Remediation)
Authority: Backend Lead + CTO Approved
Foundation: E2E API Testing Analysis (Feb 2, 2026)
Framework: SDLC 6.0.5 (RFC-SDLC-602 E2E API Testing)

Purpose:
- Provide reusable mock configurations for external services
- Enable unit tests to run without network dependencies
- Fix socket.gaierror failures in CI/CD environments

Services Mocked:
- Redis (rate limiting, session storage, cache)
- SMTP (email notifications)
- OPA (policy evaluation)
- MinIO (evidence storage)
- Ollama (AI code generation)

IMPORTANT: Zero Mock Policy Clarification
- These mocks are for TEST ISOLATION only
- Production code MUST use real service connections
- Mocks prevent socket errors when external services are unavailable
- This follows CTO directive from Sprint 142 approval

Reference: SPRINT-142-PROGRESS.md (RA-003, RA-004)
=========================================================================
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, AsyncMock, patch
import pytest


# ============================================================================
# Redis Mock Configuration
# ============================================================================

class MockRedis:
    """
    Mock Redis client for unit tests.

    Simulates Redis operations without network connection.
    Used for: rate limiting, session storage, token blacklist.

    Usage:
        from tests.unit.fixtures.mock_services import MockRedis

        def test_rate_limit(monkeypatch):
            mock_redis = MockRedis()
            monkeypatch.setattr("app.core.redis.redis_client", mock_redis)
            # Test rate limiting logic
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._ttl: Dict[str, int] = {}

    def ping(self) -> bool:
        """Simulate Redis ping."""
        return True

    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return self._store.get(key)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value with optional expiry."""
        self._store[key] = str(value)
        if ex:
            self._ttl[key] = ex
        return True

    def setex(self, key: str, time: int, value: Any) -> bool:
        """Set value with expiry."""
        self._store[key] = str(value)
        self._ttl[key] = time
        return True

    def delete(self, *keys: str) -> int:
        """Delete keys."""
        count = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                count += 1
            if key in self._ttl:
                del self._ttl[key]
        return count

    def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        return sum(1 for key in keys if key in self._store)

    def incr(self, key: str) -> int:
        """Increment value."""
        current = int(self._store.get(key, 0))
        self._store[key] = str(current + 1)
        return current + 1

    def decr(self, key: str) -> int:
        """Decrement value."""
        current = int(self._store.get(key, 0))
        self._store[key] = str(current - 1)
        return current - 1

    def expire(self, key: str, time: int) -> bool:
        """Set key expiry."""
        if key in self._store:
            self._ttl[key] = time
            return True
        return False

    def ttl(self, key: str) -> int:
        """Get time to live."""
        if key not in self._store:
            return -2  # Key doesn't exist
        return self._ttl.get(key, -1)  # -1 = no expiry

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if pattern == "*":
            return list(self._store.keys())
        # Simple wildcard matching
        import fnmatch
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    def pipeline(self) -> "MockRedisPipeline":
        """Return a mock pipeline."""
        return MockRedisPipeline(self)

    def close(self) -> None:
        """Close connection (no-op for mock)."""
        pass


class MockRedisPipeline:
    """Mock Redis pipeline for batch operations."""

    def __init__(self, redis: MockRedis):
        self._redis = redis
        self._commands: List[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def get(self, key: str) -> "MockRedisPipeline":
        self._commands.append(("get", key))
        return self

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> "MockRedisPipeline":
        self._commands.append(("set", key, value, ex))
        return self

    def delete(self, *keys: str) -> "MockRedisPipeline":
        self._commands.append(("delete", keys))
        return self

    def incr(self, key: str) -> "MockRedisPipeline":
        self._commands.append(("incr", key))
        return self

    def execute(self) -> List[Any]:
        """Execute all commands and return results."""
        results = []
        for cmd in self._commands:
            if cmd[0] == "get":
                results.append(self._redis.get(cmd[1]))
            elif cmd[0] == "set":
                results.append(self._redis.set(cmd[1], cmd[2], cmd[3] if len(cmd) > 3 else None))
            elif cmd[0] == "delete":
                results.append(self._redis.delete(*cmd[1]))
            elif cmd[0] == "incr":
                results.append(self._redis.incr(cmd[1]))
        self._commands = []
        return results


# ============================================================================
# SMTP Mock Configuration
# ============================================================================

class MockSMTP:
    """
    Mock SMTP client for unit tests.

    Captures sent emails without network connection.
    Used for: email notifications, invitation emails.

    Usage:
        from tests.unit.fixtures.mock_services import MockSMTP

        def test_send_invitation_email(monkeypatch):
            mock_smtp = MockSMTP()
            monkeypatch.setattr("smtplib.SMTP", lambda *args: mock_smtp)
            # Test email sending
            assert len(mock_smtp.sent_emails) == 1
    """

    def __init__(self, host: str = "", port: int = 587):
        self.host = host
        self.port = port
        self.sent_emails: List[Dict[str, Any]] = []
        self._logged_in = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def starttls(self) -> tuple:
        """Start TLS (no-op for mock)."""
        return (220, "TLS started")

    def login(self, user: str, password: str) -> tuple:
        """Login (no-op for mock)."""
        self._logged_in = True
        return (235, "Authentication successful")

    def sendmail(self, from_addr: str, to_addrs: List[str], msg: str) -> Dict[str, tuple]:
        """Send email and capture it."""
        self.sent_emails.append({
            "from": from_addr,
            "to": to_addrs,
            "message": msg,
        })
        return {}

    def send_message(self, msg: Any) -> Dict[str, tuple]:
        """Send message object and capture it."""
        self.sent_emails.append({
            "from": getattr(msg, "from_", ""),
            "to": getattr(msg, "to", []),
            "subject": getattr(msg, "subject", ""),
            "message": str(msg),
        })
        return {}

    def quit(self) -> tuple:
        """Quit connection (no-op for mock)."""
        return (221, "Bye")

    def close(self) -> None:
        """Close connection (no-op for mock)."""
        pass


# ============================================================================
# OPA Mock Configuration
# ============================================================================

class MockOPAClient:
    """
    Mock OPA client for unit tests.

    Simulates policy evaluation without network connection.
    Used for: gate validation, policy checks.

    Usage:
        from tests.unit.fixtures.mock_services import MockOPAClient

        async def test_policy_evaluation():
            mock_opa = MockOPAClient()
            mock_opa.set_policy_result("sdlc.g1.frd", True)
            result = await mock_opa.evaluate("sdlc.g1.frd", {"complete": True})
            assert result["allow"] == True
    """

    def __init__(self):
        self._policies: Dict[str, bool] = {}
        self._default_result = True

    def set_policy_result(self, policy_path: str, allow: bool) -> None:
        """Set expected result for a policy."""
        self._policies[policy_path] = allow

    def set_default_result(self, allow: bool) -> None:
        """Set default result for policies not explicitly configured."""
        self._default_result = allow

    async def evaluate(self, policy_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a policy and return result."""
        allow = self._policies.get(policy_path, self._default_result)
        return {
            "result": allow,
            "allow": allow,
            "policy": policy_path,
            "input": input_data,
        }

    async def compile_policy(self, rego_code: str) -> bool:
        """Compile Rego policy (always succeeds for mock)."""
        return True

    async def upload_policy(self, policy_id: str, rego_code: str) -> bool:
        """Upload policy to OPA (always succeeds for mock)."""
        return True

    async def health_check(self) -> bool:
        """Check OPA health (always healthy for mock)."""
        return True


# ============================================================================
# MinIO Mock Configuration
# ============================================================================

class MockMinIOClient:
    """
    Mock MinIO client for unit tests.

    Simulates object storage without network connection.
    Used for: evidence upload, artifact storage.

    Usage:
        from tests.unit.fixtures.mock_services import MockMinIOClient

        def test_evidence_upload():
            mock_minio = MockMinIOClient()
            etag = mock_minio.put_object("evidence-vault", "test.json", b'{"test": true}')
            assert etag is not None
    """

    def __init__(self):
        self._buckets: Dict[str, Dict[str, bytes]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if bucket exists."""
        return bucket_name in self._buckets

    def make_bucket(self, bucket_name: str) -> None:
        """Create a bucket."""
        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = {}
            self._metadata[bucket_name] = {}

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: Any,
        length: int = -1,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload object and return ETag."""
        import hashlib

        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = {}
            self._metadata[bucket_name] = {}

        # Handle different data types
        if hasattr(data, "read"):
            content = data.read()
        elif isinstance(data, bytes):
            content = data
        else:
            content = str(data).encode()

        self._buckets[bucket_name][object_name] = content
        self._metadata[bucket_name][object_name] = {
            "content_type": content_type,
            "size": len(content),
            "metadata": metadata or {},
        }

        # Generate ETag (MD5 hash)
        etag = hashlib.md5(content).hexdigest()
        self._metadata[bucket_name][object_name]["etag"] = etag
        return etag

    def get_object(self, bucket_name: str, object_name: str) -> Any:
        """Get object content."""
        if bucket_name not in self._buckets or object_name not in self._buckets[bucket_name]:
            raise Exception(f"Object not found: {bucket_name}/{object_name}")

        class MockResponse:
            def __init__(self, content: bytes):
                self._content = content

            def read(self) -> bytes:
                return self._content

            def close(self) -> None:
                pass

        return MockResponse(self._buckets[bucket_name][object_name])

    def stat_object(self, bucket_name: str, object_name: str) -> Any:
        """Get object metadata."""
        if bucket_name not in self._metadata or object_name not in self._metadata[bucket_name]:
            raise Exception(f"Object not found: {bucket_name}/{object_name}")

        meta = self._metadata[bucket_name][object_name]

        class MockStat:
            def __init__(self, m: Dict[str, Any]):
                self.size = m["size"]
                self.etag = m["etag"]
                self.content_type = m["content_type"]
                self.metadata = m.get("metadata", {})

        return MockStat(meta)

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        """Remove object."""
        if bucket_name in self._buckets and object_name in self._buckets[bucket_name]:
            del self._buckets[bucket_name][object_name]
            del self._metadata[bucket_name][object_name]

    def list_objects(self, bucket_name: str, prefix: str = "") -> List[Any]:
        """List objects in bucket."""
        if bucket_name not in self._buckets:
            return []

        class MockObject:
            def __init__(self, name: str, size: int):
                self.object_name = name
                self.size = size

        return [
            MockObject(name, self._metadata[bucket_name][name]["size"])
            for name in self._buckets[bucket_name].keys()
            if name.startswith(prefix)
        ]


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def mock_redis_instance():
    """
    Provide a fresh MockRedis instance for each test.

    Usage:
        def test_rate_limiting(mock_redis_instance):
            mock_redis_instance.set("rate:user:1", "5")
            assert mock_redis_instance.get("rate:user:1") == "5"
    """
    return MockRedis()


@pytest.fixture
def mock_smtp_instance():
    """
    Provide a fresh MockSMTP instance for each test.

    Usage:
        def test_email_sending(mock_smtp_instance, monkeypatch):
            monkeypatch.setattr("smtplib.SMTP", lambda *args: mock_smtp_instance)
            # Send email...
            assert len(mock_smtp_instance.sent_emails) == 1
    """
    return MockSMTP()


@pytest.fixture
def mock_opa_instance():
    """
    Provide a fresh MockOPAClient instance for each test.

    Usage:
        async def test_policy_check(mock_opa_instance):
            mock_opa_instance.set_policy_result("sdlc.g1.frd", True)
            result = await mock_opa_instance.evaluate("sdlc.g1.frd", {})
            assert result["allow"] == True
    """
    return MockOPAClient()


@pytest.fixture
def mock_minio_instance():
    """
    Provide a fresh MockMinIOClient instance for each test.

    Usage:
        def test_evidence_storage(mock_minio_instance):
            mock_minio_instance.make_bucket("evidence-vault")
            etag = mock_minio_instance.put_object("evidence-vault", "test.json", b'{}')
            assert etag is not None
    """
    return MockMinIOClient()


# ============================================================================
# Auto-use Fixtures (Apply to All Tests)
# ============================================================================

@pytest.fixture(autouse=True)
def auto_mock_external_services(monkeypatch):
    """
    Automatically mock external services for all unit tests.

    This fixture runs automatically for every test, ensuring:
    - No socket.gaierror from Redis/SMTP hostname resolution
    - Tests can run without external dependencies
    - Consistent test behavior in CI/CD

    Note: Integration tests may override this with real services.
    """
    # Mock Redis
    mock_redis = MockRedis()
    monkeypatch.setattr("app.core.redis.redis_client", mock_redis)
    monkeypatch.setattr("app.core.redis.get_redis_client", lambda: mock_redis)

    # Mock SMTP
    monkeypatch.setattr("smtplib.SMTP", MockSMTP)
    monkeypatch.setattr("smtplib.SMTP_SSL", MockSMTP)

    yield


# ============================================================================
# Test Summary
# ============================================================================
"""
Mock Services Summary (RA-004 - Sprint 142):

Classes:
- MockRedis: In-memory Redis simulation (rate limiting, cache)
- MockRedisPipeline: Batch Redis operations
- MockSMTP: Email capture without network
- MockOPAClient: Policy evaluation simulation
- MockMinIOClient: Object storage simulation

Fixtures:
- mock_redis_instance: Fresh MockRedis per test
- mock_smtp_instance: Fresh MockSMTP per test
- mock_opa_instance: Fresh MockOPAClient per test
- mock_minio_instance: Fresh MockMinIOClient per test
- auto_mock_external_services: Auto-applies mocks to all tests

Coverage:
- ✅ Redis: ping, get, set, delete, incr, expire, pipeline
- ✅ SMTP: starttls, login, sendmail, send_message
- ✅ OPA: evaluate, compile_policy, upload_policy
- ✅ MinIO: put_object, get_object, stat_object, remove_object

Zero Mock Policy Compliance:
- These mocks are for TEST ISOLATION only
- Production code uses real service connections
- Mocks prevent network errors in unit tests
"""
