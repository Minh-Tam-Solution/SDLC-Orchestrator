"""
SDLC 6.0.5 Pre-commit hook for validation.

This module provides pre-commit hook functionality to validate
SDLC structure compliance before commits.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from sdlcctl.validation.engine import SDLCValidator
from sdlcctl.validation.tier import Tier


def get_project_root() -> Path:
    """
    Get the root directory of the current git project.

    Returns:
        Path to the project root, or current working directory if not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def run_validation(
    project_root: Optional[Path] = None,
    docs_root: str = "docs",
    tier: str = "lite",
    strict: bool = False,
    performance_threshold: float = 2.0,
) -> int:
    """
    Run SDLC validation on a project.

    Args:
        project_root: Path to the project root. Uses git root if not specified.
        docs_root: Relative path to docs directory (default: "docs").
        tier: Project tier (lite, standard, professional, enterprise).
        strict: If True, treat warnings as errors.
        performance_threshold: Maximum allowed validation time in seconds.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if project_root is None:
        project_root = get_project_root()

    try:
        tier_enum = Tier.from_string(tier)
    except ValueError:
        # Invalid tier, use default LITE
        tier_enum = Tier.LITE

    validator = SDLCValidator(project_root, docs_root=docs_root, tier=tier_enum)
    result = validator.validate()

    # Check performance
    validation_time = result.validation_time_ms / 1000  # Convert to seconds
    if validation_time > performance_threshold:
        return 1

    # Check for errors
    if result.error_count > 0:
        return 1

    # In strict mode, warnings are treated as errors
    if strict and result.warning_count > 0:
        return 1

    return 0


def main() -> int:
    """
    Main entry point for the pre-commit hook.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(description="SDLC pre-commit validation hook")
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Project root path (defaults to git root)",
    )
    parser.add_argument(
        "--tier",
        default="lite",
        choices=["lite", "standard", "professional", "enterprise"],
        help="Project tier",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--performance-threshold",
        type=float,
        default=2.0,
        help="Maximum validation time in seconds",
    )

    args = parser.parse_args()

    project_root = Path(args.path) if args.path else None

    exit_code = run_validation(
        project_root=project_root,
        tier=args.tier,
        strict=args.strict,
        performance_threshold=args.performance_threshold,
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
