"""Consistency report formatters.

SDLC 6.0.5 - SPEC-0021 Stage Consistency Validation.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from ..violation import Severity
from .models import ConsistencyResult, ConsistencyStatus


class ConsistencyReportFormatter:
    """Format consistency validation results for output."""

    def format_text(self, result: ConsistencyResult, verbose: bool = False) -> str:
        """Format result as human-readable text.

        Args:
            result: Consistency validation result
            verbose: Include detailed context

        Returns:
            Formatted text report
        """
        lines = []

        # Header
        lines.append("Stage Consistency Validation Report")
        lines.append("=" * 40)
        lines.append(f"Project: {result.project_name}")
        lines.append(f"Tier: {result.tier.value.upper()}")
        lines.append(f"Framework: SDLC {result.framework_version}")
        lines.append(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        # Stage Consistency Results
        lines.append("Stage Consistency Results:")
        lines.append("-" * 30)

        stage_pair_labels = {
            "stage_01_02": "Stage 01 ←→ Stage 02",
            "stage_02_03": "Stage 02 ←→ Stage 03",
            "stage_03_04": "Stage 03 ←→ Stage 04",
            "stage_01_04": "Stage 01 ←→ Stage 04",
        }

        for pair_id, pair_result in result.stage_pairs.items():
            label = stage_pair_labels.get(pair_id, pair_id)
            status_icon = self._get_status_icon(pair_result.status)
            violation_count = len(pair_result.violations)

            if pair_result.status == ConsistencyStatus.CONSISTENT:
                lines.append(f"{status_icon} {label}: CONSISTENT (0 violations)")
            elif pair_result.status == ConsistencyStatus.ERROR:
                lines.append(f"{status_icon} {label}: ERROR - {pair_result.error_message}")
            else:
                lines.append(f"{status_icon} {label}: {violation_count} violations")

        lines.append("")

        # Violations
        if result.all_violations:
            lines.append("Violations:")
            lines.append("-" * 30)

            for violation in result.all_violations:
                severity_icon = self._get_severity_icon(violation.severity)
                severity_label = violation.severity.value.upper()

                lines.append(f"[{severity_label}] {violation.rule_id}: {violation.message}")

                if violation.target_file:
                    file_str = str(violation.target_file)
                    if violation.line_number:
                        file_str += f":{violation.line_number}"
                    lines.append(f"  File: {file_str}")

                if violation.expected:
                    lines.append(f"  Expected: {violation.expected}")
                if violation.actual:
                    lines.append(f"  Actual: {violation.actual}")
                if violation.fix_suggestion:
                    lines.append(f"  Fix: {violation.fix_suggestion}")

                if verbose and violation.context:
                    lines.append(f"  Context: {violation.context}")

                lines.append("")

        # Summary
        lines.append("Summary:")
        lines.append("-" * 30)
        lines.append(f"Total violations: {result.total_violations}")
        lines.append(f"  Errors: {result.error_count}")
        lines.append(f"  Warnings: {result.warning_count}")
        lines.append(f"  Info: {result.info_count}")
        lines.append("")
        lines.append(f"Overall consistency: {result.overall_consistency_percent:.1f}%")
        lines.append(f"Execution time: {result.execution_time_seconds:.2f}s")

        return "\n".join(lines)

    def format_json(self, result: ConsistencyResult) -> str:
        """Format result as JSON.

        Args:
            result: Consistency validation result

        Returns:
            JSON string
        """
        data = result.to_dict()
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        return json.dumps(data, indent=2, default=str)

    def format_github(self, result: ConsistencyResult) -> str:
        """Format result as GitHub Actions annotations.

        Args:
            result: Consistency validation result

        Returns:
            GitHub Actions annotation commands
        """
        lines = []

        for violation in result.all_violations:
            # GitHub annotation format:
            # ::error file={name},line={line}::{message}
            # ::warning file={name},line={line}::{message}

            if violation.severity == Severity.ERROR:
                level = "error"
            elif violation.severity == Severity.WARNING:
                level = "warning"
            else:
                level = "notice"

            file_part = ""
            if violation.target_file:
                file_part = f"file={violation.target_file}"
                if violation.line_number:
                    file_part += f",line={violation.line_number}"

            message = f"{violation.rule_id}: {violation.message}"
            if violation.expected and violation.actual:
                message += f" - Expected: {violation.expected}, Actual: {violation.actual}"

            if file_part:
                lines.append(f"::{level} {file_part}::{message}")
            else:
                lines.append(f"::{level}::{message}")

        # Add summary
        if result.passed:
            lines.append(f"::notice::Stage Consistency Validation PASSED ({result.overall_consistency_percent:.1f}%)")
        else:
            lines.append(f"::error::Stage Consistency Validation FAILED - {result.error_count} errors")

        return "\n".join(lines)

    def format_summary(self, result: ConsistencyResult) -> str:
        """Format result as one-line summary.

        Args:
            result: Consistency validation result

        Returns:
            One-line summary string
        """
        status = "PASS" if result.passed else "FAIL"
        return (
            f"{status} | "
            f"Consistency: {result.overall_consistency_percent:.1f}% | "
            f"Errors: {result.error_count} | "
            f"Warnings: {result.warning_count} | "
            f"Info: {result.info_count} | "
            f"Time: {result.execution_time_seconds:.2f}s"
        )

    def _get_status_icon(self, status: ConsistencyStatus) -> str:
        """Get icon for consistency status."""
        icons = {
            ConsistencyStatus.CONSISTENT: "✅",
            ConsistencyStatus.INCONSISTENT: "⚠️ ",
            ConsistencyStatus.SKIPPED: "⏭️ ",
            ConsistencyStatus.ERROR: "❌",
        }
        return icons.get(status, "❓")

    def _get_severity_icon(self, severity: Severity) -> str:
        """Get icon for severity level."""
        icons = {
            Severity.ERROR: "❌",
            Severity.WARNING: "⚠️",
            Severity.INFO: "ℹ️",
        }
        return icons.get(severity, "❓")
