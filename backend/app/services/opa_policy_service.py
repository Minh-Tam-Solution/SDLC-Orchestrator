"""
OPA Policy Service - Async Policy Evaluation Engine

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1 (10-Stage Lifecycle, 4-Tier Classification)
Epic: EP-02 AI Safety Layer v1

Purpose:
- Async policy evaluation via OPA REST API
- Policy loading and caching
- Parallel policy evaluation for performance
- Integration with ValidationPipeline

OPA Integration Strategy:
- Network-only access via HTTP REST API (AGPL-safe)
- Async httpx client for non-blocking I/O
- Docker process isolation (opa:8181 container)
- Timeout handling with circuit breaker pattern

Reference:
- docs/02-design/14-Technical-Specs/Policy-Guards-Design.md
- docs/04-build/05-SASE-Artifacts/MTS-AI-SAFETY.md

Version: 1.0.0
Updated: December 2025
Zero Mock Policy: Production-ready async implementation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.schemas.policy_pack import PolicyResult, PolicyRuleCreate, PolicySeverity

logger = logging.getLogger(__name__)


class OPAPolicyService:
    """
    Async OPA Policy Service for AI Safety Layer.

    Features:
    - Async HTTP client (httpx) for non-blocking evaluation
    - Policy caching with TTL
    - Parallel policy evaluation
    - Circuit breaker pattern for resilience

    AGPL-Safe Implementation:
    - Uses httpx library (BSD license)
    - Network-only access via HTTP REST API
    - No code dependencies on OPA libraries

    Usage:
        async with OPAPolicyService() as opa:
            results = await opa.evaluate_policies(policies, input_data)
    """

    # Cache configuration
    CACHE_TTL_SECONDS = 300  # 5 minutes

    # Circuit breaker configuration
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT_SECONDS = 30

    def __init__(self, opa_url: Optional[str] = None):
        """
        Initialize async OPA service.

        Args:
            opa_url: OPA REST API URL (default from settings)
        """
        self.opa_url = opa_url or settings.OPA_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self._client: Optional[httpx.AsyncClient] = None

        # Policy cache: {policy_id: (loaded_at, rego_hash)}
        self._policy_cache: Dict[str, tuple[datetime, str]] = {}

        # Circuit breaker state
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._circuit_open = False

        logger.info(f"OPA Policy Service initialized: {self.opa_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.opa_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, creating if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.opa_url,
                timeout=self.timeout,
            )
        return self._client

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self) -> bool:
        """
        Check if OPA server is healthy.

        Returns:
            True if OPA is healthy, False otherwise
        """
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OPA health check failed: {e}")
            return False

    # =========================================================================
    # Circuit Breaker
    # =========================================================================

    def _check_circuit(self) -> bool:
        """
        Check if circuit is open (should skip OPA calls).

        Returns:
            True if circuit is open (skip calls), False if closed (allow calls)
        """
        if not self._circuit_open:
            return False

        # Check if recovery timeout has passed
        if self._last_failure_time:
            recovery_time = self._last_failure_time + timedelta(
                seconds=self.RECOVERY_TIMEOUT_SECONDS
            )
            if datetime.utcnow() >= recovery_time:
                logger.info("Circuit breaker recovery timeout passed, closing circuit")
                self._circuit_open = False
                self._failure_count = 0
                return False

        return True

    def _record_success(self):
        """Record successful OPA call, reset failure count."""
        self._failure_count = 0
        self._circuit_open = False

    def _record_failure(self):
        """Record failed OPA call, potentially open circuit."""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()

        if self._failure_count >= self.FAILURE_THRESHOLD:
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
            self._circuit_open = True

    # =========================================================================
    # Policy Loading
    # =========================================================================

    def _is_policy_cached(self, policy_id: str, rego_hash: str) -> bool:
        """Check if policy is cached and still valid."""
        if policy_id not in self._policy_cache:
            return False

        loaded_at, cached_hash = self._policy_cache[policy_id]

        # Check TTL
        if datetime.utcnow() - loaded_at > timedelta(seconds=self.CACHE_TTL_SECONDS):
            return False

        # Check if policy content changed
        return cached_hash == rego_hash

    async def load_policy(self, policy: PolicyRuleCreate) -> bool:
        """
        Load a Rego policy to OPA server.

        Args:
            policy: Policy rule to load

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._check_circuit():
            logger.warning(f"Circuit open, skipping policy load: {policy.policy_id}")
            return False

        # Compute rego hash for cache validation
        rego_hash = str(hash(policy.rego_policy))

        # Skip if already cached with same content
        if self._is_policy_cached(policy.policy_id, rego_hash):
            logger.debug(f"Policy already cached: {policy.policy_id}")
            return True

        try:
            response = await self.client.put(
                f"/v1/policies/{policy.policy_id}",
                content=policy.rego_policy,
                headers={"Content-Type": "text/plain"},
            )

            if response.status_code == 200:
                self._policy_cache[policy.policy_id] = (datetime.utcnow(), rego_hash)
                self._record_success()
                logger.info(f"Loaded policy: {policy.policy_id}")
                return True
            else:
                logger.error(
                    f"Failed to load policy {policy.policy_id}: "
                    f"status={response.status_code}, body={response.text}"
                )
                self._record_failure()
                return False

        except Exception as e:
            logger.error(f"Error loading policy {policy.policy_id}: {e}")
            self._record_failure()
            return False

    # =========================================================================
    # Policy Evaluation
    # =========================================================================

    async def evaluate_policy(
        self,
        policy: PolicyRuleCreate,
        input_data: Dict[str, Any],
    ) -> PolicyResult:
        """
        Evaluate a single policy against input data.

        Args:
            policy: Policy rule to evaluate
            input_data: Input data for OPA (files, diff, config)

        Returns:
            PolicyResult with pass/fail status and violations
        """
        start_time = datetime.utcnow()

        # Check circuit breaker
        if self._check_circuit():
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return PolicyResult(
                policy_id=policy.policy_id,
                policy_name=policy.name,
                passed=True,  # Fail open
                severity=policy.severity,
                blocking=policy.blocking,
                message="Circuit breaker open, policy skipped",
                violations=[],
                evaluation_time_ms=duration_ms,
            )

        try:
            # Ensure policy is loaded
            await self.load_policy(policy)

            # Construct package path from policy_id
            # Format: ai_safety.{policy_id with - replaced by _}
            package_name = f"ai_safety.{policy.policy_id.replace('-', '_')}"

            # Evaluate policy - get allow result
            response = await self.client.post(
                f"/v1/data/{package_name}/allow",
                json={"input": input_data},
            )

            if response.status_code != 200:
                raise Exception(f"OPA returned status {response.status_code}")

            result_data = response.json()
            passed = result_data.get("result", True)  # Default to allow

            # Get violations if policy failed
            violations = []
            if not passed:
                try:
                    violations_response = await self.client.post(
                        f"/v1/data/{package_name}/violations",
                        json={"input": input_data},
                    )
                    if violations_response.status_code == 200:
                        raw_violations = violations_response.json().get("result", [])
                        # Convert to PolicyViolation format
                        violations = [
                            {
                                "file": v.get("file", "unknown"),
                                "line": v.get("line"),
                                "message": v.get("message", str(v)),
                                "pattern": v.get("pattern"),
                            }
                            for v in raw_violations
                        ]
                except Exception as e:
                    logger.warning(f"Failed to get violations: {e}")

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._record_success()

            # Format message from template
            message = None
            if not passed and violations:
                # Use first violation to format message
                first_violation = violations[0]
                message = policy.message_template.format(
                    file=first_violation.get("file", "unknown"),
                    line=first_violation.get("line", "?"),
                    message=first_violation.get("message", ""),
                )

            return PolicyResult(
                policy_id=policy.policy_id,
                policy_name=policy.name,
                passed=passed,
                severity=policy.severity,
                blocking=policy.blocking,
                message=message,
                violations=violations,
                evaluation_time_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._record_failure()
            logger.error(f"Error evaluating policy {policy.policy_id}: {e}")

            return PolicyResult(
                policy_id=policy.policy_id,
                policy_name=policy.name,
                passed=True,  # Fail open
                severity=policy.severity,
                blocking=policy.blocking,
                message=f"Evaluation error: {str(e)}",
                violations=[],
                evaluation_time_ms=duration_ms,
            )

    async def evaluate_policies(
        self,
        policies: List[PolicyRuleCreate],
        input_data: Dict[str, Any],
    ) -> List[PolicyResult]:
        """
        Evaluate multiple policies in parallel.

        Args:
            policies: List of policies to evaluate
            input_data: Input data for OPA

        Returns:
            List of PolicyResult for each policy
        """
        # Filter enabled policies
        enabled_policies = [p for p in policies if p.enabled]

        if not enabled_policies:
            return []

        # Create evaluation tasks
        tasks = [
            self.evaluate_policy(policy, input_data)
            for policy in enabled_policies
        ]

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, PolicyResult):
                final_results.append(result)
            else:
                # Exception occurred
                policy = enabled_policies[i]
                final_results.append(
                    PolicyResult(
                        policy_id=policy.policy_id,
                        policy_name=policy.name,
                        passed=True,  # Fail open
                        severity=PolicySeverity.INFO,
                        blocking=False,
                        message=f"Evaluation failed: {str(result)}",
                        violations=[],
                        evaluation_time_ms=0,
                    )
                )

        return final_results

    # =========================================================================
    # Cleanup
    # =========================================================================

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# ============================================================================
# Singleton Instance
# ============================================================================

# Lazy singleton - use get_opa_policy_service() to get instance
_opa_policy_service: Optional[OPAPolicyService] = None


def get_opa_policy_service() -> OPAPolicyService:
    """Get or create OPA Policy Service singleton."""
    global _opa_policy_service
    if _opa_policy_service is None:
        _opa_policy_service = OPAPolicyService()
    return _opa_policy_service
