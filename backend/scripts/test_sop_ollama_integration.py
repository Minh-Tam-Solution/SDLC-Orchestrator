#!/usr/bin/env python3
"""
=========================================================================
SOP Generator Ollama Integration Test - Phase 2-Pilot Week 2
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 30, 2025
Status: ACTIVE - Phase 2-Pilot Week 2 (M2: Agent Ready)
Authority: CTO Approved
Foundation: BRS-PILOT-001, SE 3.0 SASE Integration
Framework: SDLC 5.1.0 Complete Lifecycle

Purpose:
- Test Ollama integration for SOP generation
- Validate all 5 SOP types (FR3)
- Measure generation time (NFR1: <30s)
- Validate MRP evidence generation (FR6)
- Generate M2 test report

Usage:
    python scripts/test_sop_ollama_integration.py

Environment Variables:
    OLLAMA_URL: Ollama API endpoint (default: http://localhost:11434)
    OLLAMA_MODEL: Model to use (default: qwen3:32b)

Output:
    - Console: Test results with metrics
    - File: M2 test report (docs/03-Development-Implementation/06-Test-Reports/)

BRS Reference: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml
=========================================================================
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sop_generator_service import (
    SOPGeneratorService,
    SOPGenerationRequest,
    SOPType,
    GeneratedSOP,
    MRPEvidence,
)


# ============================================================================
# Test Data - Workflow descriptions for each SOP type
# ============================================================================

TEST_WORKFLOWS = {
    SOPType.DEPLOYMENT: {
        "description": """
Deploy the SDLC Orchestrator application to production Kubernetes cluster.

Context:
- Application is containerized with Docker (FastAPI backend + React frontend)
- Deployment target: AWS EKS cluster (3 nodes, m5.large)
- Database: PostgreSQL 15.5 on RDS
- Cache: Redis 7.2 on ElastiCache
- Storage: MinIO S3-compatible (evidence vault)

Requirements:
- Zero-downtime deployment using rolling updates
- Database migrations must run before app deployment
- Health checks must pass before traffic routing
- Automatic rollback if health checks fail within 5 minutes
- Notify Slack channel on deployment start/complete/failure
""",
        "context": "Production deployment for Bflow team. Target: 99.9% uptime SLA.",
    },
    SOPType.INCIDENT: {
        "description": """
Handle production incidents for the SDLC Orchestrator platform.

Context:
- Platform serves 5 internal teams (100+ users)
- Critical dependencies: PostgreSQL, Redis, OPA, MinIO
- On-call rotation: Backend team (24/7)
- Monitoring: Prometheus + Grafana + OnCall

Incident Classification:
- P0: Platform completely unavailable (≤15 min response)
- P1: Major feature unavailable (≤1 hour response)
- P2: Minor feature degraded (≤4 hours response)
- P3: Non-critical issue (next business day)

Requirements:
- Clear escalation path for each severity
- Communication templates for status updates
- Post-incident review process (RCA within 5 days)
- War room protocol for P0/P1 incidents
""",
        "context": "Incident response for governance platform. Compliance requirement for audit.",
    },
    SOPType.CHANGE: {
        "description": """
Manage change requests for the SDLC Orchestrator platform.

Context:
- Platform under active development (Sprint 2-week cycles)
- Changes include: code deployments, config changes, infra updates
- CAB (Change Advisory Board) meets weekly on Fridays
- Emergency changes require CTO approval

Change Types:
- Standard: Pre-approved, low risk (database index, config tweak)
- Normal: Requires CAB approval (new feature, major refactor)
- Emergency: P0/P1 fix, bypass normal process with CTO approval

Requirements:
- Change request form with impact assessment
- Testing evidence required before approval
- Rollback plan mandatory for all changes
- Post-implementation review within 48 hours
""",
        "context": "Change management for governance platform. ISO 27001 compliance required.",
    },
    SOPType.BACKUP: {
        "description": """
Backup and recovery procedures for SDLC Orchestrator data.

Context:
- Primary data: PostgreSQL database (users, projects, gates, evidence metadata)
- Evidence files: MinIO S3 storage (documents, screenshots, audit logs)
- Configuration: Git-versioned (Terraform, Kubernetes manifests)
- Secrets: HashiCorp Vault

Backup Schedule:
- PostgreSQL: Daily full backup (2 AM), hourly WAL archiving
- MinIO: Daily incremental backup (3 AM), weekly full backup (Sunday)
- Vault: Daily backup (1 AM), encrypted at rest

Retention:
- Daily backups: 30 days
- Weekly backups: 12 weeks
- Monthly backups: 12 months

Requirements:
- RTO (Recovery Time Objective): 4 hours
- RPO (Recovery Point Objective): 1 hour
- Quarterly recovery drill (documented)
""",
        "context": "Backup strategy for governance platform. SOC 2 audit compliance.",
    },
    SOPType.SECURITY: {
        "description": """
Security procedures for SDLC Orchestrator platform operations.

