# IR Processor Technical Specification
## EP-06: IR-Based Backend Scaffold Generation | Sprint 46

**Status**: APPROVED
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Backend Lead + Architect
**Sprint**: Sprint 46 (Jan 20-31, 2026)
**Framework**: SDLC 6.1.0
**Dependency**: Sprint 45 (CodegenProvider + API)

---

## 1. Overview

### 1.1 Purpose

This specification defines the IR (Intermediate Representation) Processor system that transforms validated IR schemas into deterministic backend code scaffolds.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| IR validation against JSON schemas | Frontend/React generation |
| Backend scaffold generation (FastAPI) | One-click deployment |
| SQLAlchemy model generation | DeepCode integration |
| Alembic migration generation | Complex business logic |
| Minimal CRUD endpoint generation | Authentication/Authorization |

### 1.3 Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT                                        │
│  AppBlueprint JSON (from Sprint 45 /codegen/generate)               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────────────┐
│                    IR VALIDATION                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │
│  │ app_blueprint   │ │ module_spec     │ │ data_model      │        │
│  │ .schema.json    │ │ .schema.json    │ │ .schema.json    │        │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘        │
│           │                   │                   │                  │
│           └───────────────────┼───────────────────┘                  │
│                               v                                      │
│                    JSONSchemaValidator                               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Valid IR
                              v
┌─────────────────────────────────────────────────────────────────────┐
│                    IR PROCESSORS                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │
│  │ ProjectProcessor│ │ ModelProcessor  │ │ EndpointProcessor│       │
│  │ (scaffold)      │ │ (entities)      │ │ (CRUD routes)   │        │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘        │
└───────────┼───────────────────┼───────────────────┼─────────────────┘
            │                   │                   │
            v                   v                   v
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUT BUNDLE                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  GeneratedBundle                                              │    │
│  │  ├── app/                                                     │    │
│  │  │   ├── main.py                                              │    │
│  │  │   ├── core/config.py                                       │    │
│  │  │   ├── models/{entity}.py                                   │    │
│  │  │   ├── schemas/{entity}.py                                  │    │
│  │  │   └── api/routes/{module}.py                               │    │
│  │  ├── alembic/                                                 │    │
│  │  │   └── versions/{migration}.py                              │    │
│  │  ├── requirements.txt                                         │    │
│  │  └── docker-compose.yml                                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. IR Schema Reference

