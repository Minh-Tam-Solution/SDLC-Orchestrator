"""
SASE Adapter — Thin Facade for VCR/CRP Decoupling.

Sprint 191 (SPRINT-191-UNIFIED-COMMAND-REGISTRY, Day 4).

Problem: vcr_service.py and crp_service.py import create_sase_generation_service
directly from sase_generation_service.py. This tight coupling blocked SASE
refactoring in Sprint 190.

Solution: Re-export the factory function through this adapter. VCR/CRP import
from here instead, allowing sase_generation_service.py to be moved/refactored
independently in future sprints.

Usage:
    from app.services.sase_adapter import create_sase_generation_service
"""

from app.services.sase_generation_service import (  # noqa: F401
    create_sase_generation_service,
)
