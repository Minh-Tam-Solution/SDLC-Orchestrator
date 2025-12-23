"""
Codegen IR Schemas Package.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)

This package contains IR (Intermediate Representation) schemas
for structured code generation. These schemas define the app
blueprint format used by all providers.

Schemas:
- AppBlueprint: Top-level app definition
- ModuleSpec: Module/feature definition
- EntitySpec: Data entity definition
- FieldSpec: Entity field definition

Author: Backend Lead
Date: December 23, 2025
"""

from .app_blueprint import (
    AppBlueprint,
    ModuleSpec,
    EntitySpec,
    FieldSpec,
    RelationSpec,
    FieldType,
    RelationType
)

__all__ = [
    "AppBlueprint",
    "ModuleSpec",
    "EntitySpec",
    "FieldSpec",
    "RelationSpec",
    "FieldType",
    "RelationType"
]