Context:
- Platform handles sensitive project data (requirements, evidence, decisions)
- Authentication: JWT + OAuth 2.0 (GitHub, Google, Microsoft)
- Authorization: RBAC with 13 roles, row-level security
- Security baseline: OWASP ASVS Level 2 (264 requirements)

Security Controls:
- Access control: MFA required for admin roles
- Data protection: TLS 1.3 in transit, AES-256 at rest
- Secrets: HashiCorp Vault with 90-day rotation
- Logging: Immutable audit logs for all user actions
- Scanning: Weekly vulnerability scans (Semgrep, Grype)

Requirements:
- Security incident reporting within 24 hours
- Vulnerability patching SLA: Critical=24h, High=7d, Medium=30d
- Access review: Quarterly (remove inactive users)
- Penetration test: Annual (external firm)
""",
        "context": "Security operations for governance platform. HIPAA/SOC2 alignment.",
    },
}


# ============================================================================
# Test Result Data Classes
# ============================================================================


@dataclass
class SOPTestResult:
    """Result of a single SOP generation test."""

    sop_type: SOPType
    success: bool
    generation_time_ms: float
    nfr1_pass: bool  # <30s requirement
    completeness_score: float
    sections_present: int
    sop_id: str = ""
    mrp_id: str = ""
    sha256_hash: str = ""
    error: Optional[str] = None
    sop: Optional[GeneratedSOP] = None
    mrp: Optional[MRPEvidence] = None


@dataclass
class M2TestReport:
    """Complete M2 milestone test report."""

    timestamp: datetime
    ollama_url: str
    ollama_model: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_generation_time_ms: float
    avg_completeness_score: float
    nfr1_compliance: float  # % of tests passing <30s
    results: list[SOPTestResult]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "ollama_url": self.ollama_url,
            "ollama_model": self.ollama_model,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "avg_generation_time_ms": self.avg_generation_time_ms,
            "avg_completeness_score": self.avg_completeness_score,
            "nfr1_compliance": self.nfr1_compliance,
            "results": [
                {
                    "sop_type": r.sop_type.value,
                    "success": r.success,
                    "generation_time_ms": r.generation_time_ms,
                    "nfr1_pass": r.nfr1_pass,
                    "completeness_score": r.completeness_score,
                    "sections_present": r.sections_present,
                    "sop_id": r.sop_id,
                    "mrp_id": r.mrp_id,
                    "sha256_hash": r.sha256_hash,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


# ============================================================================
# Test Runner
# ============================================================================


class SOPOllamaIntegrationTest:
    """Integration test runner for SOP Generator with Ollama."""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen3:32b",
        timeout: int = 60,  # Extended timeout for testing
    ):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.timeout = timeout
        self.service = SOPGeneratorService(
            ollama_base_url=ollama_url,
            ollama_model=ollama_model,
            timeout=timeout,
        )
        self.results: list[SOPTestResult] = []

    async def test_sop_type(self, sop_type: SOPType) -> SOPTestResult:
        """
        Test SOP generation for a specific type.

        Args:
            sop_type: Type of SOP to generate

        Returns:
            Test result with metrics
        """
        workflow = TEST_WORKFLOWS[sop_type]

        print(f"\n{'='*60}")
        print(f"Testing: {sop_type.value.upper()} SOP")
        print(f"{'='*60}")

        request = SOPGenerationRequest(
            sop_type=sop_type,
            workflow_description=workflow["description"],
            additional_context=workflow["context"],
            project_id="SE3-PILOT",
        )

        start_time = time.time()

        try:
            sop, mrp = await self.service.generate_sop(request)
            generation_time = (time.time() - start_time) * 1000

            result = SOPTestResult(
                sop_type=sop_type,
                success=True,
                generation_time_ms=generation_time,
                nfr1_pass=generation_time < 30000,  # NFR1: <30s
                completeness_score=mrp.completeness_score,
                sections_present=mrp.sections_present,
                sop_id=sop.sop_id,
                mrp_id=mrp.mrp_id,
                sha256_hash=sop.sha256_hash,
                sop=sop,
                mrp=mrp,
            )

            # Print results
            print(f"Status: SUCCESS")
            print(f"SOP ID: {sop.sop_id}")
            print(f"MRP ID: {mrp.mrp_id}")
            print(f"Generation Time: {generation_time:.0f}ms")
            print(f"NFR1 (<30s): {'PASS' if result.nfr1_pass else 'FAIL'}")
            print(f"Completeness: {mrp.completeness_score:.1f}% ({mrp.sections_present}/5 sections)")
            print(f"SHA256: {sop.sha256_hash[:16]}...")
            print(f"\nTitle: {sop.title}")
            print(f"\nPurpose (preview):\n{sop.purpose[:200]}...")

        except Exception as e:
            generation_time = (time.time() - start_time) * 1000
            result = SOPTestResult(
                sop_type=sop_type,
                success=False,
                generation_time_ms=generation_time,
                nfr1_pass=False,
                completeness_score=0.0,
                sections_present=0,
                error=str(e),
            )
            print(f"Status: FAILED")
            print(f"Error: {e}")

        return result

    async def run_all_tests(self) -> M2TestReport:
        """
        Run integration tests for all 5 SOP types.

        Returns:
            Complete M2 test report
        """
        print("\n" + "="*70)
        print("SOP GENERATOR OLLAMA INTEGRATION TEST")
        print("Phase 2-Pilot Week 2 - M2: Agent Ready")
        print("="*70)
        print(f"\nOllama URL: {self.ollama_url}")
        print(f"Ollama Model: {self.ollama_model}")
        print(f"Timeout: {self.timeout}s")
        print(f"Testing {len(SOPType)} SOP types...")

        # Test each SOP type
        for sop_type in SOPType:
            result = await self.test_sop_type(sop_type)
            self.results.append(result)

        # Calculate metrics
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed

        gen_times = [r.generation_time_ms for r in self.results if r.success]
        avg_gen_time = sum(gen_times) / len(gen_times) if gen_times else 0

        completeness_scores = [r.completeness_score for r in self.results if r.success]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0

        nfr1_passing = sum(1 for r in self.results if r.nfr1_pass)
        nfr1_compliance = (nfr1_passing / len(self.results)) * 100

        # Create report
        report = M2TestReport(
            timestamp=datetime.utcnow(),
            ollama_url=self.ollama_url,
            ollama_model=self.ollama_model,
            total_tests=len(self.results),
            passed_tests=passed,
            failed_tests=failed,
            avg_generation_time_ms=avg_gen_time,
            avg_completeness_score=avg_completeness,
            nfr1_compliance=nfr1_compliance,
            results=self.results,
        )

        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nTotal Tests: {report.total_tests}")
        print(f"Passed: {report.passed_tests}")
        print(f"Failed: {report.failed_tests}")
        print(f"\nAverage Generation Time: {report.avg_generation_time_ms:.0f}ms")
        print(f"NFR1 Compliance (<30s): {report.nfr1_compliance:.0f}%")
        print(f"Average Completeness: {report.avg_completeness_score:.1f}%")

        print("\n" + "-"*70)
        print("RESULTS BY TYPE")
        print("-"*70)
        for r in self.results:
            status = "PASS" if r.success else "FAIL"
            nfr1 = "PASS" if r.nfr1_pass else "FAIL"
            print(f"{r.sop_type.value:12} | {status:4} | {r.generation_time_ms:8.0f}ms | NFR1: {nfr1} | {r.completeness_score:5.1f}%")

        # M2 assessment
        print("\n" + "="*70)
        print("M2 MILESTONE ASSESSMENT")
        print("="*70)

        m2_pass = (
            report.passed_tests == report.total_tests and
            report.nfr1_compliance >= 80 and  # 80% NFR1 compliance acceptable
            report.avg_completeness_score >= 80  # 80% completeness acceptable
        )

        if m2_pass:
            print("\nM2 STATUS: PASS - Agent Ready")
            print("- All 5 SOP types generated successfully")
            print(f"- NFR1 compliance: {report.nfr1_compliance:.0f}% (target: ≥80%)")
            print(f"- Completeness: {report.avg_completeness_score:.1f}% (target: ≥80%)")
        else:
            print("\nM2 STATUS: NEEDS ATTENTION")
            if report.failed_tests > 0:
                print(f"- {report.failed_tests} test(s) failed")
            if report.nfr1_compliance < 80:
                print(f"- NFR1 compliance below threshold: {report.nfr1_compliance:.0f}%")
            if report.avg_completeness_score < 80:
                print(f"- Completeness below threshold: {report.avg_completeness_score:.1f}%")

        return report

    def save_report(self, report: M2TestReport, output_dir: str = None) -> str:
        """
        Save test report to file.

        Args:
            report: M2 test report
            output_dir: Output directory (default: docs/03-Development-Implementation/06-Test-Reports/)

        Returns:
            Path to saved report
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "docs" / "03-Development-Implementation" / "06-Test-Reports"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"M2-SOP-OLLAMA-INTEGRATION-{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        print(f"\nReport saved: {filepath}")
        return str(filepath)

    def save_sample_sops(self, output_dir: str = None) -> list[str]:
        """
        Save generated SOP samples to files.

        Args:
            output_dir: Output directory

        Returns:
            List of saved file paths
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "docs" / "03-Development-Implementation" / "06-Test-Reports" / "SOP-Samples"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        for result in self.results:
            if result.success and result.sop:
                filename = f"SOP-{result.sop_type.value.upper()}-SAMPLE.md"
                filepath = output_dir / filename

                with open(filepath, "w") as f:
                    f.write(result.sop.markdown_content)

                saved.append(str(filepath))
                print(f"Saved: {filepath}")

        return saved


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """Run integration tests."""
    # Configuration from environment or defaults
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")

    # Create test runner
    test_runner = SOPOllamaIntegrationTest(
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        timeout=120,  # Extended timeout for testing (2 minutes)
    )

    # Run tests
    report = await test_runner.run_all_tests()

    # Save results
    test_runner.save_report(report)
    test_runner.save_sample_sops()

    # Return exit code
    return 0 if report.failed_tests == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