### 2.1 AppBlueprint Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "version", "modules"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Application name",
      "example": "Restaurant Order System"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "example": "1.0.0"
    },
    "business_domain": {
      "type": "string",
      "enum": ["restaurant", "hotel", "retail", "custom"],
      "description": "Business domain for template selection"
    },
    "modules": {
      "type": "array",
      "items": { "$ref": "#/definitions/ModuleSpec" },
      "minItems": 1
    },
    "actors": {
      "type": "array",
      "items": { "$ref": "#/definitions/ActorSpec" }
    },
    "database": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["postgresql", "mysql", "sqlite"] },
        "name": { "type": "string" }
      }
    }
  }
}
```

### 2.2 ModuleSpec Schema

```json
{
  "type": "object",
  "required": ["name", "entities"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "example": "orders"
    },
    "entities": {
      "type": "array",
      "items": { "$ref": "#/definitions/DataModelSpec" },
      "minItems": 1
    },
    "operations": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["create", "read", "update", "delete", "list", "search"]
      },
      "default": ["create", "read", "update", "delete", "list"]
    }
  }
}
```

### 2.3 DataModelSpec Schema

```json
{
  "type": "object",
  "required": ["name", "fields"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[A-Z][a-zA-Z0-9]*$",
      "example": "Order"
    },
    "table_name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$"
    },
    "fields": {
      "type": "array",
      "items": { "$ref": "#/definitions/FieldSpec" },
      "minItems": 1
    },
    "relationships": {
      "type": "array",
      "items": { "$ref": "#/definitions/RelationshipSpec" }
    }
  }
}
```

### 2.4 FieldSpec Schema

```json
{
  "type": "object",
  "required": ["name", "type"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$"
    },
    "type": {
      "type": "string",
      "enum": ["string", "text", "integer", "float", "boolean", "datetime", "date", "uuid", "json"]
    },
    "required": { "type": "boolean", "default": false },
    "unique": { "type": "boolean", "default": false },
    "indexed": { "type": "boolean", "default": false },
    "default": { "type": ["string", "number", "boolean", "null"] },
    "max_length": { "type": "integer", "minimum": 1 },
    "description": { "type": "string" }
  }
}
```

---

## 3. Architecture

### 3.1 Package Structure

```
backend/app/
├── services/
│   └── codegen/
│       ├── ir/                           # NEW - IR Processing
│       │   ├── __init__.py
│       │   ├── validator.py              # JSON Schema validation
│       │   ├── processor_base.py         # Abstract processor
│       │   ├── project_processor.py      # Scaffold generation
│       │   ├── model_processor.py        # Entity/SQLAlchemy
│       │   ├── endpoint_processor.py     # CRUD routes
│       │   ├── migration_processor.py    # Alembic migrations
│       │   └── bundle_builder.py         # Output assembly
│       ├── templates/                    # NEW - Jinja2 templates
│       │   ├── fastapi/
│       │   │   ├── main.py.j2
│       │   │   ├── config.py.j2
│       │   │   ├── model.py.j2
│       │   │   ├── schema.py.j2
│       │   │   ├── route.py.j2
│       │   │   └── crud.py.j2
│       │   ├── alembic/
│       │   │   ├── env.py.j2
│       │   │   └── migration.py.j2
│       │   └── docker/
│       │       ├── Dockerfile.j2
│       │       └── docker-compose.yml.j2
│       └── ... (existing from Sprint 45)
```

### 3.2 Component Classes

```python
# backend/app/services/codegen/ir/validator.py
from typing import Dict, Any, List, Tuple
from jsonschema import validate, ValidationError, Draft7Validator
from pydantic import BaseModel
import json
from pathlib import Path

class ValidationIssue(BaseModel):
    path: str
    message: str
    severity: str = "error"

class IRValidationResult(BaseModel):
    valid: bool
    issues: List[ValidationIssue]
    normalized_ir: Dict[str, Any] | None = None

