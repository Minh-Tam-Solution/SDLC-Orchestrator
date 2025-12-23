"""
Codegen Demo Blueprints.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)

Demo blueprints for testing and showcasing the codegen engine.
"""

from .vietnamese_sme_demo import (
    get_retail_store_blueprint,
    get_minimal_demo_blueprint,
    DEMO_BLUEPRINTS
)

__all__ = [
    "get_retail_store_blueprint",
    "get_minimal_demo_blueprint",
    "DEMO_BLUEPRINTS"
]
