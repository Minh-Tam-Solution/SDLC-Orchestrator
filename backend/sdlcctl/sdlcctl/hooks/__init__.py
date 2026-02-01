"""SDLC Orchestrator pre-commit hooks module."""

from sdlcctl.hooks.pre_commit import run_validation, get_project_root, main

__all__ = ["run_validation", "get_project_root", "main"]