class IRValidator:
    """Validates IR against JSON schemas."""

    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self._schemas: Dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all JSON schemas from schema directory."""
        schema_files = [
            "app_blueprint.schema.json",
            "module_spec.schema.json",
            "data_model.schema.json",
            "page_spec.schema.json"
        ]
        for filename in schema_files:
            path = self.schema_dir / filename
            if path.exists():
                with open(path) as f:
                    name = filename.replace(".schema.json", "")
                    self._schemas[name] = json.load(f)

    def validate_app_blueprint(
        self,
        blueprint: Dict[str, Any]
    ) -> IRValidationResult:
        """
        Validate an AppBlueprint against schema.

        Returns:
            IRValidationResult with valid status and any issues
        """
        issues: List[ValidationIssue] = []

        # Validate against app_blueprint schema
        try:
            schema = self._schemas.get("app_blueprint")
            if not schema:
                return IRValidationResult(
                    valid=False,
                    issues=[ValidationIssue(
                        path="",
                        message="app_blueprint schema not found"
                    )]
                )

            validator = Draft7Validator(schema)
            for error in validator.iter_errors(blueprint):
                issues.append(ValidationIssue(
                    path=".".join(str(p) for p in error.path),
                    message=error.message
                ))

            # Validate nested modules
            for i, module in enumerate(blueprint.get("modules", [])):
                module_issues = self._validate_module(module, f"modules[{i}]")
                issues.extend(module_issues)

            if issues:
                return IRValidationResult(valid=False, issues=issues)

            # Normalize and return
            normalized = self._normalize_blueprint(blueprint)
            return IRValidationResult(
                valid=True,
                issues=[],
                normalized_ir=normalized
            )

        except Exception as e:
            return IRValidationResult(
                valid=False,
                issues=[ValidationIssue(path="", message=str(e))]
            )

    def _validate_module(
        self,
        module: Dict[str, Any],
        path_prefix: str
    ) -> List[ValidationIssue]:
        """Validate a module spec."""
        issues = []

        # Validate entities
        for i, entity in enumerate(module.get("entities", [])):
            entity_issues = self._validate_entity(
                entity,
                f"{path_prefix}.entities[{i}]"
            )
            issues.extend(entity_issues)

        return issues

    def _validate_entity(
        self,
        entity: Dict[str, Any],
        path_prefix: str
    ) -> List[ValidationIssue]:
        """Validate an entity/data model spec."""
        issues = []

        # Check entity name is PascalCase
        name = entity.get("name", "")
        if not name or not name[0].isupper():
            issues.append(ValidationIssue(
                path=f"{path_prefix}.name",
                message=f"Entity name must be PascalCase, got: {name}"
            ))

        # Check fields
        fields = entity.get("fields", [])
        if not fields:
            issues.append(ValidationIssue(
                path=f"{path_prefix}.fields",
                message="Entity must have at least one field"
            ))

        for i, field in enumerate(fields):
            if "name" not in field:
                issues.append(ValidationIssue(
                    path=f"{path_prefix}.fields[{i}].name",
                    message="Field must have a name"
                ))
            if "type" not in field:
                issues.append(ValidationIssue(
                    path=f"{path_prefix}.fields[{i}].type",
                    message="Field must have a type"
                ))

        return issues

    def _normalize_blueprint(
        self,
        blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize blueprint with defaults."""
        normalized = blueprint.copy()

        # Set defaults
        if "database" not in normalized:
            normalized["database"] = {
                "type": "postgresql",
                "name": blueprint["name"].lower().replace(" ", "_")
            }

        # Normalize modules
        for module in normalized.get("modules", []):
            if "operations" not in module:
                module["operations"] = ["create", "read", "update", "delete", "list"]

            # Generate table_name for entities
            for entity in module.get("entities", []):
                if "table_name" not in entity:
                    # Convert PascalCase to snake_case
                    name = entity["name"]
                    table_name = "".join(
                        f"_{c.lower()}" if c.isupper() else c
                        for c in name
                    ).lstrip("_")
                    entity["table_name"] = table_name + "s"  # Pluralize

        return normalized
```

### 3.3 Processor Base Class

```python
# backend/app/services/codegen/ir/processor_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

class GeneratedFile(BaseModel):
    """Single generated file."""
    path: str
    content: str
    language: str = "python"

class ProcessorResult(BaseModel):
    """Result from a processor."""
    success: bool
    files: List[GeneratedFile]
    errors: List[str] = []

class IRProcessor(ABC):
    """Abstract base class for IR processors."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """Processor name for logging."""
        pass

    @abstractmethod
    def process(self, ir: Dict[str, Any]) -> ProcessorResult:
        """
        Process IR and generate files.

        Args:
            ir: Normalized IR (AppBlueprint)

        Returns:
            ProcessorResult with generated files
        """
        pass

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a Jinja2 template with context."""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
```

### 3.4 Project Processor

```python
# backend/app/services/codegen/ir/project_processor.py
from typing import Dict, Any
from pathlib import Path
from .processor_base import IRProcessor, ProcessorResult, GeneratedFile

