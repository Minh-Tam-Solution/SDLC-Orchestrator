#!/usr/bin/env python3
"""
YAML Frontmatter Validator for SDLC 6.0.5 Section 8 Compliance

This script validates that markdown files have proper YAML frontmatter
with all required fields according to SDLC 6.0.5 Section 8 Specification Standard.

Usage:
    python frontmatter_checker.py <file1.md> <file2.md> ...
    pre-commit run yaml-frontmatter-check

Exit Codes:
    0 - All files valid
    1 - Validation errors found
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# SDLC 6.0.5 Section 8 Required Fields
REQUIRED_FIELDS = {
    "sprint_plan": [
        "sprint_id", "title", "status", "tier", "owner",
        "start_date", "end_date", "framework_version", "context_zone"
    ],
    "adr": [
        "adr_id", "title", "version", "status", "date",
        "author", "stage", "tier", "context_zone"
    ],
    "spec": [
        "spec_id", "title", "version", "status", "stage",
        "tier", "author", "created", "updated"
    ],
    "cto_report": [
        "report_id", "title", "report_type", "severity", "date",
        "author", "status", "stage", "tier"
    ],
    "stage_readme": [
        "stage_id", "title", "stage_name", "framework_version",
        "status", "owner", "last_updated", "context_zone", "update_frequency"
    ]
}

# Valid enum values
VALID_STATUSES = {
    "sprint_plan": ["PLANNING", "IN_PROGRESS", "COMPLETE", "CANCELLED"],
    "adr": ["DRAFT", "REVIEW", "APPROVED", "SUPERSEDED", "DEPRECATED"],
    "spec": ["DRAFT", "REVIEW", "CTO_APPROVED", "ACTIVE", "DEPRECATED"],
    "cto_report": ["DRAFT", "REVIEW", "APPROVED", "ACTIONED"],
    "stage_readme": ["ACTIVE", "PLANNED", "DEPRECATED"]
}

VALID_TIERS = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"]
VALID_CONTEXT_ZONES = ["Static", "Semi-Static", "Dynamic", "Ephemeral"]


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def detect_document_type(file_path: Path) -> Optional[str]:
    """
    Detect document type based on file path and name.

    Returns:
        Document type key or None if not a validated document type
    """
    path_str = str(file_path).lower()
    name_str = file_path.name.lower()

    # Sprint plans
    if 'sprint-plan' in path_str or name_str.startswith('sprint-'):
        return "sprint_plan"

    # ADRs
    if 'adr-' in name_str and path_str.count('adrs'):
        return "adr"

    # Technical specs
    if 'spec-' in name_str and 'technical-specs' in path_str:
        return "spec"

    # CTO reports
    if 'cto-report-' in name_str:
        return "cto_report"

    # Stage READMEs
    if name_str == 'readme.md' and re.search(r'docs/\d{2}-[a-z-]+/', path_str):
        return "stage_readme"

    return None


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, str]], int, int]:
    """
    Extract YAML frontmatter from markdown content.

    Returns:
        (frontmatter_dict, start_line, end_line) or (None, 0, 0) if not found
    """
    # Match YAML frontmatter: --- at start, content, --- at end
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return None, 0, 0

    yaml_content = match.group(1)
    start_line = 1
    end_line = content[:match.end()].count('\n')

    # Parse YAML (simple key: value parser)
    frontmatter = {}
    for line in yaml_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if ':' in line and not line.startswith('-'):
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            frontmatter[key] = value

    return frontmatter, start_line, end_line


def validate_date_format(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_version_format(version_str: str) -> bool:
    """Validate semantic version format X.Y.Z"""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version_str))


def validate_frontmatter(
    frontmatter: Dict[str, str],
    doc_type: str,
    file_path: Path
) -> List[str]:
    """
    Validate frontmatter against SDLC 6.0.5 Section 8 requirements.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    required = REQUIRED_FIELDS.get(doc_type, [])

    # Check required fields presence
    for field in required:
        if field not in frontmatter or not frontmatter[field]:
            errors.append(
                f"Missing required field: '{field}'"
            )

    # Validate specific fields
    if 'status' in frontmatter:
        valid_statuses = VALID_STATUSES.get(doc_type, [])
        if frontmatter['status'] not in valid_statuses:
            errors.append(
                f"Invalid status '{frontmatter['status']}'. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )

    if 'tier' in frontmatter:
        if frontmatter['tier'] not in VALID_TIERS:
            errors.append(
                f"Invalid tier '{frontmatter['tier']}'. "
                f"Must be one of: {', '.join(VALID_TIERS)}"
            )

    if 'context_zone' in frontmatter:
        if frontmatter['context_zone'] not in VALID_CONTEXT_ZONES:
            errors.append(
                f"Invalid context_zone '{frontmatter['context_zone']}'. "
                f"Must be one of: {', '.join(VALID_CONTEXT_ZONES)}"
            )

    # Validate date fields
    date_fields = ['date', 'start_date', 'end_date', 'created', 'updated', 'last_updated']
    for field in date_fields:
        if field in frontmatter and frontmatter[field]:
            if not validate_date_format(frontmatter[field]):
                errors.append(
                    f"Invalid date format in '{field}': '{frontmatter[field]}'. "
                    f"Must be YYYY-MM-DD"
                )

    # Validate version fields
    if 'version' in frontmatter and frontmatter['version']:
        if not validate_version_format(frontmatter['version']):
            errors.append(
                f"Invalid version format: '{frontmatter['version']}'. "
                f"Must be semantic version (e.g., 1.0.0)"
            )

    # Validate framework_version
    if 'framework_version' in frontmatter:
        if not frontmatter['framework_version'].startswith('6.0'):
            errors.append(
                f"Framework version should be 6.0.x, got: '{frontmatter['framework_version']}'"
            )

    return errors


def check_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Check a single markdown file for YAML frontmatter compliance.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Read file content
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Failed to read file: {e}"]

    # Detect document type
    doc_type = detect_document_type(file_path)
    if not doc_type:
        # Not a validated document type, skip
        return True, []

    # Extract frontmatter
    frontmatter, start_line, end_line = extract_frontmatter(content)

    if frontmatter is None:
        errors.append(
            f"Missing YAML frontmatter. Expected:\n"
            f"---\n"
            f"<fields>\n"
            f"---\n"
            f"\n"
            f"Use template: .claude/templates/yaml-frontmatter-{doc_type.replace('_', '-')}.md"
        )
        return False, errors

    # Validate frontmatter fields
    validation_errors = validate_frontmatter(frontmatter, doc_type, file_path)
    errors.extend(validation_errors)

    return len(errors) == 0, errors


def main():
    """Main entry point for pre-commit hook"""
    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}Usage: {sys.argv[0]} <file1.md> <file2.md> ...{Colors.RESET}")
        sys.exit(1)

    files = [Path(f) for f in sys.argv[1:]]
    total_files = len(files)
    valid_files = 0
    invalid_files = 0

    print(f"\n{Colors.BOLD}{Colors.CYAN}SDLC 6.0.5 YAML Frontmatter Validator{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")

    for file_path in files:
        is_valid, errors = check_file(file_path)

        if is_valid:
            valid_files += 1
            print(f"{Colors.GREEN}✓{Colors.RESET} {file_path}")
        else:
            invalid_files += 1
            print(f"{Colors.RED}✗{Colors.RESET} {Colors.BOLD}{file_path}{Colors.RESET}")
            for error in errors:
                print(f"  {Colors.RED}→{Colors.RESET} {error}")
            print()

    # Summary
    print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Summary:{Colors.RESET}")
    print(f"  Total files:   {total_files}")
    print(f"  {Colors.GREEN}Valid:{Colors.RESET}         {valid_files}")
    print(f"  {Colors.RED}Invalid:{Colors.RESET}       {invalid_files}")

    if invalid_files > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Validation failed!{Colors.RESET}")
        print(f"{Colors.YELLOW}Fix the errors above and try again.{Colors.RESET}")
        print(f"{Colors.YELLOW}Templates: .claude/templates/{Colors.RESET}\n")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All files valid!{Colors.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
