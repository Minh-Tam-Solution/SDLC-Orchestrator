#!/usr/bin/env python3
"""
SDLC 6.0.0 BDD Format Checker

Validates BDD (Behavior-Driven Development) format compliance in documentation:
- GIVEN-WHEN-THEN structure in requirements
- Scenario format in acceptance criteria
- BDD patterns in specifications (Section 8 compliance)

Usage:
    python bdd_checker.py [file1.md] [file2.md] ...
    python bdd_checker.py --help

Part of Sprint 131 Documentation Compliance initiative.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class BDDSeverity(Enum):
    """Severity levels for BDD validation issues."""
    ERROR = "error"      # Must fix - blocks compliance
    WARNING = "warning"  # Should fix - impacts quality
    INFO = "info"        # Nice to have - improvement suggestion


@dataclass
class BDDIssue:
    """Represents a BDD format validation issue."""
    file: str
    line: int
    severity: BDDSeverity
    rule: str
    message: str
    suggestion: Optional[str] = None


# BDD Keywords and Patterns
BDD_KEYWORDS = {
    "given": r"(?:Given|GIVEN)\s+(.+)",
    "when": r"(?:When|WHEN)\s+(.+)",
    "then": r"(?:Then|THEN)\s+(.+)",
    "and": r"(?:And|AND)\s+(.+)",
    "but": r"(?:But|BUT)\s+(.+)",
}

SCENARIO_PATTERN = r"(?:Scenario|SCENARIO|Feature|FEATURE):\s*(.+)"

# Sections that SHOULD contain BDD format (SDLC 6.0.0 Section 8)
BDD_REQUIRED_SECTIONS = [
    "Acceptance Criteria",
    "Requirements",
    "Functional Requirements",
    "User Stories",
    "Test Cases",
    "Scenarios",
]

# Sections that MAY contain BDD format (recommended but not required)
BDD_RECOMMENDED_SECTIONS = [
    "Goals",
    "Deliverables",
    "Success Criteria",
    "Definition of Done",
]


def detect_document_type(content: str, file_path: Path) -> str:
    """Detect document type from content and filename."""
    filename = file_path.name.upper()

    if "SPEC-" in filename or "spec_id:" in content:
        return "specification"
    elif "SPRINT-" in filename or "sprint_id:" in content:
        return "sprint_plan"
    elif "ADR-" in filename or "adr_id:" in content:
        return "adr"
    elif "README" in filename:
        return "readme"
    elif any(keyword in filename for keyword in ["TEST", "ACCEPTANCE", "CRITERIA"]):
        return "test_document"
    else:
        return "generic"


def find_sections(content: str) -> Dict[str, Tuple[int, int, str]]:
    """
    Find markdown sections in content.

    Returns:
        Dict mapping section name to (start_line, end_line, content)
    """
    sections = {}
    lines = content.split('\n')
    current_section = None
    current_start = 0
    current_content = []

    for i, line in enumerate(lines, 1):
        # Match markdown headers (## or ###)
        header_match = re.match(r'^#{1,4}\s+(.+?)(?:\s*{.*})?$', line.strip())

        if header_match:
            # Save previous section
            if current_section:
                sections[current_section] = (
                    current_start,
                    i - 1,
                    '\n'.join(current_content)
                )

            current_section = header_match.group(1).strip()
            current_start = i
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = (
            current_start,
            len(lines),
            '\n'.join(current_content)
        )

    return sections


def check_bdd_structure(content: str, start_line: int) -> List[BDDIssue]:
    """
    Check if content follows BDD GIVEN-WHEN-THEN structure.

    Returns list of issues found.
    """
    issues = []
    lines = content.split('\n')

    has_given = False
    has_when = False
    has_then = False
    given_line = 0
    when_line = 0

    for i, line in enumerate(lines, start_line):
        stripped = line.strip()

        # Skip empty lines and code blocks
        if not stripped or stripped.startswith('```'):
            continue

        # Check for BDD keywords
        if re.match(BDD_KEYWORDS["given"], stripped, re.IGNORECASE):
            has_given = True
            given_line = i
        elif re.match(BDD_KEYWORDS["when"], stripped, re.IGNORECASE):
            has_when = True
            when_line = i
            # Check if GIVEN came before WHEN
            if not has_given:
                issues.append(BDDIssue(
                    file="",
                    line=i,
                    severity=BDDSeverity.WARNING,
                    rule="BDD-002",
                    message="WHEN appears before GIVEN - consider adding GIVEN clause",
                    suggestion="Add 'Given [precondition]' before this line"
                ))
        elif re.match(BDD_KEYWORDS["then"], stripped, re.IGNORECASE):
            has_then = True
            # Check if WHEN came before THEN
            if not has_when:
                issues.append(BDDIssue(
                    file="",
                    line=i,
                    severity=BDDSeverity.WARNING,
                    rule="BDD-003",
                    message="THEN appears before WHEN - consider adding WHEN clause",
                    suggestion="Add 'When [action]' before this line"
                ))

    return issues, has_given, has_when, has_then


def check_scenario_format(content: str, start_line: int) -> List[BDDIssue]:
    """
    Check if scenarios follow proper format.

    Expected format:
    ```gherkin
    Scenario: [Description]
      Given [precondition]
      When [action]
      Then [expected result]
    ```
    """
    issues = []
    lines = content.split('\n')
    in_scenario = False
    scenario_start = 0
    scenario_content = []

    for i, line in enumerate(lines, start_line):
        stripped = line.strip()

        scenario_match = re.match(SCENARIO_PATTERN, stripped, re.IGNORECASE)

        if scenario_match:
            # Check previous scenario completeness
            if in_scenario and scenario_content:
                scenario_issues = validate_scenario(scenario_content, scenario_start)
                issues.extend(scenario_issues)

            in_scenario = True
            scenario_start = i
            scenario_content = []
        elif in_scenario:
            if stripped and not stripped.startswith('#'):
                scenario_content.append((i, stripped))

    # Check last scenario
    if in_scenario and scenario_content:
        scenario_issues = validate_scenario(scenario_content, scenario_start)
        issues.extend(scenario_issues)

    return issues


def validate_scenario(lines: List[Tuple[int, str]], scenario_start: int) -> List[BDDIssue]:
    """Validate a single scenario for BDD completeness."""
    issues = []
    has_given = False
    has_when = False
    has_then = False

    for line_num, content in lines:
        if re.match(BDD_KEYWORDS["given"], content, re.IGNORECASE):
            has_given = True
        elif re.match(BDD_KEYWORDS["when"], content, re.IGNORECASE):
            has_when = True
        elif re.match(BDD_KEYWORDS["then"], content, re.IGNORECASE):
            has_then = True

    if not has_given:
        issues.append(BDDIssue(
            file="",
            line=scenario_start,
            severity=BDDSeverity.ERROR,
            rule="BDD-101",
            message="Scenario missing GIVEN clause (precondition)",
            suggestion="Add 'Given [initial context/state]' to this scenario"
        ))

    if not has_when:
        issues.append(BDDIssue(
            file="",
            line=scenario_start,
            severity=BDDSeverity.ERROR,
            rule="BDD-102",
            message="Scenario missing WHEN clause (action/trigger)",
            suggestion="Add 'When [user action or event]' to this scenario"
        ))

    if not has_then:
        issues.append(BDDIssue(
            file="",
            line=scenario_start,
            severity=BDDSeverity.ERROR,
            rule="BDD-103",
            message="Scenario missing THEN clause (expected outcome)",
            suggestion="Add 'Then [expected result/assertion]' to this scenario"
        ))

    return issues


def check_section_bdd_compliance(
    section_name: str,
    section_content: str,
    start_line: int,
    doc_type: str
) -> List[BDDIssue]:
    """Check if a section that should have BDD format actually has it."""
    issues = []

    # Check if this is a section that requires BDD format
    requires_bdd = any(
        req.lower() in section_name.lower()
        for req in BDD_REQUIRED_SECTIONS
    )
    recommends_bdd = any(
        rec.lower() in section_name.lower()
        for rec in BDD_RECOMMENDED_SECTIONS
    )

    if not requires_bdd and not recommends_bdd:
        return []

    # Check for BDD patterns in the section
    has_any_bdd = any(
        re.search(pattern, section_content, re.IGNORECASE | re.MULTILINE)
        for pattern in BDD_KEYWORDS.values()
    )

    has_scenario = re.search(SCENARIO_PATTERN, section_content, re.IGNORECASE)

    if requires_bdd:
        if not has_any_bdd and not has_scenario:
            issues.append(BDDIssue(
                file="",
                line=start_line,
                severity=BDDSeverity.ERROR,
                rule="BDD-201",
                message=f"Section '{section_name}' requires BDD format (GIVEN-WHEN-THEN) per SDLC 6.0.0 Section 8",
                suggestion="Convert requirements to: 'Given [context], When [action], Then [outcome]'"
            ))
        elif has_any_bdd:
            # Check structure completeness
            bdd_issues, has_g, has_w, has_t = check_bdd_structure(section_content, start_line)
            issues.extend(bdd_issues)

            if has_g and has_w and not has_t:
                issues.append(BDDIssue(
                    file="",
                    line=start_line,
                    severity=BDDSeverity.ERROR,
                    rule="BDD-202",
                    message="BDD structure incomplete - missing THEN clause",
                    suggestion="Add 'Then [expected outcome]' to complete the requirement"
                ))

        # Check scenario format if present
        if has_scenario:
            scenario_issues = check_scenario_format(section_content, start_line)
            issues.extend(scenario_issues)

    elif recommends_bdd:
        if not has_any_bdd and not has_scenario:
            issues.append(BDDIssue(
                file="",
                line=start_line,
                severity=BDDSeverity.INFO,
                rule="BDD-301",
                message=f"Section '{section_name}' could benefit from BDD format",
                suggestion="Consider using GIVEN-WHEN-THEN for clearer acceptance criteria"
            ))

    return issues


def validate_file(file_path: Path) -> Tuple[List[BDDIssue], bool]:
    """
    Validate a single file for BDD format compliance.

    Returns:
        Tuple of (issues list, is_valid)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return [BDDIssue(
            file=str(file_path),
            line=0,
            severity=BDDSeverity.ERROR,
            rule="BDD-000",
            message=f"Could not read file: {e}",
            suggestion=None
        )], False

    doc_type = detect_document_type(content, file_path)
    issues = []

    # Find all sections
    sections = find_sections(content)

    # Check each relevant section for BDD compliance
    for section_name, (start_line, end_line, section_content) in sections.items():
        section_issues = check_section_bdd_compliance(
            section_name,
            section_content,
            start_line,
            doc_type
        )

        # Add file path to all issues
        for issue in section_issues:
            issue.file = str(file_path)

        issues.extend(section_issues)

    # Count errors (warnings and info don't block validation)
    error_count = sum(1 for i in issues if i.severity == BDDSeverity.ERROR)

    return issues, error_count == 0