class ProjectProcessor(IRProcessor):
    """Generates project scaffold (main.py, config, requirements)."""

    @property
    def name(self) -> str:
        return "project"

    def process(self, ir: Dict[str, Any]) -> ProcessorResult:
        files = []
        errors = []

        try:
            # Generate main.py
            files.append(GeneratedFile(
                path="app/main.py",
                content=self.render_template("fastapi/main.py.j2", {
                    "app_name": ir["name"],
                    "modules": ir.get("modules", [])
                })
            ))

            # Generate config.py
            files.append(GeneratedFile(
                path="app/core/config.py",
                content=self.render_template("fastapi/config.py.j2", {
                    "app_name": ir["name"],
                    "database": ir.get("database", {})
                })
            ))

            # Generate requirements.txt
            files.append(GeneratedFile(
                path="requirements.txt",
                content=self._generate_requirements(),
                language="text"
            ))

            # Generate docker-compose.yml
            files.append(GeneratedFile(
                path="docker-compose.yml",
                content=self.render_template("docker/docker-compose.yml.j2", {
                    "app_name": ir["name"].lower().replace(" ", "_"),
                    "database": ir.get("database", {})
                }),
                language="yaml"
            ))

            # Generate Dockerfile
            files.append(GeneratedFile(
                path="Dockerfile",
                content=self.render_template("docker/Dockerfile.j2", {}),
                language="dockerfile"
            ))

            return ProcessorResult(success=True, files=files)

        except Exception as e:
            errors.append(str(e))
            return ProcessorResult(success=False, files=files, errors=errors)

    def _generate_requirements(self) -> str:
        """Generate requirements.txt content."""
        return """# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.13.0
psycopg2-binary==2.9.9

# Utils
python-dotenv==1.0.0
httpx==0.25.2
tenacity==8.2.3

# Dev
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
ruff==0.1.7
"""
```

### 3.5 Model Processor

```python
# backend/app/services/codegen/ir/model_processor.py
from typing import Dict, Any, List
from .processor_base import IRProcessor, ProcessorResult, GeneratedFile

class ModelProcessor(IRProcessor):
    """Generates SQLAlchemy models and Pydantic schemas."""

    # Type mapping: IR type -> (SQLAlchemy type, Python type)
    TYPE_MAP = {
        "string": ("String", "str"),
        "text": ("Text", "str"),
        "integer": ("Integer", "int"),
        "float": ("Float", "float"),
        "boolean": ("Boolean", "bool"),
        "datetime": ("DateTime", "datetime"),
        "date": ("Date", "date"),
        "uuid": ("UUID", "UUID"),
        "json": ("JSON", "dict"),
    }

    @property
    def name(self) -> str:
        return "model"

    def process(self, ir: Dict[str, Any]) -> ProcessorResult:
        files = []
        errors = []

        try:
            # Collect all entities from all modules
            all_entities = []
            for module in ir.get("modules", []):
                for entity in module.get("entities", []):
                    all_entities.append({
                        **entity,
                        "module_name": module["name"]
                    })

            # Generate base model
            files.append(GeneratedFile(
                path="app/models/base.py",
                content=self._generate_base_model()
            ))

            # Generate model for each entity
            for entity in all_entities:
                files.append(GeneratedFile(
                    path=f"app/models/{entity['table_name'].rstrip('s')}.py",
                    content=self.render_template("fastapi/model.py.j2", {
                        "entity": entity,
                        "type_map": self.TYPE_MAP
                    })
                ))

                # Generate Pydantic schema
                files.append(GeneratedFile(
                    path=f"app/schemas/{entity['table_name'].rstrip('s')}.py",
                    content=self.render_template("fastapi/schema.py.j2", {
                        "entity": entity,
                        "type_map": self.TYPE_MAP
                    })
                ))

            # Generate __init__.py for models
            files.append(GeneratedFile(
                path="app/models/__init__.py",
                content=self._generate_models_init(all_entities)
            ))

            # Generate __init__.py for schemas
            files.append(GeneratedFile(
                path="app/schemas/__init__.py",
                content=self._generate_schemas_init(all_entities)
            ))

            return ProcessorResult(success=True, files=files)

        except Exception as e:
            errors.append(str(e))
            return ProcessorResult(success=False, files=files, errors=errors)

    def _generate_base_model(self) -> str:
        return '''"""Base model with common fields."""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
'''

    def _generate_models_init(self, entities: List[Dict]) -> str:
        imports = ["from .base import Base, TimestampMixin"]
        for entity in entities:
            model_file = entity["table_name"].rstrip("s")
            imports.append(f"from .{model_file} import {entity['name']}")

        exports = ["Base", "TimestampMixin"] + [e["name"] for e in entities]

        return "\n".join(imports) + f"\n\n__all__ = {exports}\n"

    def _generate_schemas_init(self, entities: List[Dict]) -> str:
        imports = []
        for entity in entities:
            schema_file = entity["table_name"].rstrip("s")
            imports.append(
                f"from .{schema_file} import "
                f"{entity['name']}Create, {entity['name']}Read, {entity['name']}Update"
            )

        exports = []
        for entity in entities:
            name = entity["name"]
            exports.extend([f"{name}Create", f"{name}Read", f"{name}Update"])

        return "\n".join(imports) + f"\n\n__all__ = {exports}\n"
