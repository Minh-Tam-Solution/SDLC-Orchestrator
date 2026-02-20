#!/usr/bin/env python3
"""
=========================================================================
Standalone Ollama SOP Generator Test - Phase 2-Pilot Week 2
SDLC Orchestrator - M2: Agent Ready Validation

This script tests SOP generation with Ollama without requiring
the full application stack (no FastAPI, no database, no Docker).

Usage:
    python3 scripts/test_ollama_standalone.py

Requirements:
    - Ollama running on localhost:11434
    - requests library (pip install requests)

Output:
    - Test results for all 5 SOP types
    - Performance metrics (generation time)
    - Sample SOP files saved to output directory
=========================================================================
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ============================================================================
# SOP Types (FR3: 5 types)
# ============================================================================


class SOPType(str, Enum):
    """5 SOP types supported by the generator (FR3)."""
    DEPLOYMENT = "deployment"
    INCIDENT = "incident"
    CHANGE = "change"
    BACKUP = "backup"
    SECURITY = "security"


# ============================================================================
# SOP Templates
# ============================================================================


SOP_TEMPLATES = {
    SOPType.DEPLOYMENT: {
        "name": "Deployment SOP",
        "prompt_context": """
You are generating a Deployment SOP for application releases.
Focus on:
- Pre-deployment requirements and checks
- Step-by-step deployment procedure
- Post-deployment verification
- Rollback procedure if issues occur
- Approval requirements
""",
    },
    SOPType.INCIDENT: {
        "name": "Incident Response SOP",
        "prompt_context": """
You are generating an Incident Response SOP.
Focus on:
- Incident classification (P0/P1/P2/P3)
- Initial triage and response steps
- Escalation procedures and contacts
- Communication protocols
- Post-incident review process
""",
    },
    SOPType.CHANGE: {
        "name": "Change Management SOP",
        "prompt_context": """
You are generating a Change Management SOP.
Focus on:
- Change request initiation process
- Impact and risk assessment
- Approval workflow (CAB if needed)
- Implementation and testing
- Documentation requirements
""",
    },
    SOPType.BACKUP: {
        "name": "Backup and Recovery SOP",
        "prompt_context": """
You are generating a Backup and Recovery SOP.
Focus on:
- Backup schedules (daily, weekly, monthly)
- Data retention policies
- Backup verification procedures
- Recovery steps for different scenarios
- Regular testing requirements
""",
    },
    SOPType.SECURITY: {
        "name": "Security SOP",
        "prompt_context": """
You are generating a Security SOP.
Focus on:
- Access control and authentication
- Security incident reporting
- Vulnerability scanning and patching
- Compliance requirements (ISO 27001, SOC 2)
- Security awareness training
""",
    },
}


# ============================================================================
# Test Workflows
# ============================================================================


TEST_WORKFLOWS = {
    SOPType.DEPLOYMENT: {
        "description": "Deploy SDLC Orchestrator to Kubernetes with zero-downtime using rolling updates. Include health checks and automatic rollback on failure.",
        "context": "Production deployment for governance platform.",
    },
    SOPType.INCIDENT: {
        "description": "Handle P0-P3 incidents for SDLC Orchestrator platform. Include escalation paths and communication protocols.",
        "context": "On-call response procedures.",
    },
    SOPType.CHANGE: {
        "description": "Manage change requests for platform updates. Include CAB approval workflow and rollback procedures.",
        "context": "ISO 27001 compliant change management.",
    },
    SOPType.BACKUP: {
        "description": "Backup PostgreSQL database and MinIO storage. RTO 4 hours, RPO 1 hour. Include quarterly drill schedule.",
        "context": "SOC 2 compliance requirements.",
    },
    SOPType.SECURITY: {
        "description": "Security operations for SDLC Orchestrator. OWASP ASVS Level 2 compliance. Include vulnerability management.",
        "context": "Security baseline enforcement.",
    },
}


# ============================================================================
# Ollama Client
# ============================================================================


def call_ollama(
    prompt: str,
    model: str = "qwen3:32b",
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> tuple[str, dict]:
    """
    Call Ollama API for text generation.

    Returns:
        Tuple of (generated_text, metrics)
    """
    import requests

    url = f"{base_url}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 2000,
        },
    }

    start_time = time.time()

    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()

    result = response.json()
    generation_time = (time.time() - start_time) * 1000

    metrics = {
        "generation_time_ms": generation_time,
        "model": result.get("model", model),
        "prompt_tokens": result.get("prompt_eval_count", 0),
        "completion_tokens": result.get("eval_count", 0),
    }

    return result.get("response", ""), metrics


def build_prompt(sop_type: SOPType, workflow: str, context: str) -> str:
    """Build SOP generation prompt."""
    template = SOP_TEMPLATES[sop_type]

    return f"""
{template["prompt_context"]}

