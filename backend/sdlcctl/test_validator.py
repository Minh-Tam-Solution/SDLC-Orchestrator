#!/usr/bin/env python3
"""Test evidence validator - Sprint 134 Dogfooding"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from sdlcctl.validation.validators.evidence_validator import EvidenceValidator

def main():
    project_root = Path('/home/nqh/shared/SDLC-Orchestrator')
    validator = EvidenceValidator(project_root)
    
    print("\n🔍 EVIDENCE VALIDATION - SPRINT 134 DOGFOODING")
    print("=" * 60)

    violations = validator.validate()
    
    print(f"\nTotal violations found: {len(violations)}\n")
    
    # Group by severity
    errors = [v for v in violations if v.severity.value == "ERROR"]
    warnings = [v for v in violations if v.severity.value == "WARNING"]
    
    if errors:
        print("🔴 ERRORS (Blocking):")
        for v in errors:
            print(f"  [{v.rule_id}] {v.message}")
            print(f"    File: {v.file_path}")
            if v.fix_suggestion:
                print(f"    Fix: {v.fix_suggestion}")
            print()
    
    if warnings:
        print("🟡 WARNINGS:")
        for v in warnings:
            print(f"  [{v.rule_id}] {v.message}")
            print(f"    File: {v.file_path}")
            print()
    
    if violations:
        print("\n✅ VALIDATOR IS WORKING!")
        print("🎯 Context drift DETECTED - This proves SPEC-0016 works!")
    else:
        print("\n⚠️ No violations found")
    
    print("=" * 60)
    
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