```

### 3.6 Endpoint Processor

```python
# backend/app/services/codegen/ir/endpoint_processor.py
from typing import Dict, Any, List
from .processor_base import IRProcessor, ProcessorResult, GeneratedFile

class EndpointProcessor(IRProcessor):
    """Generates CRUD API endpoints."""

    @property
    def name(self) -> str:
        return "endpoint"

    def process(self, ir: Dict[str, Any]) -> ProcessorResult:
        files = []
        errors = []

        try:
            for module in ir.get("modules", []):
                module_name = module["name"]
                operations = module.get("operations", [])
                entities = module.get("entities", [])

                # Generate route file for module
                files.append(GeneratedFile(
                    path=f"app/api/routes/{module_name}.py",
                    content=self.render_template("fastapi/route.py.j2", {
                        "module_name": module_name,
                        "entities": entities,
                        "operations": operations
                    })
                ))

                # Generate CRUD service for each entity
                for entity in entities:
                    files.append(GeneratedFile(
                        path=f"app/services/{entity['table_name'].rstrip('s')}_service.py",
                        content=self.render_template("fastapi/crud.py.j2", {
                            "entity": entity,
                            "operations": operations
                        })
                    ))

            # Generate api/__init__.py with router registration
            files.append(GeneratedFile(
                path="app/api/__init__.py",
                content=self._generate_api_init(ir.get("modules", []))
            ))

            # Generate api/routes/__init__.py
            files.append(GeneratedFile(
                path="app/api/routes/__init__.py",
                content=self._generate_routes_init(ir.get("modules", []))
            ))

            return ProcessorResult(success=True, files=files)

        except Exception as e:
            errors.append(str(e))
            return ProcessorResult(success=False, files=files, errors=errors)

    def _generate_api_init(self, modules: List[Dict]) -> str:
        imports = ["from fastapi import APIRouter"]
        for module in modules:
            imports.append(f"from .routes.{module['name']} import router as {module['name']}_router")

        router_setup = [
            "",
            "api_router = APIRouter()",
            ""
        ]
        for module in modules:
            router_setup.append(
                f'api_router.include_router({module["name"]}_router, prefix="/{module["name"]}", tags=["{module["name"]}"])'
            )

        return "\n".join(imports + router_setup) + "\n"

    def _generate_routes_init(self, modules: List[Dict]) -> str:
        imports = []
        for module in modules:
            imports.append(f"from .{module['name']} import router as {module['name']}_router")

        exports = [f"{m['name']}_router" for m in modules]

        return "\n".join(imports) + f"\n\n__all__ = {exports}\n"
```

### 3.7 Bundle Builder

```python
# backend/app/services/codegen/ir/bundle_builder.py
from typing import Dict, Any, List
from pydantic import BaseModel
from pathlib import Path
from .validator import IRValidator, IRValidationResult
from .project_processor import ProjectProcessor
from .model_processor import ModelProcessor
from .endpoint_processor import EndpointProcessor
from .processor_base import GeneratedFile, ProcessorResult

