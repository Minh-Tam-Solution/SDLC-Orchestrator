"""
FastAPI Prompt Templates.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)

Vietnamese-optimized prompt templates for FastAPI code generation.
Designed for Vietnam SME market (40% strategy wedge).

Features:
- Complete CRUD generation
- SQLAlchemy models
- Pydantic schemas
- Alembic migrations
- Vietnamese comments and validation messages

Author: Backend Lead
Date: December 23, 2025
"""

from typing import Dict, Any
from .base_templates import BaseTemplates, TemplateContext, GenerationType


class FastAPITemplates(BaseTemplates):
    """
    FastAPI-specific prompt templates.

    Generates production-ready FastAPI code with:
    - Async SQLAlchemy 2.0
    - Pydantic v2 schemas
    - JWT authentication
    - RBAC authorization
    - Vietnamese error messages
    """

    @property
    def framework_name(self) -> str:
        return "FastAPI"

    @property
    def language(self) -> str:
        return "python"

    def get_system_prompt(self) -> str:
        """Get FastAPI system prompt."""
        return """Bạn là một AI chuyên gia phát triển backend với FastAPI cho doanh nghiệp SME Việt Nam.

## Expertise
- FastAPI 0.100+ với async/await
- SQLAlchemy 2.0 (async, type hints)
- Pydantic v2 (validation, serialization)
- PostgreSQL + Alembic migrations
- JWT authentication + RBAC
- RESTful API design

## Coding Standards
- Python 3.11+ với type hints đầy đủ
- Async/await cho tất cả I/O operations
- Google-style docstrings
- snake_case cho variables/functions
- PascalCase cho classes
- UPPERCASE cho constants

## Security
- Input validation với Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- Authentication required cho protected routes
- Role-based access control

## Quality
- Error handling với HTTPException
- Logging với structlog
- No TODOs or placeholders
- Production-ready code only
"""

    def get_generation_prompt(self, context: TemplateContext) -> str:
        """
        Get FastAPI generation prompt.

        Args:
            context: TemplateContext with blueprint

        Returns:
            Complete generation prompt
        """
        if context.generation_type == GenerationType.FULL_APP:
            return self._get_full_app_prompt(context)
        elif context.generation_type == GenerationType.MODULE:
            return self._get_module_prompt(context)
        elif context.generation_type == GenerationType.ENTITY:
            return self._get_entity_prompt(context)
        elif context.generation_type == GenerationType.CRUD_API:
            return self._get_crud_prompt(context)
        else:
            return self._get_full_app_prompt(context)

    def _get_full_app_prompt(self, context: TemplateContext) -> str:
        """Generate prompt for full app generation."""
        return f"""{self.get_system_prompt()}

## Nhiệm vụ
Tạo ứng dụng FastAPI hoàn chỉnh từ đặc tả IR (Intermediate Representation) sau.

## App Blueprint
```json
{context.blueprint_json}
```

## Yêu cầu kỹ thuật
- **Ứng dụng**: {context.app_name}
- **Mô tả**: {context.app_description or 'Không có mô tả'}
- **Database**: {context.database}
- **Bao gồm tests**: {'Có' if context.include_tests else 'Không'}

{self.get_file_structure_hint()}

{self.VIETNAMESE_CODING_RULES if context.vietnamese_comments else ''}

{self.OUTPUT_FORMAT}

## Các file cần tạo
1. **Models** (app/models/): SQLAlchemy models với relationships
2. **Schemas** (app/schemas/): Pydantic schemas (Create, Update, Response)
3. **Routes** (app/api/routes/): CRUD endpoints với authentication
4. **Services** (app/services/): Business logic layer
5. **Dependencies** (app/api/deps.py): Common dependencies

## Bắt đầu tạo code
"""

    def _get_module_prompt(self, context: TemplateContext) -> str:
        """Generate prompt for single module generation."""
        return f"""{self.get_system_prompt()}

## Nhiệm vụ
Tạo module "{context.target_module}" cho ứng dụng FastAPI.

## App Blueprint
```json
{context.blueprint_json}
```

## Module cần tạo: {context.target_module}

{self.get_file_structure_hint()}

{self.VIETNAMESE_CODING_RULES if context.vietnamese_comments else ''}

{self.OUTPUT_FORMAT}

## Các file cần tạo cho module {context.target_module}
1. app/models/{context.target_module}.py - SQLAlchemy models
2. app/schemas/{context.target_module}.py - Pydantic schemas
3. app/api/routes/{context.target_module}.py - CRUD endpoints
4. app/services/{context.target_module}_service.py - Business logic

Bắt đầu tạo code cho module {context.target_module}:
"""

    def _get_entity_prompt(self, context: TemplateContext) -> str:
        """Generate prompt for single entity generation."""
        return f"""{self.get_system_prompt()}

## Nhiệm vụ
Tạo entity "{context.target_entity}" với đầy đủ model, schema, và routes.

## App Blueprint
```json
{context.blueprint_json}
```

## Entity cần tạo: {context.target_entity}

{self.VIETNAMESE_CODING_RULES if context.vietnamese_comments else ''}

{self.OUTPUT_FORMAT}

Tạo code cho entity {context.target_entity}:
"""

    def _get_crud_prompt(self, context: TemplateContext) -> str:
        """Generate prompt for CRUD endpoints only."""
        return f"""{self.get_system_prompt()}

## Nhiệm vụ
Tạo CRUD API endpoints cho "{context.target_entity or context.target_module}".

## Blueprint
```json
{context.blueprint_json}
```

## Yêu cầu CRUD
- GET /{{resource}} - List với pagination, filtering, sorting
- GET /{{resource}}/{{id}} - Get by ID
- POST /{{resource}} - Create
- PUT /{{resource}}/{{id}} - Update
- DELETE /{{resource}}/{{id}} - Soft delete

{self.VIETNAMESE_CODING_RULES if context.vietnamese_comments else ''}

{self.OUTPUT_FORMAT}

Tạo CRUD endpoints:
"""

    def get_file_structure_hint(self) -> str:
        """Get FastAPI file structure."""
        return """
## Cấu trúc thư mục FastAPI
```
app/
├── __init__.py
├── main.py              # FastAPI app entry point
├── core/
│   ├── config.py        # Settings
│   ├── security.py      # JWT, hashing
│   └── deps.py          # Dependencies
├── models/
│   ├── __init__.py
│   ├── base.py          # Base model với timestamps
│   └── {module}.py      # Domain models
├── schemas/
│   ├── __init__.py
│   └── {module}.py      # Pydantic schemas
├── api/
│   ├── __init__.py
│   ├── deps.py          # API dependencies
│   └── routes/
│       ├── __init__.py
│       └── {module}.py  # Route handlers
├── services/
│   └── {module}_service.py  # Business logic
└── db/
    ├── session.py       # Database session
    └── base.py          # Import all models
```
"""

    def get_common_patterns(self) -> str:
        """Get FastAPI coding patterns."""
        return """
## Common Patterns

### Model Pattern
```python
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Entity(BaseModel):
    __tablename__ = "entities"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    items = relationship("Item", back_populates="entity")
```

### Schema Pattern
```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class EntityCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class EntityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None

class EntityResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

### Route Pattern
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user

router = APIRouter(prefix="/entities", tags=["entities"])

@router.get("/", response_model=list[EntityResponse])
async def list_entities(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    # Implementation
    pass
```

### Service Pattern
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class EntityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, entity_id: UUID) -> Entity | None:
        result = await self.db.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: EntityCreate) -> Entity:
        entity = Entity(**data.model_dump())
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
```
"""

    def get_vietnamese_validation_messages(self) -> Dict[str, str]:
        """Get Vietnamese validation error messages."""
        return {
            "required": "Trường này là bắt buộc",
            "min_length": "Độ dài tối thiểu là {min_length} ký tự",
            "max_length": "Độ dài tối đa là {max_length} ký tự",
            "email": "Email không hợp lệ",
            "phone": "Số điện thoại không hợp lệ",
            "min_value": "Giá trị tối thiểu là {min_value}",
            "max_value": "Giá trị tối đa là {max_value}",
            "unique": "Giá trị đã tồn tại trong hệ thống",
            "not_found": "Không tìm thấy {resource}",
            "unauthorized": "Bạn không có quyền thực hiện thao tác này",
            "invalid_credentials": "Thông tin đăng nhập không chính xác"
        }


# Singleton instance for convenience
fastapi_templates = FastAPITemplates()
