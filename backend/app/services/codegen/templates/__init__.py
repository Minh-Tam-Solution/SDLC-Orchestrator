"""
Codegen Prompt Templates Package.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)

This package contains Vietnamese-optimized prompt templates
for different frameworks and generation scenarios.

Templates:
- FastAPI: Python backend API generation
- NextJS: React/TypeScript frontend generation
- Flutter: Mobile app generation (future)

Author: Backend Lead
Date: December 23, 2025
"""

from .fastapi_templates import FastAPITemplates
from .base_templates import BaseTemplates, TemplateContext

__all__ = [
    "FastAPITemplates",
    "BaseTemplates",
    "TemplateContext"
]