class GeneratedBundle(BaseModel):
    """Complete generated output bundle."""
    success: bool
    app_name: str
    files: List[GeneratedFile]
    file_count: int
    total_lines: int
    errors: List[str] = []
    warnings: List[str] = []

class BundleBuilder:
    """Orchestrates IR processing and bundle generation."""

    def __init__(self, schema_dir: Path, template_dir: Path):
        self.validator = IRValidator(schema_dir)
        self.processors = [
            ProjectProcessor(template_dir / "fastapi"),
            ModelProcessor(template_dir / "fastapi"),
            EndpointProcessor(template_dir / "fastapi"),
        ]

    def build(self, blueprint: Dict[str, Any]) -> GeneratedBundle:
        """
        Build complete bundle from AppBlueprint.

        Args:
            blueprint: Raw AppBlueprint JSON

        Returns:
            GeneratedBundle with all files
        """
        all_files: List[GeneratedFile] = []
        all_errors: List[str] = []

        # Step 1: Validate IR
        validation = self.validator.validate_app_blueprint(blueprint)
        if not validation.valid:
            return GeneratedBundle(
                success=False,
                app_name=blueprint.get("name", "unknown"),
                files=[],
                file_count=0,
                total_lines=0,
                errors=[f"{i.path}: {i.message}" for i in validation.issues]
            )

        normalized_ir = validation.normalized_ir

        # Step 2: Run processors
        for processor in self.processors:
            result = processor.process(normalized_ir)
            all_files.extend(result.files)
            all_errors.extend(result.errors)

        # Step 3: Calculate stats
        total_lines = sum(
            len(f.content.split("\n"))
            for f in all_files
        )

        return GeneratedBundle(
            success=len(all_errors) == 0,
            app_name=normalized_ir["name"],
            files=all_files,
            file_count=len(all_files),
            total_lines=total_lines,
            errors=all_errors
        )
```

---

## 4. Jinja2 Templates

### 4.1 main.py.j2

```jinja2
"""{{ app_name }} - Generated FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import api_router

app = FastAPI(
    title="{{ app_name }}",
    description="Generated by SDLC Orchestrator EP-06",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": "{{ app_name }}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4.2 model.py.j2

```jinja2
"""{{ entity.name }} model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from .base import Base, TimestampMixin


class {{ entity.name }}(Base, TimestampMixin):
    """{{ entity.name }} database model."""

    __tablename__ = "{{ entity.table_name }}"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

{% for field in entity.fields %}
{% set sa_type, py_type = type_map.get(field.type, ('String', 'str')) %}
    {{ field.name }}: Mapped[{% if not field.required %}Optional[{% endif %}{{ py_type }}{% if not field.required %}]{% endif %}] = mapped_column(
        {{ sa_type }}{% if field.max_length %}({{ field.max_length }}){% endif %},
        nullable={{ 'False' if field.required else 'True' }},
        {% if field.unique %}unique=True,{% endif %}
        {% if field.indexed %}index=True,{% endif %}
        {% if field.default is defined %}default={{ field.default | tojson }},{% endif %}
    )
{% endfor %}

    def __repr__(self) -> str:
        return f"<{{ entity.name }}(id={self.id})>"
```

### 4.3 schema.py.j2

```jinja2
"""{{ entity.name }} Pydantic schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class {{ entity.name }}Base(BaseModel):
    """Base schema with shared fields."""
{% for field in entity.fields %}
{% set _, py_type = type_map.get(field.type, ('String', 'str')) %}
    {{ field.name }}: {% if not field.required %}Optional[{% endif %}{{ py_type }}{% if not field.required %}] = None{% endif %}
{% endfor %}


class {{ entity.name }}Create({{ entity.name }}Base):
    """Schema for creating a {{ entity.name }}."""
    pass


class {{ entity.name }}Update(BaseModel):
    """Schema for updating a {{ entity.name }}."""
{% for field in entity.fields %}
{% set _, py_type = type_map.get(field.type, ('String', 'str')) %}
    {{ field.name }}: Optional[{{ py_type }}] = None
{% endfor %}


class {{ entity.name }}Read({{ entity.name }}Base):
    """Schema for reading a {{ entity.name }}."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 4.4 route.py.j2