def print_colored(text: str, color_code: str) -> None:
    """Print colored text to terminal."""
    if sys.stdout.isatty():
        print(f"\033[{color_code}m{text}\033[0m")
    else:
        print(text)


def format_issue(issue: BDDIssue) -> str:
    """Format an issue for display."""
    severity_colors = {
        BDDSeverity.ERROR: "91",    # Red
        BDDSeverity.WARNING: "93",  # Yellow
        BDDSeverity.INFO: "96",     # Cyan
    }

    severity_icons = {
        BDDSeverity.ERROR: "✗",
        BDDSeverity.WARNING: "⚠",
        BDDSeverity.INFO: "ℹ",
    }

    color = severity_colors[issue.severity]
    icon = severity_icons[issue.severity]

    lines = [f"  {icon} [{issue.rule}] Line {issue.line}: {issue.message}"]
    if issue.suggestion:
        lines.append(f"    → Suggestion: {issue.suggestion}")

    return '\n'.join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SDLC 6.0.0 BDD Format Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bdd_checker.py docs/02-design/14-Technical-Specs/SPEC-0013.md
  python bdd_checker.py docs/**/*.md
  python bdd_checker.py --strict docs/

BDD Rules:
  BDD-000: File read error
  BDD-002: WHEN before GIVEN
  BDD-003: THEN before WHEN
  BDD-101: Scenario missing GIVEN
  BDD-102: Scenario missing WHEN
  BDD-103: Scenario missing THEN
  BDD-201: Required section missing BDD format
  BDD-202: Incomplete BDD structure
  BDD-301: Recommended section could use BDD format

