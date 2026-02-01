"""SDLC 6.0.0 Git Hooks."""

from .pre_commit import main as pre_commit_hook

__all__ = ["pre_commit_hook"]