Generate a complete Standard Operating Procedure (SOP) in Markdown format.

WORKFLOW DESCRIPTION:
{workflow}

ADDITIONAL CONTEXT:
{context}

REQUIRED SOP STRUCTURE (ISO 9001 compliant):

# SOP: [Title based on workflow]

## Document Control
- **Document ID:** SOP-{sop_type.value.upper()}-[NUMBER]
- **Version:** 1.0.0
- **Effective Date:** [Today's Date]
- **Owner:** [Appropriate Role]
- **Approver:** [Appropriate Role]

## 1. Purpose
[2-3 sentences explaining what this SOP covers and why it's important]

## 2. Scope
- [What systems/processes are covered]
- [What is explicitly excluded]

## 3. Procedure
[Numbered step-by-step instructions with clear, actionable language]

## 4. Roles and Responsibilities
| Role | Responsibility | RACI |
|------|----------------|------|
| [Role] | [Description] | R/A/C/I |

## 5. Quality Criteria
- [ ] [Checklist item 1]
- [ ] [Checklist item 2]
- [ ] [How to verify procedure was followed correctly]

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | [Date] | AI Agent | Initial version |

Generate a complete, professional SOP following this exact structure.
Ensure all sections are filled with relevant, specific content.
Do not use placeholder text like "[TBD]" or "[TODO]".
"""


def parse_sections(markdown: str) -> dict[str, str]:
    """Parse SOP markdown to extract sections."""
    sections = {
        "purpose": "",
        "scope": "",
        "procedure": "",
        "roles": "",
        "quality_criteria": "",
    }

    current_section = None
    current_content = []

    for line in markdown.split("\n"):
        line_lower = line.lower()

        if "## 1. purpose" in line_lower or "## purpose" in line_lower:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "purpose"
            current_content = []
        elif "## 2. scope" in line_lower or "## scope" in line_lower:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "scope"
            current_content = []
        elif "## 3. procedure" in line_lower or "## procedure" in line_lower:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "procedure"
            current_content = []
        elif "## 4. roles" in line_lower or "## roles" in line_lower:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "roles"
            current_content = []
        elif "## 5. quality" in line_lower or "## quality" in line_lower:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "quality_criteria"
            current_content = []
        elif line.startswith("## ") and current_section:
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = None
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def calculate_completeness(sections: dict[str, str]) -> tuple[int, float]:
    """Calculate section completeness."""
    required = ["purpose", "scope", "procedure", "roles", "quality_criteria"]
    present = sum(1 for s in required if sections.get(s, "").strip())
    score = (present / len(required)) * 100
    return present, score


# ============================================================================
# Test Results
# ============================================================================


@dataclass
class TestResult:
    sop_type: SOPType
    success: bool
    generation_time_ms: float
    nfr1_pass: bool  # <30s requirement
    completeness_score: float
    sections_present: int
    sha256_hash: str
    error: Optional[str] = None
    markdown: str = ""


# ============================================================================
# Main Test
# ============================================================================


def test_sop_type(
    sop_type: SOPType,
    model: str = "qwen3:32b",
    base_url: str = "http://localhost:11434",
) -> TestResult:
    """Test SOP generation for a specific type."""
    workflow = TEST_WORKFLOWS[sop_type]

    print(f"\n{'='*60}")
    print(f"Testing: {sop_type.value.upper()} SOP")
    print(f"{'='*60}")

    prompt = build_prompt(
        sop_type,
        workflow["description"],
        workflow["context"],
    )

    try:
        markdown, metrics = call_ollama(prompt, model, base_url)

        sections = parse_sections(markdown)
        sections_present, completeness = calculate_completeness(sections)
        sha256 = hashlib.sha256(markdown.encode()).hexdigest()

        gen_time = metrics["generation_time_ms"]
        nfr1_pass = gen_time < 30000  # NFR1: <30s

        result = TestResult(
            sop_type=sop_type,
            success=True,
            generation_time_ms=gen_time,
            nfr1_pass=nfr1_pass,
            completeness_score=completeness,
            sections_present=sections_present,
            sha256_hash=sha256,
            markdown=markdown,
        )

        print(f"Status: SUCCESS")
        print(f"Generation Time: {gen_time:.0f}ms ({gen_time/1000:.1f}s)")
        print(f"NFR1 (<30s): {'PASS' if nfr1_pass else 'FAIL'}")
        print(f"Completeness: {completeness:.1f}% ({sections_present}/5 sections)")
        print(f"SHA256: {sha256[:32]}...")
        print(f"Content Length: {len(markdown)} chars")

    except Exception as e:
        result = TestResult(
            sop_type=sop_type,
            success=False,
            generation_time_ms=0,
            nfr1_pass=False,
            completeness_score=0,
            sections_present=0,
            sha256_hash="",
            error=str(e),
        )
        print(f"Status: FAILED")
        print(f"Error: {e}")

    return result


def run_all_tests(
    model: str = "qwen3:32b",
    base_url: str = "http://localhost:11434",
    output_dir: str = None,
) -> list[TestResult]:
    """Run tests for all 5 SOP types."""

    print("\n" + "="*70)
    print("SOP GENERATOR OLLAMA INTEGRATION TEST")
    print("Phase 2-Pilot Week 2 - M2: Agent Ready")
    print("="*70)
    print(f"\nOllama URL: {base_url}")
    print(f"Model: {model}")
    print(f"Testing {len(SOPType)} SOP types...")

    results = []

    for sop_type in SOPType:
        result = test_sop_type(sop_type, model, base_url)
        results.append(result)

    # Summary
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    gen_times = [r.generation_time_ms for r in results if r.success]
    avg_time = sum(gen_times) / len(gen_times) if gen_times else 0

    completeness_scores = [r.completeness_score for r in results if r.success]
    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0

    nfr1_passing = sum(1 for r in results if r.nfr1_pass)
    nfr1_compliance = (nfr1_passing / len(results)) * 100

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"\nAverage Generation Time: {avg_time:.0f}ms ({avg_time/1000:.1f}s)")
    print(f"NFR1 Compliance (<30s): {nfr1_compliance:.0f}%")
    print(f"Average Completeness: {avg_completeness:.1f}%")

    print("\n" + "-"*70)
    print("RESULTS BY TYPE")
    print("-"*70)
    for r in results:
        status = "PASS" if r.success else "FAIL"
        nfr1 = "PASS" if r.nfr1_pass else "FAIL"
        time_s = r.generation_time_ms / 1000
        print(f"{r.sop_type.value:12} | {status:4} | {time_s:6.1f}s | NFR1: {nfr1} | {r.completeness_score:5.1f}%")

    # M2 Assessment
    print("\n" + "="*70)
    print("M2 MILESTONE ASSESSMENT")
    print("="*70)

    m2_pass = (
        passed == len(results) and
        nfr1_compliance >= 60 and  # 60% for initial test (Ollama can be slow)
        avg_completeness >= 60
    )

    if m2_pass:
        print("\nM2 STATUS: PASS - Agent Ready")
    else:
        print("\nM2 STATUS: NEEDS ATTENTION")
        if failed > 0:
            print(f"- {failed} test(s) failed")
        if nfr1_compliance < 60:
            print(f"- NFR1 compliance: {nfr1_compliance:.0f}% (needs optimization)")
        if avg_completeness < 60:
            print(f"- Completeness: {avg_completeness:.1f}% (needs improvement)")

    # Save sample SOPs
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for r in results:
            if r.success:
                filepath = output_path / f"SOP-{r.sop_type.value.upper()}-SAMPLE.md"
                with open(filepath, "w") as f:
                    f.write(r.markdown)
                print(f"Saved: {filepath}")

        # Save report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "total_tests": len(results),
            "passed": passed,
            "failed": failed,
            "avg_generation_time_ms": avg_time,
            "nfr1_compliance": nfr1_compliance,
            "avg_completeness": avg_completeness,
            "results": [
                {
                    "sop_type": r.sop_type.value,
                    "success": r.success,
                    "generation_time_ms": r.generation_time_ms,
                    "nfr1_pass": r.nfr1_pass,
                    "completeness_score": r.completeness_score,
                    "sha256_hash": r.sha256_hash,
                    "error": r.error,
                }
                for r in results
            ],
        }

        report_path = output_path / f"M2-TEST-REPORT-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved: {report_path}")

    return results


if __name__ == "__main__":
    # Check if requests is available
    try:
        import requests
    except ImportError:
        print("ERROR: 'requests' library not found.")
        print("Install with: pip install requests")
        sys.exit(1)

    # Check Ollama connectivity
    base_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")

    try:
        import requests
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        if r.status_code != 200:
            print(f"ERROR: Ollama not responding at {base_url}")
            sys.exit(1)

        models = [m["name"] for m in r.json().get("models", [])]
        print(f"Ollama connected. Available models: {models}")

        if model not in models:
            print(f"WARNING: Model '{model}' not found. Available: {models}")
            if models:
                model = models[0]
                print(f"Using: {model}")
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at {base_url}: {e}")
        sys.exit(1)

    # Run tests
    output_dir = Path(__file__).parent.parent / "test_output" / "M2-SOP-Tests"
    results = run_all_tests(model=model, base_url=base_url, output_dir=str(output_dir))

    # Exit with proper code
    sys.exit(0 if all(r.success for r in results) else 1)