For more information, see: docs/02-design/14-Technical-Specs/SPEC-0002-Specification-Standard.md
        """
    )

    parser.add_argument(
        'files',
        nargs='*',
        help='Files to validate (defaults to docs/**/*.md)'
    )

    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json', 'github'],
        default='text',
        help='Output format (default: text)'
    )

    parser.add_argument(
        '--errors-only',
        action='store_true',
        help='Only show errors (hide warnings and info)'
    )

    args = parser.parse_args()

    # Get files to validate
    if args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]
    else:
        # Default: scan docs directory
        docs_path = Path('docs')
        if docs_path.exists():
            files = list(docs_path.rglob('*.md'))
        else:
            print("No files specified and docs/ directory not found.")
            sys.exit(1)

    if not files:
        print("No markdown files found to validate.")
        sys.exit(1)

    # Validate files
    all_issues = []
    valid_count = 0
    invalid_count = 0

    print_colored("SDLC 6.0.0 BDD Format Checker", "1;96")
    print_colored("=" * 60, "96")
    print()

    for file_path in sorted(files):
        issues, is_valid = validate_file(file_path)

        # Filter issues based on args
        if args.errors_only:
            issues = [i for i in issues if i.severity == BDDSeverity.ERROR]

        # In strict mode, warnings are treated as errors
        if args.strict:
            for issue in issues:
                if issue.severity == BDDSeverity.WARNING:
                    issue.severity = BDDSeverity.ERROR
            is_valid = not any(i.severity == BDDSeverity.ERROR for i in issues)

        if issues:
            invalid_count += 1
            print_colored(f"✗ {file_path}", "91")
            for issue in issues:
                print(format_issue(issue))
            print()
        else:
            valid_count += 1
            if not args.errors_only:
                print_colored(f"✓ {file_path}", "92")

        all_issues.extend(issues)

    # Print summary
    print_colored("=" * 60, "96")
    print_colored("Summary:", "1")
    print(f"  Total files:   {len(files)}")

    error_count = sum(1 for i in all_issues if i.severity == BDDSeverity.ERROR)
    warning_count = sum(1 for i in all_issues if i.severity == BDDSeverity.WARNING)
    info_count = sum(1 for i in all_issues if i.severity == BDDSeverity.INFO)

    print_colored(f"  Valid:         {valid_count}", "92")
    if invalid_count > 0:
        print_colored(f"  Invalid:       {invalid_count}", "91")
    else:
        print(f"  Invalid:       {invalid_count}")

    print()
    print(f"  Errors:        {error_count}")
    print(f"  Warnings:      {warning_count}")
    print(f"  Info:          {info_count}")

    # Exit with appropriate code
    if error_count > 0:
        print()
        print_colored("❌ BDD validation failed!", "1;91")
        print("See: .claude/templates/ for BDD format examples")
        sys.exit(1)
    elif warning_count > 0:
        print()
        print_colored("⚠ BDD validation passed with warnings", "1;93")
        sys.exit(0)
    else:
        print()
        print_colored("✅ All files valid!", "1;92")
        sys.exit(0)


if __name__ == "__main__":
    main()
