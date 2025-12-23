"""
App Blueprint IR Schema.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
ADR-022: IR-Based Generation (96% token reduction)

This module defines the Intermediate Representation (IR) schema
for app blueprints. Using IR instead of full context reduces
token usage by 96% (128K → 5K tokens).

Schema Hierarchy:
- AppBlueprint (top-level)
  - ModuleSpec (feature/module)
    - EntitySpec (data model)
      - FieldSpec (model field)
      - RelationSpec (relationships)

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """
    Supported field types for entity fields.

    Maps to SQLAlchemy/Pydantic types during code generation.
    """
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    UUID = "uuid"
    JSON = "json"
    ENUM = "enum"
    FILE = "file"
    IMAGE = "image"


class RelationType(str, Enum):
    """
    Relationship types between entities.
    """
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class FieldSpec(BaseModel):
    """
    Field specification for an entity.

    Defines a single field in a data model, including type,
    constraints, and validation rules.

    Example:
        >>> field = FieldSpec(
        ...     name="email",
        ...     type=FieldType.STRING,
        ...     max_length=255,
        ...     unique=True,
        ...     nullable=False
        ... )
    """
    name: str = Field(
        ...,
        description="Field name (snake_case)",
        pattern=r"^[a-z][a-z0-9_]*$"
    )
    type: FieldType = Field(
        ...,
        description="Field data type"
    )
    description: Optional[str] = Field(
        None,
        description="Field description (Vietnamese OK)"
    )
    primary: bool = Field(
        False,
        description="Is primary key"
    )
    nullable: bool = Field(
        True,
        description="Allow NULL values"
    )
    unique: bool = Field(
        False,
        description="Unique constraint"
    )
    indexed: bool = Field(
        False,
        description="Create index"
    )
    default: Optional[Any] = Field(
        None,
        description="Default value"
    )
    # String-specific
    max_length: Optional[int] = Field(
        None,
        description="Max length for string fields"
    )
    min_length: Optional[int] = Field(
        None,
        description="Min length for string fields"
    )
    # Numeric-specific
    min_value: Optional[float] = Field(
        None,
        description="Minimum value for numeric fields"
    )
    max_value: Optional[float] = Field(
        None,
        description="Maximum value for numeric fields"
    )
    # Enum-specific
    enum_values: Optional[List[str]] = Field(
        None,
        description="Allowed values for enum fields"
    )
    # Validation
    regex: Optional[str] = Field(
        None,
        description="Regex pattern for validation"
    )


class RelationSpec(BaseModel):
    """
    Relationship specification between entities.

    Example:
        >>> relation = RelationSpec(
        ...     name="tasks",
        ...     target_entity="Task",
        ...     type=RelationType.ONE_TO_MANY,
        ...     back_populates="user"
        ... )
    """
    name: str = Field(
        ...,
        description="Relationship name"
    )
    target_entity: str = Field(
        ...,
        description="Target entity name"
    )
    type: RelationType = Field(
        ...,
        description="Relationship type"
    )
    back_populates: Optional[str] = Field(
        None,
        description="Back-reference name in target entity"
    )
    cascade: str = Field(
        "all, delete-orphan",
        description="SQLAlchemy cascade options"
    )
    lazy: str = Field(
        "selectin",
        description="SQLAlchemy lazy loading strategy"
    )


class EntitySpec(BaseModel):
    """
    Entity (data model) specification.

    Defines a database table/model with its fields and relationships.

    Example:
        >>> entity = EntitySpec(
        ...     name="User",
        ...     description="Người dùng hệ thống",
        ...     fields=[
        ...         FieldSpec(name="id", type=FieldType.UUID, primary=True),
        ...         FieldSpec(name="email", type=FieldType.STRING, unique=True)
        ...     ]
        ... )
    """
    name: str = Field(
        ...,
        description="Entity name (PascalCase)",
        pattern=r"^[A-Z][a-zA-Z0-9]*$"
    )
    description: Optional[str] = Field(
        None,
        description="Entity description (Vietnamese OK)"
    )
    table_name: Optional[str] = Field(
        None,
        description="Custom table name (default: snake_case of name)"
    )
    fields: List[FieldSpec] = Field(
        default_factory=list,
        description="Entity fields"
    )
    relations: List[RelationSpec] = Field(
        default_factory=list,
        description="Entity relationships"
    )
    # Behavior flags
    soft_delete: bool = Field(
        True,
        description="Enable soft delete (deleted_at column)"
    )
    timestamps: bool = Field(
        True,
        description="Add created_at, updated_at columns"
    )
    auditable: bool = Field(
        False,
        description="Track created_by, updated_by"
    )


class ModuleSpec(BaseModel):
    """
    Module (feature) specification.

    Groups related entities and defines API endpoints.

    Example:
        >>> module = ModuleSpec(
        ...     name="tasks",
        ...     description="Quản lý công việc",
        ...     entities=[EntitySpec(name="Task", ...)]
        ... )
    """
    name: str = Field(
        ...,
        description="Module name (snake_case)",
        pattern=r"^[a-z][a-z0-9_]*$"
    )
    description: Optional[str] = Field(
        None,
        description="Module description (Vietnamese OK)"
    )
    entities: List[EntitySpec] = Field(
        default_factory=list,
        description="Entities in this module"
    )
    # API generation
    generate_crud: bool = Field(
        True,
        description="Generate CRUD endpoints"
    )
    generate_schemas: bool = Field(
        True,
        description="Generate Pydantic schemas"
    )
    api_prefix: Optional[str] = Field(
        None,
        description="Custom API prefix (default: /{module_name})"
    )
    # Access control
    auth_required: bool = Field(
        True,
        description="Require authentication for all endpoints"
    )
    roles_required: Optional[List[str]] = Field(
        None,
        description="Required roles for module access"
    )


class AppBlueprint(BaseModel):
    """
    Top-level app blueprint specification.

    This is the main IR schema that defines an entire application.
    Used by codegen providers to generate complete, production-ready code.

    Example:
        >>> blueprint = AppBlueprint(
        ...     name="TaskManager",
        ...     description="Hệ thống quản lý công việc cho SME",
        ...     modules=[
        ...         ModuleSpec(name="tasks", entities=[...]),
        ...         ModuleSpec(name="users", entities=[...])
        ...     ]
        ... )

    Cost Savings:
        Full Context: 128K tokens ($0.50/generation)
        IR-Based: 5K tokens ($0.02/generation)
        Savings: 96% reduction, 25x cheaper
    """
    name: str = Field(
        ...,
        description="Application name (PascalCase)",
        pattern=r"^[A-Z][a-zA-Z0-9]*$"
    )
    description: Optional[str] = Field(
        None,
        description="Application description (Vietnamese OK)"
    )
    version: str = Field(
        "1.0.0",
        description="Application version"
    )
    modules: List[ModuleSpec] = Field(
        default_factory=list,
        description="Application modules"
    )

    # Technology stack
    language: str = Field(
        "python",
        description="Target programming language"
    )
    framework: str = Field(
        "fastapi",
        description="Target framework"
    )
    database: str = Field(
        "postgresql",
        description="Target database"
    )

    # Features
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "authentication": True,
            "authorization": True,
            "pagination": True,
            "filtering": True,
            "sorting": True,
            "soft_delete": True,
            "audit_log": False,
            "rate_limiting": False,
            "caching": False
        },
        description="Enabled features"
    )

    # Metadata
    author: Optional[str] = Field(
        None,
        description="Blueprint author"
    )
    organization: Optional[str] = Field(
        None,
        description="Organization name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "TaskManager",
                "description": "Hệ thống quản lý công việc cho SME Việt Nam",
                "version": "1.0.0",
                "modules": [
                    {
                        "name": "tasks",
                        "description": "Quản lý công việc",
                        "entities": [
                            {
                                "name": "Task",
                                "description": "Công việc cần làm",
                                "fields": [
                                    {"name": "id", "type": "uuid", "primary": True},
                                    {"name": "title", "type": "string", "max_length": 200},
                                    {"name": "description", "type": "text", "nullable": True},
                                    {"name": "status", "type": "enum", "enum_values": ["todo", "in_progress", "done"]},
                                    {"name": "priority", "type": "integer", "min_value": 1, "max_value": 5},
                                    {"name": "due_date", "type": "datetime", "nullable": True}
                                ]
                            }
                        ]
                    }
                ],
                "language": "python",
                "framework": "fastapi",
                "database": "postgresql",
                "author": "Backend Lead"
            }
        }
