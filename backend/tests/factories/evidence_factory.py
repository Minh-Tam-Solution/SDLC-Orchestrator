"""
Evidence Factory - Test Data Generation

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Generate GateEvidence model instances and data dictionaries for testing.

Principles:
    1. Sensible defaults (realistic evidence data)
    2. Override support (Partial[GateEvidence])
    3. Valid model instances (pass validation)
    4. SHA256 integrity hashing support

Usage:
    # Get Evidence instance
    evidence = get_mock_evidence()
    pdf = get_mock_evidence({"file_type": "application/pdf"})

    # Get data dict (for API requests)
    evidence_data = get_mock_evidence_data()
    upload_data = get_mock_evidence_upload_data({"file_name": "test.pdf"})

Reference:
    - GateEvidence Model: backend/app/models/gate_evidence.py
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md § 3.5
    - FR2: Evidence Vault
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import uuid4
import hashlib


def generate_sha256_hash(content: str = "test content") -> str:
    """Generate SHA256 hash for test data"""
    return hashlib.sha256(content.encode()).hexdigest()


def get_mock_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for GateEvidence model instance data.

    Returns a dictionary representing a GateEvidence model instance with sensible defaults.
    Use this when you need a complete GateEvidence object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with GateEvidence model fields

    Examples:
        # Basic evidence (design document)
        evidence = get_mock_evidence()

        # Test results evidence
        test_evidence = get_mock_evidence({
            "file_name": "test-results.json",
            "file_type": "application/json",
            "evidence_type": "TEST_RESULTS",
        })

        # PDF documentation
        pdf_evidence = get_mock_evidence({
            "file_name": "architecture.pdf",
            "file_type": "application/pdf",
            "file_size": 5242880,  # 5MB
        })
    """
    defaults = {
        "id": str(uuid4()),
        "gate_id": str(uuid4()),
        "file_name": "data-model-v0.1.md",
        "file_size": 1400000,  # 1.4MB
        "file_type": "text/markdown",
        "evidence_type": "DESIGN_DOCUMENT",
        "s3_key": f"evidence/{uuid4()}/data-model-v0.1.md",
        "s3_bucket": "sdlc-evidence",
        "sha256_hash": generate_sha256_hash("test evidence content"),
        "description": "Data Model v0.1 - PostgreSQL schema design",
        "uploaded_by": str(uuid4()),
        "uploaded_at": datetime.now(UTC),
        "created_at": datetime.now(UTC),
        "deleted_at": None,
    }

    return {**defaults, **(overrides or {})}


def get_mock_evidence_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Evidence data (API response format).

    Returns a dictionary suitable for API response serialization.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with GateEvidence API response fields

    Examples:
        # API response data
        response_data = get_mock_evidence_data()

        # Custom evidence response
        evidence_data = get_mock_evidence_data({
            "file_name": "test-coverage.html",
            "evidence_type": "TEST_RESULTS",
        })
    """
    evidence = get_mock_evidence(overrides)

    api_safe_fields = {
        "id": evidence["id"],
        "gate_id": evidence["gate_id"],
        "file_name": evidence["file_name"],
        "file_size": evidence["file_size"],
        "file_type": evidence["file_type"],
        "evidence_type": evidence["evidence_type"],
        "sha256_hash": evidence["sha256_hash"],
        "description": evidence["description"],
        "uploaded_by": evidence["uploaded_by"],
        "uploaded_at": evidence["uploaded_at"].isoformat() if isinstance(evidence["uploaded_at"], datetime) else evidence["uploaded_at"],
        "created_at": evidence["created_at"].isoformat() if isinstance(evidence["created_at"], datetime) else evidence["created_at"],
    }

    return api_safe_fields


def get_mock_evidence_upload_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Evidence upload request data (API POST payload).

    Returns a dictionary suitable for API POST /api/v1/evidence request.
    Contains only fields required for evidence upload.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Evidence upload request fields

    Examples:
        # Upload evidence
        upload_data = get_mock_evidence_upload_data()
        response = client.post("/api/v1/evidence", data=upload_data, files={"file": file_obj})

        # Upload test results
        test_data = get_mock_evidence_upload_data({
            "gate_id": gate_id,
            "evidence_type": "TEST_RESULTS",
            "description": "Unit test coverage report",
        })
    """
    defaults = {
        "gate_id": str(uuid4()),
        "evidence_type": "DESIGN_DOCUMENT",
        "description": "Test evidence for automated testing",
    }

    return {**defaults, **(overrides or {})}


# ─────────────────────────────────────────────────────────────
# Evidence Type-Specific Factories
# ─────────────────────────────────────────────────────────────

def get_mock_design_document_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for design document evidence"""
    design_defaults = {
        "file_name": "architecture-design.md",
        "file_type": "text/markdown",
        "file_size": 2048000,  # 2MB
        "evidence_type": "DESIGN_DOCUMENT",
        "description": "System architecture design document",
    }
    return get_mock_evidence({**design_defaults, **(overrides or {})})


def get_mock_test_results_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for test results evidence"""
    test_defaults = {
        "file_name": "test-results.json",
        "file_type": "application/json",
        "file_size": 512000,  # 512KB
        "evidence_type": "TEST_RESULTS",
        "description": "Unit and integration test results",
    }
    return get_mock_evidence({**test_defaults, **(overrides or {})})


def get_mock_code_review_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for code review evidence"""
    review_defaults = {
        "file_name": "code-review-report.pdf",
        "file_type": "application/pdf",
        "file_size": 1024000,  # 1MB
        "evidence_type": "CODE_REVIEW",
        "description": "Peer code review report with findings",
    }
    return get_mock_evidence({**review_defaults, **(overrides or {})})


def get_mock_deployment_proof_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for deployment proof evidence"""
    deployment_defaults = {
        "file_name": "deployment-logs.txt",
        "file_type": "text/plain",
        "file_size": 256000,  # 256KB
        "evidence_type": "DEPLOYMENT_PROOF",
        "description": "Production deployment logs and screenshots",
    }
    return get_mock_evidence({**deployment_defaults, **(overrides or {})})


def get_mock_documentation_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for documentation evidence"""
    doc_defaults = {
        "file_name": "api-documentation.md",
        "file_type": "text/markdown",
        "file_size": 768000,  # 768KB
        "evidence_type": "DOCUMENTATION",
        "description": "API reference documentation with examples",
    }
    return get_mock_evidence({**doc_defaults, **(overrides or {})})


def get_mock_compliance_evidence(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for compliance evidence"""
    compliance_defaults = {
        "file_name": "security-scan-report.pdf",
        "file_type": "application/pdf",
        "file_size": 3145728,  # 3MB
        "evidence_type": "COMPLIANCE",
        "description": "OWASP ASVS Level 2 compliance scan results",
    }
    return get_mock_evidence({**compliance_defaults, **(overrides or {})})


# ─────────────────────────────────────────────────────────────
# Integrity Verification Helper
# ─────────────────────────────────────────────────────────────

def verify_evidence_integrity(evidence: Dict[str, Any], actual_content: str) -> bool:
    """
    Verify evidence integrity by comparing SHA256 hashes.

    Args:
        evidence: Evidence dict with sha256_hash field
        actual_content: Actual file content to verify

    Returns:
        True if hash matches, False otherwise

    Example:
        evidence = get_mock_evidence()
        content = "test evidence content"
        is_valid = verify_evidence_integrity(evidence, content)
    """
    expected_hash = evidence["sha256_hash"]
    actual_hash = generate_sha256_hash(actual_content)
    return expected_hash == actual_hash
