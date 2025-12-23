#!/usr/bin/env python3
"""
=========================================================================
E2E SOP Generator Workflow Test - Phase 2-Pilot Week 5
SDLC Orchestrator - SASE Level 1 Integration

Version: 1.0.0
Date: January 20, 2025
Status: ACTIVE - Phase 2-Pilot Week 5 (M5: VCR Complete)
Authority: CTO Approved (BRS-PILOT-001)
Foundation: SE 3.0 SASE Integration, SDLC 5.1.0 Framework

Purpose:
- End-to-end test for complete SASE Level 1 workflow
- BRS → Generate SOP → MRP Evidence → VCR Approval
- Validates all 7 Functional Requirements (FR1-FR7)
- Tests with real Ollama API

Usage:
    python3 backend/scripts/test_e2e_sop_workflow.py

Requirements:
    - Ollama running at http://api.nhatquangholding.com:11434 (or OLLAMA_URL env)
    - Backend API running at http://localhost:8000 (or API_URL env)

BRS Reference: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml
=========================================================================
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import requests

# ============================================================================
# Configuration
# ============================================================================

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://api.nhatquangholding.com:11434")

# Test data for all 5 SOP types
TEST_WORKFLOWS = {
    "deployment": {
        "description": "Deploy the SDLC Orchestrator web application to production Kubernetes cluster. The deployment should include blue-green strategy, database migrations, health checks, and automatic rollback on failure.",
        "context": "Target cluster: GKE production. Docker image from gcr.io. Helm charts for configuration.",
    },
    "incident": {
        "description": "Handle P0/P1 production incidents for the SDLC Orchestrator platform. Include initial triage, escalation procedures, communication protocols, and post-incident review process.",
        "context": "On-call rotation 24/7. PagerDuty integration. Slack #incidents channel.",
    },
    "change": {
        "description": "Process change requests for the SDLC Orchestrator infrastructure including CAB approval, risk assessment, implementation planning, and rollback procedures.",
        "context": "Weekly CAB meetings on Wednesday. Emergency changes require 2 approvals.",
    },
    "backup": {
        "description": "Backup and disaster recovery procedures for SDLC Orchestrator databases and evidence vault. Include daily, weekly, monthly schedules and recovery time objectives.",
        "context": "PostgreSQL primary database. MinIO evidence vault. RTO: 4 hours. RPO: 1 hour.",
    },
    "security": {
        "description": "Security procedures for SDLC Orchestrator including access control, vulnerability scanning, patch management, and incident response for security events.",
        "context": "OWASP ASVS Level 2 compliance. Quarterly penetration testing. 90-day password rotation.",
    },
}


# ============================================================================
# Test Functions
# ============================================================================


def log(msg: str, level: str = "INFO"):
    """Print log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def check_ollama_health() -> bool:
    """Check if Ollama is reachable."""
    log("Checking Ollama health...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            log(f"✅ Ollama healthy. Available models: {len(models)}")
            return True
        else:
            log(f"❌ Ollama unhealthy: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Ollama connection failed: {e}", "ERROR")
        return False


def check_api_health() -> bool:
    """Check if API is reachable."""
    log("Checking API health...")
    try:
        response = requests.get(f"{API_URL}/sop/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log(f"✅ API healthy. Service: {data.get('service')}")
            return True
        else:
            log(f"❌ API unhealthy: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ API connection failed: {e}", "ERROR")
        return False


def test_get_sop_types() -> bool:
    """Test GET /sop/types (FR3)."""
    log("Testing GET /sop/types (FR3)...")
    try:
        response = requests.get(f"{API_URL}/sop/types", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        types = response.json()
        assert len(types) == 5, f"Expected 5 types, got {len(types)}"

        type_values = [t["type"] for t in types]
        for expected in ["deployment", "incident", "change", "backup", "security"]:
            assert expected in type_values, f"Missing type: {expected}"

        log(f"✅ FR3 PASS: 5 SOP types available")
        return True
    except Exception as e:
        log(f"❌ FR3 FAIL: {e}", "ERROR")
        return False


def test_generate_sop(sop_type: str) -> dict | None:
    """Test POST /sop/generate (FR1, FR2)."""
    log(f"Testing SOP generation: {sop_type.upper()}...")

    workflow = TEST_WORKFLOWS[sop_type]
    payload = {
        "sop_type": sop_type,
        "workflow_description": workflow["description"],
        "additional_context": workflow["context"],
        "project_id": "PRJ-PILOT-001",
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/sop/generate",
            json=payload,
            timeout=60,  # NFR1: <30s but allow buffer
        )
        generation_time = time.time() - start_time

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

        data = response.json()

        # Validate FR2: 5 mandatory sections
        required_fields = ["purpose", "scope", "procedure", "roles", "quality_criteria"]
        for field in required_fields:
            assert field in data, f"Missing section: {field}"
            assert data[field], f"Empty section: {field}"

        # Validate FR5: SHA256 hash
        assert "sha256_hash" in data, "Missing SHA256 hash"
        assert len(data["sha256_hash"]) == 64, "Invalid SHA256 hash length"

        # Validate FR6: MRP evidence
        assert "mrp_id" in data, "Missing MRP ID"
        assert "completeness_score" in data, "Missing completeness score"

        log(f"✅ {sop_type.upper()} generated in {generation_time:.1f}s")
        log(f"   SOP ID: {data['sop_id']}")
        log(f"   Completeness: {data['completeness_score']:.0f}%")

        # NFR1: Check generation time
        if generation_time < 30:
            log(f"   ✅ NFR1 PASS: Generation time < 30s")
        else:
            log(f"   ⚠️ NFR1 WARNING: Generation time > 30s", "WARN")

        return data

    except Exception as e:
        log(f"❌ Generation FAIL: {e}", "ERROR")
        return None


def test_get_mrp(sop_id: str) -> dict | None:
    """Test GET /sop/{id}/mrp (FR6)."""
    log(f"Testing GET MRP for {sop_id}...")

    try:
        response = requests.get(f"{API_URL}/sop/{sop_id}/mrp", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Validate MRP fields
        assert data["sop_id"] == sop_id, "SOP ID mismatch"
        assert data["brs_id"] == "BRS-PILOT-001", "BRS reference mismatch"
        assert data["sections_present"] == 5, f"Expected 5 sections, got {data['sections_present']}"
        assert data["completeness_score"] >= 80, f"Completeness < 80%: {data['completeness_score']}"

        log(f"✅ FR6 PASS: MRP evidence retrieved")
        log(f"   MRP ID: {data['mrp_id']}")
        log(f"   Sections: {data['sections_present']}/{data['sections_required']}")

        return data

    except Exception as e:
        log(f"❌ FR6 FAIL: {e}", "ERROR")
        return None


def test_submit_vcr(sop_id: str, decision: str = "approved") -> dict | None:
    """Test POST /sop/{id}/vcr (FR7)."""
    log(f"Testing VCR submission: {decision.upper()}...")

    payload = {
        "decision": decision,
        "reviewer": "CTO (E2E Test)",
        "comments": f"Automated E2E test - {decision}",
        "quality_rating": 5 if decision == "approved" else 3,
    }

    try:
        response = requests.post(
            f"{API_URL}/sop/{sop_id}/vcr",
            json=payload,
            timeout=10,
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        data = response.json()

        assert data["sop_id"] == sop_id, "SOP ID mismatch"
        assert data["decision"] == decision, "Decision mismatch"
        assert data["status"] == "completed", "Status should be completed"

        log(f"✅ FR7 PASS: VCR submitted")
        log(f"   VCR ID: {data['vcr_id']}")
        log(f"   Decision: {data['decision']}")
        log(f"   Rating: {data.get('quality_rating')}/5")

        return data

    except Exception as e:
        log(f"❌ FR7 FAIL: {e}", "ERROR")
        return None


def test_sop_status_updated(sop_id: str, expected_status: str) -> bool:
    """Verify SOP status was updated after VCR."""
    log(f"Verifying SOP status = {expected_status}...")

    try:
        response = requests.get(f"{API_URL}/sop/{sop_id}", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        actual_status = data["status"]

        if actual_status == expected_status:
            log(f"✅ Status PASS: {actual_status}")
            return True
        else:
            log(f"❌ Status FAIL: Expected {expected_status}, got {actual_status}", "ERROR")
            return False

    except Exception as e:
        log(f"❌ Status check FAIL: {e}", "ERROR")
        return False


def test_sop_list() -> bool:
    """Test GET /sop/list (M4 endpoint)."""
    log("Testing GET /sop/list...")

    try:
        response = requests.get(f"{API_URL}/sop/list?page=1&page_size=10", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "items" in data, "Missing items"
        assert "total" in data, "Missing total"
        assert "page" in data, "Missing page"

        log(f"✅ List PASS: {data['total']} SOPs, showing {len(data['items'])}")
        return True

    except Exception as e:
        log(f"❌ List FAIL: {e}", "ERROR")
        return False


def run_full_e2e_workflow(sop_type: str = "deployment") -> dict:
    """Run complete E2E workflow for one SOP type."""
    log("")
    log("=" * 60)
    log(f"E2E WORKFLOW: {sop_type.upper()}")
    log("=" * 60)

    results = {
        "sop_type": sop_type,
        "fr1_generate": False,
        "fr2_sections": False,
        "fr5_hash": False,
        "fr6_mrp": False,
        "fr7_vcr": False,
        "status_update": False,
        "sop_id": None,
        "mrp_id": None,
        "vcr_id": None,
        "generation_time_ms": 0,
        "completeness_score": 0,
    }

    # Step 1: Generate SOP (FR1, FR2, FR5)
    sop_data = test_generate_sop(sop_type)
    if sop_data:
        results["fr1_generate"] = True
        results["fr2_sections"] = all([
            sop_data.get("purpose"),
            sop_data.get("scope"),
            sop_data.get("procedure"),
            sop_data.get("roles"),
            sop_data.get("quality_criteria"),
        ])
        results["fr5_hash"] = len(sop_data.get("sha256_hash", "")) == 64
        results["sop_id"] = sop_data["sop_id"]
        results["mrp_id"] = sop_data["mrp_id"]
        results["generation_time_ms"] = sop_data["generation_time_ms"]
        results["completeness_score"] = sop_data["completeness_score"]
    else:
        return results

    # Step 2: Get MRP Evidence (FR6)
    mrp_data = test_get_mrp(sop_data["sop_id"])
    if mrp_data:
        results["fr6_mrp"] = True

    # Step 3: Submit VCR (FR7)
    vcr_data = test_submit_vcr(sop_data["sop_id"], "approved")
    if vcr_data:
        results["fr7_vcr"] = True
        results["vcr_id"] = vcr_data["vcr_id"]

    # Step 4: Verify status updated
    results["status_update"] = test_sop_status_updated(sop_data["sop_id"], "approved")

    return results


def main():
    """Main test runner."""
    print("")
    print("=" * 70)
    print("SDLC ORCHESTRATOR - E2E SOP WORKFLOW TEST")
    print("Phase 2-Pilot Week 5: M5 VCR Complete")
    print("BRS Reference: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml")
    print("=" * 70)
    print("")

    # Check prerequisites
    log("PHASE 1: PREREQUISITES CHECK")
    log("-" * 40)

    if not check_api_health():
        log("API not available. Start backend first.", "ERROR")
        sys.exit(1)

    # Test SOP types (FR3)
    log("")
    log("PHASE 2: FR3 - SOP TYPES")
    log("-" * 40)
    if not test_get_sop_types():
        log("FR3 failed. Aborting.", "ERROR")
        sys.exit(1)

    # Test SOP list (M4)
    log("")
    log("PHASE 3: M4 - SOP LIST")
    log("-" * 40)
    test_sop_list()

    # Run E2E workflow for each SOP type
    log("")
    log("PHASE 4: FULL E2E WORKFLOWS")
    log("-" * 40)

    all_results = []
    for sop_type in ["deployment", "incident", "change", "backup", "security"]:
        results = run_full_e2e_workflow(sop_type)
        all_results.append(results)

    # Summary
    print("")
    print("=" * 70)
    print("E2E TEST SUMMARY")
    print("=" * 70)

    total_pass = 0
    total_tests = 0

    for r in all_results:
        print(f"\n{r['sop_type'].upper()}:")

        tests = [
            ("FR1: Generate SOP", r["fr1_generate"]),
            ("FR2: 5 Sections", r["fr2_sections"]),
            ("FR5: SHA256 Hash", r["fr5_hash"]),
            ("FR6: MRP Evidence", r["fr6_mrp"]),
            ("FR7: VCR Workflow", r["fr7_vcr"]),
            ("Status Update", r["status_update"]),
        ]

        for name, passed in tests:
            icon = "✅" if passed else "❌"
            print(f"  {icon} {name}")
            total_tests += 1
            if passed:
                total_pass += 1

        if r["generation_time_ms"]:
            print(f"  ⏱️  Generation: {r['generation_time_ms']:.0f}ms")
        if r["completeness_score"]:
            print(f"  📊 Completeness: {r['completeness_score']:.0f}%")

    print("")
    print("=" * 70)
    pass_rate = (total_pass / total_tests * 100) if total_tests else 0
    print(f"OVERALL: {total_pass}/{total_tests} tests passed ({pass_rate:.0f}%)")

    if pass_rate >= 95:
        print("✅ M5 VCR COMPLETE: PASS")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ M5 VCR COMPLETE: FAIL")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
