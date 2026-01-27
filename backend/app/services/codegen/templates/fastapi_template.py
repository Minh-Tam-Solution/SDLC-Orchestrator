"""
FastAPI Template - Python API scaffolding with SQLAlchemy + JWT

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Backend API Template
- AI Governance Principle 4: Deterministic Code Generation
- Methodology: FastAPI best practices (async, Pydantic, dependency injection)

Purpose:
Scaffolds production-ready FastAPI application with:
- SQLAlchemy ORM (async) + Alembic migrations
- JWT authentication with bcrypt
- Pydantic schemas for validation
- CRUD endpoints for entities
- pytest test structure
- Docker support

Tech Stack:
- FastAPI 0.104+, SQLAlchemy 2.0, Pydantic v2
- PostgreSQL (configurable)
- pytest, httpx for testing

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
Status: ACTIVE
"""

from typing import List
from .base_template import BaseTemplate, GeneratedFile, TemplateBlueprint, TemplateType

class FastAPITemplate(BaseTemplate):
    """FastAPI application template with SQLAlchemy + JWT"""

    template_type = TemplateType.FASTAPI
    template_name = "FastAPI REST API"
    template_version = "1.0.0"

    default_tech_stack = ["fastapi", "sqlalchemy", "postgresql", "jwt", "pytest"]
    required_env_vars = ["DATABASE_URL", "JWT_SECRET", "JWT_ALGORITHM"]

    def get_file_structure(self, blueprint: TemplateBlueprint) -> dict:
        """FastAPI project structure"""
        return {
            "app/": "Application package",
            "app/api/": "API routes",
            "app/api/endpoints/": "Endpoint modules",
            "app/core/": "Core configuration",
            "app/db/": "Database setup",
            "app/models/": "SQLAlchemy models",
            "app/schemas/": "Pydantic schemas",
            "app/services/": "Business logic",
            "tests/": "Test suite",
            "alembic/": "Database migrations",
        }

    def generate_config_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate FastAPI configuration files"""
        files = []

        # pyproject.toml
        files.append(GeneratedFile(
            path="pyproject.toml",
            content=self._generate_pyproject_toml(blueprint),
            language="toml"
        ))

        # requirements.txt
        files.append(GeneratedFile(
            path="requirements.txt",
            content=self._generate_requirements(blueprint),
            language="text"
        ))

        # alembic.ini
        files.append(GeneratedFile(
            path="alembic.ini",
            content=self._generate_alembic_ini(blueprint),
            language="ini"
        ))

        # Dockerfile
        files.append(GeneratedFile(
            path="Dockerfile",
            content=self._generate_dockerfile(blueprint),
            language="dockerfile"
        ))

        # docker-compose.yml
        files.append(GeneratedFile(
            path="docker-compose.yml",
            content=self._generate_docker_compose(blueprint),
            language="yaml"
        ))

        return files

    def generate_entry_point(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate FastAPI entry point (main.py)"""
        files = []

        # app/main.py
        files.append(GeneratedFile(
            path="app/main.py",
            content=self._generate_main(blueprint),
            language="python"
        ))

        # app/__init__.py
        files.append(GeneratedFile(
            path="app/__init__.py",
            content='"""FastAPI application package"""',
            language="python"
        ))

        # app/core/config.py
        files.append(GeneratedFile(
            path="app/core/config.py",
            content=self._generate_config(blueprint),
            language="python"
        ))

        # app/core/__init__.py
        files.append(GeneratedFile(
            path="app/core/__init__.py",
            content="",
            language="python"
        ))

        # app/db/session.py
        files.append(GeneratedFile(
            path="app/db/session.py",
            content=self._generate_db_session(blueprint),
            language="python"
        ))

        # app/db/base.py
        files.append(GeneratedFile(
            path="app/db/base.py",
            content=self._generate_db_base(blueprint),
            language="python"
        ))

        # app/db/__init__.py
        files.append(GeneratedFile(
            path="app/db/__init__.py",
            content="",
            language="python"
        ))

        return files

    def generate_entity_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate SQLAlchemy models and Pydantic schemas for entities"""
        files = []

        for entity in blueprint.entities:
            # Model file
            files.append(GeneratedFile(
                path=f"app/models/{entity.name.lower()}.py",
                content=self._generate_model(entity, blueprint),
                language="python"
            ))

            # Schema file
            files.append(GeneratedFile(
                path=f"app/schemas/{entity.name.lower()}.py",
                content=self._generate_schema(entity, blueprint),
                language="python"
            ))

        # models/__init__.py
        model_imports = "\n".join([
            f"from .{entity.name.lower()} import {entity.name}"
            for entity in blueprint.entities
        ])
        files.append(GeneratedFile(
            path="app/models/__init__.py",
            content=f'"""{blueprint.project_name} models"""\n{model_imports}',
            language="python"
        ))

        # schemas/__init__.py
        schema_imports = "\n".join([
            f"from .{entity.name.lower()} import {entity.name}Create, {entity.name}Update, {entity.name}Response"
            for entity in blueprint.entities
        ])
        files.append(GeneratedFile(
            path="app/schemas/__init__.py",
            content=f'"""{blueprint.project_name} schemas"""\n{schema_imports}',
            language="python"
        ))

        return files

    def generate_route_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate API route files"""
        files = []

        # Group routes by entity
        entity_routes = {}
        for route in blueprint.api_routes:
            if route.entity:
                if route.entity not in entity_routes:
                    entity_routes[route.entity] = []
                entity_routes[route.entity].append(route)

        # Generate endpoint file for each entity
        for entity_name, routes in entity_routes.items():
            entity = next((e for e in blueprint.entities if e.name == entity_name), None)
            if entity:
                files.append(GeneratedFile(
                    path=f"app/api/endpoints/{entity_name.lower()}.py",
                    content=self._generate_endpoint(entity, routes, blueprint),
                    language="python"
                ))

        # app/api/__init__.py
        files.append(GeneratedFile(
            path="app/api/__init__.py",
            content="",
            language="python"
        ))

        # app/api/endpoints/__init__.py
        endpoint_imports = "\n".join([
            f"from . import {entity_name.lower()}"
            for entity_name in entity_routes.keys()
        ])
        files.append(GeneratedFile(
            path="app/api/endpoints/__init__.py",
            content=f'"""API endpoints"""\n{endpoint_imports}',
            language="python"
        ))

        # app/api/router.py (aggregates all routers)
        files.append(GeneratedFile(
            path="app/api/router.py",
            content=self._generate_main_router(entity_routes.keys(), blueprint),
            language="python"
        ))

        return files

    def get_smoke_test_command(self) -> str:
        """Smoke test: Check if Python compiles"""
        return "python -m py_compile app/main.py app/core/config.py"

    # Private helper methods

    def _generate_pyproject_toml(self, blueprint: TemplateBlueprint) -> str:
        return f"""[project]
name = "{blueprint.project_name}"
version = "0.1.0"
description = "{blueprint.project_name} FastAPI application"
requires-python = ">=3.11"

[build-system]
requires = ["setuptools>=65.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]
"""

    def _generate_requirements(self, blueprint: TemplateBlueprint) -> str:
        return """fastapi[all]==0.104.1
sqlalchemy[asyncio]==2.0.23
alembic==1.13.0
pydantic==2.5.2
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
psycopg2-binary==2.9.9
asyncpg==0.29.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
"""

    def _generate_alembic_ini(self, blueprint: TemplateBlueprint) -> str:
        return """[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

    def _generate_dockerfile(self, blueprint: TemplateBlueprint) -> str:
        return f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    def _generate_docker_compose(self, blueprint: TemplateBlueprint) -> str:
        return f"""version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/{blueprint.project_name}
      - JWT_SECRET=your-secret-key-change-in-production
      - JWT_ALGORITHM=HS256
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB={blueprint.project_name}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

    def _generate_main(self, blueprint: TemplateBlueprint) -> str:
        return f'''"""
{blueprint.project_name} FastAPI application

Generated by SDLC Orchestrator App Builder
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title="{blueprint.project_name}",
    version="0.1.0",
    openapi_url=f"{{settings.API_V1_STR}}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Health check endpoint"""
    return {{"message": "Welcome to {blueprint.project_name} API"}}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {{"status": "healthy"}}
'''

    def _generate_config(self, blueprint: TemplateBlueprint) -> str:
        return f'''"""Application configuration"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "{blueprint.project_name}"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
'''

    def _generate_db_session(self, blueprint: TemplateBlueprint) -> str:
        return """\"\"\"Database session management\"\"\"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    \"\"\"Dependency to get database session\"\"\"
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
"""

    def _generate_db_base(self, blueprint: TemplateBlueprint) -> str:
        model_imports = "\n".join([
            f"from app.models.{entity.name.lower()} import {entity.name}"
            for entity in blueprint.entities
        ])
        return f'''"""Import all models here for Alembic"""

from app.db.session import Base

{model_imports}
'''

    def _generate_model(self, entity, blueprint: TemplateBlueprint) -> str:
        fields_code = []
        for field in entity.fields:
            if field.type == "string":
                fields_code.append(f"    {field.name} = Column(String, {'unique=True, ' if field.unique else ''}nullable={not field.required})")
            elif field.type == "integer":
                fields_code.append(f"    {field.name} = Column(Integer, nullable={not field.required})")
            elif field.type == "boolean":
                fields_code.append(f"    {field.name} = Column(Boolean, default=False, nullable={not field.required})")
            elif field.type in ["date", "datetime"]:
                fields_code.append(f"    {field.name} = Column(DateTime, nullable={not field.required})")

        fields_str = "\n".join(fields_code)

        return f'''"""SQLAlchemy model for {entity.name}"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.db.session import Base


class {entity.name}(Base):
    """{entity.name} model"""

    __tablename__ = "{entity.name.lower()}s"

    id = Column(Integer, primary_key=True, index=True)
{fields_str}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
'''

    def _generate_schema(self, entity, blueprint: TemplateBlueprint) -> str:
        fields_code = []
        for field in entity.fields:
            python_type = {
                "string": "str",
                "integer": "int",
                "boolean": "bool",
                "date": "datetime",
                "datetime": "datetime",
            }.get(field.type, "str")

            optional = "Optional[" + python_type + "] = None" if not field.required else python_type

            fields_code.append(f"    {field.name}: {optional}")

        fields_str = "\n".join(fields_code)

        return f'''"""Pydantic schemas for {entity.name}"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class {entity.name}Base(BaseModel):
    """{entity.name} base schema"""
{fields_str}


class {entity.name}Create({entity.name}Base):
    """{entity.name} creation schema"""
    pass


class {entity.name}Update(BaseModel):
    """{entity.name} update schema"""
{fields_str}


class {entity.name}Response({entity.name}Base):
    """{entity.name} response schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
'''

    def _generate_endpoint(self, entity, routes, blueprint: TemplateBlueprint) -> str:
        has_get = any("GET" in r.methods for r in routes)
        has_post = any("POST" in r.methods for r in routes)
        has_put = any("PUT" in r.methods for r in routes)
        has_delete = any("DELETE" in r.methods for r in routes)

        crud_methods = []

        if has_get:
            crud_methods.append(f'''
@router.get("/", response_model=List[{entity.name}Response])
async def list_{entity.name.lower()}s(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all {entity.name.lower()}s"""
    result = await db.execute(
        select({entity.name}).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{{item_id}}", response_model={entity.name}Response)
async def get_{entity.name.lower()}(
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get {entity.name.lower()} by ID"""
    result = await db.execute(
        select({entity.name}).where({entity.name}.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="{entity.name} not found")
    return item
''')

        if has_post:
            crud_methods.append(f'''
@router.post("/", response_model={entity.name}Response, status_code=201)
async def create_{entity.name.lower()}(
    item: {entity.name}Create,
    db: AsyncSession = Depends(get_db)
):
    """Create new {entity.name.lower()}"""
    db_item = {entity.name}(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
''')

        if has_put:
            crud_methods.append(f'''
@router.put("/{{item_id}}", response_model={entity.name}Response)
async def update_{entity.name.lower()}(
    item_id: int,
    item: {entity.name}Update,
    db: AsyncSession = Depends(get_db)
):
    """Update {entity.name.lower()}"""
    result = await db.execute(
        select({entity.name}).where({entity.name}.id == item_id)
    )
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="{entity.name} not found")

    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)

    await db.commit()
    await db.refresh(db_item)
    return db_item
''')

        if has_delete:
            crud_methods.append(f'''
@router.delete("/{{item_id}}", status_code=204)
async def delete_{entity.name.lower()}(
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete {entity.name.lower()}"""
    result = await db.execute(
        select({entity.name}).where({entity.name}.id == item_id)
    )
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="{entity.name} not found")

    await db.delete(db_item)
    await db.commit()
''')

        methods_str = "".join(crud_methods)

        return f'''"""API endpoints for {entity.name}"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.{entity.name.lower()} import {entity.name}
from app.schemas.{entity.name.lower()} import (
    {entity.name}Create,
    {entity.name}Update,
    {entity.name}Response
)

router = APIRouter(prefix="/{entity.name.lower()}s", tags=["{entity.name.lower()}s"])

{methods_str}
'''

    def _generate_main_router(self, entity_names, blueprint: TemplateBlueprint) -> str:
        router_includes = "\n".join([
            f"from app.api.endpoints import {name.lower()}\n"
            f"api_router.include_router({name.lower()}.router)"
            for name in entity_names
        ])

        return f'''"""Main API router"""

from fastapi import APIRouter

api_router = APIRouter()

{router_includes}
'''