```jinja2
"""{{ module_name }} API routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
{% for entity in entities %}
from app.schemas.{{ entity.table_name | replace('s', '') }} import (
    {{ entity.name }}Create,
    {{ entity.name }}Read,
    {{ entity.name }}Update
)
from app.services.{{ entity.table_name | replace('s', '') }}_service import {{ entity.name }}Service
{% endfor %}

router = APIRouter()

{% for entity in entities %}
# ============================================================
# {{ entity.name }} CRUD Endpoints
# ============================================================

{% if 'create' in operations %}
@router.post("/{{ entity.table_name }}", response_model={{ entity.name }}Read, status_code=status.HTTP_201_CREATED)
async def create_{{ entity.table_name | replace('s', '') }}(
    data: {{ entity.name }}Create,
    db: AsyncSession = Depends(get_db)
) -> {{ entity.name }}Read:
    """Create a new {{ entity.name }}."""
    service = {{ entity.name }}Service(db)
    return await service.create(data)
{% endif %}

{% if 'list' in operations %}
@router.get("/{{ entity.table_name }}", response_model=List[{{ entity.name }}Read])
async def list_{{ entity.table_name }}(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[{{ entity.name }}Read]:
    """List all {{ entity.table_name }}."""
    service = {{ entity.name }}Service(db)
    return await service.list(skip=skip, limit=limit)
{% endif %}

{% if 'read' in operations %}
@router.get("/{{ entity.table_name }}/{id}", response_model={{ entity.name }}Read)
async def get_{{ entity.table_name | replace('s', '') }}(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> {{ entity.name }}Read:
    """Get a {{ entity.name }} by ID."""
    service = {{ entity.name }}Service(db)
    item = await service.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="{{ entity.name }} not found")
    return item
{% endif %}

{% if 'update' in operations %}
@router.patch("/{{ entity.table_name }}/{id}", response_model={{ entity.name }}Read)
async def update_{{ entity.table_name | replace('s', '') }}(
    id: UUID,
    data: {{ entity.name }}Update,
    db: AsyncSession = Depends(get_db)
) -> {{ entity.name }}Read:
    """Update a {{ entity.name }}."""
    service = {{ entity.name }}Service(db)
    item = await service.update(id, data)
    if not item:
        raise HTTPException(status_code=404, detail="{{ entity.name }} not found")
    return item
{% endif %}

{% if 'delete' in operations %}
@router.delete("/{{ entity.table_name }}/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{{ entity.table_name | replace('s', '') }}(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a {{ entity.name }}."""
    service = {{ entity.name }}Service(db)
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="{{ entity.name }} not found")
{% endif %}

{% endfor %}
```

---

## 5. API Integration

### 5.1 Enhanced /codegen/generate Endpoint

The existing `/codegen/generate` endpoint from Sprint 45 will be enhanced to use IR processors:

