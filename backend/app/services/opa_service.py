"""
=========================================================================
OPA Service Adapter - Policy-as-Code Evaluation Engine (FR1 + FR5)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 4, 2025
Status: ACTIVE - Week 4 Day 4 (OPA Integration)
Authority: Backend Lead + CTO Approved
Foundation: FR1 (Gate Engine), FR5 (Policy Pack Library), Data Model v0.1
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Policy-as-Code evaluation via OPA REST API
- Rego policy compilation and validation
- Gate approval/rejection based on policy results
- Policy violation tracking and reporting

OPA Integration Strategy:
✅ Network-only access via HTTP REST API (AGPL-safe)
✅ NO OPA SDK imports (avoid tight coupling)
✅ Docker process isolation (opa:8181 container)
✅ Timeout handling (5s default, fail-safe)

Legal Precedent:
- MongoDB SSPL (2018): Network-only access is safe
- OPA is Apache 2.0 (permissive license, not AGPL)
- Legal counsel approved (2025-11-25 AGPL Containment Brief)

Zero Mock Policy: 100% real implementation (requests + Rego)
=========================================================================
"""

import logging
from typing import Any, Optional

import requests
from requests.exceptions import RequestException, Timeout

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# OPA Client Configuration
# ============================================================================


class OPAService:
    """
    OPA (Open Policy Agent) service adapter using REST API.

    AGPL-Safe Implementation:
    - Uses Python requests library (Apache 2.0 license)
    - Network-only access via HTTP REST API
    - No code dependencies on OPA libraries

    OPA REST API Endpoints:
    - POST /v1/data/{package_path} - Evaluate policy
    - PUT /v1/policies/{policy_id} - Upload Rego policy
    - GET /v1/policies - List policies
    - DELETE /v1/policies/{policy_id} - Delete policy

    Usage:
        opa = OPAService()
        result = opa.evaluate_policy(
            policy_code="FRD_COMPLETENESS",
            stage="WHAT",
            input_data={"frd_sections": {...}}
        )
        if result["allowed"]:
            print("Policy passed!")
        else:
            print(f"Policy failed: {result['violations']}")
    """

    def __init__(self):
        """Initialize OPA service with REST API endpoint."""
        self.base_url = settings.OPA_URL
        self.timeout = 5  # 5 seconds timeout (fail-safe)

        logger.info(f"OPA service initialized: {self.base_url}")

    # ============================================================================
    # Policy Evaluation
    # ============================================================================

    def evaluate_policy(
        self,
        policy_code: str,
        stage: str,
        input_data: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Evaluate policy against input data using OPA REST API.

        OPA evaluates Rego policies in the format:
            package sdlc.gates.{stage}.{policy_code}

            default allowed = false

            allowed {
                # Rego evaluation logic
                input.frd_sections["Introduction"]
                input.frd_sections["Functional Requirements"]
            }

            violations[msg] {
                not input.frd_sections["Introduction"]
                msg := "FRD missing required section: Introduction"
            }

        Args:
            policy_code: Policy identifier (e.g., "FRD_COMPLETENESS")
            stage: SDLC stage (e.g., "WHAT", "HOW", "BUILD")
            input_data: Input data for policy evaluation (dict)
            timeout: Request timeout in seconds (default: 5s)

        Returns:
            Policy evaluation result:
            {
                "allowed": bool,  # True if policy passed
                "violations": list[str],  # List of violation messages (empty if passed)
                "metadata": dict,  # Additional metadata (execution time, etc.)
            }

        Raises:
            OPAEvaluationError: If OPA request fails

        Example:
            result = opa.evaluate_policy(
                policy_code="FRD_COMPLETENESS",
                stage="WHAT",
                input_data={
                    "frd_sections": {
                        "Introduction": "Project overview...",
                        "Functional Requirements": "FR1, FR2, FR3...",
                        "API Contracts": "OpenAPI spec..."
                    }
                }
            )

            if result["allowed"]:
                print("✅ FRD completeness check passed!")
            else:
                print(f"❌ Policy failed: {result['violations']}")
        """
        # Construct OPA package path
        # Format: sdlc/gates/{stage}/{policy_code}
        package_path = f"sdlc/gates/{stage.lower()}/{policy_code.lower()}"
        url = f"{self.base_url}/v1/data/{package_path}"

        # Prepare request payload
        payload = {"input": input_data}

        # Set timeout
        timeout = timeout or self.timeout

        try:
            # Call OPA REST API
            logger.debug(f"Evaluating policy: {package_path} (timeout={timeout}s)")
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )

            # Handle HTTP errors
            response.raise_for_status()

            # Parse OPA response
            opa_response = response.json()

            # Extract result
            result = opa_response.get("result", {})

            # Parse allowed/violations
            allowed = result.get("allowed", False)
            violations = result.get("violations", [])

            # Return structured result
            return {
                "allowed": allowed,
                "violations": violations,
                "metadata": {
                    "policy_code": policy_code,
                    "stage": stage,
                    "package_path": package_path,
                    "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                },
            }

        except Timeout:
            logger.error(f"OPA request timeout after {timeout}s: {url}")
            raise OPAEvaluationError(
                f"Policy evaluation timed out after {timeout}s. "
                f"Policy: {policy_code}, Stage: {stage}"
            )

        except RequestException as e:
            logger.error(f"OPA request failed: {url}, Error: {e}")
            raise OPAEvaluationError(
                f"Failed to evaluate policy via OPA. "
                f"Policy: {policy_code}, Stage: {stage}, Error: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error during OPA evaluation: {e}")
            raise OPAEvaluationError(
                f"Unexpected error during policy evaluation. "
                f"Policy: {policy_code}, Stage: {stage}, Error: {str(e)}"
            )

    # ============================================================================
    # Policy Management
    # ============================================================================

    def upload_policy(
        self,
        policy_id: str,
        rego_code: str,
    ) -> dict[str, Any]:
        """
        Upload Rego policy to OPA.

        Args:
            policy_id: Policy identifier (e.g., "frd_completeness")
            rego_code: Rego policy code (string)

        Returns:
            Upload result:
            {
                "success": bool,
                "policy_id": str,
                "message": str
            }

        Raises:
            OPAEvaluationError: If upload fails

        Example:
            rego_code = '''
            package sdlc.gates.what.frd_completeness

            default allowed = false

            allowed {
                input.frd_sections["Introduction"]
                input.frd_sections["Functional Requirements"]
            }

            violations[msg] {
                not input.frd_sections["Introduction"]
                msg := "FRD missing required section: Introduction"
            }
            '''

            result = opa.upload_policy("frd_completeness", rego_code)
            if result["success"]:
                print(f"✅ Policy uploaded: {policy_id}")
        """
        url = f"{self.base_url}/v1/policies/{policy_id}"

        try:
            logger.debug(f"Uploading policy: {policy_id}")
            response = requests.put(
                url,
                data=rego_code,
                timeout=self.timeout,
                headers={"Content-Type": "text/plain"},
            )

            response.raise_for_status()

            logger.info(f"Policy uploaded successfully: {policy_id}")

            return {
                "success": True,
                "policy_id": policy_id,
                "message": "Policy uploaded successfully",
            }

        except RequestException as e:
            logger.error(f"Failed to upload policy: {policy_id}, Error: {e}")
            raise OPAEvaluationError(
                f"Failed to upload policy to OPA. "
                f"Policy: {policy_id}, Error: {str(e)}"
            )

    def delete_policy(self, policy_id: str) -> dict[str, Any]:
        """
        Delete Rego policy from OPA.

        Args:
            policy_id: Policy identifier

        Returns:
            Deletion result:
            {
                "success": bool,
                "policy_id": str,
                "message": str
            }

        Raises:
            OPAEvaluationError: If deletion fails

        Example:
            result = opa.delete_policy("frd_completeness")
            if result["success"]:
                print(f"✅ Policy deleted: {policy_id}")
        """
        url = f"{self.base_url}/v1/policies/{policy_id}"

        try:
            logger.debug(f"Deleting policy: {policy_id}")
            response = requests.delete(
                url,
                timeout=self.timeout,
            )

            response.raise_for_status()

            logger.info(f"Policy deleted successfully: {policy_id}")

            return {
                "success": True,
                "policy_id": policy_id,
                "message": "Policy deleted successfully",
            }

        except RequestException as e:
            logger.error(f"Failed to delete policy: {policy_id}, Error: {e}")
            raise OPAEvaluationError(
                f"Failed to delete policy from OPA. "
                f"Policy: {policy_id}, Error: {str(e)}"
            )

    def list_policies(self) -> dict[str, Any]:
        """
        List all policies in OPA.

        Returns:
            List of policy IDs:
            {
                "policies": list[str],
                "total": int
            }

        Raises:
            OPAEvaluationError: If request fails

        Example:
            result = opa.list_policies()
            print(f"Total policies: {result['total']}")
            for policy_id in result["policies"]:
                print(f"  - {policy_id}")
        """
        url = f"{self.base_url}/v1/policies"

        try:
            logger.debug("Listing OPA policies")
            response = requests.get(
                url,
                timeout=self.timeout,
            )

            response.raise_for_status()

            # Parse response
            opa_response = response.json()
            policies = opa_response.get("result", [])

            # Extract policy IDs
            policy_ids = []
            if isinstance(policies, list):
                policy_ids = policies
            elif isinstance(policies, dict):
                policy_ids = list(policies.keys())

            logger.debug(f"Found {len(policy_ids)} policies in OPA")

            return {
                "policies": policy_ids,
                "total": len(policy_ids),
            }

        except RequestException as e:
            logger.error(f"Failed to list policies: {e}")
            raise OPAEvaluationError(
                f"Failed to list policies from OPA. Error: {str(e)}"
            )

    # ============================================================================
    # Batch Evaluation (Sprint 111)
    # ============================================================================

    def batch_evaluate(
        self,
        evaluations: list[dict[str, Any]],
        timeout: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Evaluate multiple policies in batch.

        Sprint 111 Day 5: Batch policy evaluation for performance optimization.

        Args:
            evaluations: List of evaluation requests:
                [
                    {
                        "policy_code": "FRD_COMPLETENESS",
                        "stage": "WHAT",
                        "input_data": {...}
                    },
                    ...
                ]
            timeout: Request timeout per evaluation in seconds

        Returns:
            List of evaluation results (same order as input):
            [
                {
                    "allowed": bool,
                    "violations": list[str],
                    "metadata": dict,
                    "error": str | None  # If evaluation failed
                },
                ...
            ]

        Example:
            evaluations = [
                {"policy_code": "FRD_COMPLETENESS", "stage": "WHAT", "input_data": {...}},
                {"policy_code": "API_COVERAGE", "stage": "HOW", "input_data": {...}},
            ]
            results = opa.batch_evaluate(evaluations)
            for i, result in enumerate(results):
                if result.get("error"):
                    print(f"Evaluation {i} failed: {result['error']}")
                elif result["allowed"]:
                    print(f"Evaluation {i}: PASSED")
                else:
                    print(f"Evaluation {i}: FAILED - {result['violations']}")
        """
        results = []

        for evaluation in evaluations:
            try:
                result = self.evaluate_policy(
                    policy_code=evaluation.get("policy_code", "unknown"),
                    stage=evaluation.get("stage", "unknown"),
                    input_data=evaluation.get("input_data", {}),
                    timeout=timeout,
                )
                result["error"] = None
                results.append(result)

            except OPAEvaluationError as e:
                results.append({
                    "allowed": False,
                    "violations": [],
                    "metadata": {
                        "policy_code": evaluation.get("policy_code"),
                        "stage": evaluation.get("stage"),
                    },
                    "error": str(e),
                })

            except Exception as e:
                results.append({
                    "allowed": False,
                    "violations": [],
                    "metadata": {
                        "policy_code": evaluation.get("policy_code"),
                        "stage": evaluation.get("stage"),
                    },
                    "error": f"Unexpected error: {str(e)}",
                })

        logger.info(f"Batch evaluation complete: {len(results)} policies evaluated")
        return results

    # ============================================================================
    # Health Check
    # ============================================================================

    def health_check(self) -> dict[str, Any]:
        """
        Check OPA service health.

        Returns:
            Health status:
            {
                "healthy": bool,
                "version": str,
                "uptime_seconds": int
            }

        Example:
            health = opa.health_check()
            if health["healthy"]:
                print(f"✅ OPA is healthy (version: {health['version']})")
            else:
                print("❌ OPA is unhealthy")
        """
        url = f"{self.base_url}/health"

        try:
            logger.debug("Checking OPA health")
            response = requests.get(
                url,
                timeout=self.timeout,
            )

            # OPA health endpoint returns 200 if healthy
            is_healthy = response.status_code == 200

            # Try to get version info
            version = "unknown"
            uptime = 0
            try:
                health_data = response.json()
                version = health_data.get("version", "unknown")
                uptime = health_data.get("uptime_seconds", 0)
            except Exception:
                pass

            return {
                "healthy": is_healthy,
                "version": version,
                "uptime_seconds": uptime,
            }

        except Exception as e:
            logger.error(f"OPA health check failed: {e}")
            return {
                "healthy": False,
                "version": "unknown",
                "uptime_seconds": 0,
                "error": str(e),
            }


# ============================================================================
# Custom Exceptions
# ============================================================================


class OPAEvaluationError(Exception):
    """Exception raised when OPA policy evaluation fails."""

    pass


# ============================================================================
# Global OPA Service Instance
# ============================================================================

# Singleton instance (initialized on first import)
opa_service = OPAService()