```python
# Update to backend/app/api/routes/codegen.py

@router.post("/generate")
async def generate_code(
    request: GenerateRequest,
    current_user = Depends(get_current_user)
):
    """Generate code from IR specification."""
    try:
        # Use BundleBuilder for IR processing
        bundle_builder = BundleBuilder(
            schema_dir=settings.IR_SCHEMA_DIR,
            template_dir=settings.CODEGEN_TEMPLATE_DIR
        )

        bundle = bundle_builder.build(request.app_blueprint)

        if not bundle.success:
            raise HTTPException(
                status_code=400,
                detail={"errors": bundle.errors}
            )

        return {
            "success": True,
            "result": {
                "success": True,
                "files": [f.dict() for f in bundle.files],
                "provider": "ir_processor",  # Deterministic, no AI
                "file_count": bundle.file_count,
                "total_lines": bundle.total_lines,
                "metadata": {
                    "app_name": bundle.app_name,
                    "generator": "SDLC Orchestrator EP-06"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# backend/tests/unit/services/codegen/ir/test_validator.py

import pytest
from app.services.codegen.ir.validator import IRValidator, IRValidationResult

class TestIRValidator:
    @pytest.fixture
    def validator(self, tmp_path):
        # Create test schemas
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        # ... write test schemas
        return IRValidator(schema_dir)

    def test_valid_blueprint(self, validator):
        blueprint = {
            "name": "Test App",
            "version": "1.0.0",
            "modules": [{
                "name": "orders",
                "entities": [{
                    "name": "Order",
                    "fields": [{"name": "status", "type": "string"}]
                }]
            }]
        }

        result = validator.validate_app_blueprint(blueprint)

        assert result.valid is True
        assert len(result.issues) == 0

    def test_invalid_entity_name(self, validator):
        blueprint = {
            "name": "Test App",
            "version": "1.0.0",
            "modules": [{
                "name": "orders",
                "entities": [{
                    "name": "order",  # Should be PascalCase
                    "fields": [{"name": "status", "type": "string"}]
                }]
            }]
        }

        result = validator.validate_app_blueprint(blueprint)

        assert result.valid is False
        assert any("PascalCase" in i.message for i in result.issues)
```

### 6.2 Integration Tests

```python
# backend/tests/integration/test_ir_bundle.py

import pytest
from app.services.codegen.ir.bundle_builder import BundleBuilder

class TestBundleBuilder:
    @pytest.fixture
    def builder(self):
        return BundleBuilder(
            schema_dir=Path("backend/app/schemas/codegen"),
            template_dir=Path("backend/app/services/codegen/templates")
        )

    def test_generate_restaurant_app(self, builder):
        blueprint = {
            "name": "Restaurant Order System",
            "version": "1.0.0",
            "business_domain": "restaurant",
            "modules": [{
                "name": "orders",
                "entities": [{
                    "name": "Order",
                    "fields": [
                        {"name": "table_number", "type": "integer", "required": True},
                        {"name": "status", "type": "string", "required": True},
                        {"name": "total", "type": "float"}
                    ]
                }],
                "operations": ["create", "read", "list", "update"]
            }]
        }

        bundle = builder.build(blueprint)

        assert bundle.success is True
        assert bundle.file_count > 5

        # Check key files exist
        file_paths = [f.path for f in bundle.files]
        assert "app/main.py" in file_paths
        assert "app/models/order.py" in file_paths
        assert "app/api/routes/orders.py" in file_paths

    def test_generated_code_is_valid_python(self, builder):
        # ... test that generated code compiles
        pass
```

---

## 7. Sprint 46 Implementation Checklist

### Week 1 (Jan 20-24)

- [ ] Create package structure (`backend/app/services/codegen/ir/`)
- [ ] Implement `validator.py` with JSON Schema validation
- [ ] Implement `processor_base.py` abstract class
- [ ] Create Jinja2 template directory structure
- [ ] Implement `project_processor.py` (scaffold)
- [ ] Write unit tests for validator

### Week 2 (Jan 27-31)

- [ ] Implement `model_processor.py` (SQLAlchemy models)
- [ ] Implement `endpoint_processor.py` (CRUD routes)
- [ ] Implement `bundle_builder.py` orchestrator
- [ ] Create all Jinja2 templates
- [ ] Write integration tests
- [ ] Demo: generate restaurant app from IR

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Backend Lead + Architect |
| **Status** | APPROVED |
| **Sprint** | Sprint 46 (Jan 20-31, 2026) |
| **Dependency** | Sprint 45 |
